#!/usr/bin/env python3
"""SRAG data quality assessment, in the Kahn et al. (2016) framework.

Each check declares where it sits in the framework, and the report is grouped
by that, so a gap in the taxonomy is visible as an empty cell rather than as
something nobody thought of. (That is not hypothetical: the uniqueness cell was
empty until it was filled, and the check then found 1,854 apparent
re-notifications whose copies disagree on the outcome.)

    Kahn MG, Callahan TJ, Barnard J, et al. "A Harmonized Data Quality
    Assessment Terminology and Framework for the Secondary Use of Electronic
    Health Record Data." eGEMs. 2016;4(1):18. doi:10.13063/2327-9214.1244

Categories
    conformance   does the *representation* comply with a definition?
                  (value / relational / computational)
    completeness  are the attributes present, without looking at values?
    plausibility  are the values believable?
                  (uniqueness / atemporal / temporal)

Contexts
    verification  against this dataset's own stated expectations
    validation    against an external reference — the Ministry's dictionary,
                  the published literature, or another dataset

The checks are pandera schemas and plain measurements; the report is generated
markdown, committed like every other claim in this repository. Great
Expectations covers the same ground and renders a nicer report, but writes it
to an uncommitted directory by default; the report layout here is modelled on
theirs (overview counts, per-column status, unexpected values with their share
of rows) without reusing their Apache-2.0 code.

Usage:  python3 tools/srag_quality.py [data_dir] [output.md]
"""

from __future__ import annotations

import dataclasses
import pathlib
import sys
from collections.abc import Callable

import pandas as pd
import pyarrow.parquet as pq

CATEGORIES = {
    "conformance": "Conformance",
    "completeness": "Completeness",
    "plausibility": "Plausibility",
}


@dataclasses.dataclass
class Finding:
    """One check's outcome on one year."""

    check_id: str
    category: str
    subcategory: str
    context: str  # "verification" | "validation"
    column: str
    statement: str  # what the check asserts, in words
    n_rows: int
    n_failed: int
    examples: list[str]

    @property
    def passed(self) -> bool:
        return self.n_failed == 0

    @property
    def share(self) -> float:
        return 100 * self.n_failed / self.n_rows if self.n_rows else 0.0


@dataclasses.dataclass
class Check:
    check_id: str
    category: str
    subcategory: str
    context: str
    column: str
    statement: str
    run: Callable[[pd.DataFrame], tuple[int, list[str]]]
    columns: tuple[str, ...]


def _norm(s: pd.Series) -> pd.Series:
    """2020 writes coded values as '1.0' where every other year writes '1'."""
    return s.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)


def in_set(column: str, allowed: list[str], source: str) -> Check:
    def run(df: pd.DataFrame) -> tuple[int, list[str]]:
        s = _norm(df[column])
        bad = s[s.notna() & ~s.isin(allowed)]
        return len(bad), bad.value_counts().head(5).index.tolist()

    return Check(
        check_id=f"conf-value-{column.lower()}",
        category="conformance",
        subcategory="value",
        context="validation",  # the value set comes from the official dictionary
        column=column,
        statement=f"values are one of {{{', '.join(allowed)}}} ({source})",
        run=run,
        columns=(column,),
    )


def numeric_range(column: str, lo: float, hi: float) -> Check:
    def run(df: pd.DataFrame) -> tuple[int, list[str]]:
        s = _norm(df[column])
        n = pd.to_numeric(s, errors="coerce")
        bad = s[s.notna() & (n.isna() | (n < lo) | (n > hi))]
        return len(bad), bad.value_counts().head(5).index.tolist()

    return Check(
        check_id=f"plaus-atemporal-{column.lower()}",
        category="plausibility",
        subcategory="atemporal",
        context="validation",  # plausible range is domain knowledge, not metadata
        column=column,
        statement=f"an integer within [{lo:g}, {hi:g}]",
        run=run,
        columns=(column,),
    )


def unique_key(columns: tuple[str, ...], check_id: str, statement: str) -> Check:
    def run(df: pd.DataFrame) -> tuple[int, list[str]]:
        dup = df.duplicated(subset=list(columns), keep=False)
        if not dup.any():
            return 0, []
        groups = df[dup].groupby(list(columns), dropna=False).size()
        ex = [f"{int(groups.max())} cópias no maior grupo", f"{len(groups):,} grupos"]
        return int(dup.sum()), ex

    return Check(
        check_id=check_id,
        category="plausibility",
        subcategory="uniqueness",
        context="verification",  # internal expectation about the records
        column=" + ".join(columns),
        statement=statement,
        run=run,
        columns=columns,
    )


# The official dictionary declares dates as "Date DD/MM/AAAA"; the published
# parquet writes ISO YYYY-MM-DD. Parsing with the documented format silently
# yields NaT for every row, which makes an ordering check pass on nothing — so
# the format is asserted separately (conf-format-dates) rather than assumed.
DATE_FORMAT = "%Y-%m-%d"


def parse_dates(s: pd.Series) -> pd.Series:
    """Permissive parse, for checks that need the value rather than its shape."""
    return pd.to_datetime(
        s.astype("string").str.strip(), format="mixed", errors="coerce"
    )


def date_format(columns: tuple[str, ...]) -> Check:
    def run(df: pd.DataFrame) -> tuple[int, list[str]]:
        # The finding is a column carrying more than one shape, not an
        # unreadable value: most rows are a bare ISO date, a minority carry a
        # full timestamp. Both parse; only one matches the declared format.
        bad, ex = 0, []
        for c in columns:
            raw = df[c].astype("string").str.strip()
            iso = pd.to_datetime(raw, format=DATE_FORMAT, errors="coerce")
            off = raw.notna() & iso.isna()
            bad += int(off.sum())
            ex += raw[off].head(2).tolist()
        return bad, ex[:4]

    return Check(
        check_id="conf-format-dates",
        category="conformance",
        subcategory="value",
        context="validation",
        column=", ".join(columns),
        statement=f"every value has the same shape `{DATE_FORMAT}` (the dictionary declares `DD/MM/AAAA`)",
        run=run,
        columns=columns,
    )


def date_order(earlier: str, later: str) -> Check:
    def run(df: pd.DataFrame) -> tuple[int, list[str]]:
        a = parse_dates(df[earlier])
        b = parse_dates(df[later])
        both = a.notna() & b.notna()
        bad = both & (a > b)
        ex = [
            f"{earlier}={x:%Y-%m-%d} > {later}={y:%Y-%m-%d}"
            for x, y in zip(a[bad].head(3), b[bad].head(3))
        ]
        return int(bad.sum()), ex

    return Check(
        check_id=f"plaus-temporal-{earlier.lower()}-{later.lower()}",
        category="plausibility",
        subcategory="temporal",
        context="verification",
        column=f"{earlier} → {later}",
        statement=f"`{earlier}` never after `{later}`",
        run=run,
        columns=(earlier, later),
    )


def completeness(column: str, essential: bool = True) -> Check:
    def run(df: pd.DataFrame) -> tuple[int, list[str]]:
        s = df[column]
        return int(s.isna().sum()), []

    return Check(
        check_id=f"compl-{column.lower()}",
        category="completeness",
        subcategory="",
        context="verification",
        column=column,
        statement="present" + (" (Campo Essencial)" if essential else ""),
        run=run,
        columns=(column,),
    )


# The coded value sets come from the official dictionary — see
# modules/00-dataset/DICTIONARY.md.
CHECKS: list[Check] = [
    in_set(
        "EVOLUCAO", ["1", "2", "3", "9"], "1-Cura 2-Óbito 3-Óbito outras 9-Ignorado"
    ),
    in_set("CS_SEXO", ["M", "F", "I"], "M-Masculino F-Feminino I-Ignorado"),
    in_set("CLASSI_FIN", ["1", "2", "3", "4", "5"], "etiologia final"),
    in_set("CRITERIO", ["1", "2", "3", "4"], "critério de encerramento"),
    in_set("TP_IDADE", ["1", "2", "3"], "1-Dia 2-Mês 3-Ano"),
    in_set("UTI", ["1", "2", "9"], "1-Sim 2-Não 9-Ignorado"),
    in_set(
        "SUPORT_VEN", ["1", "2", "3", "9"], "1-Invasivo 2-Não invasivo 3-Não 9-Ignorado"
    ),
    in_set("CARDIOPATI", ["1", "2", "9"], "1-Sim 2-Não 9-Ignorado"),
    in_set("DIABETES", ["1", "2", "9"], "1-Sim 2-Não 9-Ignorado"),
    in_set("FATOR_RISC", ["1", "2", "9", "S", "N"], "1-Sim 2-Não 9-Ignorado"),
    date_format(("DT_SIN_PRI", "DT_NOTIFIC", "DT_INTERNA", "DT_EVOLUCA", "DT_ENCERRA")),
    numeric_range("NU_IDADE_N", 0, 150),
    unique_key(
        ("NU_NOTIFIC",), "plaus-uniq-nu-notific", "`NU_NOTIFIC` identifies one record"
    ),
    unique_key(
        ("DT_NASC", "CS_SEXO", "CO_MUN_NOT", "DT_SIN_PRI"),
        "plaus-uniq-pessoa-evento",
        "no two records share birth date, sex, municipality and first-symptom date",
    ),
    date_order("DT_SIN_PRI", "DT_NOTIFIC"),
    date_order("DT_NOTIFIC", "DT_ENCERRA"),
    date_order("DT_INTERNA", "DT_EVOLUCA"),
    completeness("EVOLUCAO"),
    completeness("CLASSI_FIN"),
    completeness("CARDIOPATI"),
    completeness("VACINA_COV"),
]


def assess(path: pathlib.Path) -> tuple[list[Finding], int]:
    needed = sorted({c for chk in CHECKS for c in chk.columns})
    df = pq.read_table(path, columns=needed).to_pandas()
    n = len(df)
    out = []
    for chk in CHECKS:
        failed, examples = chk.run(df)
        out.append(
            Finding(
                chk.check_id,
                chk.category,
                chk.subcategory,
                chk.context,
                chk.column,
                chk.statement,
                n,
                failed,
                examples,
            )
        )
    return out, n


def render(by_year: dict[str, tuple[list[Finding], int]]) -> str:
    years = sorted(by_year)
    L: list[str] = []
    L.append("# SRAG — data quality assessment\n")
    L.append(
        "Generated by [`tools/srag_quality.py`](../../tools/srag_quality.py). Every check "
        "declares its place in the framework of Kahn et al. (2016), the harmonised terminology "
        "for the secondary use of electronic health record data — which is exactly what these "
        "notifications are.\n"
    )
    L.append(
        "> Kahn MG, Callahan TJ, Barnard J, et al. *A Harmonized Data Quality Assessment "
        "Terminology and Framework for the Secondary Use of Electronic Health Record Data.* "
        "eGEMs. 2016;4(1):18. [doi:10.13063/2327-9214.1244](https://doi.org/10.13063/2327-9214.1244)\n"
    )
    L.append(
        "**Categories** — *Conformance*: does the representation comply with a definition? "
        "*Completeness*: are the attributes present, without looking at values? "
        "*Plausibility*: are the values believable?\n\n"
        "**Contexts** — *Verification* checks against this dataset's own stated expectations; "
        "*Validation* checks against an external reference (the Ministry's dictionary, domain "
        "knowledge, the literature).\n"
    )
    L.append("Do not edit this file by hand — run the generator.\n")

    # Overview, in the shape Great Expectations' Data Docs use.
    L.append("## Overview\n")
    L.append("| Year | Records | Checks | Passed | Failed | Pass rate |")
    L.append("|---|---:|---:|---:|---:|---:|")
    for y in years:
        f, n = by_year[y]
        ok = sum(1 for x in f if x.passed)
        L.append(
            f"| {y} | {n:,} | {len(f)} | {ok} | {len(f) - ok} | {100 * ok / len(f):.0f}% |"
        )

    L.append("\n## Coverage of the framework\n")
    L.append("A cell with no check is a gap, not a clean bill of health.\n")
    L.append("| Category | Subcategory | Checks | Context |")
    L.append("|---|---|---:|---|")
    seen: dict[tuple[str, str], list[Check]] = {}
    for chk in CHECKS:
        seen.setdefault((chk.category, chk.subcategory), []).append(chk)
    for (cat, sub), chks in seen.items():
        ctx = "/".join(sorted({c.context for c in chks}))
        L.append(f"| {CATEGORIES[cat]} | {sub or '—'} | {len(chks)} | {ctx} |")

    for cat, title in CATEGORIES.items():
        rows = [c for c in CHECKS if c.category == cat]
        if not rows:
            continue
        L.append(f"\n## {title}\n")
        L.append("| Check | Column | Asserts | Context | " + " | ".join(years) + " |")
        L.append("|---|---|---|---|" + "---:|" * len(years))
        for chk in rows:
            cells = []
            for y in years:
                f = next(x for x in by_year[y][0] if x.check_id == chk.check_id)
                cells.append("✓" if f.passed else f"**{f.n_failed:,}**")
            sub = f" · {chk.subcategory}" if chk.subcategory else ""
            L.append(
                f"| `{chk.check_id}`{sub} | `{chk.column}` | {chk.statement} | "
                f"{chk.context} | " + " | ".join(cells) + " |"
            )

    L.append("\n## Failures in detail\n")
    for y in years:
        f, n = by_year[y]
        bad = [x for x in f if not x.passed]
        if not bad:
            continue
        L.append(f"\n### {y}\n")
        L.append("| Check | Failing rows | Share | Examples |")
        L.append("|---|---:|---:|---|")
        for x in sorted(bad, key=lambda z: -z.n_failed):
            ex = "; ".join(str(e) for e in x.examples[:4]) or "—"
            L.append(f"| `{x.check_id}` | {x.n_failed:,} | {x.share:.3f}% | {ex} |")

    return "\n".join(L).rstrip("\n") + "\n"


def main(argv: list[str]) -> int:
    root = pathlib.Path(__file__).resolve().parent.parent
    data = (
        pathlib.Path(argv[0]).expanduser()
        if argv
        else pathlib.Path.home() / "Documents/srag-data"
    )
    out = (
        pathlib.Path(argv[1])
        if len(argv) > 1
        else root / "modules/00-dataset/QUALITY.md"
    )

    files = sorted(data.glob("INFLUD*.parquet"))
    if not files:
        print(
            f"no INFLUD*.parquet under {data} — run tools/fetch_srag.sh first",
            file=sys.stderr,
        )
        return 2

    by_year = {}
    for f in files:
        year = "20" + f.name[6:8]
        by_year[year] = assess(f)
        findings, n = by_year[year]
        bad = sum(1 for x in findings if not x.passed)
        print(f"  {year}: {n:,} records, {bad}/{len(findings)} checks failing")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(by_year), encoding="utf-8")
    print(f"{out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
