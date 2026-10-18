"""Render the module-10 log-loss figures from recorded, audited measurements.

No model is fitted here. Files are generated only into a caller-selected
working directory; promotion into the versioned lesson is a separate action.
The historical module-00 Brier figures and their generator remain unchanged.
"""

from __future__ import annotations

import contextlib
import io
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import sapians as SP
from matplotlib.lines import Line2D


def render_slide_figures(payload, destination: Path):
    """Keep the approved Inter slide assets independent of notebook styling.

    The research figures follow the caller's Global profile. The interactive
    lecture retains its explicit editorial profile, including SVG element IDs
    used by its motion and keyboard controls.
    """
    editorial_defaults = {
        key: value
        for key, value in matplotlib.rcParamsDefault.items()
        if key != "backend"
    }
    with plt.rc_context(rc=editorial_defaults):
        plt.style.use(str(SP.ESTILO))
        _render_slide_figures(payload, destination)


def _render_slide_figures(payload, destination: Path):
    """Produce the seven stable SVGs consumed by the interactive slide motion."""
    if payload["protocol"]["primary_metric"] != "logloss":
        raise ValueError("The slide figures must depict the selected log loss")
    destination.mkdir(parents=True, exist_ok=True)
    rows = payload["rows"]
    with plt.rc_context({"svg.fonttype": "none", "svg.hashsalt": "pfi-logloss"}):
        for mode, neutral, xmax, xlabel in [
            ("difference", 0, 0.11, "Extra log loss (0 = no change)"),
            ("ratio", 1, 1.45, "Log-loss ratio (1 = no change)"),
        ]:
            fig, ax = plt.subplots(figsize=(8.6, 4.3))
            means = np.asarray([r[mode + "_mean"] for r in rows])
            sds = np.asarray([r[mode + "_sd"] for r in rows])
            positions = np.arange(len(rows))
            colors = ["#212322"] + ["#a2aeaf"] * (len(rows) - 1)
            ax.barh(positions, means, left=0, height=0.54, color=colors)
            for k, (mean, sd) in enumerate(zip(means, sds, strict=True)):
                ax.errorbar(
                    mean,
                    k,
                    xerr=sd,
                    fmt="none",
                    ecolor="#212322",
                    capsize=3,
                    elinewidth=1.1,
                )
                value_label = f"+{mean:.4f}" if mode == "difference" else f"{mean:.3f}×"
                ax.text(
                    mean + sd + xmax * 0.015,
                    k,
                    value_label,
                    va="center",
                    ha="left",
                    fontsize=10,
                    color="#212322",
                    gid=f"pfi-value-{k}",
                )
            ax.set_yticks(positions, [r["label"] for r in rows], fontsize=12)
            ax.invert_yaxis()
            ax.set_xlim(0, xmax)
            ax.set_xlabel(xlabel, fontsize=11, labelpad=12)
            ax.axvline(neutral, color="#707878", lw=1, ls="--")
            ax.spines[["top", "right", "left"]].set_visible(False)
            ax.spines["bottom"].set_color("#cbd0cf")
            ax.tick_params(axis="y", length=0, pad=10)
            ax.tick_params(axis="x", labelsize=10, color="#cbd0cf")
            ax.xaxis.grid(True, color="#eceded", lw=0.7)
            ax.set_axisbelow(True)
            fig.subplots_adjust(left=0.29, right=0.98, top=0.98, bottom=0.15)
            _save(fig, destination, "pfi-slide-" + mode)

        trace = payload["walkthrough"]
        delta = np.asarray(trace["difference"])
        offsets = np.random.default_rng(42).uniform(-0.14, 0.14, len(delta))
        fig, ax = plt.subplots(figsize=(7.2, 3.2))
        for k, (value, offset) in enumerate(zip(delta, offsets, strict=True)):
            ax.plot(
                value,
                offset,
                "o",
                color="#a2aeaf",
                markersize=5,
                gid=f"repeat-point-{k}",
            )
        mean, sd = delta.mean(), delta.std(ddof=1)
        ax.axvspan(mean - sd, mean + sd, color="#e5eae8", zorder=0, gid="repeat-sd")
        ax.axvline(mean, color="#212322", lw=1.5, gid="repeat-mean")
        ax.set_xlabel("Increase in log loss for Age", fontsize=12)
        ax.set_yticks([])
        ax.set_ylim(-0.3, 0.3)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color("#cbd0cf")
        ax.tick_params(axis="x", labelsize=11)
        ax.text(
            0.02,
            0.94,
            "Each dot is one full-test column shuffle",
            transform=ax.transAxes,
            fontsize=12,
            va="top",
        )
        ax.text(
            0.02,
            0.04,
            "Line: mean     Band: ±1 sample SD",
            transform=ax.transAxes,
            fontsize=11,
            va="bottom",
        )
        fig.tight_layout()
        _save(fig, destination, "pfi-age-repeats")

        methods = payload["dependence"]["results"]
        fig, ax = plt.subplots(figsize=(8.8, 3.6))
        for k, result in enumerate(methods):
            mean, sd = result["difference_mean"] * 1000, result["difference_sd"] * 1000
            ax.barh(
                k,
                mean,
                height=0.45,
                color="#212322" if result["key"] == "within" else "#a2aeaf",
                gid=f"dep-bar-{k}",
            )
            whisker = ax.errorbar(
                mean,
                k,
                xerr=sd,
                fmt="none",
                ecolor="#212322",
                capsize=4,
                elinewidth=1.2,
            )
            for line in whisker[1]:
                line.set_gid(f"dep-cap-{k}-{line.get_marker()}")
            whisker[2][0].set_gid(f"dep-whisker-{k}")
            ax.text(
                mean + sd + 0.035,
                k,
                f"{mean:+.3f}",
                va="center",
                fontsize=11,
                gid=f"dep-value-{k}",
            )
        ax.set_yticks(range(len(methods)), [r["label"] for r in methods], fontsize=11)
        ax.invert_yaxis()
        xmax = max((r["difference_mean"] + r["difference_sd"]) * 1000 for r in methods)
        ax.set_xlim(
            min(
                0,
                min(
                    (r["difference_mean"] - r["difference_sd"]) * 1000 for r in methods
                ),
            )
            - 0.025,
            xmax * 1.3 + 0.06,
        )
        ax.axvline(0, color="#707878", lw=1)
        ax.set_xlabel(
            "Extra log loss × 1,000  (mean ± one sample SD)", fontsize=11, labelpad=10
        )
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color("#cbd0cf")
        ax.tick_params(axis="y", length=0, pad=10)
        ax.tick_params(axis="x", labelsize=10)
        ax.xaxis.grid(True, color="#eceded", lw=0.7)
        ax.set_axisbelow(True)
        fig.subplots_adjust(left=0.36, right=0.97, top=0.96, bottom=0.22)
        _save(fig, destination, "pfi-dependence")

    with plt.rc_context(
        {
            "mathtext.fontset": "cm",
            "svg.fonttype": "path",
            "svg.hashsalt": "pfi-logloss",
        }
    ):
        for name, equation in payload["equations"].items():
            fig = plt.figure(figsize=(8 if name == "logloss" else 5, 0.8))
            fig.text(
                0.02,
                0.5,
                equation,
                va="center",
                ha="left",
                fontsize=24,
                color="#212322",
            )
            fig.savefig(
                destination / f"equation-{name}.svg",
                transparent=True,
                bbox_inches="tight",
                pad_inches=0.05,
                metadata={"Date": None},
            )
            _normalize_svg(destination / f"equation-{name}.svg")
            plt.close(fig)


def _normalize_svg(path: Path):
    """Keep SVG text compatible with the repository whitespace convention."""
    text = path.read_text(encoding="utf-8")
    path.write_text(
        "\n".join(line.rstrip() for line in text.splitlines()) + "\n", encoding="utf-8"
    )


def _save(fig, destination, name):
    fig.savefig(destination / f"{name}.svg", facecolor="white", metadata={"Date": None})
    _normalize_svg(destination / f"{name}.svg")
    fig.savefig(
        destination / f"{name}.png",
        dpi=180,
        facecolor="white",
        metadata={"Software": "SAPIANS"},
    )
    plt.close(fig)


def render_research_figures(record, destination: Path):
    """Rebuild the primary before/after, close-up and rank plots using log loss."""
    rows = sorted(record["rows"], key=lambda r: r["metrics"]["logloss"]["rank"])[:10]
    baseline = record["original"]["logloss"]
    positions = np.arange(len(rows))
    labels = [r["label"] for r in rows]
    means = np.asarray([r["metrics"]["logloss"]["mean"] for r in rows])
    deviations = np.asarray([r["metrics"]["logloss"]["sd"] for r in rows])
    values = [r["metrics"]["logloss"]["delta"] for r in rows]
    rng = np.random.default_rng(42)
    destination.mkdir(parents=True, exist_ok=True)

    def boxes(ax, selected, yy, select_means, select_sd):
        ax.boxplot(
            selected,
            positions=yy,
            orientation="horizontal",
            widths=0.42,
            patch_artist=True,
            showfliers=False,
            manage_ticks=False,
            boxprops={"facecolor": SP.CINZA_CLARO, "alpha": 0.4},
            medianprops={"color": SP.ESCURO, "linewidth": 1},
            whiskerprops={"color": SP.CINZA, "linewidth": 0.8},
            capprops={"color": SP.CINZA, "linewidth": 0.8},
        )
        for vv, pos in zip(selected, yy, strict=True):
            ax.scatter(
                vv,
                pos + rng.uniform(-0.13, 0.13, len(vv)),
                color=SP.CINZA,
                s=7,
                alpha=0.3,
                zorder=3,
            )
        ax.errorbar(
            select_means,
            yy,
            xerr=select_sd,
            fmt="o",
            color=SP.ESCURO,
            markersize=4,
            capsize=3,
            linewidth=1.2,
            zorder=4,
        )
        ax.axvline(0, **SP.L_REF)

    def save(fig, name):
        previous = SP.FIGDIR
        SP.FIGDIR = destination
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                SP.salvar(
                    fig,
                    name,
                    rect=(
                        0.01,
                        0.18 if name == "antes-depois-top10" else 0.03,
                        0.99,
                        0.84,
                    ),
                )
            print("Figura regenerada:", name + ".png")
        finally:
            SP.FIGDIR = previous

    fig, (left, right) = plt.subplots(1, 2, figsize=SP.PAINEL, sharey=True)
    for pos, mean in zip(positions, means, strict=True):
        left.plot([baseline, baseline + mean], [pos, pos], color=SP.CINZA_CLARO)
    left.scatter(
        np.full(len(rows), baseline), positions, color=SP.CINZA, marker="s", s=20
    )
    left.errorbar(
        baseline + means,
        positions,
        xerr=deviations,
        fmt="o",
        color=SP.ESCURO,
        capsize=3,
        markersize=4,
    )
    left.axvline(baseline, **SP.L_REF)
    left.set_yticks(positions, labels)
    left.invert_yaxis()
    left.set_title("Antes e depois da permutação")
    left.set_xlabel("Log loss do conjunto · menor é melhor\nEixo ampliado")
    left.set_xlim(baseline - 0.002, baseline + max(means + 2 * deviations) * 1.08)
    boxes(right, values, positions, means, deviations)
    right.set_title("PFI: distribuição do aumento do erro")
    right.set_xlabel(
        "Log loss após − log loss original\nMaior: maior dependência do modelo"
    )
    legend = [
        Line2D(
            [],
            [],
            marker="s",
            linestyle="none",
            color=SP.CINZA,
            label="Erro original fixo",
        ),
        Line2D([], [], marker="o", color=SP.ESCURO, label="Média ± 1 desvio padrão"),
        Line2D(
            [], [], color=SP.CINZA, label="Caixa: mediana e quartis; bigodes: 1,5 IQR"
        ),
    ]
    fig.legend(handles=legend, loc="lower left", bbox_to_anchor=(0.16, 0.01), ncol=1)
    SP.titulo(
        fig,
        "Permutar uma entrada mostra quanto o erro aumenta",
        "§4 · PFI · TESTE HISTÓRICO 2024 · EXPLORATÓRIO",
    )
    fig.text(
        0.19,
        0.875,
        f"{SP.pt_int(record['protocol']['repeats'])} sorteios por coluna · mesmos registros e modelo · pontos cinza: sorteios individuais",
    )
    fig.subplots_adjust(left=0.19, right=0.985, top=0.82, bottom=0.23, wspace=0.12)
    save(fig, "antes-depois-top10")

    fig2, ax = plt.subplots(figsize=SP.PAINEL)
    boxes(ax, values[1:], positions[1:], means[1:], deviations[1:])
    ax.set_yticks(positions[1:], labels[1:])
    ax.invert_yaxis()
    ax.set_xlabel("PFI em aumento da log loss · mesma escala para todas as linhas")
    SP.titulo(
        fig2,
        "Ampliação das posições abaixo da primeira",
        "§4 · PFI · POSIÇÕES 2–10 · SEM A VARIÁVEL DE MAIOR PFI",
    )
    fig2.text(
        0.19,
        0.875,
        "A primeira posição foi omitida apenas nesta ampliação. Ponto preto e haste: média ± 1 DP.",
    )
    fig2.subplots_adjust(left=0.25, right=0.975, top=0.82, bottom=0.12)
    save(fig2, "pfi-detalhe")

    fig3, ax = plt.subplots(figsize=SP.PAINEL)
    for pos, row in zip(positions, rows, strict=True):
        ranks = np.asarray(row["metrics"]["logloss"]["rank_repeats"])
        ax.scatter(
            ranks,
            pos + rng.uniform(-0.18, 0.18, len(ranks)),
            color=SP.CINZA,
            s=12,
            alpha=0.3,
        )
        ax.scatter(np.median(ranks), pos, color=SP.ESCURO, marker="D", s=28)
    ax.set_yticks(positions, labels)
    ax.invert_yaxis()
    ax.set_xlabel(
        "Posição entre todas as entradas em cada sorteio · menor é mais importante"
    )
    low = min(min(r["metrics"]["logloss"]["rank_repeats"]) for r in rows)
    high = max(max(r["metrics"]["logloss"]["rank_repeats"]) for r in rows)
    ax.set_xlim(low - 0.6, high + 0.6)
    ax.set_xticks(range(int(low), int(np.ceil(high)) + 1))
    SP.titulo(
        fig3,
        "O ranking também varia entre permutações",
        "§4 · PFI · MODELO E PACIENTES FIXOS",
    )
    fig3.text(
        0.25,
        0.875,
        "Cada ponto é um sorteio; losango: posição mediana. As linhas seguem o ranking da PFI média.",
    )
    fig3.subplots_adjust(left=0.25, right=0.975, top=0.82, bottom=0.12)
    save(fig3, "ranking-sorteios")
    return [fig, fig2, fig3]
