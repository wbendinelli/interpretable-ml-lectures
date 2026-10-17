'use strict';
(() => {
  const source = 'https://christophm.github.io/interpretable-ml-book/feature-importance.html';
  const link = (href, label) => `<a href="${href}" target="_blank" rel="noreferrer">${label} ↗</a>`;
  window.PFICompactTheorySlides = {
    'dependence-results': data => {
      const study = data.diabetes_subgroups;
      return {
        kicker: 'Molnar · dependent inputs',
        title: 'Dependent inputs: a limitation of PFI',
        subtitle: 'Shuffle diabetes freely, then within heart-disease groups.',
        body: '<div data-subgroup-pfi></div>',
        takeaway: '',
        notes: `<p>${link(`${source}#conditional-feature-importance`, 'Molnar · conditional importance')} · ${link(`${source}#group-wise-pfi-example`, 'Molnar · subgroup example')} · ${link('method.html#protocol', 'Recorded SRAG protocol')}</p><p>This slide uses the same fixed historical XGBoost as the preceding slides. Its known-response subset contains ${Number(study.metadata.n_cohort).toLocaleString('en-US')} temporal-test records; ${Number(study.metadata.n_excluded).toLocaleString('en-US')} records with an unknown or absent response in either field are excluded. All original inputs and outcomes remain aligned. Only diabetes is permuted; heart-disease No/Yes defines the groups.</p><p>The subset baseline is ${study.results.global.baseline.toFixed(4)}. It is not the full-test baseline ${study.full_test_reference.logloss.reconstructed.toFixed(4)} from earlier slides. Each procedure uses ${study.metadata.repeats} consecutive, paired permutations, seed ${study.metadata.seed}. Every repeat starts from the original inputs. The permuted input diagrams reproduce each procedure’s first recorded permutation; those losses can differ from the means over all repeats.</p><p>Global loss and loss differences are checked using group-size weights. Ratios are computed directly against each evaluated subset's baseline, not averaged across subgroup ratios. Whiskers show sample shuffle SD, not population confidence intervals. The two mean importance estimates are close; a lower restricted estimate is not automatically more correct. The procedures answer different questions.</p><p>Subgroups preserve the heart-disease/diabetes table, although individual diabetes values change. Other dependencies can still be disrupted. The moving packets count aggregate response transitions, not identified people exchanging with each other. This is not fully conditional importance, clinical causality, redundancy or hospital treatment quality. Grouping by diabetes itself would produce a degenerate operation preserving the permuted values by construction.</p>`
      };
    }
  };
})();
