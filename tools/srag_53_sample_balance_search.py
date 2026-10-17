"""Versioned XGBoost balancing search on the committed training sample.

Stages: --prepare, --search, --finalize, --evaluate and --export. Training
artifacts require an explicit external --output-dir. Imports never fit models.
The old full-training study and historical course model are never modified.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import os
import shutil
import subprocess
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import srag_51_course_study as C
import srag_52_course_balance as B
from sklearn.exceptions import ConvergenceWarning
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

ROOT = C.ROOT
VERSION = "course-sample-balance-v3"
STRATEGIES = ("plain", "weights", "rus", "smotenc_restricted")
SEED = 42


def original_parameters() -> dict:
    return {key: C.M.XGB_PARAMS[key] for key in C.S.ESPACOS["xgb"]}


def configurations() -> tuple[list[dict], dict]:
    """Offer the same thirty parameter vectors to each strategy, without ties to AUC."""
    common = B.candidate_specs("xgb", "weights", seed=SEED)
    original = original_parameters()
    if original not in common:
        raise ValueError(
            "Original settings are absent from the registered grid. Decide an equal-budget replacement in every arm before preparation."
        )
    common = [original] + [params for params in common if params != original]
    candidates = []
    for strategy in STRATEGIES:
        if strategy != "plain" and B.candidate_specs(
            "xgb", strategy, seed=SEED
        ) != B.candidate_specs("xgb", "weights", seed=SEED):
            raise ValueError("All strategies must receive the same parameter vectors")
        for params in common:
            spec = {"family": "xgb", "strategy": strategy, "params": params}
            spec["candidate_id"] = C.object_hash(spec)[:16]
            candidates.append(spec)
    control = next(
        spec
        for spec in candidates
        if spec["strategy"] == "plain" and spec["params"] == original
    )
    if len(candidates) != 4 * C.S.N_ITER["xgb"]:
        raise ValueError("Unexpected search budget")
    return candidates, control


def source_hashes() -> dict:
    return {**C._source_hashes(), Path(__file__).name: C.file_hash(Path(__file__))}


def _committed_sample_sha256() -> str:
    relative = C.M.AMOSTRA.relative_to(ROOT).as_posix()
    result = subprocess.run(
        ["git", "show", f"HEAD:{relative}"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    return hashlib.sha256(result.stdout).hexdigest()


def load_sample(data_path: Path) -> pd.DataFrame:
    """Require the exact committed sample, including complete validation/test rows."""
    expected_hash = _committed_sample_sha256()
    if (
        C.file_hash(data_path) != expected_hash
        or C.file_hash(C.M.AMOSTRA) != expected_hash
    ):
        raise ValueError("The sample must match the committed parquet bytes exactly")
    frame = C.M.load_gold(data_path)
    counts = C.read_json(ROOT / "modules/00-dataset/gold/counts.json")
    expected = {
        "train": counts["amostra"]["treino_amostrado"],
        "val": counts["splits"]["val"]["n"],
        "test": counts["splits"]["test"]["n"],
    }
    if expected["train"] != 200_000 or len(frame) != sum(expected.values()):
        raise ValueError(
            "This version requires the committed 200,000-record training sample"
        )
    if set(frame["split"].astype(str).unique()) != set(expected):
        raise ValueError("Unexpected temporal splits")
    ids = frame["gold_id"].to_numpy()
    if len(np.unique(ids)) != len(ids) or not np.all(np.diff(ids) > 0):
        raise ValueError("Sample record IDs must remain unique and in original order")
    if (ids < 0).any() or (ids >= counts["n_gold"]).any():
        raise ValueError("Sample record IDs do not belong to the recorded cohort")
    if not frame["y_obito"].isin([0, 1]).all():
        raise ValueError("The recorded target must be binary")
    for split, lower, upper in (
        ("train", 2020, 2022),
        ("val", 2023, 2023),
        ("test", 2024, 2024),
    ):
        mask = frame["split"] == split
        if (
            int(mask.sum()) != expected[split]
            or not frame.loc[mask, "ano_onset"].between(lower, upper).all()
        ):
            raise ValueError(f"Wrong size or onset years for {split}")
        if (
            split != "train"
            and int(frame.loc[mask, "y_obito"].sum())
            != counts["splits"][split]["obitos"]
        ):
            raise ValueError(f"Incomplete recorded evaluation outcomes for {split}")
    return frame


def _signed(document: dict, key: str) -> dict:
    return {**document, key: C.object_hash(document)}


def _verify(document: dict, key: str) -> None:
    if document.get(key) != C.object_hash(
        {name: value for name, value in document.items() if name != key}
    ):
        raise ValueError(f"Artifact integrity failure: {key}")


def _child(directory: Path, relative: str) -> Path:
    path = (directory / relative).resolve()
    if Path(relative).is_absolute() or directory not in path.parents:
        raise ValueError("Artifact paths must stay inside the study directory")
    return path


def _verify_file(directory: Path, artifact: dict) -> Path:
    path = _child(directory, artifact["path"])
    if C.file_hash(path) != artifact["sha256"]:
        raise ValueError("Artifact content hash mismatch")
    return path


def prepare_protocol(data_path: Path, output_dir: Path, threads: int = 4) -> dict:
    output_dir = C.external_directory(output_dir)
    if threads not in range(1, 5):
        raise ValueError("Use one through four threads")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Prepare requires a new or empty external directory")
    frame = load_sample(data_path)
    candidates, control = configurations()
    splits = {}
    for split in ("train", "val", "test"):
        mask = frame["split"] == split
        splits[split] = {"n": int(mask.sum())}
        if split != "test":
            splits[split]["events"] = int(frame.loc[mask, "y_obito"].sum())
    protocol = {
        "version": VERSION,
        "seed": SEED,
        "threads": threads,
        "source": {
            "basename": data_path.name,
            "sha256": C.file_hash(data_path),
        },
        "cohort_manifest_sha256": C.file_hash(
            ROOT / "modules/00-dataset/gold/counts.json"
        ),
        "code_sha256": source_hashes(),
        "versions": C._versions(),
        "features": list(C.M.FEATURES),
        "splits": splits,
        "training": "The same committed 200,000 real training records before any balancing; validation and test are complete and never resampled.",
        "strategies": list(STRATEGIES),
        "candidates": candidates,
        "original_control": control,
        "control_candidate_id": control["candidate_id"],
        "control_semantics": "Original five hyperparameter settings rebuilt with the explicitly versioned train-only phase-51 preprocessing; not asserted identical to the historical fitted binary or its metrics.",
        "selection": "Minimum unrounded 2023 validation log loss; exact ties by candidate_id. Select one finalist independently per strategy, then one winner across the four frozen finalists.",
        "budget": "The same thirty predeclared XGBoost configurations in each of four strategies. Each strategy is tuned independently; no inherited winning settings or prefix shortcuts.",
        "trial_order": "Original hyperparameter vector first in each arm; remaining vectors in the declared fixed JSON order.",
        "preprocessing": "Phase-51 train-only vocabulary and categorical splits; fit once per strategy and reuse its transformed train/validation inputs across independent estimator fits.",
        "probability_calibration": "Raw probabilities only; no recalibration. Diagnostic calibration metrics never modify predictions.",
        "test_status": "2024 was previously inspected. All four finalists and the fixed original-settings control are frozen before exploratory test comparison; test scores cannot change selection.",
        "threshold_metrics": "Threshold 0.5 is descriptive; candidate selection uses probabilities through log loss.",
        "scope": "A finite XGBoost-only sample study. It neither completes nor overwrites the interrupted full-training study, and does not silently replace the historical reference.",
    }
    protocol = _signed(protocol, "protocol_sha256")
    C.write_json(output_dir / "protocol.json", protocol)
    print(
        f"Sample-study protocol frozen: {len(candidates)} independent fits, none executed.",
        flush=True,
    )
    return protocol


def read_protocol(output_dir: Path, *, verify_sources: bool = True) -> dict:
    protocol = C.read_json(C.external_directory(output_dir) / "protocol.json")
    _verify(protocol, "protocol_sha256")
    if protocol["version"] != VERSION or protocol["features"] != list(C.M.FEATURES):
        raise ValueError("Unsupported sample-study contract")
    if verify_sources and (
        protocol["code_sha256"] != source_hashes()
        or protocol["versions"] != C._versions()
    ):
        raise ValueError("Frozen study source or runtime changed")
    if protocol["cohort_manifest_sha256"] != C.file_hash(
        ROOT / "modules/00-dataset/gold/counts.json"
    ):
        raise ValueError("The recorded cohort manifest changed")
    return protocol


def load_protocol(data_path: Path, output_dir: Path) -> dict:
    protocol = read_protocol(output_dir)
    if (
        C.file_hash(data_path) != protocol["source"]["sha256"]
        or protocol["source"]["sha256"] != _committed_sample_sha256()
    ):
        raise ValueError("Data no longer match the frozen committed sample")
    return protocol


def _result_path(directory: Path, spec: dict) -> Path:
    return directory / "trials" / spec["candidate_id"] / "result.json"


def completed(
    directory: Path, protocol: dict, spec: dict, *, audit_predictions: bool = False
) -> dict | None:
    path = _result_path(directory, spec)
    if not path.exists():
        return None
    result = C.read_json(path)
    if result.get("status") != "complete" or "result_sha256" not in result:
        return None
    _verify(result, "result_sha256")
    if result["protocol_sha256"] != protocol["protocol_sha256"]:
        raise ValueError("Trial belongs to another protocol")
    if any(
        result[key] != spec[key]
        for key in ("candidate_id", "family", "strategy", "params")
    ):
        raise ValueError("Trial configuration differs from the frozen candidate")
    if audit_predictions:
        path = _verify_file(directory, result["validation_predictions"])
        with np.load(path, allow_pickle=False) as saved:
            measured = C.compute_metrics(saved["y"], saved["p"])
        if C.object_hash(measured) != C.object_hash(result["validation"]):
            raise ValueError(
                "Validation metrics do not match their prediction checkpoint"
            )
        if measured["n"] != protocol["splits"]["val"]["n"]:
            raise ValueError("Validation checkpoint is incomplete")
    return result


def _model_artifact(directory: Path, model: Pipeline, path: str) -> dict:
    destination = _child(directory, path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    joblib.dump(model, temporary, compress=3)
    os.replace(temporary, destination)
    return {"path": path, "sha256": C.file_hash(destination)}


def _archive_unsigned(directory: Path, protocol: dict, spec: dict) -> None:
    """Preserve an interrupted phase-51 write before retrying its candidate.

    Phase 51 regards its own unsigned result as complete. Leaving it in the
    comparison list would make the retry tie itself and lose its model link.
    """
    path = _result_path(directory, spec)
    if not path.exists():
        return
    partial = C.read_json(path)
    if "result_sha256" in partial:
        return
    if partial.get("protocol_sha256") != protocol["protocol_sha256"] or any(
        partial.get(key) != spec[key]
        for key in ("candidate_id", "family", "strategy", "params")
    ):
        raise ValueError("Unsigned checkpoint does not belong to this candidate")
    archive = path.with_name(f"result.unsigned-{C.object_hash(partial)[:16]}.json")
    os.replace(path, archive)


def run_search(data_path: Path, output_dir: Path, strategy: str = "all") -> list[dict]:
    output_dir = C.external_directory(output_dir)
    protocol = load_protocol(data_path, output_dir)
    if (output_dir / "selection.json").exists():
        raise ValueError("Finalists are frozen; no additional search is allowed")
    if strategy not in (*STRATEGIES, "all"):
        raise ValueError("Unknown search strategy")
    frame = load_sample(data_path)
    train = frame.loc[frame["split"] == "train"].copy()
    val = frame.loc[frame["split"] == "val"].copy()
    del frame
    produced = []
    for arm in STRATEGIES if strategy == "all" else (strategy,):
        specs = [spec for spec in protocol["candidates"] if spec["strategy"] == arm]
        pending = [
            spec for spec in specs if completed(output_dir, protocol, spec) is None
        ]
        if not pending:
            print(f"Already complete: {arm}", flush=True)
            continue
        for spec in pending:
            _archive_unsigned(output_dir, protocol, spec)
        prepared = None
        if arm != "plain":
            print(f"Preparing {arm} from the same real sample", flush=True)
            with threadpool_limits(limits=protocol["threads"]):
                prepared = B.prepare_resampled_training(
                    train,
                    arm,
                    seed=protocol["seed"],
                    cache_dir=output_dir / "resampling-cache",
                )
        fitting_frame = train if prepared is None else prepared.frame
        fitting_y = train["y_obito"].to_numpy() if prepared is None else prepared.y
        audit = (
            {
                "strategy": "plain",
                "n": len(train),
                "events": int(train["y_obito"].sum()),
                "sampling": "none; unchanged committed training sample",
            }
            if prepared is None
            else prepared.audit
        )
        template = C.build_pipeline("xgb", pending[0]["params"], protocol["threads"])
        preprocessing = Pipeline(template.steps[:-1])
        started = time.perf_counter()
        with threadpool_limits(limits=protocol["threads"]):
            encoded_train = preprocessing.fit_transform(
                C.model_inputs(fitting_frame, "xgb"), fitting_y
            )
            encoded_val = preprocessing.transform(C.model_inputs(val, "xgb"))
        audit = {
            **audit,
            "preprocessing_fit_scope": "strategy training rows only",
            "preprocessing_reused_within_arm": True,
            "preprocessing_seconds": time.perf_counter() - started,
        }
        for spec in pending:
            params = (
                spec["params"]
                if prepared is None
                else B.effective_params(prepared, "xgb", spec["params"])
            )
            print(f"Fitting {arm} {spec['candidate_id']}", flush=True)
            started = time.perf_counter()
            with (
                warnings.catch_warnings(record=True) as caught,
                threadpool_limits(limits=protocol["threads"]),
            ):
                warnings.simplefilter("always")
                estimator = C.build_pipeline("xgb", params, protocol["threads"])[
                    "model"
                ]
                estimator.fit(encoded_train, fitting_y)
                messages = [str(item.message) for item in caught]
                if any(
                    issubclass(item.category, ConvergenceWarning) for item in caught
                ):
                    raise RuntimeError(
                        "Candidate did not converge: " + " | ".join(messages)
                    )
                probabilities = estimator.predict_proba(encoded_val)[:, 1]
                model = Pipeline(preprocessing.steps + [("model", estimator)])
            result = C._record_trial(
                model,
                audit,
                spec,
                protocol,
                output_dir,
                val,
                time.perf_counter() - started,
                messages,
                probabilities,
                C.compact_parameters(estimator, params),
            )
            if spec["candidate_id"] == protocol["original_control"]["candidate_id"]:
                result["control_artifact"] = _model_artifact(
                    output_dir, model, "control-original.joblib"
                )
            result = _signed(result, "result_sha256")
            C.write_json(_result_path(output_dir, spec), result)
            produced.append(result)
            del model, estimator
            gc.collect()
        del encoded_train, encoded_val, preprocessing, template, prepared
        gc.collect()
    rows = [
        row
        for spec in protocol["candidates"]
        if (row := completed(output_dir, protocol, spec)) is not None
    ]
    C.write_json(
        output_dir / "validation-results.json",
        {
            "protocol_sha256": protocol["protocol_sha256"],
            "status": "provisional until all four strategies finish",
            "candidates": rows,
        },
    )
    return produced


def _read_selection(directory: Path, protocol: dict) -> dict:
    selection = C.read_json(directory / "selection.json")
    _verify(selection, "selection_sha256")
    if selection["protocol_sha256"] != protocol["protocol_sha256"]:
        raise ValueError("Selection belongs to another protocol")
    _verify_file(directory, selection["canonical_model"])
    return selection


def finalize_selection(data_path: Path, output_dir: Path) -> dict:
    output_dir = C.external_directory(output_dir)
    protocol = load_protocol(data_path, output_dir)
    if (output_dir / "selection.json").exists():
        return _read_selection(output_dir, protocol)
    rows = [
        completed(output_dir, protocol, spec, audit_predictions=True)
        for spec in protocol["candidates"]
    ]
    if any(row is None for row in rows):
        raise ValueError(
            "All registered candidates must finish before freezing any finalists"
        )
    finalists = [
        min(
            (row for row in rows if row["strategy"] == arm),
            key=lambda row: (row["validation"]["logloss"], row["candidate_id"]),
        )
        for arm in STRATEGIES
    ]
    winner = min(
        finalists, key=lambda row: (row["validation"]["logloss"], row["candidate_id"])
    )
    control = next(
        row
        for row in rows
        if row["candidate_id"] == protocol["original_control"]["candidate_id"]
    )
    for row in finalists:
        if row["model_artifact"] is None:
            raise ValueError("A strategy finalist is missing its fitted checkpoint")
        _verify_file(output_dir, row["model_artifact"])
    _verify_file(output_dir, control["control_artifact"])
    destination = output_dir / "winner.joblib"
    shutil.copyfile(_verify_file(output_dir, winner["model_artifact"]), destination)
    selection = {
        "protocol_sha256": protocol["protocol_sha256"],
        "rule": protocol["selection"],
        "candidate_count": len(rows),
        "finalists": finalists,
        "control": control,
        "winner": winner,
        "canonical_model": {
            "path": destination.name,
            "sha256": C.file_hash(destination),
        },
        "prediction_interface": "srag_51_course_study.predict_probabilities(joblib.load(model), raw_forty_input_frame, 'xgb')",
        "test_used_for_selection": False,
        "probabilities_recalibrated": False,
        "finalists_frozen_before_test": True,
    }
    selection = _signed(selection, "selection_sha256")
    C.write_json(output_dir / "selection.json", selection)
    print(
        f"Four validation finalists frozen; selected {winner['strategy']} {winner['candidate_id']}",
        flush=True,
    )
    return selection


def evaluate_selected(data_path: Path, output_dir: Path) -> dict:
    output_dir = C.external_directory(output_dir)
    protocol = load_protocol(data_path, output_dir)
    selection = _read_selection(output_dir, protocol)
    report_path = output_dir / "test-evaluation.json"
    if report_path.exists():
        report = C.read_json(report_path)
        _verify(report, "evaluation_sha256")
        if report["selection_sha256"] != selection["selection_sha256"]:
            raise ValueError("Test comparison belongs to another frozen selection")
        return report
    frame = load_sample(data_path)
    test = frame.loc[frame["split"] == "test"]
    y = test["y_obito"].to_numpy(dtype=np.int8)
    records = {}
    for row in selection["finalists"] + [selection["control"]]:
        candidate_id = row["candidate_id"]
        if candidate_id in records:
            continue
        artifact = row["model_artifact"] or row.get("control_artifact")
        path = _verify_file(output_dir, artifact)
        prediction_path = output_dir / "test-predictions" / f"{candidate_id}.npz"
        prediction_path.parent.mkdir(parents=True, exist_ok=True)
        model = joblib.load(path)
        with threadpool_limits(limits=protocol["threads"]):
            p = C.predict_probabilities(model, test, "xgb")
        np.savez_compressed(prediction_path, y=y, p=p)
        records[candidate_id] = {
            "candidate_id": candidate_id,
            "family": "xgb",
            "strategy": row["strategy"],
            "test": C.compute_metrics(y, p),
            "predictions": {
                "path": str(prediction_path.relative_to(output_dir)),
                "sha256": C.file_hash(prediction_path),
            },
        }
        del model
        gc.collect()
    selected = records[selection["winner"]["candidate_id"]]
    root_predictions = output_dir / "test-predictions.npz"
    shutil.copyfile(_verify_file(output_dir, selected["predictions"]), root_predictions)
    report = {
        "protocol_sha256": protocol["protocol_sha256"],
        "selection_sha256": selection["selection_sha256"],
        "status": "exploratory; previously inspected temporal period",
        "canonical_model": selection["canonical_model"],
        "test": selected["test"],
        "test_predictions_sha256": C.file_hash(root_predictions),
        "finalists": [records[row["candidate_id"]] for row in selection["finalists"]],
        "control": records[selection["control"]["candidate_id"]],
        "selection_changed": False,
        "finalists_frozen_before_test": True,
    }
    report = _signed(report, "evaluation_sha256")
    C.write_json(report_path, report)
    print(
        "Exploratory test comparison saved; validation selection unchanged.", flush=True
    )
    return report


def project_evidence(output_dir: Path) -> dict:
    """Export audited aggregates only: no prediction arrays or model binaries."""
    directory = C.external_directory(output_dir)
    protocol = read_protocol(directory)
    rows = [
        row
        for spec in protocol["candidates"]
        if (row := completed(directory, protocol, spec, audit_predictions=True))
        is not None
    ]
    selection = None
    evaluation = None
    if (directory / "selection.json").exists():
        selection = _read_selection(directory, protocol)
        if len(rows) != len(protocol["candidates"]):
            raise ValueError("A selected study cannot contain unfinished candidates")
        expected_finalists = [
            min(
                (row for row in rows if row["strategy"] == arm),
                key=lambda row: (row["validation"]["logloss"], row["candidate_id"]),
            )
            for arm in STRATEGIES
        ]
        if C.object_hash(expected_finalists) != C.object_hash(selection["finalists"]):
            raise ValueError("Frozen finalists differ from their validation minima")
        expected_winner = min(
            expected_finalists,
            key=lambda row: (row["validation"]["logloss"], row["candidate_id"]),
        )
        if C.object_hash(expected_winner) != C.object_hash(selection["winner"]):
            raise ValueError("The selected model differs from the validation minimum")
        expected_control = next(
            row
            for row in rows
            if row["candidate_id"] == protocol["original_control"]["candidate_id"]
        )
        if C.object_hash(expected_control) != C.object_hash(selection["control"]):
            raise ValueError(
                "Original-settings control differs from its recorded candidate"
            )
    if (directory / "test-evaluation.json").exists():
        evaluation = C.read_json(directory / "test-evaluation.json")
        _verify(evaluation, "evaluation_sha256")
        if (
            selection is None
            or evaluation["selection_sha256"] != selection["selection_sha256"]
            or evaluation["protocol_sha256"] != protocol["protocol_sha256"]
            or evaluation["canonical_model"] != selection["canonical_model"]
        ):
            raise ValueError("Test comparison does not belong to this frozen selection")
        if (
            evaluation["selection_changed"]
            or not evaluation["finalists_frozen_before_test"]
        ):
            raise ValueError("Test comparison cannot alter the validation choice")
        expected_ids = [row["candidate_id"] for row in selection["finalists"]]
        if [
            row["candidate_id"] for row in evaluation["finalists"]
        ] != expected_ids or evaluation["control"]["candidate_id"] != selection[
            "control"
        ]["candidate_id"]:
            raise ValueError("Test comparison contains an unfrozen finalist")
        for row in evaluation["finalists"] + [evaluation["control"]]:
            with np.load(
                _verify_file(directory, row["predictions"]), allow_pickle=False
            ) as saved:
                measured = C.compute_metrics(saved["y"], saved["p"])
            if (
                C.object_hash(measured) != C.object_hash(row["test"])
                or measured["n"] != protocol["splits"]["test"]["n"]
            ):
                raise ValueError(
                    "Test metrics differ from their complete prediction checkpoint"
                )
        root_path = directory / "test-predictions.npz"
        if C.file_hash(root_path) != evaluation["test_predictions_sha256"]:
            raise ValueError("Canonical test prediction checkpoint changed")
        with np.load(root_path, allow_pickle=False) as saved:
            measured = C.compute_metrics(saved["y"], saved["p"])
        if C.object_hash(measured) != C.object_hash(evaluation["test"]):
            raise ValueError("Canonical test metrics differ from predictions")
    return {
        "status": "complete" if evaluation else "selected" if selection else "running",
        "execution": None,
        "adoption": "Separate sample-search version; historical model and interrupted full-data study remain preserved.",
        "protocol": protocol,
        "validation_candidates": rows,
        "selection": selection,
        "evaluation": evaluation,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, help="Aggregate JSON destination for --export"
    )
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--strategy", choices=(*STRATEGIES, "all"), default="all")
    stages = parser.add_mutually_exclusive_group(required=True)
    for name in ("prepare", "search", "finalize", "evaluate", "export"):
        stages.add_argument(f"--{name}", action="store_true")
    args = parser.parse_args()
    if args.export:
        if args.output is None:
            parser.error("--export requires --output")
        evidence = project_evidence(args.output_dir)
        C.write_json(args.output, evidence)
        print(f"Aggregate sample-study evidence: {evidence['status']}", flush=True)
        return
    if args.data is None:
        parser.error("This stage requires --data")
    if args.prepare:
        prepare_protocol(args.data, args.output_dir, args.threads)
    elif args.search:
        run_search(args.data, args.output_dir, args.strategy)
    elif args.finalize:
        finalize_selection(args.data, args.output_dir)
    else:
        evaluate_selected(args.data, args.output_dir)


if __name__ == "__main__":
    main()
