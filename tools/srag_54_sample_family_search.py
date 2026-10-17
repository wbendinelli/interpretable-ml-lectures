"""Versioned six-family log-loss search on the committed temporal sample.

Stages: --prepare, --search, --finalize, --evaluate, --export. All training
artifacts stay in an explicitly named external directory. Optional reuse of
the completed phase-53 plain XGBoost arm is audited before protocol freezing.
Imports never fit models. Historical studies and the course reference remain
unchanged; the previously inspected test remains exploratory.
"""

from __future__ import annotations

import argparse
import copy
import gc
import os
import re
import shutil
import time
import warnings
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
import srag_51_course_study as C
import srag_53_sample_balance_search as R
from sklearn.exceptions import ConvergenceWarning
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

ROOT = C.ROOT
VERSION = "course-sample-family-logloss-v1"
FAMILIES = tuple(C.S.MODELOS)
SEED = 42


def configurations() -> list[dict]:
    rows = []
    for original in C.plain_configurations():
        spec = {**original, "candidate_id": C.object_hash(original)[:16]}
        rows.append(spec)
    counts = Counter(row["family"] for row in rows)
    if counts != Counter(C.S.N_ITER) or len({r["candidate_id"] for r in rows}) != len(
        rows
    ):
        raise ValueError(
            "The family budgets/configurations do not match the fixed grid"
        )
    return rows


def source_hashes() -> dict:
    return {**R.source_hashes(), Path(__file__).name: C.file_hash(Path(__file__))}


def _signed(value: dict, key: str) -> dict:
    return R._signed(value, key)


def _verify(value: dict, key: str) -> None:
    R._verify(value, key)


def _child(directory: Path, relative: str) -> Path:
    return R._child(directory, relative)


def _verify_file(directory: Path, artifact: dict) -> Path:
    return R._verify_file(directory, artifact)


def _split_audit(frame) -> dict:
    result = {}
    for split in ("train", "val", "test"):
        part = frame.loc[frame["split"] == split]
        result[split] = {
            "n": len(part),
            "ids_sha256": C.object_hash(part["gold_id"].tolist()),
        }
        if split != "test":
            result[split].update(
                events=int(part["y_obito"].sum()),
                y_sha256=C.object_hash(part["y_obito"].tolist()),
            )
    return result


def _audit_probabilities(path: Path, expected_y: np.ndarray, expected_ids: np.ndarray):
    with np.load(path, allow_pickle=False) as saved:
        y, p = saved["y"], saved["p"]
        np.testing.assert_array_equal(y, expected_y)
        if "gold_id" in saved:
            np.testing.assert_array_equal(saved["gold_id"], expected_ids)
        if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
            raise ValueError("Invalid checkpoint probabilities")
        return C.compute_metrics(y, p)


def _audit_import(
    source: Path, data_path: Path, frame, specs: list[dict], threads: int
):
    source = C.external_directory(source)
    protocol = R.load_protocol(data_path, source)
    selection = R._read_selection(source, protocol)
    if (
        protocol["threads"] != threads
        or protocol["seed"] != SEED
        or protocol["features"] != list(C.M.FEATURES)
        or protocol["versions"] != C._versions()
        or protocol["code_sha256"] != R.source_hashes()
        or selection["test_used_for_selection"]
        or selection["probabilities_recalibrated"]
    ):
        raise ValueError("Imported XGBoost study has a different execution contract")
    requested = {s["candidate_id"]: s for s in specs if s["family"] == "xgb"}
    offered = {
        s["candidate_id"]: s for s in protocol["candidates"] if s["strategy"] == "plain"
    }
    if requested != offered:
        raise ValueError("Imported plain XGBoost parameter vectors differ")
    val = frame.loc[frame["split"] == "val"]
    y = val["y_obito"].to_numpy(dtype=np.int8)
    ids = val["gold_id"].to_numpy()
    rows, receipts = [], []
    for spec in requested.values():
        row = R.completed(source, protocol, spec, audit_predictions=True)
        if row is None:
            raise ValueError(
                "All imported XGBoost candidates must be complete and signed"
            )
        prediction = _verify_file(source, row["validation_predictions"])
        measured = _audit_probabilities(prediction, y, ids)
        if measured != row["validation"] or row["training"]["n"] != len(
            frame.loc[frame["split"] == "train"]
        ):
            raise ValueError("Imported validation/training evidence differs")
        if row["model_artifact"] is not None:
            _verify_file(source, row["model_artifact"])
        rows.append(row)
        receipts.append(
            {
                "candidate_id": row["candidate_id"],
                "result_sha256": row["result_sha256"],
                "result_file_sha256": C.file_hash(R._result_path(source, spec)),
                "validation_predictions": row["validation_predictions"],
                "model_artifact": row["model_artifact"],
            }
        )
    best = min(rows, key=lambda r: (r["validation"]["logloss"], r["candidate_id"]))
    frozen = next(r for r in selection["finalists"] if r["strategy"] == "plain")
    if frozen != best or best["model_artifact"] is None:
        raise ValueError("Imported plain finalist differs from its validation minimum")
    # Only validation is predicted here. No test predictions are read/imported.
    model = joblib.load(_verify_file(source, best["model_artifact"]))
    with threadpool_limits(limits=threads):
        p = C.predict_probabilities(model, val, "xgb")
    with np.load(
        _verify_file(source, best["validation_predictions"]), allow_pickle=False
    ) as saved:
        np.testing.assert_array_equal(p, saved["p"])
    del model
    receipt = {
        "study_basename": source.name,
        "protocol_path": "protocol.json",
        "protocol_sha256": protocol["protocol_sha256"],
        "protocol_file_sha256": C.file_hash(source / "protocol.json"),
        "selection_sha256": selection["selection_sha256"],
        "source_sha256": protocol["source"]["sha256"],
        "split_membership": _split_audit(frame),
        "candidates": receipts,
    }
    return receipt, rows


def prepare_protocol(
    data_path: Path,
    output_dir: Path,
    threads: int = 4,
    import_xgb_study: Path | None = None,
) -> dict:
    output_dir = C.external_directory(output_dir)
    if threads not in range(1, 5):
        raise ValueError("Use one through four threads")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Prepare requires a new or empty external directory")
    frame = R.load_sample(data_path)
    specs = configurations()
    imported = None
    if import_xgb_study is not None:
        receipt, _ = _audit_import(import_xgb_study, data_path, frame, specs, threads)
        C.write_json(
            output_dir / "import-location.json",
            {"path": str(import_xgb_study.resolve())},
        )
        C.write_json(output_dir / "import-receipt.json", receipt)
        imported = {
            "study_basename": import_xgb_study.name,
            "protocol_path": receipt["protocol_path"],
            "protocol_sha256": receipt["protocol_sha256"],
            "receipt": {
                "path": "import-receipt.json",
                "sha256": C.file_hash(output_dir / "import-receipt.json"),
            },
            "location": {
                "path": "import-location.json",
                "sha256": C.file_hash(output_dir / "import-location.json"),
            },
            "candidate_count": len(receipt["candidates"]),
        }
    protocol = {
        "version": VERSION,
        "seed": SEED,
        "threads": threads,
        "primary_metric": "logloss",
        "strategy": "plain",
        "source": {"basename": data_path.name, "sha256": C.file_hash(data_path)},
        "cohort_manifest_sha256": C.file_hash(
            ROOT / "modules/00-dataset/gold/counts.json"
        ),
        "code_sha256": source_hashes(),
        "versions": C._versions(),
        "features": list(C.M.FEATURES),
        "splits": _split_audit(frame),
        "candidates": specs,
        "budgets": dict(C.S.N_ITER),
        "parameter_spaces": copy.deepcopy(C.S.ESPACOS),
        "import_xgb": imported,
        "training": "The exact committed 200,000 training records; natural class frequencies, no class weights or resampling in any family.",
        "preprocessing": "Phase-51 train-only vocabulary, imputation and scaling, fitted once per family; all pipelines receive the same forty raw inputs.",
        "selection": "Minimum unrounded 2023 validation log loss within each family, then across the six frozen finalists; exact ties by candidate_id. Test never chooses.",
        "budget": "Historical predeclared parameter spaces and family-specific budgets, not equal optimization capacity. Random forest has 300 fixed trees; dummy and LPM have no tuning grid.",
        "lpm": "OLS is fitted by squared error, not log loss, and has no tuning grid. Its continuous outputs are clipped to [1e-6, 1-1e-6], as in phases 50/51; raw range and clipping counts are reported before scoring this diagnostic baseline.",
        "convergence": "ConvergenceWarning is fatal; logistic iteration counts must be strictly below max_iter and are recorded with each result.",
        "historical_bridge": "Phase 50 assembled category vocabularies before slicing the data. Phase 54 uses the phase-51 train-only pipeline. Changes from the historical table do not isolate the selection-metric change alone.",
        "probability_calibration": "Raw probabilities only; no post-fit recalibration. Threshold 0.5 is descriptive, never the selection rule.",
        "test_status": "2024 was previously inspected. No new test prediction/metric before all six finalists and the winner are frozen; later comparison is exploratory.",
        "scope": "Finite plain-family comparison, separate from XGBoost balancing. No automatic replacement of the historical course model or its explanations.",
    }
    protocol = _signed(protocol, "protocol_sha256")
    C.write_json(output_dir / "protocol.json", protocol)
    print(
        f"Protocol frozen: {len(specs)} candidates, {0 if imported is None else imported['candidate_count']} reusable; no fits executed.",
        flush=True,
    )
    return protocol


def read_protocol(directory: Path) -> dict:
    directory = C.external_directory(directory)
    protocol = C.read_json(directory / "protocol.json")
    _verify(protocol, "protocol_sha256")
    if (
        protocol["version"] != VERSION
        or protocol["primary_metric"] != "logloss"
        or protocol["strategy"] != "plain"
        or protocol["features"] != list(C.M.FEATURES)
        or protocol["code_sha256"] != source_hashes()
        or protocol["versions"] != C._versions()
        or protocol["candidates"] != configurations()
        or protocol["cohort_manifest_sha256"]
        != C.file_hash(ROOT / "modules/00-dataset/gold/counts.json")
    ):
        raise ValueError("Frozen protocol, sources or runtime changed")
    if protocol["import_xgb"]:
        for key in ("location", "receipt"):
            _verify_file(directory, protocol["import_xgb"][key])
    return protocol


def load_protocol(data_path: Path, directory: Path) -> dict:
    protocol = read_protocol(directory)
    if (
        C.file_hash(data_path) != protocol["source"]["sha256"]
        or C.file_hash(data_path) != R._committed_sample_sha256()
    ):
        raise ValueError("Data differ from the frozen committed sample")
    return protocol


def _result_path(directory: Path, spec: dict) -> Path:
    return directory / "trials" / spec["candidate_id"] / "result.json"


def completed(directory: Path, protocol: dict, spec: dict, frame=None) -> dict | None:
    path = _result_path(directory, spec)
    if not path.exists():
        return None
    row = C.read_json(path)
    _verify(row, "result_sha256")
    if (
        row["status"] != "complete"
        or row["protocol_sha256"] != protocol["protocol_sha256"]
        or any(row[k] != spec[k] for k in spec)
    ):
        raise ValueError("Trial belongs to another candidate/protocol")
    prediction = _verify_file(directory, row["validation_predictions"])
    if row["model_artifact"] is not None:
        _verify_file(directory, row["model_artifact"])
    if frame is not None:
        val = frame.loc[frame["split"] == "val"]
        measured = _audit_probabilities(
            prediction,
            val["y_obito"].to_numpy(dtype=np.int8),
            val["gold_id"].to_numpy(),
        )
        if measured != row["validation"]:
            raise ValueError(
                "Validation scores differ from the real ordered labels/checkpoint"
            )
    return row


def _copy_artifact(
    source: Path, artifact: dict, destination: Path, relative: str
) -> dict:
    old = _verify_file(source, artifact)
    new = _child(destination, relative)
    new.parent.mkdir(parents=True, exist_ok=True)
    temporary = new.with_suffix(new.suffix + ".tmp")
    shutil.copyfile(old, temporary)
    os.replace(temporary, new)
    if C.file_hash(new) != artifact["sha256"]:
        raise ValueError("Copied artifact changed bytes")
    return {"path": relative, "sha256": artifact["sha256"]}


def _import_trials(data_path: Path, directory: Path, protocol: dict, frame) -> None:
    imported = protocol["import_xgb"]
    if not imported:
        return
    source = Path(C.read_json(_verify_file(directory, imported["location"]))["path"])
    receipt, rows = _audit_import(
        source, data_path, frame, protocol["candidates"], protocol["threads"]
    )
    if receipt != C.read_json(_verify_file(directory, imported["receipt"])):
        raise ValueError("Import evidence changed since preparation")
    for old in rows:
        spec = next(
            s
            for s in protocol["candidates"]
            if s["candidate_id"] == old["candidate_id"]
        )
        if completed(directory, protocol, spec, frame) is not None:
            continue
        candidate_id = spec["candidate_id"]
        prediction = _copy_artifact(
            source,
            old["validation_predictions"],
            directory,
            f"trials/{candidate_id}/validation-predictions.npz",
        )
        artifact = (
            None
            if old["model_artifact"] is None
            else _copy_artifact(
                source,
                old["model_artifact"],
                directory,
                f"checkpoints/xgb/{candidate_id}.joblib",
            )
        )
        row = {
            **spec,
            "status": "complete",
            "protocol_sha256": protocol["protocol_sha256"],
            **{
                key: copy.deepcopy(old[key])
                for key in (
                    "validation",
                    "training",
                    "effective_params",
                    "fit_seconds",
                    "fit_warnings",
                )
            },
            "validation_predictions": prediction,
            "model_artifact": artifact,
            "origin": {
                "kind": "imported_phase53_plain",
                "protocol_sha256": imported["protocol_sha256"],
                "result_sha256": old["result_sha256"],
            },
            "lpm_clip": None,
            "convergence": None,
        }
        C.write_json(_result_path(directory, spec), _signed(row, "result_sha256"))
    print(
        "Audited plain XGBoost arm imported; probabilities and scores unchanged.",
        flush=True,
    )


def _save_predictions(path: Path, frame, p: np.ndarray) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as stream:
        np.savez_compressed(
            stream,
            gold_id=frame["gold_id"].to_numpy(),
            y=frame["y_obito"].to_numpy(dtype=np.int8),
            p=np.asarray(p, dtype=np.float64),
        )
    os.replace(temporary, path)
    return {"path": str(path), "sha256": C.file_hash(path)}


def _lpm_diagnostics(raw: np.ndarray) -> dict:
    raw = np.asarray(raw, dtype=np.float64)
    if not np.isfinite(raw).all():
        raise ValueError("LPM produced a nonfinite raw prediction")
    return {
        "n": len(raw),
        "raw_min": float(raw.min()),
        "raw_max": float(raw.max()),
        "raw_below_zero": int((raw < 0).sum()),
        "raw_above_one": int((raw > 1).sum()),
        "clipped_low": int((raw < 1e-6).sum()),
        "clipped_high": int((raw > 1 - 1e-6).sum()),
        "clip_lower": 1e-6,
        "clip_upper": 1 - 1e-6,
    }


def run_search(data_path: Path, directory: Path, family: str = "all") -> None:
    directory = C.external_directory(directory)
    protocol = load_protocol(data_path, directory)
    if family not in (*FAMILIES, "all"):
        raise ValueError("Unknown search family")
    if (directory / "selection.json").exists():
        raise ValueError("Selection is frozen; no more search is allowed")
    frame = R.load_sample(data_path)
    if _split_audit(frame) != protocol["splits"]:
        raise ValueError("Ordered split membership changed")
    xgb_specs = [s for s in protocol["candidates"] if s["family"] == "xgb"]
    if protocol["import_xgb"] and any(
        completed(directory, protocol, s) is None for s in xgb_specs
    ):
        _import_trials(data_path, directory, protocol, frame)
    train = frame.loc[frame["split"] == "train"].copy()
    val = frame.loc[frame["split"] == "val"].copy()
    del frame
    y = train["y_obito"].to_numpy(dtype=np.int8)
    for name in FAMILIES if family == "all" else (family,):
        specs = [s for s in protocol["candidates"] if s["family"] == name]
        rows = [
            r for s in specs if (r := completed(directory, protocol, s)) is not None
        ]
        pending = [s for s in specs if completed(directory, protocol, s) is None]
        if not pending:
            print(f"Already complete: {name}", flush=True)
            continue
        template = C.build_pipeline(name, pending[0]["params"], protocol["threads"])
        prepare = Pipeline(template.steps[:-1])
        with threadpool_limits(limits=protocol["threads"]):
            xt = prepare.fit_transform(C.model_inputs(train, name), y)
            xv = prepare.transform(C.model_inputs(val, name))
        for spec in pending:
            print(f"Fitting {name} {spec['candidate_id']}", flush=True)
            started = time.perf_counter()
            with (
                warnings.catch_warnings(record=True) as caught,
                threadpool_limits(limits=protocol["threads"]),
            ):
                warnings.simplefilter("always")
                estimator = C.build_pipeline(name, spec["params"], protocol["threads"])[
                    "model"
                ]
                estimator.fit(xt, y)
                if any(issubclass(w.category, ConvergenceWarning) for w in caught):
                    raise RuntimeError("Candidate did not converge")
                convergence = None
                if name == "logit":
                    iterations = np.asarray(estimator.n_iter_, dtype=int)
                    if (iterations >= estimator.max_iter).any():
                        raise RuntimeError(
                            "Logistic candidate reached its iteration limit"
                        )
                    convergence = {
                        "n_iter": iterations.tolist(),
                        "max_iter": estimator.max_iter,
                        "converged": True,
                    }
                clipping = None
                if name == "lpm":
                    raw = estimator.predict(xv)
                    clipping = _lpm_diagnostics(raw)
                    p = np.clip(raw, 1e-6, 1 - 1e-6)
                else:
                    p = estimator.predict_proba(xv)[:, 1]
            measured = C.compute_metrics(val["y_obito"].to_numpy(), p)
            prediction = _save_predictions(
                directory
                / "trials"
                / spec["candidate_id"]
                / "validation-predictions.npz",
                val,
                p,
            )
            prediction["path"] = str(Path(prediction["path"]).relative_to(directory))
            artifact = None
            best = (
                min(rows, key=lambda r: (r["validation"]["logloss"], r["candidate_id"]))
                if rows
                else None
            )
            if best is None or (measured["logloss"], spec["candidate_id"]) < (
                best["validation"]["logloss"],
                best["candidate_id"],
            ):
                artifact = R._model_artifact(
                    directory,
                    Pipeline(prepare.steps + [("model", estimator)]),
                    f"checkpoints/{name}/{spec['candidate_id']}.joblib",
                )
            row = _signed(
                {
                    **spec,
                    "status": "complete",
                    "protocol_sha256": protocol["protocol_sha256"],
                    "training": {
                        "n": len(train),
                        "events": int(y.sum()),
                        "strategy": "plain",
                        "sampling": "none; unchanged committed training sample",
                        "preprocessing_fit_scope": "family training rows only",
                        "preprocessing_reused_within_family": True,
                    },
                    "validation": measured,
                    "validation_predictions": prediction,
                    "model_artifact": artifact,
                    "effective_params": C.compact_parameters(estimator, spec["params"]),
                    "fit_seconds": time.perf_counter() - started,
                    "fit_warnings": [str(w.message) for w in caught],
                    "origin": {"kind": "fitted_phase54"},
                    "lpm_clip": clipping,
                    "convergence": convergence,
                },
                "result_sha256",
            )
            C.write_json(_result_path(directory, spec), row)
            rows.append(row)
            del estimator
            gc.collect()
        del xt, xv, prepare, template
        gc.collect()


def _all_rows(directory: Path, protocol: dict, frame) -> list[dict]:
    rows = [
        completed(directory, protocol, spec, frame) for spec in protocol["candidates"]
    ]
    if any(r is None for r in rows):
        raise ValueError("All registered candidates must finish before selection")
    return rows


def _finalists(rows: list[dict]) -> list[dict]:
    return [
        min(
            (r for r in rows if r["family"] == name),
            key=lambda r: (r["validation"]["logloss"], r["candidate_id"]),
        )
        for name in FAMILIES
    ]


def _read_selection(directory: Path, protocol: dict, rows: list[dict]) -> dict:
    selection = C.read_json(directory / "selection.json")
    _verify(selection, "selection_sha256")
    finalists = _finalists(rows)
    winner = min(
        finalists, key=lambda r: (r["validation"]["logloss"], r["candidate_id"])
    )
    if (
        selection["protocol_sha256"] != protocol["protocol_sha256"]
        or selection["finalists"] != finalists
        or selection["winner"] != winner
        or selection["candidate_count"] != len(rows)
        or selection["rule"] != protocol["selection"]
        or selection["test_used_for_selection"]
        or selection["probabilities_recalibrated"]
        or not selection["finalists_frozen_before_test"]
        or selection["canonical_model"]["sha256"] != winner["model_artifact"]["sha256"]
    ):
        raise ValueError("Frozen selection differs from validation minima")
    _verify_file(directory, selection["canonical_model"])
    return selection


def finalize_selection(data_path: Path, directory: Path) -> dict:
    directory = C.external_directory(directory)
    protocol = load_protocol(data_path, directory)
    frame = R.load_sample(data_path)
    rows = _all_rows(directory, protocol, frame)
    if (directory / "selection.json").exists():
        return _read_selection(directory, protocol, rows)
    finalists = _finalists(rows)
    winner = min(
        finalists, key=lambda r: (r["validation"]["logloss"], r["candidate_id"])
    )
    for row in finalists:
        if row["model_artifact"] is None:
            raise ValueError("A family finalist is missing its fitted checkpoint")
        _verify_file(directory, row["model_artifact"])
    canonical = _copy_artifact(
        directory, winner["model_artifact"], directory, "winner.joblib"
    )
    selection = _signed(
        {
            "protocol_sha256": protocol["protocol_sha256"],
            "rule": protocol["selection"],
            "candidate_count": len(rows),
            "finalists": finalists,
            "winner": winner,
            "canonical_model": canonical,
            "prediction_interface": "srag_51_course_study.predict_probabilities(saved_pipeline, raw_forty_input_frame, selected_family)",
            "test_used_for_selection": False,
            "probabilities_recalibrated": False,
            "finalists_frozen_before_test": True,
        },
        "selection_sha256",
    )
    C.write_json(directory / "selection.json", selection)
    print(
        f"Six family finalists frozen; winner {winner['family']} {winner['candidate_id']}",
        flush=True,
    )
    return selection


def _read_evaluation(directory: Path, protocol: dict, selection: dict, frame) -> dict:
    report = C.read_json(directory / "test-evaluation.json")
    _verify(report, "evaluation_sha256")
    if (
        report["protocol_sha256"] != protocol["protocol_sha256"]
        or report["selection_sha256"] != selection["selection_sha256"]
        or report["selection_changed"]
        or not report["finalists_frozen_before_test"]
    ):
        raise ValueError("Test comparison differs from its frozen selection")
    if [r["candidate_id"] for r in report["finalists"]] != [
        r["candidate_id"] for r in selection["finalists"]
    ]:
        raise ValueError("An unfrozen model was included in test evaluation")
    test = frame.loc[frame["split"] == "test"]
    for row, frozen in zip(report["finalists"], selection["finalists"], strict=True):
        if row["family"] != frozen["family"] or row["strategy"] != "plain":
            raise ValueError("Test evidence has an incorrect family or strategy")
        measured = _audit_probabilities(
            _verify_file(directory, row["predictions"]),
            test["y_obito"].to_numpy(dtype=np.int8),
            test["gold_id"].to_numpy(),
        )
        if measured != row["test"]:
            raise ValueError("Test metrics differ from real labels/checkpoint")
    selected = next(
        r
        for r in report["finalists"]
        if r["candidate_id"] == selection["winner"]["candidate_id"]
    )
    if (
        report["test"] != selected["test"]
        or report["canonical_model"] != selection["canonical_model"]
    ):
        raise ValueError("Canonical test/model evidence differs")
    if (
        C.file_hash(directory / "test-predictions.npz")
        != selected["predictions"]["sha256"]
    ):
        raise ValueError("Canonical test predictions changed")
    return report


def evaluate_selected(data_path: Path, directory: Path) -> dict:
    directory = C.external_directory(directory)
    protocol = load_protocol(data_path, directory)
    frame = R.load_sample(data_path)
    selection = _read_selection(
        directory, protocol, _all_rows(directory, protocol, frame)
    )
    if (directory / "test-evaluation.json").exists():
        return _read_evaluation(directory, protocol, selection, frame)
    test = frame.loc[frame["split"] == "test"]
    records = []
    for row in selection["finalists"]:
        model = joblib.load(_verify_file(directory, row["model_artifact"]))
        with threadpool_limits(limits=protocol["threads"]):
            p = C.predict_probabilities(model, test, row["family"])
            clipping = None
            if row["family"] == "lpm":
                raw = model.predict(C.model_inputs(test, "lpm"))
                clipping = _lpm_diagnostics(raw)
                np.testing.assert_array_equal(p, np.clip(raw, 1e-6, 1 - 1e-6))
        artifact = _save_predictions(
            directory / "test-predictions" / f"{row['candidate_id']}.npz", test, p
        )
        artifact["path"] = str(Path(artifact["path"]).relative_to(directory))
        records.append(
            {
                "candidate_id": row["candidate_id"],
                "family": row["family"],
                "strategy": "plain",
                "test": C.compute_metrics(test["y_obito"].to_numpy(), p),
                "predictions": artifact,
                "lpm_clip": clipping,
            }
        )
        del model
        gc.collect()
    selected = next(
        r for r in records if r["candidate_id"] == selection["winner"]["candidate_id"]
    )
    _copy_artifact(
        directory, selected["predictions"], directory, "test-predictions.npz"
    )
    report = _signed(
        {
            "protocol_sha256": protocol["protocol_sha256"],
            "selection_sha256": selection["selection_sha256"],
            "status": "exploratory; previously inspected temporal period",
            "canonical_model": selection["canonical_model"],
            "test": selected["test"],
            "finalists": records,
            "selection_changed": False,
            "finalists_frozen_before_test": True,
        },
        "evaluation_sha256",
    )
    C.write_json(directory / "test-evaluation.json", report)
    print("Exploratory test comparison saved; validation choice unchanged.", flush=True)
    return _read_evaluation(directory, protocol, selection, frame)


def project_evidence(data_path: Path, directory: Path) -> dict:
    directory = C.external_directory(directory)
    protocol = load_protocol(data_path, directory)
    frame = R.load_sample(data_path)
    rows = _all_rows(directory, protocol, frame)
    selection = _read_selection(directory, protocol, rows)
    evaluation = _read_evaluation(directory, protocol, selection, frame)
    payload = {
        "status": "complete",
        "adoption": "Separate finite-family sample study; no automatic replacement of the historical course reference. XGBoost balancing remains a separate study.",
        "protocol": protocol,
        "validation_candidates": rows,
        "selection": selection,
        "evaluation": evaluation,
    }
    if re.search(
        r"/Users/|/private/|/var/folders|file://", C.canonical_bytes(payload).decode()
    ):
        raise ValueError("Private absolute path in aggregate export")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--import-xgb-study", type=Path)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--family", choices=(*FAMILIES, "all"), default="all")
    parser.add_argument("--output", type=Path)
    stages = parser.add_mutually_exclusive_group(required=True)
    for name in ("prepare", "search", "finalize", "evaluate", "export"):
        stages.add_argument(f"--{name}", action="store_true")
    args = parser.parse_args()
    if args.import_xgb_study is not None and not args.prepare:
        parser.error("--import-xgb-study is declared only at --prepare")
    if args.prepare:
        prepare_protocol(
            args.data, args.output_dir, args.threads, args.import_xgb_study
        )
    elif args.search:
        run_search(args.data, args.output_dir, args.family)
    elif args.finalize:
        finalize_selection(args.data, args.output_dir)
    elif args.evaluate:
        evaluate_selected(args.data, args.output_dir)
    else:
        if args.output is None:
            parser.error("--export requires --output")
        evidence = project_evidence(args.data, args.output_dir)
        C.write_json(args.output, evidence)
        print("Aggregate family-study evidence exported: complete.", flush=True)


if __name__ == "__main__":
    main()
