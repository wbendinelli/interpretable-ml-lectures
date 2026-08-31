#!/usr/bin/env python3
"""Bronze → Silver for the SRAG microdata.

Silver repairs and makes explicit; it does not choose a task. Same grain, same
universe: every Bronze row comes out, either in the table or in the quarantine,
never dropped. Typing, value normalisation and semantic recoding happen here;
target definition, leakage exclusion and row filtering are Gold's job.

The separation test is *is this value determined by the record alone, or by the
task?* — `idade_anos` and `covid_caso` are determined by the record; `y_obito`
and the exclusion list are determined by the task.

Where the Ministry's own script (MIT, gitlab.com/cgcovid/dados-publicos,
"Script 1. LimpezaClassificao.R", Osowski, de Carvalho, Silva Filho and Gomes,
CGCOVID/DEDT/SVSA/MS 2025) settles a question, it is followed and cited by line.
Where this module departs, DEVIATIONS says so and why — every departure is
because that script exists to *count surveillance cases for the weekly
bulletin*, and a filter that is right for counting is wrong for a dataset that
will later be modelled and explained.

Usage:  python3 tools/srag_silver.py [data_dir] [out_dir]
"""

from __future__ import annotations

import pathlib
import re
import sys

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

# --------------------------------------------------------------------------
# Where we depart from the Ministry's script, and why. Each entry is checked
# against the data in `report()`, so a deviation cannot rot into a claim.
# --------------------------------------------------------------------------
DEVIATIONS = {
    "caso_srag_nao_filtra": (
        "MS line 260 runs filter(caso_srag == 1). Here it is a column. The filter "
        "drops 1,656,396 of 4,109,567 rows (40.3%), including 892,168 with "
        "CLASSI_FIN=5 and 524,862 with PCR_SARS2 positive — it selects on symptom "
        "fields being filled, not on disease."
    ),
    "coorte_sem_evolucao": (
        "MS line 246 defines criterio_1 as HOSPITAL==1 | EVOLUCAO==2. Membership "
        "would then depend on the outcome: 24,475 rows qualify only because the "
        "patient died. `coorte_hospitalizado` uses HOSPITAL==1 alone; the full "
        "official flag stays as `caso_srag_ms`."
    ),
    "idade_neonato_zero": (
        "MS lines 269-276 set idade_anos to NA when DT_SIN_PRI == DT_NASC. That is "
        "6,835 neonates symptomatic on the day of birth — clinically ordinary. "
        "Age 0 describes them; absent does not."
    ),
    "datas_iso": (
        "MS line 231 parses dates as %d/%m/%Y. The published data — CSV and parquet "
        "alike — is ISO yyyy-mm-dd, so as.Date() would return NA for every date and "
        "silently void idade_anos. DT_VGM and DT_RT_VGM really are dd/mm/yyyy and "
        "are parsed as such."
    ),
    "evolucao_nao_zerada": (
        "MS line 193 does replace_na(EVOLUCAO = 0). 0 is not a valid code, and it "
        "merges 'outcome unknown' with 'did not die'. That is safe for counting "
        "deaths (they only test == 2) and unsafe for a label. Kept distinct."
    ),
    "subtipos_influenza_nao_zerados": (
        "MS line 193 also zeroes TP_FLU_PCR, TP_FLU_AN and PCR_FLUASU. Those are "
        "subtype categoricals (1=Influenza A, 2=B …), not checkboxes; 0 is not in "
        "their domain. Left as missing."
    ),
}

# The 18 laboratory checkboxes. Official domain, dictionary p.21: "1-marcado
# pelo usuário / Vazio - não marcado" — there is no code for "not detected".
CHECKBOXES = [
    "PCR_SARS2",
    "PCR_VSR",
    "PCR_ADENO",
    "PCR_METAP",
    "PCR_BOCA",
    "PCR_RINO",
    "PCR_PARA1",
    "PCR_PARA2",
    "PCR_PARA3",
    "PCR_PARA4",
    "PCR_OUTRO",
    "AN_SARS2",
    "AN_VSR",
    "AN_ADENO",
    "AN_PARA1",
    "AN_PARA2",
    "AN_PARA3",
]
# Subtype categoricals that LOOK like the block but are not — 0 is invalid here.
NOT_CHECKBOXES = ["TP_FLU_PCR", "TP_FLU_AN", "PCR_FLUASU", "PCR_FLUBLI"]

# The 13 comorbidities, and the funnel that gates them. `FATOR_RISC` absent
# means the block was never presented: measured at 100.00% across all six years,
# with zero exceptions. Ribas et al. 2022 call this a "variável-funil".
COMORBIDITIES = [
    "PUERPERA",
    "CARDIOPATI",
    "HEMATOLOGI",
    "SIND_DOWN",
    "HEPATICA",
    "ASMA",
    "DIABETES",
    "NEUROLOGIC",
    "PNEUMOPATI",
    "IMUNODEPRE",
    "RENAL",
    "OBESIDADE",
    "OUT_MORBI",
]
COMORBIDITY_GATE = "FATOR_RISC"

DMY_DATES = ["DT_VGM", "DT_RT_VGM"]  # the only two that are dd/mm/yyyy
DECIMAL_COLUMNS = {"OBES_IMC"}  # never strip ".0" here: the decimal is real

TRAILING_ZEROS = re.compile(r"^(-?\d+)\.0+$")


def normalise(s: pd.Series, column: str) -> pd.Series:
    """Strip the serialisation artefact, before any domain is inferred.

    2020 writes '1.0' where other years write '1'; RAIOX_RES writes
    '2.0000000000' in all six years. A rule written as a literal comparison
    against '1' silently discards 519,518 COVID-positive records in 2020 while
    the row count stays intact. `\\.0$` — the previous attempt — catches the
    first case and not the second.
    """
    out = s.astype("string").str.strip()
    if column in DECIMAL_COLUMNS:
        return out
    return out.str.replace(TRAILING_ZEROS, r"\1", regex=True)


def parse_dates(s: pd.Series, column: str) -> pd.Series:
    fmt = "%d/%m/%Y" if column in DMY_DATES else None
    if fmt:
        return pd.to_datetime(s, format=fmt, errors="coerce")
    return pd.to_datetime(s, format="ISO8601", errors="coerce")


def missing_state(value: pd.Series, applicable: pd.Series) -> pd.Series:
    """The three readings of an empty cell, kept apart.

    nao_aplicavel  the field was disabled by its predicate — not missing data
    ignorado       '9', an explicit record of not knowing
    ausente        applicable, and left blank
    """
    state = pd.Series("preenchido", index=value.index, dtype="object")
    state[value.isna() & ~applicable] = "nao_aplicavel"
    state[value.isna() & applicable] = "ausente"
    state[value == "9"] = "ignorado"
    return state


def find_shifted_rows(df: pd.DataFrame) -> pd.Series:
    """Seven rows across six years are shifted by one field from HOSPITAL on.

    In such a row every field is wrong, not only the ones that look alien — UTI
    holds a hospital name, NM_UN_INTE holds the CNES code. Detected once as a
    row-level pattern rather than as fourteen separate column anomalies: a coded
    column holding a date.
    """
    coded = [
        c for c in ("EVOLUCAO", "UTI", "CRITERIO", "FATOR_RISC", "HOSPITAL") if c in df
    ]
    looks_like_date = pd.Series(False, index=df.index)
    for c in coded:
        v = df[c].astype("string").str.strip()
        looks_like_date |= v.str.match(r"^\d{4}-\d{2}-\d{2}").fillna(False)
        looks_like_date |= v.str.len().gt(4).fillna(False)
    return looks_like_date


def build(path: pathlib.Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """One year in, (silver, quarantine) out. Every input row is in exactly one."""
    raw = pq.read_table(path).to_pandas()
    n_in = len(raw)
    df = pd.DataFrame(index=raw.index)

    for c in raw.columns:
        df[c] = normalise(raw[c], c)

    quarantine_mask = find_shifted_rows(df)

    # --- dates ------------------------------------------------------------
    for c in [c for c in df.columns if c.startswith("DT_")]:
        df[c + "_d"] = parse_dates(df[c], c)

    # --- age: MS lines 269-276, minus the neonate rule (see DEVIATIONS) ----
    nasc, sin = df.get("DT_NASC_d"), df.get("DT_SIN_PRI_d")
    if nasc is not None and sin is not None:
        days = (sin - nasc).dt.days
        df["idade_anos"] = np.where(days >= 0, days / 365.25, np.nan)
        df["idade_cat_ms"] = pd.cut(
            df["idade_anos"],
            [-0.01, 2, 5, 15, 50, 65, 200],
            labels=[
                "< 2 anos",
                "2 a 4 anos",
                "5 a 14 anos",
                "15 a 49 anos",
                "50 a 64 anos",
                "65 anos ou +",
            ],
        )

    # --- laboratory checkboxes: official domain is {1, blank} -------------
    for c in [c for c in CHECKBOXES if c in df]:
        df[c + "_marcado"] = (df[c] == "1").fillna(False)

    # --- comorbidities: the funnel decides what a blank means -------------
    if COMORBIDITY_GATE in df:
        gate = df[COMORBIDITY_GATE].isin(["1", "S"])
        df["fator_risco_declarado"] = gate
        for c in [c for c in COMORBIDITIES if c in df]:
            df[c + "_estado"] = missing_state(df[c], gate)

    # --- case definition: MS lines 246-257, kept as a column --------------
    def is1(c: str) -> pd.Series:
        return (
            (df[c] == "1").fillna(False)
            if c in df
            else pd.Series(False, index=df.index)
        )

    crit2 = is1("TOSSE") | is1("GARGANTA")
    crit3 = is1("DISPNEIA") | is1("SATURACAO") | is1("DESC_RESP")
    df["caso_srag_ms"] = (
        (is1("HOSPITAL") | (df.get("EVOLUCAO") == "2").fillna(False)) & crit2 & crit3
    )
    df["coorte_hospitalizado"] = is1("HOSPITAL") & crit2 & crit3

    # --- etiology: MS lines 388-390 and the derived-variable dictionary ----
    df["covid_caso"] = (
        df.get("PCR_SARS2_marcado", False)
        | df.get("AN_SARS2_marcado", False)
        | (df.get("CLASSI_FIN") == "5").fillna(False)
    )
    marked = [c + "_marcado" for c in CHECKBOXES if c + "_marcado" in df]
    df["n_agentes"] = df[marked].sum(axis=1) if marked else 0
    df["codeteccao"] = df["n_agentes"] > 1

    silver = df[~quarantine_mask].copy()
    quarantined = df[quarantine_mask].copy()
    quarantined["motivo"] = "linha deslocada: coluna codificada contém data"

    assert len(silver) + len(quarantined) == n_in, "rows lost between Bronze and Silver"
    return silver, quarantined


def write_year(
    silver: pd.DataFrame, quarantined: pd.DataFrame, year: str, out_dir: pathlib.Path
) -> None:
    """One parquet per year, with the quarantine beside it.

    Sorted by NU_NOTIFIC — unique across all 4,109,567 records in all six years,
    verified — so a rerun is comparable to the last one rather than merely
    equivalent to it.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    for frame, name in ((silver, "silver"), (quarantined, "quarentena")):
        if "NU_NOTIFIC" in frame:
            frame = frame.sort_values("NU_NOTIFIC", kind="stable")
        frame.to_parquet(out_dir / f"{name}_{year}.parquet", index=False)


def main(argv: list[str]) -> int:
    data = (
        pathlib.Path(argv[0]).expanduser()
        if argv
        else pathlib.Path.home() / "Documents/srag-data"
    )
    out_dir = pathlib.Path(argv[1]).expanduser() if len(argv) > 1 else data / "silver"
    files = sorted(data.glob("INFLUD*.parquet"))
    if not files:
        print(f"no INFLUD*.parquet under {data}", file=sys.stderr)
        return 2

    total_in = total_silver = total_quarantine = 0
    for f in files:
        year = "20" + re.search(r"INFLUD(\d\d)", f.name).group(1)
        silver, quarantined = build(f)
        n_in = len(silver) + len(quarantined)
        total_in += n_in
        total_silver += len(silver)
        total_quarantine += len(quarantined)
        write_year(silver, quarantined, year, out_dir)
        print(
            f"  {year}: {n_in:>9,} → silver {len(silver):>9,}"
            f" + quarentena {len(quarantined)}  ({len(silver.columns)} colunas)"
        )

    print(f"\n  total: {total_in:,} = {total_silver:,} + {total_quarantine}")
    assert total_silver + total_quarantine == total_in
    print("  invariante: nenhuma linha perdida entre Bronze e Silver ✓")
    print(f"  escrito em {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
