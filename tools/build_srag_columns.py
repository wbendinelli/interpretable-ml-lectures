"""Generate COLUMNS.md — the coverage contract, one row per published column.

Usage:
    python tools/build_srag_columns.py            # write modules/00-dataset/COLUMNS.md
    python tools/build_srag_columns.py --check    # render in memory, diff, exit 1 on drift

Reads ONLY committed artifacts — the contract tables in tools/srag_silver.py
and modules/00-dataset/PROFILE.json — never a parquet, so it runs in CI
without the dataset and produces the same bytes everywhere.

The point of the generator is the assertion, not the table: every one of
the 194 columns must belong to exactly one family, carry a rule (a closed
domain, a date parse, a checkbox reading, free text kept raw, or an
identifier policy), and have a class. A column left over fails the build.
The claim "194/194 have a rule" is generated here, not written by hand.

The YEAR_GATED list in srag_silver.py is re-derived from PROFILE.json
(fill == 0.0 exactly, unrounded, in at least one year) and the build fails
if the static list has drifted — same self-falsifying shape as the gates.
"""

from __future__ import annotations

import json
import pathlib
import sys

import srag_silver as S

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROFILE = ROOT / "modules/00-dataset/PROFILE.json"
OUT = ROOT / "modules/00-dataset/COLUMNS.md"

DATE_COLUMNS = frozenset(
    c for c in S.ALL_COLUMNS if c.startswith("DT_") or c in S.DMY_DATES
)


def rule_of(col: str) -> str:
    """The treatment rule, from the contract tables — never free-typed."""
    if col in DATE_COLUMNS:
        fmt = "dd/mm/yyyy" if col in S.DMY_DATES else "ISO"
        return f"date {fmt} → `{col}_d`"
    if col in S.CHECKBOXES:
        return "checkbox {1, blank} → `_marcado`"
    if col in S.COMORBIDITIES:
        return "in {1,2,9}, gated → `_estado`"
    if col in S.FAB_COLUMNS:
        return "vocabulary harmonised → `_codigo`, `_fabricante`; raw kept"
    if col == "OBES_IMC":
        return "decimal kept raw (declared Varchar2(3), measured free text)"
    if col in S.FREE_TEXT:
        return "free text, kept raw"
    if col in S.IDENTIFIER_COLS:
        return "identifier, kept raw, never a feature"
    if col in S.DOMAINS:
        dom = ",".join(S.DOMAINS[col])
        return f"in {{{dom}}} [{S.DOMAIN_SOURCE[col]}]"
    if col in S.CODE_PAIRS:
        return f"name side of `{S.CODE_PAIRS[col]}`, kept raw"
    if col in S.CODE_PAIRS.values():
        if col.startswith("CO_MU") or col == "CO_MUN_RES":
            return "6-digit IBGE code, referential-checked"
        return "code side of its pair, kept raw"
    if col in {"SEM_NOT", "SEM_PRI"}:
        return "epi week, derived from its date and verified (MMWR, 100.00%)"
    if col in {"NU_IDADE_N", "COD_IDADE"}:
        return "unit-aware age, verified against `TP_IDADE` identity"
    return ""


def missing_of(col: str) -> str:
    if col in S.GATES:
        parent, values, tier, worst = S.GATES[col]
        return f"gated by `{parent}` ∈ {{{','.join(values)}}} (tier {tier}, {worst}%)"
    if col in S.CHECKBOXES:
        return "blank = not marked"
    if col in S.SINTOMAS:
        return "ungated `_estado` (no candidate passes the G-rule)"
    if col in S.YEAR_GATED:
        return "blank encodes the year (form revision)"
    return "blank = absent; 9 = ignorado" if col in S.DOMAINS else "—"


def derived_of(col: str) -> str:
    out = []
    if col in DATE_COLUMNS:
        out.append(f"`{col}_d`")
    if col in S.CHECKBOXES:
        out.append(f"`{col}_marcado`")
    if col in S.GATES or col in S.COMORBIDITIES:
        out.append(f"`{col}_estado`")
    if col in S.SINTOMAS:
        out.append(f"`{col}_estado`")
    if col in S.FAB_COLUMNS:
        out.append(f"`{col.lower()}_codigo`, `{col.lower()}_fabricante`")
    extra = {
        "FATOR_RISC": "`fator_risco_declarado`",
        "SG_UF": "`regiao`, `uf_resid_coerente`",
        "DT_SIN_PRI": "`se_primeiro_sinto`, `ano_epi_primeiro_sinto`, `idade_anos`",
        "DT_NOTIFIC": "`se_notificacao`, `ano_epi_notificacao`",
        "DT_NASC": "`idade_anos`, `idade_cat_ms`",
        "TP_IDADE": "`idade_unidade`, `idade_declarada_anos`",
        "NU_IDADE_N": "`idade_declarada_anos`, `cod_idade_consistente`",
        "COD_IDADE": "`cod_idade_consistente`",
        "VACINA_COV": "`vacina_covid_declarada`",
        "DOSE_1_COV": "`n_doses_covid_registradas`, `dose_1_covid_antes_campanha`",
        "CO_MUN_NOT": "`municipio_notif_valido`, `municipio_notif_df_ra`",
        "CO_MUN_RES": "`municipio_resid_valido`, `municipio_resid_df_ra`",
        "CO_MU_INTE": "`municipio_inte_valido`, `municipio_inte_df_ra`",
        "DT_ENTUTI": "`dias_uti`",
        "DT_INTERNA": "`dias_ate_internacao`",
        "EVOLUCAO": "every `_obito` variant (18 + 18 `_unico`)",
        "CLASSI_FIN": "`covid_caso`, `out_agentes`, `srag_n_especificada`, `investigacao`",
        "PCR_FLUASU": "the influenza A subtype `_caso` flags",
        "PCR_FLUBLI": "the influenza B lineage `_caso` flags",
        "TP_FLU_PCR": "`influenza_a_n_sub_caso`, `influenza_b_inconclusivo_caso`",
        "TP_FLU_AN": "`influenza_a_n_sub_caso`, `influenza_b_inconclusivo_caso`",
    }
    if col in extra:
        out.append(extra[col])
    if col in S.CHECKBOXES:
        out.append("agent `_caso` flags")
    if col in S.SINTOMAS:
        out.append("`n_sintomas_*`")
    return "; ".join(out) if out else "—"


def year_gated_from_profile(
    profile: dict,
) -> tuple[frozenset[str], dict[str, list[str]]]:
    empty_years: dict[str, list[str]] = {}
    for year, cols in profile.items():
        for c, info in cols.items():
            if info["fill"] == 0.0:
                empty_years.setdefault(c, []).append(year)
    return frozenset(empty_years), empty_years


def fill_range(profile: dict, col: str) -> str:
    fills = [profile[y][col]["fill"] for y in sorted(profile) if col in profile[y]]
    return f"{min(fills):.0f}–{max(fills):.0f}%"


def render() -> str:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    cols_in_profile = sorted({c for y in profile.values() for c in y})

    # --- the contract's assertions, before a single row is rendered --------
    fam_cols = [c for _, cs in S.FAMILIES for c in cs]
    problems = []
    if len(cols_in_profile) != 194:
        problems.append(f"PROFILE.json carries {len(cols_in_profile)} columns, not 194")
    if sorted(fam_cols) != cols_in_profile:
        extra = set(fam_cols) - set(cols_in_profile)
        missing = set(cols_in_profile) - set(fam_cols)
        problems.append(
            f"FAMILIES is not a partition: extra={sorted(extra)} missing={sorted(missing)}"
        )
    unruled = [c for c in cols_in_profile if not rule_of(c)]
    if unruled:
        problems.append(f"columns with no rule: {unruled}")
    gated_parents = {parent for parent, _, _, _ in S.GATES.values()}
    if not gated_parents <= set(cols_in_profile):
        problems.append(
            f"gate parents outside the schema: {sorted(gated_parents - set(cols_in_profile))}"
        )
    derived_year_gated, empty_years = year_gated_from_profile(profile)
    if derived_year_gated != S.YEAR_GATED:
        problems.append(
            "YEAR_GATED drifted from PROFILE.json: "
            f"missing={sorted(derived_year_gated - S.YEAR_GATED)} "
            f"stale={sorted(S.YEAR_GATED - derived_year_gated)}"
        )
    if problems:
        for p in problems:
            print(f"contract violation: {p}", file=sys.stderr)
        raise SystemExit(2)

    L = [
        "# The column contract",
        "",
        "Generated by `tools/build_srag_columns.py` from the tables in",
        "`tools/srag_silver.py` and the measured `PROFILE.json`. Do not edit by",
        "hand — the generator asserts, at build time, that the 13 families",
        "partition the 194 published columns, that every column carries a rule,",
        "and that the `year_gated` list still matches the measured fill. A",
        "column this table cannot place fails the build.",
        "",
        f"**{len(cols_in_profile)}/194 columns covered.** "
        f"Classes: "
        + ", ".join(
            f"{f} {sum(1 for c in cols_in_profile if S.class_of(c) == f)}"
            for f in S.CLASS_PRECEDENCE
        )
        + ".",
        "",
    ]

    for family, cols in S.FAMILIES:
        L.append(f"## {family}")
        L.append("")
        L.append(
            "| Field | Rule | Missing semantics | Class | Fill 2019–2024 | Derived |"
        )
        L.append("|---|---|---|---|---|---|")
        for c in cols:
            L.append(
                f"| `{c}` | {rule_of(c)} | {missing_of(c)} | {S.class_of(c)} "
                f"| {fill_range(profile, c)} | {derived_of(c)} |"
            )
        L.append("")

    L.append("## The gate ladder")
    L.append("")
    L.append("Adopted under the G-rule — contradiction ≤ 0.05% of the child's filled")
    L.append("cells in **every** year (tier A = 0.00% flat, and ≥1,000 filled rows in")
    L.append("some year). `build()` re-measures each entry on every year it processes")
    L.append("and refuses to run when a recorded bound is broken.")
    L.append("")
    L.append("| Child | Parent ∈ | Tier | Worst-year contradiction |")
    L.append("|---|---|---|---|")
    for child, (parent, values, tier, worst) in S.GATES.items():
        L.append(
            f"| `{child}` | `{parent}` ∈ {{{','.join(values)}}} | {tier} | {worst}% |"
        )
    L.append("")
    L.append("### Rejected, with the number that rejected them")
    L.append("")
    L.append("| Child | Documented predicate | Worst contradiction | Why it matters |")
    L.append("|---|---|---|---|")
    for child, (parent, value, worst, note) in S.GATES_REJECTED.items():
        L.append(f"| `{child}` | `{parent}` = {value} | {worst}% | {note} |")
    L.append("")

    L.append("## The derived columns")
    L.append("")
    L.append("Every column Silver adds, with its definition label (Portuguese, like")
    L.append("the raw labels in DICTIONARY.md), provenance (the Ministry's script")
    L.append("line where it defines the variable, or this module) and class.")
    L.append("`write_year()` asserts that the built Silver's extra columns are")
    L.append("exactly this catalogue — a derived column without a label fails the")
    L.append("build, the same way a raw column without a rule does.")
    L.append("")
    catalogue = S.derived_catalogue()
    L.append(f"**{len(catalogue)} derived columns.**")
    L.append("")
    L.append("| Column | Definition | Provenance | Class |")
    L.append("|---|---|---|---|")
    for nome in sorted(catalogue):
        definicao, fonte, classe = catalogue[nome]
        L.append(f"| `{nome}` | {definicao} | {fonte} | {classe} |")
    L.append("")

    L.append("## Year-gated columns")
    L.append("")
    L.append("100% empty in at least one year — the blank encodes the year, not the")
    L.append("patient. Derived mechanically from `PROFILE.json`.")
    L.append("")
    L.append("| Field | Empty years | First year with data |")
    L.append("|---|---|---|")
    for c in sorted(S.YEAR_GATED):
        anos = empty_years[c]
        com_dado = sorted(set(profile) - set(anos))
        L.append(
            f"| `{c}` | {', '.join(sorted(anos))} | {com_dado[0] if com_dado else '—'} |"
        )
    L.append("")

    return "\n".join(L).rstrip("\n") + "\n"


def main(argv: list[str]) -> int:
    text = render()
    if "--check" in argv:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            for i, (a, b) in enumerate(zip(current.splitlines(), text.splitlines())):
                if a != b:
                    print(f"COLUMNS.md drifted at line {i + 1}:", file=sys.stderr)
                    print(f"  committed: {a[:100]}", file=sys.stderr)
                    print(f"  generated: {b[:100]}", file=sys.stderr)
                    break
            else:
                print("COLUMNS.md drifted in length", file=sys.stderr)
            return 1
        print("COLUMNS.md is current")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"{OUT}: {sum(len(cs) for _, cs in S.FAMILIES)} columns")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    raise SystemExit(main(sys.argv[1:]))
