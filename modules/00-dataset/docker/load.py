#!/usr/bin/env python3
"""Load the SRAG parquet files into the local Postgres — Bronze, Prata e Ouro.

Bronze means raw: every column lands as text, exactly as published, with no
coercion, no renaming and no rows dropped. Typing and recoding belong to
Silver, where each decision is recorded rather than assumed. Gold is the
modeling table, and it travels with its own dictionary — quem abre o
Metabase lê o que cada coluna significa sem abrir o repositório.

DuckDB does the transfer — it reads parquet natively and writes to Postgres
through its `postgres` extension, so there is no CSV round-trip.

As tabelas, por esquema:

    bronze.srag_2019 … bronze.srag_2024   uma por ano, tudo VARCHAR
    bronze.srag                           a view de união, com a coluna `ano`
    silver.srag                           o Prata inteiro, uma tabela só
    silver.contrato                       as 420 colunas documentadas
    gold.covid_obito                      o Ouro completo (parquet privado)
    gold.amostra                          a amostra commitada, 240.290 × 50
    gold.dicionario                       as 50 colunas do Ouro, uma por linha
    gold.funil                            os passos do funil da coorte
    gold.decisoes                         as decisões de tarefa, chave/valor
    gold.modelo                           XGBoost e logística em val e test
    gold.exemplar                         os dois pacientes-exemplo
    gold.xgb_params                       os hiperparâmetros do estudo
    gold.impossibilidades                 as restrições e a fração que violam

    docker compose up -d
    python3 modules/00-dataset/docker/load.py [data_dir] [--only-gold]

Re-running replaces the tables, so it is safe to repeat — e uma faxina no
começo derruba o que versões antigas do loader deixaram para trás (as
tabelas por ano `silver.srag_20xx` e `silver.quarentena_20xx`, que a
tabela única aposentou). O Bronze continua por ano mais a view de união.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import sys

import duckdb

# Tudo que pode existir em `silver` e `gold`. O que estiver fora desta
# lista é resto de uma versão antiga do loader e é derrubado na faxina.
# O Bronze fica de fora de propósito: lá as tabelas anuais são o desenho.
PERMITIDAS: frozenset[tuple[str, str]] = frozenset(
    {
        ("silver", "srag"),
        ("silver", "contrato"),
        ("gold", "covid_obito"),
        ("gold", "amostra"),
        ("gold", "dicionario"),
        ("gold", "funil"),
        ("gold", "decisoes"),
        ("gold", "modelo"),
        ("gold", "exemplar"),
        ("gold", "xgb_params"),
        ("gold", "impossibilidades"),
    }
)

# O papel de cada coluna do Ouro que NÃO é feature (MANIFEST §2.5).
PAPEL_NAO_FEATURE: dict[str, str] = {
    "y_obito": "alvo",
    "split": "escrituração",
    "gold_id": "escrituração",
    "ano_onset": "escrituração",
    "rt_pcr_confirmado": "escrituração",
    "fator_risc_portao": "diagnóstico",
    "raiox_res": "diagnóstico",
    "tomo_res": "diagnóstico",
    "n_crit2": "diagnóstico",
    "n_crit3": "diagnóstico",
}

# De onde a coluna veio, quando não é o campo SIVEP de mesmo nome.
ORIGEM: dict[str, str] = {
    "idade_anos": "idade_anos",
    "n_doses_antes_do_sintoma": "DOSE_1_COV_d … DOS_RE_BI_d",
    "meses_desde_mar2020": "DT_SIN_PRI_d",
    "semana_epi": "se_primeiro_sinto",
    "vacina_covid_declarada": "vacina_covid_declarada",
    "coinfeccao_outro_virus": "codeteccao_casos",
    "regiao": "regiao",
    "capital_interior": "CO_MUN_RES + municipio_resid_df_ra",
    "y_obito": "EVOLUCAO",
    "split": "DT_SIN_PRI_d",
    "rt_pcr_confirmado": "PCR_SARS2_marcado",
    "gold_id": "ordem estável (ano_onset, NU_NOTIFIC)",
    "ano_onset": "DT_SIN_PRI_d",
    "fator_risc_portao": "fator_risco_declarado",
    "n_crit2": "TOSSE + GARGANTA",
    "n_crit3": "DISPNEIA + SATURACAO + DESC_RESP",
}

# A definição em português das colunas que não vêm do catálogo de
# derivadas do Prata e não são o fold de três estados. Cada frase sai do
# MANIFEST.md ou do GOLD.md — este arquivo não inventa política.
DEFINICAO: dict[str, str] = {
    "cs_sexo": "CS_SEXO rotulada (ROTULOS_SEXO); código fora do domínio vira desconhecido.",
    "cs_raca": "CS_RACA rotulada (ROTULOS_RACA); código fora do domínio vira desconhecido.",
    "cs_escol_n": (
        "CS_ESCOL_N rotulada (ROTULOS_ESCOLA); código fora do domínio vira desconhecido."
    ),
    "cs_zona": "CS_ZONA rotulada (ROTULOS_ZONA); código fora do domínio vira desconhecido.",
    "cs_gestant": (
        "CS_GESTANT rotulada (ROTULOS_GESTANT); código fora do domínio vira desconhecido."
    ),
    "n_doses_antes_do_sintoma": (
        "quantas das seis datas de dose COVID são anteriores a DT_SIN_PRI (0 a 6)."
    ),
    "meses_desde_mar2020": (
        "(DT_SIN_PRI − 2020-03-01) em dias dividido por 30,44 — o eixo do tempo do curso."
    ),
    "semana_epi": (
        "semana epidemiológica MMWR do primeiro sintoma, ordinal 1–53; "
        "seno/cosseno só dentro do pipeline logístico (MANIFEST §2.8)."
    ),
    "coinfeccao_outro_virus": (
        "codeteccao_casos do Prata: dois ou mais agentes distintos detectados; "
        "o vazio é preenchido com False, e o manifesto conta quantos."
    ),
    "capital_interior": (
        "capital / interior por CO_MUN_RES contra as 27 capitais, `desconhecido` "
        "quando o município não foi informado; as regiões administrativas do DF "
        "contam como capital (MANIFEST §2.5)."
    ),
    "nosocomial": (
        "NOSOCOMIAL rotulada em sim/nao/ignorado; o vazio fica em `desconhecido`, "
        "nunca fundido no 9 (MANIFEST §2.8)."
    ),
    "y_obito": (
        "o alvo: EVOLUCAO = 2 (óbito), exigido EVOLUCAO ∈ {1,2} no funil — "
        "óbito nos casos fechados (MANIFEST §2.1)."
    ),
    "split": (
        "train/val/test pelo corte temporal 2022-12-31/2023/2024 sobre DT_SIN_PRI: "
        "val é 2023, test é 2024, treino é tudo até o corte (MANIFEST §2.4)."
    ),
    "rt_pcr_confirmado": (
        "PCR_SARS2 marcado. O Ouro usa a definição ampla de covid_caso; esta coluna "
        "deixa o recorte estrito disponível para quem quiser (MANIFEST §2.2)."
    ),
    "gold_id": (
        "identificador estável da linha no Ouro: 0..n−1 na ordem (ano_onset, NU_NOTIFIC). "
        "É por ele que os módulos apontam para um paciente."
    ),
    "ano_onset": (
        "ano-calendário de DT_SIN_PRI. É a chave do split e da leitura ano a ano."
    ),
    "fator_risc_portao": (
        "o portão do funil (FATOR_RISC ∈ {1,S}) que habilita o bloco de comorbidades. "
        "Viaja no Ouro exatamente para que os módulos possam contar perturbações que "
        "o contradizem (MANIFEST §2.5)."
    ),
    "raiox_res": (
        "resultado do raio X de tórax. Imagem fica FORA das features e viaja como "
        "diagnóstico: é a célula-armadilha do caderno do modelo, que mede o que o "
        "modelo teria aprendido (MANIFEST §2.6)."
    ),
    "tomo_res": (
        "resultado da tomografia. Imagem fica FORA das features e viaja como "
        "diagnóstico, pelo mesmo motivo de raiox_res (MANIFEST §2.6)."
    ),
    "n_crit2": (
        "quantos dos critérios 2 da definição de SRAG estão em 1 (TOSSE, GARGANTA). "
        "O funil da coorte exige pelo menos um, então o mínimo no Ouro é 1 — e é por "
        "isso que o caderno do modelo consegue contar quem passa por um fio."
    ),
    "n_crit3": (
        "quantos dos critérios 3 da definição de SRAG estão em 1 "
        "(DISPNEIA, SATURACAO, DESC_RESP). Pelo mesmo motivo de n_crit2, o mínimo "
        "no Ouro é 1."
    ),
}

TRES_ESTADOS = "desconhecido = nao_aplicavel ∪ ausente ∪ ignorado (MANIFEST §2.5)"

# Como ordenar os níveis de uma categórica na coluna `dominio_no_ouro`:
# a leitura natural é sim, nao, ignorado, o resto, desconhecido por último.
_PREFERENCIA = {"sim": 0, "nao": 1, "ignorado": 2}


def dsn() -> str:
    """Connection string from the environment, same source the compose file uses."""
    user = os.environ.get("SRAG_DB_USER", "srag")
    name = os.environ.get("SRAG_DB_NAME", "srag")
    port = os.environ.get("SRAG_DB_PORT", "5433")
    password = os.environ.get("SRAG_DB_PASSWORD")
    if not password:
        raise SystemExit(
            "SRAG_DB_PASSWORD is not set. Copy .env.example to .env, choose a "
            "password, and `set -a; . .env; set +a` before running."
        )
    return f"host=127.0.0.1 port={port} dbname={name} user={user} password={password}"


def faxina(con: duckdb.DuckDBPyConnection) -> None:
    """Derruba o que não está em PERMITIDAS — restos de loaders antigos.

    Uma máquina que rodou a versão por ano ainda carrega `silver.srag_2019`
    … `silver.quarentena_2024`; elas não são erradas, são obsoletas, e
    deixá-las no banco faz o Metabase oferecer duas verdades.
    """
    rows = con.execute(
        "SELECT table_schema, table_name, table_type FROM postgres_query('pg', "
        "$$SELECT table_schema, table_name, table_type FROM information_schema.tables "
        "WHERE table_schema IN ('silver','gold')$$)"
    ).fetchall()
    estranhas = [(s, t, k) for s, t, k in rows if (s, t) not in PERMITIDAS]
    # Views primeiro: uma view pendurada numa tabela impede o DROP dela.
    estranhas.sort(key=lambda r: (r[2] != "VIEW", r[0], r[1]))
    for esquema, tabela, tipo in estranhas:
        objeto = "VIEW" if tipo == "VIEW" else "TABLE"
        con.execute(f"DROP {objeto} IF EXISTS pg.{esquema}.{tabela};")
    if estranhas:
        lista = ", ".join(f"{s}.{t}" for s, t, _ in estranhas)
        print(f"  faxina: {len(estranhas)} objeto(s) de versões antigas — {lista}")


def derrubar(con: duckdb.DuckDBPyConnection, esquema: str, tabela: str) -> None:
    """DROP na forma certa, e SEMPRE pelo DuckDB.

    Duas armadilhas de uma vez. A primeira: o Postgres recusa `DROP VIEW`
    numa tabela e o contrário também, então uma máquina que trocou de
    forma entre versões do loader (o Prata já foi view, hoje é tabela)
    quebrava no re-run. A segunda é pior porque é silenciosa — derrubar
    pelo `postgres_execute` passa por fora do catálogo que o DuckDB
    guarda do ATTACH, e o `CREATE TABLE … AS SELECT` seguinte cria a
    tabela com as colunas certas e **zero linhas**, sem erro nenhum
    (medido 2026-09-02: 240.290 → 0 → 240.290 no mesmo parquet). Todo
    DROP daqui passa pelo DuckDB.
    """
    tipo = con.execute(
        "SELECT table_type FROM postgres_query('pg', "
        f"$$SELECT table_type FROM information_schema.tables "
        f"WHERE table_schema = '{esquema}' AND table_name = '{tabela}'$$)"
    ).fetchall()
    if not tipo:
        return
    objeto = "VIEW" if tipo[0][0] == "VIEW" else "TABLE"
    con.execute(f"DROP {objeto} IF EXISTS pg.{esquema}.{tabela};")


def dicionario_oficial(path: pathlib.Path) -> dict[str, tuple[str, str]]:
    """Campo SIVEP → (rótulo oficial, valores codificados), lido de DICTIONARY.md.

    A tabela do dicionário é a fonte gerada do PDF do Ministério; ler o
    markdown evita reimplementar a extração aqui — e se ele mudar, esta
    tabela muda junto.
    """
    oficial: dict[str, tuple[str, str]] = {}
    for linha in path.read_text(encoding="utf-8").splitlines():
        if not linha.startswith("|"):
            continue
        celulas = [c.strip() for c in linha.strip().strip("|").split("|")]
        if len(celulas) < 11:  # as tabelas curtas do texto não são o dicionário
            continue
        m = re.search(r"`([A-Z0-9_]+)`", celulas[0])
        if m:
            oficial[m.group(1)] = (celulas[1], celulas[3])
    return oficial


def _ordem_nivel(v: str) -> tuple[int, str]:
    return (_PREFERENCIA.get(v, 99 if v == "desconhecido" else 50), v)


def carregar_ouro(con: duckdb.DuckDBPyConnection, data: pathlib.Path) -> None:
    """O Ouro: a tabela cheia, a amostra commitada e a papelada ao lado."""
    modulo = pathlib.Path(__file__).resolve().parents[1]
    raiz = pathlib.Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(raiz / "tools"))
    import srag_30_silver as S
    import srag_60_model as M

    amostra_pq = modulo / "gold/gold_covid_obito_sample.parquet"
    if not amostra_pq.exists():
        print(f"  ouro: {amostra_pq} não existe — pulando", file=sys.stderr)
        return
    counts = json.loads((modulo / "gold/counts.json").read_text(encoding="utf-8"))
    metrics = json.loads(
        (modulo / "gold/model_metrics.json").read_text(encoding="utf-8")
    )
    dtypes: dict[str, str] = counts["features"]

    # y_obito é int8 no parquet (pandas não tem bool anulável barato) e
    # `split` vem dicionarizado; no banco os dois merecem o tipo certo.
    projecao = (
        "* REPLACE (CAST(y_obito AS BOOLEAN) AS y_obito, CAST(split AS VARCHAR) AS split)"
    )

    gold_pq = data / "gold/gold_covid_obito.parquet"
    if gold_pq.exists():
        print("  ouro … ", end="", flush=True)
        con.execute("DROP TABLE IF EXISTS pg.gold.covid_obito;")
        con.execute(
            f"CREATE TABLE pg.gold.covid_obito AS SELECT {projecao} "
            f"FROM read_parquet('{gold_pq.as_posix()}')"
        )
        n = con.execute("SELECT count(*) FROM pg.gold.covid_obito").fetchone()[0]
        print(f"{n:,} linhas")
        for col in ("gold_id", "split", "ano_onset"):
            con.execute(
                "CALL postgres_execute('pg', "
                f"'CREATE INDEX IF NOT EXISTS idx_ouro_{col} "
                f'ON gold.covid_obito ("{col}")\');'
            )
        print("  índices: 3 em gold.covid_obito")
    else:
        print(f"  ouro completo ausente ({gold_pq}) — só a amostra")

    print("  amostra … ", end="", flush=True)
    con.execute("DROP TABLE IF EXISTS pg.gold.amostra;")
    con.execute(
        f"CREATE TABLE pg.gold.amostra AS SELECT {projecao} "
        f"FROM read_parquet('{amostra_pq.as_posix()}')"
    )
    n = con.execute("SELECT count(*) FROM pg.gold.amostra").fetchone()[0]
    print(f"{n:,} linhas")

    # ---- gold.dicionario --------------------------------------------------
    # As 50 colunas do Ouro, uma por linha: papel, família, tipo, de onde
    # veio, o que o Ministério chama aquilo, e o que o Ouro fez com o campo.
    colunas = [
        r[0]
        for r in con.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{amostra_pq.as_posix()}')"
        ).fetchall()
    ]
    if set(colunas) != set(dtypes):
        raise SystemExit(
            "counts.json e o parquet do Ouro discordam das colunas: "
            f"{sorted(set(colunas) ^ set(dtypes))}"
        )

    # Os domínios são MEDIDOS, não declarados: o Ouro cheio quando existe,
    # a amostra quando não. Uma consulta só, sobre o parquet.
    fonte = gold_pq if gold_pq.exists() else amostra_pq
    categoricas = [c for c in colunas if dtypes[c] in ("category", "object")]
    numericas = [c for c in colunas if dtypes[c] not in ("category", "object", "bool")]
    selecao = ", ".join(
        [f'list(DISTINCT "{c}") AS d_{c}' for c in categoricas]
        + [f'min("{c}") AS lo_{c}, max("{c}") AS hi_{c}' for c in numericas]
    )
    cur = con.execute(f"SELECT {selecao} FROM read_parquet('{fonte.as_posix()}')")
    medido = dict(zip([d[0] for d in cur.description], cur.fetchone()))

    def dominio_no_ouro(c: str) -> str:
        tipo = dtypes[c]
        if tipo == "bool":
            return "bool"
        if c in categoricas:
            return " / ".join(sorted(medido[f"d_{c}"], key=_ordem_nivel))
        lo, hi = medido[f"lo_{c}"], medido[f"hi_{c}"]
        fmt = (
            (lambda v: f"{v:.1f}") if tipo.startswith("float") else (lambda v: f"{int(v)}")
        )
        return f"numérico ({tipo}, {fmt(lo)} … {fmt(hi)})"

    catalogo = S.derived_catalogue()
    tres_estados = {c.lower() for c in S.COMORBIDITIES} | {
        c.lower() for c in S.SINTOMAS
    }
    oficial = dicionario_oficial(modulo / "DICTIONARY.md")

    linhas = []
    for c in colunas:
        papel = PAPEL_NAO_FEATURE.get(c, "feature")
        familia = M.GRUPO_DE_FEATURE[c] if papel == "feature" else papel
        origem = ORIGEM.get(c, c.upper() if c.upper() in S.ALL_COLUMNS else "")
        if not origem:
            raise SystemExit(f"coluna do Ouro sem origem declarada: {c}")
        chave = origem
        if chave not in oficial:
            chave = re.sub(r"_(d|marcado)$", "", chave)
        rotulo, dominio = oficial.get(chave, ("", ""))
        if c in catalogo:
            definicao = catalogo[c][0]
        elif c in tres_estados:
            definicao = TRES_ESTADOS
        else:
            definicao = DEFINICAO[c]
        linhas.append(
            (
                c,
                papel,
                familia,
                dtypes[c],
                origem,
                rotulo,
                dominio,
                dominio_no_ouro(c),
                definicao,
            )
        )
    if len(linhas) != 50:
        raise SystemExit(f"gold.dicionario com {len(linhas)} linhas, esperadas 50")

    con.execute("DROP TABLE IF EXISTS pg.gold.dicionario;")
    con.execute(
        "CREATE TABLE pg.gold.dicionario "
        "(coluna VARCHAR, papel VARCHAR, familia VARCHAR, dtype VARCHAR, "
        "origem VARCHAR, rotulo_oficial VARCHAR, dominio_oficial VARCHAR, "
        "dominio_no_ouro VARCHAR, definicao VARCHAR);"
    )
    con.executemany(
        "INSERT INTO pg.gold.dicionario VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", linhas
    )

    # ---- gold.funil -------------------------------------------------------
    # A ordem importa: as contagens não comutam (MANIFEST §1).
    funil = []
    anterior = None
    for i, (filtro, restam) in enumerate(counts["funil"]):
        funil.append((i, filtro, restam, None if anterior is None else anterior - restam))
        anterior = restam
    con.execute("DROP TABLE IF EXISTS pg.gold.funil;")
    con.execute(
        "CREATE TABLE pg.gold.funil "
        "(ordem INTEGER, filtro VARCHAR, restam BIGINT, saem BIGINT);"
    )
    con.executemany("INSERT INTO pg.gold.funil VALUES (?, ?, ?, ?)", funil)

    # ---- gold.decisoes ----------------------------------------------------
    decisoes = [(k, str(v)) for k, v in counts["decisoes"].items()]
    for s, d in counts["splits"].items():
        decisoes += [(f"split.{s}.{k}", str(v)) for k, v in d.items()]
    decisoes += [(f"na_absorvidos.{k}", str(v)) for k, v in counts["na_absorvidos"].items()]
    decisoes += [
        (k, str(counts[k]))
        for k in ("n_gold", "obitos", "letalidade_pct", "rt_pcr_confirmado", "extracao")
    ]
    decisoes += [(f"amostra.{k}", str(v)) for k, v in counts["amostra"].items()]
    con.execute("DROP TABLE IF EXISTS pg.gold.decisoes;")
    con.execute("CREATE TABLE pg.gold.decisoes (chave VARCHAR, valor VARCHAR);")
    con.executemany("INSERT INTO pg.gold.decisoes VALUES (?, ?)", decisoes)

    # ---- gold.modelo, gold.exemplar, gold.xgb_params, gold.impossibilidades
    modelo = [
        (
            nome,
            r["split"],
            r["n"],
            r["obitos"],
            r["auc"],
            r["brier"],
            r["previsto_medio"],
            r["observado"],
        )
        for nome in ("xgb", "logit")
        for r in metrics[nome]
    ]
    con.execute("DROP TABLE IF EXISTS pg.gold.modelo;")
    con.execute(
        "CREATE TABLE pg.gold.modelo "
        "(modelo VARCHAR, split VARCHAR, n BIGINT, obitos BIGINT, auc DOUBLE, "
        "brier DOUBLE, previsto_medio DOUBLE, observado DOUBLE);"
    )
    con.executemany("INSERT INTO pg.gold.modelo VALUES (?, ?, ?, ?, ?, ?, ?, ?)", modelo)

    exemplar = [
        (
            "paciente-regra",
            metrics["exemplar"]["gold_id"],
            metrics["exemplar"]["p_obito"],
            metrics["exemplar"].get("resumo"),
        ),
        (
            "paciente-2021",
            metrics["paciente_2021"]["gold_id"],
            metrics["paciente_2021"]["p_obito"],
            metrics["paciente_2021"].get("resumo"),
        ),
    ]
    con.execute("DROP TABLE IF EXISTS pg.gold.exemplar;")
    con.execute(
        "CREATE TABLE pg.gold.exemplar "
        "(papel VARCHAR, gold_id INTEGER, p_obito DOUBLE, resumo VARCHAR);"
    )
    con.executemany("INSERT INTO pg.gold.exemplar VALUES (?, ?, ?, ?)", exemplar)

    con.execute("DROP TABLE IF EXISTS pg.gold.xgb_params;")
    con.execute("CREATE TABLE pg.gold.xgb_params (chave VARCHAR, valor VARCHAR);")
    con.executemany(
        "INSERT INTO pg.gold.xgb_params VALUES (?, ?)",
        [(k, str(v)) for k, v in metrics["xgb_params"].items()],
    )

    con.execute("DROP TABLE IF EXISTS pg.gold.impossibilidades;")
    con.execute(
        "CREATE TABLE pg.gold.impossibilidades (restricao VARCHAR, fracao_pct DOUBLE);"
    )
    con.executemany(
        "INSERT INTO pg.gold.impossibilidades VALUES (?, ?)",
        list(metrics["impossibilidades"].items()),
    )


def main(argv: list[str]) -> int:
    apenas_ouro = "--only-gold" in argv
    posicionais = [a for a in argv if not a.startswith("-")]
    data = (
        pathlib.Path(posicionais[0]).expanduser()
        if posicionais
        else pathlib.Path.home() / "Documents/srag-data"
    )
    files = sorted(data.glob("INFLUD*.parquet"))
    if not files and not apenas_ouro:
        print(
            f"no INFLUD*.parquet under {data} — run tools/srag_10_fetch.sh first",
            file=sys.stderr,
        )
        return 2

    con = duckdb.connect()
    con.execute("INSTALL postgres; LOAD postgres;")
    con.execute(f"ATTACH '{dsn()}' AS pg (TYPE postgres);")
    for schema in ("bronze", "silver", "gold"):
        con.execute(f"CREATE SCHEMA IF NOT EXISTS pg.{schema};")

    faxina(con)

    years: list[str] = []
    if not apenas_ouro:
        # Drop the union views before their tables: a view depends on every
        # yearly table, so dropping the tables first fails on the second run
        # with "cannot drop table ... because other objects depend on it". The
        # first run succeeds because the view does not exist yet, which is why
        # this only surfaces on re-run.
        derrubar(con, "bronze", "srag")

        for f in files:
            m = re.search(r"INFLUD(\d\d)", f.name)
            year = "20" + m.group(1)
            years.append(year)
            table = f"pg.bronze.srag_{year}"
            print(f"  {year} … ", end="", flush=True)
            con.execute(f"DROP TABLE IF EXISTS {table};")
            # Everything as VARCHAR: Bronze does not decide what a value means.
            con.execute(
                f"CREATE TABLE {table} AS SELECT * FROM read_parquet('{f.as_posix()}')"
            )
            n = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            print(f"{n:,} linhas")

        union = "\nUNION ALL\n".join(
            f"  SELECT {y} AS ano, * FROM bronze.srag_{y}" for y in years
        )
        derrubar(con, "bronze", "srag")
        con.execute(f"CREATE VIEW pg.bronze.srag AS\n{union}")

    # Silver, if tools/srag_30_silver.py has been run: ONE table for the whole
    # series — the per-year split and the separate quarantine banks are gone
    # (the 7 shifted rows travel in the single table under `linha_deslocada`).
    silver_pq = data / "silver.parquet"
    if silver_pq.exists() and not apenas_ouro:
        print("  silver … ", end="", flush=True)
        derrubar(con, "silver", "srag")
        con.execute(
            f"CREATE TABLE pg.silver.srag AS "
            f"SELECT * FROM read_parquet('{silver_pq.as_posix()}')"
        )
        n = con.execute("SELECT count(*) FROM pg.silver.srag").fetchone()[0]
        print(f"{n:,} linhas (tabela única)")
        for col in ("NU_NOTIFIC", "SG_UF", "se_primeiro_sinto", "covid_caso"):
            con.execute(
                "CALL postgres_execute('pg', "
                f"'CREATE INDEX IF NOT EXISTS idx_srag_{col.lower()} "
                f'ON silver.srag ("{col}")\');'
            )
        print("  índices: 4 na tabela única")

        # As derivadas entram no mesmo contrato, com o label de definição na
        # coluna `definicao` — quem navega no Metabase lê o que cada coluna
        # significa sem abrir o repositório. Para as cruas, `definicao` traz
        # o domínio.
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
        import srag_30_silver as S

        rows = []
        for family, cols in S.FAMILIES:
            for c in cols:
                parent = S.GATES.get(c)
                rows.append(
                    (
                        c,
                        family,
                        S.class_of(c),
                        ",".join(S.DOMAINS.get(c, ())),
                        f"{parent[0]} in {'/'.join(parent[1])}" if parent else "",
                    )
                )
        for nome, (definicao, fonte, classe) in sorted(S.derived_catalogue().items()):
            rows.append((nome, f"derivada ({fonte})", classe, definicao, ""))
        con.execute("DROP TABLE IF EXISTS pg.silver.contrato;")
        con.execute(
            "CREATE TABLE pg.silver.contrato "
            "(coluna VARCHAR, familia VARCHAR, classe VARCHAR, "
            "definicao VARCHAR, portao VARCHAR);"
        )
        con.executemany("INSERT INTO pg.silver.contrato VALUES (?, ?, ?, ?, ?)", rows)
        n = con.execute("SELECT count(*) FROM pg.silver.contrato").fetchone()[0]
        print(f"  silver.contrato: {n} colunas documentadas")

    carregar_ouro(con, data)

    if years:
        total = con.execute("SELECT count(*) FROM pg.bronze.srag").fetchone()[0]
        print(f"\nbronze.srag: {total:,} linhas em {len(years)} tabelas anuais")
    else:
        print()
    # A contagem final é feita PELO Postgres (postgres_query), não puxando a
    # tabela para o DuckDB: `silver.srag` tem 4,1 M linhas e 420 colunas.
    existentes = {
        (s, t)
        for s, t in con.execute(
            "SELECT table_schema, table_name FROM postgres_query('pg', "
            "$$SELECT table_schema, table_name FROM information_schema.tables "
            "WHERE table_schema IN ('silver','gold')$$)"
        ).fetchall()
    }
    for esquema, tabela in sorted(PERMITIDAS):
        if (esquema, tabela) not in existentes:
            continue
        n = con.execute(
            "SELECT * FROM postgres_query('pg', "
            f"$$SELECT count(*) FROM {esquema}.{tabela}$$)"
        ).fetchone()[0]
        print(f"  {esquema}.{tabela}: {n:,} linhas")
    print("\n  Metabase: http://localhost:3000   ·   Adminer: http://localhost:8080")
    print("  psql:    postgresql://$SRAG_DB_USER@127.0.0.1:5433/$SRAG_DB_NAME")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
