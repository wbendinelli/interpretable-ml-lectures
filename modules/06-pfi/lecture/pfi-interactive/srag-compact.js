'use strict';
(() => {
  const count = value => Number(value).toLocaleString('en-US');
  const fixed = (value, decimals = 4) => Number(value).toFixed(decimals);
  const link = (href, label) => `<a href="${href}" target="_blank" rel="noreferrer">${label} ↗</a>`;
  const evidence = () => link('method.html#evidence', 'Aggregate evidence · study protocol');
  const icon = name => window.PFIVisualAids.icon(name);
  const heading = (name, label) => `<div class="meaning-heading">${icon(name)}<span class="small-label">${label}</span></div>`;
  const selectionResults = data => {
    const {family_search: current, review} = data.model_selection;
    const selected = current.families.find(row => row.model === current.winner);
    const rows = (items, key, winner) => items.map(row => `<tr class="${row[key] === winner ? 'selected-result' : ''}"><th scope="row">${row.label}</th><td>${fixed(row.validation_logloss)}</td><td>${fixed(row.test_logloss)}</td></tr>`).join('');
    const table = (body, label) => `<table class="selection-results-table" aria-label="${label}"><thead><tr><th scope="col">Model / strategy</th><th scope="col">Val. 2023</th><th scope="col">Test 2024</th></tr></thead><tbody>${body}</tbody></table>`;
    return `<div class="selection-results-grid">
      <section aria-labelledby="family-results-title"><p class="selection-stage">Model-family comparison</p><h3 id="family-results-title">Lowest validation loss: ${selected.label}</h3><p class="selection-rule">Selected by validation log loss · training-only preparation</p>
        ${table(rows([...current.families].sort((a, b) => a.validation_logloss - b.validation_logloss), 'model', current.winner), 'Log loss after model-family hyperparameter selection by validation log loss')}
        <p class="selection-footnote">Fixed baselines: constant + clipped OLS. Budgets vary by family.</p>
      </section>
      <section aria-labelledby="balance-results-title"><p class="selection-stage">XGBoost balancing + tuning</p><h3 id="balance-results-title">Original configuration retained</h3><p class="selection-rule">${count(review.candidates_per_strategy)} configurations per strategy · minimum validation log loss</p>
        ${table(rows(review.strategies, 'strategy', review.winner), 'Log loss after separate XGBoost tuning for each balancing strategy')}
        <p class="selection-footnote">Original: no balancing. No recalibration.</p>
      </section>
    </div><p class="selection-conclusion">${current.winner === data.study.winner ? `${selected.label} remains selected by validation log loss.` : `New family selection: ${selected.label}. PFI still explains the historical reference.`}</p><p class="selection-test-note">Log loss ↓ lower is better. Choose on validation; the previously inspected test is exploratory.</p>`;
  };

  window.PFICompactStudySlides = {
    '66': data => {
      const study = data.study;
      return {
        kicker: 'Our SRAG study · population and target',
        title: 'Our study cohort',
        subtitle: 'What are we predicting, and for whom?',
        body: `<div class="cohort-study">
          <div class="cohort-pipeline" aria-label="Data preparation: Bronze, Silver and Gold">
            <section data-enter>${heading('source', 'Bronze')}<p>Raw records</p></section>
            <span class="cohort-flow-arrow" aria-hidden="true">→</span>
            <section data-enter>${heading('clean', 'Silver')}<p>Standardized fields</p></section>
            <span class="cohort-flow-arrow" aria-hidden="true">→</span>
            <section data-enter>${heading('cohort', 'Gold')}<p>Study cohort and target</p></section>
          </div>
          <div class="cohort-layout">
            <section class="cohort-eligibility" data-enter aria-label="Who is included">
              ${heading('cohort', 'Who is included')}
              <ul class="cohort-criteria">
                <li><strong>Hospitalization + required symptoms</strong><span>Cough/sore throat + dyspnea/low oxygen/respiratory distress.</span></li>
                <li><strong>COVID-19 recorded</strong><span>Positive molecular/antigen marker or final classification.</span></li>
                <li><strong>Recovery or death recorded</strong><span>Other-cause deaths excluded.</span></li>
                <li><strong>Symptom onset from 26 Feb 2020</strong><span>Available age ≤ 120 years.</span></li>
              </ul>
              <p class="cohort-total"><strong>${count(study.cohort_n)}</strong><span>eligible records</span></p>
            </section>
            <section class="cohort-question" data-enter aria-label="The prediction task">
              ${heading('model', 'The prediction task')}
              <h3>Estimate the probability of recorded death.</h3>
              <dl class="cohort-target"><div><dt>Predictors</dt><dd><strong>${count(study.input_n)}</strong> recorded features</dd></div><div><dt>Target</dt><dd>Recorded death vs recovery</dd></div></dl>
              <p class="cohort-scope">This study does not assess<br>hospital care quality.</p>
            </section>
          </div>
        </div>`,
        takeaway: 'Records without documented hospitalization are outside this cohort. Results do not represent all people with COVID-19.',
        notes: `<p>Hospitalization alone is insufficient: HOSPITAL = 1 AND (TOSSE = 1 OR GARGANTA = 1) AND (DISPNEIA = 1 OR SATURACAO = 1 OR DESC_RESP = 1). Unrecorded criteria do not count as present. The broad COVID definition is PCR_SARS2_marcado OR AN_SARS2_marcado OR CLASSI_FIN = 5; this is not a PCR-only cohort.</p>
          <p>Gold admits EVOLUCAO = 1 (recovery) or 2 (recorded death); 3 (death from other causes), ignored and missing outcomes are excluded. Symptom onset must be on or after 2020-02-26. Age from the birth and symptom-onset dates must be present and no greater than 120 years; negative derived ages become missing upstream. Displaced rows are excluded. Vaccination is not an inclusion criterion. Records are not demonstrated to be unique people. The cohort count precedes the uniform training sample.</p>
          <p>Silver derives decimal age from birth and symptom-onset dates. Gold merges missing, ignored and not-applicable categorical states into Unknown according to the recorded recipe. Unknown is not a negative diagnosis. The risk-factor gate remains a diagnostic field outside the model inputs; imaging is omitted.</p>
          <p>The final XGBoost uses native categorical inputs. Candidate families had their own preprocessing. These retrospective exclusions do not establish that every retained field would be available at a prospective clinical decision time.</p>
          <p>${link('method.html#study', 'Gold decisions')} · ${link('method.html#model', 'Model card')} · ${evidence()}</p>`
      };
    },

    '66-selection': data => {
      const study = data.study;
      const winner = study.scoreboard.find(row => row.model === study.winner);
      const current = data.model_selection.family_search;
      const familyWinner = current.families.find(row => row.model === current.winner);
      const scoreboard = study.scoreboard.map(row => `<tr class="${row.model === study.winner ? 'winner' : ''}"><td>${row.label}${row.model === study.winner ? ' · selected' : ''}</td><td>${fixed(row.auc)}</td></tr>`).join('');
      return {
        kicker: 'Our SRAG study · model and evaluation',
        title: 'Training, selection and evaluation',
        subtitle: 'Split by symptom onset year; sample training only.',
        body: `<div class="selection-study"><div class="selection-views" role="group" aria-label="Training and model selection views"><button type="button" data-selection-view="split" aria-pressed="true">Data split</button><button type="button" data-selection-view="results" aria-pressed="false">Model results</button></div>
        <div class="sample-study" data-selection-panel="split">
          <p class="sample-origin" data-enter>${icon('cohort')}<strong>${count(study.cohort_n)}</strong><span>eligible cohort records</span></p>
          <div class="sample-timeline" aria-label="Split by symptom onset year. Only the training partition is sampled.">
            <section class="sample-training" data-enter aria-labelledby="sample-training-title">
              ${heading('fit', 'Training')}
              <h3 id="sample-training-title">2020–${study.train_end}</h3>
              <p class="sample-count">${count(study.splits.train.n)}</p><p class="sample-description">eligible training records</p>
              <div class="training-sample-arrow" aria-hidden="true"><span></span></div>
              <p class="sample-selected">${count(study.train_sample_n)}</p><p class="sample-description">uniform random sample</p>
            </section>
            <section data-enter aria-labelledby="sample-validation-title">
              ${heading('choose', 'Validation')}
              <h3 id="sample-validation-title">${study.validation_year}</h3>
              <p class="sample-count">${count(study.splits.val.n)}</p><p class="sample-description">all eligible records</p>
              <p class="sample-purpose">Choose the model</p>
            </section>
            <section data-enter aria-labelledby="sample-test-title">
              ${heading('explain', 'Temporal test')}
              <h3 id="sample-test-title">${study.test_year}</h3>
              <p class="sample-count">${count(study.splits.test.n)}</p><p class="sample-description">all eligible records</p>
              <p class="sample-purpose">Evaluate and explain<br><span>Previously inspected · exploratory</span></p>
            </section>
          </div>
          <section class="sample-model" data-enter aria-label="The explained model and the separate model-selection studies"><div>${heading('model', 'PFI reference')}<h3>${winner.label}</h3><p class="sample-model-fixed">Fixed during PFI</p></div><div class="sample-selection-history"><p><span>Family selection</span><strong>${familyWinner.label} · validation log loss</strong></p><p><span>XGBoost balancing + tuning</span><strong>Original configuration retained · validation log loss</strong></p></div></section>
          <p class="sample-explanation" data-enter>Uniform draw · without replacement · seed ${study.sample_seed}. A computational choice, separate from class balancing.</p>
        </div><div class="selection-results" data-selection-panel="results" hidden>${selectionResults(data)}</div></div>`,
        takeaway: '',
        notes: `<p>The training sample has ${count(study.train_sample_n)} records from ${count(study.splits.train.n)} eligible records with symptom onset in 2020–${study.train_end}; sampling seed ${study.sample_seed}. The uniform random draw is without replacement, without equal year quotas and without balancing classes. The sample size is an operational computation/distribution choice, not a demonstrated optimum or a PFI-specific sample. First split the cohort by symptom onset year, then sample only training. The unused training records do not become validation or test.</p>
          <p>Validation and test contain every eligible record in their respective periods, with real outcomes and observed class distributions. Validation was not added to the final training data. The temporal test was excluded from model selection, but has since been inspected; this is exploratory evaluation.</p>
          <p>Historical selection rule: highest validation AUC. The paired-bootstrap technical tie rule did not produce a tie. The following are the recorded historical candidates, rather than a new search:</p>
          <table class="candidate-table"><thead><tr><th>Candidate family</th><th>Validation AUC ↑</th></tr></thead><tbody>${scoreboard}</tbody></table>
          <p>The Model results view reports the new plain-family search selected by unrounded validation log loss, and the separate XGBoost balancing review. Family-specific search budgets are declared; constant and OLS are fixed diagnostic baselines. OLS outputs are clipped for log loss. All current preparation is fitted only on training records. The historical ROC-AUC search above remains a separate record; the differences do not isolate only the choice of metric. No recalibration was performed.</p>
          <p>Final parameters: ${Object.entries(study.xgb_params).map(([key, value]) => `${key} = ${value}`).join('; ')}. No class weights or resampling were used in this reference; the balancing comparison did not replace it.</p>
          <p>All full-test PFI screens share the same full-precision original test log loss. The displayed value is rounded. Each repeat starts from the original inputs; the SD describes shuffle variation for this fitted model and these records.</p>
          <p>${link('method.html#selection', 'Selection protocol')} · ${link('method.html#model', 'Final XGBoost')} · ${link('method.html#protocol', 'PFI protocol')} · ${evidence()}</p>`
      };
    }
  };
})();
