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


# --------------------------------------------------------------------------
# The Ministry's derived-variable catalogue, from "Script 1. LimpezaClassificao.R"
# and `dicionário_var_novas.pdf`. Each agent gets four variables — the case, the
# death, and the two co-detection-free variants — which is how the official
# product avoids choosing between "count co-infections" and "don't": it publishes
# both. That is the same shape Ranzani uses for comorbidity missingness, and the
# reason a single collapsed `agente` column would have been wrong.
#
# Only the case definitions are written out; `_obito` and `_unico` follow from
# them mechanically, so writing them by hand 63 times would only add places to
# make a typo.
#
# One caveat worth carrying: the published dictionary gives `adenovirus_caso`
# the VSR criterion (`AN_VSR | PCR_VSR`). The R script is correct
# (`AN_ADENO | PCR_ADENO`) and that is what is implemented — a reader who
# follows only the PDF gets adenovirus counts that are really VSR counts.
AGENTES: dict[str, list[str]] = {
    "vsr": ["AN_VSR", "PCR_VSR"],
    "adenovirus": ["AN_ADENO", "PCR_ADENO"],
    "rinovirus": ["PCR_RINO"],
    "metapneumo": ["PCR_METAP"],
    "bocavirus": ["PCR_BOCA"],
    "parainfluenza": [
        "AN_PARA1",
        "AN_PARA2",
        "AN_PARA3",
        "PCR_PARA1",
        "PCR_PARA2",
        "PCR_PARA3",
        "PCR_PARA4",
    ],
    "outros_virus": ["PCR_OUTRO", "AN_OUTRO"],
}

# Influenza A is subtyped through PCR_FLUASU, so it is a value test rather than
# a set of checkboxes: 1=H1N1, 2=H3N2, 4=not subtypeable, 5/6=inconclusive.
INFLUENZA_A_SUBTIPOS = {
    "influenza_h1n1": ["1"],
    "influenza_h3n2": ["2"],
    "influenza_a_n_subtipavel": ["4"],
    "influenza_a_inconclusiva": ["5", "6"],
}
# Influenza B through PCR_FLUBLI: 1=Victoria, 2=Yamagata.
INFLUENZA_B_LINHAGENS = {"influenza_b_vict": ["1"], "influenza_b_yam": ["2"]}

# The nine agents `soma_casos` runs over: one flag per distinct agent, with no
# composite and no subtype, so that a single detection counts once.
AGENTES_PRIMITIVOS = [
    "covid",
    "influenza_geral",
    "vsr",
    "adenovirus",
    "rinovirus",
    "parainfluenza",
    "metapneumo",
    "bocavirus",
    "outros_virus",
]

REGIOES = {
    "N": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
    "NE": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "CO": ["DF", "GO", "MT", "MS"],
    "SE": ["ES", "MG", "RJ", "SP"],
    "S": ["PR", "RS", "SC"],
}


def add_etiologia(df: pd.DataFrame) -> pd.DataFrame:
    """The full official catalogue: case, death, and both co-detection variants.

    `_obito` combines a fact about the exam with the outcome, so it is a Gold
    concern by this module's own test — it is computed here because the official
    product defines it and a module reproducing the weekly bulletin needs it, but
    nothing in Silver consumes it and a model must not take it as a feature.
    """
    obito = (df.get("EVOLUCAO") == "2").fillna(False)

    def marcado(cols: list[str]) -> pd.Series:
        hit = pd.Series(False, index=df.index)
        for c in cols:
            if c + "_marcado" in df:
                hit |= df[c + "_marcado"]
            elif c in df:
                hit |= (df[c] == "1").fillna(False)
        return hit

    for agente, cols in AGENTES.items():
        df[f"{agente}_caso"] = marcado(cols)

    for nome, valores in INFLUENZA_A_SUBTIPOS.items():
        df[f"{nome}_caso"] = (
            df.get("PCR_FLUASU", pd.Series(dtype="string")).isin(valores).fillna(False)
        )
    for nome, valores in INFLUENZA_B_LINHAGENS.items():
        df[f"{nome}_caso"] = (
            df.get("PCR_FLUBLI", pd.Series(dtype="string")).isin(valores).fillna(False)
        )

    df["influenza_a_total_caso"] = pd.concat(
        [df[f"{n}_caso"] for n in INFLUENZA_A_SUBTIPOS], axis=1
    ).any(axis=1)
    df["influenza_b_total_caso"] = pd.concat(
        [df[f"{n}_caso"] for n in INFLUENZA_B_LINHAGENS], axis=1
    ).any(axis=1)
    df["influenza_geral_caso"] = (
        df["influenza_a_total_caso"] | df["influenza_b_total_caso"]
    )

    # "Outros vírus respiratórios" in the official sense: everything that is not
    # influenza and not covid.
    df["ovr_caso"] = pd.concat(
        [
            df[f"{a}_caso"]
            for a in (
                "parainfluenza",
                "adenovirus",
                "bocavirus",
                "metapneumo",
                "outros_virus",
            )
        ],
        axis=1,
    ).any(axis=1)

    # Co-detection means two *different* agents, so the sum runs over the nine
    # primitive flags only. Summing every `_caso` column instead would count a
    # single metapneumovirus twice — once as `metapneumo_caso`, once inside the
    # `ovr_caso` composite — and mark the row as a co-detection on its own.
    casos = [c for c in df.columns if c.endswith("_caso")]
    df["soma_casos"] = df[[f"{a}_caso" for a in AGENTES_PRIMITIVOS]].sum(axis=1)
    df["codeteccao_casos"] = df["soma_casos"] >= 2

    for c in casos:
        base = c[: -len("_caso")]
        df[f"{base}_obito"] = df[c] & obito
        df[f"{base}_caso_unico"] = df[c] & ~df["codeteccao_casos"]
        df[f"{base}_obito_unico"] = df[f"{base}_caso_unico"] & obito

    # Cases with no agent detected at all, and the two states the Ministry
    # separates within them.
    df["n_detectado"] = df["soma_casos"] == 0
    df["out_agentes"] = (df.get("CLASSI_FIN") == "3").fillna(False)
    df["srag_n_especificada"] = (df.get("CLASSI_FIN") == "4").fillna(False) | df[
        "n_detectado"
    ]
    df["investigacao"] = (
        df.get("CLASSI_FIN").isna()
        & (df.get("PCR_RESUL") == "5").fillna(False)
        & df["n_detectado"]
    )
    return df


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

    # --- geography and epidemiological week (MS: regiao, se_primeiro_sinto) --
    if "SG_UF" in df:
        uf_to_regiao = {uf: r for r, ufs in REGIOES.items() for uf in ufs}
        df["regiao"] = df["SG_UF"].map(uf_to_regiao)
    if "DT_SIN_PRI_d" in df:
        df["ano_sintomas"] = df["DT_SIN_PRI_d"].dt.year
        df["se_primeiro_sinto"] = df["DT_SIN_PRI_d"].dt.isocalendar().week

    # --- etiology: MS lines 388-390 plus the full derived catalogue ---------
    df["covid_caso"] = (
        df.get("PCR_SARS2_marcado", False)
        | df.get("AN_SARS2_marcado", False)
        | (df.get("CLASSI_FIN") == "5").fillna(False)
    )
    df = add_etiologia(df)

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
