"""PFI of the sole finalized full-training course predictor, without fitting.

Requires a completed versioned study, its evaluated canonical fitted model and
the exact full Gold source. Every permutation operates on the original forty
raw inputs of the complete temporal test. Output files contain aggregate losses
and ranks, never patient records or individual predictions.

Usage::

    python tools/srag_76_course_pfi.py --study-dir /external/course-study \\
        --data /external/gold.parquet --output-dir /external/course-pfi

Checkpoints are per feature/diagnostic and are valid only for the same dataset,
fitted model, frozen selection, source code, runtime and permutation protocol.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
from pathlib import Path

import numpy as np
import pandas as pd
import srag_51_course_study as S
import srag_62_pfi as labels
import srag_63_course_reference as reference_loader
import srag_70_explain as K
from sklearn.metrics import log_loss
from threadpoolctl import threadpool_limits

VERSION = "course-full-logloss-pfi-v2"
DEPENDENCE_PAIR = ("cardiopati", "diabetes")
CODE_FILES = (
    "srag_51_course_study.py",
    "srag_62_pfi.py",
    "srag_63_course_reference.py",
    "srag_70_explain.py",
    "srag_76_course_pfi.py",
)


def _verify_hash(document: dict, hash_key: str) -> None:
    expected = document.get(hash_key)
    content = {key: value for key, value in document.items() if key != hash_key}
    if not isinstance(expected, str) or S.object_hash(content) != expected:
        raise ValueError(f"PFI metadata failed its {hash_key} check")


def _with_hash(document: dict, hash_key: str) -> dict:
    return {**document, hash_key: S.object_hash(document)}


def _order_hash(orders) -> str:
    return hashlib.sha256(np.asarray(orders, dtype="<i8").tobytes()).hexdigest()


def _frame_hash(frame: pd.DataFrame) -> str:
    values = pd.util.hash_pandas_object(frame, index=True).to_numpy()
    return hashlib.sha256(values.tobytes()).hexdigest()


def _loss(y: np.ndarray, p: np.ndarray) -> float:
    """Unweighted mean binary log loss of float64 death probabilities."""
    return float(log_loss(y, np.asarray(p, dtype=np.float64), labels=[0, 1]))


def summarize_losses(original: float, after: np.ndarray) -> dict:
    """Aggregate repeated losses; SD describes permutations, not a patient CI."""
    after = np.asarray(after, dtype=np.float64)
    if after.ndim != 1 or len(after) < 2 or not np.isfinite(after).all():
        raise ValueError("At least two finite permutation losses are required")
    if not np.isfinite(original) or original <= 0:
        raise ValueError("The loss ratio requires a finite, positive original loss")
    delta = after - original
    ratio = after / original
    sd = float(delta.std(ddof=1))
    return {
        "after": after.tolist(),
        "delta": delta.tolist(),
        "ratio": ratio.tolist(),
        "after_mean": float(after.mean()),
        "after_sd": float(after.std(ddof=1)),
        "mean": float(delta.mean()),
        "sd": sd,
        "mcse": sd / np.sqrt(len(after)),
        "median": float(np.median(delta)),
        "q25": float(np.quantile(delta, 0.25)),
        "q75": float(np.quantile(delta, 0.75)),
        "q05": float(np.quantile(delta, 0.05)),
        "q95": float(np.quantile(delta, 0.95)),
        "ratio_mean": float(ratio.mean()),
        "ratio_sd": float(ratio.std(ddof=1)),
        "relative_increase_mean": float((ratio - 1).mean()),
        "relative_increase_sd": float((ratio - 1).std(ddof=1)),
    }


def subgroup_orders(values: pd.Series, orders: list[np.ndarray]) -> list[np.ndarray]:
    """Reuse each global random order while keeping donors in the same subgroup.

    Observed categories, including an unknown or missing state, define groups.
    This conditions the transport only on the supplied subgroup variable; it
    does not estimate a full conditional distribution given every other input.
    """
    codes, _ = pd.factorize(values, sort=True, use_na_sentinel=False)
    receivers_by_group = [np.flatnonzero(codes == group) for group in np.unique(codes)]
    restricted = []
    for order in orders:
        order = np.asarray(order, dtype=np.int64)
        if not np.array_equal(np.sort(order), np.arange(len(values))):
            raise ValueError("A subgroup order must start from a full row permutation")
        donors = np.arange(len(values), dtype=np.int64)
        for receivers in receivers_by_group:
            group = codes[receivers[0]]
            donors[receivers] = order[codes[order] == group]
        np.testing.assert_array_equal(codes[donors], codes)
        np.testing.assert_array_equal(np.sort(donors), np.arange(len(values)))
        restricted.append(donors)
    return restricted


def _complete_context(study_dir: Path, data_path: Path):
    """Reject partial studies and verify their fitted/evaluated source artifacts."""
    study_dir = study_dir.expanduser().resolve()
    data_path = data_path.expanduser().resolve()
    required = ("protocol.json", "selection.json", "test-evaluation.json")
    if missing := [name for name in required if not (study_dir / name).is_file()]:
        raise ValueError(
            "PFI requires completed selection and test evaluation; missing: "
            + ", ".join(missing)
        )
    parent_protocol = S.load_protocol(data_path, study_dir)
    reference = reference_loader.load_reference(study_dir)
    selection = S.read_json(study_dir / "selection.json")
    evaluation = S.read_json(study_dir / "test-evaluation.json")
    if (
        evaluation.get("protocol_sha256") != parent_protocol["protocol_sha256"]
        or evaluation.get("selection_sha256") != selection["selection_sha256"]
        or evaluation.get("canonical_model") != selection["canonical_model"]
        or evaluation.get("selection_changed") is not False
    ):
        raise ValueError("The completed test evaluation does not match the selection")
    prediction_path = study_dir / "test-predictions.npz"
    if not prediction_path.is_file() or S.file_hash(prediction_path) != evaluation.get(
        "test_predictions_sha256"
    ):
        raise ValueError("The completed test-prediction artifact is absent or modified")
    expected = parent_protocol["splits"]["test"]
    test_metrics = evaluation.get("test", {})
    if test_metrics.get("n") != expected["n"]:
        raise ValueError("The evaluated test size differs from the full study protocol")

    columns = list(reference.features) + ["split", "ano_onset", "gold_id", "y_obito"]
    test = pd.read_parquet(
        data_path, columns=columns, filters=[("split", "==", "test")]
    ).reset_index(drop=True)
    if (
        len(test) != expected["n"]
        or not test["split"].eq("test").all()
        or not test["ano_onset"].eq(2024).all()
        or not test["gold_id"].is_unique
        or not test["gold_id"].is_monotonic_increasing
        or not test["y_obito"].isin([0, 1]).all()
    ):
        raise ValueError(
            "The source does not supply the complete ordered temporal test"
        )
    y = test["y_obito"].to_numpy(dtype=np.int8)
    if set(np.unique(y)) != {0, 1} or int(y.sum()) != test_metrics.get("events"):
        raise ValueError("The test outcomes differ from the completed evaluation")
    x = test.loc[:, list(reference.features)].copy()
    if len(x.columns) != 40 or tuple(x.columns) != reference.features:
        raise ValueError("PFI requires all forty raw inputs of the selected predictor")
    return reference, parent_protocol, selection, evaluation, x, y


def _freeze_protocol(output_dir: Path, protocol: dict) -> dict:
    path = output_dir / "pfi-protocol.json"
    if path.exists():
        stored = S.read_json(path)
        _verify_hash(stored, "pfi_protocol_sha256")
        if stored != protocol:
            raise ValueError(
                "PFI checkpoints belong to another model, dataset or protocol"
            )
        return stored
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("A new PFI run needs an empty output directory")
    S.write_json(path, protocol)
    return protocol


def _checkpoint(
    output_dir: Path,
    protocol: dict,
    key: str,
    columns: tuple[str, ...],
    orders: list[np.ndarray],
    reference,
    x: pd.DataFrame,
    y: np.ndarray,
    original: float,
) -> dict:
    path = output_dir / "checkpoints" / f"{key}.json"
    signature = {
        "pfi_protocol_sha256": protocol["pfi_protocol_sha256"],
        "key": key,
        "columns": list(columns),
        "orders_sha256": _order_hash(orders),
        "repeats": len(orders),
    }
    if path.exists():
        checkpoint = S.read_json(path)
        _verify_hash(checkpoint, "checkpoint_sha256")
        if checkpoint.get("signature") != signature:
            raise ValueError(f"PFI checkpoint signature differs: {key}")
        if checkpoint.get("status") != "complete":
            raise ValueError(f"PFI checkpoint is not complete: {key}")
        if checkpoint.get("original") != original:
            raise ValueError(f"PFI original loss differs from the checkpoint: {key}")
        errors = np.asarray(checkpoint["metrics"]["logloss"]["after"])
        if len(errors) != len(orders):
            raise ValueError(f"PFI checkpoint has an incomplete repeat vector: {key}")
        if summarize_losses(original, errors) != checkpoint["metrics"]["logloss"]:
            raise ValueError(f"PFI checkpoint summaries differ from its losses: {key}")
        return checkpoint
    before, after = K.trace_pfi(reference, x, y, columns, orders, _loss)
    if not np.isclose(before, original, rtol=0, atol=1e-14):
        raise ValueError(f"PFI baseline changed while evaluating {key}")
    checkpoint = _with_hash(
        {
            "signature": signature,
            "status": "complete",
            "original": original,
            "metrics": {"logloss": summarize_losses(original, after)},
        },
        "checkpoint_sha256",
    )
    S.write_json(path, checkpoint)
    return checkpoint


def _add_ranks(rows: list[dict]) -> list[str]:
    matrix = np.asarray([row["metrics"]["logloss"]["delta"] for row in rows])
    mean_order = np.argsort(-matrix.mean(axis=1), kind="stable")
    ranks = pd.DataFrame(matrix).rank(ascending=False, method="average").to_numpy()
    for position, index in enumerate(mean_order):
        repeated = ranks[index]
        rows[index]["metrics"]["logloss"].update(
            {
                "rank": position + 1,
                "rank_repeats": repeated.tolist(),
                "rank_mean": float(repeated.mean()),
                "rank_sd": float(repeated.std(ddof=1)),
                "top10_fraction": float(np.mean(repeated <= 10)),
            }
        )
    # A common positive baseline makes both rankings mathematically equal.
    # Compare the identities with tolerance rather than comparing sorted
    # float orders: rounding can otherwise break a numerical near-tie.
    for row in rows:
        metric = row["metrics"]["logloss"]
        original = metric["after_mean"] - metric["mean"]
        np.testing.assert_allclose(
            metric["ratio_mean"], 1 + metric["mean"] / original, rtol=0, atol=1e-14
        )
        metric["ratio_rank"] = metric["rank"]
    return [rows[index]["feature"] for index in mean_order]


def _audit_dependence(
    x: pd.DataFrame, orders: list[np.ndarray], within: list[np.ndarray]
) -> dict:
    def pair_counts(frame):
        return frame.groupby(list(DEPENDENCE_PAIR), observed=False, dropna=False).size()

    original_pairs = pair_counts(x)
    for order, restricted in zip(orders, within, strict=True):
        joint_frame = K.permutar_colunas(x, DEPENDENCE_PAIR, order)
        within_frame = K.permutar_colunas(x, "cardiopati", restricted)
        pd.testing.assert_series_equal(pair_counts(joint_frame), original_pairs)
        pd.testing.assert_series_equal(pair_counts(within_frame), original_pairs)
        pd.testing.assert_series_equal(within_frame["diabetes"], x["diabetes"])
    return {
        "joint_pair_counts_preserved": True,
        "within_pair_counts_preserved": True,
        "diabetes_unchanged_within": True,
        "all_repeats_audited": len(orders),
    }


def run_pfi(
    study_dir: Path,
    data_path: Path,
    output_dir: Path,
    *,
    repeats: int = 50,
    seed: int = 42,
) -> dict:
    """Load, verify and explain the selected artifact; there is no fit path."""
    if (
        isinstance(repeats, bool)
        or not isinstance(repeats, (int, np.integer))
        or repeats < 2
    ):
        raise ValueError("PFI needs at least two integer repeats for a sample SD")
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)) or seed < 0:
        raise ValueError("The permutation seed must be a nonnegative integer")
    repeats, seed = int(repeats), int(seed)
    study_dir = Path(study_dir).expanduser().resolve()
    data_path = Path(data_path).expanduser().resolve()
    output_dir = S.external_directory(Path(output_dir))
    if output_dir == study_dir:
        raise ValueError("PFI artifacts need their own output directory")
    reference, parent_protocol, selection, evaluation, x, y = _complete_context(
        study_dir, data_path
    )
    original_frame_hash = _frame_hash(x)
    original_labels = y.copy()
    rng = np.random.default_rng(seed)
    orders = [rng.permutation(len(x)) for _ in range(repeats)]
    within = subgroup_orders(x["diabetes"], orders)
    protocol = _with_hash(
        {
            "version": VERSION,
            "study_protocol_sha256": parent_protocol["protocol_sha256"],
            "selection_sha256": selection["selection_sha256"],
            "evaluation_sha256": S.file_hash(study_dir / "test-evaluation.json"),
            "canonical_model": selection["canonical_model"],
            "model": reference.provenance,
            "training": selection["winner"]["training"],
            "dataset_sha256": parent_protocol["source"]["sha256"],
            "test_predictions_sha256": evaluation["test_predictions_sha256"],
            "test_input_fingerprint": original_frame_hash,
            "code_sha256": {
                name: S.file_hash(S.ROOT / "tools" / name) for name in CODE_FILES
            },
            "versions": parent_protocol["versions"],
            "pfi_runtime_versions": {
                package: importlib.metadata.version(package)
                for package in ("scipy", "pyarrow", "threadpoolctl")
            },
            "metric": "unweighted mean binary log loss; float64 probabilities",
            "positive_class": "death=1; survival=0",
            "features": list(reference.features),
            "split": "test",
            "period": 2024,
            "status": "exploratory; previously inspected temporal period",
            "n_evaluation": len(y),
            "events": int(y.sum()),
            "sampling": "all test records; no evaluation subsampling or resampling",
            "repeats": repeats,
            "permutation_seed": seed,
            "random_generator": rng.bit_generator.__class__.__name__,
            "permutation": "one raw input at a time; same global row order per repeat; always start from the original table",
            "permutation_orders_sha256": _order_hash(orders),
            "within_diabetes_orders_sha256": _order_hash(within),
            "difference": "permuted log loss minus original log loss; no-change reference zero",
            "ratio": "permuted log loss divided by original log loss; no-change reference one; values below one are allowed",
            "sd": "sample SD across permutations; ddof=1",
            "mcse": "sample permutation SD divided by square root of repeats",
            "uncertainty": "conditional on the fitted model and fixed observed test; not a patient/population confidence interval",
            "ranking": "descending mean log-loss difference; exact mean ties retain raw feature order",
            "rank_ties": "average feature rank within each repeat; top10_fraction uses these ranks",
            "before_sd": "zero across permutations because model and evaluation rows remain fixed",
            "dependence": {
                "pair": list(DEPENDENCE_PAIR),
                "joint": "move both raw columns with the same global donor order; preserve their observed tuples",
                "within": "move heart disease only, among records in the same observed diabetes state; unknown/missing states define their own groups",
                "interpretation": "distinct predictive perturbations; not causal effects, isolated interaction estimates or a full conditional distribution given every input",
                "group_counts": {
                    str(level): int(count)
                    for level, count in x["diabetes"].value_counts(dropna=False).items()
                },
            },
            "publication": "aggregate losses/ranks only; no patient rows, identifiers or individual predictions",
        },
        "pfi_protocol_sha256",
    )
    _freeze_protocol(output_dir, protocol)
    with threadpool_limits(limits=parent_protocol["threads"]):
        probabilities = np.asarray(reference.predict_proba(x)[:, 1], dtype=np.float64)
        original = _loss(y, probabilities)
        with np.load(
            study_dir / "test-predictions.npz", allow_pickle=False
        ) as recorded:
            np.testing.assert_array_equal(y, recorded["y"])
            np.testing.assert_allclose(probabilities, recorded["p"], rtol=0, atol=1e-12)
        if not np.isclose(original, evaluation["test"]["logloss"], rtol=0, atol=1e-12):
            raise ValueError(
                "The frozen predictor does not reproduce its evaluated loss"
            )
        rows = []
        for position, feature in enumerate(reference.features):
            checkpoint = _checkpoint(
                output_dir,
                protocol,
                feature,
                (feature,),
                orders,
                reference,
                x,
                y,
                original,
            )
            rows.append(
                {
                    "feature": feature,
                    "label": labels.NAMES.get(feature, feature),
                    "family": S.M.GRUPO_DE_FEATURE[feature],
                    "metrics": checkpoint["metrics"],
                }
            )
            print(
                f"PFI feature complete: {position + 1}/{len(x.columns)} {feature}",
                flush=True,
            )
        ranking = _add_ranks(rows)
        dependence = []
        for feature in DEPENDENCE_PAIR:
            row = next(row for row in rows if row["feature"] == feature)
            dependence.append(
                {
                    "key": feature,
                    "label": labels.NAMES[feature],
                    "metrics": row["metrics"],
                }
            )
        for key, columns, selected_orders, label in (
            ("joint", DEPENDENCE_PAIR, orders, "Heart disease and diabetes together"),
            ("within", ("cardiopati",), within, "Heart disease within diabetes states"),
        ):
            checkpoint = _checkpoint(
                output_dir,
                protocol,
                key,
                columns,
                selected_orders,
                reference,
                x,
                y,
                original,
            )
            dependence.append(
                {"key": key, "label": label, "metrics": checkpoint["metrics"]}
            )
            print(f"PFI dependence diagnostic complete: {key}", flush=True)
    audit = _audit_dependence(x, orders, within)
    if _frame_hash(x) != original_frame_hash:
        raise ValueError("PFI changed the original test inputs")
    np.testing.assert_array_equal(y, original_labels)
    model_path = study_dir / selection["canonical_model"]["path"]
    if S.file_hash(model_path) != selection["canonical_model"]["sha256"]:
        raise ValueError("The selected model artifact changed during PFI")
    if S.file_hash(data_path) != protocol["dataset_sha256"]:
        raise ValueError("The full source dataset changed during PFI")
    for name, expected_hash in protocol["code_sha256"].items():
        if S.file_hash(S.ROOT / "tools" / name) != expected_hash:
            raise ValueError(f"The PFI source changed during the run: {name}")
    result = _with_hash(
        {
            "protocol": protocol,
            "status": "complete",
            "original": {"logloss": original},
            "ranking": ranking,
            "rows": rows,
            "dependence": {"results": dependence, "audit": audit},
            "integrity": {
                "original_inputs_unchanged": True,
                "original_labels_unchanged": True,
                "original_predictions_match_frozen_evaluation": True,
                "canonical_model_file_unchanged": True,
                "source_dataset_file_unchanged": True,
                "source_code_unchanged": True,
                "fit_performed": False,
            },
        },
        "results_sha256",
    )
    S.write_json(output_dir / "pfi-results.json", result)
    print(
        "PFI complete; aggregate results saved without patient-level records",
        flush=True,
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--study-dir", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run_pfi(
        args.study_dir, args.data, args.output_dir, repeats=args.repeats, seed=args.seed
    )


if __name__ == "__main__":
    main()
