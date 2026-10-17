'use strict';
(() => {
  const source = 'https://christophm.github.io/interpretable-ml-book/feature-importance.html';
  const link = (href, label) => `<a href="${href}" target="_blank" rel="noreferrer">${label} ↗</a>`;
  window.PFICompactTheorySlides = {
    'dependence-results': data => {
      const study = data.age_subgroups;
      return {
        kicker: 'Molnar · dependent inputs',
        title: 'Dependent inputs: shuffling within groups',
        subtitle: 'Compare unrestricted age shuffling with shuffling within heart-disease groups.',
        body: '<div data-age-subgroup-pfi></div>',
        takeaway: '',
        notes: `<p>${link(`${source}#conditional-feature-importance`, 'Molnar · conditional importance')} · ${link(`${source}#group-wise-pfi-example`, 'Molnar · subgroup example')} · ${link('method.html#subgroups', 'Recorded SRAG subgroup protocol')}</p><p>The same historical XGBoost stays fixed with all 40 inputs. This illustration uses ${Number(study.metadata.n_cohort).toLocaleString('en-US')} records from the 2024 temporal test with valid age and heart disease recorded as No/Yes. The other ${Number(study.metadata.n_excluded).toLocaleString('en-US')} records are outside this known-response subset. Its baseline is ${study.results.global.baseline.toFixed(4)}, distinct from the complete-test baseline in earlier slides.</p><p>Only real, continuous age is permuted; the five bands organize the drawing only. Heart disease defines the two fixed groups, not death, the age bands or the diagram cells. First redistribute age freely across the subset; then restore the original inputs and shuffle age within heart-disease No and Yes separately. Other inputs and outcomes remain in their original records. Each procedure starts from the original data.</p><p>The endpoint distributions show the first recorded shuffle; prediction error is recalculated using the actual continuous ages and all inputs. The PFI chart shows the mean of ${study.metadata.repeats} paired orders, seed ${study.metadata.seed}, with sample shuffle SD, not confidence intervals. It reuses the continuous-age candidate recorded in internals §8; §9 adds only the display bands and aggregate flows. These were not chosen to maximize the difference in error.</p><p>The arrows illustrate who may supply an age to a fixed recipient record; they are not measured donor paths or patient movement. During an arrow, the destination location refers to the recipient's original age band. Unrestricted links may cross heart-disease rows, while restricted links remain in the active row. The links have no quantitative weights and are removed before revealing the recorded endpoint distribution. Running No and then Yes is a teaching choice; the donor restriction defines the method. Restricting donors preserves each heart-disease group's age distribution, although individual assignments and predictions can change.</p><p>Age remains important in both procedures. Their mean difference is small relative to shuffle variability; a lower restricted estimate is not automatically more correct. Conditioning on one input does not preserve all dependencies or guarantee realistic individual profiles. This example does not establish causality, impossible clinical combinations or an improvement to the fitted model. The association is moderate in this selected cohort. The earlier diabetes example remains in the separate evidence and technical sheet; the two cohorts are not interchangeable.</p>`
      };
    }
  };
})();
