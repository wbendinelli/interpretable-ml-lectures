"""Fase 72 — exportação documentada da apresentação de PFI (módulo 06).

O registro científico da fase 62 permanece no módulo 00. Esta projeção
seleciona campos por um esquema explícito, em cada nível: nunca transporta
tabelas de associação ou campos não declarados. O recorte didático real
fica em um segundo arquivo, com seu próprio contrato e escopo explícito.
O navegador reproduz resultados e previsões registrados pelo notebook.

Sem dependências externas. ``--check`` verifica a cópia canônica. Uma
exportação estática exige um diretório fora do repositório, e copia somente
os recursos listados abaixo; não varre o módulo nem o diretório de dados.
"""

from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import json
import math
import pathlib
import re
import shutil
import statistics
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
LESSON = pathlib.Path("modules/06-pfi/lecture/pfi-interactive")
SOURCE = pathlib.Path("modules/00-dataset/gold/pfi_slide_explainer.json")
DATA = pathlib.Path("data/pfi-aggregates.json")
TEACHING_DATA = pathlib.Path("data/pfi-teaching-records.json")
RANKING_SOURCE = pathlib.Path("modules/00-dataset/gold/pfi_ranking.json")
COMPARISON_SOURCE = pathlib.Path("modules/06-pfi/evidence/pfi_metric_comparison.json")
TEACHING_SOURCE = pathlib.Path("modules/06-pfi/evidence/pfi_teaching_demo.json")
MODEL_SELECTION_DATA = pathlib.Path("data/model-selection.json")
SELECTION_SOURCE = pathlib.Path("modules/00-dataset/gold/selection_metrics.json")
BALANCE_SOURCE = pathlib.Path("modules/00-dataset/gold/sample_balance_search.json")
FAMILY_SEARCH_SOURCE = pathlib.Path("modules/00-dataset/gold/sample_family_search.json")

# Leaves describe values, not permissions to recursively copy a dictionary.
NUMBER = (int, float)
PARAMS = {
    "n_estimators": int,
    "max_depth": int,
    "learning_rate": NUMBER,
    "min_child_weight": int,
    "reg_lambda": NUMBER,
    "tree_method": str,
    "enable_categorical": bool,
    "eval_metric": str,
    "random_state": int,
    "n_jobs": int,
}
PROTOCOL = {
    "model": str,
    "primary_metric": str,
    "metric_definition": str,
    "ranking_source_sha256": str,
    "comparison_source_sha256": str,
    "xgb_params": PARAMS,
    "split": str,
    "period": int,
    "status": str,
    "n_train": int,
    "n_evaluation": int,
    "events": int,
    "features": [str],
    "repeats": int,
    "permutation_seed": int,
    "sampling": str,
    "permutation": str,
    "sd": str,
    "uncertainty": str,
    "top10_criterion": str,
    "rank_ties": str,
    "boxplot": str,
    "before_sd": str,
    "versions": {"numpy": str, "pandas": str, "scikit-learn": str, "xgboost": str},
}
RANKING_ROW = {
    "feature": str,
    "label": str,
    "before": NUMBER,
    "after_mean": NUMBER,
    "after_sd": NUMBER,
    "difference_mean": NUMBER,
    "difference_sd": NUMBER,
    "ratio_mean": NUMBER,
    "ratio_sd": NUMBER,
    "relative_increase_percent": NUMBER,
}
SPLIT = {"letalidade_pct": NUMBER, "n": int, "obitos": int}
MODEL_NAMES = ("arvore", "dummy", "floresta", "logit", "lpm", "xgb")
STUDY = {
    "cohort_n": int,
    "train_sample_n": int,
    "input_n": int,
    "train_end": int,
    "validation_year": int,
    "test_year": int,
    "splits": {"test": SPLIT, "train": SPLIT, "val": SPLIT},
    "sample_seed": int,
    "scoreboard": [{"model": str, "label": str, "auc": NUMBER, "brier": NUMBER}],
    "search_counts": {name: int for name in MODEL_NAMES},
    "bootstrap_repeats": int,
    "winner": str,
    "xgb_params": PARAMS,
    "test_auc": NUMBER,
    "test_brier": NUMBER,
    "test_logloss": NUMBER,
    "selection_rule": str,
    "cohort_rule": str,
    "balancing": str,
    "missing": str,
    "status": str,
}
DIAGNOSTIC = {
    "key": str,
    "label": str,
    "after": [NUMBER],
    "before": NUMBER,
    "after_mean": NUMBER,
    "after_sd": NUMBER,
    "difference": [NUMBER],
    "difference_mean": NUMBER,
    "difference_sd": NUMBER,
}
SCHEMA = {
    "protocol": PROTOCOL,
    "original": {"brier": NUMBER, "logloss": NUMBER, "auc": NUMBER},
    "rows": [RANKING_ROW],
    "equations": {"difference": str, "ratio": str, "logloss": str},
    "walkthrough": {
        "feature": str,
        "after": [NUMBER],
        "difference": [NUMBER],
        "first_after": NUMBER,
        "first_difference": NUMBER,
        "mean_after": NUMBER,
        "mean_difference": NUMBER,
        "sd_difference": NUMBER,
        "train_end": int,
        "validation_year": int,
        "audit": str,
        "max_trace_error": NUMBER,
    },
    "study": STUDY,
    "dependence": {
        "results": [DIAGNOSTIC],
        "protocol": {
            "repeats": int,
            "seed": int,
            "n": int,
            "metric": str,
            "status": str,
            "sd": str,
            # Protocol descriptions only; subgroup tables are not selected.
            "subgroups": str,
            "joint": str,
        },
    },
}
PRESENTATION = {
    "row_diagrams": "real SRAG teaching records in a separate, explicitly scoped evidence file",
    "empirical_results": "aggregate fixed-model, temporal-test measurements",
}
STATIC_FILES = (
    "index.html",
    "lecture.css",
    "lecture.js",
    "pfi-example.css",
    "pfi-example.js",
    "sequence.css",
    "sequence.js",
    "study.css",
    "study.js",
    "srag-compact.js",
    "theory-compact.js",
    "presentation-grid.css",
    "real-records.css",
    "navigation.css",
    "visual-aids.js",
    "visual-aids.css",
    "method.html",
    "teacher-guide.html",
    "teacher-guide.css",
    "teacher-guide.js",
    "fontes/LICENSE-Lecture.txt",
    "fontes/LICENSE-Raschka.txt",
    "fontes/provenance.json",
    "figures/equation-logloss.svg",
    "figures/equation-difference.svg",
    "figures/equation-ratio.svg",
    "figures/pfi-age-repeats.svg",
    "figures/pfi-dependence.svg",
    "figures/pfi-slide-difference.svg",
    "figures/pfi-slide-ratio.svg",
)
FONT_FILES = ("Inter-Regular.ttf", "Inter-Medium.ttf", "OFL-Inter.txt")
FAMILY_LABELS = {
    "dummy": "Constant baseline",
    "lpm": "Linear probability model",
    "logit": "Logistic regression",
    "arvore": "Decision tree",
    "floresta": "Random forest",
    "xgb": "XGBoost",
}
STRATEGY_LABELS = {
    "plain": "Original",
    "weights": "Class weights",
    "rus": "Undersampling",
    "smotenc_restricted": "Restricted SMOTENC",
}
TUNED_XGB_PARAMS = {
    key: PARAMS[key]
    for key in (
        "learning_rate",
        "max_depth",
        "min_child_weight",
        "n_estimators",
        "reg_lambda",
    )
}
FAMILY_PARAM_SCHEMAS = {
    "dummy": {"strategy": str},
    "lpm": {},
    "logit": {"C": NUMBER},
    "arvore": {
        "ccp_alpha": NUMBER,
        "criterion": str,
        "max_depth": (int, type(None)),
        "min_samples_leaf": int,
    },
    "floresta": {
        "max_depth": int,
        "max_features": (str, int, float),
        "min_samples_leaf": int,
    },
    "xgb": TUNED_XGB_PARAMS,
}
MODEL_SELECTION_SCHEMA = {
    "historical": {
        "criterion": str,
        "families": [
            {
                "model": str,
                "label": str,
                "validation_logloss": NUMBER,
                "test_logloss": NUMBER,
                "params": dict,
            }
        ],
        "winner": str,
    },
    "review": {
        "criterion": str,
        "family": str,
        "candidates_per_strategy": int,
        "strategies": [
            {
                "strategy": str,
                "label": str,
                "validation_logloss": NUMBER,
                "test_logloss": NUMBER,
                "params": dict,
            }
        ],
        "winner": str,
        "recalibrated": bool,
    },
    "family_search": {
        "criterion": str,
        "strategy": str,
        "families": [
            {
                "model": str,
                "label": str,
                "validation_logloss": NUMBER,
                "test_logloss": NUMBER,
                "params": dict,
                "candidate_count": int,
            }
        ],
        "winner": str,
        "recalibrated": bool,
    },
}


def _project(value, schema, path):
    """Select known fields recursively and reject missing or ill-typed values."""
    if isinstance(schema, dict):
        if not isinstance(value, dict):
            raise TypeError(f"{path}: expected an object")
        missing = schema.keys() - value.keys()
        if missing:
            raise ValueError(f"{path}: missing fields {sorted(missing)}")
        return {
            key: _project(value[key], spec, f"{path}.{key}")
            for key, spec in schema.items()
        }
    if isinstance(schema, list):
        if not isinstance(value, list):
            raise TypeError(f"{path}: expected an array")
        return [
            _project(item, schema[0], f"{path}[{i}]") for i, item in enumerate(value)
        ]
    if isinstance(schema, tuple):
        valid = type(value) in schema and (
            not isinstance(value, (int, float)) or math.isfinite(value)
        )
    else:
        valid = type(value) is schema
    if not valid:
        raise TypeError(f"{path}: incompatible value type")
    return value


def _equal(left, right, description):
    if not math.isclose(left, right, rel_tol=0, abs_tol=1e-12):
        raise ValueError(f"Inconsistent aggregate: {description}")


def _trace(after, difference, baseline, repeats, label):
    if len(after) != repeats or len(difference) != repeats:
        raise ValueError(f"{label}: repeat vectors do not match the protocol")
    for p, d in zip(after, difference, strict=True):
        if p < 0:
            raise ValueError(f"{label}: negative log loss")
        _equal(p - baseline, d, f"{label} repeat")


def _validate_values(payload):
    protocol, study = payload["protocol"], payload["study"]
    if protocol["primary_metric"] != "logloss":
        raise ValueError("This presentation requires log loss as its primary metric")
    for key in ("ranking_source_sha256", "comparison_source_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", protocol[key]):
            raise ValueError("Invalid scientific evidence hash")
    baseline = payload["original"]["logloss"]
    repeats = protocol["repeats"]
    if baseline <= 0 or repeats < 2:
        raise ValueError(
            "Positive baseline and multiple repeats are required for the displayed ratio/SD"
        )
    if protocol["n_train"] <= 0 or protocol["n_evaluation"] <= 0:
        raise ValueError("Record counts must be positive")
    if not 0 <= protocol["events"] <= protocol["n_evaluation"]:
        raise ValueError("Outcome count exceeds evaluation count")
    features = protocol["features"]
    if not features or len(features) != len(set(features)):
        raise ValueError("Input names must be nonempty and unique")
    rows = payload["rows"]
    if not rows or len({r["feature"] for r in rows}) != len(rows):
        raise ValueError("Ranking names must be nonempty and unique")
    for row in rows:
        if row["feature"] not in features or row["after_sd"] < 0:
            raise ValueError("Ranking contains an unknown input or a negative SD")
        _equal(row["before"], baseline, "ranking baseline")
        _equal(
            row["after_mean"] - baseline, row["difference_mean"], "ranking difference"
        )
        _equal(row["after_sd"], row["difference_sd"], "ranking difference SD")
        _equal(row["after_mean"] / baseline, row["ratio_mean"], "ranking ratio")
        _equal(row["after_sd"] / baseline, row["ratio_sd"], "ranking ratio SD")
        _equal(
            (row["ratio_mean"] - 1) * 100,
            row["relative_increase_percent"],
            "ranking percent",
        )
    trace = payload["walkthrough"]
    _trace(trace["after"], trace["difference"], baseline, repeats, "Age")
    _equal(trace["first_after"], trace["after"][0], "first Age error")
    _equal(trace["first_difference"], trace["difference"][0], "first Age difference")
    _equal(trace["mean_after"], statistics.mean(trace["after"]), "mean Age error")
    _equal(
        trace["mean_difference"],
        statistics.mean(trace["difference"]),
        "mean Age difference",
    )
    _equal(
        trace["sd_difference"], statistics.stdev(trace["difference"]), "Age sample SD"
    )
    row = next((r for r in rows if r["feature"] == trace["feature"]), None)
    if row is None:
        raise ValueError("Walkthrough input is absent from the ranking")
    _equal(trace["mean_difference"], row["difference_mean"], "Age ranking versus trace")
    _equal(trace["sd_difference"], row["difference_sd"], "Age ranking SD versus trace")
    _equal(study["test_logloss"], baseline, "study baseline")
    _equal(study["test_brier"], payload["original"]["brier"], "historical study Brier")
    _equal(study["test_auc"], payload["original"]["auc"], "study AUC")
    if (
        study["input_n"] != len(features)
        or study["xgb_params"] != protocol["xgb_params"]
    ):
        raise ValueError("Study inputs/model disagree with the PFI protocol")
    if study["splits"]["test"]["n"] != protocol["n_evaluation"]:
        raise ValueError("Study evaluation count disagrees with PFI")
    dependence = payload["dependence"]
    dp = dependence["protocol"]
    if (
        dp["repeats"] != repeats
        or dp["n"] != protocol["n_evaluation"]
        or dp["metric"] != "logloss"
    ):
        raise ValueError("Dependence protocol disagrees with the shared test/repeats")
    if [r["key"] for r in dependence["results"]] != [
        "cardiopati",
        "diabetes",
        "joint",
        "within",
    ]:
        raise ValueError("Unexpected dependence diagnostics/order")
    for result in dependence["results"]:
        _equal(result["before"], baseline, "dependence baseline")
        _trace(result["after"], result["difference"], baseline, repeats, result["key"])
        _equal(
            result["after_mean"],
            statistics.mean(result["after"]),
            "diagnostic mean error",
        )
        _equal(
            result["difference_mean"],
            statistics.mean(result["difference"]),
            "diagnostic mean difference",
        )
        _equal(
            result["after_sd"], statistics.stdev(result["after"]), "diagnostic error SD"
        )
        _equal(
            result["difference_sd"],
            statistics.stdev(result["difference"]),
            "diagnostic difference SD",
        )


def _json_hash(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def _individual_logloss(probability: float, outcome: int) -> float:
    # Match sklearn's float64 clipping and natural logarithm convention.
    eps = sys.float_info.epsilon
    probability = min(max(probability, eps), 1 - eps)
    return -math.log(probability) if outcome else -math.log1p(-probability)


def _logloss_source(source: dict, record: dict | None, comparison: dict | None) -> dict:
    """Recompute the public loss projection; preserve historical source objects."""
    record = record if record is not None else _read_json(REPO / RANKING_SOURCE)
    comparison = (
        comparison if comparison is not None else _read_json(REPO / COMPARISON_SOURCE)
    )
    primary = "logloss"
    protocol = copy.deepcopy(source["protocol"])
    for key in ("n_evaluation", "repeats", "permutation_seed"):
        if (
            protocol[key] != record["protocol"][key]
            or protocol[key] != comparison["protocol"][key]
        ):
            raise ValueError(
                "The metric projection must use the same recorded evaluation protocol"
            )
    if (
        comparison["protocol"]["permutation_orders_sha256"]
        != record["protocol"]["permutation_orders_sha256"]
    ):
        raise ValueError("The metric comparison uses different permutation orders")
    protocol.update(
        primary_metric=primary,
        metric_definition="mean negative natural logarithm of probability assigned to the observed outcome; float64 clipping at machine epsilon",
        ranking_source_sha256=_json_hash(record),
        comparison_source_sha256=_json_hash(comparison),
        top10_criterion="descending mean increase in log loss on the fixed temporal test",
    )
    baseline = record["original"][primary]
    labels = {r["feature"]: r["label"] for r in source["rows"]}
    rows = []
    for row in sorted(record["rows"], key=lambda r: r["metrics"][primary]["rank"])[:10]:
        after = row["metrics"][primary]["after"]
        delta = [value - baseline for value in after]
        ratios = [value / baseline for value in after]
        rows.append(
            {
                "feature": row["feature"],
                "label": labels.get(row["feature"], row["label"]),
                "before": baseline,
                "after_mean": statistics.mean(after),
                "after_sd": statistics.stdev(after),
                "difference_mean": statistics.mean(delta),
                "difference_sd": statistics.stdev(delta),
                "ratio_mean": statistics.mean(ratios),
                "ratio_sd": statistics.stdev(ratios),
                "relative_increase_percent": (statistics.mean(ratios) - 1) * 100,
            }
        )
    age = next(r for r in record["rows"] if r["feature"] == "idade_anos")["metrics"][
        primary
    ]
    after, difference = age["after"], age["delta"]
    trace = {
        **source["walkthrough"],
        "after": after,
        "difference": difference,
        "first_after": after[0],
        "first_difference": difference[0],
        "mean_after": statistics.mean(after),
        "mean_difference": statistics.mean(difference),
        "sd_difference": statistics.stdev(difference),
    }
    dep_labels = {r["key"]: r["label"] for r in source["dependence"]["results"]}
    diagnostics = []
    for row in comparison["dependence"]:
        values = row["metrics"][primary]["after"]
        delta = [value - baseline for value in values]
        diagnostics.append(
            {
                "key": row["key"],
                "label": dep_labels[row["key"]],
                "before": baseline,
                "after": values,
                "after_mean": statistics.mean(values),
                "after_sd": statistics.stdev(values),
                "difference": delta,
                "difference_mean": statistics.mean(delta),
                "difference_sd": statistics.stdev(delta),
            }
        )
    return {
        "protocol": protocol,
        "original": copy.deepcopy(record["original"]),
        "rows": rows,
        "equations": {
            "difference": r"$FI_j = e_{\mathrm{perm},j} - e_{\mathrm{orig}}$",
            "ratio": r"$FI_j = \frac{e_{\mathrm{perm},j}}{e_{\mathrm{orig}}}$",
            "logloss": r"$\mathrm{Log\ loss} = -\frac{1}{n}\sum_{i=1}^{n}\left[y_i\ln(p_i)+(1-y_i)\ln(1-p_i)\right]$",
        },
        "walkthrough": trace,
        "study": {**source["study"], "test_logloss": baseline},
        "dependence": {
            "results": diagnostics,
            "protocol": {**source["dependence"]["protocol"], "metric": primary},
        },
    }


def project_aggregates(
    source: dict, record: dict | None = None, comparison: dict | None = None
) -> dict:
    """Return the explicit aggregate projection, validating its numerical contract.

    Extra fields in the research source are intentionally unselected. A nested
    object cannot replace a selected scalar, so newly introduced patient data
    cannot pass through a supposedly aggregate field.
    """
    if source["protocol"].get("primary_metric") != "logloss":
        source = _logloss_source(source, record, comparison)
    payload = _project(source, SCHEMA, "source")
    payload["presentation"] = dict(PRESENTATION)
    _validate_values(payload)
    return payload


def validate_aggregates(payload: dict) -> None:
    """Reject any field outside the public schema, including nested extras."""
    projected = project_aggregates(payload)
    if payload != projected:
        raise ValueError(
            "The presentation payload contains fields outside the explicit aggregate schema"
        )


def _validate_model_selection(payload: dict) -> None:
    if payload != _project(payload, MODEL_SELECTION_SCHEMA, "model_selection"):
        raise ValueError("Unexpected public model-selection fields")
    historical, review = payload["historical"], payload["review"]
    if historical["criterion"] != "validation_roc_auc":
        raise ValueError("The historical selection criterion must remain ROC-AUC")
    if (
        review["criterion"] != "validation_logloss"
        or review["family"] != "xgb"
        or review["recalibrated"]
        or review["candidates_per_strategy"] <= 0
    ):
        raise ValueError("The review is a log-loss comparison of raw XGBoost outputs")
    for rows, key, labels, schemas in (
        (
            historical["families"],
            "model",
            FAMILY_LABELS,
            FAMILY_PARAM_SCHEMAS,
        ),
        (
            review["strategies"],
            "strategy",
            STRATEGY_LABELS,
            {name: TUNED_XGB_PARAMS for name in STRATEGY_LABELS},
        ),
    ):
        if [row[key] for row in rows] != list(labels):
            raise ValueError("Unexpected model/strategy names or order")
        for row in rows:
            name = row[key]
            if row["label"] != labels[name] or row["params"] != _project(
                row["params"], schemas[name], f"{name}.params"
            ):
                raise ValueError("Unexpected model label or parameter fields")
            for metric in ("validation_logloss", "test_logloss"):
                if row[metric] < 0:
                    raise ValueError("Log loss cannot be negative")
                if key == "model" and row[metric] != round(row[metric], 4):
                    raise ValueError(
                        "Historical losses must preserve recorded precision"
                    )
    if historical["winner"] not in FAMILY_LABELS:
        raise ValueError("Unknown historical winner")
    if review["winner"] not in STRATEGY_LABELS:
        raise ValueError("Unknown review winner")
    current = payload["family_search"]
    if (
        current["criterion"] != "validation_logloss"
        or current["strategy"] != "plain"
        or current["recalibrated"]
        or current["winner"] not in FAMILY_LABELS
        or [row["model"] for row in current["families"]] != list(FAMILY_LABELS)
    ):
        raise ValueError("The family study must preserve its plain log-loss protocol")
    for row in current["families"]:
        name = row["model"]
        if (
            row["label"] != FAMILY_LABELS[name]
            or row["candidate_count"] <= 0
            or row["params"]
            != _project(row["params"], FAMILY_PARAM_SCHEMAS[name], f"current.{name}")
            or any(row[key] < 0 for key in ("validation_logloss", "test_logloss"))
        ):
            raise ValueError("Invalid current-family projection")


def _project_family_search(record: dict, reference_protocol: dict) -> dict:
    """Project the completed, separately frozen family search, without trial arrays."""
    protocol, selection, evaluation = (
        record["protocol"],
        record["selection"],
        record["evaluation"],
    )
    if (
        record["status"] != "complete"
        or protocol["version"] != "course-sample-family-logloss-v1"
        or protocol["primary_metric"] != "logloss"
        or protocol["strategy"] != "plain"
        or protocol["source"] != reference_protocol["source"]
        or protocol["features"] != reference_protocol["features"]
        or protocol["seed"] != reference_protocol["seed"]
        or any(
            protocol["splits"][split]["n"] != reference_protocol["splits"][split]["n"]
            for split in ("train", "val", "test")
        )
        or selection["test_used_for_selection"]
        or selection["probabilities_recalibrated"]
        or not selection["finalists_frozen_before_test"]
        or evaluation["selection_changed"]
        or not evaluation["finalists_frozen_before_test"]
        or evaluation["selection_sha256"] != selection["selection_sha256"]
    ):
        raise ValueError("Incomplete or inconsistent family-search protocol")
    trials = record["validation_candidates"]
    ids = {row["candidate_id"] for row in trials}
    counts = collections.Counter(row["family"] for row in trials)
    if (
        len(ids) != len(trials)
        or len(trials) != selection["candidate_count"]
        or counts != collections.Counter(protocol["budgets"])
        or set(counts) != set(FAMILY_LABELS)
        or any(row["strategy"] != "plain" for row in trials)
    ):
        raise ValueError("Family candidates differ from the declared search budget")
    finalists = {row["family"]: row for row in selection["finalists"]}
    tested = {row["candidate_id"]: row for row in evaluation["finalists"]}
    if len(finalists) != len(FAMILY_LABELS) or len(tested) != len(FAMILY_LABELS):
        raise ValueError("Expected one frozen finalist per family")
    families = []
    for name, label in FAMILY_LABELS.items():
        best = min(
            (row for row in trials if row["family"] == name),
            key=lambda row: (row["validation"]["logloss"], row["candidate_id"]),
        )
        if best != finalists[name]:
            raise ValueError("A family finalist differs from its validation minimum")
        test = tested[best["candidate_id"]]
        if test["family"] != name or test["strategy"] != "plain":
            raise ValueError("Family test metrics belong to another finalist")
        families.append(
            {
                "model": name,
                "label": label,
                "validation_logloss": best["validation"]["logloss"],
                "test_logloss": test["test"]["logloss"],
                "params": _project(
                    best["params"], FAMILY_PARAM_SCHEMAS[name], f"family.{name}"
                ),
                "candidate_count": counts[name],
            }
        )
    winner = min(
        trials, key=lambda row: (row["validation"]["logloss"], row["candidate_id"])
    )
    if selection["winner"] != winner:
        raise ValueError("Family winner differs from the validation minimum")
    return {
        "criterion": "validation_logloss",
        "strategy": "plain",
        "families": families,
        "winner": winner["family"],
        "recalibrated": False,
    }


def project_model_selection(
    historical: dict | None = None,
    review: dict | None = None,
    family_search: dict | None = None,
) -> dict:
    """Select only aggregate losses and tuned parameters from the recorded studies.

    Historical family finalists were chosen by ROC-AUC, whereas the separate
    XGBoost-only review chose one finalist per balancing strategy by log loss.
    No individual predictions, artifact paths, or fit routines are selected.
    """
    historical = (
        historical if historical is not None else _read_json(REPO / SELECTION_SOURCE)
    )
    review = review if review is not None else _read_json(REPO / BALANCE_SOURCE)
    if "maior AUC-ROC" not in historical["criterio"]:
        raise ValueError("Unrecognized historical selection protocol")
    if (
        review["status"] != "complete"
        or review["selection"]["test_used_for_selection"]
        or not review["selection"]["finalists_frozen_before_test"]
        or review["selection"]["probabilities_recalibrated"]
    ):
        raise ValueError("The balancing review must be complete and frozen before test")
    placar = {(row["modelo"], row["split"]): row for row in historical["placar"]}
    expected = {(name, split) for name in FAMILY_LABELS for split in ("val", "test")}
    if set(placar) != expected or len(historical["placar"]) != len(expected):
        raise ValueError(
            "Expected one validation and test record per historical family"
        )
    families = []
    for name, label in FAMILY_LABELS.items():
        families.append(
            {
                "model": name,
                "label": label,
                "validation_logloss": placar[name, "val"]["logloss"],
                "test_logloss": placar[name, "test"]["logloss"],
                "params": _project(
                    historical["escolha"]["melhores"][name],
                    FAMILY_PARAM_SCHEMAS[name],
                    f"historical.{name}.params",
                ),
            }
        )
    trials = review["validation_candidates"]
    counts = collections.Counter(row["strategy"] for row in trials)
    if (
        set(counts) != set(STRATEGY_LABELS)
        or len(set(counts.values())) != 1
        or len(trials) != review["selection"]["candidate_count"]
        or len({row["candidate_id"] for row in trials}) != len(trials)
        or any(row["family"] != "xgb" or row["status"] != "complete" for row in trials)
    ):
        raise ValueError(
            "The review requires an equal completed XGBoost budget per arm"
        )
    final_by_arm = {row["strategy"]: row for row in review["selection"]["finalists"]}
    test_by_id = {row["candidate_id"]: row for row in review["evaluation"]["finalists"]}
    if (
        set(final_by_arm) != set(STRATEGY_LABELS)
        or len(review["selection"]["finalists"]) != len(STRATEGY_LABELS)
        or len(test_by_id) != len(STRATEGY_LABELS)
        or len(review["evaluation"]["finalists"]) != len(STRATEGY_LABELS)
    ):
        raise ValueError("Expected one validation-selected finalist per strategy")
    strategies = []
    for name, label in STRATEGY_LABELS.items():
        selected = final_by_arm[name]
        best = min(
            (row for row in trials if row["strategy"] == name),
            key=lambda row: (row["validation"]["logloss"], row["candidate_id"]),
        )
        if selected != best:
            raise ValueError("A review finalist differs from its validation argmin")
        tested = test_by_id[selected["candidate_id"]]
        if tested["strategy"] != name or tested["family"] != "xgb":
            raise ValueError("Test evidence belongs to another strategy/model")
        strategies.append(
            {
                "strategy": name,
                "label": label,
                "validation_logloss": selected["validation"]["logloss"],
                "test_logloss": tested["test"]["logloss"],
                "params": _project(
                    selected["params"], TUNED_XGB_PARAMS, f"review.{name}.params"
                ),
            }
        )
    winner = min(
        trials, key=lambda row: (row["validation"]["logloss"], row["candidate_id"])
    )
    if review["selection"]["winner"] != winner:
        raise ValueError("The review winner differs from its validation argmin")
    payload = {
        "historical": {
            "criterion": "validation_roc_auc",
            "families": families,
            "winner": historical["escolha"]["vencedor"],
        },
        "review": {
            "criterion": "validation_logloss",
            "family": "xgb",
            "candidates_per_strategy": counts["plain"],
            "strategies": strategies,
            "winner": winner["strategy"],
            "recalibrated": False,
        },
        "family_search": _project_family_search(
            family_search
            if family_search is not None
            else _read_json(REPO / FAMILY_SEARCH_SOURCE),
            review["protocol"],
        ),
    }
    _validate_model_selection(payload)
    return payload


def validate_model_selection(
    payload: dict,
    historical: dict | None = None,
    review: dict | None = None,
    family_search: dict | None = None,
) -> None:
    """Require the public schema and exact equality with the recorded sources."""
    _validate_model_selection(payload)
    if payload != project_model_selection(historical, review, family_search):
        raise ValueError("Model-selection data diverge from their scientific sources")


TEACHING_ROW = {
    "record": str,
    "idade_anos": NUMBER,
    "saturacao": str,
    "y_obito": int,
    "p_original": NUMBER,
    "class_original": int,
    "correct_original": bool,
    "loss_original": NUMBER,
    "p_after_age": NUMBER,
    "class_after_age": int,
    "correct_after_age": bool,
    "loss_after_age": NUMBER,
    "p_after_oxygen": NUMBER,
    "class_after_oxygen": int,
    "correct_after_oxygen": bool,
    "loss_after_oxygen": NUMBER,
}
TEACHING_ROUND = {
    "feature": str,
    "label": str,
    "cell": str,
    "values": [(int, float, str)],
    "shuffled_values": [(int, float, str)],
    "probability": [NUMBER],
    "predicted": [int],
    "correct": [bool],
    "individual_loss": [NUMBER],
    "sample_loss_mean": NUMBER,
    "full_test_single_loss": NUMBER,
    "full_test": RANKING_ROW,
}
TEACHING_SCHEMA = {
    "metric": str,
    "rows": [TEACHING_ROW],
    "rounds": [TEACHING_ROUND],
    "permutation_seed": int,
    "displayed_repeat": int,
    "evaluation_n": int,
    "permutation_scope": str,
    "permutation_orders_sha256": str,
    "threshold": NUMBER,
    "age_unit": str,
    "selection": {"records_per_outcome": int, "rule": str},
    "scope": str,
}


def project_teaching_records(source: dict) -> dict:
    """Select the recorded teaching subset; never imply that it is aggregate data.

    Labels A-H are presentation positions, not an anonymization claim. Ages,
    low-oxygen categories, outcomes and model probabilities are real individual
    observations. Publication of this separate file needs specific authorization.
    Identifiers, dates, locations and unselected research fields cannot pass.
    """
    preview = _project(source["preview"], TEACHING_SCHEMA, "teaching.preview")
    rows, rounds = preview["rows"], preview["rounds"]
    if preview["metric"] != "logloss":
        raise ValueError("Teaching loss must be log loss")
    n = len(rows)
    if n != 8 or preview["permutation_seed"] != 42 or preview["displayed_repeat"] != 1:
        raise ValueError(
            "Teaching table must display the recorded first full-test shuffle"
        )
    if (
        preview["permutation_scope"] != "full temporal test"
        or preview["evaluation_n"] <= n
    ):
        raise ValueError(
            "The displayed records must come from a larger full-test shuffle"
        )
    if not re.fullmatch(r"[0-9a-f]{64}", preview["permutation_orders_sha256"]):
        raise ValueError("Invalid full-test permutation-order hash")
    if [r["record"] for r in rows] != list("ABCDEFGH"):
        raise ValueError("Teaching labels must be presentation positions A-H")
    threshold = preview["threshold"]
    if not 0 < threshold < 1:
        raise ValueError("Invalid teaching classification cutoff")
    for row in rows:
        if row["y_obito"] not in {0, 1} or row["saturacao"] not in {
            "sim",
            "nao",
            "desconhecido",
        }:
            raise ValueError("Invalid observed outcome/category")
        for suffix in ("original", "after_age", "after_oxygen"):
            probability = row["p_" + suffix]
            predicted = int(probability >= threshold)
            if not 0 <= probability <= 1 or row["class_" + suffix] != predicted:
                raise ValueError("Inconsistent teaching prediction")
            if row["correct_" + suffix] != (predicted == row["y_obito"]):
                raise ValueError("Inconsistent correctness flag")
            _equal(
                row["loss_" + suffix],
                _individual_logloss(probability, row["y_obito"]),
                "individual teaching loss",
            )
    if [r["feature"] for r in rounds] != ["idade_anos", "saturacao"]:
        raise ValueError("Teaching rounds must be separate Age and low-oxygen shuffles")
    if [r["cell"] for r in rounds] != ["age", "oxygen"]:
        raise ValueError("Teaching rounds must target their matching display columns")
    for round_, suffix in zip(rounds, ("age", "oxygen"), strict=True):
        for field in (
            "values",
            "shuffled_values",
            "probability",
            "predicted",
            "correct",
            "individual_loss",
        ):
            if len(round_[field]) != n:
                raise ValueError("Teaching round fields must match the row count")
        if round_["values"] != [r[round_["feature"]] for r in rows]:
            raise ValueError("Teaching round must start from original input values")
        if round_["full_test_single_loss"] < 0:
            raise ValueError("Displayed full-test log loss is negative")
        for value in round_["shuffled_values"]:
            if suffix == "age" and (type(value) not in NUMBER or value < 0):
                raise ValueError("Invalid shuffled age value")
            if suffix == "oxygen" and value not in {"sim", "nao", "desconhecido"}:
                raise ValueError("Invalid shuffled low-oxygen category")
        for i, row in enumerate(rows):
            _equal(
                round_["probability"][i],
                row["p_after_" + suffix],
                "teaching probability",
            )
            _equal(
                round_["individual_loss"][i],
                row["loss_after_" + suffix],
                "teaching loss",
            )
            if (
                round_["correct"][i] != row["correct_after_" + suffix]
                or round_["predicted"][i] != row["class_after_" + suffix]
            ):
                raise ValueError("Teaching round decisions disagree with their rows")
        _equal(
            round_["sample_loss_mean"],
            statistics.mean(round_["individual_loss"]),
            "teaching mean log loss",
        )
    return {"preview": preview}


def validate_teaching_records(payload: dict, aggregates: dict) -> None:
    if payload != project_teaching_records(payload):
        raise ValueError(
            "Teaching file includes fields outside its explicit record schema"
        )
    if payload["preview"]["evaluation_n"] != aggregates["protocol"]["n_evaluation"]:
        raise ValueError(
            "Displayed shuffle and global ranking use different evaluation sets"
        )
    ranking = {row["feature"]: row for row in aggregates["rows"]}
    for round_ in payload["preview"]["rounds"]:
        if round_["full_test"] != ranking.get(round_["feature"]):
            raise ValueError(
                "Teaching full-test context disagrees with the aggregate ranking"
            )


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _check_resources(root):
    # Literal runtime URLs: template-generated figure names are checked by the
    # explicit STATIC_FILES list, rather than guessed from arbitrary JS text.
    for name in STATIC_FILES:
        path = root / name
        if not path.is_file():
            raise ValueError(f"Missing presentation asset: {name}")
        if path.suffix not in {".html", ".css", ".js"}:
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r"(?:file://|/Users/|127\.0\.0\.1|localhost)", text):
            raise ValueError(f"Local-only URL in presentation asset: {name}")
        patterns = r"""(?:href|src)=["']([^"']+)["']|(?:fetch|url)\(["']([^"']+)["']"""
        for pair in re.findall(patterns, text):
            url = next(part for part in pair if part)
            if url.startswith(("https:", "http:", "data:", "#")) or "${" in url:
                continue
            url = url.split("#", 1)[0].split("?", 1)[0]
            if url and not (path.parent / url).is_file():
                raise ValueError(f"Broken presentation resource in {name}: {url}")


def check_presentation(repo_root: pathlib.Path | None = None) -> dict:
    """Compare committed data with its research-source projection and assets."""
    repo = pathlib.Path(repo_root or REPO).resolve()
    projected = project_aggregates(_read_json(repo / SOURCE))
    recorded = _read_json(repo / LESSON / DATA)
    validate_aggregates(recorded)
    if recorded != projected:
        raise ValueError(
            "Presentation aggregates diverge from the recorded scientific source"
        )
    teaching = _read_json(repo / LESSON / TEACHING_DATA)
    validate_teaching_records(teaching, recorded)
    if teaching != project_teaching_records(_read_json(repo / TEACHING_SOURCE)):
        raise ValueError("Teaching records diverge from their recorded evidence")
    selection = _read_json(repo / LESSON / MODEL_SELECTION_DATA)
    validate_model_selection(
        selection,
        _read_json(repo / SELECTION_SOURCE),
        _read_json(repo / BALANCE_SOURCE),
        _read_json(repo / FAMILY_SEARCH_SOURCE),
    )
    experiment = _read_json(repo / "modules/00-dataset/gold/pfi_ranking.json")
    if (
        teaching["preview"]["permutation_orders_sha256"]
        != experiment["protocol"]["permutation_orders_sha256"]
    ):
        raise ValueError(
            "The displayed shuffle comes from another permutation protocol"
        )
    for round_ in teaching["preview"]["rounds"]:
        result = next(
            row for row in experiment["rows"] if row["feature"] == round_["feature"]
        )
        _equal(
            round_["full_test_single_loss"],
            result["metrics"]["logloss"]["after"][0],
            "displayed full-test repeat",
        )
    for key, path in (
        ("ranking_source_sha256", RANKING_SOURCE),
        ("comparison_source_sha256", COMPARISON_SOURCE),
    ):
        if recorded["protocol"][key] != _json_hash(_read_json(repo / path)):
            raise ValueError(
                "Scientific source content hash does not match the projection"
            )
    _check_resources(repo / LESSON)
    for name in STATIC_FILES:
        if name.startswith("figures/"):
            source = repo / "modules/06-pfi" / name
            if (repo / LESSON / name).read_bytes() != source.read_bytes():
                raise ValueError(
                    f"Presentation figure diverges from its promoted scientific source: {name}"
                )
    return projected


def export_presentation(
    output_dir: pathlib.Path, repo_root: pathlib.Path | None = None
) -> dict:
    """Export listed static assets and scoped public data files, outside the repo.

    Require an absent or empty output directory. Do not remove unrelated files,
    and do not recursively copy from the source lesson or research directories.
    Shared course fonts are copied only into this independent distribution.
    """
    repo = pathlib.Path(repo_root or REPO).resolve()
    output = pathlib.Path(output_dir).expanduser().resolve()
    if output == repo or output.is_relative_to(repo):
        raise ValueError("Export into a temporary directory outside the repository")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError("The export directory must be absent or empty")
    payload = check_presentation(repo)
    output.mkdir(parents=True, exist_ok=True)
    lesson = repo / LESSON
    for name in STATIC_FILES:
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(lesson / name, destination)
    (output / "fonts").mkdir()
    for name in FONT_FILES:
        shutil.copyfile(repo / "tools/fonts" / name, output / "fonts" / name)
    for name in ("lecture.css", "method.html", "teacher-guide.css"):
        path = output / name
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "../../../../tools/fonts/", "fonts/"
            ),
            encoding="utf-8",
        )
    (output / DATA.parent).mkdir()
    shutil.copyfile(lesson / TEACHING_DATA, output / TEACHING_DATA)
    shutil.copyfile(lesson / MODEL_SELECTION_DATA, output / MODEL_SELECTION_DATA)
    (output / DATA).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    _check_resources(output)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--check",
        action="store_true",
        help="Validate canonical aggregate and teaching data, and static resources",
    )
    action.add_argument(
        "--output-dir",
        type=pathlib.Path,
        help="Export to an absent/empty directory outside the repository",
    )
    args = parser.parse_args()
    try:
        if args.check:
            check_presentation()
            print(
                "PFI presentation: aggregate and teaching schemas, source equality and static resources verified."
            )
        else:
            export_presentation(args.output_dir)
            print(
                "PFI presentation exported with scoped data files and explicitly selected static assets."
            )
    except (TypeError, ValueError, OSError, json.JSONDecodeError) as exc:
        parser.exit(1, f"PFI presentation: {exc}\n")


if __name__ == "__main__":
    main()
