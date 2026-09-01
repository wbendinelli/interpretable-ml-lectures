"""Silver → Gold: the modeling table, every decision an explicit flag.

Usage:
    python3 tools/srag_gold.py \\
        --silver ~/Documents/srag-data/silver \\
        --out    ~/Documents/srag-data/gold \\
        --coorte hospitalizado --etiologia covid-amplo \\
        --alvo obito-casos-fechados --inicio 2020-02-26 \\
        --idade todas --idade-maxima 120 --idade-ausente excluir \\
        --nosocomial manter --split temporal:2022-12-31/2023/2024 \\
        --amostra-treino 200000 --semente 42

    python3 tools/srag_gold.py --check-manifest    # MANIFEST.md em dia?

The Silver states facts; the Gold makes task choices — and this tool
refuses to make one silently: every decision is a REQUIRED flag with no
default, running it bare prints the menu (GOLD.md) and exits 2, and the
same frozen `Decisions` object drives both the build and the committed
manifest, so a choice cannot be applied without being written down.

Two hard rules, both bought with this repository's own mistakes:

* The single Silver is 4.1M × 420 — never `read_table` it whole. Batches
  only (`iter_batches`), filtered to the cohort before concatenating.
* Nullable booleans: `.astype(int)` raises on NA and `.mean()` silently
  drops NA from the denominator. `bool_feature(s, na=...)` makes the fill
  decision mandatory at every call site, and the manifest prints how many
  NA each fill absorbed.

Committed outputs (modules/00-dataset/gold/): counts.json and
MANIFEST.md — the manifest is a pure function of counts.json + Decisions
(no timestamps; the extraction tag 26-06-2025 stands in for a build
date), so the `gold-manifest-generated` pre-commit hook can re-render and
diff it exactly like COLUMNS.md.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import hashlib
import json
import pathlib
import sys

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import srag_silver as S

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOLD_DIR = ROOT / "modules/00-dataset/gold"
COUNTS_JSON = GOLD_DIR / "counts.json"
MANIFEST_MD = GOLD_DIR / "MANIFEST.md"
EXTRACAO = "26-06-2025"  # the frozen re-export the whole module is built on

# --------------------------------------------------------------------------
# The 27 capitals. This lives here, not in srag_silver: "is this
# municipality a capital" is a modeling recode, not a fact about the
# record — the same test the medallion doc states. Checked at import
# against the pinned IBGE table; a typo refuses to run.
# --------------------------------------------------------------------------
CAPITAIS: dict[str, str] = {
    "AC": "120040",  # Rio Branco
    "AL": "270430",  # Maceió
    "AM": "130260",  # Manaus
    "AP": "160030",  # Macapá
    "BA": "292740",  # Salvador
    "CE": "230440",  # Fortaleza
    "DF": "530010",  # Brasília
    "ES": "320530",  # Vitória
    "GO": "520870",  # Goiânia
    "MA": "211130",  # São Luís
    "MG": "310620",  # Belo Horizonte
    "MS": "500270",  # Campo Grande
    "MT": "510340",  # Cuiabá
    "PA": "150140",  # Belém
    "PB": "250750",  # João Pessoa
    "PE": "261160",  # Recife
    "PI": "221100",  # Teresina
    "PR": "410690",  # Curitiba
    "RJ": "330455",  # Rio de Janeiro
    "RN": "240810",  # Natal
    "RO": "110020",  # Porto Velho
    "RR": "140010",  # Boa Vista
    "RS": "431490",  # Porto Alegre
    "SC": "420540",  # Florianópolis
    "SE": "280030",  # Aracaju
    "SP": "355030",  # São Paulo
    "TO": "172100",  # Palmas
}


def _check_capitais() -> None:
    tabela = {}
    with (ROOT / "modules/00-dataset/reference/municipios_ibge.csv").open(
        encoding="utf-8"
    ) as f:
        for r in csv.DictReader(f):
            tabela[r["codigo6"]] = r["uf"]
    errados = {uf: cod for uf, cod in CAPITAIS.items() if tabela.get(cod) != uf}
    if errados:
        raise ValueError(f"CAPITAIS contradiz a tabela IBGE pinada: {errados}")


_check_capitais()

CAMPANHA = pd.Timestamp("2021-01-17")  # first CoronaVac dose in Brazil

DOSE_D = [c + "_d" for c in S.DOSE_DATES]

# Every Silver column the Gold reads. Batches project exactly this.
NEEDED = [
    "NU_NOTIFIC",
    "DT_SIN_PRI_d",
    "EVOLUCAO",
    "coorte_hospitalizado",
    "covid_caso",
    "PCR_SARS2_marcado",
    "idade_anos",
    "CS_SEXO",
    "CS_RACA",
    "CS_ESCOL_N",
    "CS_ZONA",
    "CS_GESTANT",
    *S.COMORBIDITIES,
    *S.SINTOMAS,
    *DOSE_D,
    "vacina_covid_declarada",
    "se_primeiro_sinto",
    "regiao",
    "CO_MUN_RES",
    "municipio_resid_df_ra",
    "codeteccao_casos",
    "NOSOCOMIAL",
    "fator_risco_declarado",
    "RAIOX_RES",
    "TOMO_RES",
]

ROTULOS_RACA = {
    "1": "branca",
    "2": "preta",
    "3": "amarela",
    "4": "parda",
    "5": "indigena",
}
ROTULOS_ESCOLA = {
    "0": "sem_escolaridade",
    "1": "fundamental_1",
    "2": "fundamental_2",
    "3": "medio",
    "4": "superior",
    "5": "nao_se_aplica",
}
ROTULOS_ZONA = {"1": "urbana", "2": "rural", "3": "periurbana"}
ROTULOS_GESTANT = {
    "1": "1_trimestre",
    "2": "2_trimestre",
    "3": "3_trimestre",
    "4": "idade_gestacional_ignorada",
    "5": "nao",
    "6": "nao_se_aplica",
}
ROTULOS_SEXO = {"M": "masculino", "F": "feminino", "I": "ignorado"}


@dataclasses.dataclass(frozen=True)
class Decisions:
    """Every task choice, frozen. The single source for build AND manifest."""

    coorte: str
    etiologia: str
    alvo: str
    inicio: pd.Timestamp
    idade: str
    idade_maxima: float
    idade_ausente: str
    nosocomial: str
    split: str
    amostra_treino: int
    semente: int

    @property
    def split_bounds(self) -> tuple[pd.Timestamp, int, int]:
        # "temporal:2022-12-31/2023/2024"
        kind, resto = self.split.split(":", 1)
        if kind != "temporal":
            raise ValueError(f"split não suportado: {self.split}")
        corte, val, teste = resto.split("/")
        return pd.Timestamp(corte), int(val), int(teste)


def bool_feature(s: pd.Series, *, na: bool) -> tuple[np.ndarray, int]:
    """Nullable boolean → plain bool, with the NA decision written down.

    Returns (values, how_many_NA_the_fill_absorbed) — the manifest prints
    the second number, so a fill can never be silent.
    """
    n_na = int(s.isna().sum())
    return s.fillna(na).astype(bool).to_numpy(), n_na


def _cat(s: pd.Series, rotulos: dict[str, str]) -> pd.Series:
    out = s.map(rotulos)
    out[out.isna()] = "desconhecido"
    return out.astype("category")


def _tres_estados(s: pd.Series) -> pd.Series:
    """sim / nao / desconhecido — the modeling fold of the three
    missing-states, declared in the manifest and undone where it matters
    via the fator_risc_portao diagnostic column."""
    out = pd.Series("desconhecido", index=s.index, dtype="object")
    out[s == "1"] = "sim"
    out[s == "2"] = "nao"
    return out.astype("category")


def cohort_funnel(
    df: pd.DataFrame, d: Decisions
) -> tuple[pd.DataFrame, list[tuple[str, int]]]:
    """Apply the filters in the stated order; the counts do not commute."""
    passos: list[tuple[str, int]] = [("prata (sem linhas deslocadas)", len(df))]

    df = df[df["coorte_hospitalizado"].fillna(False)]
    passos.append(("coorte_hospitalizado", len(df)))

    df = df[df["covid_caso"].fillna(False)]
    passos.append(("covid_caso (definição ampla)", len(df)))

    df = df[df["EVOLUCAO"].isin(["1", "2"])]
    passos.append(("casos fechados (EVOLUCAO 1 ou 2)", len(df)))

    df = df[df["DT_SIN_PRI_d"] >= d.inicio]
    passos.append((f"DT_SIN_PRI >= {d.inicio.date()}", len(df)))

    if d.idade_ausente == "excluir":
        df = df[df["idade_anos"].notna()]
        passos.append(("idade presente", len(df)))
    df = df[df["idade_anos"] <= d.idade_maxima]
    passos.append((f"idade <= {d.idade_maxima:g}", len(df)))

    return df.copy(), passos


def build_features(
    df: pd.DataFrame, d: Decisions
) -> tuple[pd.DataFrame, dict[str, int]]:
    g = pd.DataFrame(index=df.index)
    na_fills: dict[str, int] = {}

    # --- demografia --------------------------------------------------------
    g["idade_anos"] = df["idade_anos"].astype("float32")
    g["cs_sexo"] = _cat(df["CS_SEXO"], ROTULOS_SEXO)
    g["cs_raca"] = _cat(df["CS_RACA"], ROTULOS_RACA)
    g["cs_escol_n"] = _cat(df["CS_ESCOL_N"], ROTULOS_ESCOLA)
    g["cs_zona"] = _cat(df["CS_ZONA"], ROTULOS_ZONA)
    g["cs_gestant"] = _cat(df["CS_GESTANT"], ROTULOS_GESTANT)

    # --- comorbidades e sintomas: o fold declarado -------------------------
    for c in S.COMORBIDITIES:
        g[c.lower()] = _tres_estados(df[c])
    for c in S.SINTOMAS:
        g[c.lower()] = _tres_estados(df[c])

    # --- vacinação ---------------------------------------------------------
    onset = df["DT_SIN_PRI_d"]
    doses = pd.concat([(df[c].notna() & (df[c] < onset)) for c in DOSE_D], axis=1)
    g["n_doses_antes_do_sintoma"] = doses.sum(axis=1).astype("int8")
    vals, na = bool_feature(df["vacina_covid_declarada"], na=False)
    g["vacina_covid_declarada"] = vals
    na_fills["vacina_covid_declarada"] = na

    # --- tempo -------------------------------------------------------------
    g["meses_desde_mar2020"] = (
        (onset - pd.Timestamp("2020-03-01")).dt.days / 30.44
    ).astype("float32")
    g["semana_epi"] = df["se_primeiro_sinto"].astype("int8")

    # --- geografia ---------------------------------------------------------
    regiao = df["regiao"].copy()
    regiao[regiao.isna()] = "desconhecido"
    g["regiao"] = regiao.astype("category")
    capitais = frozenset(CAPITAIS.values())
    cap = pd.Series("desconhecido", index=df.index, dtype="object")
    tem_mun = df["CO_MUN_RES"].notna()
    cap[tem_mun] = "interior"
    cap[df["CO_MUN_RES"].isin(capitais)] = "capital"
    # As regiões administrativas do DF (pseudo-códigos DATASUS) são a área
    # urbana da capital — julgamento registrado no manifesto, contado.
    df_ra = df["municipio_resid_df_ra"].fillna(False)
    cap[df_ra.astype(bool)] = "capital"
    g["capital_interior"] = cap.astype("category")
    na_fills["capital_interior (RAs do DF → capital)"] = int(df_ra.sum())

    # --- clínica de admissão ----------------------------------------------
    vals, na = bool_feature(df["codeteccao_casos"], na=False)
    g["coinfeccao_outro_virus"] = vals
    na_fills["coinfeccao_outro_virus"] = na
    noso = pd.Series("desconhecido", index=df.index, dtype="object")
    noso[df["NOSOCOMIAL"] == "1"] = "sim"
    noso[df["NOSOCOMIAL"] == "2"] = "nao"
    noso[df["NOSOCOMIAL"] == "9"] = "ignorado"
    g["nosocomial"] = noso.astype("category")

    # --- alvo, split, escrituração ----------------------------------------
    g["y_obito"] = (df["EVOLUCAO"] == "2").astype("int8")
    corte, ano_val, ano_teste = d.split_bounds
    split = pd.Series("train", index=df.index, dtype="object")
    split[onset.dt.year == ano_val] = "val"
    split[onset.dt.year == ano_teste] = "test"
    assert bool((onset[split == "train"] <= corte).all())
    g["split"] = split.astype("category")
    vals, na = bool_feature(df["PCR_SARS2_marcado"], na=False)
    g["rt_pcr_confirmado"] = vals
    na_fills["rt_pcr_confirmado"] = na
    g["ano_onset"] = onset.dt.year.astype("int16")

    # --- diagnósticos: nunca features --------------------------------------
    vals, na = bool_feature(df["fator_risco_declarado"], na=False)
    g["fator_risc_portao"] = vals
    na_fills["fator_risc_portao"] = na
    for c in ("RAIOX_RES", "TOMO_RES"):
        v = df[c].copy()
        v[v.isna()] = "desconhecido"
        g[c.lower()] = v.astype("category")

    # comparação em dtype `string` devolve booleano ANULÁVEL — o fill é
    # explícito, senão o astype levanta no NA (a armadilha de sempre)
    def _is1(c: str) -> pd.Series:
        return (df[c] == "1").fillna(False).astype("int8")

    g["n_crit2"] = _is1("TOSSE") + _is1("GARGANTA")
    g["n_crit3"] = _is1("DISPNEIA") + _is1("SATURACAO") + _is1("DESC_RESP")
    return g, na_fills


def _iter_silver(silver: pathlib.Path):
    """Batches of NEEDED columns, whether Silver is the single parquet or
    the per-year directory — never the whole table at once."""
    if silver.is_dir():
        for f in sorted(silver.glob("silver_*.parquet")):
            yield pq.read_table(f, columns=NEEDED).to_pandas()
    else:
        pf = pq.ParquetFile(silver)
        cols = NEEDED + (
            ["linha_deslocada"] if "linha_deslocada" in pf.schema_arrow.names else []
        )
        for batch in pf.iter_batches(columns=cols, batch_size=250_000):
            df = batch.to_pandas()
            if "linha_deslocada" in df:
                df = df[~df["linha_deslocada"].fillna(False)]
                df = df.drop(columns=["linha_deslocada"])
            yield df


def build_gold(
    silver: pathlib.Path | list[pd.DataFrame], d: Decisions
) -> tuple[pd.DataFrame, dict]:
    frames = _iter_silver(silver) if isinstance(silver, pathlib.Path) else iter(silver)

    partes: list[pd.DataFrame] = []
    funil_total: dict[str, int] = {}
    na_total: dict[str, int] = {}
    for df in frames:
        recorte, passos = cohort_funnel(df, d)
        for nome, n in passos:
            funil_total[nome] = funil_total.get(nome, 0) + n
        if len(recorte) == 0:
            continue
        feats, na_fills = build_features(recorte, d)
        feats["NU_NOTIFIC"] = recorte["NU_NOTIFIC"].to_numpy()
        for k, v in na_fills.items():
            na_total[k] = na_total.get(k, 0) + v
        partes.append(feats)
        del df, recorte, feats

    gold = pd.concat(partes, ignore_index=True)
    gold = gold.sort_values(
        ["ano_onset", "NU_NOTIFIC"], kind="stable", ignore_index=True
    )
    gold["gold_id"] = np.arange(len(gold), dtype="int32")
    gold = gold.drop(columns=["NU_NOTIFIC"])

    splits = {
        s: {
            "n": int((gold["split"] == s).sum()),
            "obitos": int(gold.loc[gold["split"] == s, "y_obito"].sum()),
        }
        for s in ("train", "val", "test")
    }
    for v in splits.values():
        v["letalidade_pct"] = round(100 * v["obitos"] / v["n"], 1)

    counts = {
        "extracao": EXTRACAO,
        "decisoes": {
            k: (str(v) if isinstance(v, pd.Timestamp) else v)
            for k, v in dataclasses.asdict(d).items()
        },
        "funil": [[nome, n] for nome, n in funil_total.items()],
        "n_gold": len(gold),
        "obitos": int(gold["y_obito"].sum()),
        "letalidade_pct": round(100 * float(gold["y_obito"].mean()), 2),
        "splits": splits,
        "na_absorvidos": na_total,
        "rt_pcr_confirmado": int(gold["rt_pcr_confirmado"].sum()),
        "features": {c: str(gold[c].dtype) for c in gold.columns},
    }
    return gold, counts


# --------------------------------------------------------------------------
# The manifest: a pure function of counts + decisions. No timestamps, no
# hash-ordered dicts — hook-checkable byte for byte.
# --------------------------------------------------------------------------
FEATURES_MODELO = 40  # asserted in render_manifest


def render_manifest(counts: dict) -> str:
    d = counts["decisoes"]
    fun = counts["funil"]
    L = [
        "# O Ouro — gold_covid_obito",
        "",
        "Gerado por `tools/srag_gold.py` a partir do Prata (banco congelado de",
        f"{counts['extracao']}). Não editar à mão: este texto é função pura de",
        "`counts.json` + das decisões, e o hook `gold-manifest-generated`",
        "re-renderiza e compara.",
        "",
        "O Prata afirma fatos; aqui ficam as **escolhas de tarefa**, cada uma",
        "com dono, data e a evidência que a sustenta. O cardápio de onde elas",
        "vieram é o [GOLD.md](../GOLD.md).",
        "",
        "## 1. O funil, na ordem em que os filtros correm",
        "",
        "A ordem importa: as contagens abaixo não comutam.",
        "",
        "| # | Filtro | Restam | Saem |",
        "|--:|---|---:|---:|",
    ]
    anterior = None
    for i, (nome, n) in enumerate(fun):
        saem = "—" if anterior is None else f"{anterior - n:,}".replace(",", ".")
        L.append(f"| {i} | {nome} | {n:,} | {saem} |".replace(",", "."))
        anterior = n
    L += [
        "",
        "Das 7 linhas em quarentena, **0** satisfariam coorte ∧ COVID — o",
        "descarte não esconde caso nenhum (medido no desenho, 2026-09-01).",
        "",
        "## 2. As decisões, uma a uma",
        "",
        "### 2.1 Alvo — óbito nos casos fechados",
        "`y_obito = (EVOLUCAO == 2)`, exigido `EVOLUCAO ∈ {1,2}` no funil.",
        "**Decidido 2026-09-01 — William.** Os registros que nunca fecham saem",
        'do Ouro (contados no funil) e a censura difere por ano — "casos',
        'fechados" já é uma escolha de coorte, dita aqui. `EVOLUCAO` e as 39',
        "derivadas de classe `leakage` nunca entram como feature → COLUMNS.md.",
        "",
        "### 2.2 Coorte — hospitalizado ∧ COVID (definição ampla)",
        "`coorte_hospitalizado` usa HOSPITAL = 1 sem o `∨ EVOLUCAO = 2` oficial",
        "(a definição oficial admite 24.475 linhas *porque o paciente morreu*",
        "→ DEVIATIONS). `covid_caso` é a definição ampla; quem quiser o recorte",
        f"estrito tem `rt_pcr_confirmado` = {counts['rt_pcr_confirmado']:,} registros.".replace(
            ",", "."
        ),
        "**Decidido 2026-09-01 — William.** (A contagem da coorte difere em 1",
        "do internals §7, que mede o Bronze pré-quarentena: a linha deslocada",
        "de 2023 satisfazia o critério com os campos fora do lugar.)",
        "",
        "### 2.3 Janela — a partir de " + d["inicio"][:10],
        "Primeiro caso confirmado no Brasil (26/02/2020, MS). **Não existe",
        "corte oficial** — o script do Ministério não filtra por data (lido",
        "linha a linha); o evento Fiocruz que se costuma lembrar é o InfoGripe",
        "passando a incluir COVID no boletim na SE 15 (21/04/2020), anotado",
        "aqui como referência, não usado como filtro.",
        "**Decidido 2026-09-01 — William.**",
        "",
        "### 2.4 Split temporal",
        f"`{d['split']}` por DT_SIN_PRI. **Decidido 2026-09-01 — William.**",
        "",
        "| split | n | óbitos | letalidade |",
        "|---|---:|---:|---:|",
    ]
    for s in ("train", "val", "test"):
        v = counts["splits"][s]
        L.append(
            f"| {s} | {v['n']:,} | {v['obitos']:,} | {v['letalidade_pct']}% |".replace(
                ",", "."
            )
        )
    L += [
        "",
        "Os conjuntos de avaliação são pequenos e completos: a assimetria é",
        "consequência da epidemia, não do desenho, e a letalidade cai quase à",
        "metade na fronteira do split — o achado central que os módulos 01–05",
        "explicam, não um incômodo a corrigir.",
        "",
        "### 2.5 Features — 40 colunas de modelo",
        "",
        "| Coluna | dtype |",
        "|---|---|",
    ]
    escrituracao = {
        "y_obito",
        "split",
        "rt_pcr_confirmado",
        "gold_id",
        "ano_onset",
        "fator_risc_portao",
        "raiox_res",
        "tomo_res",
        "n_crit2",
        "n_crit3",
    }
    n_feats = 0
    for c, t in counts["features"].items():
        if c in escrituracao:
            continue
        n_feats += 1
        L.append(f"| `{c}` | {t} |")
    assert n_feats == FEATURES_MODELO, (
        f"{n_feats} features de modelo, esperava {FEATURES_MODELO}"
    )
    L += [
        "",
        f"E {len(escrituracao)} colunas de escrituração/diagnóstico que **nunca**",
        "entram no X: `y_obito`, `split`, `rt_pcr_confirmado`, `gold_id`,",
        "`ano_onset`, `fator_risc_portao`, `raiox_res`, `tomo_res`, `n_crit2`,",
        "`n_crit3`.",
        "",
        "**O que a codificação funde, e por quê.** `desconhecido` =",
        "`nao_aplicavel` ∪ `ausente` ∪ `ignorado`. O módulo 00 mede que esses",
        "vazios são coisas diferentes — e mesmo assim o Ouro os funde: três",
        "níveis por variável são legíveis, cinco × 26 variáveis não. A",
        "compressão é declarada aqui e **desfeita onde importa**:",
        "`fator_risc_portao` viaja no Ouro exatamente para que os módulos",
        "possam contar perturbações que contradizem o portão.",
        "",
        "NA absorvidos por cada fill booleano (a decisão nunca é silenciosa):",
        "",
        "| Fill | NA absorvidos |",
        "|---|---:|",
    ]
    for k in sorted(counts["na_absorvidos"]):
        L.append(f"| {k} | {counts['na_absorvidos'][k]:,} |".replace(",", "."))
    L += [
        "",
        "### 2.6 Exclusões",
        "Classes `leakage`, `identifier`, `free_text` e o lado-nome dos",
        "`code_pair` — lista **gerada** de COLUMNS.md, nunca digitada. Imagem",
        "(`RAIOX_RES`/`TOMO_RES`) fica fora das features e viaja como",
        "diagnóstico: a célula-armadilha do notebook do modelo mede o que o",
        "modelo teria aprendido. **Decidido 2026-09-01 — William**, com a",
        "explicação registrada (modelo não zera proxy; e o medido é invertido:",
        "a ausência do registro é que prediz óbito).",
        "",
        "### 2.7 Sem pesos de classe",
        f"Letalidade global de {counts['letalidade_pct']}% não é",
        "desbalanceamento extremo, e reponderar destruiria a história de",
        "calibração que a mudança de regime torna interessante.",
        "",
        "### 2.8 Decisões que o cardápio não previu",
        "",
        "| Questão | Decisão |",
        "|---|---|",
        "| `NOSOCOMIAL` vazio (14,5% da coorte) | quarto nível `desconhecido`, não fundido no 9 |",
        f"| idade ausente | {d['idade_ausente']} (idade é a feature dominante) |",
        f"| idade > {float(d['idade_maxima']):g} anos | excluídas |",
        "| regiões administrativas do DF | contam como `capital` (área urbana da capital; contagem em §2.5) |",
        "| semana epidemiológica | ordinal 1–53; sin/cos só dentro do pipeline logístico |",
        "",
        "## 3. Procedência e limites",
        "",
        f"Coorte final: **{counts['n_gold']:,} internações**, ".replace(",", ".")
        + f"{counts['obitos']:,} óbitos ({counts['letalidade_pct']}%).".replace(
            ",", "."
        ),
        "Prata → COLUMNS.md · qualidade → QUALITY.md (84 checagens) · validação",
        "externa → srag_infogripe_validation (0,9997 em 2019).",
        "Este Ouro **não** trata: `DT_EVOLUCA > DT_ENCERRA` em escala, as datas",
        "de 2020 fora de [1900, 2030], a inconsistência resultado↔checkbox",
        "(9–20% ao ano). Nenhuma toca as 40 features → walkthrough §7.",
    ]
    return "\n".join(L).rstrip("\n") + "\n"


def sha256_amostra(g: pd.DataFrame) -> str:
    """Content hash of a canonical CSV projection — parquet bytes are not
    stable across pyarrow versions, so bytes are never compared."""
    proj = g[sorted(g.columns)].copy()
    for c in proj.columns:
        if proj[c].dtype == "float32":
            proj[c] = proj[c].round(4)
    return hashlib.sha256(
        proj.to_csv(index=False, float_format="%.4f").encode()
    ).hexdigest()


def main(argv: list[str]) -> int:
    if "--check-manifest" in argv:
        counts = json.loads(COUNTS_JSON.read_text(encoding="utf-8"))
        atual = MANIFEST_MD.read_text(encoding="utf-8") if MANIFEST_MD.exists() else ""
        esperado = render_manifest(counts)
        if atual != esperado:
            print("MANIFEST.md divergiu de counts.json + decisões", file=sys.stderr)
            return 1
        print("MANIFEST.md em dia")
        return 0

    ap = argparse.ArgumentParser(
        description="Silver → Gold. Toda decisão é flag obrigatória; rodar sem "
        "flags imprime o cardápio (GOLD.md) e sai 2."
    )
    ap.add_argument("--silver", required=True, type=pathlib.Path)
    ap.add_argument("--out", required=True, type=pathlib.Path)
    for flag in (
        "coorte",
        "etiologia",
        "alvo",
        "idade",
        "idade-ausente",
        "nosocomial",
        "split",
    ):
        ap.add_argument(f"--{flag}", required=True)
    ap.add_argument("--inicio", required=True)
    ap.add_argument("--idade-maxima", required=True, type=float)
    ap.add_argument("--amostra-treino", required=True, type=int)
    ap.add_argument("--semente", required=True, type=int)
    if not argv:
        print((ROOT / "modules/00-dataset/GOLD.md").read_text(encoding="utf-8"))
        return 2
    args = ap.parse_args(argv)

    d = Decisions(
        coorte=args.coorte,
        etiologia=args.etiologia,
        alvo=args.alvo,
        inicio=pd.Timestamp(args.inicio),
        idade=args.idade,
        idade_maxima=args.idade_maxima,
        idade_ausente=args.idade_ausente,
        nosocomial=args.nosocomial,
        split=args.split,
        amostra_treino=args.amostra_treino,
        semente=args.semente,
    )
    gold, counts = build_gold(args.silver, d)

    args.out.mkdir(parents=True, exist_ok=True)
    destino = args.out / "gold_covid_obito.parquet"
    gold.to_parquet(destino, compression="zstd", index=False)

    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    COUNTS_JSON.write_text(
        json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    # renderizar do JSON canônico (sort_keys), nunca do dict em memória —
    # senão a geração usa ordem de inserção e o --check, ordem alfabética
    canonico = json.loads(COUNTS_JSON.read_text(encoding="utf-8"))
    MANIFEST_MD.write_text(render_manifest(canonico), encoding="utf-8")

    print("funil:")
    for nome, n in counts["funil"]:
        print(f"  {nome:<38} {n:>11,}".replace(",", "."))
    print(
        f"\nOuro: {len(gold):,} × {len(gold.columns)}  →  {destino}".replace(",", ".")
    )
    print(
        f"óbitos: {counts['obitos']:,} ({counts['letalidade_pct']}%)".replace(",", ".")
    )
    for s, v in counts["splits"].items():
        print(f"  {s:<6} {v['n']:>11,}  CFR {v['letalidade_pct']}%".replace(",", "."))
    print(f"manifesto: {MANIFEST_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
