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
import json
import math
import pathlib
import re
import shutil
import statistics

REPO = pathlib.Path(__file__).resolve().parents[1]
LESSON = pathlib.Path("modules/06-pfi/lecture/pfi-interactive")
SOURCE = pathlib.Path("modules/00-dataset/gold/pfi_slide_explainer.json")
DATA = pathlib.Path("data/pfi-aggregates.json")
TEACHING_DATA = pathlib.Path("data/pfi-teaching-records.json")
TEACHING_SOURCE = pathlib.Path("modules/06-pfi/evidence/pfi_teaching_demo.json")

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
    "equations": {"difference": str, "ratio": str, "brier": str},
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
    "figures/equation-brier.svg",
    "figures/equation-difference.svg",
    "figures/equation-ratio.svg",
    "figures/pfi-age-repeats.svg",
    "figures/pfi-dependence.svg",
    "figures/pfi-slide-difference.svg",
    "figures/pfi-slide-ratio.svg",
)
FONT_FILES = ("Inter-Regular.ttf", "Inter-Medium.ttf", "OFL-Inter.txt")


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
        if not 0 <= p <= 1:
            raise ValueError(f"{label}: Brier outside its binary range")
        _equal(p - baseline, d, f"{label} repeat")


def _validate_values(payload):
    protocol, study = payload["protocol"], payload["study"]
    baseline = payload["original"]["brier"]
    repeats = protocol["repeats"]
    if not 0 < baseline <= 1 or repeats < 2:
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
    _equal(study["test_brier"], baseline, "study baseline")
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
    if dp["repeats"] != repeats or dp["n"] != protocol["n_evaluation"]:
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


def project_aggregates(source: dict) -> dict:
    """Return the explicit aggregate projection, validating its numerical contract.

    Extra fields in the research source are intentionally unselected. A nested
    object cannot replace a selected scalar, so newly introduced patient data
    cannot pass through a supposedly aggregate field.
    """
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


TEACHING_ROW = {
    "record": str,
    "idade_anos": NUMBER,
    "saturacao": str,
    "y_obito": int,
    "p_original": NUMBER,
    "class_original": int,
    "correct_original": bool,
    "brier_original": NUMBER,
    "p_after_age": NUMBER,
    "class_after_age": int,
    "correct_after_age": bool,
    "brier_after_age": NUMBER,
    "p_after_oxygen": NUMBER,
    "class_after_oxygen": int,
    "correct_after_oxygen": bool,
    "brier_after_oxygen": NUMBER,
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
    "individual_brier": [NUMBER],
    "sample_brier_mean": NUMBER,
    "full_test_single_brier": NUMBER,
    "full_test": RANKING_ROW,
}
TEACHING_SCHEMA = {
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
                row["brier_" + suffix],
                (probability - row["y_obito"]) ** 2,
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
            "individual_brier",
        ):
            if len(round_[field]) != n:
                raise ValueError("Teaching round fields must match the row count")
        if round_["values"] != [r[round_["feature"]] for r in rows]:
            raise ValueError("Teaching round must start from original input values")
        if not 0 <= round_["full_test_single_brier"] <= 1:
            raise ValueError("Displayed full-test Brier is outside its binary range")
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
                round_["individual_brier"][i],
                row["brier_after_" + suffix],
                "teaching loss",
            )
            if (
                round_["correct"][i] != row["correct_after_" + suffix]
                or round_["predicted"][i] != row["class_after_" + suffix]
            ):
                raise ValueError("Teaching round decisions disagree with their rows")
        _equal(
            round_["sample_brier_mean"],
            statistics.mean(round_["individual_brier"]),
            "teaching mean Brier",
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
            round_["full_test_single_brier"],
            result["metrics"]["brier"]["after"][0],
            "displayed full-test repeat",
        )
    _check_resources(repo / LESSON)
    for name in STATIC_FILES:
        if name.startswith("figures/"):
            source = repo / "modules/00-dataset" / name
            if (repo / LESSON / name).read_bytes() != source.read_bytes():
                raise ValueError(
                    f"Presentation figure diverges from its promoted scientific source: {name}"
                )
    return projected


def export_presentation(
    output_dir: pathlib.Path, repo_root: pathlib.Path | None = None
) -> dict:
    """Export listed static assets and the two scoped data files, outside the repo.

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
