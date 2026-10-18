'use strict';
(() => {
  const NS = 'http://www.w3.org/2000/svg';
  const labels = {nao: 'No', sim: 'Yes'};
  const modeNames = {original: 'Original', marginal: 'Unrestricted shuffle', within: 'Within heart-disease groups'};
  let nextInstance = 0;
  const count = value => Number(value).toLocaleString('en-US');
  const fixed = (value, digits = 4) => Number(value).toFixed(digits);
  const percent = value => Number(value).toFixed(1) + '%';
  const signed = value => (value > 0 ? '+' : '') + fixed(value);
  function svgNode(tag, attributes = {}, text) {
    const element = document.createElementNS(NS, tag);
    Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
    if (text !== undefined) element.textContent = text;
    return element;
  }
  function validate(pfi) {
    if (pfi?.schema_version !== 'srag-age-cardiopathy-preview-v1' || pfi.metadata.feature !== 'idade_anos' || pfi.metadata.fixed_group_feature !== 'cardiopati' || pfi.bins.length !== 5) throw Error('The recorded continuous-age subgroup study is required.');
    if (!(pfi.results.global.baseline > 0) || pfi.results.global.n !== pfi.metadata.n_cohort || pfi.metadata.repeats !== 50) throw Error('The subgroup protocol does not match its cohort.');
    for (const mode of ['original', 'marginal', 'within']) {
      const state = pfi.plot.states[mode];
      if (state.counts.length !== 2 || state.counts.some(row => row.length !== 5 || row.some(n => !Number.isInteger(n) || n < 0)) || state.counts.flat().reduce((a, b) => a + b, 0) !== pfi.metadata.n_cohort) throw Error('The age diagram has a different cohort.');
      state.counts.forEach((row, r) => row.forEach((n, c) => {if (Math.abs(100 * n / state.y_marginals[r] - state.conditional_percent[r][c]) > 1e-8) throw Error('Within-row percentages are inconsistent.');}));
    }
    for (const mode of ['marginal', 'within']) {
      const result = pfi.results.global[mode];
      if (result.after.length !== pfi.metadata.repeats || !Number.isFinite(result.difference_mean) || !(result.difference_sd >= 0)) throw Error('The repeated age PFI result is incomplete.');
      if (pfi.flows[mode].length !== 2) throw Error('Recorded aggregate age flows are required.');
    }
    if (JSON.stringify(pfi.plot.states.original.counts) !== JSON.stringify(pfi.plot.states.within.counts)) throw Error('The grouped age table must preserve the original counts.');
  }
  function mount(host, pfi) {
    validate(pfi);
    const evidence = pfi.plot, metadata = pfi.metadata, results = pfi.results.global;
    const reduced = matchMedia('(prefers-reduced-motion: reduce)');
    const abort = new AbortController(), listenerOptions = {signal: abort.signal};
    const uid = 'age-sgp-' + (++nextInstance);
    host.innerHTML = `<div class="sgp-root age-sgp-root">
      <div class="sgp-toolbar"><div class="sgp-roles"><span>Shuffled input: <strong>Age · continuous</strong></span><span>Subgroups: <strong>Heart disease · No / Yes</strong></span></div><div class="sgp-controls"><button type="button" data-sgp-pause>Pause</button><button type="button" data-sgp-replay>Replay ↻</button></div></div>
      <div class="sgp-scope"><span data-sgp-cohort></span><span>Bubble area = number of records</span></div>
      <div class="sgp-plots">${['original', 'marginal', 'within'].map(mode => `<section class="sgp-panel" data-sgp-panel="${mode}" aria-label="${modeNames[mode]}"><h3>${modeNames[mode]}</h3><svg class="sgp-bubbles" role="img" aria-label="${modeNames[mode]}"></svg><p class="sgp-first-loss" data-sgp-first-loss></p></section>`).join('')}</div>
      <p class="sgp-denominators" data-sgp-denominators></p>
      <div class="sgp-motion-line"><span class="sgp-phase" data-sgp-phase>Original inputs</span><p data-sgp-status role="status" aria-live="polite"></p></div>
      <section class="sgp-measurement" aria-labelledby="${uid}-error-title"><div class="sgp-measurement-heading"><h3 id="${uid}-error-title">What happened to prediction error?</h3><p>Original loss in this subset: <strong data-sgp-baseline></strong></p></div><svg class="sgp-error-chart" role="img" aria-label="Mean increase in log loss over repeated age shuffles, with one sample standard deviation"></svg><p class="sgp-error-caption" data-sgp-error-caption></p></section>
      <p class="sgp-conclusion">Restricting donors preserves age patterns by heart disease, not all dependencies.</p>
      <div class="sgp-tooltip" role="tooltip" hidden></div>
    </div>`;
    const root = host.querySelector('.sgp-root'), $ = selector => root.querySelector(selector);
    const charts = new Map(), pfiRows = new Map(), pauseButton = $('[data-sgp-pause]'), tooltip = $('.sgp-tooltip');
    const motion = {phase: 'original', progress: 0, elapsed: 0, startedAt: 0, running: false, frame: null, disposed: false};
    let resizeFrame = null, previousWidth = 0;
    const timeline = {intro: 1200, freeEnd: 4200, reset: 5100, groups: 6200, groupDuration: 4000, end: 14200};
    const maximum = Math.max(...Object.values(evidence.states).flatMap(state => state.counts.flat()));
    $('[data-sgp-cohort]').textContent = `SRAG ${metadata.year} · Valid age · Heart disease: No / Yes`;
    $('[data-sgp-denominators]').textContent = 'Percentages within heart-disease rows · Example donor links.';
    $('[data-sgp-baseline]').textContent = fixed(results.baseline);
    $('[data-sgp-error-caption]').textContent = `Mean of ${count(metadata.repeats)} shuffles · Whiskers: ±1 shuffle SD, not confidence intervals.`;
    function dataMode(mode) {
      return mode === 'marginal' && ['free-done', 'reset', 'group-no', 'group-yes', 'finished'].includes(motion.phase) ? 'marginal' : mode === 'within' && motion.phase === 'finished' ? 'within' : 'original';
    }
    function formatFirstLoss(mode) {
      if (mode === 'original') return `Original log loss: ${fixed(results.baseline)}`;
      if (mode === 'marginal' && motion.phase === 'free') return 'Example donor links · heart disease fixed';
      if (mode === 'marginal' && ['free-done', 'reset', 'group-no', 'group-yes', 'finished'].includes(motion.phase)) return `Shuffle 1 log loss: ${fixed(results.marginal.first_after)}`;
      if (mode === 'within' && motion.phase === 'finished') return `Shuffle 1 log loss: ${fixed(results.within.first_after)}`;
      return mode === 'within' && ['group-no', 'group-yes'].includes(motion.phase) ? 'Example donor links · heart disease fixed' : 'Starts from the original inputs';
    }
    function updateCaptions() {
      root.querySelectorAll('[data-sgp-panel]').forEach(panel => {
        panel.querySelector('[data-sgp-first-loss]').textContent = formatFirstLoss(panel.dataset.sgpPanel);
        panel.classList.toggle('sgp-active', (motion.phase === 'free' || motion.phase === 'free-done') ? panel.dataset.sgpPanel === 'marginal' : ['reset', 'group-no', 'group-yes'].includes(motion.phase) ? panel.dataset.sgpPanel === 'within' : panel.dataset.sgpPanel === 'original' && motion.phase === 'original');
      });
    }
    function renderBubbles() {
      charts.clear();
      root.querySelectorAll('[data-sgp-panel]').forEach(panel => {
        const mode = panel.dataset.sgpPanel, previousSVG = panel.querySelector('svg');
        // A fresh SVG root prevents stale paint layers after a radius transition.
        const svg = svgNode('svg', {class: 'sgp-bubbles', role: 'img', 'aria-label': modeNames[mode]});
        const state = evidence.states[dataMode(mode)], width = panel.getBoundingClientRect().width;
        const height = innerWidth <= 900 ? 250 : innerHeight <= 800 ? Math.max(180, innerHeight * .37 - 96) : Math.max(190, Math.min(265, innerHeight * .37 - 80));
        const left = 40, right = width - 4, top = 8, bottom = height - 40;
        const xpos = pfi.bins.map((_, i) => left + (right - left) * (i + .5) / 5);
        const ypos = [top + (bottom - top) * .25, top + (bottom - top) * .75];
        const maxRadius = Math.max(8, Math.min(31, (right - left) / 10 - 3, (bottom - top) / 4 - 8));
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        svg.setAttribute('height', height);
        svg.replaceChildren();
        svg.append(svgNode('title', {}, modeNames[mode]));
        svg.append(svgNode('desc', {}, 'Age bands are for display only; the model receives continuous age. Heart disease stays fixed. Arrows are illustrative allowed donor-to-record links. Recipient locations refer to original age bands. They are not patient movement or measured flows. Endpoint areas and percentages are recorded data.'));
        if (mode !== 'original') {
          const defs = svgNode('defs'), marker = svgNode('marker', {id: uid + '-' + mode + '-arrow', viewBox: '0 0 10 10', refX: 8, refY: 5, markerWidth: 6, markerHeight: 6, markerUnits: 'userSpaceOnUse', orient: 'auto'});
          marker.append(svgNode('path', {d: 'M 2 2 L 8 5 L 2 8', fill: 'none', stroke: 'var(--sgp-accent)', 'stroke-width': 1.3, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'}));
          defs.append(marker); svg.append(defs);
        }
        const midpoint = (ypos[0] + ypos[1]) / 2;
        const highlight = svgNode('rect', {x: left, y: top, width: right - left, height: 0, class: 'sgp-group-band'});
        svg.append(highlight, svgNode('rect', {x: left, y: top, width: right - left, height: bottom - top, class: 'sgp-frame'}));
        svg.append(svgNode('line', {x1: left, x2: right, y1: midpoint, y2: midpoint, class: 'sgp-grid'}));
        ['nao', 'sim'].forEach((level, index) => svg.append(svgNode('text', {x: left - 7, y: ypos[index] + 4, 'text-anchor': 'end'}, labels[level])));
        pfi.bins.forEach((bin, index) => svg.append(svgNode('text', {x: xpos[index], y: bottom + 16, 'text-anchor': 'middle', class: 'sgp-bin-label'}, bin.label)));
        svg.append(svgNode('text', {x: (left + right) / 2, y: height - 3, 'text-anchor': 'middle', class: 'sgp-axis-title'}, 'Age in years · bands for display only'));
        const cy = (top + bottom) / 2;
        if (mode === 'original' || innerWidth <= 900) svg.append(svgNode('text', {x: 10, y: cy, transform: `rotate(-90 10 ${cy})`, 'text-anchor': 'middle', class: 'sgp-axis-title'}, 'Heart disease'));
        const circles = [], valueLabels = [];
        state.counts.forEach((row, r) => row.forEach((n, c) => {
          const cell = svgNode('g', {'data-tooltip': `Heart disease: ${labels[['nao', 'sim'][r]]} · Age: ${pfi.bins[c].label} years\n${count(n)} of ${count(state.y_marginals[r])} records · ${percent(state.conditional_percent[r][c])} within this heart-disease group`, tabindex: 0});
          const radius = maxRadius * Math.sqrt(n / maximum);
          const circle = svgNode('circle', {cx: xpos[c], cy: ypos[r], r: radius, class: 'sgp-bubble' + (r === 1 ? ' sgp-both' : '')});
          const values = svgNode('g', {class: 'sgp-cell-values'});
          values.append(svgNode('text', {x: xpos[c], y: ypos[r] - 2, 'text-anchor': 'middle', class: 'sgp-count'}, count(n)), svgNode('text', {x: xpos[c], y: ypos[r] + 13, 'text-anchor': 'middle', class: 'sgp-percent'}, percent(state.conditional_percent[r][c])));
          cell.append(circle, svgNode('circle', {cx: xpos[c], cy: ypos[r], r: Math.max(22, radius), fill: 'transparent'}), values);
          svg.append(cell); circles.push({node: circle, row: r, col: c}); valueLabels.push(values);
        }));
        const overlay = svgNode('g', {'aria-hidden': 'true'}); svg.append(overlay);
        previousSVG.replaceWith(svg);
        charts.set(mode, {svg, width, height, left, right, top, bottom, xpos, ypos, midpoint, maxRadius, highlight, overlay, circles, valueLabels});
      });
      updateCaptions(); drawMotion();
    }
    function renderPFI() {
      const svg = $('.sgp-error-chart'), width = svg.getBoundingClientRect().width, compact = width < 550;
      const height = compact ? 168 : 116, left = compact ? 118 : 139, right = width - (compact ? 10 : 126);
      const bottom = compact ? 124 : 78, ys = compact ? [38, 92] : [26, 63];
      const rows = [{mode: 'marginal', label: 'Unrestricted'}, {mode: 'within', label: 'Within groups'}];
      const low = Math.min(0, ...rows.map(row => results[row.mode].difference_mean - results[row.mode].difference_sd));
      const high = Math.max(...rows.map(row => results[row.mode].difference_mean + results[row.mode].difference_sd));
      const rough = (high - low) / 4 || 1, power = 10 ** Math.floor(Math.log10(rough));
      const step = [1, 2, 2.5, 5, 10].find(value => value * power >= rough) * power;
      const min = Math.floor(low / step) * step, rawMax = Math.ceil(high / step) * step, max = rawMax > min ? rawMax : min + step;
      const x = value => left + 12 + (value - min) / (max - min) * (right - left - 24);
      svg.setAttribute('viewBox', `0 0 ${width} ${height}`); svg.setAttribute('height', height); svg.replaceChildren();
      svg.append(svgNode('title', {}, 'Repeated permutation importance of continuous age in the eligible SRAG subset'));
      svg.append(svgNode('desc'));
      pfiRows.clear();
      for (let value = min; value <= max + step / 100; value += step) {
        svg.append(svgNode('line', {x1: x(value), x2: x(value), y1: 9, y2: bottom, class: 'sgp-grid'}), svgNode('text', {x: x(value), y: bottom + 18, 'text-anchor': 'middle', class: 'sgp-tick'}, fixed(value)));
      }
      svg.append(svgNode('line', {x1: x(0), x2: x(0), y1: 9, y2: bottom, class: 'sgp-zero'}));
      svg.append(svgNode('text', {x: (left + right) / 2, y: height - 3, 'text-anchor': 'middle', class: 'sgp-axis-title'}, 'Increase in log loss (PFI)'));
      rows.forEach((row, i) => {
        const result = results[row.mode], mean = result.difference_mean, sd = result.difference_sd, y = ys[i];
        const group = svgNode('g', {class: 'age-pfi-result', 'data-sgp-pfi-row': row.mode});
        group.append(svgNode('text', {x: 0, y, class: 'sgp-method'}, compact && i === 0 ? 'Unrestricted' : row.label));
        group.append(svgNode('text', {x: 0, y: y + 16, class: 'sgp-mean-loss'}, `Mean loss: ${fixed(result.after_mean)}`));
        group.append(svgNode('line', {x1: x(mean - sd), x2: x(mean + sd), y1: y - 2, y2: y - 2, class: 'sgp-whisker'}));
        [mean - sd, mean + sd].forEach(value => group.append(svgNode('line', {x1: x(value), x2: x(value), y1: y - 8, y2: y + 4, class: 'sgp-whisker'})));
        group.append(svgNode('circle', {cx: x(mean), cy: y - 2, r: 4.5, class: row.mode === 'marginal' ? 'sgp-free-point' : 'sgp-within-point'}));
        const label = signed(mean) + ' ± ' + fixed(sd);
        group.append(svgNode('text', compact ? {x: right - 1, y: y - 16, 'text-anchor': 'end', class: 'sgp-pfi-value'} : {x: width - 1, y: y + 3, 'text-anchor': 'end', class: 'sgp-pfi-value'}, label));
        group.append(svgNode('circle', {cx: x(mean), cy: y - 2, r: 19, fill: 'transparent', tabindex: -1, 'data-tooltip': `${row.label}\nMean extra log loss: ${fixed(mean)}\nShuffle SD: ${fixed(sd)}\nMean ratio: ${fixed(result.ratio_mean)}\nRelative increase: ${fixed(result.relative_percent_mean, 2)}%`}));
        svg.append(group); pfiRows.set(row.mode, {group, label: row.label});
      });
      updateMeasurement();
    }
    function updateMeasurement() {
      // Reveal each recorded summary only after its illustrative shuffle ends.
      // Derive visibility from the phase so replay, resize and reduced motion agree.
      const freeDone = ['free-done', 'reset', 'group-no', 'group-yes', 'finished'].includes(motion.phase);
      const visible = [];
      pfiRows.forEach(({group, label}, mode) => {
        const ready = mode === 'marginal' ? freeDone : motion.phase === 'finished';
        group.classList.toggle('age-pfi-result-ready', ready);
        group.setAttribute('aria-hidden', String(!ready));
        group.querySelector('[data-tooltip]').setAttribute('tabindex', ready ? '0' : '-1');
        if (ready) visible.push(`${label}: mean extra log loss ${fixed(results[mode].difference_mean, 8)}, sample SD ${fixed(results[mode].difference_sd, 8)}`);
      });
      $('.sgp-error-chart').classList.toggle('age-pfi-chart-ready', freeDone);
      $('.sgp-error-chart').setAttribute('aria-hidden', String(!freeDone));
      $('.sgp-error-chart desc').textContent = visible.length ? `Baseline ${fixed(results.baseline, 8)}. ${visible.join('. ')}. Both procedures use the same scale.` : 'Results appear after each shuffle procedure finishes.';
      $('[data-sgp-error-caption]').classList.toggle('age-pfi-caption-ready', freeDone);
      $('[data-sgp-error-caption]').setAttribute('aria-hidden', String(!freeDone));
    }
    function drawMotion() {
      const free = charts.get('marginal'), within = charts.get('within'); if (!free || !within) return;
      if (motion.phase === 'free') {
        free.circles.forEach(({node, row, col}) => {
          const before = evidence.states.original.counts[row][col], after = evidence.states.marginal.counts[row][col];
          node.setAttribute('r', free.maxRadius * Math.sqrt((before + (after - before) * motion.progress) / maximum));
        });
        free.valueLabels.forEach(node => node.setAttribute('opacity', '0'));
      }
      charts.forEach(chart => {chart.overlay.replaceChildren(); chart.highlight.setAttribute('height', 0);});
      const row = motion.phase === 'group-no' ? 0 : motion.phase === 'group-yes' ? 1 : -1;
      const shared = motion.phase === 'free' || motion.phase === 'free-done';
      const active = shared ? free : within;
      root.dataset.agePool = shared ? 'shared' : row >= 0 ? 'separate' : 'none';
      if (shared) {active.highlight.setAttribute('y', active.top); active.highlight.setAttribute('height', active.bottom - active.top);}
      const activeRows = motion.phase === 'free' ? [0, 1] : row >= 0 ? [row] : [];
      // Arrows illustrate allowed donor-to-record links, not measured flows.
      // Destinations use recipients' ORIGINAL bands; heart disease stays fixed.
      const turn = Math.min(2, Math.floor(motion.progress * 3));
      const shownOrigins = [turn * 2 % pfi.bins.length, (turn * 2 + 1) % pfi.bins.length];
      const linkProgress = Math.min(1, motion.progress * 3 - turn);
      activeRows.forEach(r => {
        const y = active.ypos[r], upper = r === 0 ? active.top : active.midpoint, lower = r === 0 ? active.midpoint : active.bottom;
        if (row >= 0) {active.highlight.setAttribute('y', upper); active.highlight.setAttribute('height', lower - upper);}
        pfi.bins.forEach((bin, from) => {
          if (!shownOrigins.includes(from)) return;
          const to = (from + 1) % pfi.bins.length;
          const targetRow = shared && from % 2 === 0 ? 1 - r : r;
          const startX = active.xpos[from], endX = active.xpos[to], endY = active.ypos[targetRow];
          const xmid = (startX + endX) / 2;
          const cy = targetRow !== r ? (y + endY) / 2 : y + (to > from ? -1 : 1) * (Math.min(y - upper, lower - y) - 9) * 1.6;
          const d = `M ${startX} ${y} Q ${xmid} ${cy} ${endX} ${endY}`;
          const attrs = {'data-age-from-row': r, 'data-age-to-row': targetRow, 'data-age-from-bin': from, 'data-age-to-bin': to};
          // One short stroke travels over a quiet guide; no moving data point.
          // The same RAF governs routes, pause, replay and reduced-motion steps.
          active.overlay.append(svgNode('path', {d, class: 'sgp-flow age-donor-guide', 'aria-hidden': 'true'}));
          const path = svgNode('path', {d, pathLength: 100, class: 'sgp-flow age-donor-arrow', 'stroke-dashoffset': -82 * linkProgress, 'marker-end': `url(#${uid}-${shared ? 'marginal' : 'within'}-arrow)`, ...attrs});
          path.append(svgNode('title', {}, `Allowed age donor: heart disease ${labels[['nao', 'sim'][r]]}, age ${bin.label}. Recipient record: heart disease ${labels[['nao', 'sim'][targetRow]]}, original age band ${pfi.bins[to].label}. Illustrative link, not a measured flow or patient movement.`));
          active.overlay.append(path);
        });
      });
    }


    function controls() {
      pauseButton.disabled = motion.phase === 'finished' && !reduced.matches;
      pauseButton.textContent = reduced.matches ? (motion.phase === 'finished' ? 'Restart steps' : 'Next step') : motion.phase === 'finished' ? 'Finished' : motion.running ? 'Pause' : 'Resume';
      pauseButton.setAttribute('aria-pressed', String(motion.running));
    }
    function setPhase(phase, progress = 0) {
      const changed = phase !== motion.phase; motion.phase = phase; motion.progress = progress;
      if (changed) {
        tooltip.hidden = true;
        const phaseLabels = {original: 'Original inputs', free: '1 · Shuffle freely', 'free-done': '1 · One recorded shuffle', reset: 'Reset to original', 'group-no': '2 · Heart disease: No', 'group-yes': '2 · Heart disease: Yes', finished: 'Compare the two procedures'};
        $('[data-sgp-phase]').textContent = phaseLabels[phase];
        if (phase === 'original') $('[data-sgp-status]').textContent = 'Only age is reassigned. Heart disease, outcomes and the model stay fixed.';
        else if (phase === 'free') $('[data-sgp-status]').textContent = 'Across-group links allowed. Heart disease stays fixed. Destination: receiver’s ORIGINAL age band.';
        else if (phase === 'free-done') $('[data-sgp-status]').textContent = 'Unrestricted donors change the age patterns in both fixed heart-disease rows.';
        else if (phase === 'reset') $('[data-sgp-status]').textContent = 'Restore the original ages before using separate heart-disease pools.';
        else if (phase === 'finished') $('[data-sgp-status]').textContent = 'Individual age assignments change; each group’s age distribution is preserved.';
        else {
          $('[data-sgp-status]').textContent = 'Same-group donors only. Heart disease stays fixed. Destination: receiver’s ORIGINAL age band.';
        }
        renderBubbles(); updateMeasurement(); controls();
      } else drawMotion();
    }
    function tick(now) {
      if (!motion.running || motion.disposed) return;
      motion.elapsed = now - motion.startedAt;
      const time = motion.elapsed;
      if (time < timeline.intro) setPhase('original');
      else if (time < timeline.freeEnd) setPhase('free', (time - timeline.intro) / (timeline.freeEnd - timeline.intro));
      else if (time < timeline.reset) setPhase('free-done');
      else if (time < timeline.groups) setPhase('reset');
      else if (time < timeline.end) {
        const local = time - timeline.groups, index = Math.floor(local / timeline.groupDuration);
        setPhase(index === 0 ? 'group-no' : 'group-yes', Math.max(0, Math.min(1, ((local % timeline.groupDuration) - 400) / 2900)));
      } else {motion.running = false; setPhase('finished'); controls(); return;}
      motion.frame = requestAnimationFrame(tick);
    }
    function replay() {
      cancelAnimationFrame(motion.frame); motion.elapsed = 0; motion.phase = ''; motion.running = !reduced.matches;
      setPhase('original');
      if (motion.running) {motion.startedAt = performance.now(); motion.frame = requestAnimationFrame(tick);} controls();
    }
    function pause() {
      if (reduced.matches) {const phases = ['original', 'free', 'free-done', 'reset', 'group-no', 'group-yes', 'finished']; setPhase(phases[(phases.indexOf(motion.phase) + 1) % phases.length], .5); controls(); return;}
      if (motion.phase === 'finished') return;
      motion.running = !motion.running;
      if (motion.running) {motion.startedAt = performance.now() - motion.elapsed; motion.frame = requestAnimationFrame(tick);} else {cancelAnimationFrame(motion.frame); renderBubbles();}
      controls();
    }
    function render() {if (!motion.disposed) {renderBubbles(); renderPFI();}}
    function resize() {if (resizeFrame !== null) cancelAnimationFrame(resizeFrame); resizeFrame = requestAnimationFrame(() => {resizeFrame = null; render();});}
    function showTooltip(target, x, y) {
      if (motion.phase === 'free') return;
      tooltip.textContent = target.dataset.tooltip; tooltip.hidden = false;
      const box = tooltip.getBoundingClientRect(); tooltip.style.left = Math.max(8, Math.min(x + 10, innerWidth - box.width - 8)) + 'px'; tooltip.style.top = Math.max(8, Math.min(y + 10, innerHeight - box.height - 8)) + 'px';
    }
    $('[data-sgp-replay]').addEventListener('click', replay, listenerOptions); pauseButton.addEventListener('click', pause, listenerOptions);
    root.addEventListener('pointermove', event => {const target = event.target.closest('[data-tooltip]'); if (target) showTooltip(target, event.clientX, event.clientY); else tooltip.hidden = true;}, listenerOptions);
    root.addEventListener('pointerleave', () => {tooltip.hidden = true;}, listenerOptions);
    root.addEventListener('focusin', event => {const target = event.target.closest('[data-tooltip]'); if (target) {const box = target.getBoundingClientRect(); showTooltip(target, box.left, box.bottom);}}, listenerOptions);
    root.addEventListener('focusout', () => {tooltip.hidden = true;}, listenerOptions);
    window.addEventListener('resize', resize, listenerOptions);
    document.addEventListener('visibilitychange', () => {if (document.hidden && motion.running) pause();}, listenerOptions);
    reduced.addEventListener('change', replay, listenerOptions);
    const observer = new ResizeObserver(entries => {const width = Math.round(entries[0].contentRect.width); if (width !== previousWidth) {previousWidth = width; resize();}}); observer.observe(root);
    render(); replay();
    return {dispose() {motion.disposed = true; motion.running = false; cancelAnimationFrame(motion.frame); if (resizeFrame !== null) cancelAnimationFrame(resizeFrame); observer.disconnect(); abort.abort(); tooltip.hidden = true;}};
  }
  window.PFIAgeSubgroupPFI = {mount};
})();
