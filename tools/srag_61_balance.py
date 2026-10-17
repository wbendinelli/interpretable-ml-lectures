"""Controlled temporal class-balancing study; never changes the course model.

The sampler instrument only records ancestry. Calendar reconstruction and
rejection define a restricted SMOTENC strategy, explicitly distinct from the
unmodified algorithm. All probabilities evaluated here are uncalibrated.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.metadata
import json
from pathlib import Path

import numpy as np
import pandas as pd
import srag_30_silver as S
import srag_60_model as M
from imblearn.over_sampling import SMOTENC
from imblearn.under_sampling import RandomUnderSampler
from scipy.optimize import brentq, minimize
from scipy.special import expit, logit
from sklearn import config_context
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits
from xgboost import XGBClassifier


class TracedSMOTENC(SMOTENC):
    """Preserve the library RNG/output; record minority-relative anchor rows."""

    def _generate_samples(self, X, nn_data, nn_num, rows, cols, steps, y_type, y=None):
        self.anchor_rows_ = rows.copy()
        self.anchor_class_ = y_type
        return super()._generate_samples(
            X, nn_data, nn_num, rows, cols, steps, y_type, y
        )


def verify_tracing() -> None:
    """A behavioral check: recording ancestry cannot alter synthetic values."""
    x = pd.DataFrame(
        {"a": np.arange(24, dtype=float), "b": pd.Categorical(["a", "b"] * 12)}
    )
    y = np.array([0] * 16 + [1] * 8)
    params = {"categorical_features": ["b"], "random_state": 42, "k_neighbors": 3}
    plain_x, plain_y = SMOTENC(**params).fit_resample(x, y)
    traced = TracedSMOTENC(**params)
    trace_x, trace_y = traced.fit_resample(x, y)
    pd.testing.assert_frame_equal(plain_x, trace_x)
    np.testing.assert_array_equal(plain_y, trace_y)
    assert len(traced.anchor_rows_) == 8


def calibration_diagnostics(y: np.ndarray, p: np.ndarray) -> dict:
    """Diagnostic regressions on evaluation labels, never applied to predictions."""
    clipped = np.clip(p, 1e-7, 1 - 1e-7)
    z = logit(clipped)
    offset = brentq(lambda a: float(expit(z + a).mean() - y.mean()), -40, 40)
    center, scale = float(z.mean()), float(z.std())
    u = (z - center) / scale

    def objective(theta):
        eta = theta[0] + theta[1] * u
        residual = expit(eta) - y
        loss = np.mean(np.logaddexp(0, eta) - y * eta)
        gradient = np.array([residual.mean(), np.mean(residual * u)])
        return loss, gradient

    fit = minimize(objective, np.array([0.0, 1.0]), jac=True, method="BFGS")
    if not fit.success and np.max(np.abs(fit.jac)) > 1e-5:
        raise RuntimeError("calibration diagnostic did not converge")
    slope = float(fit.x[1] / scale)
    intercept = float(fit.x[0] - slope * center)
    return {
        "cal_intercept": float(offset),
        "cal_intercept_joint": intercept,
        "cal_slope": slope,
        "clipped_probabilities": int(np.sum(p != clipped)),
    }


def metrics(y: np.ndarray, probabilities: np.ndarray) -> dict:
    p = probabilities.astype(np.float64)
    predicted = p >= 0.5
    positive = y == 1
    tp, fp = int(np.sum(predicted & positive)), int(np.sum(predicted & ~positive))
    tn, fn = int(np.sum(~predicted & ~positive)), int(np.sum(~predicted & positive))
    return {
        "auc": float(roc_auc_score(y, p)),
        "ap": float(average_precision_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "logloss": float(log_loss(y, p)),
        "mean_pred": float(p.mean()),
        "observed": float(y.mean()),
        "gap": float(p.mean() - y.mean()),
        "sensitivity": tp / (tp + fn),
        "specificity": tn / (tn + fp),
        "ppv": tp / (tp + fp) if tp + fp else None,
        "alert_rate": float(predicted.mean()),
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        **calibration_diagnostics(y, p),
    }


def curves(y: np.ndarray, p: np.ndarray) -> dict:
    edges = np.linspace(0, 1, 11)
    index = np.minimum(np.searchsorted(edges, p, side="right") - 1, 9)
    bins = []
    for j in range(10):
        mask = index == j
        n = int(mask.sum())
        events = int(y[mask].sum())
        rate = events / n if n else None
        if n:
            z = 1.959963984540054
            denominator = 1 + z * z / n
            center = (rate + z * z / (2 * n)) / denominator
            half = (
                z * np.sqrt(rate * (1 - rate) / n + z * z / (4 * n * n)) / denominator
            )
        bins.append(
            {
                "left": float(edges[j]),
                "right": float(edges[j + 1]),
                "n": n,
                "events": events,
                "mean_pred": float(p[mask].mean()) if n else None,
                "event_rate": rate,
                "lo": float(center - half) if n else None,
                "hi": float(center + half) if n else None,
            }
        )
    fpr, tpr, _ = roc_curve(y, p)
    precision, recall, _ = precision_recall_curve(y, p)

    def thin(a, b):
        keep = np.unique(np.linspace(0, len(a) - 1, min(220, len(a))).astype(int))
        return np.column_stack([a[keep], b[keep]]).tolist()

    return {
        "bins": bins,
        "roc": thin(fpr, tpr),
        "pr": thin(recall[::-1], precision[::-1]),
    }


def counts(y, real_n=None, weight=1.0) -> dict:
    n, pos = len(y), int(np.sum(y))
    return {
        "n": n,
        "positivos": pos,
        "negativos": n - pos,
        "prev": pos / n,
        "real_n": n if real_n is None else real_n,
        "synthetic_n": 0 if real_n is None else n - real_n,
        "effective_positive_weight": weight,
    }


def fingerprint(frame: pd.DataFrame) -> str:
    values = pd.util.hash_pandas_object(frame, index=True).to_numpy()
    return hashlib.sha256(values.tobytes()).hexdigest()


def restricted_smotenc(train: pd.DataFrame, seed: int):
    """Generate proposals, reconstruct calendar, reject only synthetic rows."""
    original_x = M.design_matrix(train)[0]
    y = train["y_obito"].to_numpy()
    needed = int(np.sum(y == 0) - np.sum(y == 1))
    origin = pd.Timestamp("2020-03-01")
    days = np.rint(train["meses_desde_mar2020"].to_numpy(dtype=float) * 30.44)
    numeric = pd.DataFrame({"idade_anos": train["idade_anos"], "onset_day": days})
    scaler = StandardScaler().fit(numeric)
    sample = pd.DataFrame(scaler.transform(numeric), columns=numeric.columns)
    categorical = list(M.CATEGORICAS + M.BOOLEANAS) + ["n_doses_antes_do_sintoma"]
    for c in categorical:
        sample[c] = pd.Categorical(train[c].astype(str))
    sampler = TracedSMOTENC(
        categorical_features=categorical,
        sampling_strategy={1: int(np.sum(y == 1)) + 2 * needed},
        random_state=seed,
        k_neighbors=5,
    )
    before = fingerprint(train)
    with config_context(working_memory=256), threadpool_limits(limits=4):
        resampled, resampled_y = sampler.fit_resample(sample, y)
    pd.testing.assert_frame_equal(
        resampled.iloc[: len(sample)].reset_index(drop=True), sample
    )
    assert sampler.anchor_class_ == 1
    proposals = resampled.iloc[len(sample) :].reset_index(drop=True)
    assert np.all(resampled_y[len(sample) :] == 1)
    numeric_new = scaler.inverse_transform(
        proposals[list(numeric.columns)].astype(float)
    )
    day_new = np.rint(numeric_new[:, 1]).astype(int)
    dates = pd.Series(origin + pd.to_timedelta(day_new, unit="D"))
    synthetic = pd.DataFrame(index=proposals.index)
    synthetic["idade_anos"] = numeric_new[:, 0].astype("float32")
    synthetic["meses_desde_mar2020"] = (day_new / 30.44).astype("float32")
    synthetic["semana_epi"] = S.epiweek(dates).astype("int8")
    synthetic["n_doses_antes_do_sintoma"] = (
        proposals["n_doses_antes_do_sintoma"].astype(str).astype("int8")
    )
    for c in M.CATEGORICAS:
        synthetic[c] = pd.Categorical(
            proposals[c].astype(str), categories=train[c].cat.categories
        )
    for c in M.BOOLEANAS:
        synthetic[c] = proposals[c].astype(str).eq("True")
    minority_rows = np.flatnonzero(y == 1)
    anchors = minority_rows[sampler.anchor_rows_]
    synthetic["fator_risc_portao"] = train["fator_risc_portao"].iloc[anchors].to_numpy()
    reasons = M.gate_reasons(synthetic)
    reasons["dominio_idade"] = ~(synthetic["idade_anos"].between(0, 120))
    reasons["dominio_categorias"] = synthetic[list(M.CATEGORICAS)].isna().any(axis=1)
    reasons["dominio_dose"] = ~synthetic["n_doses_antes_do_sintoma"].isin(
        train["n_doses_antes_do_sintoma"].unique()
    )
    valid = ~reasons.any(axis=1)
    accepted = np.flatnonzero(valid.to_numpy())
    used = accepted[:needed]
    clean = synthetic.iloc[used][list(M.FEATURES)].copy()
    x = pd.concat([original_x, clean], ignore_index=True)
    new_y = np.concatenate([y, np.ones(len(clean), dtype=y.dtype)])
    pd.testing.assert_frame_equal(
        x.iloc[: len(train)].reset_index(drop=True), original_x
    )
    assert before == fingerprint(train)
    assert not M.gate_reasons(synthetic.iloc[used]).any(axis=1).any()
    overlap = (
        reasons.astype(int).astype(str).agg("".join, axis=1).value_counts().to_dict()
    )
    by_year = (
        pd.DataFrame({"ano": dates.dt.year, "rejeitada": ~valid})
        .groupby("ano")["rejeitada"]
        .agg(["size", "sum", "mean"])
    )
    by_portao = (
        pd.DataFrame(
            {"portao_ancora": synthetic["fator_risc_portao"], "rejeitada": ~valid}
        )
        .groupby("portao_ancora")["rejeitada"]
        .agg(["size", "sum", "mean"])
    )
    audit = {
        "n_proposto": len(proposals),
        "n_rejeitado": int((~valid).sum()),
        "n_aceito": int(valid.sum()),
        "n_usado": len(clean),
        "quota_desejada": needed,
        "quota_atingida": len(clean) == needed,
        "rejeicoes_por_regra": {c: int(reasons[c].sum()) for c in reasons},
        "ordem_regras_intersecoes": reasons.columns.tolist(),
        "intersecoes": overlap,
        "rejeicoes_por_ano": json.loads(by_year.to_json(orient="index")),
        "rejeicoes_por_portao_ancora": json.loads(by_portao.to_json(orient="index")),
        "anomalias_originais": {
            c: int(M.gate_reasons(train)[c].sum()) for c in M.GATE_REASONS
        },
        "originais_preservados": True,
        "metadado_portao": "herdado da ancora; apenas auditoria",
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "sampler_features": sample.columns.tolist(),
    }
    return x, new_y, audit


def bootstrap_deltas(y, reference, candidate, repeats=500, seed=42):
    rng = np.random.default_rng(seed)
    names = ["brier", "logloss", "auc", "ap", "gap"]
    values = {name: [] for name in names}
    a, b = reference.astype(float), candidate.astype(float)
    for _ in range(repeats):
        ix = rng.integers(0, len(y), len(y))
        yy, aa, bb = y[ix], a[ix], b[ix]
        values["brier"].append(np.mean((bb - yy) ** 2 - (aa - yy) ** 2))
        # Match log_loss's float64 bounds; other metrics keep raw probabilities.
        eps = np.finfo(float).eps
        a_log, b_log = np.clip(aa, eps, 1 - eps), np.clip(bb, eps, 1 - eps)
        values["logloss"].append(
            np.mean(
                -yy * np.log(b_log)
                - (1 - yy) * np.log1p(-b_log)
                + yy * np.log(a_log)
                + (1 - yy) * np.log1p(-a_log)
            )
        )
        values["gap"].append(float((bb - aa).mean()))
        if len(np.unique(yy)) == 2:
            values["auc"].append(roc_auc_score(yy, bb) - roc_auc_score(yy, aa))
            values["ap"].append(
                average_precision_score(yy, bb) - average_precision_score(yy, aa)
            )
    return {name: np.quantile(values[name], [0.025, 0.975]).tolist() for name in names}


def run_study(output: Path, seeds=(42, 43, 44), bootstrap_repeats=500) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    verify_tracing()
    gold = M.load_gold()
    train = gold[gold["split"] == "train"].reset_index(drop=True)
    evaluations = {
        s: gold[gold["split"] == s].reset_index(drop=True) for s in ["val", "test"]
    }
    x_train, _, y_train = M.design_matrix(train)
    designs = {s: M.design_matrix(g)[0] for s, g in evaluations.items()}
    labels = {s: g["y_obito"].to_numpy() for s, g in evaluations.items()}
    weight = float(np.sum(y_train == 0) / np.sum(y_train == 1))
    result = {
        "protocol": {
            "xgb_params": M.XGB_PARAMS,
            "sampler_seeds": list(seeds),
            "model_seed": 42,
            "sampling_ratio": "1:1",
            "probabilities": "raw; no recalibrator fitted",
            "primary": "Brier/log-loss, calibration; AUC/AP secondary",
            "test_status": "2024 exploratory; already observed",
            "bootstrap_repeats": bootstrap_repeats,
            "bootstrap_seed": 42,
            "threshold_diagnostic": 0.5,
            "smotenc": "calendar reconstruction and synthetic-only rejection; anchor gate audit",
            "versions": {
                p: importlib.metadata.version(p)
                for p in [
                    "numpy",
                    "pandas",
                    "scikit-learn",
                    "xgboost",
                    "imbalanced-learn",
                    "sklearn-compat",
                ]
            },
        },
        "dataset": {
            "train_original": counts(y_train),
            **{s: counts(y) for s, y in labels.items()},
            "sample_sha256": hashlib.sha256(M.AMOSTRA.read_bytes()).hexdigest(),
            "features": list(M.FEATURES),
            "notebook_html": "caderno.html",
        },
        "runs": [],
        "comparisons": [],
    }
    (output / "protocolo.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False)
    )
    probabilities = {}

    def status(message):
        print(message, flush=True)
        (output / "status.json").write_text(
            json.dumps({"etapa": message}, ensure_ascii=False)
        )

    jobs = [("atual", 42), ("pesos", 42)] + [
        (m, s) for m in ["reducao", "smotenc_restrito"] for s in seeds
    ]
    for method, seed in jobs:
        status(f"Preparando {method}, semente {seed}")
        audit = {}
        params = dict(M.XGB_PARAMS)
        if method == "pesos":
            x, y = x_train, y_train
            params["scale_pos_weight"] = weight
        elif method == "reducao":
            rus = RandomUnderSampler(sampling_strategy=1.0, random_state=seed)
            x, y = rus.fit_resample(x_train, y_train)
            kept = train.iloc[rus.sample_indices_]
            audit["retidos_por_ano"] = {
                str(k): int(v) for k, v in kept["ano_onset"].value_counts().items()
            }
            audit["hash_ids_retidos"] = hashlib.sha256(
                kept["gold_id"].to_numpy().tobytes()
            ).hexdigest()
        elif method == "smotenc_restrito":
            x, y, audit = restricted_smotenc(train, seed)
        else:
            x, y = x_train, y_train
        status(f"Treinando {method}, semente {seed}: {len(y)} registros")
        model = XGBClassifier(**params).fit(x, y)
        record = {
            "method": method,
            "seed": seed,
            "train": counts(
                y,
                real_n=len(train) if method == "smotenc_restrito" else None,
                weight=weight if method == "pesos" else 1.0,
            ),
            "audit": audit,
            "curves": {},
        }
        for split in ["val", "test"]:
            p = model.predict_proba(designs[split])[:, 1]
            probabilities[f"{method}_{seed}_{split}"] = p
            record[split] = metrics(labels[split], p)
            record["curves"][split] = curves(labels[split], p)
        if method == "atual":
            expected = json.loads(M.METRICS_JSON.read_text())["xgb"]
            for row in expected:
                for k in ["auc", "brier"]:
                    assert abs(record[row["split"]][k] - row[k]) < 5e-5
        result["runs"].append(record)
        (output / "resultados-parciais.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False)
        )
        np.savez_compressed(
            output / "previsoes.npz",
            **probabilities,
            **{f"y_{s}": v for s, v in labels.items()},
        )
        status(
            f"Concluído {method}, semente {seed}; Brier val={record['val']['brier']:.6f}"
        )
        del model
        if method in ["reducao", "smotenc_restrito"]:
            del x, y
        gc.collect()
    baseline = result["runs"][0]
    for run in result["runs"][1:]:
        method, seed = run["method"], run["seed"]
        status(f"Intervalos pareados: {method}, semente {seed}")
        for split in ["val", "test"]:
            intervals = bootstrap_deltas(
                labels[split],
                probabilities[f"atual_42_{split}"],
                probabilities[f"{method}_{seed}_{split}"],
                repeats=bootstrap_repeats,
            )
            for name, (low, high) in intervals.items():
                result["comparisons"].append(
                    {
                        "method": method,
                        "seed": seed,
                        "split": split,
                        "metric": name,
                        "delta": run[split][name] - baseline[split][name],
                        "ci_low": low,
                        "ci_high": high,
                    }
                )
    (output / "resultados.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    )
    status("Estudo concluído; gráficos e caderno podem ser gerados")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run_study(args.output)
