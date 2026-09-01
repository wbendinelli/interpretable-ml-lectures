#!/usr/bin/env python3
"""Load the SRAG parquet files into the local Postgres, as the Bronze layer.

Bronze means raw: every column lands as text, exactly as published, with no
coercion, no renaming and no rows dropped. Typing and recoding belong to
Silver, where each decision is recorded rather than assumed.

DuckDB does the transfer — it reads parquet natively and writes to Postgres
through its `postgres` extension, so there is no CSV round-trip.

    docker compose up -d
    python3 modules/00-dataset/docker/load.py [data_dir]

Re-running replaces the tables, so it is safe to repeat.
"""

from __future__ import annotations

import os
import pathlib
import re
import sys

import duckdb


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


def main(argv: list[str]) -> int:
    data = (
        pathlib.Path(argv[0]).expanduser()
        if argv
        else pathlib.Path.home() / "Documents/srag-data"
    )
    files = sorted(data.glob("INFLUD*.parquet"))
    if not files:
        print(
            f"no INFLUD*.parquet under {data} — run tools/fetch_srag.sh first",
            file=sys.stderr,
        )
        return 2

    con = duckdb.connect()
    con.execute("INSTALL postgres; LOAD postgres;")
    con.execute(f"ATTACH '{dsn()}' AS pg (TYPE postgres);")
    for schema in ("bronze", "silver", "gold"):
        con.execute(f"CREATE SCHEMA IF NOT EXISTS pg.{schema};")

    # Drop the union views before their tables: a view depends on every yearly
    # table, so dropping the tables first fails on the second run with
    # "cannot drop table ... because other objects depend on it". The first run
    # succeeds because the view does not exist yet, which is why this only
    # surfaces on re-run.
    for schema in ("bronze", "silver"):
        con.execute(f"DROP VIEW IF EXISTS pg.{schema}.srag;")

    years = []
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
    con.execute("DROP VIEW IF EXISTS pg.bronze.srag;")
    con.execute(f"CREATE VIEW pg.bronze.srag AS\n{union}")

    # Silver, if tools/srag_silver.py has been run: ONE table for the whole
    # series — the per-year split and the separate quarantine banks are gone
    # (the 7 shifted rows travel in the single table under `linha_deslocada`).
    silver_pq = data / "silver.parquet"
    if silver_pq.exists():
        print("  silver … ", end="", flush=True)
        con.execute("DROP VIEW IF EXISTS pg.silver.srag;")
        con.execute("DROP TABLE IF EXISTS pg.silver.srag;")
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
        import srag_silver as S

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

    total = con.execute("SELECT count(*) FROM pg.bronze.srag").fetchone()[0]
    print(f"\nbronze.srag: {total:,} linhas em {len(years)} tabelas anuais")
    print("  Metabase: http://localhost:3000   ·   Adminer: http://localhost:8080")
    print("  psql:    postgresql://$SRAG_DB_USER@127.0.0.1:5433/$SRAG_DB_NAME")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
