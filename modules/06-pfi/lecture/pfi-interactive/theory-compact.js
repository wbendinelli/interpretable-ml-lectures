'use strict';
(() => {
  const source = 'https://christophm.github.io/interpretable-ml-book/feature-importance.html';
  const link = (href, label) => `<a href="${href}" target="_blank" rel="noreferrer">${label} ↗</a>`;
  const motion = label => `<div class="study-motion"><span id="study-motion-state">${label}</span><button id="study-motion-pause" class="text-button" aria-pressed="false">Pause</button></div>`;

  const diagnosticCopies = {
    cardiopati: {
      title: 'Heart disease alone',
      question: 'What changes when the model loses the original heart-disease information?',
      steps: [
        'Copy the original test inputs.',
        'Shuffle heart disease; diabetes stays fixed.',
        'Predict again; compare log loss with the original error.'
      ],
      scope: 'This can disrupt the observed heart–diabetes relationship.'
    },
    diabetes: {
      title: 'Diabetes alone',
      question: 'What changes when the model loses the original diabetes information?',
      steps: [
        'Copy the original test inputs.',
        'Shuffle diabetes; heart disease stays fixed.',
        'Predict again; compare log loss with the original error.'
      ],
      scope: 'This can disrupt the observed heart–diabetes relationship.'
    },
    joint: {
      title: 'Move the pair together',
      question: 'What changes when the model loses the original information from both inputs together?',
      steps: [
        'Copy the original test inputs.',
        'One donor order for both columns: each pair moves together.',
        'Predict again; compare log loss with the original error.'
      ],
      scope: 'Pairs stay intact; relationships with other inputs can still break. Our complementary diagnostic.'
    },
    within: {
      title: 'Shuffle inside diabetes groups',
      question: 'What changes when heart disease is shuffled between records with the same diabetes category?',
      steps: [
        'Group original inputs by diabetes category.',
        'Shuffle heart disease only inside each group; diabetes stays fixed.',
        'Compare each group’s log loss; average changes by group size.'
      ],
      scope: 'Molnar’s subgroup approach; other dependencies may remain.'
    }
  };

  function diagnosticCopy(key) {
    const copy = diagnosticCopies[key];
    return `<p class="small-label">How this shuffle works · same fitted model</p><h3>${copy.title}</h3><p class="sr-only">${copy.question}</p>${window.PFIVisualAids.diagnosticSketch(key)}<ol class="diagnostic-steps">${copy.steps.map(step => `<li>${step}</li>`).join('')}</ol><p class="fine-reading">${copy.scope}</p>`;
  }

  window.PFICompactTheorySlides = {
    'dependence-results': data => ({
      kicker: 'SRAG · one dependence example',
      title: 'Related inputs: change the shuffle',
      subtitle: 'Heart disease and diabetes. One fitted model, different questions.',
      body: `<div class="diagnostic-layout"><section data-enter><p class="small-label">Full temporal test · ${data.dependence.protocol.repeats} shuffles per diagnostic</p><div id="dependence-chart" class="dependence-chart"></div><p class="fine-reading">Axis: extra log loss × 1,000. Whiskers: one sample SD across shuffles.</p>${motion('Revealing the recorded means and SD')}</section><section class="diagnostic-reading" data-enter><label class="diagnostic-select">Choose the shuffle<select id="diagnostic-choice"><option value="cardiopati">Heart disease alone</option><option value="diabetes">Diabetes alone</option><option value="joint" selected>Both inputs together</option><option value="within">Heart disease within diabetes groups</option></select></label><div id="diagnostic-detail">${diagnosticCopy('joint')}</div></section></div>${Object.keys(diagnosticCopies).map(key => `<template id="diagnostic-copy-${key}">${diagnosticCopy(key)}</template>`).join('')}`,
      takeaway: 'Keep pairs together, or shuffle within groups. Different procedures answer different questions.',
      notes: `<p>${link(`${source}#group-wise-pfi-example`, 'Molnar · subgroup example')} · ${link('method.html#evidence', 'Aggregate SRAG evidence')} · ${link('method.html#protocol', 'Diagnostic protocol')}</p><p>Every repeat starts from the original evaluation inputs. Outcomes, the fitted predictor and all non-permuted inputs stay fixed. The chart uses the same log loss baseline and recorded row orders throughout.</p><p>Molnar describes permutation within subgroups. Moving both columns together is a separate complementary check. Our diabetes-only subgroup calculation is not full conditional PFI given every other input. Joint importance versus the sum of individual importances does not, by itself, prove interaction or redundancy.</p><p>The observed heart–diabetes association includes shared Unknown states. It is not evidence of a causal relationship. Repeat counts, means and sample SD are recorded in the aggregate evidence file.</p>`
    })
  };
})();
