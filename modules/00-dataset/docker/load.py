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
    data = pathlib.Path(argv[0]).expanduser() if argv else pathlib.Path.home() / "Documents/srag-data"
    files = sorted(data.glob("INFLUD*.parquet"))
    if not files:
        print(f"no INFLUD*.parquet under {data} — run tools/fetch_srag.sh first", file=sys.stderr)
        return 2

    con = duckdb.connect()
    con.execute("INSTALL postgres; LOAD postgres;")
    con.execute(f"ATTACH '{dsn()}' AS pg (TYPE postgres);")
    for schema in ("bronze", "silver", "gold"):
        con.execute(f"CREATE SCHEMA IF NOT EXISTS pg.{schema};")

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
            f"CREATE TABLE {table} AS "
            f"SELECT * FROM read_parquet('{f.as_posix()}')"
        )
        n = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        print(f"{n:,} linhas")

    union = "\nUNION ALL\n".join(
        f"  SELECT {y} AS ano, * FROM bronze.srag_{y}" for y in years
    )
    con.execute("DROP VIEW IF EXISTS pg.bronze.srag;")
    con.execute(f"CREATE VIEW pg.bronze.srag AS\n{union}")

    total = con.execute("SELECT count(*) FROM pg.bronze.srag").fetchone()[0]
    print(f"\nbronze.srag: {total:,} linhas em {len(years)} tabelas anuais")
    print("  Metabase: http://localhost:3000   ·   Adminer: http://localhost:8080")
    print("  psql:    postgresql://$SRAG_DB_USER@127.0.0.1:5433/$SRAG_DB_NAME")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
