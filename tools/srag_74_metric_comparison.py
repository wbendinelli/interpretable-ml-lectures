"""Compare recorded PFI losses and discrimination on identical permutations.

This module reads aggregate measurements only. It never fits a model, changes
the permutation protocol or selects a metric using the temporal test.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from copy import deepcopy

import numpy as np
import pandas as pd

METRICS = ("brier", "logloss", "mae", "auc")
LABELS = {"brier": "Brier", "logloss": "Log loss", "mae": "MAE", "auc": "AUC"}


def add_mae(record, baseline, after_by_feature):
    """Add freshly measured probability MAE without rewriting the old record."""
    expected = {row["feature"] for row in record["rows"]}
    if set(after_by_feature) != expected:
        raise ValueError("MAE must cover precisely the original input features")
    enriched = deepcopy(record)
    enriched["original"]["mae"] = float(baseline)
    means = []
    for row in enriched["rows"]:
        values = np.asarray(after_by_feature[row["feature"]], dtype=np.float64)
        summary = summarise_values(values, baseline, "mae")
        delta = values - baseline
        if len(values) != record["protocol"]["repeats"]:
            raise ValueError("MAE must use every original permutation")
        row["metrics"]["mae"] = {
            "after": values.tolist(),
            "delta": delta.tolist(),
            "mean": summary["importance_mean"],
            "sd": summary["importance_sd"],
        }
        means.append(summary["importance_mean"])
    for position, index in enumerate(np.argsort(-np.asarray(means), kind="stable")):
        enriched["rows"][index]["metrics"]["mae"]["rank"] = position + 1
    return enriched


def summarise_values(values, baseline, metric):
    """Orient all importance differences so positive means worse performance."""
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 1 or len(values) < 2 or not np.all(np.isfinite(values)):
        raise ValueError("A finite vector of repeated measurements is required")
    if metric not in METRICS or not np.isfinite(baseline) or baseline <= 0:
        raise ValueError("Use a supported metric with a positive baseline")
    delta = baseline - values if metric == "auc" else values - baseline
    result = {
        "before": float(baseline),
        "first_after": float(values[0]),
        "after_mean": float(values.mean()),
        "after_sd": float(values.std(ddof=1)),
        "importance_mean": float(delta.mean()),
        "importance_sd": float(delta.std(ddof=1)),
        "worse_repeats": int(np.count_nonzero(delta > 0)),
        "better_repeats": int(np.count_nonzero(delta < 0)),
        "after": values.tolist(),
    }
    if metric != "auc":
        result["ratio_of_means"] = float(values.mean() / baseline)
        result["relative_increase_percent"] = float(delta.mean() / baseline * 100)
    return result


def compare_record(record):
    """Recompute summary, mean ranking and agreement from recorded after arrays."""
    protocol = record["protocol"]
    features = []
    matrices = {}
    for row in record["rows"]:
        metrics = {}
        for metric in METRICS:
            stored = row["metrics"][metric]
            values = np.asarray(stored["after"], dtype=np.float64)
            if len(values) != protocol["repeats"]:
                raise ValueError("A feature is missing recorded permutations")
            summary = summarise_values(values, record["original"][metric], metric)
            delta = (
                record["original"][metric] - values
                if metric == "auc"
                else values - record["original"][metric]
            )
            np.testing.assert_allclose(delta, stored["delta"], rtol=0, atol=1e-15)
            np.testing.assert_allclose(
                summary["importance_mean"], stored["mean"], rtol=0, atol=1e-15
            )
            np.testing.assert_allclose(
                summary["importance_sd"], stored["sd"], rtol=0, atol=1e-15
            )
            metrics[metric] = summary
        features.append(
            {"feature": row["feature"], "label": row["label"], "metrics": metrics}
        )
    for metric in METRICS:
        matrix = np.asarray(
            [row["metrics"][metric]["after"] for row in features], dtype=np.float64
        )
        direction = -1 if metric == "auc" else 1
        matrix = direction * (matrix - record["original"][metric])
        matrices[metric] = matrix
        ranks = pd.DataFrame(matrix).rank(ascending=False, method="average").to_numpy()
        order = np.argsort(-matrix.mean(axis=1), kind="stable")
        for position, index in enumerate(order):
            summary = features[index]["metrics"][metric]
            summary["rank"] = position + 1
            summary["rank_repeats"] = ranks[index].tolist()
            summary["top10_repeats"] = int(np.count_nonzero(ranks[index] <= 10))
            if summary["rank"] != record["rows"][index]["metrics"][metric]["rank"]:
                raise ValueError("Recomputed mean ranking differs from the record")
    agreement = []
    for left, right in itertools.combinations(METRICS, 2):
        lmean, rmean = matrices[left].mean(axis=1), matrices[right].mean(axis=1)
        lrank, rrank = pd.Series(lmean).rank(), pd.Series(rmean).rank()
        ltop = {
            row["feature"] for row in features if row["metrics"][left]["rank"] <= 10
        }
        rtop = {
            row["feature"] for row in features if row["metrics"][right]["rank"] <= 10
        }
        agreement.append(
            {
                "left": left,
                "right": right,
                "spearman": float(lrank.corr(rrank)),
                "top10_common": len(ltop & rtop),
                "left_only": sorted(ltop - rtop),
                "right_only": sorted(rtop - ltop),
            }
        )
    source_hash = hashlib.sha256(
        json.dumps(record, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    return {
        "source_content_sha256": source_hash,
        "protocol": {
            key: protocol[key]
            for key in (
                "model",
                "split",
                "period",
                "n_evaluation",
                "events",
                "repeats",
                "permutation_seed",
                "permutation_orders_sha256",
                "uncertainty",
            )
        },
        "original": record["original"],
        "features": features,
        "agreement": agreement,
        "directions": {
            "brier": "after-before",
            "logloss": "after-before",
            "mae": "after-before",
            "auc": "before-after",
        },
    }
