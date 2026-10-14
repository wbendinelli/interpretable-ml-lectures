'use strict';
(() => {
  const count = value => Number(value).toLocaleString('en-US');
  const fixed = (value, decimals = 4) => Number(value).toFixed(decimals);
  const link = (href, label) => `<a href="${href}" target="_blank" rel="noreferrer">${label} ↗</a>`;
  const evidence = () => link('../../notebooks/srag_pfi_ranking.ipynb', 'Executed evidence · section 13');

  window.PFICompactStudySlides = {
    '66': data => {
      const study = data.study;
      return {
        kicker: 'Our SRAG study · data and preparation',
        title: 'From real records to model inputs',
        subtitle: 'Define the prediction task before measuring importance.',
        body: `<div class="compact-study">
          <div class="compact-pipeline" aria-label="Data preparation: Bronze, Silver and Gold">
            <section data-enter data-pulse><span class="small-label">Bronze</span><h3>Keep the source</h3><p>Public SIVEP-Gripe notifications.</p></section>
            <span class="compact-flow-arrow" aria-hidden="true">→</span>
            <section data-enter data-pulse><span class="small-label">Silver</span><h3>Make fields consistent</h3><p>Types, categories, dates and age.</p></section>
            <span class="compact-flow-arrow" aria-hidden="true">→</span>
            <section data-enter data-pulse><span class="small-label">Gold</span><h3>Define this study</h3><p>Cohort, outcome and temporal split.</p></section>
          </div>
          <div class="compact-data-grid">
            <section data-enter><p class="small-label">Study cohort</p><strong class="compact-study-number">${count(study.cohort_n)}</strong><p>Hospitalized COVID cases with a closed outcome.</p><p class="compact-study-detail">Predict death or survival.</p></section>
            <section data-enter><p class="small-label">Model inputs</p><strong class="compact-study-number">${count(study.input_n)}</strong><p>Exclude identifiers, the outcome, ICU and ventilatory support.</p><p class="compact-study-detail">Age is expressed in decimal years.</p></section>
            <section data-enter><p class="small-label">Recorded categories</p><h3 class="compact-category-heading">Unknown ≠ No</h3><div class="category-values"><span>Yes</span><span>No</span><span class="unknown">Unknown</span></div><p>Unknown stays an explicit category in XGBoost.</p></section>
          </div>
        </div>`,
        takeaway: 'Our animations use real processed records from this study cohort.',
        notes: `<p>The Gold cohort uses the broad COVID definition, hospitalization and closed outcomes. It requires symptom onset from 2020-02-26, a present age at most 120 years, and excludes displaced rows. The cohort total is before the uniform training sample.</p>
          <p>Silver derives decimal age from birth and symptom-onset dates. Gold merges missing, ignored and not-applicable categorical states into Unknown according to the recorded recipe. Unknown is not a negative diagnosis. The risk-factor gate remains a diagnostic field outside the model inputs; imaging is omitted.</p>
          <p>The final XGBoost uses native categorical inputs. Candidate families had their own preprocessing. These retrospective exclusions do not establish that every retained field would be available at a prospective clinical decision time.</p>
          <p>${link('../../GOLD.md', 'Gold decisions')} · ${link('../../MODEL.md', 'Model card')} · ${evidence()}</p>`
      };
    },

    '66-selection': data => {
      const study = data.study;
      const winner = study.scoreboard.find(row => row.model === study.winner);
      const scoreboard = study.scoreboard.map(row => `<tr class="${row.model === study.winner ? 'winner' : ''}"><td>${row.label}${row.model === study.winner ? ' · selected' : ''}</td><td>${fixed(row.auc)}</td><td>${fixed(row.brier)}</td></tr>`).join('');
      return {
        kicker: 'Our SRAG study · model and evaluation',
        title: 'Fit, choose, then explain',
        subtitle: 'Time separates training, model selection and evaluation.',
        body: `<div class="compact-study">
          <div class="compact-split" aria-label="Temporal split for fitting, selection and evaluation">
            <section data-enter data-pulse><p class="small-label">Fit · through ${study.train_end}</p><h3>${count(study.train_sample_n)}</h3><p>Uniformly sampled training records.</p></section>
            <section data-enter data-pulse><p class="small-label">Choose · ${study.validation_year}</p><h3>${count(study.splits.val.n)}</h3><p>Validation records for model selection.</p></section>
            <section data-enter data-pulse><p class="small-label">Explain · ${study.test_year}</p><h3>${count(study.splits.test.n)}</h3><p>All temporal test records for PFI.</p></section>
          </div>
          <div class="compact-model-summary" data-enter>
            <div><p class="small-label">Selected model</p><h3>${winner.label}</h3><p>Highest validation AUC: <strong>${fixed(winner.auc)}</strong>.</p></div>
            <p>Selected on validation only.<br>The fitted predictor stays fixed during PFI.</p>
          </div>
          <div class="compact-pfi-link" data-enter><span>Original test Brier <strong>${fixed(study.test_brier)}</strong></span><span class="compact-flow-arrow" aria-hidden="true">→</span><span>Shuffle one input</span><span class="compact-flow-arrow" aria-hidden="true">→</span><span>Repeat <strong>${count(data.protocol.repeats)}</strong> times and summarize</span></div>
          <p class="fine-reading compact-study-scope">Reference model: no class weights or resampling. This already inspected test supports an exploratory explanation.</p>
        </div>`,
        takeaway: 'Choose the model first. Permutation changes its inputs, while its fitted parameters remain fixed.',
        notes: `<p>The training sample has ${count(study.train_sample_n)} records from ${count(study.splits.train.n)} eligible records through ${study.train_end}; sampling seed ${study.sample_seed}. Validation was not added to the final training data. The temporal test was excluded from selection, but has since been inspected. This is an exploratory course study.</p>
          <p>Primary selection rule: highest validation AUC. The paired-bootstrap technical tie rule did not produce a tie. The following are the recorded tuned candidates, rather than a new search:</p>
          <table class="candidate-table"><thead><tr><th>Candidate family</th><th>Validation AUC ↑</th><th>Validation Brier ↓</th></tr></thead><tbody>${scoreboard}</tbody></table>
          <p>Final parameters: ${Object.entries(study.xgb_params).map(([key, value]) => `${key} = ${value}`).join('; ')}. No class weights or resampling were used in this reference; the balancing comparison did not replace it.</p>
          <p>All PFI screens share the same full-precision original test Brier. The displayed value is rounded. Each repeat starts from the original inputs; the SD describes shuffle variation for this fitted model and these records.</p>
          <p>${link('../../SELECTION.md', 'Selection protocol')} · ${link('../../MODEL.md', 'Final XGBoost')} · ${link('../../PFI.md', 'PFI protocol')} · ${evidence()}</p>`
      };
    }
  };
})();
