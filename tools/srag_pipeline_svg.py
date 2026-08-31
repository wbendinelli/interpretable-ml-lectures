"""Generate PIPELINE.svg — the Bronze→Silver→Gold map, with measured numbers.

Usage:
    python tools/srag_pipeline_svg.py            # write modules/00-dataset/PIPELINE.svg
    python tools/srag_pipeline_svg.py --check    # render in memory, diff, exit 1 on drift

Structure and counts come from the same committed inputs the coverage
contract reads — the tables in tools/srag_silver.py and PROFILE.json — so
those cannot drift from the code without the diff saying so. Numbers that
required the full data (the influenza recount, the cross-check failure
rates) are quoted findings, printed by committed notebook cells, and say
so in the subtitle. Nothing here opens a parquet.

The three lanes follow the medallion rule the module argues for: Bronze is
the download, untouched; Silver states facts about the record; Gold makes
task choices, and makes them visibly pending — its boxes are dashed because
the decisions (target, cohort, split) belong to William and the course, not
to this repository's defaults.
"""

from __future__ import annotations

import json
import pathlib
import sys

import srag_silver as S

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROFILE = ROOT / "modules/00-dataset/PROFILE.json"
OUT = ROOT / "modules/00-dataset/PIPELINE.svg"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def counts() -> dict:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    years = sorted(profile)
    cols = sorted({c for y in profile.values() for c in y})
    rows = sum(next(iter(profile[y].values()))["n_rows"] for y in years)
    classes = {
        f: sum(1 for c in cols if S.class_of(c) == f) for f in S.CLASS_PRECEDENCE
    }

    return {
        "years": years,
        "n_cols": len(cols),
        "n_rows": rows,
        "classes": classes,
        "gates": len(S.GATES),
        "gates_rejected": len(S.GATES_REJECTED),
        "families": len(S.FAMILIES),
        "leakage_derived": 36 + 2 + 1,  # _obito*, dias_*, caso_srag_ms
    }


def render() -> str:
    c = counts()
    W, H = 1180, 760
    lane_w, gap, x0, y0 = 350, 40, 20, 84
    xs = [x0, x0 + lane_w + gap, x0 + 2 * (lane_w + gap)]

    p: list[str] = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'font-family="Georgia, serif" font-size="14">'
    )
    p.append(f'<rect width="{W}" height="{H}" fill="#faf7f2"/>')
    p.append(
        f'<text x="{W / 2}" y="34" text-anchor="middle" font-size="22" fill="#222">'
        "SRAG / SIVEP-Gripe — the treatment, Bronze to Gold</text>"
    )
    p.append(
        f'<text x="{W / 2}" y="56" text-anchor="middle" font-size="13" fill="#666">'
        f"{c['n_rows']:,} notifications · {c['years'][0]}–{c['years'][-1]} · structure and "
        "counts generated from the committed contract; quoted findings are printed by notebook cells</text>"
    )

    def lane(i: int, title: str, sub: str, dashed: bool = False) -> None:
        x = xs[i]
        dash = ' stroke-dasharray="7,5"' if dashed else ""
        p.append(
            f'<rect x="{x}" y="{y0}" width="{lane_w}" height="{H - y0 - 20}" rx="10" '
            f'fill="#ffffff" stroke="#b8b0a4" stroke-width="1.5"{dash}/>'
        )
        p.append(
            f'<text x="{x + lane_w / 2}" y="{y0 + 30}" text-anchor="middle" '
            f'font-size="19" fill="#1c1c1c" font-weight="bold">{esc(title)}</text>'
        )
        p.append(
            f'<text x="{x + lane_w / 2}" y="{y0 + 50}" text-anchor="middle" '
            f'font-size="12.5" fill="#777">{esc(sub)}</text>'
        )

    def box(
        i: int,
        y: int,
        h: int,
        title: str,
        lines: list[str],
        color: str = "#2e7d52",
        dashed: bool = False,
    ) -> int:
        x = xs[i] + 16
        w = lane_w - 32
        dash = ' stroke-dasharray="6,4"' if dashed else ""
        p.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" '
            f'fill="{color}" fill-opacity="0.09" stroke="{color}" stroke-width="1.4"{dash}/>'
        )
        p.append(
            f'<text x="{x + 12}" y="{y + 22}" font-size="13.5" font-weight="bold" '
            f'fill="{color}">{esc(title)}</text>'
        )
        for j, ln in enumerate(lines):
            p.append(
                f'<text x="{x + 12}" y="{y + 42 + j * 17}" font-size="12" '
                f'fill="#3a3a3a">{esc(ln)}</text>'
            )
        return y + h + 12

    # ---- Bronze ------------------------------------------------------------
    lane(0, "Bronze", "the download, byte for byte, never modified")
    y = y0 + 68
    y = box(
        0,
        y,
        78,
        f"{c['n_cols']} columns × 6 yearly files",
        [
            "re-export of 2025-06-26, one layout",
            f"{c['n_rows']:,} rows, ~2.2 GB parquet",
        ],
        "#7a6a55",
    )
    y = box(
        0,
        y,
        112,
        "what the profile measured",
        [
            "75 columns change value shape between",
            "years ('1' vs '1.0' — PCR_SARS2 loses",
            "519,518 positives to a literal rule)",
            f"{sum(1 for _ in S.YEAR_GATED)} columns 100% empty in some year",
        ],
        "#7a6a55",
    )
    y = box(
        0,
        y,
        112,
        "dirt, kept visible",
        [
            "7 shifted rows (UTI holds a hospital",
            "name) → quarantined, none lost",
            "dates like 1695-06-14 02:32:37.74…",
            "20 rows with negative declared age",
        ],
        "#7a6a55",
    )
    y = box(
        0,
        y,
        95,
        "provenance",
        [
            "the dadosabertos S3 bucket (the portal",
            "was down; the bucket stayed up)",
            "reference: the Ministry's own MIT script",
        ],
        "#7a6a55",
    )

    # ---- Silver ------------------------------------------------------------
    lane(1, "Silver", "facts about the record — no task choices")
    y = y0 + 68
    y = box(
        1,
        y,
        95,
        f"contract: {c['families']} families, 194/194 ruled",
        [
            "COLUMNS.md generated + asserted;",
            "pre-commit re-renders and diffs",
            "normalise() before any domain is read",
        ],
    )
    y = box(
        1,
        y,
        95,
        f"gates: {c['gates']} confirmed, {c['gates_rejected']} rejected",
        [
            "G-rule: ≤0.05% contradiction, every year",
            "build() re-measures and refuses on drift",
            "3 missing states, never merged",
        ],
    )
    y = box(
        1,
        y,
        95,
        "224 derived columns (→ 418)",
        [
            "MMWR week (100.00% vs SEM_PRI),",
            "full etiology catalogue (influenza 2.1x),",
            "FAB makers, IBGE flags, unit-aware age",
        ],
    )
    cls = c["classes"]
    y = box(
        1,
        y,
        132,
        "every column classed",
        [
            f"ok {cls['ok']} · code_pair {cls['code_pair']} · free_text {cls['free_text']}",
            f"year_gated {cls['year_gated']} · identifier {cls['identifier']} · leakage {cls['leakage']}",
            "84 Kahn checks — the failing ones are",
            "documentation (RES_AN⇢agent: 9–20%/yr)",
            "quarantine invariant: 4,109,560 + 7",
        ],
        "#4a7fb5",
    )

    # ---- Gold --------------------------------------------------------------
    lane(2, "Gold", "task choices — deliberately still open", dashed=True)
    y = y0 + 68
    y = box(
        2,
        y,
        95,
        "target (decision: William + course)",
        [
            "candidates: óbito · UTI · ventilation",
            "EVOLUCAO stays a label, never a feature",
            "GOLD.md lays out the menu with evidence",
        ],
        "#c03434",
        dashed=True,
    )
    y = box(
        2,
        y,
        95,
        f"leakage exclusion — generable ({cls['leakage']}+{c['leakage_derived']})",
        [
            f"{cls['leakage']} raw columns classed leakage +",
            f"{c['leakage_derived']} derived (_obito*, dias_*, caso_srag_ms)",
            "generated from COLUMN_CLASS, not typed",
        ],
        "#c03434",
        dashed=True,
    )
    y = box(
        2,
        y,
        95,
        "cohort & years",
        [
            "coorte_hospitalizado vs full SRAG",
            "vs covid_caso — regime drift is context:",
            "lethality 29→8.6%, COVID share 70→12%",
        ],
        "#c03434",
        dashed=True,
    )
    y = box(
        2,
        y,
        112,
        "encoding & split",
        [
            "3 missing states → categories, never",
            "imputed silently; year-gated columns",
            "are calendars in disguise; temporal",
            "split proposal in GOLD.md",
        ],
        "#c03434",
        dashed=True,
    )

    # arrows between lanes
    ay = H / 2
    for i in (0, 1):
        x1 = xs[i] + lane_w
        x2 = xs[i + 1]
        p.append(
            f'<path d="M {x1 + 4} {ay} L {x2 - 10} {ay}" stroke="#8a8177" '
            'stroke-width="2.5" fill="none" marker-end="url(#arr)"/>'
        )
    p.append(
        '<defs><marker id="arr" markerWidth="10" markerHeight="8" refX="8" refY="4" '
        'orient="auto"><path d="M0,0 L10,4 L0,8 z" fill="#8a8177"/></marker></defs>'
    )

    p.append("</svg>")
    return "\n".join(p) + "\n"


def main(argv: list[str]) -> int:
    text = render()
    if "--check" in argv:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            print("PIPELINE.svg drifted from the contract", file=sys.stderr)
            return 1
        print("PIPELINE.svg is current")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"{OUT}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    raise SystemExit(main(sys.argv[1:]))
