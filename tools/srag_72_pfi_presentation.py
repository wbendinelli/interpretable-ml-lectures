"""Fase 72 — exportação documentada da apresentação de PFI (módulo 10).

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
LESSON = pathlib.Path("modules/10-pfi/lecture/pfi-interactive")
SOURCE = pathlib.Path("modules/00-dataset/gold/pfi_slide_explainer.json")
DATA = pathlib.Path("data/pfi-aggregates.json")
TEACHING_DATA = pathlib.Path("data/pfi-teaching-records.json")
RANKING_SOURCE = pathlib.Path("modules/00-dataset/gold/pfi_ranking.json")
COMPARISON_SOURCE = pathlib.Path("modules/10-pfi/evidence/pfi_metric_comparison.json")
TEACHING_SOURCE = pathlib.Path("modules/10-pfi/evidence/pfi_teaching_demo.json")
MODEL_SELECTION_DATA = pathlib.Path("data/model-selection.json")
SELECTION_SOURCE = pathlib.Path("modules/00-dataset/gold/selection_metrics.json")
BALANCE_SOURCE = pathlib.Path("modules/00-dataset/gold/sample_balance_search.json")
FAMILY_SEARCH_SOURCE = pathlib.Path("modules/00-dataset/gold/sample_family_search.json")
SUBGROUP_SOURCE = pathlib.Path("modules/10-pfi/evidence/pfi_diabetes_subgroups.json")
SUBGROUP_DATA = pathlib.Path("data/pfi-diabetes-subgroups.json")
AGE_SUBGROUP_SOURCE = pathlib.Path("modules/10-pfi/evidence/pfi_age_cardiopathy.json")
AGE_CANDIDATES_SOURCE = pathlib.Path(
    "modules/10-pfi/evidence/pfi_subgroup_candidates.json"
)
AGE_SUBGROUP_DATA = pathlib.Path("data/pfi-age-cardiopathy.json")

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
SUBGROUP_MEASURES = ("after", "difference", "ratio", "relative_percent")
SUBGROUP_TRACE = {
    **{key: [NUMBER] for key in SUBGROUP_MEASURES},
    **{
        key + suffix: NUMBER for key in SUBGROUP_MEASURES for suffix in ("_mean", "_sd")
    },
    **{"first_" + key: NUMBER for key in SUBGROUP_MEASURES},
}
SUBGROUP_SCOPE = {
    "n": int,
    "events": int,
    "baseline": NUMBER,
    "baseline_sd": NUMBER,
    "marginal": SUBGROUP_TRACE,
    "within": SUBGROUP_TRACE,
}
SUBGROUP_AXIS = {
    "key": str,
    "label": str,
    "levels": [str],
    "level_labels": {"nao": str, "sim": str},
}
SUBGROUP_PLOT_STATE = {
    "counts": [[int]],
    "n": int,
    "phi": NUMBER,
    "changed_n": int,
    "x_marginals": [int],
    "y_marginals": [int],
    "conditional": [[NUMBER]],
    "conditional_percent": [[NUMBER]],
}
SUBGROUP_SCHEMA = {
    "schema_version": str,
    "metadata": {
        **{
            key: str
            for key in (
                "source_path",
                "source_sha256",
                "source_notebook",
                "source_section",
                "reference_protocol_path",
                "reference_protocol_sha256",
                "protocol_hash_encoding",
                "model_raw_sha256",
                "model_raw_format",
                "split",
                "metric",
                "feature",
                "fixed_group_feature",
                "sampling",
                "first_order_sha256",
                "all_orders_sha256",
                "first_within_order_sha256",
                "all_within_orders_sha256",
            )
        },
        **{
            key: int
            for key in (
                "n_train",
                "n_full_test",
                "n_cohort",
                "n_excluded",
                "year",
                "seed",
                "repeats",
                "sd_ddof",
            )
        },
        "xgb_params": PARAMS,
    },
    "full_test_reference": {
        key: {"reconstructed": NUMBER, "registered": NUMBER}
        for key in ("logloss", "brier", "auc")
    },
    "rules": {
        key: str
        for key in (
            "model",
            "cohort",
            "baseline",
            "marginal",
            "within",
            "loss",
            "aggregation",
            "sd",
            "relative_percent",
            "degenerate",
            "interpretation",
        )
    },
    "results": {
        "global": SUBGROUP_SCOPE,
        "groups": [{"cardio": str, "weight": NUMBER, **SUBGROUP_SCOPE}],
    },
    "plot": {
        "x": SUBGROUP_AXIS,
        "y": SUBGROUP_AXIS,
        "states": {
            key: SUBGROUP_PLOT_STATE for key in ("original", "marginal", "within")
        },
        "within_flows": {
            "levels": [str],
            "level_labels": {"nao": str, "sim": str},
            "counts_orientation": str,
            "groups": [
                {
                    "cardio": str,
                    "n": int,
                    "counts": [[int]],
                    "changed_n": int,
                    "unchanged_n": int,
                    "no_to_yes_n": int,
                    "yes_to_no_n": int,
                }
            ],
        },
        "source_procedure": str,
    },
    "checks": {
        **{
            key: NUMBER
            for key in (
                "manual_loss_max_gap",
                "weighted_loss_max_gap",
                "weighted_difference_max_gap",
            )
        },
        **{
            key: bool
            for key in (
                "model_raw_unchanged",
                "original_inputs_unchanged",
                "target_unchanged",
                "other_39_inputs_unchanged_each_repeat",
                "first_diagram_matches_section20",
            )
        },
    },
}
PRESENTATION = {
    "row_diagrams": "real SRAG teaching records in a separate, explicitly scoped evidence file",
    "empirical_results": "aggregate fixed-model, temporal-test measurements",
}
AGE_GAP_SUMMARY = {
    key: NUMBER
    for key in (
        "mean",
        "sd",
        "first",
        "relative_percent_mean",
        "relative_percent_sd",
        "first_relative_percent",
    )
}
AGE_SCOPE = {"n": int, "events": int, "baseline": NUMBER}
AGE_STATE = {
    "counts": [[int]],
    "n": int,
    "changed_age_n": int,
    "changed_bin_n": int,
    "x_marginals": [int],
    "y_marginals": [int],
    "conditional": [[NUMBER]],
    "conditional_percent": [[NUMBER]],
}
AGE_SCHEMA = {
    "schema_version": str,
    "metadata": {
        **{
            key: str
            for key in (
                "source_path",
                "source_sha256",
                "source_notebook",
                "source_section",
                "reused_evidence_path",
                "reused_evidence_sha256",
                "reused_candidate",
                "reused_section",
                "reference_protocol_sha256",
                "model_raw_sha256",
                "split",
                "feature",
                "fixed_group_feature",
                "metric",
                "selection",
                "counts_orientation",
                "flow_orientation",
            )
        },
        **{
            key: int
            for key in (
                "n_train",
                "n_full_test",
                "n_cohort",
                "n_excluded",
                "events",
                "input_n",
                "year",
                "seed",
                "repeats",
                "sd_ddof",
                "displayed_repeat",
            )
        },
        "orders": {
            key: str
            for key in (
                "first_sha256",
                "all_sha256",
                "within_first_sha256",
                "within_all_sha256",
            )
        },
    },
    "bins": [
        {
            "index": int,
            "label": str,
            "lower_inclusive": NUMBER,
            "upper_exclusive": (int, float, type(None)),
        }
    ],
    "association": {
        "pearson_continuous_original": NUMBER,
        "cramers_v_binned_original": NUMBER,
        "distinction": str,
    },
    "results": {
        "global": {
            **AGE_SCOPE,
            "marginal": SUBGROUP_TRACE,
            "within": SUBGROUP_TRACE,
            "gap": {
                **AGE_GAP_SUMMARY,
                "difference": [NUMBER],
                "relative_percent": [NUMBER],
            },
        },
        "groups": [
            {
                **AGE_SCOPE,
                "level": str,
                "label": str,
                "weight": NUMBER,
                "gap": AGE_GAP_SUMMARY,
                **{
                    mode: {
                        key: NUMBER
                        for key in SUBGROUP_TRACE
                        if key not in SUBGROUP_MEASURES
                    }
                    for mode in ("marginal", "within")
                },
            }
        ],
    },
    "first_losses": {key: NUMBER for key in ("original", "marginal", "within")},
    "plot": {
        "x": {"key": str, "labels": [str]},
        "y": {"key": str, "levels": [str]},
        "states": {key: AGE_STATE for key in ("original", "marginal", "within")},
    },
    "flows": {
        mode: [
            {
                "cardio": str,
                "n": int,
                "counts": [[int]],
                **{
                    key: int
                    for key in (
                        "changed_age_n",
                        "changed_bin_n",
                        "same_bin_n",
                        "age_changed_same_bin_n",
                    )
                },
                "outgoing_changed_bin": [int],
                "incoming_changed_bin": [int],
            }
        ]
        for mode in ("marginal", "within")
    },
    "rules": {
        key: str
        for key in (
            "age",
            "bins",
            "permutation",
            "reuse",
            "percentages",
            "flows",
            "interpretation",
            "uncertainty",
            "scope",
        )
    },
    "checks": {
        key: bool
        for key in (
            "results_equal_section8",
            "orders_equal_section8",
            "first_losses_equal_section8",
            "within_binned_joint_equal_original",
            "real_age_supplied_to_model",
            "other_39_inputs_fixed",
            "original_inputs_unchanged",
            "target_unchanged",
            "model_raw_unchanged",
        )
    },
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
    "subgroup-pfi.js",
    "subgroup-pfi.css",
    "age-subgroup-pfi.js",
    "age-subgroup-pfi.css",
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


def _subgroup_matrix(value, label):
    if len(value) != 2 or any(len(row) != 2 for row in value):
        raise ValueError(f"{label}: expected a two-by-two matrix")
    return value


def _validate_subgroup_values(payload, reference):
    meta, protocol = payload["metadata"], reference["protocol"]
    if payload["schema_version"] != "srag-diabetes-subgroup-pfi-v1":
        raise ValueError("Unknown subgroup evidence schema")
    expected = {
        "source_path": "modules/00-dataset/gold/gold_covid_obito_sample.parquet",
        "source_sha256": protocol["sample_sha256"],
        "source_notebook": "modules/10-pfi/notebooks/pfi_internals.ipynb",
        "source_section": "§7",
        "reference_protocol_path": str(RANKING_SOURCE),
        "xgb_params": protocol["xgb_params"],
        "model_raw_format": "ubj",
        "n_train": protocol["n_train"],
        "n_full_test": protocol["n_evaluation"],
        "year": protocol["period"],
        "split": "test",
        "metric": "log_loss",
        "feature": "diabetes",
        "fixed_group_feature": "cardiopati",
        "seed": protocol["permutation_seed"],
        "repeats": protocol["repeats"],
        "sd_ddof": 1,
    }
    if any(meta[key] != value for key, value in expected.items()):
        raise ValueError("Subgroup evidence disagrees with the historical protocol")
    protocol_hash = hashlib.sha256(
        json.dumps(
            protocol, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
    if meta["reference_protocol_sha256"] != protocol_hash:
        raise ValueError("Subgroup reference protocol content hash differs")
    for key, value in meta.items():
        if key.endswith("sha256") and not re.fullmatch(r"[0-9a-f]{64}", value):
            raise ValueError(f"Invalid subgroup evidence hash: {key}")
    n, repeats = meta["n_cohort"], meta["repeats"]
    if n <= 0 or repeats < 2 or meta["n_excluded"] != meta["n_full_test"] - n:
        raise ValueError("Invalid subgroup cohort/repetition counts")
    if meta["n_excluded"] < 0:
        raise ValueError("Subgroup cohort exceeds the temporal test")
    for key, values in payload["full_test_reference"].items():
        _equal(
            values["reconstructed"], reference["original"][key], "full-test reference"
        )
        _equal(values["registered"], reference["original"][key], "registered reference")

    overall, groups = payload["results"]["global"], payload["results"]["groups"]
    if [group["cardio"] for group in groups] != ["nao", "sim"]:
        raise ValueError("Expected the two original cardiopathy groups")
    if overall["n"] != n or sum(group["n"] for group in groups) != n:
        raise ValueError("Subgroup sizes do not sum to the closed cohort")
    if sum(group["events"] for group in groups) != overall["events"]:
        raise ValueError("Subgroup event counts disagree with the cohort")
    for scope in [overall, *groups]:
        if scope["n"] <= 0 or not 0 <= scope["events"] <= scope["n"]:
            raise ValueError("Invalid subgroup size or outcome count")
        baseline = scope["baseline"]
        if baseline <= 0 or scope["baseline_sd"] != 0:
            raise ValueError("Subgroup baseline must be positive and fixed")
        for mode in ("marginal", "within"):
            trace = scope[mode]
            _trace(trace["after"], trace["difference"], baseline, repeats, mode)
            for key in SUBGROUP_MEASURES:
                values = trace[key]
                if len(values) != repeats or trace[key + "_sd"] < 0:
                    raise ValueError("Invalid subgroup vector length or SD")
                _equal(trace["first_" + key], values[0], "first subgroup repeat")
                _equal(trace[key + "_mean"], statistics.mean(values), "subgroup mean")
                _equal(trace[key + "_sd"], statistics.stdev(values), "subgroup SD")
            for after, ratio, percent in zip(
                trace["after"], trace["ratio"], trace["relative_percent"], strict=True
            ):
                _equal(after / baseline, ratio, "subgroup ratio")
                _equal((ratio - 1) * 100, percent, "subgroup relative percent")
    for group in groups:
        _equal(group["weight"], group["n"] / n, "subgroup sample weight")
    _equal(
        overall["baseline"],
        sum(group["weight"] * group["baseline"] for group in groups),
        "pooled subgroup baseline",
    )
    for mode in ("marginal", "within"):
        for index in range(repeats):
            for key in ("after", "difference"):
                _equal(
                    overall[mode][key][index],
                    sum(group["weight"] * group[mode][key][index] for group in groups),
                    "pooled subgroup " + key,
                )

    plot = payload["plot"]
    for axis, key in (("x", "diabetes"), ("y", "cardiopati")):
        if plot[axis]["key"] != key or plot[axis]["levels"] != ["nao", "sim"]:
            raise ValueError("Subgroup diagram axes or levels disagree")
    original = plot["states"]["original"]
    for name, state in plot["states"].items():
        counts = _subgroup_matrix(state["counts"], name)
        conditional = _subgroup_matrix(state["conditional"], name)
        percentages = _subgroup_matrix(state["conditional_percent"], name)
        if any(value < 0 for row in counts for value in row):
            raise ValueError("Negative subgroup diagram count")
        rows = [sum(row) for row in counts]
        columns = [sum(row[col] for row in counts) for col in range(2)]
        if (
            state["n"] != n
            or sum(rows) != n
            or rows != state["y_marginals"]
            or columns != state["x_marginals"]
            or rows != [group["n"] for group in groups]
            or rows != original["y_marginals"]
            or columns != original["x_marginals"]
            or not 0 <= state["changed_n"] <= n
        ):
            raise ValueError("Subgroup diagram counts/margins disagree")
        for row in range(2):
            for col in range(2):
                _equal(
                    conditional[row][col],
                    counts[row][col] / rows[row],
                    "conditional proportion",
                )
                _equal(
                    percentages[row][col],
                    100 * conditional[row][col],
                    "conditional percentage",
                )
        a, b, c, d = (float(value) for row in counts for value in row)
        denominator = math.sqrt(math.prod(rows) * math.prod(columns))
        if denominator == 0:
            raise ValueError("Subgroup diagram requires two nonconstant inputs")
        _equal(state["phi"], (a * d - b * c) / denominator, "diagram phi")
    if (
        original["changed_n"] != 0
        or plot["states"]["within"]["counts"] != original["counts"]
    ):
        raise ValueError(
            "Within-group permutation must preserve the original joint table"
        )
    flows = plot["within_flows"]
    if flows["levels"] != ["nao", "sim"] or [g["cardio"] for g in flows["groups"]] != [
        "nao",
        "sim",
    ]:
        raise ValueError("Subgroup transition labels disagree")
    for index, flow in enumerate(flows["groups"]):
        counts = _subgroup_matrix(flow["counts"], "within transitions")
        if any(value < 0 for row in counts for value in row):
            raise ValueError("Negative subgroup transition count")
        margins = original["counts"][index]
        if (
            [sum(row) for row in counts] != margins
            or [sum(row[col] for row in counts) for col in range(2)] != margins
            or flow["n"] != groups[index]["n"]
            or flow["no_to_yes_n"] != counts[0][1]
            or flow["yes_to_no_n"] != counts[1][0]
            or counts[0][1] != counts[1][0]
            or flow["changed_n"] != counts[0][1] + counts[1][0]
            or flow["unchanged_n"] != counts[0][0] + counts[1][1]
        ):
            raise ValueError("Subgroup transition counts disagree")
    if (
        sum(flow["changed_n"] for flow in flows["groups"])
        != plot["states"]["within"]["changed_n"]
    ):
        raise ValueError("Subgroup transitions do not sum to the displayed changes")
    for key, value in payload["checks"].items():
        if isinstance(value, bool):
            if not value:
                raise ValueError("Failed scientific subgroup invariant: " + key)
        elif not 0 <= value <= 1e-12:
            raise ValueError("Subgroup audit discrepancy: " + key)


def project_subgroup_pfi(source: dict, reference: dict | None = None) -> dict:
    """Select aggregate subgroup evidence only; never carry unlisted fields."""
    payload = _project(source, SUBGROUP_SCHEMA, "subgroup")
    reference = (
        reference if reference is not None else _read_json(REPO / RANKING_SOURCE)
    )
    _validate_subgroup_values(payload, reference)
    return payload


def validate_subgroup_pfi(payload: dict, source: dict, reference: dict) -> None:
    """Require the scoped schema and agreement with committed scientific evidence."""
    if payload != project_subgroup_pfi(payload, reference):
        raise ValueError("Subgroup payload contains unselected fields")
    if payload != project_subgroup_pfi(source, reference):
        raise ValueError("Subgroup data diverge from their recorded evidence")


def _validate_age_subgroup_values(payload, reference, candidates, candidates_hash):
    meta, protocol = payload["metadata"], reference["protocol"]
    candidate = next(
        row
        for row in candidates["candidates"]
        if row["id"] == "idade_anos__by__cardiopati"
    )
    expected = {
        "source_path": "modules/00-dataset/gold/gold_covid_obito_sample.parquet",
        "source_sha256": protocol["sample_sha256"],
        "source_notebook": "modules/10-pfi/notebooks/pfi_internals.ipynb",
        "source_section": "§9",
        "reused_evidence_path": str(AGE_CANDIDATES_SOURCE),
        "reused_evidence_sha256": candidates_hash,
        "reused_candidate": candidate["id"],
        "reused_section": "§8",
        "feature": "idade_anos",
        "fixed_group_feature": "cardiopati",
        "split": "test",
        "metric": "log_loss",
        "sd_ddof": 1,
        "displayed_repeat": 1,
        "n_train": protocol["n_train"],
        "n_full_test": protocol["n_evaluation"],
        "year": protocol["period"],
        "seed": protocol["permutation_seed"],
        "repeats": protocol["repeats"],
        "input_n": len(candidates["metadata"]["features"]),
        "model_raw_sha256": candidates["metadata"]["model_raw_sha256"],
        "reference_protocol_sha256": hashlib.sha256(
            json.dumps(
                protocol, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest(),
        "orders": candidate["orders"],
        "n_cohort": candidate["cohort"]["n"],
        "n_excluded": candidate["cohort"]["n_excluded"],
        "events": candidate["cohort"]["events"],
    }
    if (
        payload["schema_version"] != "srag-age-cardiopathy-preview-v1"
        or any(meta[key] != value for key, value in expected.items())
        or payload["results"] != candidate["results"]
    ):
        raise ValueError(
            "Age subgroup evidence disagrees with its recorded protocol/candidate"
        )
    for obj in (meta, meta["orders"]):
        for key, value in obj.items():
            if key.endswith("sha256") and not re.fullmatch(r"[0-9a-f]{64}", value):
                raise ValueError("Invalid age subgroup provenance hash: " + key)
    n, repeats = meta["n_cohort"], meta["repeats"]
    if n <= 0 or repeats < 2 or meta["n_excluded"] != meta["n_full_test"] - n:
        raise ValueError("Invalid age subgroup cohort/repetition counts")
    if meta["n_excluded"] < 0 or not all(payload["checks"].values()):
        raise ValueError("Failed age subgroup invariant")
    expected_bins = [
        (0, 18, "<18"),
        (18, 40, "18–<40"),
        (40, 60, "40–<60"),
        (60, 80, "60–<80"),
        (80, None, "80+"),
    ]
    if payload["bins"] != [
        {"index": i, "label": label, "lower_inclusive": lower, "upper_exclusive": upper}
        for i, (lower, upper, label) in enumerate(expected_bins)
    ]:
        raise ValueError("Age display bins disagree with the fixed display protocol")
    association = payload["association"]
    _equal(
        association["pearson_continuous_original"],
        candidate["association"]["pearson_r"],
        "continuous-age Pearson association",
    )
    overall, groups = payload["results"]["global"], payload["results"]["groups"]
    if (
        [g["level"] for g in groups] != ["nao", "sim"]
        or overall["n"] != n
        or sum(g["n"] for g in groups) != n
        or sum(g["events"] for g in groups) != overall["events"]
        or overall["events"] != meta["events"]
    ):
        raise ValueError("Age subgroup sizes/events disagree")
    for scope in [overall, *groups]:
        if (
            scope["n"] <= 0
            or not 0 <= scope["events"] <= scope["n"]
            or scope["baseline"] <= 0
        ):
            raise ValueError("Invalid age subgroup size, outcome count or baseline")
        for mode in ("marginal", "within"):
            trace = scope[mode]
            for measure in SUBGROUP_MEASURES:
                if trace[measure + "_sd"] < 0:
                    raise ValueError("Negative age subgroup SD")
                if scope is overall:
                    values = trace[measure]
                    if len(values) != repeats:
                        raise ValueError(
                            "Age trace length differs from the permutation protocol"
                        )
                    _equal(trace["first_" + measure], values[0], "first age repeat")
                    _equal(
                        trace[measure + "_mean"],
                        statistics.mean(values),
                        "age trace mean",
                    )
                    _equal(
                        trace[measure + "_sd"],
                        statistics.stdev(values),
                        "age sample SD",
                    )
            _equal(
                trace["after_mean"] - scope["baseline"],
                trace["difference_mean"],
                "age mean PFI difference",
            )
            _equal(
                trace["first_after"] - scope["baseline"],
                trace["first_difference"],
                "first age PFI difference",
            )
            _equal(
                trace["ratio_mean"],
                trace["after_mean"] / scope["baseline"],
                "age mean ratio",
            )
            _equal(
                trace["relative_percent_mean"],
                (trace["ratio_mean"] - 1) * 100,
                "age mean relative percent",
            )
    for group in groups:
        _equal(group["weight"], group["n"] / n, "age group weight")
    _equal(
        overall["baseline"],
        sum(g["weight"] * g["baseline"] for g in groups),
        "weighted age baseline",
    )
    for mode in ("marginal", "within"):
        trace = overall[mode]
        _trace(
            trace["after"],
            trace["difference"],
            overall["baseline"],
            repeats,
            "age " + mode,
        )
        _equal(
            payload["first_losses"][mode], trace["after"][0], "first displayed age loss"
        )
        for after, ratio, percent in zip(
            trace["after"], trace["ratio"], trace["relative_percent"], strict=True
        ):
            _equal(ratio, after / overall["baseline"], "age repeat ratio")
            _equal(percent, (ratio - 1) * 100, "age repeat relative percent")
        for key in ("after_mean", "first_after", "difference_mean", "first_difference"):
            _equal(
                trace[key],
                sum(g["weight"] * g[mode][key] for g in groups),
                "weighted age " + key,
            )
    _equal(
        payload["first_losses"]["original"], overall["baseline"], "original age loss"
    )
    gap = overall["gap"]
    for i, (free, within) in enumerate(
        zip(
            overall["marginal"]["difference"],
            overall["within"]["difference"],
            strict=True,
        )
    ):
        _equal(gap["difference"][i], free - within, "paired age PFI gap")
        _equal(
            gap["relative_percent"][i],
            100 * (free - within) / overall["baseline"],
            "paired age relative gap",
        )
    for key, values in (
        ("", gap["difference"]),
        ("relative_percent_", gap["relative_percent"]),
    ):
        _equal(gap[key + "mean"], statistics.mean(values), "paired age mean gap")
        _equal(gap[key + "sd"], statistics.stdev(values), "paired age gap SD")
    plot, bins = payload["plot"], len(payload["bins"])
    if plot["x"] != {
        "key": "age_bin",
        "labels": [b["label"] for b in payload["bins"]],
    } or plot["y"] != {"key": "cardiopati", "levels": ["nao", "sim"]}:
        raise ValueError("Age subgroup diagram axes disagree")
    original = plot["states"]["original"]
    for state in plot["states"].values():
        counts = state["counts"]
        if any(
            len(state[key]) != 2 or any(len(row) != bins for row in state[key])
            for key in ("counts", "conditional", "conditional_percent")
        ) or any(value < 0 for row in counts for value in row):
            raise ValueError("Invalid age subgroup count matrix")
        rows, cols = (
            [sum(row) for row in counts],
            [sum(row[c] for row in counts) for c in range(bins)],
        )
        if (
            state["n"] != n
            or sum(rows) != n
            or rows != [g["n"] for g in groups]
            or rows != state["y_marginals"]
            or cols != state["x_marginals"]
            or cols != original["x_marginals"]
            or not 0 <= state["changed_bin_n"] <= state["changed_age_n"] <= n
        ):
            raise ValueError("Age diagram counts, margins or changes disagree")
        for r in range(2):
            for c in range(bins):
                _equal(
                    state["conditional"][r][c],
                    counts[r][c] / rows[r],
                    "age row proportion",
                )
                _equal(
                    state["conditional_percent"][r][c],
                    100 * counts[r][c] / rows[r],
                    "age row percentage",
                )
    if (
        original["changed_age_n"] != 0
        or plot["states"]["within"]["counts"] != original["counts"]
    ):
        raise ValueError(
            "Within-cardio permutation must preserve the age-bin joint table"
        )
    chi2 = sum(
        (
            original["counts"][r][c]
            - original["y_marginals"][r] * original["x_marginals"][c] / n
        )
        ** 2
        / (original["y_marginals"][r] * original["x_marginals"][c] / n)
        for r in range(2)
        for c in range(bins)
    )
    _equal(
        association["cramers_v_binned_original"],
        math.sqrt(chi2 / n),
        "binned-age Cramer V",
    )
    for mode, flows in payload["flows"].items():
        if [f["cardio"] for f in flows] != ["nao", "sim"]:
            raise ValueError("Age flow groups disagree")
        for r, flow in enumerate(flows):
            counts = flow["counts"]
            if (
                len(counts) != bins
                or any(len(row) != bins for row in counts)
                or any(v < 0 for row in counts for v in row)
            ):
                raise ValueError("Invalid age flow matrix")
            outgoing = [sum(row) - row[i] for i, row in enumerate(counts)]
            incoming = [
                sum(row[c] for row in counts) - counts[c][c] for c in range(bins)
            ]
            same = sum(counts[i][i] for i in range(bins))
            if (
                [sum(row) for row in counts] != original["counts"][r]
                or [sum(row[c] for row in counts) for c in range(bins)]
                != plot["states"][mode]["counts"][r]
                or flow["n"] != groups[r]["n"]
                or flow["same_bin_n"] != same
                or flow["changed_bin_n"] != flow["n"] - same
                or flow["outgoing_changed_bin"] != outgoing
                or flow["incoming_changed_bin"] != incoming
                or not 0 <= flow["age_changed_same_bin_n"] <= same
                or flow["changed_age_n"]
                != flow["changed_bin_n"] + flow["age_changed_same_bin_n"]
            ):
                raise ValueError("Age flow counts disagree with before/after states")
        for key in ("changed_age_n", "changed_bin_n"):
            if sum(flow[key] for flow in flows) != plot["states"][mode][key]:
                raise ValueError("Age flows do not sum to the displayed changes")


def project_age_subgroup_pfi(
    source, reference=None, candidates=None, candidates_hash=None
):
    """Select aggregate age evidence; display bins never become model inputs."""
    reference = (
        reference if reference is not None else _read_json(REPO / RANKING_SOURCE)
    )
    candidates = (
        candidates
        if candidates is not None
        else _read_json(REPO / AGE_CANDIDATES_SOURCE)
    )
    if candidates_hash is None:
        candidates_hash = hashlib.sha256(
            (REPO / AGE_CANDIDATES_SOURCE).read_bytes()
        ).hexdigest()
    payload = _project(source, AGE_SCHEMA, "age_subgroup")
    _validate_age_subgroup_values(payload, reference, candidates, candidates_hash)
    return payload


def validate_age_subgroup_pfi(payload, source, reference, candidates, candidates_hash):
    """Require the declared public schema and exact committed-evidence projection."""
    if payload != project_age_subgroup_pfi(
        payload, reference, candidates, candidates_hash
    ):
        raise ValueError("Age subgroup payload contains unselected fields")
    if payload != project_age_subgroup_pfi(
        source, reference, candidates, candidates_hash
    ):
        raise ValueError("Age subgroup data diverge from their recorded evidence")


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
    validate_subgroup_pfi(
        _read_json(repo / LESSON / SUBGROUP_DATA),
        _read_json(repo / SUBGROUP_SOURCE),
        experiment,
    )
    validate_age_subgroup_pfi(
        _read_json(repo / LESSON / AGE_SUBGROUP_DATA),
        _read_json(repo / AGE_SUBGROUP_SOURCE),
        experiment,
        _read_json(repo / AGE_CANDIDATES_SOURCE),
        hashlib.sha256((repo / AGE_CANDIDATES_SOURCE).read_bytes()).hexdigest(),
    )
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
            source = repo / "modules/10-pfi" / name
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
    shutil.copyfile(lesson / SUBGROUP_DATA, output / SUBGROUP_DATA)
    shutil.copyfile(lesson / AGE_SUBGROUP_DATA, output / AGE_SUBGROUP_DATA)
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
