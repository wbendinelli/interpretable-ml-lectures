'use strict';
(() => {
  const source = 'https://christophm.github.io/interpretable-ml-book/feature-importance.html';
  const link = (href, label) => `<a href="${href}" target="_blank" rel="noreferrer">${label} ↗</a>`;
  const motion = label => `<div class="study-motion"><span id="study-motion-state">${label}</span><button id="study-motion-pause" class="text-button" aria-pressed="false">Pause</button></div>`;

  const diagnosticCopies = {
    cardiopati: {
      title: 'Heart disease alone',
      question: 'What changes when the model loses the original heart-disease information?',
      movement: 'Donor heart disease → destination record',
      steps: [
        'Copy the original test inputs.',
        'Shuffle heart disease across records. Keep diabetes fixed.',
        'Use the same XGBoost; compare Brier with the original error.'
      ],
      scope: 'This can disrupt the observed heart–diabetes relationship.'
    },
    diabetes: {
      title: 'Diabetes alone',
      question: 'What changes when the model loses the original diabetes information?',
      movement: 'Donor diabetes → destination record',
      steps: [
        'Copy the original test inputs.',
        'Shuffle diabetes across records. Keep heart disease fixed.',
        'Use the same XGBoost; compare Brier with the original error.'
      ],
      scope: 'This can disrupt the observed heart–diabetes relationship.'
    },
    joint: {
      title: 'Move the pair together',
      question: 'What changes when the model loses the original information from both inputs together?',
      movement: '[Heart disease + Diabetes] → another record',
      steps: [
        'Copy the original test inputs.',
        'Use the same donor row for both columns. Move each pair together.',
        'Use the same XGBoost; compare Brier with the original error.'
      ],
      scope: 'Pairs stay intact; relationships with other inputs can still break. Our complementary diagnostic.'
    },
    within: {
      title: 'Shuffle inside diabetes groups',
      question: 'What changes when heart disease is shuffled between records with the same diabetes category?',
      movement: 'Same diabetes category [Heart disease ↔ Heart disease]',
      steps: [
        'Group original records by diabetes: Yes, No or Unknown.',
        'Shuffle heart disease inside each group. Keep diabetes fixed.',
        'Use the same model; compare each group’s original and permuted Brier. Weight by group size.'
      ],
      scope: 'Molnar’s subgroup approach; other dependencies may remain.'
    }
  };

  function diagnosticCopy(key) {
    const copy = diagnosticCopies[key];
    return `<p class="small-label">How this shuffle works</p><h3>${copy.title}</h3><p class="sr-only">${copy.question}</p><div class="diagnostic-movement">${copy.movement}</div><ol class="diagnostic-steps">${copy.steps.map(step => `<li>${step}</li>`).join('')}</ol><p class="fine-reading">${copy.scope}</p>`;
  }

  window.PFICompactTheorySlides = {
    '73': () => ({
      kicker: 'Molnar · strengths and limitations',
      title: 'What PFI tells us — and what to check',
      subtitle: 'Importance describes predictive reliance in this fitted model.',
      body: `<div class="limits-layout"><section data-enter><p class="limits-label">What we gain</p><div class="limit-item" data-pulse><div><h3>A direct performance question</h3><p>Measure how much predictive error changes after a shuffle.</p></div></div><div class="limit-item" data-pulse><div><h3>Keep the trained predictor</h3><p>Explain its reliance without training a replacement model.</p></div></div><div class="limit-item" data-pulse><div><h3>A global picture</h3><p>Summarize reliance across the evaluation records. Repeated shuffles reveal its variation.</p></div></div></section><section data-enter><p class="limits-label">What we must check</p><div class="limit-item" data-pulse><div><h3>The ranking has a context</h3><p>The model, loss and evaluation data determine the ranking. Observed outcomes are required.</p></div></div><div class="limit-item" data-pulse><div><h3>Inputs can share information</h3><p>Related inputs can substitute for one another. Exchanges can create unlikely records.</p></div></div><div class="limit-item" data-pulse><div><h3>Interpret with care</h3><p>A rank gives neither an effect’s direction nor a causal explanation.</p></div></div></section></div>${motion('Reading the strengths and interpretation limits')}`,
      takeaway: 'A low PFI does not prove clinical irrelevance. Check dependent inputs before interpreting the ranking.',
      notes: `<p>${link(`${source}#strengths`, 'Molnar · strengths')} · ${link(`${source}#limitations`, 'Molnar · limitations')}</p><p>Interactions can contribute to more than one importance; individual PFI values are not generally additive. Shuffle SD measures variation conditional on this fitted predictor and these records, rather than a population confidence interval.</p><p>Our historical temporal test was already inspected. The current explanation is exploratory.</p>`
    }),
    'dependence-results': data => ({
      kicker: 'SRAG · one dependence example',
      title: 'Related inputs: change the shuffle',
      subtitle: 'Heart disease and diabetes. One fitted model, different questions.',
      body: `<div class="diagnostic-layout"><section data-enter><p class="small-label">Full temporal test · ${data.dependence.protocol.repeats} shuffles per diagnostic</p><div id="dependence-chart" class="dependence-chart"></div><p class="fine-reading">Axis: extra Brier × 1,000. Whiskers: one sample SD across shuffles.</p>${motion('Revealing the recorded means and SD')}</section><section class="diagnostic-reading" data-enter><label class="diagnostic-select">Choose the shuffle<select id="diagnostic-choice"><option value="cardiopati">Heart disease alone</option><option value="diabetes">Diabetes alone</option><option value="joint" selected>Both inputs together</option><option value="within">Heart disease within diabetes groups</option></select></label><div id="diagnostic-detail">${diagnosticCopy('joint')}</div></section></div>${Object.keys(diagnosticCopies).map(key => `<template id="diagnostic-copy-${key}">${diagnosticCopy(key)}</template>`).join('')}`,
      takeaway: 'The pair shuffle preserves observed pairs. Subgroup shuffling keeps diabetes fixed. Each answers a different question.',
      notes: `<p>${link(`${source}#group-wise-pfi-example`, 'Molnar · subgroup example')} · ${link('method.html#evidence', 'Aggregate SRAG evidence')} · ${link('method.html#protocol', 'Diagnostic protocol')}</p><p>Every repeat starts from the original evaluation inputs. Outcomes, the fitted predictor and all non-permuted inputs stay fixed. The chart uses the same Brier baseline and recorded row orders throughout.</p><p>Molnar describes permutation within subgroups. Moving both columns together is a separate complementary check. Our diabetes-only subgroup calculation is not full conditional PFI given every other input. Joint importance versus the sum of individual importances does not, by itself, prove interaction or redundancy.</p><p>The observed heart–diabetes association includes shared Unknown states. It is not evidence of a causal relationship. Repeat counts, means and sample SD are recorded in the aggregate evidence file.</p>`
    })
  };
})();
