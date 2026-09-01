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
import warnings

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
    "AN_OUTRO",  # the 18th — left out of the first Silver, read raw as a fallback
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

# dd/mm/yyyy fields. The DT_ prefix rule finds ISO dates; these nine do not
# follow it: the travel pair is documented dmy, the six vaccine-dose dates
# carry no DT_ prefix at all (measured: >=99.99% parse as %d/%m/%Y in every
# year), and VG_DTRES is a date the prefix rule cannot see.
DMY_DATES = [
    "DT_VGM",
    "DT_RT_VGM",
    "DOSE_1_COV",
    "DOSE_2_COV",
    "DOSE_REF",
    "DOSE_2REF",
    "DOSE_ADIC",
    "DOS_RE_BI",
    "VG_DTRES",
]
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


def days_between(later: pd.Series, earlier: pd.Series) -> pd.Series:
    """Difference in days, safe against the corrupt extremes the data carries.

    2020 stores DT_INTERNA values like `1695-06-14 02:32:37.742690304` —
    literal nanosecond timestamps three centuries out. In pandas' default
    ns resolution the subtraction overflows int64 (325 years of
    nanoseconds); at seconds resolution it does not, and the implausible
    result stays visible instead of crashing the build.
    """
    return (later.astype("datetime64[s]") - earlier.astype("datetime64[s]")).dt.days


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
# ==========================================================================
# The column contract. Families partition the 194 published columns; DOMAINS
# closes the coded value sets; GATES holds the enabling predicates the data
# confirms, with the measured worst-year contradiction each carries; the
# class lists say what a column may be used for downstream. Everything here
# is the single source read by build(), by tools/build_srag_columns.py
# (COLUMNS.md), by tools/build_srag_dictionary.py (its section layout) and
# by tools/srag_quality.py.
# ==========================================================================

FAMILIES: list[tuple[str, list[str]]] = [
    (
        "Identificação e notificação",
        [
            "NU_NOTIFIC",
            "DT_NOTIFIC",
            "SEM_NOT",
            "DT_SIN_PRI",
            "SEM_PRI",
            "SG_UF_NOT",
            "ID_REGIONA",
            "CO_REGIONA",
            "ID_MUNICIP",
            "CO_MUN_NOT",
            "DT_DIGITA",
            "TEM_CPF",
            "ESTRANG",
            "SURTO_SG",
            "NOSOCOMIAL",
            "AVE_SUINO",
            "OUT_ANIM",
        ],
    ),
    (
        "Demografia e residência",
        [
            "CS_SEXO",
            "DT_NASC",
            "NU_IDADE_N",
            "TP_IDADE",
            "COD_IDADE",
            "CS_GESTANT",
            "CS_RACA",
            "CS_ETINIA",
            "CS_ESCOL_N",
            "CS_ZONA",
            "POV_CT",
            "TP_POV_CT",
            "ID_PAIS",
            "CO_PAIS",
            "SG_UF",
            "ID_RG_RESI",
            "CO_RG_RESI",
            "ID_MN_RESI",
            "CO_MUN_RES",
            "PAC_COCBO",
            "PAC_DSCBO",
        ],
    ),
    (
        "Sinais e sintomas",
        [
            "FEBRE",
            "TOSSE",
            "GARGANTA",
            "DISPNEIA",
            "DESC_RESP",
            "SATURACAO",
            "DIARREIA",
            "VOMITO",
            "DOR_ABD",
            "FADIGA",
            "PERD_OLFT",
            "PERD_PALA",
            "OUTRO_SIN",
            "OUTRO_DES",
        ],
    ),
    (
        "Comorbidades e fatores de risco",
        [
            "FATOR_RISC",
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
            "OBES_IMC",
            "OUT_MORBI",
            "MORB_DESC",
            "TABAG",
        ],
    ),
    (
        "Vacinação",
        [
            "VACINA",
            "DT_UT_DOSE",
            "MAE_VAC",
            "DT_VAC_MAE",
            "M_AMAMENTA",
            "DT_DOSEUNI",
            "DT_1_DOSE",
            "DT_2_DOSE",
            "VACINA_COV",
            "DOSE_1_COV",
            "DOSE_2_COV",
            "DOSE_REF",
            "DOSE_2REF",
            "DOSE_ADIC",
            "DOS_RE_BI",
            "FAB_COV_1",
            "FAB_COV_2",
            "FAB_COVRF",
            "FAB_COVRF2",
            "FAB_ADIC",
            "FAB_RE_BI",
            "LOTE_1_COV",
            "LOTE_2_COV",
            "LOTE_REF",
            "LOTE_REF2",
            "LOTE_ADIC",
            "LOT_RE_BI",
            "FNT_IN_COV",
        ],
    ),
    (
        "Internação, UTI e suporte ventilatório",
        [
            "HOSPITAL",
            "DT_INTERNA",
            "SG_UF_INTE",
            "ID_RG_INTE",
            "CO_RG_INTE",
            "ID_MN_INTE",
            "CO_MU_INTE",
            "NM_UN_INTE",
            "UTI",
            "DT_ENTUTI",
            "DT_SAIDUTI",
            "SUPORT_VEN",
        ],
    ),
    (
        "Tratamento",
        [
            "ANTIVIRAL",
            "TP_ANTIVIR",
            "OUT_ANTIV",
            "DT_ANTIVIR",
            "TRAT_COV",
            "TIPO_TRAT",
            "DT_TRT_COV",
            "OUT_TRAT",
        ],
    ),
    (
        "Imagem",
        ["RAIOX_RES", "RAIOX_OUT", "DT_RAIOX", "TOMO_RES", "TOMO_OUT", "DT_TOMO"],
    ),
    (
        "Laboratório — RT-PCR",
        [
            "AMOSTRA",
            "DT_COLETA",
            "TP_AMOSTRA",
            "OUT_AMOST",
            "PCR_RESUL",
            "DT_PCR",
            "POS_PCRFLU",
            "TP_FLU_PCR",
            "PCR_FLUASU",
            "FLUASU_OUT",
            "PCR_FLUBLI",
            "FLUBLI_OUT",
            "POS_PCROUT",
            "PCR_VSR",
            "PCR_PARA1",
            "PCR_PARA2",
            "PCR_PARA3",
            "PCR_PARA4",
            "PCR_ADENO",
            "PCR_METAP",
            "PCR_BOCA",
            "PCR_RINO",
            "PCR_OUTRO",
            "DS_PCR_OUT",
            "PCR_SARS2",
        ],
    ),
    (
        "Laboratório — antigênico e sorologia",
        [
            "TP_TES_AN",
            "DT_RES_AN",
            "RES_AN",
            "POS_AN_FLU",
            "TP_FLU_AN",
            "POS_AN_OUT",
            "AN_SARS2",
            "AN_VSR",
            "AN_PARA1",
            "AN_PARA2",
            "AN_PARA3",
            "AN_ADENO",
            "AN_OUTRO",
            "DS_AN_OUT",
            "TP_AM_SOR",
            "SOR_OUT",
            "DT_CO_SOR",
            "TP_SOR",
            "OUT_SOR",
            "DT_RES",
            "RES_IGG",
            "RES_IGM",
            "RES_IGA",
        ],
    ),
    (
        "Vigilância genômica e reinfecção",
        [
            "CO_DETEC",
            "VG_OMS",
            "VG_OMSOUT",
            "VG_LIN",
            "VG_MET",
            "VG_METOUT",
            "VG_DTRES",
            "VG_ENC",
            "VG_REINF",
            "VG_CODEST",
            "REINF",
        ],
    ),
    (
        "Histórico de viagem",
        ["HISTO_VGM", "PAIS_VGM", "CO_PS_VGM", "LO_PS_VGM", "DT_VGM", "DT_RT_VGM"],
    ),
    (
        "Encerramento e desfecho",
        [
            "CLASSI_FIN",
            "CLASSI_OUT",
            "CRITERIO",
            "EVOLUCAO",
            "DT_EVOLUCA",
            "DT_ENCERRA",
        ],
    ),
]

ALL_COLUMNS: frozenset[str] = frozenset(c for _, cs in FAMILIES for c in cs)

UF_CODES = {
    "RO": "11",
    "AC": "12",
    "AM": "13",
    "RR": "14",
    "PA": "15",
    "AP": "16",
    "TO": "17",
    "MA": "21",
    "PI": "22",
    "CE": "23",
    "RN": "24",
    "PB": "25",
    "PE": "26",
    "AL": "27",
    "SE": "28",
    "BA": "29",
    "MG": "31",
    "ES": "32",
    "RJ": "33",
    "SP": "35",
    "PR": "41",
    "SC": "42",
    "RS": "43",
    "MS": "50",
    "MT": "51",
    "GO": "52",
    "DF": "53",
}
UFS = tuple(sorted(UF_CODES))

SINTOMAS = [
    "FEBRE",
    "TOSSE",
    "GARGANTA",
    "DISPNEIA",
    "DESC_RESP",
    "SATURACAO",
    "DIARREIA",
    "VOMITO",
    "DOR_ABD",
    "FADIGA",
    "PERD_OLFT",
    "PERD_PALA",
    "OUTRO_SIN",
]

# Closed value sets, after normalise(). DOMAIN_SOURCE records the authority:
# "pdf" when the official dictionary prints the codes, "observed" when only
# the data speaks (HISTO_VGM's 0 is real and undocumented), "inferred" when a
# sibling's scale is extended and the extension is declared.
_D129 = ("1", "2", "9")
_D169 = ("1", "2", "3", "4", "5", "6", "9")
_RES = ("1", "2", "3", "4", "5", "9")
DOMAINS: dict[str, tuple[str, ...]] = {
    # identificação
    "TEM_CPF": ("1", "2"),
    "ESTRANG": ("1", "2"),
    "SURTO_SG": _D129,
    "NOSOCOMIAL": _D129,
    "AVE_SUINO": ("1", "2", "3", "9"),
    "SG_UF_NOT": UFS,
    "SG_UF": UFS,
    "SG_UF_INTE": UFS,
    # demografia
    "CS_SEXO": ("M", "F", "I"),
    "TP_IDADE": ("1", "2", "3"),
    "CS_GESTANT": ("1", "2", "3", "4", "5", "6", "9"),
    "CS_RACA": ("1", "2", "3", "4", "5", "9"),
    "CS_ESCOL_N": ("0", "1", "2", "3", "4", "5", "9"),
    "CS_ZONA": ("1", "2", "3", "9"),
    "POV_CT": ("1", "2"),
    # sintomas
    **{c: _D129 for c in SINTOMAS},
    # comorbidades
    **{c: _D129 for c in COMORBIDITIES},
    "TABAG": _D129,
    # the funnel variable itself: 1/2 in the current form, S/N in the legacy
    # encoding some years still carry, 9 observed
    "FATOR_RISC": ("1", "2", "9", "S", "N"),
    # vacinação
    "VACINA": _D129,
    "MAE_VAC": _D129,
    "M_AMAMENTA": _D129,
    "VACINA_COV": _D129,
    "FNT_IN_COV": ("1", "2"),
    # internação
    "HOSPITAL": _D129,
    "UTI": _D129,
    "SUPORT_VEN": ("1", "2", "3", "9"),
    # tratamento
    "ANTIVIRAL": _D129,
    "TP_ANTIVIR": ("1", "2", "3"),
    "TRAT_COV": _D129,
    "TIPO_TRAT": ("1", "2", "3", "4"),
    # imagem
    "RAIOX_RES": _D169,
    "TOMO_RES": _D169,
    # laboratório
    "AMOSTRA": _D129,
    "TP_AMOSTRA": _RES,
    "PCR_RESUL": _RES,
    "POS_PCRFLU": _D129,
    "TP_FLU_PCR": ("1", "2"),
    "PCR_FLUASU": ("1", "2", "3", "4", "5", "6"),
    "PCR_FLUBLI": ("1", "2", "3", "4", "5"),
    "POS_PCROUT": _D129,
    "TP_TES_AN": ("1", "2"),
    "RES_AN": _RES,
    "POS_AN_FLU": _D129,
    "TP_FLU_AN": ("1", "2"),
    "POS_AN_OUT": _D129,
    "TP_AM_SOR": _D129,
    "TP_SOR": ("1", "2", "3", "4"),
    "RES_IGG": _RES,
    "RES_IGM": _RES,
    "RES_IGA": _RES,
    **{c: ("1",) for c in CHECKBOXES},
    # vigilância genômica
    "CO_DETEC": _D129,
    "VG_OMS": ("1", "2", "3", "4", "5", "6", "7"),
    "VG_MET": ("1", "2", "3", "4"),
    "VG_ENC": ("1", "2", "3", "4", "5"),
    "VG_REINF": _D129,
    "REINF": _D129,
    # viagem
    "HISTO_VGM": ("0", "1", "2", "9"),
    # encerramento
    "EVOLUCAO": ("1", "2", "3", "9"),
    "CLASSI_FIN": ("1", "2", "3", "4", "5"),
    "CRITERIO": ("1", "2", "3", "4"),
}
DOMAIN_SOURCE: dict[str, str] = {
    **{c: "pdf" for c in DOMAINS},
    "SG_UF_NOT": "observed",
    "SG_UF": "observed",
    "SG_UF_INTE": "observed",
    "HISTO_VGM": "observed",  # 0 dominates and the PDF documents no domain
    "FATOR_RISC": "observed",  # mixed current and legacy encodings
    "RES_IGG": "inferred",
    "RES_IGM": "inferred",
    "RES_IGA": "inferred",
    "REINF": "inferred",
    **{c: "observed" for c in CHECKBOXES},
}

FREE_TEXT = frozenset(
    {
        "OUT_ANIM",
        "TP_POV_CT",
        "CS_ETINIA",
        "OUTRO_DES",
        "MORB_DESC",
        "OUT_ANTIV",
        "OUT_TRAT",
        "RAIOX_OUT",
        "TOMO_OUT",
        "OUT_AMOST",
        "DS_PCR_OUT",
        "FLUASU_OUT",
        "FLUBLI_OUT",
        "DS_AN_OUT",
        "SOR_OUT",
        "OUT_SOR",
        "VG_OMSOUT",
        "VG_METOUT",
        "VG_LIN",
        "CLASSI_OUT",
        "LO_PS_VGM",
        "PAC_DSCBO",
    }
)

# (name column, code column) pairs carrying the same information twice. The
# name side is what a human typed; the code side is what joins.
CODE_PAIRS: dict[str, str] = {
    "ID_REGIONA": "CO_REGIONA",
    "ID_MUNICIP": "CO_MUN_NOT",
    "ID_PAIS": "CO_PAIS",
    "ID_RG_RESI": "CO_RG_RESI",
    "ID_MN_RESI": "CO_MUN_RES",
    "ID_RG_INTE": "CO_RG_INTE",
    "ID_MN_INTE": "CO_MU_INTE",
    "PAC_DSCBO": "PAC_COCBO",
    "PAIS_VGM": "CO_PS_VGM",
}

# A value that cannot exist, or cannot take its final value, before the
# outcome. EVOLUCAO heads the list because it IS the outcome. Derived columns
# inherit the flag from their inputs (the _obito variants, dias_uti,
# dias_ate_internacao, caso_srag_ms).
LEAKAGE_COLS = frozenset(
    {
        "EVOLUCAO",
        "DT_EVOLUCA",
        "DT_ENCERRA",
        "UTI",
        "DT_ENTUTI",
        "DT_SAIDUTI",
        "SUPORT_VEN",
        "CLASSI_FIN",
        "CLASSI_OUT",
        "CRITERIO",
        "VG_ENC",
    }
)

# Free-form names, codes of artifacts, or quasi-identifiers: never a feature.
# DT_NASC is here for privacy — with municipality and sex it re-identifies —
# and because idade_anos already carries what a model should see of it.
IDENTIFIER_COLS = frozenset(
    {
        "NU_NOTIFIC",
        "NM_UN_INTE",
        "VG_CODEST",
        "DT_NASC",
        "LOTE_1_COV",
        "LOTE_2_COV",
        "LOTE_REF",
        "LOTE_REF2",
        "LOTE_ADIC",
        "LOT_RE_BI",
    }
)

# 100% empty in at least one year: the blank encodes the year, not the
# patient. Derived from PROFILE.json (fill == 0.0 exactly, unrounded);
# tools/build_srag_columns.py re-derives the list and fails if it drifts.
YEAR_GATED = frozenset(
    {
        "OUT_ANIM",
        "TABAG",
        "TIPO_TRAT",
        "OUT_TRAT",
        "SOR_OUT",
        "OUT_SOR",
        "VG_OMS",
        "VG_OMSOUT",
        "VG_LIN",
        "VG_MET",
        "VG_METOUT",
        "VG_DTRES",
        "VG_ENC",
        "VG_REINF",
        "VG_CODEST",
        "PAIS_VGM",
        "CO_PS_VGM",
        "LO_PS_VGM",
        "DT_VGM",
        "DT_RT_VGM",
        "DT_TRT_COV",
    }
)

# --------------------------------------------------------------------------
# O catálogo das derivadas: toda coluna que o Silver cria ganha um label de
# definição, em português, com a origem e a proveniência (linha do script do
# Ministério, ou "deste módulo"). O gerador do COLUMNS.md renderiza o
# catálogo, e write_year() confere que as colunas realmente criadas são
# exatamente as catalogadas — uma derivada sem label quebra o build, igual a
# uma coluna crua sem regra.
# --------------------------------------------------------------------------

_AGENTES_LABELS = {
    "covid": (
        "SARS-CoV-2 detectado (PCR_SARS2 ou AN_SARS2 marcados, ou CLASSI_FIN = 5)",
        "MS l.388-390",
    ),
    "vsr": ("vírus sincicial respiratório detectado (AN_VSR ou PCR_VSR)", "MS l.~420"),
    "adenovirus": (
        "adenovírus detectado (AN_ADENO ou PCR_ADENO — o script; o PDF oficial erra e repete o critério do VSR)",
        "MS script",
    ),
    "rinovirus": ("rinovírus detectado (PCR_RINO)", "MS script"),
    "metapneumo": ("metapneumovírus detectado (PCR_METAP)", "MS script"),
    "bocavirus": ("bocavírus detectado (PCR_BOCA)", "MS script"),
    "parainfluenza": (
        "parainfluenza detectada (AN_PARA1-3 ou PCR_PARA1-4)",
        "MS script",
    ),
    "outros_virus": ("outro vírus detectado (PCR_OUTRO ou AN_OUTRO)", "MS script"),
    "influenza_h1n1": ("influenza A(H1N1)pdm09 (PCR_FLUASU = 1)", "MS script"),
    "influenza_h3n2": ("influenza A(H3N2) (PCR_FLUASU = 2)", "MS script"),
    "influenza_a_n_subtipavel": (
        "influenza A não subtipável (PCR_FLUASU = 4)",
        "MS l.457",
    ),
    "influenza_a_inconclusiva": (
        "influenza A inconclusiva (PCR_FLUASU = 5 ou 6; o PDF chama 6 de Outro — seguimos o script)",
        "MS l.441",
    ),
    "influenza_a_n_sub": (
        "influenza A não subtipada: PCR_FLUASU = 3, ou triagem A positiva (TP_FLU_AN/TP_FLU_PCR = 1) sem nenhum subtipo",
        "MS l.474",
    ),
    "influenza_b_vict": ("influenza B linhagem Victoria (PCR_FLUBLI = 1)", "MS l.517"),
    "influenza_b_yam": ("influenza B linhagem Yamagata (PCR_FLUBLI = 2)", "MS l.533"),
    "influenza_b_inconclusivo": (
        "influenza B inconclusiva: triagem B positiva (TP_FLU_AN/TP_FLU_PCR = 2) sem linhagem",
        "MS l.557",
    ),
    "influenza_a_total": (
        "qualquer influenza A (união dos cinco flags de A)",
        "MS script",
    ),
    "influenza_b_total": (
        "qualquer influenza B (união dos três flags de B)",
        "MS script",
    ),
    "influenza_geral": ("qualquer influenza, A ou B", "MS script"),
    "ovr": (
        '"outros vírus respiratórios" no sentido oficial: parainfluenza, adenovírus, bocavírus, metapneumovírus ou outros — nem influenza, nem COVID',
        "MS script",
    ),
}

_FATOS_LABELS = {
    "fator_risco_declarado": (
        "FATOR_RISC em {1, S}: o portão que habilita o bloco de comorbidades",
        "deste módulo",
    ),
    "caso_srag_ms": (
        "a definição oficial completa de caso SRAG: (HOSPITAL = 1 ou EVOLUCAO = 2) e (tosse ou garganta) e (dispneia, saturação ou desconforto). Usa o desfecho: classe leakage",
        "MS l.246-257",
    ),
    "coorte_hospitalizado": (
        "caso SRAG sem a circularidade do desfecho: HOSPITAL = 1 e os mesmos sintomas",
        "deste módulo",
    ),
    "regiao": ("região (N/NE/CO/SE/S) da UF de residência", "MS script"),
    "ano_sintomas": ("ano-calendário de DT_SIN_PRI", "deste módulo"),
    "se_primeiro_sinto": (
        "semana epidemiológica MMWR (domingo) do primeiro sintoma — confere 100,00% com SEM_PRI nos seis anos",
        "MS script (epiweek)",
    ),
    "ano_epi_primeiro_sinto": (
        "ano epidemiológico do primeiro sintoma (dezembro em semana 1 pertence ao ano seguinte)",
        "deste módulo",
    ),
    "se_notificacao": (
        "semana epidemiológica MMWR da notificação — confere 100,00% com SEM_NOT",
        "deste módulo",
    ),
    "ano_epi_notificacao": ("ano epidemiológico da notificação", "deste módulo"),
    "idade_anos": (
        "idade em anos, das datas: (DT_SIN_PRI - DT_NASC)/365,25; recém-nascido sintomático no parto fica 0, não vazio",
        "MS l.269-276, com desvio",
    ),
    "idade_cat_ms": (
        "faixa etária oficial: <2, 2-4, 5-14, 15-49, 50-64, 65+",
        "MS script",
    ),
    "idade_unidade": (
        "a unidade de NU_IDADE_N segundo TP_IDADE: dia, mês ou ano",
        "deste módulo",
    ),
    "idade_declarada_anos": (
        "NU_IDADE_N convertida para anos pela unidade declarada",
        "deste módulo",
    ),
    "cod_idade_consistente": (
        "COD_IDADE = TP_IDADE + zfill(NU_IDADE_N, 3)? Falha em 20 linhas de 4,1 M — todas com idade negativa",
        "deste módulo",
    ),
    "vacina_covid_declarada": (
        "VACINA_COV = 1 (declaração, independente das datas de dose)",
        "deste módulo",
    ),
    "n_doses_covid_registradas": (
        "quantas das seis datas de dose estão preenchidas (0-6)",
        "deste módulo",
    ),
    "dose_1_covid_antes_campanha": (
        "primeira dose anterior a 17/01/2021, o início da campanha — flag, nunca reparo",
        "deste módulo",
    ),
    "n_sintomas_marcados": (
        "quantos dos 13 sintomas codificados estão em 1",
        "deste módulo",
    ),
    "n_sintomas_ignorados": ("quantos dos 13 sintomas estão em 9", "deste módulo"),
    "n_sintomas_ausentes": ("quantos dos 13 sintomas estão vazios", "deste módulo"),
    "dias_uti": (
        "DT_SAIDUTI - DT_ENTUTI, em dias. Decorre da gravidade: classe leakage",
        "deste módulo",
    ),
    "dias_ate_internacao": (
        "DT_INTERNA - DT_SIN_PRI, em dias. Classe leakage",
        "deste módulo",
    ),
    "municipio_notif_valido": (
        "CO_MUN_NOT existe na tabela IBGE pinada",
        "deste módulo",
    ),
    "municipio_notif_df_ra": (
        "CO_MUN_NOT é região administrativa do DF (pseudo-código DATASUS, fora do IBGE)",
        "deste módulo",
    ),
    "municipio_resid_valido": (
        "CO_MUN_RES existe na tabela IBGE pinada",
        "deste módulo",
    ),
    "municipio_resid_df_ra": (
        "CO_MUN_RES é região administrativa do DF",
        "deste módulo",
    ),
    "municipio_inte_valido": (
        "CO_MU_INTE existe na tabela IBGE pinada",
        "deste módulo",
    ),
    "municipio_inte_df_ra": (
        "CO_MU_INTE é região administrativa do DF",
        "deste módulo",
    ),
    "uf_resid_coerente": (
        "os dois primeiros dígitos de CO_MUN_RES batem com o código IBGE de SG_UF",
        "deste módulo",
    ),
    "soma_casos": ("quantos dos 9 agentes primitivos foram detectados", "MS script"),
    "codeteccao_casos": (
        "dois ou mais agentes distintos detectados (soma_casos >= 2)",
        "MS script",
    ),
    "n_detectado": ("nenhum agente detectado (soma_casos = 0)", "MS script"),
    "out_agentes": ("CLASSI_FIN = 3, SRAG por outro agente etiológico", "MS script"),
    "srag_n_especificada": ("CLASSI_FIN = 4 ou nenhum agente detectado", "MS script"),
    "investigacao": (
        "sem classificação final, PCR em análise (PCR_RESUL = 5) e nada detectado",
        "MS script",
    ),
}


def derived_catalogue() -> dict[str, tuple[str, str, str]]:
    """nome -> (definição em português, proveniência, classe).

    Construído das mesmas tabelas que build() usa, então a lista de colunas não
    pode divergir do que o Silver realmente cria — e write_year() confere.
    """
    cat: dict[str, tuple[str, str, str]] = {}
    date_cols = sorted(c for c in ALL_COLUMNS if c.startswith("DT_")) + [
        c for c in DMY_DATES if not c.startswith("DT_")
    ]
    for c in date_cols:
        fmt = "dd/mm/aaaa" if c in DMY_DATES else "ISO"
        cat[c + "_d"] = (
            f"{c} convertida de texto para data ({fmt})",
            "deste módulo",
            "ok",
        )
    for c in CHECKBOXES:
        cat[c + "_marcado"] = (
            f"checkbox {c}: True quando 1; vazio significa não marcado, nunca ausente",
            "deste módulo",
            "ok",
        )
    for child, (parent, values, tier, _) in GATES.items():
        cat[child + "_estado"] = (
            (
                f"os estados do vazio de {child}: preenchido / nao_aplicavel "
                f"(portão {parent} em {{{','.join(values)}}}, tier {tier}) / "
                "ausente / ignorado"
            ),
            "deste módulo",
            "ok",
        )
    for c in SINTOMAS:
        cat[c + "_estado"] = (
            f"os estados do vazio de {c}: sem portão que passe a regra-G — preenchido / ausente / ignorado",
            "deste módulo",
            "ok",
        )
    for base, (definicao, fonte) in _AGENTES_LABELS.items():
        cat[base + "_caso"] = (definicao, fonte, "ok")
        cat[base + "_obito"] = (
            f"{base}_caso e EVOLUCAO = 2. Combina exame com desfecho: classe leakage",
            fonte,
            "leakage",
        )
        cat[base + "_caso_unico"] = (
            f"{base}_caso sem co-detecção (codeteccao_casos = False)",
            fonte,
            "ok",
        )
        cat[base + "_obito_unico"] = (
            f"{base}_caso_unico e EVOLUCAO = 2: classe leakage",
            fonte,
            "leakage",
        )
    for c in FAB_COLUMNS:
        cat[c + "_codigo"] = (
            f"código PNI extraído do prefixo de {c} (ex.: 86 = CoronaVac)",
            "deste módulo",
            "ok",
        )
        cat[c + "_fabricante"] = (
            f"{c} harmonizado no vocabulário de 8 fabricantes; mojibake 0x81 reparado; cru preservado",
            "deste módulo",
            "ok",
        )
    for nome, (definicao, fonte) in _FATOS_LABELS.items():
        classe = (
            "leakage"
            if nome in ("caso_srag_ms", "dias_uti", "dias_ate_internacao")
            else "ok"
        )
        cat[nome] = (definicao, fonte, classe)
    return cat


DOSE_DATES = [
    "DOSE_1_COV",
    "DOSE_2_COV",
    "DOSE_REF",
    "DOSE_2REF",
    "DOSE_ADIC",
    "DOS_RE_BI",
]
FAB_COLUMNS = [
    "FAB_COV_1",
    "FAB_COV_2",
    "FAB_COVRF",
    "FAB_COVRF2",
    "FAB_ADIC",
    "FAB_RE_BI",
]

# Manufacturer harmonisation, built from the measured vocabulary: 2,092,142
# filled cells, 7,823 distinct raw values, top-30 covering 96.6%. The PNI
# code prefix ("86 - COVID-19 SINOVAC/BUTANTAN - CORONAVAC") covers 94-99%
# of cells in every year except 2021 — the campaign's first year, 55%, when
# free text ("CORONAVAC", "ASTRAZENICA", "FIO CRUZ") was still common.
# 20,842 cells carry the mojibake byte 0x81 where an accented A should be
# ("PEDIA\x81TRICA"); the derived column repairs it, the raw one keeps it.
# Codes 14-67 are OTHER vaccines (BCG, polio, HPV...) leaking in from the
# general PNI registry — named as such, not folded into an existing maker.
FABRICANTES_POR_CODIGO = {
    "85": "astrazeneca",
    "89": "astrazeneca",
    "86": "sinovac_butantan",
    "98": "sinovac_butantan",
    "87": "pfizer",
    "19": "pfizer",
    "99": "pfizer_pediatrica",
    "102": "pfizer_pediatrica",
    "103": "pfizer_bivalente",
    "88": "janssen",
    "97": "moderna",
    "33": "nao_harmonizado",  # "PENDENTE IDENTIFICACAO"
    "81": "nao_harmonizado",
    **{
        c: "outro_imunobiologico"
        for c in (
            "14",
            "15",
            "22",
            "24",
            "25",
            "26",
            "41",
            "42",
            "45",
            "46",
            "55",
            "57",
            "67",
        )
    },
}
# Substring rules for the code-less cells, checked in order — BIVALENTE and
# PEDIATRICA must fire before the bare PFIZER.
FABRICANTES_POR_TEXTO = [
    ("BIVALENTE", "pfizer_bivalente"),
    ("PEDIATRICA", "pfizer_pediatrica"),
    ("CORONAVAC", "sinovac_butantan"),
    ("BUTANTAN", "sinovac_butantan"),
    ("SINOVAC", "sinovac_butantan"),
    ("ASTRAZEN", "astrazeneca"),
    ("COVISHIELD", "astrazeneca"),
    ("OXFORD", "astrazeneca"),
    ("FIOCRUZ", "astrazeneca"),
    ("FIO CRUZ", "astrazeneca"),
    ("OSWALDO", "astrazeneca"),
    ("CHADOX", "astrazeneca"),
    ("COMIRNATY", "pfizer"),
    ("PFIZER", "pfizer"),
    ("JANSSEN", "janssen"),
    ("SPIKEVAX", "moderna"),
    ("MODERNA", "moderna"),
]
_FAB_CODE = re.compile(r"^(\d{2,3})\s*-")


def harmonise_fabricante(s: pd.Series) -> tuple[pd.Series, pd.Series]:
    """(PNI code, harmonised maker) for one FAB_* column. Raw stays raw."""
    limpo = s.str.replace("\x81", "", regex=False).str.upper().str.strip()
    codigo = limpo.str.extract(_FAB_CODE, expand=False)
    fabricante = codigo.map(FABRICANTES_POR_CODIGO)
    resto = fabricante.isna() & limpo.notna()
    for padrao, nome in FABRICANTES_POR_TEXTO:
        alvo = resto & limpo.str.contains(padrao, regex=False)
        fabricante[alvo] = nome
        resto &= ~alvo
    fabricante[resto] = "nao_harmonizado"
    return codigo, fabricante


_IBGE_CSV = (
    pathlib.Path(__file__).resolve().parent.parent
    / "modules/00-dataset/reference/municipios_ibge.csv"
)


def _ibge_codigos6() -> frozenset[str]:
    """The pinned IBGE municipality table (see tools/fetch_ibge_municipios.py)."""
    import csv

    with _IBGE_CSV.open(encoding="utf-8") as f:
        return frozenset(r["codigo6"] for r in csv.DictReader(f))


CLASS_PRECEDENCE = (
    "leakage",
    "identifier",
    "free_text",
    "code_pair",
    "year_gated",
    "ok",
)


def column_flags(col: str) -> tuple[str, ...]:
    """Every class flag a column carries; `class_of` collapses by precedence."""
    flags = []
    if col in LEAKAGE_COLS:
        flags.append("leakage")
    if col in IDENTIFIER_COLS:
        flags.append("identifier")
    if col in FREE_TEXT:
        flags.append("free_text")
    if col in CODE_PAIRS or col in CODE_PAIRS.values():
        flags.append("code_pair")
    if col in YEAR_GATED:
        flags.append("year_gated")
    return tuple(flags) or ("ok",)


def class_of(col: str) -> str:
    flags = column_flags(col)
    return next(f for f in CLASS_PRECEDENCE if f in flags)


# Enabling predicates the data confirms, child -> (parent, values, tier,
# measured worst-year contradiction %). The G-rule: adopted only when, in
# each of the six years, the child has support and the contradiction —
# child filled while parent outside the values — stays at 0.00% (tier A) or
# <= 0.05% (tier B). build() re-measures every entry on every year it
# processes and refuses to run if the recorded bound is broken: a gate
# adopted on a 2026 measurement and never re-measured is exactly the failure
# mode the profiler was written to prevent.
GATES: dict[str, tuple[str, tuple[str, ...], str, float]] = {
    **{c: ("FATOR_RISC", ("1", "S"), "A", 0.0) for c in COMORBIDITIES},
    "MORB_DESC": ("OUT_MORBI", ("1",), "A", 0.0),
    "CS_ETINIA": ("CS_RACA", ("5",), "A", 0.0),
    "TP_FLU_PCR": ("POS_PCRFLU", ("1",), "A", 0.0),
    "PCR_FLUASU": ("TP_FLU_PCR", ("1",), "A", 0.0),
    "TP_FLU_AN": ("POS_AN_FLU", ("1",), "A", 0.0),
    "OUT_ANTIV": ("TP_ANTIVIR", ("3",), "A", 0.0),
    # 0.00% flat but the child never reaches 1,000 filled rows in a year
    # (min 56), so tier A's support clause fails: B on support, not on
    # contradiction.
    "PCR_FLUBLI": ("TP_FLU_PCR", ("2",), "B", 0.0),
    "DT_TRT_COV": ("TRAT_COV", ("1",), "B", 0.0),
    "OBES_IMC": ("OBESIDADE", ("1",), "B", 0.0037),
    "OUTRO_DES": ("OUTRO_SIN", ("1",), "B", 0.0003),
    "DT_ENTUTI": ("UTI", ("1",), "B", 0.0021),
    "DT_SAIDUTI": ("UTI", ("1",), "B", 0.0024),
    "TP_AMOSTRA": ("AMOSTRA", ("1",), "B", 0.0006),
    "DT_COLETA": ("AMOSTRA", ("1",), "B", 0.0012),
    "DT_INTERNA": ("HOSPITAL", ("1",), "B", 0.0042),
    "TP_ANTIVIR": ("ANTIVIRAL", ("1",), "B", 0.0101),
    "DT_ANTIVIR": ("ANTIVIRAL", ("1",), "B", 0.0101),
    "RAIOX_OUT": ("RAIOX_RES", ("5",), "B", 0.0092),
    "OUT_AMOST": ("TP_AMOSTRA", ("4",), "B", 0.0112),
    # V = exam done. Adding 9 to V changes nothing: zero rows nationwide
    # carry RAIOX_RES == 9 with DT_RAIOX filled.
    "DT_RAIOX": ("RAIOX_RES", ("1", "2", "3", "4", "5"), "B", 0.0083),
    "DT_UT_DOSE": ("VACINA", ("1",), "B", 0.0099),
}

# Predicates the dictionary documents and the data contradicts. Recorded with
# the worst measured year because a documented rule the data breaks is a
# finding, not an omission — two are contradicted every single time.
GATES_REJECTED: dict[str, tuple[str, str, float, str]] = {
    "DOSE_*_COV/FAB_*/LOTE_*": (
        "VACINA_COV",
        "1",
        0.4598,
        "1,701 FAB_COV_1 cells in 2021 while VACINA_COV is not 1",
    ),
    "AN_* checkboxes": (
        "POS_AN_OUT",
        "1",
        6.40,
        "0.00-1.6% in five years, then AN_ADENO 6.04% / AN_OUTRO 6.40% in 2024 — the family degrades in the newest year; the one-year measurement trap",
    ),
    "PCR_* checkboxes": (
        "POS_PCROUT",
        "1",
        0.0289,
        "would pass tier B, kept ungated: a checkbox blank already means not-marked",
    ),
    "OUT_TRAT": (
        "TIPO_TRAT",
        "4",
        100.0,
        "TIPO_TRAT never takes the value 4 in 4.1M rows — a documented predicate that cannot ever hold",
    ),
    "PAIS_VGM": (
        "HISTO_VGM",
        "1",
        12.90,
        "12.9% in 2021 (n=62); the travel block stops being collected after 2021 and HISTO_VGM is uniformly 0",
    ),
    "CLASSI_OUT": ("CLASSI_FIN", "3", 0.1409, "above the 0.05% bar (2021)"),
    "SG_UF_INTE/NM_UN_INTE": ("HOSPITAL", "1", 0.2060, "above the 0.05% bar (2019)"),
    "TOMO_OUT": (
        "TOMO_RES",
        "5",
        3.77,
        "same design as RAIOX_OUT, which passes at 0.0092% — the asymmetry is real (2021)",
    ),
    "DT_TOMO": (
        "TOMO_RES",
        "1-5",
        0.1499,
        "the imaging-date pair splits: DT_RAIOX passes, DT_TOMO does not (2022)",
    ),
    "DT_VAC_MAE": ("MAE_VAC", "1", 0.87, "above the bar (2021)"),
    "TIPO_TRAT": ("TRAT_COV", "1", 0.0955, "above the bar (2023)"),
    "DT_RES_AN": (
        "TP_TES_AN",
        "1/2",
        8.96,
        "antigen result dates exist without a recorded test type (2020)",
    ),
    "DS_AN_OUT": ("POS_AN_OUT", "1", 3.02, "above the bar (2024)"),
    "DT_CO_SOR/DT_RES": (
        "TP_AM_SOR",
        "1/2",
        64.5,
        "sorology dates are filled while the sample-type field is not — the block is not funnel-shaped at all",
    ),
}


def epiweek(d: pd.Series) -> pd.Series:
    """The Brazilian epidemiological week: MMWR, Sunday-start.

    The first Silver derived this as `d.dt.isocalendar().week` — the ISO,
    Monday-start week — which agrees with the system's own SEM_PRI in only
    ~86% of rows. Shifting the date one day forward maps Sunday-start onto
    ISO's Monday-start and its "four days in January" rule onto MMWR's:
    measured against SEM_PRI and SEM_NOT, agreement is 100.00% in each of
    the six years. One record in seven was in the wrong week.
    """
    return (d + pd.Timedelta(days=1)).dt.isocalendar().week


def epiyear(d: pd.Series) -> pd.Series:
    """The year the epidemiological week belongs to, not the calendar year.

    A late-December date in week 1 belongs to the next epidemiological
    year; an early-January date in week 52/53 to the previous one. SEM_PRI
    carries only the week, so the year comes from the same shifted-ISO
    identity that reproduces the week.
    """
    return (d + pd.Timedelta(days=1)).dt.isocalendar().year


INFLUENZA_A_SUBTIPOS = {
    "influenza_h1n1": ["1"],
    "influenza_h3n2": ["2"],
    "influenza_a_n_subtipavel": ["4"],
    "influenza_a_inconclusiva": ["5", "6"],
}
# Influenza B through PCR_FLUBLI: 1=Victoria, 2=Yamagata.
INFLUENZA_B_LINHAGENS = {"influenza_b_vict": ["1"], "influenza_b_yam": ["2"]}
# Two more influenza flags do not reduce to a PCR_FLUASU/PCR_FLUBLI value test
# and were missing from the first catalogue — which undercounted influenza by
# 2.1x (33,668 vs the Ministry's 71,808 over the six years):
#   influenza_a_n_sub  (MS line 474): PCR_FLUASU == 3 ("nao subtipado"), OR the
#     screening said Influenza A (TP_FLU_AN == 1 | TP_FLU_PCR == 1) and no
#     subtype flag fired. Value 3 was in no subtype set, and the TP_FLU_*
#     fallback is exactly the pair of columns NOT_CHECKBOXES names but the
#     first Silver never consumed.
#   influenza_b_inconclusivo (MS line 557): screening said Influenza B and
#     neither lineage flag fired.
# The PDF, recovered by the dictionary fix, reads PCR_FLUASU 5=Inconclusivo,
# 6=Outro; the reference script groups both as "inconclusiva" (MS line 441)
# and the catalogue follows the script.

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

    flu_an = df.get("TP_FLU_AN", pd.Series(dtype="string"))
    flu_pcr = df.get("TP_FLU_PCR", pd.Series(dtype="string"))
    triagem_a = ((flu_an == "1") | (flu_pcr == "1")).fillna(False)
    triagem_b = ((flu_an == "2") | (flu_pcr == "2")).fillna(False)
    subtipo_a = pd.concat([df[f"{n}_caso"] for n in INFLUENZA_A_SUBTIPOS], axis=1).any(
        axis=1
    )
    df["influenza_a_n_sub_caso"] = (
        df.get("PCR_FLUASU", pd.Series(dtype="string")) == "3"
    ).fillna(False) | (triagem_a & ~subtipo_a)
    df["influenza_b_inconclusivo_caso"] = triagem_b & ~pd.concat(
        [df[f"{n}_caso"] for n in INFLUENZA_B_LINHAGENS], axis=1
    ).any(axis=1)

    df["influenza_a_total_caso"] = subtipo_a | df["influenza_a_n_sub_caso"]
    df["influenza_b_total_caso"] = (
        pd.concat([df[f"{n}_caso"] for n in INFLUENZA_B_LINHAGENS], axis=1).any(axis=1)
        | df["influenza_b_inconclusivo_caso"]
    )
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


def report(df: pd.DataFrame) -> str:
    """Re-measure every adopted gate on a built frame and render the ladder.

    This is the self-check the module's docstring promises: each GATES entry
    carries the worst-year contradiction it was adopted under, and this
    function recomputes the number on the frame it is given. build() already
    refuses to run when a bound is broken; report() is the legible version,
    for notebooks to print.
    """
    lines = ["gate                                    tier   recorded   measured"]
    for child, (parent, values, tier, worst) in GATES.items():
        if child not in df or parent not in df:
            continue
        aplicavel = df[parent].isin(list(values))
        filled = int(df[child].notna().sum())
        contradiz = int((df[child].notna() & ~aplicavel).sum())
        pct = 100.0 * contradiz / filled if filled else 0.0
        lines.append(
            f"{child:<20} <= {parent:<12} in {'/'.join(values):<4} {tier:>3}"
            f"{worst:>9.2f}% {pct:>9.3f}%"
        )
    return "\n".join(lines)


def build(path: pathlib.Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """One year in, (silver, quarantine) out. Every input row is in exactly one."""
    # 418 columns are inserted one by one; pandas warns about fragmentation
    # at every insert past ~100. The frame is defragmented once, on return.
    warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

    raw = pq.read_table(path).to_pandas()
    n_in = len(raw)
    df = pd.DataFrame(index=raw.index)

    for c in raw.columns:
        df[c] = normalise(raw[c], c)

    quarantine_mask = find_shifted_rows(df)

    # --- dates ------------------------------------------------------------
    # The DT_ prefix finds the ISO dates; DMY_DATES adds the nine that hide
    # behind other prefixes (dose dates, VG_DTRES) or carry dd/mm/yyyy.
    date_cols = [c for c in df.columns if c.startswith("DT_") or c in DMY_DATES]
    for c in date_cols:
        df[c + "_d"] = parse_dates(df[c], c)

    # --- age: MS lines 269-276, minus the neonate rule (see DEVIATIONS) ----
    nasc, sin = df.get("DT_NASC_d"), df.get("DT_SIN_PRI_d")
    if nasc is not None and sin is not None:
        days = days_between(sin, nasc)
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

    # --- declared age: unit-aware, and the identity that checks it --------
    # COD_IDADE is TP_IDADE + zfill(NU_IDADE_N, 3) in 100.00% of rows; the 20
    # disagreements in 4.1M all have a negative NU_IDADE_N — a defect the
    # flag records and nothing repairs.
    if "TP_IDADE" in df and "NU_IDADE_N" in df:
        df["idade_unidade"] = df["TP_IDADE"].map({"1": "dia", "2": "mes", "3": "ano"})
        n = pd.to_numeric(df["NU_IDADE_N"], errors="coerce")
        df["idade_declarada_anos"] = np.select(
            [df["TP_IDADE"] == "1", df["TP_IDADE"] == "2", df["TP_IDADE"] == "3"],
            [n / 365.25, n / 12.0, n],
            default=np.nan,
        )
        if "COD_IDADE" in df:
            esperado = df["TP_IDADE"].fillna("") + n.astype("Int64").astype(
                "string"
            ).str.zfill(3).fillna("")
            df["cod_idade_consistente"] = df["COD_IDADE"].fillna("") == esperado

    # --- COVID vaccination: facts that cannot contradict ------------------
    # The PDF's gate on VACINA_COV is contradicted in 0.46% of dose cells in
    # 2021 (1,701 rows), above the G-rule bar, so no gate: two independent
    # facts instead, free to disagree because the data does.
    if "VACINA_COV" in df:
        df["vacina_covid_declarada"] = (df["VACINA_COV"] == "1").fillna(False)
    for c in [c for c in FAB_COLUMNS if c in df]:
        df[c + "_codigo"], df[c + "_fabricante"] = harmonise_fabricante(df[c])
    dose_d = [c + "_d" for c in DOSE_DATES if c + "_d" in df]
    if dose_d:
        df["n_doses_covid_registradas"] = df[dose_d].notna().sum(axis=1)
    if "DOSE_1_COV_d" in df:
        # Brazil's campaign started 2021-01-17; earlier first doses exist and
        # stay — flagged, never repaired.
        df["dose_1_covid_antes_campanha"] = (
            df["DOSE_1_COV_d"] < pd.Timestamp("2021-01-17")
        ).fillna(False)

    # --- symptom counts over the thirteen coded symptom fields ------------
    sint = [c for c in SINTOMAS if c in df]
    if sint:
        quadro = pd.concat([df[c] for c in sint], axis=1)
        df["n_sintomas_marcados"] = (quadro == "1").sum(axis=1)
        df["n_sintomas_ignorados"] = (quadro == "9").sum(axis=1)
        df["n_sintomas_ausentes"] = quadro.isna().sum(axis=1)

    # --- stays: both inherit the leakage class of their inputs ------------
    if "DT_ENTUTI_d" in df and "DT_SAIDUTI_d" in df:
        df["dias_uti"] = days_between(df["DT_SAIDUTI_d"], df["DT_ENTUTI_d"])
    if "DT_INTERNA_d" in df and "DT_SIN_PRI_d" in df:
        df["dias_ate_internacao"] = days_between(df["DT_INTERNA_d"], df["DT_SIN_PRI_d"])

    # --- geographic referential: the pinned IBGE table --------------------
    # The DF is one IBGE municipality (Brasília), but SIVEP records its
    # administrative regions under DATASUS pseudo-codes (530040 Ceilândia,
    # 530140 Samambaia, …) that IBGE does not carry — 9,690 rows in 2023
    # alone. Calling those invalid would be wrong, so the fact splits in two:
    # membership in the IBGE table, and the DF pseudo-code case, named.
    codigos6 = _ibge_codigos6()
    for col, nome in [
        ("CO_MUN_NOT", "municipio_notif_valido"),
        ("CO_MUN_RES", "municipio_resid_valido"),
        ("CO_MU_INTE", "municipio_inte_valido"),
    ]:
        if col in df:
            no_ibge = df[col].isin(codigos6)
            df[nome] = no_ibge.astype("boolean").mask(df[col].isna())
            df[nome.replace("_valido", "_df_ra")] = (
                (~no_ibge & df[col].str.startswith("53"))
                .astype("boolean")
                .mask(df[col].isna())
            )
    if "CO_MUN_RES" in df and "SG_UF" in df:
        df["uf_resid_coerente"] = (
            (df["CO_MUN_RES"].str[:2] == df["SG_UF"].map(UF_CODES))
            .astype("boolean")
            .mask(df["CO_MUN_RES"].isna() | df["SG_UF"].isna())
        )

    # --- laboratory checkboxes: official domain is {1, blank} -------------
    for c in [c for c in CHECKBOXES if c in df]:
        df[c + "_marcado"] = (df[c] == "1").fillna(False)

    # --- missing states: every confirmed gate, plus the ungated symptoms --
    # GATES holds the enabling predicates the data confirms; each application
    # re-measures the contradiction and refuses to run when the recorded
    # bound is broken — a gate adopted once and never re-measured is the
    # one-year-assertion failure mode all over again.
    if COMORBIDITY_GATE in df:
        df["fator_risco_declarado"] = df[COMORBIDITY_GATE].isin(["1", "S"])
    for child, (parent, values, tier, worst) in GATES.items():
        if child not in df or parent not in df:
            continue
        aplicavel = df[parent].isin(list(values))
        filled = int(df[child].notna().sum())
        contradiz = int((df[child].notna() & ~aplicavel).sum())
        pct = 100.0 * contradiz / filled if filled else 0.0
        if pct > max(worst, 0.05) + 0.005:
            raise ValueError(
                f"gate {child} <= {parent} in {sorted(values)} broke its recorded "
                f"bound: {pct:.3f}% contradiction (tier {tier}, recorded {worst}%). "
                f"Re-measure before trusting this Silver."
            )
        df[child + "_estado"] = missing_state(df[child], aplicavel)
    for c in [c for c in SINTOMAS if c in df]:
        # no gate passes the G-rule for the symptom block: a blank is really
        # absent (or, for the four 2020-era symptoms, the form's year — see
        # YEAR_GATED and the notebooks)
        df[c + "_estado"] = missing_state(df[c], pd.Series(True, index=df.index))

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
        df["se_primeiro_sinto"] = epiweek(df["DT_SIN_PRI_d"])
        df["ano_epi_primeiro_sinto"] = epiyear(df["DT_SIN_PRI_d"])
    if "DT_NOTIFIC_d" in df:
        df["se_notificacao"] = epiweek(df["DT_NOTIFIC_d"])
        df["ano_epi_notificacao"] = epiyear(df["DT_NOTIFIC_d"])

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
    # Toda coluna derivada tem de estar no catálogo — uma coluna nova sem
    # label de definição quebra o build, igual a uma crua sem regra.
    extras = set(silver.columns) - ALL_COLUMNS
    catalogo = set(derived_catalogue())
    sem_label = sorted(extras - catalogo)
    sem_coluna = sorted(catalogo - extras)
    if sem_label or sem_coluna:
        raise ValueError(
            f"derivadas fora do catálogo: sem label={sem_label} "
            f"catalogadas mas não criadas={sem_coluna}"
        )

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
