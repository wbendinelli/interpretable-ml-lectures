"""Gerar a janela de fichas reais de uma repetição da PFI do teste completo.

As mesmas fichas históricas são somente receptores visíveis. Seus doadores
vêm da primeira ordem do experimento global registrado, sorteada sobre todo
o teste. Não há seleção de ordem pelo resultado. Índices, posições e
identificadores dos doadores nunca são exportados. O modelo já ajustado é
recebido; este gerador não seleciona fichas, treina, escreve ou publica.
"""

from __future__ import annotations

import copy
import hashlib
import json

import numpy as np
import pandas as pd
import srag_70_explain as E
from sklearn.metrics import log_loss, roc_auc_score


def individual_logloss(target: np.ndarray, probability: np.ndarray) -> np.ndarray:
    """Binary natural-log loss using the recorded float64 clipping convention."""
    probability = np.asarray(probability, dtype=np.float64)
    eps = np.finfo(np.float64).eps
    clipped = np.clip(probability, eps, 1 - eps)
    return np.where(np.asarray(target) == 1, -np.log(clipped), -np.log1p(-clipped))


def _probability(fitted_model, inputs: pd.DataFrame) -> np.ndarray:
    """Probabilidade da classe óbito, preservando a precisão do preditor."""
    if not np.array_equal(fitted_model.classes_, [0, 1]):
        raise ValueError("O preditor deve ter classes 0 e 1, nesta ordem.")
    prediction = np.asarray(fitted_model.predict_proba(inputs), dtype=np.float64)
    if prediction.shape != (len(inputs), 2):
        raise ValueError("O preditor deve retornar duas probabilidades por ficha.")
    probability = prediction[:, 1]
    if not np.all(np.isfinite(probability) & (probability >= 0) & (probability <= 1)):
        raise ValueError("Probabilidades inválidas na demonstração.")
    return probability


# This is a regression acceptance budget for the recorded binary32 predictor,
# not a universal XGBoost error bound. Conversion to float64 cannot recover
# bits already rounded during training, tree accumulation and probability output.
REFERENCE_PROBABILITY_ULPS = 8
REFERENCE_STRUCTURE_SHA256 = (
    "d8cebf0e21f762aa8588bc1a819078d4e8071743f6e19207e6b0a64adf8523ac"
)


def structure_sha256(fitted_model) -> str:
    """Fingerprint every decision rule, excluding floating fitted leaf weights.

    Topology, categories, internal cut values, feature order and objective/base
    score must be identical. A small numeric agreement never substitutes for
    this contract. Leaf-weight drift from refitting is checked at prediction
    precision; serialized model bytes must stay fixed within each PFI run.
    """
    learner = json.loads(fitted_model.get_booster().save_raw(raw_format="json"))[
        "learner"
    ]
    gradient = learner["gradient_booster"]
    if (
        gradient["name"] != "gbtree"
        or learner["objective"]["name"] != "binary:logistic"
    ):
        raise ValueError("The recorded reference requires binary logistic gbtree.")
    tree_model = gradient["model"]
    trees = []
    for tree in tree_model["trees"]:
        decision = {
            key: value
            for key, value in tree.items()
            if key
            not in {"base_weights", "loss_changes", "sum_hessian", "split_conditions"}
        }
        decision["internal_cut_values"] = [
            None if child == -1 else value
            for child, value in zip(
                tree["left_children"], tree["split_conditions"], strict=True
            )
        ]
        trees.append(decision)
    structure = {
        "model_param": learner["learner_model_param"],
        "feature_names": learner["feature_names"],
        "feature_types": learner["feature_types"],
        "category_encoding": tree_model["cats"],
        "tree_model_param": tree_model["gbtree_model_param"],
        "objective": learner["objective"],
        "tree_info": tree_model["tree_info"],
        "iteration_indptr": tree_model["iteration_indptr"],
        "trees": trees,
    }
    return hashlib.sha256(
        json.dumps(
            structure, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def _binary32_probability(values) -> tuple[np.ndarray, np.ndarray]:
    promoted = np.asarray(values, dtype=np.float64)
    binary = promoted.astype(np.float32)
    if (
        not np.all(np.isfinite(promoted) & (promoted >= 0) & (promoted <= 1))
        or np.any(np.signbit(promoted))
        or not np.array_equal(binary.astype(np.float64), promoted)
    ):
        raise ValueError(
            "Reference comparisons require finite promoted binary32 probabilities."
        )
    return promoted, np.ascontiguousarray(binary).view(np.uint32)


def check_reference_probabilities(actual, recorded) -> dict:
    """Bound a cross-reconstruction comparison in representable float32 steps.

    Eight ULP is the declared acceptance budget for this frozen recipe/data,
    allowing guard bits across fitted weights, float32 tree accumulation and
    logistic output. It is not an error theorem for arbitrary models/builds.
    Structural, data and same-run oracle checks remain independent and exact.
    A different budget needs a documented investigation, never automatic scaling.
    """
    actual, a_bits = _binary32_probability(actual)
    recorded, r_bits = _binary32_probability(recorded)
    if actual.shape != recorded.shape:
        raise ValueError("Probability shapes differ from the recorded receivers.")
    distance = np.abs(a_bits.astype(np.int64) - r_bits.astype(np.int64))
    if np.any(distance > REFERENCE_PROBABILITY_ULPS):
        raise AssertionError(
            "Recorded probabilities exceed the declared binary32 reconstruction budget."
        )
    return {
        "max_ulp": int(distance.max(initial=0)),
        "max_abs": float(np.max(np.abs(actual - recorded), initial=0)),
        "budget_ulp": REFERENCE_PROBABILITY_ULPS,
    }


def reference_metric_interval(
    target, actual_probability, recorded, metric="logloss"
) -> dict:
    """Check a historical metric inside analytically propagated p±ULP bounds.

    For binary outcomes log loss and Brier are monotone in p on [0,1], so
    endpoint losses bound each row. Average endpoint bounds, with gamma_n
    binary64 roundoff for nonnegative summation/division and endpoint arithmetic.
    AUC is bounded by lowering positive scores/raising negative scores and the
    reverse; this also covers rank ties that binary32 rounding may create.
    No free atol/rtol parameter or platform-dependent branch is provided.
    """
    target = np.asarray(target)
    probability, bits = _binary32_probability(actual_probability)
    if target.shape != probability.shape or probability.ndim != 1 or not len(target):
        raise ValueError(
            "A nonempty target/probability vector of equal shape is required."
        )
    if not np.all(np.isin(target, [0, 1])):
        raise ValueError("The recorded metric uses binary outcomes.")
    one_bits = int(np.float32(1).view(np.uint32))
    lower_bits = np.maximum(
        0, bits.astype(np.int64) - REFERENCE_PROBABILITY_ULPS
    ).astype(np.uint32)
    upper_bits = np.minimum(
        one_bits, bits.astype(np.int64) + REFERENCE_PROBABILITY_ULPS
    ).astype(np.uint32)
    lower, upper = (
        lower_bits.view(np.float32).astype(np.float64),
        upper_bits.view(np.float32).astype(np.float64),
    )
    if metric == "auc":
        if not np.array_equal(np.unique(target), [0, 1]):
            raise ValueError("AUC requires both observed classes.")
        low = float(roc_auc_score(target, np.where(target == 1, lower, upper)))
        high = float(roc_auc_score(target, np.where(target == 1, upper, lower)))
    else:
        if metric == "logloss":
            left, right = (
                individual_logloss(target, lower),
                individual_logloss(target, upper),
            )
        elif metric == "brier":
            left, right = (lower - target) ** 2, (upper - target) ** 2
        else:
            raise ValueError("Only recorded log loss, Brier or AUC are supported.")
        lo, hi = np.minimum(left, right), np.maximum(left, right)
        if np.ndim(recorded) == 0:
            low, high = float(lo.mean()), float(hi.mean())
        else:
            low, high = lo, hi
    # u is unit roundoff. Individual comparisons have no n-term reduction.
    # Scale only by the computed nonnegative bounds: there is no absolute
    # loss-unit floor. Round the final interval outwards in binary64.
    unit = np.finfo(np.float64).eps / 2
    operations = len(target) + 8 if np.ndim(recorded) == 0 else 8
    gamma = operations * unit / (1 - operations * unit)
    rounding = gamma * np.maximum(np.abs(low), np.abs(high))
    low = np.maximum(0, np.nextafter(np.asarray(low) - rounding, -np.inf))
    high = np.nextafter(np.asarray(high) + rounding, np.inf)
    if metric in {"auc", "brier"}:
        high = np.minimum(1, high)
    reference = np.asarray(recorded, dtype=np.float64)
    if reference.shape != low.shape or not np.all(np.isfinite(reference)):
        raise ValueError("Recorded metric has an invalid shape or value.")
    if np.any((reference < low) | (reference > high)):
        raise AssertionError(
            "Recorded metric is outside the propagated probability-precision interval."
        )
    return {
        "lower": low,
        "upper": high,
        "reference": reference,
        "budget_ulp": REFERENCE_PROBABILITY_ULPS,
    }


def build_teaching_demo(
    fitted_model,
    full_inputs: pd.DataFrame,
    full_target: np.ndarray,
    receiver_positions: np.ndarray,
    historical_preview: dict,
    full_rows: list[dict],
    experiment: dict,
) -> dict:
    """Janela das mesmas fichas na primeira permutação GLOBAL registrada.

    As ordens são reproduzidas com o protocolo e conferidas pelo hash do
    estudo antes das novas previsões. Cada entrada é permutada a partir da
    matriz completa original; as trocas nunca se acumulam. Preservamos
    float32, categorias nativas, demais entradas e alvos. As posições dos
    receptores/doadores são usadas somente aqui e não aparecem na saída.
    """
    protocol = experiment["protocol"]
    params = fitted_model.get_params()
    if any(params.get(key) != value for key, value in protocol["xgb_params"].items()):
        raise ValueError("The predictor parameters must match the recorded recipe.")
    if list(full_inputs.columns) != protocol["features"]:
        raise ValueError("Input names and order must match the recorded experiment.")
    if structure_sha256(fitted_model) != REFERENCE_STRUCTURE_SHA256:
        raise ValueError(
            "The reconstructed decision rules differ from the recorded model."
        )
    full_target = np.asarray(full_target)
    receiver_positions = np.asarray(receiver_positions)
    historical_rows = historical_preview["rows"]
    if len(full_inputs) != protocol["n_evaluation"]:
        raise ValueError("A matriz precisa incluir todo o teste registrado.")
    if full_target.shape != (len(full_inputs),) or not np.all(
        np.isin(full_target, [0, 1])
    ):
        raise ValueError("Um desfecho binário original é necessário por ficha.")
    if (
        receiver_positions.shape != (len(historical_rows),)
        or len(receiver_positions) != 8
        or receiver_positions.dtype.kind not in "iu"
        or len(np.unique(receiver_positions)) != len(receiver_positions)
        or np.any((receiver_positions < 0) | (receiver_positions >= len(full_inputs)))
    ):
        raise ValueError("Indique as posições das oito mesmas fichas receptoras.")
    if full_inputs["idade_anos"].dtype != np.dtype("float32"):
        raise ValueError("Idade deve preservar o float32 da matriz original.")
    if not isinstance(full_inputs["saturacao"].dtype, pd.CategoricalDtype):
        raise TypeError("Saturação deve preservar categorias nativas.")
    case_inputs = full_inputs.iloc[receiver_positions]
    case_target = full_target[receiver_positions]
    for feature in ("idade_anos", "saturacao"):
        if not np.array_equal(
            case_inputs[feature].to_numpy(), [row[feature] for row in historical_rows]
        ):
            raise ValueError("As entradas visíveis devem ser as fichas históricas.")
    if not np.array_equal(case_target, [row["y_obito"] for row in historical_rows]):
        raise ValueError("Não altere os desfechos das fichas históricas.")
    threshold = float(historical_preview["threshold"])
    if not 0 < threshold < 1:
        raise ValueError("O limiar deve estar entre zero e um.")
    original_inputs = full_inputs.copy(deep=True)
    original_target = full_target.copy()
    # Sorteio sobre TODO o teste, sem consultar desfechos ou perdas.
    rng = np.random.default_rng(protocol["permutation_seed"])
    orders = [rng.permutation(len(full_inputs)) for _ in range(protocol["repeats"])]
    orders_hash = hashlib.sha256(np.asarray(orders).tobytes()).hexdigest()
    if orders_hash != protocol["permutation_orders_sha256"]:
        raise ValueError("As ordens precisam reproduzir o experimento registrado.")
    order = orders[0]
    original_probability = _probability(fitted_model, full_inputs)
    case_original_probability = original_probability[receiver_positions]
    check_reference_probabilities(
        case_original_probability, [row["p_original"] for row in historical_rows]
    )
    reference_metric_interval(
        full_target, original_probability, experiment["original"]["logloss"]
    )
    rows = [
        {
            key: row[key]
            for key in (
                "record",
                "idade_anos",
                "saturacao",
                "y_obito",
                "p_original",
                "class_original",
                "correct_original",
            )
        }
        for row in historical_rows
    ]
    for i, row in enumerate(rows):
        # The generated window is coherent with this run's measured probability;
        # the historical JSON is untouched and checked separately above.
        row["p_original"] = float(case_original_probability[i])
        if row["class_original"] != int(case_original_probability[i] >= threshold):
            raise AssertionError(
                "Numeric reconstruction changed an original displayed class."
            )
        row["loss_original"] = float(
            individual_logloss(case_target, case_original_probability)[i]
        )
    rounds = []
    for feature, cell, label in (
        ("idade_anos", "age", "Age"),
        ("saturacao", "oxygen", "Low oxygen"),
    ):
        changed = E.permutar_colunas(full_inputs, feature, order)
        pd.testing.assert_frame_equal(
            changed.drop(columns=feature), full_inputs.drop(columns=feature)
        )
        assert changed.dtypes.equals(full_inputs.dtypes)
        full_probability = _probability(fitted_model, changed)
        full_loss = individual_logloss(full_target, full_probability)
        full_single_loss = float(full_loss.mean())
        np.testing.assert_allclose(
            full_single_loss,
            log_loss(full_target, full_probability),
            rtol=0,
            atol=1e-15,
        )
        registered = next(
            row for row in experiment["rows"] if row["feature"] == feature
        )
        reference_metric_interval(
            full_target, full_probability, registered["metrics"]["logloss"]["after"][0]
        )
        probability = full_probability[receiver_positions]
        predicted = (probability >= threshold).astype(int)
        correct = predicted == case_target
        loss = individual_logloss(case_target, probability)
        for i, row in enumerate(rows):
            row["p_after_" + cell] = float(probability[i])
            row["class_after_" + cell] = int(predicted[i])
            row["correct_after_" + cell] = bool(correct[i])
            row["loss_after_" + cell] = float(loss[i])
        full_test = next(row for row in full_rows if row["feature"] == feature)
        rounds.append(
            {
                "feature": feature,
                "label": label,
                "cell": cell,
                "values": case_inputs[feature].tolist(),
                "shuffled_values": changed.iloc[receiver_positions][feature].tolist(),
                "probability": probability.tolist(),
                "predicted": predicted.tolist(),
                "correct": correct.tolist(),
                "individual_loss": loss.tolist(),
                "sample_loss_mean": float(loss.mean()),
                "full_test_single_loss": full_single_loss,
                "full_test": copy.deepcopy(full_test),
            }
        )
    pd.testing.assert_frame_equal(full_inputs, original_inputs)
    np.testing.assert_array_equal(full_target, original_target)
    return {
        "preview": {
            "metric": "logloss",
            "rows": rows,
            "rounds": rounds,
            "permutation_seed": int(protocol["permutation_seed"]),
            "displayed_repeat": 1,
            "evaluation_n": len(full_inputs),
            "permutation_scope": "full temporal test",
            "permutation_orders_sha256": orders_hash,
            "threshold": threshold,
            "age_unit": historical_preview["age_unit"],
            "selection": {
                "records_per_outcome": historical_preview["selection"][
                    "records_per_outcome"
                ],
                "rule": (
                    "Same first four adult temporal-test receiver records per outcome, then "
                    "original dataset order. The displayed receivers are selected by outcome; "
                    "neither predictions nor shuffle losses select them. Donor values come "
                    "from the full-test permutation, not a shuffle restricted to these rows."
                ),
            },
            "scope": (
                "Eight unchanged real SRAG receivers are a window into repeat 1 of the "
                "registered full temporal-test permutation. Donor values are drawn from "
                "all evaluation rows; no donor identifier, position, or outcome is exported. "
                "Age and low oxygen are permuted separately, restoring original inputs "
                "before each. Global errors and PFI use all test rows; these selected "
                "receivers do not estimate population performance."
            ),
        }
    }
