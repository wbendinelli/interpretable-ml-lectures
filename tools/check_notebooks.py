#!/usr/bin/env python3
"""Machine-check the notebook conventions from CONTRIBUTING.md.

Checked, per committed notebook under modules/*/notebooks/:

  1. Execution counts run exactly 1..N — the observable trace of
     "Restart & Run All in a fresh kernel" (CONTRIBUTING, Notebook conventions).
  2. The first code cell is an unpinned `%pip install -q ...`: no `-U`, no
     `==`/`>=` version specifiers (CONTRIBUTING, Your first contribution).
  3. No `%%time` / `%time` magics — wall-clock output is nondeterministic
     (CONTRIBUTING, "Keep outputs deterministic").
  4. The first markdown cell opens with the SAPIANS kicker line
     (CONTRIBUTING, "O esqueleto do caderno").
  5. Section headers use the `## §N — título` notation — never `## Passo N`
     nor `## N.` — so the prose pointers "(walkthrough §N)" are literally
     findable in the notebook (same section).
  6. Exactly one `## Fechamento` closing section — except under
     modules/00-dataset/, whose last section stays numbered because the
     module README points at it by number (same section).

Exit 0 when every notebook passes, 1 with one line per violation otherwise.
Stdlib only; requires Python >= 3.9.

Usage:
    python3 tools/check_notebooks.py [notebook.ipynb ...]   # default: all committed
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PIN_RE = re.compile(r"[=<>~]=|\s-U\b|\s--upgrade\b")
KICKER_RE = re.compile(r"^\*\*SAPIANS\*\* · SCC5819 · ")
SECAO_VELHA_RE = re.compile(r"^##\s+(?:Passo\s+\d|\d+[a-z]?\.\s)", re.MULTILINE)
FECHAMENTO_RE = re.compile(r"^##\s+Fechamento\b", re.MULTILINE)


def check(path: pathlib.Path) -> list[str]:
    problems = []
    nb = json.loads(path.read_text(encoding="utf-8"))
    code_cells = [c for c in nb.get("cells", []) if c.get("cell_type") == "code"]

    counts = [c.get("execution_count") for c in code_cells]
    expected = list(range(1, len(code_cells) + 1))
    if counts != expected:
        problems.append(
            f"{path}: execution counts are {counts[:8]}{'...' if len(counts) > 8 else ''}, "
            f"not 1..{len(code_cells)} — run Restart & Run All in a fresh kernel"
        )

    if code_cells:
        first = "".join(code_cells[0].get("source", []))
        if "%pip install" not in first:
            problems.append(
                f"{path}: first code cell is not the `%pip install -q ...` Colab cell"
            )
        elif PIN_RE.search(first):
            problems.append(
                f"{path}: the `%pip install` cell must stay unpinned and without -U "
                "(CONTRIBUTING, 'Your first contribution')"
            )

    for i, c in enumerate(code_cells):
        src = "".join(c.get("source", []))
        if re.search(r"^\s*%%?time\b", src, flags=re.MULTILINE):
            problems.append(
                f"{path}: code cell {i + 1} uses a %time magic — outputs must be deterministic"
            )

    md_cells = [c for c in nb.get("cells", []) if c.get("cell_type") == "markdown"]
    if md_cells:
        first_md = "".join(md_cells[0].get("source", []))
        if not KICKER_RE.match(first_md):
            problems.append(
                f"{path}: the first markdown cell does not open with the SAPIANS "
                "kicker (CONTRIBUTING, 'O esqueleto do caderno')"
            )
    md_text = "\n".join("".join(c.get("source", [])) for c in md_cells)
    for m in SECAO_VELHA_RE.finditer(md_text):
        problems.append(
            f"{path}: section header {m.group(0).strip()!r} — use `## §N — título` "
            "(CONTRIBUTING, 'O esqueleto do caderno')"
        )
    if "00-dataset" not in path.as_posix():
        n_fecho = len(FECHAMENTO_RE.findall(md_text))
        if n_fecho != 1:
            problems.append(
                f"{path}: expected exactly one `## Fechamento — …` section, found {n_fecho}"
            )

    return problems


def main(argv: list[str]) -> int:
    paths = [pathlib.Path(a) for a in argv] or sorted(
        ROOT.glob("modules/*/notebooks/*.ipynb")
    )
    problems = []
    for p in paths:
        try:
            problems += check(p)
        except (json.JSONDecodeError, OSError) as e:
            problems.append(f"{p}: unreadable notebook — {e}")
    for line in problems:
        print(line, file=sys.stderr)
    if not problems:
        print(f"{len(paths)} notebook(s) pass the CONTRIBUTING conventions")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
