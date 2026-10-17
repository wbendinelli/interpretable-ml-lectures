"""Training-only balancing arms for the new full-cohort course study.

This module never receives evaluation labels and never replaces the historical
course model. The caller fits and selects candidates on its declared temporal
protocol. All probabilities remain raw: there is no fitted recalibrator here.

The restricted SMOTENC implementation is the audited historical sampler from
``srag_61_balance``. Its exact nearest-neighbour preparation can be expensive on
the full training cohort, so a verified external cache is shared by all fits.
An interrupted preparation leaves no complete cache manifest.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import srag_60_model as M

ROOT = Path(__file__).resolve().parent.parent
STRATEGIES = ("weights", "rus", "smotenc_restricted")
SAMPLER_PROTOCOL = "2026-10-16-full-raw-matched-search-v1"
DIAGNOSTIC_THRESHOLD = 0.5
ALIASES = {
    "pesos": "weights",
    "reducao": "rus",
    "smotenc_restrito": "smotenc_restricted",
}

FAMILIES = ("logit", "xgb")


@dataclass
class PreparedTraining:
    """Only predictor values and training labels; no evaluation partition."""

    frame: pd.DataFrame
    y: np.ndarray
    strategy: str
    seed: int
    audit: dict


def _strategy(value: str) -> str:
    name = ALIASES.get(value, value)
    if name not in STRATEGIES:
        raise ValueError(f"Unknown balancing strategy: {value!r}")
    return name


def _assert_training_frame(train: pd.DataFrame) -> None:
    required = set(M.FEATURES) | {"split", "ano_onset", "y_obito", "gold_id"}
    if missing := required - set(train):
        raise ValueError(f"Training frame lacks required columns: {sorted(missing)}")
    if train.empty or not train["split"].eq("train").all():
        raise ValueError("Balancing accepts only nonempty split=train records")
    if not train["ano_onset"].between(2020, 2022).all():
        raise ValueError("Training onset years must be 2020 through 2022")
    if not train["gold_id"].is_unique:
        raise ValueError("Training gold_id values must be unique")
    if set(train["y_obito"].unique()) != {0, 1}:
        raise ValueError("Training labels must contain both binary outcome classes")


def _fingerprint(frame: pd.DataFrame) -> str:
    hashed = pd.util.hash_pandas_object(frame, index=True).to_numpy()
    return hashlib.sha256(hashed.tobytes()).hexdigest()


def _label_fingerprint(y: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(y, dtype="int8").tobytes()).hexdigest()


def _versions() -> dict[str, str]:
    return {
        package: importlib.metadata.version(package)
        for package in ("numpy", "pandas", "scipy", "scikit-learn", "imbalanced-learn")
    }


def _sampler_sources() -> dict[str, str]:
    """Invalidate standalone caches when calendar or sampling rules change."""
    return {
        name: hashlib.sha256((ROOT / "tools" / name).read_bytes()).hexdigest()
        for name in (
            "srag_30_silver.py",
            "srag_52_course_balance.py",
            "srag_61_balance.py",
        )
    }


def _counts(y: np.ndarray) -> dict:
    positives = int(np.sum(y == 1))
    return {
        "n": len(y),
        "positives": positives,
        "negatives": int(np.sum(y == 0)),
        "event_fraction": positives / len(y),
    }


def _cache_path(cache_dir: Path | None, signature: dict) -> Path | None:
    if cache_dir is None:
        return None
    directory = Path(cache_dir).expanduser().resolve()
    if directory == ROOT or ROOT in directory.parents:
        raise ValueError("Training caches must be written outside the repository")
    key = hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()
    return directory / f"{signature['strategy']}-{key[:20]}"


def _read_cache(directory: Path | None, signature: dict) -> PreparedTraining | None:
    if directory is None or not (directory / "manifest.json").exists():
        return None
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest["signature"] != signature:
        raise RuntimeError("Training cache signature does not match the input")
    for name, expected in manifest["file_sha256"].items():
        actual = hashlib.sha256((directory / name).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"Training cache integrity failure: {name}")
    frame = pd.read_parquet(directory / "features.parquet")
    y = np.load(directory / "labels.npy", allow_pickle=False)
    if list(frame) != list(M.FEATURES) or len(frame) != len(y):
        raise RuntimeError("Training cache schema or row counts do not match")
    if _fingerprint(frame) != manifest["frame_fingerprint"]:
        raise RuntimeError("Training cache predictor fingerprint does not match")
    if _label_fingerprint(y) != manifest["label_fingerprint"]:
        raise RuntimeError("Training cache label fingerprint does not match")
    return PreparedTraining(
        frame=frame,
        y=y,
        strategy=signature["strategy"],
        seed=signature["seed"],
        audit=manifest["audit"],
    )


def _write_cache(
    directory: Path | None, signature: dict, data: PreparedTraining
) -> None:
    if directory is None:
        return
    directory.mkdir(parents=True, exist_ok=True)
    # A manifest appears only after both payloads are complete. Partial files
    # are never treated as a successful preparation on a resumed execution.
    feature_temp = directory / "features.partial.parquet"
    label_temp = directory / "labels.partial.npy"
    data.frame.to_parquet(feature_temp, index=False, compression="zstd")
    np.save(label_temp, data.y, allow_pickle=False)
    feature_temp.replace(directory / "features.parquet")
    label_temp.replace(directory / "labels.npy")
    names = ("features.parquet", "labels.npy")
    manifest = {
        "signature": signature,
        "audit": data.audit,
        "frame_fingerprint": _fingerprint(data.frame),
        "label_fingerprint": _label_fingerprint(data.y),
        "file_sha256": {
            name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
            for name in names
        },
    }
    temporary = directory / "manifest.partial.json"
    temporary.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(directory / "manifest.json")


def candidate_specs(family: str, strategy: str, *, seed: int = 42) -> list[dict]:
    """Mirror the reference-family search budget and sampled configurations.

    The same parameter candidates are offered to every balancing strategy;
    each strategy is selected independently by the caller's validation loss.
    This preserves the historical search spaces without inheriting their
    AUC-selected winning parameters or their AUC-based ranking criterion.
    """
    import srag_50_selection as S
    from sklearn.model_selection import ParameterGrid, ParameterSampler

    _strategy(strategy)
    if family not in FAMILIES:
        raise ValueError("Balancing candidates are defined only for logit and xgb")
    space, budget = S.ESPACOS[family], S.N_ITER[family]
    grid = list(ParameterGrid(space))
    if len(grid) <= budget:
        configs = grid
    else:
        configs = list(ParameterSampler(space, budget, random_state=seed))
    return sorted(configs, key=lambda params: json.dumps(params, sort_keys=True))


def prepare_resampled_training(
    train: pd.DataFrame,
    strategy: str,
    *,
    seed: int = 42,
    cache_dir: Path | None = None,
) -> PreparedTraining:
    """Prepare one arm from real training rows; validation/test are rejected.

    The weights arm preserves all rows. RUS keeps all minority observations and
    randomly retains equally many majority observations. Restricted SMOTENC
    preserves every original row and adds audited synthetic minority rows to
    the same final class ratio. No synthetic proposal is silently substituted
    for a real observation, and no smaller training reservoir is introduced.
    """
    _assert_training_frame(train)
    strategy = _strategy(strategy)
    train = train.reset_index(drop=True)
    signature = {
        "strategy": strategy,
        "seed": int(seed),
        "protocol": SAMPLER_PROTOCOL,
        "training_fingerprint": _fingerprint(train),
        "features": list(M.FEATURES),
        "versions": _versions(),
        "sampler_sources": _sampler_sources(),
    }
    directory = _cache_path(cache_dir, signature)
    if cached := _read_cache(directory, signature):
        return cached

    y = train["y_obito"].to_numpy(dtype="int8")
    before = signature["training_fingerprint"]
    original_counts = _counts(y)
    if original_counts["positives"] >= original_counts["negatives"]:
        raise ValueError("These arms require death to be the minority outcome")
    sampler_audit = {}
    frame = train[list(M.FEATURES)].copy()
    real_used = len(train)
    if strategy == "rus":
        from imblearn.under_sampling import RandomUnderSampler

        sampler = RandomUnderSampler(sampling_strategy=1.0, random_state=seed)
        frame, y = sampler.fit_resample(frame, y)
        retained = train.iloc[sampler.sample_indices_]
        sampler_audit = {
            "retained_id_sha256": hashlib.sha256(
                retained["gold_id"].to_numpy().tobytes()
            ).hexdigest(),
            "retained_by_year": {
                str(year): int(n)
                for year, n in retained["ano_onset"].value_counts().items()
            },
        }
        real_used = len(y)
    elif strategy == "smotenc_restricted":
        import srag_61_balance as B

        if "fator_risc_portao" not in train:
            raise ValueError("Restricted SMOTENC needs the cohort-gate audit metadata")
        B.verify_tracing()
        frame, y, sampler_audit = B.restricted_smotenc(train, seed)
        if not sampler_audit["quota_atingida"]:
            raise RuntimeError("Restricted SMOTENC did not reach its declared quota")
        pd.testing.assert_frame_equal(
            frame.iloc[: len(train)].reset_index(drop=True),
            M.design_matrix(train)[0],
        )
    frame = frame[list(M.FEATURES)].reset_index(drop=True)
    y = np.asarray(y, dtype="int8")
    if _fingerprint(train) != before:
        raise RuntimeError("Balancing changed the original training frame")
    audit = {
        "strategy": strategy,
        "sampler_seed": int(seed),
        "training_fingerprint": before,
        "original": original_counts,
        "prepared": _counts(y),
        "real_records_used": real_used,
        "synthetic_records_used": len(y) - real_used,
        "original_frame_unchanged": True,
        "probabilities": "raw; no recalibrator fitted",
        "diagnostic_threshold": DIAGNOSTIC_THRESHOLD,
        "threshold_used_for_selection": False,
        "sampling_ratio": "natural; rows unchanged" if strategy == "weights" else "1:1",
        "sampler_audit": sampler_audit,
    }
    prepared = PreparedTraining(frame, y, strategy, int(seed), audit)
    _write_cache(directory, signature, prepared)
    return prepared


# A short alias for callers that use the same naming as the historical study.
prepare_strategy = prepare_resampled_training


def effective_params(prepared: PreparedTraining, family: str, params: dict) -> dict:
    """Add weights derived only from the training class counts when requested."""
    if family not in FAMILIES:
        raise ValueError("Balancing candidates are defined only for logit and xgb")
    effective = dict(params)
    if any(key in effective for key in ("class_weight", "scale_pos_weight")):
        raise ValueError("Class weights belong to the declared balancing strategy")
    if prepared.strategy == "weights":
        if family == "logit":
            effective["class_weight"] = "balanced"
        else:
            counts = prepared.audit["original"]
            effective["scale_pos_weight"] = counts["negatives"] / counts["positives"]
    return effective


def fit_candidate(
    prepared: PreparedTraining,
    family: str,
    params: dict,
    *,
    threads: int = 4,
    build_pipeline: Callable,
    model_inputs: Callable,
):
    """Fit with caller-supplied phase-51 preprocessing and no evaluation data.

    Pipelines learn their encoding, imputation and scaling only from this
    training arm. The caller stores the complete effective parameters next to
    its validation metrics, and selects candidates by its declared criterion.
    """
    effective = effective_params(prepared, family, params)
    pipeline = build_pipeline(family, effective, threads)
    pipeline.fit(model_inputs(prepared.frame, family), prepared.y)
    return pipeline
