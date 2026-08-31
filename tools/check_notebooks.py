#!/usr/bin/env python3
"""Machine-check the notebook conventions from CONTRIBUTING.md.

Checked, per committed notebook under modules/*/notebooks/:

  1. Execution counts run exactly 1..N — the observable trace of
     "Restart & Run All in a fresh kernel" (CONTRIBUTING, Notebook conventions).
  2. The first code cell is an unpinned `%pip install -q ...`: no `-U`, no
     `==`/`>=` version specifiers (CONTRIBUTING, Your first contribution).
  3. No `%%time` / `%time` magics — wall-clock output is nondeterministic
     (CONTRIBUTING, "Keep outputs deterministic").

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
