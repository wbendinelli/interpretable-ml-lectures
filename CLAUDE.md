# CLAUDE.md — operating manual for agents working in this repository

Lecture materials on machine learning interpretability, written by William
Bendinelli for SCC5819 (Interpretable ML, ICMC-USP). This is the **working
repository**: where modules are written, studied in depth, and revised.
The repository has **one hard rule** and everything else serves it:

> **Every quantitative claim in prose is printed by a committed notebook cell
> in the same module.** A number without a printing cell is a bug — either add
> the cell or delete the number. When a measurement contradicts the prose, the
> prose changes and the old value stays in the record, marked as corrected
> (evidence bar, rule 3 — see CONTRIBUTING.md).

Full policy: [CONTRIBUTING.md](CONTRIBUTING.md). This file is the condensed,
agent-facing version plus the duties no check enforces.

## Module numbering, and the relationship to the course repository

Modules use **this repository's own sequential numbering**, in teaching order:
`01-ceteris-paribus`, `02-ice`, `03-lime`. They map onto Molnar's chapters 12,
13 and 14, and each module README names its chapter — but the directory number
is ours, not Molnar's.

> **2026-09-02 — publication downstream is SUSPENDED (owner's decision).**
> Nothing goes out to `scc5819/interpretable-ml-lectures` until the class
> actually adopts the repository. `modules/14-lime` over there stays frozen
> in its BCW-era English form — it is a delivered artifact of a talk, and
> half-publishing the SRAG/COVID rewrite over it would leave the public
> repository describing a course that does not exist yet. The procedure
> below is kept verbatim, and is **inactive**: read it as the recipe to
> follow *if and when* publication resumes, not as a duty that content
> changes now trigger.

**This repository is the source.** Modules are written here.
[`scc5819/interpretable-ml-lectures`](https://github.com/scc5819/interpretable-ml-lectures)
(locally `~/Documents/scc5819-interpretable-ml-lectures`) is the course's
public repository and a **publication target**: material goes out to it, never
comes back. It numbers modules by Molnar chapter, so publishing module 03
means copying notebooks, figures, and `lecture/outline.md` verbatim into
`modules/14-lime/`, then rewriting in its README:

- `Module 03` → `Module 14`
- `wbendinelli/interpretable-ml-lectures` → `scc5819/interpretable-ml-lectures`
- `modules/03-lime` → `modules/14-lime`

Deck PDFs are identical in both repositories and are historical artifacts —
never retro-edited on either side. The two repositories pin different Python
versions on purpose (3.12 here, 3.14 there); the committed outputs are
byte-identical across both, which is what makes verbatim copying safe. Before
publishing, confirm that still holds rather than assuming it.

## What CI already enforces (don't fight it, don't duplicate it)

Red checks are correct behavior — fix the cause, never weaken the check:

- **links** — relative links and anchors in every `.md` + `CITATION.cff`.
- **checks** — pre-commit (ruff on `tools/`, codespell, actionlint, yaml/toml,
  `tools/check_notebooks.py`: execution counts 1..N, unpinned `%pip`, no
  `%%time`). `check_notebooks.py` **will** grow checks for the notebook
  skeleton — the brand cell, the `## §N — título` headers, the `SP.aplicar()`
  setup lines, the closing section (CONTRIBUTING.md, "O esqueleto do
  caderno") — in a later commit; until then the skeleton is a duty you keep
  by hand, like the CHANGELOG line.
- **walkthroughs / internals** — the notebooks must run end to end on the
  pinned stack (`requirements.lock`, `--require-hashes`, Python 3.12.13) and
  write nothing into the repo tree.
- **citation** — `CITATION.cff` stays schema-valid.
- **changelog** — a PR touching `modules/`, `tools/`, `.github/` or
  `requirements*` must also touch `CHANGELOG.md`, unless it carries the
  `no-changelog` label. Keep entries short: what changed and why it matters.
- Weekly (not on PRs): external link check, latest-stack canary
  (`canary.yml`).

## Duties CI cannot enforce (do these without being asked)

1. **CHANGELOG.md** — one line per notable change, under a date heading.
   The CI check makes you touch the file; making the line say something
   useful is on you.
2. **Notebook protocol** — any notebook edit, however small, ends with a full
   fresh-kernel run before committing:

   ```bash
   PIP_DISABLE_PIP_VERSION_CHECK=1 jupyter nbconvert --to notebook \
     --execute --inplace modules/NN-slug/notebooks/<name>.ipynb
   ```

   (The env var matters: without it, pip's upgrade banner bakes a local
   filesystem path into the committed output.) Outputs are committed **by
   design** — never strip them, never add nbstripout, never pin versions in
   the `%pip` cell.
3. **Figures** — notebooks write to `figures_generated/` (git-ignored).
   Promote to `modules/NN-slug/figures/` by explicit copy, and say in the
   commit which cell regenerated the figure and why the picture moved.
   Unchanged figures reproduce byte-identically on the pinned stack — a
   figure that diffs without a code change is a finding, not noise.

   One known exception, measured 2026-08-30: **PDF figures are not byte-stable,
   PNGs are.** matplotlib stamps `/CreationDate` into a PDF, so re-running
   module 03 leaves `lime_walkthrough_combined.pdf` differing from the
   committed copy in exactly 6 bytes, all inside that timestamp — same file
   size, and the PNG of the same figure is byte-identical. That is the whole
   difference; treat a *larger* PDF diff as a real change. To compare PDFs
   byte-for-byte, pin the stamp:

   ```bash
   SOURCE_DATE_EPOCH=1600000000 jupyter nbconvert --to notebook --execute ...
   ```

   (verified: matplotlib 3.11.1 then writes `D:20200913122640Z`). Nothing
   leaks into a commit either way — `figures_generated/` is git-ignored and
   the committed `figures/` copy is only ever updated by an explicit copy.
4. **Prose ↔ cell sync** — after a re-run, diff every printed number against
   the module README and `lecture/outline.md`. Section pointers use the short
   forms `(walkthrough §N)` / `(internals §N)`.
5. **Module table** — the table in the root README is maintained by hand.
   Adding a module directory means adding its row in the same commit.
6. **Publication** — ~~after content changes to a module that is already
   public in the course repository, push the change downstream with the
   rewrites listed above~~. **SUSPENDED 2026-09-02 (owner's decision):** do
   not publish anything downstream; `modules/14-lime` in the course
   repository stays frozen in its BCW-era English form. Publication resumes
   only if the class uses the repo — and then by the recipe above, still
   one-way.

## Things that look like improvements but are policy violations

- **Editing a delivered deck** (`lecture/*.pdf`). Decks are historical
  artifacts of a talk given by a person on a date — never retro-edited, even
  when a number in them has since been corrected. The living form of the
  lecture is `lecture/outline.md`; corrections go there, with a note that the
  frozen deck differs. (Precedent: the deck's "R² swings 30%" vs the
  measured 26% — module 03, outline §5.)
- **Bumping Python packages** or adding Dependabot for pip. Pins move once
  per offering, as a single deliberate PR. (Adding a *new* package that no
  existing notebook imports is the narrow exception — taken 2026-09-01 for
  xgboost — and its lock diff must contain only additions; a resolver that
  moves any existing pin turns it into the full ritual.) The ritual: `requirements.txt` + regenerated
  `requirements.lock` (`uv pip compile --universal --generate-hashes
  --python-version 3.12`) + every notebook re-run + figures + every quoted
  number re-checked. Actions bumps are the one exception (Dependabot handles
  them; keep the SHA-pin style).
- **Stripping notebook outputs, adding timestamps/`%%time`/progress bars,**
  or "fixing" the unpinned `%pip` cell — all deliberately the way they are.
- **Adding infrastructure.** The repo is at its deliberate infra ceiling
  (CI, pre-commit, lock, notebook checks, canary). New investment goes into
  modules, not machinery. The course repository's board tooling
  (`schedule.toml`, `render_board.py`) is deliberately *not* mirrored here —
  it manages a class calendar this repository does not have.

## Workflow facts

- **Branch → PR → green CI → merge.** Commit style: `type(scope): summary` —
  `docs(03-lime): …`, `fix(03-lime): …`, `ci: …`, `feat(tools): …`.
  A falsification is a `fix`.
- Local setup:

  ```bash
  uv venv --python 3.12 .venv
  VIRTUAL_ENV="$PWD/.venv" uv pip install --require-hashes -r requirements.lock
  ```

  (or `-r requirements.txt` to merely follow along). Before pushing:
  `pre-commit run --all-files`.
- Numbers were produced on Apple Silicon + the pinned stack and reproduce
  byte-identically there; a Linux runner may move third decimals, which is
  why CI executes notebooks but never diffs outputs.
