# Changelog

Notable changes to the repository as a whole. Module-level content changes are
tracked in the git history under their `docs(NN-slug)`/`fix(NN-slug)` scopes.

## 2026-09-08 — this repository is public, and the downstream one is closed

- **The working repository was made public; the course repository was archived
  and made private.** The trigger was practical: the modules 01–05 report went
  to Prof. André, and the link in that mail had to open for him. Before the
  switch the history was audited rather than assumed — the only
  credential-shaped file ever committed, on any branch, is
  `modules/00-dataset/docker/.env.example`, whose password field is empty;
  `.env` has been git-ignored since the docker stack was written; and the
  committed gold sample carries only derived features (age in years, sex,
  comorbidities, symptoms, region, capital/interior), with no name, no exact
  date and no municipality — coarser than the SIVEP-Gripe microdata it comes
  from, which is already open. Side effect worth naming: the Colab badges on
  modules 01–05 work for an outside reader for the first time.
- **The publication procedure is deleted, not suspended.** `CLAUDE.md` carried
  a recipe for copying module 03 downstream into `modules/14-lime`; it was
  marked inactive on 2026-09-02 and kept verbatim, to be followed "if and when
  publication resumes". An archived repository refuses pushes and a private
  one shows a reader nothing, so the recipe is gone and the section now says
  why. Keeping a dead procedure verbatim is what let it read as live.
- **The weekly link check is told to expect one 404.** The entry of 2026-08-30
  below links the course repository, which now answers 404 to an anonymous
  checker. A historical entry is not retro-edited, so the URL stays and a new
  `.lycheeignore` records why the weekly external run skips it.

## 2026-09-08 — a review board found thirteen serious claims the evidence bar could not see

- **The evidence bar guards digits, not meaning, and that is where the report
  went wrong.** A five-specialist board (surveillance epidemiology on
  SIVEP-Gripe, infectious disease and critical care, prognostic-model
  biostatistics, interpretability, and number tracing) read
  `reports/01-metodos-locais/main.typ` against the external sources and against
  the committed cells. The arithmetic survived whole: 35 quantitative claims
  audited, no central computation wrong, `check_numbers.py` green at 56/56
  before and 67/67 after. What failed was the *class* of the sentence, and the
  three most dangerous ones carried no digit and no footnote at all.
- **`FATOR_RISC` never takes the value "no".** The report said 37,3% of the
  sample "declared they had no risk factor". Across six years and 4.1 M records
  the value never appears once (`PROFILE.md:391,590`): the field is blank, and
  the comorbidity block is blank with it. That is non-response, not a
  declaration — the very error the same paragraph warned against.
- **The SRAG case definition was the repository's filter wearing the Ministry's
  clothes.** The official definition is influenza-like illness (two of eight
  symptoms, fever among them) plus a severity sign that includes chest pressure
  and cyanosis. The text described `HOSPITAL & crit2 & crit3` and called it the
  definition of a case; it also claimed a patient outside it "would not be in
  the base", when 40,9% of the base fails that filter and sits there anyway.
- **Discrimination does not suffer with calibration.** §2 claimed the ability to
  rank patients "suffers along with" the level error. No cell measures that, AUC
  is invariant to monotone rescaling, and the by-year series contradicts it:
  0,7890 (2020) to 0,7680 (2024), with the floor in 2022, inside the training
  window. `srag_model_internals` cell 7 already said the opposite in prose.
- **Two lethality series were chained as one.** 29,0% → 8,6% is all of SRAG, and
  most of that fall is population turnover (COVID fraction 59,8% → 11,6%). The
  model's cohort falls 31,4% → 18,2%. The report put the first number three
  lines from the model's calibration gap, inviting the reader to add them.
- **Also corrected**: the ALE described with the M-plot's mechanism and sold as
  the remedy for the fences (it fixes extrapolation, not logical constraint);
  the pre-campaign fence stated as law when `srag_30_silver.py:1532` records
  that earlier doses exist and stay; "not pulmonary, documentation" contradicting
  the trap cell's own table, where lethality falls from typical-COVID to
  negative-for-pneumonia and the leak lives in the uninformative levels, worth
  0,0038 of AUC; the vaccine φ given all three mechanisms instead of the
  weakest one; "there is none" for the counterfactual becoming "not in this
  model", since the feature space contains no treatment by design; and the
  vulnerable patient's "fiction from start to finish", which no cell measures
  and `gate_impossible` makes impossible.
- **The figures were right; the legend was lying.** §3 claimed one colour axis
  and the report uses three (class, possibility, series identity). Fixed in the
  legend, not in the figures — no notebook ran, no pixel moved.
- **Headings stopped colliding with the paragraph they introduce.** The
  suspicion that `par.spacing` swallowed the heading's `below` is false: a block
  adjacent to a paragraph takes precedence. The real defect was that 0,9 mm was
  under half the leading. Values recalibrated by measuring the rendered PNG:
  with body lines 1,34 mm apart, a section title now gets 4,33 mm above and a
  subheading 2,24 mm below. Two dead parameters removed on the way (`above:` on
  the caption block, which `figure.gap` actually governs).
- **`shapley1953` left the bibliography** (credit kept in prose), `wolff2019` had
  its pages corrected from W1–W33 to 51–58 and the PROBAST *Explanation and
  Elaboration* entered as its own entry, and the report gained the repository
  URL it never had — twenty-three footnotes pointed at "module 0N, walkthrough
  §M" with no way for an outside reader to resolve any of them.
- **The bronchiolitis explanation was printed by a cell, so the fix had to run
  the kernel.** `ice_walkthrough` cell 14 attributed the pediatric peak of the
  derivative (0,0239/year at 10) to "inheritance from the pre-COVID cohort
  (bronchiolitis)". The cohort cannot carry it: the Gold funnel filters
  `covid_caso` and onset ≥ 2020-02-26, so there is no 2019, no non-COVID SRAG
  and no RSV in training — and bronchiolitis is a disease of under-twos, median
  age 3.5 months, against a peak at 10 years. The cell now *measures* the real
  explanation instead of asserting a wrong one: observed lethality in training
  rises 3,49% → 4,50% → 9,25% → 13,89% across the 4–20 bands, the adolescent arm
  of the U-shaped pediatric COVID mortality curve, with the missing caveat
  (292–720 patients per band against tens of thousands in the adult middle) now
  printed too. Module README, lecture outline and the report followed.
- **The barred point stopped being terracotta.** Figure 9 painted a
  gate-blocked vaccine dose in TERRACOTA — a colour the report defines as
  *death* in §3 and uses for φ>0 in §8. On an axis labelled `p(óbito) prevista`,
  in a chart about vaccine doses, that is the worst possible collision. It is
  now CINZA_CLARO, which the palette already reserves for "synthetic without
  class · neutral/unknown": a barred point is a non-point, not a bad outcome.
  `cf_walkthrough` cell 12 changed with it, so the same question does not carry
  two colour schemes across the repository.
- **And the legend was covering the bars it explained.** Cell 22's own comment
  anticipated the risk ("a bar touching a legend is the figure lying about its
  height") and the 0,51-to-0,70 headroom did not fit a two-line legend: it
  covered bars 0 and 1 of the right panel, which is exactly where the single
  green bar lives. One row (`ncol=2`, no frame) fits.
- **The barred point ended up blue, not green.** SAGE and CINZA_CLARO sit too
  close in luminance for the surviving bar to stand out, and green appeared in
  exactly one of the report's seven figures. AZUL is the palette's primary
  series and is already used that way in figure 6. The objection that blue means
  *survived* does not hold: an outcome reading needs its contrast pair, and this
  report pairs blue with terracotta, not blue with gray — gray is the absent, not
  the good outcome.
- **`check_numbers.py` was green for the wrong reason.** The §9 table packs seven
  logical rows into two physical lines, `pointed_modules` used a ±2-line window,
  and `match_pointed` iterated `sorted(pointed)` and stopped at the first
  rounding match. That is alphabetical order, not semantics: the module 04
  `3,5%` was credited to module 01's `0,03542`, the local slope of a dose curve,
  and six of the seven table numbers matched in more than one module. The line
  carrying the token now wins over the window — the nearest pointer to the left
  governs, which in a table is the one on the same logical row — and
  `HaystackValue` names the notebook, so `[c6]` became
  `[srag_model_internals c6]` and a suspicious match can be audited without
  re-deriving the search. Five new `--self-test` cases (32 checks), including
  the table case and a non-regression for running prose.
- **The observed outcome that disarms "the vaccine kills" is now measured.** §5
  of module 05 explained the positive φ on doses only by collinearity — true, but
  a statement about the *estimator*, which leaves the wrong reading standing for
  anyone who looks at the panel and skips the paragraph. The cell now prints what
  no cell in the repository measured: post-campaign, **within each age band**,
  observed lethality falls monotonically as doses rise (85+: 53,6% at zero doses
  against 24,3% at five; 60–74: 40,1% against 18,7%). Positive φ and falling
  lethality coexist because the model credits the dose count with the risk of
  *whom the campaign prioritised* — confounding by indication, named at last.
- **The §9 table gained a denominators column**, now that attribution is
  trustworthy: the fractions range over a hundred candidates to a quarter-million
  rows and were never comparable to each other. Module 01's cell 15 prints the
  denominator it had always assumed.
- **Protocol.** Three walkthroughs re-run on a clean kernel. Of the 11 module
  figures, exactly 3 moved and the other 8 are byte-identical; `cf` did not move
  a single stdout line and `ice` moved only the new block. `gerar_figuras.py
  --so cp` then returned 0 with `cp_passo_1b_modelos.png` byte-identical, which
  is what makes "only figure 9 changed" a measurement rather than a claim.

## 2026-09-04 — the report reviewed: theory checked against the sources, figures legible, layout without holes

- **Twelve statements of theory corrected in `reports/01-metodos-locais/main.typ`**,
  each checked against its source (Molnar ch. 12, 13, 14, 15, 17, 18; Wachter et
  al. 2018; Slack et al. 2020; Lundberg & Lee 2017; Lundberg et al. 2020) before
  the sentence was rewritten. The ones that changed a claim: the logistic
  profile is the same S-curve *slid along the axis* by the rest of the record,
  not "the same curve at another height" (in probability space height and
  slope both move); a step height belongs to the grid only while the grid is
  coarse, and belongs to the model once refining stops moving it (module 01
  measured exactly that: 0,1387 → 0,0852, then no further); TreeSHAP walks the
  trees, so §1's "does not walk trees" now names the one declared exception
  (KernelSHAP is the agnostic form); the calendar variable is **19th of 40 by
  `gain`**, the middle of the table, not "among the last" (two places); the §9
  table separates *cohort exposure* (module 01 rows) from *method fiction*
  (modules 02–05); the temporal split is justified by what a shuffle would
  hide, not by "teaching the model the year" it already receives as a feature;
  the drift reappears in five *places* (base, calibration, ICE, SHAP,
  counterfactuals), not in "the five methods"; Slack et al. (2020) is cited for
  the scaffolding attack; the five counterfactual criteria are credited to
  Molnar's chapter and the loss to Wachter; φ is an average over orderings,
  not "given the rest of the patient"; d-ICE is a finite difference on the
  grid; "four rules" and "three fences" are reconciled; the ICE test reads "no
  interaction *in the fitted model*"; the path-dependent TreeSHAP has its
  price named too (credit to a feature the model does not use).
- **Module 01 carried two of those sentences** (README, `lecture/outline.md`,
  and markdown cells 0, 5, 7, 10 and 28 of `cp_walkthrough.ipynb`); corrected in
  the same wording. The notebook was re-run fresh-kernel under the protocol:
  every PNG byte-identical, every printed value identical; only the kernel's
  segmentation of stdout blocks around four figure cells differs, which moves
  between runs and carries no content.
- **Figures you can read.** The module figures are 9,6–12 in wide and the
  article column is 170 mm, so tick labels printed at 4,2–5,2 pt.
  `tools/sapians.py` gains an opt-in knob, `SAPIANS_ESCALA_TEXTO`, that scales
  the style's font sizes and is inert when unset (proved: `cp_walkthrough`
  re-run without it reproduces the committed PNGs byte for byte).
  `reports/01-metodos-locais/gerar_figuras.py` re-executes the five
  walkthroughs off-tree at 1,5 (1,35 for modules 01 and 05, where 1,5 clipped a
  tick or a label), crops the in-image headline as before and writes the seven
  PNGs to `figuras/` in 68 s; `shap_passo_5_dependencia` stays at notebook
  scale because its vertical colorbar label does not fit the canvas at any
  larger scale. Notebooks and `modules/*/figures/` untouched.
- **Layout.** The model-selection diagram, drawn but never used, becomes
  Figura 1 in §2; the orphan "journey" diagram is deleted. `sp-tab` is now
  breakable with a repeating header, so an unbreakable table can no longer
  leave a third of a column empty as the §9 table did on the old page 7.
  Headings are sticky blocks again: the custom `show heading` rule had dropped
  Typst's keep-with-next, and a heading could sit alone at the foot of a
  column. The four footnotes that lived inside figure captions moved into the
  body sentences they support, because a footnote inside a float lands on the
  page after its figure and breaks the numbering order. The three-bar figure
  sits at 85 % width; the diagram boxes use the package tokens (`radius-sm`,
  `stroke-light`, `stroke-accent`). Still 9 pages. `check_numbers.py
  --prose`: **56 numbers, 56 traced, zero exemptions**.
- **Docs caught up with the code**: the report README's file table, figure
  pipeline, dates and the phantom "Anexo A"; `reports/README.md`;
  `figuras/README.md`; `tools/README.md`; the exemption file's header and its
  stale "139 numbers".

## 2026-09-03 — the course report, rewritten to teach

- **`report/` enters git.** The Typst source, the `.bib`, the exemption file
  and the compiled PDF had lived only in the worktree, untracked; a `git
  clean` would have deleted the work. Committed as-is first, so the rewrite
  below is diffable.
- **The report was written as proof, not as a lesson.** The repository's hard
  rule (every number in prose is printed by a versioned cell, and the sentence
  names the module) had become a *prose style*: 7.097 words carrying ~150
  numbers, 133 module pointers and 91 em dashes — one number or pointer every
  line and a half. The owner, who did the work, could not read it: he read
  `"200 pacientes, 40 por ano, semente 42"` as *"somente 42"*, because
  "semente" was never explained.
- **Pointers moved into footnotes, and the evidence bar still holds.**
  `check_numbers.py --prose` needs a `módulo 0N` within two lines of each
  number, and its `_strip_typ` leaves `#footnote[...]` intact — so the checker
  reads the source while the reader reads the PDF. Result: **139 numbers, 139
  traced to a cell, zero exemptions**, against 11 exemptions before.
- **Three writing rules**, applied by six agents over one style contract: no
  term before the sentence that defines it; every paragraph carries a claim and
  its consequence; no `(módulo NN, §N)` left in the body. Em dashes went from
  91 to **0**; the body from 7.097 to 5.973 words; the report proper now ends
  on page 10.
- **Appendices A, B and C** — the repository explained directory by directory,
  a traceability table from claim to notebook cell, and the three code
  fragments that actually decide something (`gate_impossible`, the LIME
  prediction wrapper that rounds in silence, `pred_contribs`).
- **`report/figuras.typ` — three diagrams drawn in Typst.** The module SVGs
  were made for the README (Georgia serif, beige ground, 1180×816 landscape)
  and landed on the page as a rectangle of foreign typography. Redrawn with
  the sapians tokens, and with no numbers inside the drawing: the figure
  teaches the mechanism, the numbers stay in the prose.
- **The masthead names the course.** `sapians:0.1.0` hard-codes "SAPIANS
  RESEARCH ARTICLE" and a journal name in the footer; `@preview/sapians:0.3.0`
  exposes `kicker`, `journal` and `lang`. The report now says *SCC5819 ·
  Tópicos em Inteligência Artificial* over *ICMC-USP*.
- Bibliography pruned from 22 entries to the 15 that carry an argument; the
  five "what the book says" cards and the five question blocks that repeated
  their own section title were removed.
- **Second pass, on beauty, against journal practice.** The footnote apparatus
  was eating ~20% of some pages: 63 notes over 10 pages, many of them bare
  addresses (`Módulo 00, MODEL.md.`). The rule applied: *a number whose only
  justification is a file address is a number not earning its place in the
  prose*, so cutting the note means cutting the number. Notes went **63 → 16**
  and numbers **139 → 52**, still 52/52 traced and still zero exemptions. A
  third option turned up beside "note" and "cut": the pointer written into the
  sentence itself ("O escolhido, pela regra do módulo 00, é um homem de 90
  anos…"), which satisfies the checker and reads as prose — §3 now carries no
  footnote at all.
- **Journal typography.** Tables in booktabs (rules top, under the header and
  at the foot; no verticals, no grid, no shaded header) as in IEEE, Elsevier
  and ACM. Captions at 7,6 pt, left-aligned, with a bold "Figura N." label.
  First-line paragraph indent instead of inter-paragraph space, none on the
  paragraph opening a section. Heading hierarchy fixed: level-2 headings were
  set at 8,4 pt, *smaller than the 9 pt body*.
- **Figures lost their internal titles.** The module figures carry a kicker
  (`§1 · O FEIXE`) and a headline with the finding baked into the image —
  right for a notebook, wrong for an article, where it duplicates the caption
  ("Aos 80 anos o feixe vale 0,481 em 2020 e 0,303 em 2024" repeated what
  Figura 3 said below it). `report/recortar_figuras.py` finds the largest
  whitespace gap in the top third — always the space between headline and plot
  — and cuts there: 13–14% of the height on all seven. Panel labels (A, B,
  C...) stay, because an article does use those. Module figures untouched;
  `report/figuras/` is derived and reproducible.
- **Appendices A, B and C removed**, and figures 9 and 10 with them; the
  repository became one footnote in the opening, which is what it needed to be.
- Bibliography now **8 entries**, each naming the origin of a method or
  carrying the PROBAST criterion that excludes ICU and ventilation.
- **10 → 9 pages.**
- **`report/` became `reports/01-metodos-locais/`.** A report is a written
  deliverable built on top of the modules: it reads the notebooks, cites their
  measurements and argues something with them, and measures nothing of its
  own. The plural directory, numbered sequentially like `modules/`, gives the
  next one somewhere to go. `reports/README.md` states the extra clause the
  evidence bar needs outside `modules/`: the sentence carrying a number must
  name its module, so the checker knows where to look.

## 2026-09-02 — the SAPIANS house style in the seventeen notebooks; every printed number in Portuguese

- **`tools/sapians.py` — the SAPIANS identity, in one import.** The colours,
  palettes, line styles, three figure sizes and the Portuguese number
  formatters (`pt`, `pt_int`, `pct`, `pt_sig`, `tabela`) the seventeen
  notebooks will share, copied verbatim from `sapians-latex @ 4c10f27`
  (`tokens.typ`, `sapians.mplstyle`, `sapians_plots/theme.py`) with the
  figure conventions of its `make_figures.py`. The rule it encodes is one
  colour, one meaning across the whole course: a student who learned
  "terracota = óbito" in module 01 reads the terracotta bar of module 05 the
  same way. `tools/sapians.mplstyle` carries exactly three marked deltas from
  the brand file (`figure.dpi: 100`, `savefig.dpi: 150`,
  `figure.autolayout: False`), all because the target here is the PNG
  embedded in a committed `.ipynb` rather than a slide PDF.
- **Fonts are bundled** in `tools/fonts/` (four Inter weights 4.000, two
  JetBrains Mono 2.304, ~2.1 MB, OFL-1.1 with both licence texts). Not a
  preference: Linux CI and Colab have no Inter, matplotlib falls back to
  DejaVu Sans without an error, and every glyph moves. Registered by absolute
  path, `SP.aplicar()` fails loudly instead. Measured: the same figure saved
  twice is byte-identical (`metadata={"Software": None}` drops matplotlib's
  version stamp from the PNG).
- **CONTRIBUTING gains "O esqueleto do caderno"** — the shape every notebook
  keeps: brand cell, `SP.aplicar()` setup, `## §N — título` headers whose
  numbers never change, the four-beat section rhythm ending in "O que olhar",
  one "O que o livro diz", a `## Fechamento`, and every printed number in
  Portuguese. `check_notebooks.py` will grow checks for it.
- **Publication downstream is suspended** (owner's decision, recorded in
  CLAUDE.md): `scc5819/interpretable-ml-lectures` keeps `modules/14-lime`
  frozen in its BCW-era English form until the class actually uses the repo.
  The procedure stays written, marked inactive.
- **The seventeen notebooks, one skeleton.** Every notebook opens with the
  typographic brand cell (`**SAPIANS** · SCC5819 · MÓDULO NN — … · MOLNAR,
  CAP. N`, H1, one tie-in sentence, a links line), keeps its section
  numbers but writes them `## §N — título` (the three notations `## N.`,
  `## Passo N —`, `## §N —` are gone; module 00's `## N.` too), closes the
  method modules with `## Fechamento — …` (the two English `## Summary`
  included) and ends with a short-form references cell. Each figure section
  now carries an "O que olhar" block tied to numbers the cell prints.
- **One colour, one meaning, across 01–05.** The per-notebook colour
  dictionaries that disagreed with each other are gone: impossível /
  óbito / φ>0 / fabricado = terracota, válido / possível = sálvia, sobrevida
  / φ<0 / the course model = azul, the second arm of a comparison that is
  not about class (logística, rodada ingênua, interventional) = âmbar, the
  model's own objects (fronteira, ✕ do paciente, PDP) = escuro, year = a
  blue intensity ramp (2020 darkest), module 04's move families = tones
  keyed by `GRUPO_DE_FEATURE`. The 25 figures were regenerated at the three
  slide-slot sizes with active-insight titles and a `§N · nome` kicker;
  file names unchanged. Two figure bugs fell out: module 05's colorbar sat
  on top of its right panel, and module 04's legend overlapped its bars.
- **All outputs in Portuguese.** `SP.pt` / `pt_int` / `pct` / `pt_sig` /
  `tabela` replace the English f-strings in all ten method notebooks (≈240
  sites) and the module-00 notebooks; axis ticks too (`SP.salvar` formats
  them where the default formatter is in use). Years, `gold_id` and codes
  keep no thousands separator. One notebook's `.replace(",", ".")` had been
  rewriting the punctuation of a printed sentence — gone. Each module lands
  as two commits, skeleton then formatting, and the formatting commit's
  output diff is separators only: **no measurement moved** (the checker
  below reports MISS 0 on every module before and after).
- **Module 00's seven notebooks** get the brand cell and the `## §N —`
  notation (52 headers, same numbers — the module README already pointed
  with `§N`) and Portuguese outputs (150 sites, 52 of them tables), with the
  private Bronze and Gold present: no internals branch degraded to PULADO.
  Two things surfaced and are recorded rather than fixed: four of these
  notebooks print wall-clock fit times into committed outputs (an old,
  non-deterministic habit — `420` had been passing the number checker only
  by coinciding with a `4.2 s` clock reading), and module 00's measurements
  that come from the pipeline generators rather than from a cell (COLUMNS.md,
  MANIFEST.md) now live in its exemption file with that reason.
- **`tools/check_numbers.py`** — the prose↔cell checker that enforced the
  hard rule in the 01–05 re-sync, promoted from the scratchpad: every
  numeric token in README, outline (and markdown cells) must be printed by a
  code cell of the module (or of a sibling module named in a nearby
  "módulo 0N" pointer); reads outputs in both number conventions;
  per-module exemption files with reasons in `tools/check_numbers_exempt/`;
  `--self-test`, `--dump`. Run by hand, not a hook.
- **`tools/check_notebooks.py`** now also checks the skeleton: the brand
  kicker on the first markdown cell, no `## Passo N` / `## N.` headers, and
  exactly one `## Fechamento` outside module 00.

## 2026-09-02 — modules 01–05 re-synced onto the chosen model; `tools/` numbered by phase

- **The conditioning change, said once.** PR #29 adopted the tuned course
  model (400 trees / depth 5 / lr 0.08 → **800 / 4 / 0.05**, min_child_weight
  100, reg_lambda 5.0; sample test AUC 0.7575 → 0.7644, Brier 0.1326 →
  0.1308) and moved the rule-picked exemplar (gold_id 1269214 → 1276776) and
  the 2021 patient (770295 → 834192). The five method modules had been built
  on the previous model and cited its numbers. All ten notebooks were re-run
  from a fresh kernel and every prose number re-synced against its printing
  cell. Evidence-bar rule 3 applied in two tiers, as decided by the owner:
  one collective conditioning note per module ("the numbers are from the
  model adopted 2026-09-01; the previous version measured on 400/5, and the
  exemplar was another patient"), and an individual "it said X, it measures
  Y" record for every claim the measurement actually falsified.
- **01-ceteris-paribus:** four claims fell. The amplitude never moved with
  the grid (0.4809 at all four steps; only the step size does, 0.1387 →
  0.0852 — the old "0.288 → 0.331" was the previous model's); the logistic
  ramp is not the more aggressive one (staircase 0.481 vs ramp 0.397, the
  reverse of what the page said); "XGBoost descends on doses" was reading
  the endpoint, not the patient (it rises to the second dose; local slope
  +0.03542); and the Gower numbers had never matched the committed cell
  even before the model change (prose 0.043 / 0.130 / 0.005 vs printed
  0.0491 / 0.1364 / 0.0046; now 0.0037 / 0.1287 / 0.0046). Two citation
  fixes (the outline's stale AUC 0.7575; a full-base pointer that said
  internals §6 and meant §5). New template-mandated "why" section, backed
  by a metrics print in the walkthrough setup.
- **02-ice:** nothing fell. The bundle stratifies by regime even more (at
  age 80: 0.481 in 2020 vs 0.303 in 2024, PDP 0.400), the fence counts are
  identical under both models (0/10,200; 252/1,400; 54%) — the fence is the
  base's, not the model's, now measured twice. Lethality 31.4% → 18.2% is
  printed locally instead of cited without a cell. New "why" section.
- **03-lime:** four claims fell, stacked on the two corrections the page
  already carried. Declaring the categoricals now raises R² (0.50 → 0.65)
  AND lowers the patient error (0.046 → 0.008); the top-5 is identical
  across ten seeds (Jaccard 1.00, was 0.83 / min 0.43 — the instability
  moved to the top-10 tail and returns with 1,000-point clouds); the CP↔LIME
  bridge agrees on all three directed numerics, doses by a hair; the feature
  whose point slope flips sign is doses, not age. Stale module-00 AUCs
  (0.7575 / 0.7674 / 0.7926) replaced by the printed 0.7644 and pointered
  0.7680 / 0.7890. `lime_internals_kernel.png`, generated since the module
  was born and never promoted, is now committed. The frozen decks are
  untouched, as policy requires.
- **04-counterfactual:** the "p ≈ 0.8" rule now lands on a 32-year-old
  (gold_id 1266990), and eight claims fell with the change of subject: the
  best single move is `saturacao → nao` (p 0.793 → 0.571), not "rejuvenate
  71 years"; no single move crosses 0.5 any more; the Rashomon stories are
  others (0.199 / 0.316 / 0.452 among 68 valid candidates, was 151);
  raising doses leaves p at 0.793 instead of raising it; actionable
  coverage 36% → 30.3% of 624; and in the p ≥ 0.7 band it is not "almost
  nobody" (3% of 62) but nobody (0% of 19). New finding written into the
  material: the pair `meses → 6` + `doses → 0` clears the pre-campaign fence
  that the single move `meses → 6` cannot — plausibility is decided on the
  whole candidate. Unchanged: 113 moves / 6,129 pairs, 3.5% invalid vs the
  LIME's 30.6%, Gower 0.0042.
- **05-shap:** one claim fell — `meses` is 3rd by mean|SHAP| and **19th** by
  gain (was 16th; the gap that carries the regime-drift argument grew).
  Everything keyed to the exemplar moved with him (φ(age) +0.92, vaccination
  −0.36, force +1.86 / −1.07); "7/8 signs agree with LIME" survived and is
  recomputed here, so module 03 follows 05; hybrid rows 23.1% impossible
  (gate 15.4%, pre-campaign 8.2%); efficiency 1.05×10⁻⁵ over the whole test.
  The outline's "above 70" was a read off the figure and became the printed
  78–90 window.
- **Cross-module citations reconciled with no edits needed:** module 01's
  79.6% (cited by 03), module 03's 30.6% (cited by 04) and module 05's 7/8
  are all unchanged under the new model; module 05's dose attribution, which
  01 and 04 point to, kept its sign (+0.08 at 3+ doses, was +0.16).
- **tools, renamed by phase (decided 2026-09-01, applied now):**
  `srag_10_fetch` / `srag_11_fetch_ibge`, `srag_20_profile` /
  `srag_21_dictionary` / `srag_22_quality`, `srag_30_silver` /
  `srag_31_columns` / `srag_32_diagrams`, `srag_40_gold`, `srag_50_selection`,
  `srag_60_model` — tens = layer, units = order inside it, so a future
  insertion renumbers nothing. New phase **70**, `srag_70_explain.py`: the
  kernels the modules copied cell by cell (`perfil_cp`, `curvas_ice`, the
  Gower family), with the walkthroughs showing the source via
  `inspect.getsource` — one definition, the student still reads the code.
  `srag_60_model.py` gains the four categorical families as slices with a
  partition assert (`DEMOGRAFIA` / `COMORBIDADES` / `SINTOMAS` / `CONTEXTO`),
  `GRUPO_DE_FEATURE`, `gate_reasons()` (the same three fences, one column
  each; `gate_impossible` is their OR) and `pick_vulneravel()` (the second
  patient's rule, previously re-derived inline in three notebooks). All
  measured bit-identical against the inline versions before deletion. The
  notebooks' repo sentinel moved to `tools/README.md`: with a script name, a
  missed rename fell through to the Colab `git clone` of `main` and imported
  the OLD module with green CI. `srag_40_gold --manifest` added; generated
  files changed only in their header line; PROFILE.json and the SVGs
  byte-identical. `tools/README.md` now carries the runnable sequence 10 → 70.
- **docs:** the root README, `modules/README.md`, CONTRIBUTING's shared-setup
  paragraph, `CITATION.cff`'s abstract and ROADMAP's legend still described
  the Breast Cancer Wisconsin / RandomForest / patient #67 era; they now
  describe the SRAG/COVID course model and list modules 04 and 05.
- **00-dataset (docker):** `load.py` now loads the **Ouro** as well, so the
  local Postgres carries the whole medallion: `gold.covid_obito` (1,282,970
  rows, indexed on `gold_id`/`split`/`ano_onset`) when the private parquet is
  there, plus `gold.amostra` and seven documentation tables built from the
  committed `counts.json`/`model_metrics.json` — `gold.dicionario` (one row
  per Gold column: papel, família, dtype, origem, the official SIVEP label
  and domain parsed out of `DICTIONARY.md`, the domain **measured** in the
  Gold, and the definition), `funil`, `decisoes`, `modelo`, `exemplar`,
  `xgb_params`, `impossibilidades`. The dictionary sits beside the data, the
  way `silver.contrato` already does. A `--only-gold` flag skips Bronze and
  Prata, and every run starts by dropping whatever is left in `silver`/`gold`
  from older loader versions (the per-year `silver.srag_20xx` /
  `silver.quarentena_20xx` the single table retired — 12 of them on the
  owner's machine). Measuring the domains falsified one sentence written
  from the code: `n_crit2`/`n_crit3` cannot be 0 in the Gold, because the
  cohort funnel already demands at least one criterion of each — minimum 1,
  not 0. Two loader bugs fell out of the re-runs, both only visible on a
  second run: `DROP VIEW IF EXISTS silver.srag` aborts once `silver.srag` is
  a table (Postgres refuses the wrong object kind), and — the silent one —
  dropping a table through `postgres_execute` goes around the catalog DuckDB
  caches at ATTACH, so the next `CREATE TABLE … AS SELECT` builds the table
  with the right 420 columns and **zero rows**, no error (measured
  2026-09-02: 240,290 → 0 → 240,290 on the same parquet). Every DROP now
  goes through DuckDB, and picks VIEW or TABLE from `information_schema`.
  Stale pointer `tools/fetch_srag.sh` → `tools/srag_10_fetch.sh`.

## 2026-09-01 — why `UTI` and `SUPORT_VEN` stay out: measured, referenced, decided

- **00-dataset:** the course owner asked the right question — ICU admission and
  ventilatory support are the strongest clinical predictors in the file, so why
  are they not features? Three consulted perspectives (prediction-model
  methodology, SIVEP-Gripe literature, intensive care) and a measurement
  converged, and the repo now says so instead of assuming it. Measured on the
  committed sample with the adopted params (model internals, new final
  section): adding `UTI`+`SUPORT_VEN` to the 40 lifts test AUC 0.7644 → 0.8514
  (+0.087, 22.6 paired-bootstrap SE), `SUPORT_VEN` alone carrying ~half the
  gain — because invasive ventilation has 76% lethality in the training split
  (Ranzani et al. 2021 measured 80% nationally). The field is an episode
  summary ("O paciente *fez uso* de suporte ventilatório?", no timestamp,
  filled at closure per the Ministry's guide), so a model with it answers "who
  died?" rather than "who will die?" — PROBAST signalling question 2.3 and
  TRIPOD+AI item 9b name the criterion; the 4C Mortality Score (admission-time
  predictors only) validates at AUROC 0.767, the band the course model sits in.
  The Brazilian literature is split (Silva & Silva Neto 2022 keep them with
  importance 0.46; Baqui 2021 and ABC2-SPH exclude them, the latter
  substituting SpO2/FiO2 at presentation). Decision, recorded: the course
  model keeps the 40; no second model "just for a higher AUC". GOLD.md
  decisão 3 gains the full justification with references; MODEL.md's declared
  limits gain the line; README points to it.

## 2026-09-01 — the seam audited, the CI scoped, the journey drawn

- **tools:** a full audit of `srag_model.py` × `srag_selection.py` found the
  seam between "the adopted model" and "the study that chose it" underguarded,
  and closed it: `--check-card` now also compares the live `XGB_PARAMS`
  against `model_metrics.json` (hand-editing `random_state` used to pass every
  guard — verified by tampering); the rule-8 consequence record now covers all
  five tuned keys, not three (a future study differing only in
  `min_child_weight`/`reg_lambda` would have printed "confirms" falsely); and
  `pick_model`'s tie test gained the right bootstrap reference (the old code
  measured ties against the bootstrap leader, whose own `delta_ep` is 0 by
  construction — dormant today, latent for any future study). Plus: sha256
  recipe delegated to `srag_gold` (was a verbatim copy), missing-JSON guards
  on both card CLIs, an empty `MELHORES` now fails the check. The larger
  refactors (naming the `CATEGORICAS[5:18]` comorbidity slice used by five
  notebooks, `gate_reasons()`, shared `ece`) are queued for the 01–05 re-sync.
- **ci:** notebooks are now scoped per PR — a PR executes only the touched
  modules' walkthroughs/internals (tools/requirements/.github changes widen to
  all; push to main and the weekly run still sweep everything). Measured on
  the runner before scoping: 539 s of walkthroughs on EVERY PR (selection
  175 s, shap 138 s) and 879 s of internals when triggered. A docs-only PR
  now waits ~1.5 min instead of ~10. The selection walkthrough's §2 also
  slimmed: the k-fold trap reproduces ONE configuration live (checked against
  the committed record at 4 decimals) and reads the full table from
  `selection_metrics.json` — 24 fits → 6, 82 s → 28 s locally, same lesson.
- **00-dataset:** the module's visual layer caught up with the journey.
  `PIPELINE.svg` v2 shows all five stages (Bronze → Silver → Gold, solid and
  dated → selection study → course model) with every number read from the
  committed JSONs; the hardcoded "~2.2 GB" (no printing cell) is gone. New
  `SELECTION.svg`: the temporal protocol with the anti-test barrier, and the
  validation leaderboard with the visibly-empty 1-SE tie band and the test
  diamond at 0.7644. `srag_diagrams.py --check` finally gets its pre-commit
  hook (it was the only checker without one). README tightened onto the new
  visuals.
- **tools naming, decided:** the scripts get phase-numbered names
  (`srag_10_fetch` … `srag_60_model`) at the 01–05 re-sync PR, where the
  forced full notebook re-run is already being paid; recorded in
  `tools/README.md`.

## 2026-09-01 — the course model is chosen by protocol, and the model changed

- **00-dataset:** `tools/srag_selection.py` — the pre-registered selection
  study. Six candidates (Dummy, linear-probability model, logistic, decision
  tree, random forest, XGBoost — GAM/rules/RuleFit deliberately deferred to
  their own chapter modules), three declared design matrices, tuning on
  train, selection on val-2023, test-2024 read ONCE by a function that
  raises on test rows. The pre-registration commit precedes the search
  commit in git; the criterion is printed before any number.
- Measured: tuned XGBoost wins val AUC 0.7564 with no candidate within one
  paired-bootstrap SE of the leader (forest 0.7403, gap 0.0160 vs SE
  0.0018); the registered hypothesis (≥0.02 over logistic, ≥0.01 over
  forest) confirmed at +0.035/+0.016. The traps, measured rather than
  asserted: shuffled 5-fold would pick max_depth=7 where temporal
  validation picks 5 (inflation +0.0038..+0.0114); the LPM predicts
  outside [0,1] for 20.7% of validation; retraining on train+val would
  score 0.7700 on test and is refused by protocol; the factory-default
  forest fits 11,222,316 nodes with ECE 0.1004; one-hot costs the tree
  0.0074 AUC vs ordinal codes; subsample=1.0 buys bit-identical
  predictions across seeds for 0.31 SE of AUC.
- **The course model changed** (rule 8 of the criterion, written before
  measuring): XGB_PARAMS is now 800 trees, depth 4, lr 0.05,
  min_child_weight 100, reg_lambda 5.0 — test AUC 0.7575 → 0.7644, Brier
  0.1326 → 0.1308; the sampling price fell from −0.0099 to −0.0036; the
  rule-picked exemplar moved to gold_id 1276776 (and the 2021 patient to
  834192). `srag_model.py --metrics` makes model_metrics.json regenerable
  (verified byte-identical under the old params before adopting the new).
  PENDING, registered: ALL five method modules (01-05 — 03/04/05
  landed on main while this study was in flight) were built on the
  previous model and cite its numbers; their re-run and prose re-sync
  is a later PR.
- Evidence and cards: `gold/selection_metrics.json` + generated
  `SELECTION.md`; two new local hooks (model-card-generated,
  selection-card-generated) wire the existing `--check-card` modes into
  pre-commit; two new notebooks (`srag_selection_walkthrough`, every PR;
  `srag_selection_internals`, weekly) reproduce the cheap arms live and
  assert equality with the committed record (1e-3 tolerance for the
  cross-platform third-decimal drift ci.yml documents).
- **modules/00-dataset/README.md rewritten end to end** as the full
  professional journey (acquisition → profiling → regimes → shape →
  empty-states → derived → contract → audit → the Silver/Gold hinge → five
  task decisions → model selection → the course model), each stage carrying
  the named industry default and the measured trap. One prose claim fell in
  the rewrite and is registered as corrected: only ONE rejected gate is
  contradicted 100% of the time, not two.

## 2026-09-01 — modules 01/02 didactic pass: the chapter's readings, and fig. 12.5

- **01-ceteris-paribus** and **02-ice** raised to the course
  documentation standard and wired to Molnar chs. 12–13: method cells
  with the chapters' definitions quoted, per-figure "what to look for"
  paragraphs, "what the book says" tables mapping each chapter warning
  to this base's measurement, and closings that return the opening
  question. One new canonical figure in 01 (the book's fig. 12.5): the
  same CP profile drawn on both course models — the logistic ramp is
  MORE aggressive than the staircase (amplitude 0.718 vs 0.330 on age;
  no interactions means the global coefficient hits everyone), and on
  doses the two models disagree in DIRECTION (the logistic rises,
  carrying the who-got-vaccinated confounding; the XGBoost drifts
  down) — the thread module 05's dependence plot picks up.
- ICE's markdown now reads the bundle exactly as ch. 13 prescribes: the
  "same course?" interaction test (it fails on purpose — that is the
  finding), c-ICE "easier to compare", d-ICE "spot ranges", and the
  declared 200-patient rule as the overcrowding answer. READMEs and
  outlines rebuilt on the template (objections to anticipate,
  discussion prompts, annotated references incl. Goldstein et al. 2015).
## 2026-09-01 — module 04 didactic pass: Molnar's tables, the Rashomon effect, Wachter enumerated

- **04-counterfactual** raised to the course documentation standard AND
  to Molnar ch. 15: counterfactuals now presented as the chapter's
  feature/original/counterfactual tables; the five criteria (validity,
  proximity, sparsity, plausibility, diversity) mapped one-by-one to
  their operationalizations, plus the module's sixth — actionability;
  Wachter's loss written term-by-term with the walkthrough's scatter
  reframed as the loss ENUMERATED (no λ to pick: the whole
  validity×proximity cloud is shown); and the Rashomon effect made
  concrete — from the 151 valid crossers, three feature-disjoint
  stories printed side by side (become a child without
  immunosuppression, p→0.18; erase the low saturation and the race
  record, p→0.34; be recorded as a pregnancy of unknown gestational
  age at 81, p→0.40) with the chapter's warning quoted.
- Walkthrough markdown on the BCW template (objectives, symbol table,
  per-figure "what to look for", "what the book says" with the
  strengths quote and its measured caveat — no assumptions in the
  method pushes the assumptions into the search-space design, where
  they are visible); README/outline rebuilt to match, with annotated
  references (Wachter 2018; Dandl et al. 2020 as the plan B; DiCE
  cited-not-run with the pin decision).
## 2026-09-01 — module 05 didactic pass: the classic SHAP plots, and the chapter

- **05-shap** rebuilt to the course documentation standard AND to Molnar
  chs. 17-18: the five classic plots — waterfall, force, beeswarm+bar,
  dependence — now exist in pure matplotlib over `pred_contribs`, each
  with the book's prescribed reading and one measurement the book does
  not make. New teaching moments, all printed: the dependence trap
  (φ(doses) POSITIVE among the vaccinated — misreading no. 3 of ch. 17
  in the flesh, disarmed with module 04's measured counterfactual); the
  age curve splitting into two era bands (+0.91 pre-mar/2022 vs +0.69
  after, ages 78-90); no dark-blue pre-campaign points outside doses=0
  (real data respects the fence module 03's neighbours violated); the
  dummy axiom tested and reported as honestly vacuous (all 40 features
  split somewhere). Dependence plots use the full sample and say so —
  the test split alone covers only 2024 and the interaction is between
  eras.
- Walkthrough markdown raised to the BCW template (Shapley game/gain
  symbol table, four axioms with ch.-17 quotes, per-figure "what to
  look for", a "what the book says" table, the closing five-module
  arc); README/outline rebuilt to match, with annotated references
  incl. Štrumbelj & Kononenko (2014) for the permutation estimator.

## 2026-09-01 — module 03 regains the six-step figure and the documentation standard

- The A–F step-by-step figure of the BCW era — the module's most didactic
  asset — is rebuilt on the COVID model as walkthrough §0: the plane is a
  real ceteris-paribus slice (idade × meses, 38 features frozen on the
  patient), and the figure itself prints the three surprises the module
  then counts (the cloud is centred 5.7 SDs away from the patient, 0.1%
  of neighbours carry weight > 0.1, the line is fitted in that desert).
- The walkthrough markdown is raised to the BCW documentation standard:
  the objective in LaTeX with a symbol table instantiated for this model,
  justified patient/axis choices, a drawing-tools cell, per-figure "what
  to look for" paragraphs, a "what the book says" cell mapping Molnar's
  ch. 14 limitations to this module's measurements, and a closing that
  returns the opening question. README and outline rebuilt to the same
  template (findings with provenance, literature map, annotated
  references, objections to anticipate).
## 2026-09-01 — modules 04 (counterfactuals) and 05 (SHAP): the course arc is complete

- **04-counterfactual** (new, Molnar ch. 15): exhaustive hand-rolled
  search, no DiCE (declared: its published version does not resolve
  against the pinned numpy 2.x). The lesson is the three distinct
  filters — exists (gate), close (Gower), reachable (declared levers):
  free search answers "become 71 years younger" (p 0.804→0.480), 151
  depth-2 candidates cross 0.5 "validly" while being absurd
  prescriptions, and with real levers **64% of the 902 high-risk test
  patients have no actionable counterfactual at all** (97% in the
  p≥0.7 stratum). Internals: the full pair space confirms the
  walkthrough optimum; the funnel gate is one-directional in the real
  data (0.54% declare a risk factor without naming a comorbidity).
- **05-shap** (new, chs. 17–18): exact TreeSHAP via native
  `pred_contribs` (the `shap` library stays out — pinned-stack
  resolution decision recorded in the pin PR). Sum-to-margin exact
  (7.6e-6 max), bit-identical across refits, sigmoid(sum)=p digit for
  digit; 7/8 sign agreement with LIME on the same patient (the one
  divergence is the module-03 "flat in CP" feature); hand-rolled
  permutation Shapley shows path vs interventional diverging where
  correlations live — and the 2,460 hybrid rows the interventional
  evaluates are **26.3% impossible** by the same `gate_impossible`.
  The five-module arc closes on the question it opened with: who are
  the rows the method feeds the model?
- Root README module table and ROADMAP statuses flipped (12–15, 17–18
  done); ci.yml timing comments extended with the measured cf/shap
  costs.

## 2026-09-01 — module 03 (LIME) rewritten onto the COVID model

- **03-lime** completes the CP → ICE → LIME arc on the course model (BCW
  version in git history). The module is two runs with the same patient:
  naive (no `categorical_features`: 4,999/5,000 synthetic neighbours
  carry a fabricated encoding — the prediction wrapper's silent rounding
  gets a counter) and correct (0 fabricated — and the JOINT fences
  remain: 30.6% impossible neighbours for the rule patient, 79.2% for
  the vulnerable one, same `gate_impossible` as modules 00–02). Measured
  surprises kept as lessons: the two patients' clouds are IDENTICAL
  (the Gaussian is centred on the training mean, verified against the
  pinned lime source), the generator erases the meses×doses correlation
  (+0.61 real → −0.00 synthetic), the respectable knobs rescue one
  patient by geography and worsen the other, a narrow kernel yields the
  perfect empty explanation (R² 0.00, error 0.00), and the CP↔LIME
  bridge only works regionally — the pointwise staircase slope flips
  sign with step size.
- ci.yml timing comments re-measured after the rewrite (lime_internals
  283.8 s → 50 s: the module now runs on the committed sample, no
  network).

## 2026-09-01 — modules 01 and 02 rewritten onto the COVID model

- **01-ceteris-paribus** and **02-ice** now run on the course model (the
  BCW versions live in git history, pointed to from each README). The
  substantive change is announced, not hidden: impossibility moved from
  an empirical envelope to DERIVABLE fences (the funnel gate at 0.00%
  over six years, the vaccination calendar, the cohort definition),
  counted by the shared `gate_impossible` so modules print identical
  numbers by construction.
- Measured teaching moments that replaced the BCW ones: whether a sweep
  is fiction depends on WHO (the rule-picked exemplar is immune to two
  fences; a rule-picked vulnerable patient turns every sweep fictional);
  Molnar's grid restriction REMOVES the dose question for pre-campaign
  patients (amplitude 0.151 → 0.000, 6/7 impossible); XGBoost `hist`
  without subsampling is seed-DETERMINISTIC (12 seeds, correlation
  1.0000 — the BCW seed-instability lesson inverts; with subsample 0.8
  it returns at 0.979); the ICE bundle stratifies by regime (0.48 vs
  0.32 at age 80, PDP says 0.407 — describing nobody) and the ICE
  derivative peaks in the PEDIATRIC tail (0.023/yr at age 10), the
  bronchiolitis inheritance; sweeping a fenced feature costs fiction at
  bundle scale (doses 18%, tosse 54%, idade 0%).
- One real bug found by module 01's first run and fixed in the shared
  tool: `gate_impossible` read the frozen n_crit diagnostics, letting a
  swept symptom flip pass unflagged — criteria are now recounted from
  the swept symptom columns.
- New figures promoted; BCW figures removed; PT module docs join the
  codespell exclusion.

## 2026-09-01 — the course model: one XGBoost, one rule-picked patient

- **00-dataset:** the model the five method modules explain.
  `tools/srag_model.py` (features, params, fit, metrics, the exemplar as
  a RULE — |p−0.5| minimal on test, tie by gold_id — and
  `gate_impossible()`, the single function all modules count
  impossibilities with). The committed artifact is the deterministic
  Gold SAMPLE (val/test whole, train 200k seed 42, 4.0 MB), never a
  model binary: every module refits in seconds and explains the same
  object by construction. MODEL.md is generated (`--card`) from
  `gold/model_metrics.json`.
- Measured against the design's pre-registration: XGB test AUC 0.7575
  on the sample (expected ~0.757), 0.7674 full — the price of sampling
  is −0.0099 and it is printed; logistic 0.7246; calibration gap 0.216
  predicted vs 0.182 observed = the regime-drift finding. The image
  trap cell lands inverted, as measured in design: the ABSENCE of a
  tomography record predicts death (9-Ignorado deadliest), and the
  with-image model uses the proxy (+0.006 AUC, mid-ranking gain) —
  the "why not let the weight be zero" answer, printed.
- ci.yml: walkthrough timeout 15→30 min; the measured-timing comment
  block re-measured, not estimated. `*.parquet binary` in
  .gitattributes.

## 2026-09-01 — one Silver table, and tools/ reads in layer order

- **00-dataset:** the Silver is now ONE parquet (4,109,567 × 420, zstd,
  streamed year by year with a schema guard) instead of six per-year
  files plus quarantine banks: the 7 shifted rows travel in the single
  table under the `linha_deslocada` flag, catalogued like every other
  derived column, and the row invariant is a `count(*)` instead of an
  accounting exercise. `build()` is untouched — only the packaging
  moved. The Postgres loader collapses six tables + a union view into
  one `silver.srag` (verified against the running stack), and the
  derived catalogue grows 224 → 226 (the `ano` and `linha_deslocada`
  columns), cascading through COLUMNS.md, the three diagrams (whose
  count is now computed, not typed), and the READMEs.
- **tools:** renamed to a single `srag_<noun>` convention in layer order
  (`srag_fetch`, `srag_profile`, `srag_dictionary`, `srag_silver`,
  `srag_quality`, `srag_columns`, `srag_diagrams`, `srag_gold`) — which
  also heals the walkthrough's broken link to `tools/srag_columns.py`,
  a name that did not exist until now. `tools/README.md` documents what
  each script reads and writes; the root README stops describing tools/
  as a single checker (wrong for eight files).
## 2026-09-01 — the Gold exists, and every choice in it is a flag

- **00-dataset:** `tools/srag_gold.py` builds `gold_covid_obito.parquet`
  (1,282,970 × 50: 40 model features + bookkeeping + diagnostics) from
  the Silver, with **every task decision a required CLI flag** — running
  it bare prints the GOLD.md menu and exits. The committed
  `gold/MANIFEST.md` is a pure function of `counts.json` + the decisions
  (hook-verified): the funnel in filter order, the NA each boolean fill
  absorbed, the three-state fold declared and undone via the
  `fator_risc_portao` diagnostic, and the decisions the menu never
  anticipated. The funnel reproduces the design's pre-registered numbers
  step by step (the one-row cohort difference is the quarantined 2023
  row, noted in the manifest).
- **00-dataset:** GOLD.md's five decision sections now carry their
  "Decidido 2026-09-01 — William" blocks; the closing section describes
  what was materialized instead of promising a tool.

## 2026-09-01 — xgboost joins the pinned stack; shap tried and rejected

- **build:** `xgboost==3.4.1` pinned for the course model. The lock diff
  contains only additions (xgboost + its nvidia-nccl marker dep), verified
  against the falsification criterion: no existing pin moved. `shap` was
  spiked and rejected — against numpy 2.4.6 the resolver walks numba back
  to 0.53.1 (2021), which fails to build on Python 3.12; module 05 will
  use xgboost's native `pred_contribs` (exact TreeSHAP) instead, with the
  runtime evidence in the PR. macOS needs `brew install libomp`.

## 2026-08-31 — every derived column gets a definition label

- **00-dataset:** the 224 derived columns now carry definition labels
  (Portuguese, like the raw labels in DICTIONARY.md) with provenance —
  the Ministry's script line for the official catalogue, "deste módulo"
  for ours. `derived_catalogue()` builds the list from the same tables
  `build()` uses, COLUMNS.md renders it, and `write_year()` asserts the
  built Silver's extra columns are exactly the catalogue: a derived
  column without a label now fails the build, the same way a raw column
  without a rule does. `silver.contrato` in Postgres grows 194 → 418
  rows, so the labels are browsable in Metabase next to the data.

## 2026-08-31 — the Silver, browsable

- **00-dataset:** the Postgres loader gains four indexes per yearly Silver
  table (NU_NOTIFIC, SG_UF, se_primeiro_sinto, covid_caso) and
  `silver.contrato` — the 194 columns with family, class, domain and gate,
  straight from the contract tables, browsable in Metabase next to the
  data. Verified against the running stack: 4,109,560 rows in silver.srag,
  194 in the contract.

## 2026-08-31 — the map, the Gold menu, the roadmap, and Fiocruz agreement

- **00-dataset:** `PIPELINE.svg` — the Bronze→Silver→Gold map, generated by
  `tools/srag_pipeline_svg.py` from the contract tables (structure and
  counts cannot drift from the code; quoted findings cite notebook cells).
  Gold's lane is dashed: its decisions are open by design.
- **00-dataset:** `GOLD.md` — the decision menu (target, cohort, leakage
  exclusion, split, encoding), each option with measured evidence printed
  by internals §7, a recommendation, and an owner. The leakage exclusion
  is generable from the class annotations and changes with the target.
- **00-dataset:** external validation against Fiocruz's published InfoGripe
  series: the public CSV freezes at 2019, and on that window our
  reproduction identifies their fever-inclusive case definition by fit and
  reaches correlation 0.9997 on stable weeks (median gap 28 cases/week,
  3.3%; 27 UFs at median 0.997). The authoritative GitLab is login-gated
  as of 2026-08 — recorded as the upgrade path, not hidden.
- **ROADMAP.md** — every Molnar chapter mapped onto the base: 17 method
  modules planned beyond the existing three, 4 excluded as image/NN-only,
  compute constraints at 4.1M×418 stated per method, and the organizing
  thesis: the feature-independence assumption is the comorbidity funnel.
- **Language:** module 00's README, GOLD.md and the ROADMAP are written in
  Portuguese by decision (2026-08-31) — they are study material, in the
  language William studies in. Two more generated diagrams join the map:
  FUNIL.svg (the three readings of a blank) and REGIMES.svg (lethality and
  COVID share per year, computed from the committed PROFILE.json).

## 2026-08-31 — every column has a rule: the contract, and three falsifications

- **00-dataset:** all 194 columns now carry a family rule — `COLUMNS.md`,
  generated and asserted (13 families partition the schema, no column
  unruled, `year_gated` re-derived from PROFILE.json), enforced by a
  pre-commit hook. Gates follow a stated rule: 34 enabling predicates
  confirmed at ≤0.05% contradiction in every year, 14 rejected with the
  worst-year number — two contradicted 100% of the time. `build()`
  re-measures every gate on every year and refuses to run on drift.
- **00-dataset:** three falsifications of the morning's Silver, measured
  before fixing: the epidemiological week was derived as ISO where SIVEP
  uses MMWR (`SEM_PRI` agrees 100.00% with MMWR in all six years, ~86%
  with ISO — one record in seven in the wrong week); the influenza
  catalogue dropped `PCR_FLUASU = 3` and never consumed `TP_FLU_AN`/
  `TP_FLU_PCR`, undercounting influenza 2.1x (33,668 → 71,808); seven
  dd/mm/yyyy dates (six dose fields, `VG_DTRES`) sat unparsed behind
  non-`DT_` names.
- **00-dataset:** quality grows 21 → 84 checks and the Kahn grid's two
  empty cells close (computational, relational — the pinned IBGE table,
  with Brasília's administrative regions recognised as DATASUS
  pseudo-codes rather than flagged invalid). Checks expected to fail are
  the documentation: `RES_AN` positive with no agent identified runs at
  9–20% every year since 2020.
- **00-dataset:** the dictionary generator's prose-anchor bug is fixed at
  the root (a field name must carry an underscore and end its table row):
  28 labels recover, including the full `PCR_FLUASU` subtype domain whose
  value 3 the catalogue had been dropping. `srag_quality` had kept a
  private copy of the broken pre-fix normalisation; it is single-sourced
  now. Silver: 418 columns, 4,109,567 = 4,109,560 + 7, every year green.

## 2026-08-31 — the derived-variable catalogue, in full

- **00-dataset:** Silver now implements the Ministry's derived-variable
  catalogue in full — 141 derived columns against the 8 it had, including the
  etiology cascade with the `_obito` and co-detection-free `_unico` variants,
  `regiao`, `se_primeiro_sinto` and the investigation flags. Transcribed from
  the official R script, not the derived-variable PDF, which gives
  `adenovirus_caso` the VSR criterion.
- **00-dataset:** `soma_casos` sums the nine primitive agent flags rather than
  every `_caso` column. Summing the composites too counted a single
  metapneumovirus twice — once as `metapneumo_caso`, once inside `ovr_caso` —
  and marked the row as a co-detection on its own, zeroing the `_unico`
  variants of every agent inside `ovr`.
- **00-dataset:** the treatment notebook is split into `walkthrough` (one year,
  narrated, runs on every PR) and `internals` (all six years in a single pass).
  Measuring one year and asserting six was the recurring error; the split makes
  it structural rather than a matter of care.
- **00-dataset:** percentages state their denominator. `Series.mean()` on a
  nullable boolean silently drops the NAs from the denominator, which had the
  notebook reporting the 2021 COVID share as 73.1% — the share among records
  with an etiology filled — where the question was 70.2%.

## 2026-08-31 — security bump: pyarrow 23.0.1, pypdf 6.15.0

Two high-severity advisories against the pinned stack: a use-after-free in
pyarrow reading IPC files, and an infinite loop in pypdf on a non-terminated
inline image. The repository's policy of moving Python pins once per offering is
about version churn, not about sitting on a fix — but the discipline it demands
still applies, so every generated artefact was regenerated and diffed.

`PROFILE.md`, `PROFILE.json`, `DICTIONARY.md` and `QUALITY.md` are **byte-identical**
after the bump: pypdf 6.15 extracts the same text from the Ministry's PDF, and
pyarrow 23 reads the parquet the same way.

The Silver parquet bytes **do** change — all six files — because pyarrow also
*writes* them and a major bump moves metadata and compression defaults. Values
are unchanged, verified against the figures the notebook prints. Worth recording
as a property of the stack: parquet byte-stability holds only within a pyarrow
version, which is what the lock is for.

Modules 01-03 import neither package, so their notebooks were not affected.

## 2026-08-31 — the Silver walkthrough notebook

`modules/00-dataset/notebooks/srag_silver_walkthrough.ipynb` walks the treatment
and prints the evidence for each decision. It imports `tools/srag_silver.py`
rather than restating it, so the ~20 modules that will consume the same data
cannot drift from the code that produced it. Runs in Colab: the first cell is
the unpinned `%pip`, the data is fetched from the Ministry's public S3 bucket,
and the repository is cloned when the import is not already on the path.

The central demonstration is two lines of output:

    regra ingênua  == '1' :         0 registros
    após normalise()      :   519,518 registros

## 2026-08-31 — Silver materialised, and a loader bug that only bit on re-run

`tools/srag_silver.py` now writes one parquet per year plus its quarantine,
sorted by `NU_NOTIFIC`, and `load.py` carries both into the `silver` schema. The
invariant is checkable in SQL against the database, not only in the Python that
produced it: `bronze=4109567, silver=4109560, quarentena=7`.

`load.py` dropped each yearly table before the union view that depends on it,
so the **first** run succeeded (no view yet) and every run after it failed with
`cannot drop table ... because other objects depend on it`. The views are now
dropped first. Worth recording because a review flagged this as *probable* from
reading the code; running it twice is what turned probable into confirmed.

## 2026-08-31 — the local stack takes its credentials from the environment

The Postgres password was hardcoded in `compose.yaml` and `load.py`. The stack
binds to 127.0.0.1 and the value was deliberately trivial, but a secret scanner
flagged it and was right to: a reader cannot tell "local dev" from "leaked" by
looking, and CI should not learn to ignore that check. Credentials now come from
a git-ignored `.env`, with `.env.example` as the template; compose fails loudly
when the variable is unset rather than falling back to a default.

## 2026-08-31 — Silver, and the Ministry's own script as the reference

`tools/srag_silver.py` turns Bronze into Silver without dropping a row: every
input record leaves either in the table or in a quarantine, and the module
asserts it. Across all six years that is 4,109,567 = 4,109,560 + 7, where the
seven are structurally shifted rows — a coded column holding a date, every field
after `HOSPITAL` off by one. They had been documented as fourteen unrelated
column anomalies; they are one defect, detected once as a row-level rule.

The reference is the Ministry's own cleaning script (MIT,
gitlab.com/cgcovid/dados-publicos, authored inside CGCOVID/DEDT/SVSA/MS). What
it settles is adopted and cited by line; six departures are recorded in the
module's DEVIATIONS, each because that script exists to count surveillance cases
for the weekly bulletin, and a filter that is right for counting is wrong for a
dataset that will be modelled and explained:

- `filter(caso_srag == 1)` becomes a column. The filter drops 40.3% of records,
  including 892,168 with `CLASSI_FIN=5` — it selects on symptom fields being
  filled, not on disease.
- The official cohort criterion is `HOSPITAL==1 | EVOLUCAO==2`, so membership
  depends on the outcome. `coorte_hospitalizado` drops the second clause; in
  2021 that is 10,322 records that qualified only by dying.
- Dates are ISO in the published data, not the `%d/%m/%Y` the script parses;
  `DT_VGM` and `DT_RT_VGM` genuinely are dd/mm/yyyy and are parsed as such.
- `replace_na(0)` is followed for the 18 laboratory checkboxes, which is their
  documented domain, and not for `EVOLUCAO` (0 merges "unknown" with "did not
  die") nor for the influenza subtype fields, where 0 is not a valid code.
- Neonates symptomatic on their day of birth get age 0 rather than NA.

Two measured results worth recording. Normalising `^(-?\d+)\.0+$` *before*
inferring any domain recovers all 519,518 of 2020's COVID-positive checkboxes,
which a literal comparison against `'1'` would have discarded silently. And
separating the three readings of an empty cell shows that `CARDIOPATI` is
genuinely absent in **11.9%** of 2021 records, not the 56.1% reported until now
— 44.2% is a field the system never presented, gated by `FATOR_RISC`.

## 2026-08-31 — profile every column, in every year

Five rounds of review found the same defect in my own findings each time: a
number measured on 2021 and stated as if it held for all six years. The worst
instance would have shipped — the laboratory checkbox columns hold `'1'` in five
years and `'1.0'` in 2020, so a rule written as a literal comparison would have
discarded 519,518 COVID-positive records while leaving the row count intact.

The fix is structural rather than a promise to be careful:

- `tools/srag_profile.py` profiles all 194 columns across every year, and
  **takes no year parameter** — a caller cannot ask for one year, so a finding
  cannot be scoped to one by accident. It also **does not normalise**: values
  are reported raw, because normalising is what hid the 2020 defect.
- `modules/00-dataset/PROFILE.md` and `.json` are the committed result. Every
  claim about a column in this repository should cite a year and agree with it.
- The headline: **75 of 194 columns change value shape between years.** These
  had been surfacing one at a time, one per audit. `EVOLUCAO` is `int.0` and
  `iso-date` in 2020; `AMOSTRA` carries dates; `CO_MU_INTE` carries text; and
  `RAIOX_RES` is `int.0` in all six years, which is why `_norm`'s `\.0$` never
  touched it.

Also: `pandas`, `pyarrow`, `pypdf` and `duckdb` were missing from both
`requirements.txt` and the lock, so `build_srag_dictionary.py` — already
committed — could not run in the repository's own pinned environment. Now
pinned with hashes.

## 2026-08-30 — a data quality framework for the SRAG base

Molnar's book offers no data-preparation guidance, so the treatment is anchored
externally: **Kahn et al. (2016)** for the quality taxonomy (the standard for
secondary use of EHR data, which is what these notifications are), the
Databricks **medallion** pattern for the layers, and **pandera**-style schema
checks in committed Python rather than Great Expectations — GE finds exactly
the same defects but writes its report to an uncommitted directory by default,
and this repository's premise is that every claim is reviewable in a diff. The
report layout is modelled on GE's Data Docs without reusing its Apache-2.0 code.

- `tools/srag_quality.py` + `modules/00-dataset/QUALITY.md`: 21 checks across
  the six Kahn cells, run over all six years.
- What it found beyond the earlier pass: negative ages (`-1`, `-9`) in five of
  six years; dates leaked into `UTI` as well as `EVOLUCAO`; invalid
  `SUPORT_VEN`, `CRITERIO` and `FATOR_RISC` values; and 21,997 rows in 2021
  sharing a person-event key, 1,854 of whose groups disagree on the outcome.
- Two findings about the dictionary itself: the published data uses ISO
  `YYYY-MM-DD` where the official dictionary declares `DD/MM/AAAA`, and
  `DT_INTERNA` mixes bare dates with full timestamps in the same column.
  Parsing with the documented format silently yields NaT for every row, which
  made the three date-ordering checks pass on nothing until it was caught; with
  a correct parse they compare 82-100% of rows and find no violation at all.

## 2026-08-30 — module 00: the SRAG dataset

First step of moving the course case from Breast Cancer Wisconsin to the
SIVEP-Gripe SRAG microdata (individual hospitalised-case notifications,
194 fields, 4.1M records over 2019-2024). This lands the acquisition path and
the documentation; the recorte, the treatment pipeline and the notebooks come
next.

- `tools/fetch_srag.sh`: pins the frozen yearly banks (extraction 26/06/2025)
  straight from the S3 bucket. The `dadosabertos.saude.gov.br` portal was
  returning HTTP 500 on every page on both hosts, which also blocks Guaraci's
  `srag_arquivos` discovery — the bucket is a separate service and stayed up.
  Guaraci remains the documented discovery path for the live banks, whose
  filenames carry an extraction date and change weekly.
- `tools/build_srag_dictionary.py` + `modules/00-dataset/DICIONARIO.md`: the
  194 fields with coded values, obligation class and measured fill rate per
  year, generated from the official PDF anchored on the real parquet schema.
  11 published columns are absent from the official dictionary, and the PDF
  spells `CO_DETEC`, `FAB_COV_1` and `FAB_COV_2` differently from the data.
- CI: the `changes` job now declares `pull-requests: read`. `paths-filter`
  lists the PR's files through the API, which the workflow's default
  `contents: read` does not allow.
- `modules/00-dataset/README.md`: what the measurements found — blank is not
  `9-Ignorado`; comorbidity fill tracks age, not documentation quality
  (a Simpson's paradox); the population flips from paediatric to elderly and
  back between regimes; pandemic distortion reaches non-COVID cases too; and
  the fields that leak the outcome.

## 2026-08-30 — the engineering layer

This repository is now where the modules are written; the course repository
[`scc5819/interpretable-ml-lectures`](https://github.com/scc5819/interpretable-ml-lectures)
becomes a one-way publication target. This batch brings over the engineering
that had grown there, adapted to this repository's own numbering and to its
Python 3.12 baseline. No module content changed — the LIME module was already
byte-identical in both repositories.

- `requirements.lock`: full transitive resolution with hashes, generated for
  Python 3.12 (`uv pip compile --universal --generate-hashes`). CI installs it
  with `--require-hashes`; `requirements.txt` stays the human-readable pins.
- CI (`.github/workflows/ci.yml`): link checking, pre-commit, notebook
  execution on the pinned stack with a dirty-tree guard, and `CITATION.cff`
  validation. A PR touching `modules/`, `tools/`, `.github/` or `requirements*`
  must touch `CHANGELOG.md` too (escape hatch: the `no-changelog` label).
  Third-party actions are pinned to commit SHAs.
- `canary.yml`: weekly, non-blocking run of the walkthrough notebooks on the
  newest Python and unpinned latest packages — the early-warning light for
  when the latest stack drifts away from the pinned baseline.
- `.pre-commit-config.yaml` + `tools/check_notebooks.py`: the notebook
  conventions (execution counts 1..N, unpinned `%pip`, no `%%time`) are now
  machine-checked, alongside ruff, codespell, actionlint and yaml/toml lint.
- `dependabot.yml`: GitHub Actions only. The pip ecosystem is deliberately
  unwatched — a package bump moves printed numbers and figures here, so it
  travels as a deliberate PR with a full re-run.
- `.editorconfig` and `.gitattributes`: consistent whitespace rules, and
  `linguist-documentation` so GitHub stops classifying the repository as ~99%
  Jupyter Notebook.
- `modules/_template/`: the starting point for a new module, with the section
  order that makes the modules read as one series.
- `CONTRIBUTING.md`, `AGENTS.md`, and a rewritten `CLAUDE.md` — the operating
  manual, now stating that this repository is the source and publication runs
  one way.

Two things the verification turned up, both recorded rather than papered over:

- All three modules re-run clean on the Python 3.12 locked stack, and every
  committed **PNG** figure reproduces byte-identically. The one **PDF**
  figure (`modules/03-lime/figures/lime_walkthrough_combined.pdf`) does not:
  matplotlib stamps `/CreationDate`, so a re-run differs in exactly 6 bytes
  inside that timestamp, at identical file size. `SOURCE_DATE_EPOCH` pins the
  stamp when a byte-for-byte PDF comparison is wanted — see `CLAUDE.md`.
- `lime_internals` takes 283.8 s on this 3.12 stack against 158.5 s on the
  3.14 stack the course repository pins. The CI timeouts here are set from
  the numbers measured on 3.12, not inherited.

The course repository's board tooling (`schedule.toml`, `render_board.py` and
its test suite) was deliberately left behind: it manages a class calendar with
seminar dates and presenter names, which this repository does not have.
