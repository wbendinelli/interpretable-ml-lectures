"""Versioned full-training study; never changes the historical course model.

Run --prepare first, then --plain, --balance, --finalize and --evaluate.
All stages require --data and an explicit --output-dir outside the repository.
Only --evaluate computes test predictions, after the validation choice is frozen.
The test period was previously inspected: its evaluation remains exploratory.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import shutil
import time
import warnings
from functools import partial
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import srag_50_selection as S
import srag_60_model as M
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)
from sklearn.model_selection import ParameterGrid, ParameterSampler
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    FunctionTransformer,
    OneHotEncoder,
    OrdinalEncoder,
    StandardScaler,
)
from sklearn.tree import DecisionTreeClassifier
from threadpoolctl import threadpool_limits
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parent.parent
VERSION = "course-full-logloss-v2"
SEED = 42
STRATEGIES = ("weights", "rus", "smotenc_restricted")
BALANCED_FAMILIES = ("logit", "xgb")
PACKAGES = ("numpy", "pandas", "scikit-learn", "xgboost", "imbalanced-learn", "joblib")


def json_ready(value):
    """Normalize NumPy scalars without serializing estimators or callbacks."""
    if isinstance(value, np.generic):
        return json_ready(value.item())
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [json_ready(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"Unsupported study metadata type: {type(value).__name__}")


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        json_ready(value), sort_keys=True, ensure_ascii=False, allow_nan=False
    ).encode()


def object_hash(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(
            json_ready(value),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def external_directory(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        raise ValueError("Study artifacts must be written outside the repository")
    return resolved


def model_inputs(frame: pd.DataFrame, family: str | None = None) -> pd.DataFrame:
    """Every fitted pipeline receives the same raw forty-column input contract."""
    if family is not None and family not in S.MODELOS:
        raise ValueError(f"Unknown family: {family}")
    missing = set(M.FEATURES) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing model inputs: {sorted(missing)}")
    return frame.loc[:, list(M.FEATURES)]


def _week_transform(function) -> Pipeline:
    return Pipeline(
        [
            (
                "radians",
                FunctionTransformer(
                    partial(np.multiply, 2 * np.pi / 52.0), validate=True
                ),
            ),
            ("periodic", FunctionTransformer(function, validate=True)),
        ]
    )


def build_pipeline(family: str, params: dict, threads: int = 4) -> Pipeline:
    """Fit vocabulary, imputation and scaling only through Pipeline.fit(train)."""
    numeric = list(M.NUMERICAS + M.BOOLEANAS)
    categories = list(M.CATEGORICAS)
    if family == "dummy":
        return Pipeline(
            [
                (
                    "prepare",
                    ColumnTransformer([("age", "passthrough", ["idade_anos"])]),
                ),
                ("model", DummyClassifier(**params)),
            ]
        )
    if family == "xgb":
        prepare = ColumnTransformer(
            [
                (
                    "numeric",
                    FunctionTransformer(np.asarray, kw_args={"dtype": np.float32}),
                    numeric,
                ),
                (
                    "categorical",
                    OrdinalEncoder(
                        handle_unknown="use_encoded_value",
                        unknown_value=np.nan,
                        encoded_missing_value=np.nan,
                        dtype=np.float32,
                    ),
                    categories,
                ),
            ],
            sparse_threshold=0.0,
        )
        fixed = {
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "tree_method": "hist",
            "enable_categorical": True,
            "feature_types": ["q"] * len(numeric) + ["c"] * len(categories),
            "subsample": 1.0,
            "colsample_bytree": 1.0,
            "random_state": SEED,
            "n_jobs": threads,
        }
        model = XGBClassifier(**(fixed | params))
        return Pipeline([("prepare", prepare), ("model", model)])

    linear = family in ("lpm", "logit")
    numeric_columns = [col for col in numeric if not linear or col != "semana_epi"]
    transformers = [
        ("numeric", SimpleImputer(strategy="median"), numeric_columns),
        (
            "categorical",
            OneHotEncoder(
                drop="first" if linear else None,
                handle_unknown="ignore",
                sparse_output=True,
                dtype=np.float64,
            ),
            categories,
        ),
    ]
    if linear:
        transformers.extend(
            [
                ("week_sin", _week_transform(np.sin), ["semana_epi"]),
                ("week_cos", _week_transform(np.cos), ["semana_epi"]),
            ]
        )
    prepare = ColumnTransformer(transformers, sparse_threshold=1.0)
    steps = [("prepare", prepare)]
    if linear:
        steps.append(("scale", StandardScaler(with_mean=False)))
    if family == "lpm":
        model = LinearRegression(n_jobs=threads, **params)
    elif family == "logit":
        model = LogisticRegression(
            max_iter=2000, solver="lbfgs", l1_ratio=0.0, **params
        )
    elif family == "arvore":
        model = DecisionTreeClassifier(random_state=SEED, **params)
    elif family == "floresta":
        model = RandomForestClassifier(
            n_estimators=300,
            bootstrap=True,
            random_state=SEED,
            n_jobs=threads,
            **params,
        )
    else:
        raise ValueError(f"Unknown family: {family}")
    return Pipeline(steps + [("model", model)])


def predict_probabilities(
    model: Pipeline, frame: pd.DataFrame, family: str
) -> np.ndarray:
    x = model_inputs(frame, family)
    if family == "lpm":
        p = np.clip(model.predict(x), 1e-6, 1 - 1e-6)
    else:
        p = model.predict_proba(x)[:, 1]
    p = np.asarray(p, dtype=np.float64)
    if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("Invalid predicted probabilities")
    return p


def compact_parameters(estimator, explicit: dict) -> dict:
    """Record numerical controls and relevant defaults, never callback objects."""
    keys = (
        "objective",
        "eval_metric",
        "tree_method",
        "enable_categorical",
        "subsample",
        "colsample_bytree",
        "n_jobs",
        "random_state",
        "max_iter",
        "solver",
        "l1_ratio",
        "n_estimators",
        "bootstrap",
        "early_stopping_rounds",
        "class_weight",
        "scale_pos_weight",
        "strategy",
    )
    actual = estimator.get_params(deep=False)
    return json_ready({key: actual[key] for key in keys if key in actual} | explicit)


def compute_metrics(y: np.ndarray, probabilities: np.ndarray) -> dict:
    """No rounding before selection; calibration bins are diagnostics only."""
    y = np.asarray(y, dtype=np.int8)
    p = np.asarray(probabilities, dtype=np.float64)
    if y.shape != p.shape or set(np.unique(y)) != {0, 1}:
        raise ValueError("Metrics require aligned outcomes containing both classes")
    bins = np.clip(np.digitize(p, np.linspace(0, 1, 11)[1:-1]), 0, 9)
    reliability = []
    for index in range(10):
        mask = bins == index
        if mask.any():
            reliability.append(
                {
                    "bin": index,
                    "n": int(mask.sum()),
                    "mean_predicted": float(p[mask].mean()),
                    "observed": float(y[mask].mean()),
                }
            )
    positive, predicted = y == 1, p >= 0.5
    tp, fp = int((positive & predicted).sum()), int((~positive & predicted).sum())
    tn, fn = int((~positive & ~predicted).sum()), int((positive & ~predicted).sum())
    return {
        "n": len(y),
        "events": int(y.sum()),
        "logloss": float(log_loss(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "auc": float(roc_auc_score(y, p)),
        "ap": float(average_precision_score(y, p)),
        "mean_predicted": float(p.mean()),
        "observed": float(y.mean()),
        "calibration_gap": float(p.mean() - y.mean()),
        "ece_10_equal_width": float(
            sum(
                row["n"] * abs(row["mean_predicted"] - row["observed"])
                for row in reliability
            )
            / len(y)
        ),
        "reliability": reliability,
        "threshold": 0.5,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "sensitivity": tp / (tp + fn),
        "specificity": tn / (tn + fp),
        "precision": tp / (tp + fp) if tp + fp else None,
    }


def plain_configurations() -> list[dict]:
    configurations = []
    for family in S.MODELOS:
        space = S.ESPACOS[family]
        grid = list(ParameterGrid(space)) if space else [{}]
        if len(grid) > S.N_ITER[family]:
            grid = list(ParameterSampler(space, S.N_ITER[family], random_state=SEED))
        for params in sorted(grid, key=lambda value: canonical_bytes(value)):
            configurations.append(
                {"family": family, "strategy": "plain", "params": params}
            )
    return configurations


def balance_configurations() -> list[dict]:
    helper = importlib.import_module("srag_52_course_balance")
    configurations = []
    for strategy in STRATEGIES:
        for family in BALANCED_FAMILIES:
            choices = helper.candidate_specs(family, strategy)
            if len(choices) != S.N_ITER[family]:
                raise ValueError(
                    "Balancing must reuse the family's complete registered plain budget"
                )
            configurations.extend(
                {"family": family, "strategy": strategy, "params": params}
                for params in choices
            )
    return configurations


def _versions() -> dict:
    return {
        "python": platform.python_version(),
        **{package: importlib.metadata.version(package) for package in PACKAGES},
    }


def _source_hashes() -> dict:
    names = (
        "srag_30_silver.py",
        "srag_40_gold.py",
        "srag_50_selection.py",
        "srag_51_course_study.py",
        "srag_52_course_balance.py",
        "srag_60_model.py",
        "srag_61_balance.py",
    )
    return {
        **{name: file_hash(ROOT / "tools" / name) for name in names},
        "requirements.lock": file_hash(ROOT / "requirements.lock"),
    }


def _load(data_path: Path) -> pd.DataFrame:
    frame = M.load_gold(data_path)
    if set(frame["split"].astype(str).unique()) != {"train", "val", "test"}:
        raise ValueError("The temporal data must contain train, val and test")
    if not frame["y_obito"].isin([0, 1]).all():
        raise ValueError("The recorded target must be binary")
    if "ano_onset" not in frame:
        raise ValueError("The temporal audit requires ano_onset")
    expected = read_json(ROOT / "modules/00-dataset/gold/counts.json")
    if len(frame) != expected["n_gold"]:
        raise ValueError(
            "This full-cohort study does not accept the historical training sample"
        )
    if "gold_id" not in frame or not np.array_equal(
        frame["gold_id"].to_numpy(), np.arange(len(frame))
    ):
        raise ValueError("Full Gold records must retain unique, complete gold_id order")
    for split, lower, upper in (
        ("train", 2020, 2022),
        ("val", 2023, 2023),
        ("test", 2024, 2024),
    ):
        mask = frame["split"] == split
        years = frame.loc[mask, "ano_onset"]
        if not years.between(lower, upper).all():
            raise ValueError(f"Unexpected onset year in {split}")
        recorded = expected["splits"][split]
        if (
            int(mask.sum()) != recorded["n"]
            or int(frame.loc[mask, "y_obito"].sum()) != recorded["obitos"]
        ):
            raise ValueError(
                f"Full Gold counts/outcomes differ from the recorded cohort: {split}"
            )
    return frame


def prepare_protocol(data_path: Path, output_dir: Path, threads: int = 4) -> dict:
    """Freeze the complete candidate list and all selection rules before fitting."""
    output_dir = external_directory(output_dir)
    if threads < 1 or threads > 4:
        raise ValueError("This study is bounded to one through four threads")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Prepare requires a new or empty output directory")
    frame = _load(data_path)
    splits = {}
    for split in ("train", "val", "test"):
        mask = frame["split"] == split
        splits[split] = {"n": int(mask.sum())}
        if split != "test":
            splits[split]["events"] = int(frame.loc[mask, "y_obito"].sum())
    configurations = plain_configurations() + balance_configurations()
    for spec in configurations:
        spec["candidate_id"] = object_hash(spec)[:16]
    protocol = {
        "version": VERSION,
        "seed": SEED,
        "threads": threads,
        "source": {"basename": data_path.name, "sha256": file_hash(data_path)},
        "cohort_manifest_sha256": file_hash(
            ROOT / "modules/00-dataset/gold/counts.json"
        ),
        "code_sha256": _source_hashes(),
        "versions": _versions(),
        "features": list(M.FEATURES),
        "splits": splits,
        "training": "All eligible train records; only registered balancing strategies resample training.",
        "selection": "Minimum unrounded 2023 validation log loss across every registered candidate; exact ties by candidate_id.",
        "test_status": "2024 was previously inspected; no test predictions in search, selection or calibration. Later test evaluation is exploratory.",
        "preprocessing": "All learned preprocessing is fitted only on each candidate's training data; all pipelines receive the same forty raw inputs.",
        "xgb_encoding": "Train-fitted ordinal codes declared categorical to XGBoost; unknown evaluation categories become missing. Numeric missing values remain native.",
        "linear_encoding": "Train-fitted one-hot (drop first), median imputation and sparse-compatible scaling; deterministic week sine/cosine inside pipeline.",
        "tree_encoding": "Train-fitted full one-hot and median imputation; ordinal week.",
        "probability_calibration": "No post-fit recalibration; reliability bins and calibration diagnostics never modify predictions.",
        "lpm_probability_rule": "Clip raw linear predictions to [1e-6, 1-1e-6] only when scoring probabilities.",
        "threshold_metrics": "Threshold 0.5 is descriptive only and never used for candidate selection.",
        "search_scope": "Historical finite configuration lists reused; no claim of exhaustive family optimality. No early stopping.",
        "candidates": configurations,
    }
    protocol["protocol_sha256"] = object_hash(protocol)
    write_json(output_dir / "protocol.json", protocol)
    print(
        f"Protocol frozen: {len(configurations)} candidates; no model fitted.",
        flush=True,
    )
    return protocol


def load_protocol(data_path: Path, output_dir: Path) -> dict:
    protocol = read_json(external_directory(output_dir) / "protocol.json")
    recorded_hash = protocol["protocol_sha256"]
    if (
        object_hash(
            {key: value for key, value in protocol.items() if key != "protocol_sha256"}
        )
        != recorded_hash
    ):
        raise ValueError("The frozen protocol was modified")
    if file_hash(data_path) != protocol["source"]["sha256"]:
        raise ValueError("Dataset content differs from the frozen protocol")
    if (
        file_hash(ROOT / "modules/00-dataset/gold/counts.json")
        != protocol["cohort_manifest_sha256"]
    ):
        raise ValueError(
            "The recorded cohort manifest differs from the frozen protocol"
        )
    if (
        _versions() != protocol["versions"]
        or _source_hashes() != protocol["code_sha256"]
    ):
        raise ValueError("Runtime or study source differs from the frozen protocol")
    return protocol


def _result_path(output_dir: Path, spec: dict) -> Path:
    return output_dir / "trials" / spec["candidate_id"] / "result.json"


def _completed(output_dir: Path, protocol: dict, spec: dict) -> dict | None:
    path = _result_path(output_dir, spec)
    if not path.exists():
        return None
    result = read_json(path)
    if result.get("status") != "complete":
        return None
    if (
        result["protocol_sha256"] != protocol["protocol_sha256"]
        or result["candidate_id"] != spec["candidate_id"]
    ):
        raise ValueError("Candidate checkpoint does not match the protocol")
    return result


def _record_trial(
    model,
    train_audit: dict,
    spec: dict,
    protocol: dict,
    output_dir: Path,
    val: pd.DataFrame,
    elapsed: float,
    warning_messages: list[str],
    probabilities: np.ndarray | None = None,
    effective_params: dict | None = None,
) -> dict:
    p = (
        predict_probabilities(model, val, spec["family"])
        if probabilities is None
        else probabilities
    )
    metrics = compute_metrics(val["y_obito"].to_numpy(), p)
    group = f"{spec['strategy']}--{spec['family']}"
    earlier = [
        _completed(output_dir, protocol, other)
        for other in protocol["candidates"]
        if other["strategy"] == spec["strategy"] and other["family"] == spec["family"]
    ]
    earlier = [row for row in earlier if row is not None]
    best_score = (
        min((row["validation"]["logloss"], row["candidate_id"]) for row in earlier)
        if earlier
        else (float("inf"), "")
    )
    artifact = None
    if (metrics["logloss"], spec["candidate_id"]) < best_score:
        model_path = (
            output_dir / "checkpoints" / group / f"{spec['candidate_id']}.joblib"
        )
        model_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = model_path.with_suffix(".joblib.tmp")
        joblib.dump(model, temporary, compress=3)
        os.replace(temporary, model_path)
        artifact = {
            "path": str(model_path.relative_to(output_dir)),
            "sha256": file_hash(model_path),
        }
    trial_dir = _result_path(output_dir, spec).parent
    trial_dir.mkdir(parents=True, exist_ok=True)
    prediction_path = trial_dir / "validation-predictions.npz"
    np.savez_compressed(prediction_path, y=val["y_obito"].to_numpy(dtype=np.int8), p=p)
    result = {
        **spec,
        "protocol_sha256": protocol["protocol_sha256"],
        "status": "complete",
        "training": train_audit,
        "effective_params": spec["params"]
        if effective_params is None
        else effective_params,
        "validation": metrics,
        "fit_seconds": elapsed,
        "fit_warnings": warning_messages,
        "model_artifact": artifact,
        "validation_predictions": {
            "path": str(prediction_path.relative_to(output_dir)),
            "sha256": file_hash(prediction_path),
        },
    }
    write_json(_result_path(output_dir, spec), result)
    print(
        f"Completed {group} {spec['candidate_id']}: validation log loss={metrics['logloss']:.6f}; fit={elapsed:.1f}s",
        flush=True,
    )
    return result


def run_stage(data_path: Path, output_dir: Path, stage: str) -> list[dict]:
    output_dir = external_directory(output_dir)
    protocol = load_protocol(data_path, output_dir)
    if (output_dir / "selection.json").exists():
        raise ValueError("The selection is frozen; search cannot continue")
    if stage not in ("plain", "balance"):
        raise ValueError("Search stage must be plain or balance")
    frame = _load(data_path)
    train = frame.loc[frame["split"] == "train"].copy()
    val = frame.loc[frame["split"] == "val"].copy()
    del frame
    helper = (
        importlib.import_module("srag_52_course_balance")
        if stage == "balance"
        else None
    )
    completed = []
    strategies = ("plain",) if stage == "plain" else STRATEGIES
    for strategy in strategies:
        specs = [
            spec for spec in protocol["candidates"] if spec["strategy"] == strategy
        ]
        pending = [
            spec for spec in specs if _completed(output_dir, protocol, spec) is None
        ]
        if not pending:
            print(f"Already complete: {strategy}", flush=True)
            continue
        prepared = None
        if helper is not None:
            print(f"Preparing full training strategy: {strategy}", flush=True)
            with threadpool_limits(limits=protocol["threads"]):
                prepared = helper.prepare_resampled_training(
                    train,
                    strategy,
                    seed=protocol["seed"],
                    cache_dir=output_dir / "resampling-cache",
                )
        families = tuple(dict.fromkeys(spec["family"] for spec in pending))
        for family in families:
            family_specs = [spec for spec in pending if spec["family"] == family]
            fitting_frame = train if prepared is None else prepared.frame
            fitting_y = train["y_obito"].to_numpy() if prepared is None else prepared.y
            audit = (
                {
                    "strategy": "plain",
                    "n": len(train),
                    "events": int(train["y_obito"].sum()),
                    "sampling": "none; all eligible temporal training rows",
                }
                if prepared is None
                else prepared.audit
            )
            first_params = family_specs[0]["params"]
            if prepared is not None:
                first_params = helper.effective_params(prepared, family, first_params)
            template = build_pipeline(family, first_params, protocol["threads"])
            preprocessing = Pipeline(template.steps[:-1])
            print(
                f"Fitting train-only preprocessing once: {strategy}/{family}",
                flush=True,
            )
            preprocessing_started = time.perf_counter()
            with threadpool_limits(limits=protocol["threads"]):
                encoded_train = preprocessing.fit_transform(
                    model_inputs(fitting_frame, family), fitting_y
                )
                encoded_val = preprocessing.transform(model_inputs(val, family))
            preprocessing_seconds = time.perf_counter() - preprocessing_started
            audit = {
                **audit,
                "preprocessing_fit_scope": "candidate training rows only",
                "preprocessing_reused_within_arm": True,
                "preprocessing_seconds": preprocessing_seconds,
            }
            for spec in family_specs:
                effective = (
                    spec["params"]
                    if prepared is None
                    else helper.effective_params(prepared, family, spec["params"])
                )
                print(f"Fitting {strategy}/{family} {spec['candidate_id']}", flush=True)
                started = time.perf_counter()
                with (
                    warnings.catch_warnings(record=True) as caught,
                    threadpool_limits(limits=protocol["threads"]),
                ):
                    warnings.simplefilter("always")
                    estimator = build_pipeline(family, effective, protocol["threads"])[
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
                    if family == "lpm":
                        probabilities = np.clip(
                            estimator.predict(encoded_val), 1e-6, 1 - 1e-6
                        )
                    else:
                        probabilities = estimator.predict_proba(encoded_val)[:, 1]
                    model = Pipeline(preprocessing.steps + [("model", estimator)])
                completed.append(
                    _record_trial(
                        model,
                        audit,
                        spec,
                        protocol,
                        output_dir,
                        val,
                        time.perf_counter() - started,
                        messages,
                        probabilities,
                        compact_parameters(estimator, effective),
                    )
                )
                del model, estimator
                gc.collect()
            del encoded_train, encoded_val, preprocessing, template
            gc.collect()
        del prepared
        gc.collect()
    rows = [
        row
        for spec in protocol["candidates"]
        if (row := _completed(output_dir, protocol, spec)) is not None
    ]
    write_json(
        output_dir / "validation-results.json",
        {
            "protocol_sha256": protocol["protocol_sha256"],
            "status": "provisional until every registered candidate completes",
            "candidates": rows,
        },
    )
    return completed


def finalize_selection(data_path: Path, output_dir: Path) -> dict:
    output_dir = external_directory(output_dir)
    protocol = load_protocol(data_path, output_dir)
    selection_path = output_dir / "selection.json"
    if selection_path.exists():
        return read_json(selection_path)
    rows = [_completed(output_dir, protocol, spec) for spec in protocol["candidates"]]
    if any(row is None for row in rows):
        raise ValueError(
            "Every registered plain and balanced candidate must finish before selection"
        )
    winner = min(
        rows, key=lambda row: (row["validation"]["logloss"], row["candidate_id"])
    )
    artifact = winner["model_artifact"]
    if (
        artifact is None
        or file_hash(output_dir / artifact["path"]) != artifact["sha256"]
    ):
        raise ValueError(
            "The selected candidate's fitted artifact is missing or changed"
        )
    destination = output_dir / "winner.joblib"
    shutil.copyfile(output_dir / artifact["path"], destination)
    selection = {
        "protocol_sha256": protocol["protocol_sha256"],
        "rule": protocol["selection"],
        "candidate_count": len(rows),
        "winner": winner,
        "canonical_model": {"path": destination.name, "sha256": file_hash(destination)},
        "prediction_interface": "srag_51_course_study.predict_probabilities(joblib.load(model), raw_forty_input_frame, winner_family)",
        "test_used_for_selection": False,
        "probabilities_recalibrated": False,
    }
    selection["selection_sha256"] = object_hash(selection)
    write_json(selection_path, selection)
    print(
        f"Selection frozen: {winner['strategy']}/{winner['family']} {winner['candidate_id']}",
        flush=True,
    )
    return selection


def evaluate_selected(data_path: Path, output_dir: Path) -> dict:
    output_dir = external_directory(output_dir)
    protocol = load_protocol(data_path, output_dir)
    selection = read_json(output_dir / "selection.json")
    if (
        selection["protocol_sha256"] != protocol["protocol_sha256"]
        or object_hash(
            {
                key: value
                for key, value in selection.items()
                if key != "selection_sha256"
            }
        )
        != selection["selection_sha256"]
    ):
        raise ValueError("The frozen selection was modified")
    model_path = output_dir / selection["canonical_model"]["path"]
    if file_hash(model_path) != selection["canonical_model"]["sha256"]:
        raise ValueError("The canonical fitted model was modified")
    report_path = output_dir / "test-evaluation.json"
    if report_path.exists():
        report = read_json(report_path)
        if report["selection_sha256"] != selection["selection_sha256"]:
            raise ValueError("Test report belongs to another selection")
        return report
    frame = _load(data_path)
    test = frame.loc[frame["split"] == "test"]
    model = joblib.load(model_path)
    with threadpool_limits(limits=protocol["threads"]):
        p = predict_probabilities(model, test, selection["winner"]["family"])
    y = test["y_obito"].to_numpy(dtype=np.int8)
    np.savez_compressed(output_dir / "test-predictions.npz", y=y, p=p)
    report = {
        "protocol_sha256": protocol["protocol_sha256"],
        "selection_sha256": selection["selection_sha256"],
        "status": "exploratory; previously inspected temporal period",
        "canonical_model": selection["canonical_model"],
        "test": compute_metrics(y, p),
        "test_predictions_sha256": file_hash(output_dir / "test-predictions.npz"),
        "selection_changed": False,
    }
    write_json(report_path, report)
    print(
        f"Exploratory temporal test log loss={report['test']['logloss']:.6f}",
        flush=True,
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--threads", type=int, default=4, help="Frozen at --prepare; maximum four"
    )
    stages = parser.add_mutually_exclusive_group(required=True)
    for stage in ("prepare", "plain", "balance", "finalize", "evaluate"):
        stages.add_argument(f"--{stage}", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        prepare_protocol(args.data, args.output_dir, args.threads)
    elif args.plain or args.balance:
        run_stage(args.data, args.output_dir, "plain" if args.plain else "balance")
    elif args.finalize:
        finalize_selection(args.data, args.output_dir)
    else:
        evaluate_selected(args.data, args.output_dir)


if __name__ == "__main__":
    main()
