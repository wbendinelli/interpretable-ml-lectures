"""Pin the IBGE municipality table that the Silver referential check reads.

Usage:
    python tools/srag_11_fetch_ibge.py

Writes modules/00-dataset/reference/municipios_ibge.csv with one row per
municipality: the 6-digit code SIVEP-Gripe uses (the 7-digit IBGE code
without its check digit), the full 7-digit code, the name, and the UF.

Provenance: IBGE Localidades API,
https://servicodados.ibge.gov.br/api/v1/localidades/municipios?view=nivelado
— the official registry. The file is a committed snapshot, so the
referential check runs offline and deterministically; re-running this
script only changes it when IBGE itself creates or renames a
municipality, and that diff is a finding, not noise.

SIVEP's CO_MUN_* fields carry the 6-digit form in 100% of filled cells in
all six years (measured 2026-08-31), which is why `codigo6` is the join
key.
"""

from __future__ import annotations

import csv
import gzip
import json
import pathlib
import sys
import urllib.request

URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?view=nivelado"
OUT = (
    pathlib.Path(__file__).resolve().parent.parent
    / "modules/00-dataset/reference/municipios_ibge.csv"
)


def fetch() -> list[dict]:
    req = urllib.request.Request(URL, headers={"Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = r.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return json.loads(raw)


def main() -> int:
    rows = []
    for m in fetch():
        code7 = str(m["municipio-id"])
        if len(code7) != 7 or not code7.isdigit():
            print(f"unexpected municipality id: {code7!r}", file=sys.stderr)
            return 2
        rows.append(
            {
                "codigo6": code7[:6],
                "codigo7": code7,
                "nome": m["municipio-nome"],
                "uf": m["UF-sigla"],
            }
        )
    rows.sort(key=lambda r: r["codigo7"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["codigo6", "codigo7", "nome", "uf"])
        w.writeheader()
        w.writerows(rows)
    print(f"{OUT}: {len(rows)} municípios")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
