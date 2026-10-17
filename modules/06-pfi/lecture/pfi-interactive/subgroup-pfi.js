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
    if (pfi?.schema_version !== 'srag-diabetes-subgroup-pfi-v1' || pfi.metadata.feature !== 'diabetes' || pfi.metadata.fixed_group_feature !== 'cardiopati') throw Error('The recorded diabetes subgroup study is required.');
    if (!(pfi.results.global.baseline > 0) || pfi.results.global.n !== pfi.metadata.n_cohort) throw Error('The subgroup baseline does not match its cohort.');
    for (const mode of ['original', 'marginal', 'within']) {
      const state = pfi.plot.states[mode];
      if (state.counts.flat().reduce((a, b) => a + b, 0) !== pfi.metadata.n_cohort) throw Error('The input diagram has a different cohort.');
    }
    for (const mode of ['marginal', 'within']) {
      const result = pfi.results.global[mode];
      if (result.after.length !== pfi.metadata.repeats || !Number.isFinite(result.difference_mean) || !(result.difference_sd >= 0)) throw Error('The repeated PFI result is incomplete.');
    }
    if (JSON.stringify(pfi.plot.states.original.counts) !== JSON.stringify(pfi.plot.states.within.counts)) throw Error('The grouped table must preserve the original counts.');
    if (pfi.plot.within_flows.groups.length !== 2) throw Error('The two recorded heart-disease groups are required.');
  }
  function mount(host, pfi) {
    validate(pfi);
    const evidence = pfi.plot, metadata = pfi.metadata, results = pfi.results.global;
    const reduced = matchMedia('(prefers-reduced-motion: reduce)');
    const abort = new AbortController(), listenerOptions = {signal: abort.signal};
    const uid = 'sgp-' + (++nextInstance);
    host.innerHTML = `<div class="sgp-root">
      <div class="sgp-toolbar"><div class="sgp-roles"><span>Shuffled input: <strong>Diabetes</strong></span><span>Subgroups: <strong>Heart disease · No / Yes</strong></span></div><div class="sgp-controls"><button type="button" data-sgp-pause>Pause</button><button type="button" data-sgp-replay>Replay ↻</button></div></div>
      <div class="sgp-scope"><span data-sgp-cohort></span><span>Bubble area = number of records</span></div>
      <div class="sgp-plots">${['original', 'marginal', 'within'].map(mode => `<section class="sgp-panel" data-sgp-panel="${mode}" aria-label="${modeNames[mode]}"><h3>${modeNames[mode]}</h3><svg class="sgp-bubbles" role="img" aria-label="${modeNames[mode]}"></svg><p class="sgp-first-loss" data-sgp-first-loss></p></section>`).join('')}</div>
      <p class="sgp-denominators" data-sgp-denominators></p>
      <div class="sgp-motion-line"><span class="sgp-phase" data-sgp-phase>Original inputs</span><p data-sgp-status role="status" aria-live="polite"></p></div>
      <section class="sgp-measurement" aria-labelledby="${uid}-error-title"><div class="sgp-measurement-heading"><h3 id="${uid}-error-title">What happened to prediction error?</h3><p>Original loss in this subset: <strong data-sgp-baseline></strong></p></div><svg class="sgp-error-chart" role="img" aria-label="Mean increase in log loss over repeated diabetes shuffles, with one sample standard deviation"></svg><p class="sgp-error-caption" data-sgp-error-caption></p></section>
      <p class="sgp-conclusion">The estimates are close. Grouping preserves the within-group proportions.</p>
      <div class="sgp-tooltip" role="tooltip" hidden></div>
    </div>`;
    const root = host.querySelector('.sgp-root'), $ = selector => root.querySelector(selector);
    const charts = new Map(), pauseButton = $('[data-sgp-pause]'), tooltip = $('.sgp-tooltip');
    const motion = {phase: 'original', progress: 0, elapsed: 0, startedAt: 0, running: false, frame: null, disposed: false};
    let resizeFrame = null, previousWidth = 0;
    const timeline = {intro: 1200, freeEnd: 2500, reset: 3400, groups: 4500, groupDuration: 4000, end: 12500};
    const maximum = Math.max(...Object.values(evidence.states).flatMap(state => state.counts.flat()));
    $('[data-sgp-cohort]').textContent = `SRAG ${metadata.year} · ${count(metadata.n_cohort)} records · both inputs known · ${count(metadata.n_excluded)} excluded`;
    $('[data-sgp-denominators]').textContent = `Within-row percentages · Heart disease No: n = ${count(evidence.states.original.y_marginals[0])} · Yes: n = ${count(evidence.states.original.y_marginals[1])}.`;
    $('[data-sgp-baseline]').textContent = fixed(results.baseline);
    $('[data-sgp-error-caption]').textContent = `Mean of ${count(metadata.repeats)} shuffles · Whiskers: ±1 shuffle SD, not confidence intervals.`;
    function dataMode(mode) {
      return mode === 'marginal' && ['free-done', 'reset', 'group-no', 'group-yes', 'finished'].includes(motion.phase) ? 'marginal' : mode === 'within' && motion.phase === 'finished' ? 'within' : 'original';
    }
    function formatFirstLoss(mode) {
      if (mode === 'original') return `Original log loss: ${fixed(results.baseline)}`;
      if (mode === 'marginal' && ['free-done', 'reset', 'group-no', 'group-yes', 'finished'].includes(motion.phase)) return `Shuffle 1 log loss: ${fixed(results.marginal.first_after)}`;
      if (mode === 'within' && motion.phase === 'finished') return `Shuffle 1 log loss: ${fixed(results.within.first_after)}`;
      return mode === 'within' && ['group-no', 'group-yes'].includes(motion.phase) ? 'Shuffle 1 · within-group redistribution…' : 'Starts from the original inputs';
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
        const height = innerWidth <= 900 ? 252 : Math.max(186, Math.min(252, innerHeight * .52 - 190));
        const left = 52, right = width - 8, top = 5, bottom = height - 36;
        const xpos = [left + (right - left) / 4, left + 3 * (right - left) / 4];
        const ypos = [top + (bottom - top) * .75, top + (bottom - top) * .25];
        const maxRadius = Math.max(16, Math.min(innerWidth <= 900 ? 42 : 38, (right - left) / 4 - 32, (bottom - top) / 4 - 9));
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        svg.setAttribute('height', height);
        svg.replaceChildren();
        svg.append(svgNode('title', {}, modeNames[mode]));
        svg.append(svgNode('desc', {}, 'Diabetes is the horizontal axis; heart disease defines the fixed rows. Bubble areas count records; percentages use the total in each heart-disease row.'));
        if (mode === 'within') {
          const defs = svgNode('defs'), marker = svgNode('marker', {id: uid + '-arrow', viewBox: '0 0 10 10', refX: 9, refY: 5, markerWidth: 5, markerHeight: 5, orient: 'auto-start-reverse'});
          marker.append(svgNode('path', {d: 'M 0 0 L 10 5 L 0 10 z', fill: 'var(--sgp-accent)'}));
          defs.append(marker); svg.append(defs);
        }
        const midpoint = (ypos[0] + ypos[1]) / 2;
        const highlight = svgNode('rect', {x: left, y: top, width: right - left, height: 0, class: 'sgp-group-band'});
        svg.append(highlight, svgNode('rect', {x: left, y: top, width: right - left, height: bottom - top, class: 'sgp-frame'}));
        svg.append(svgNode('line', {x1: left, x2: right, y1: midpoint, y2: midpoint, class: 'sgp-grid'}));
        ['nao', 'sim'].forEach((level, index) => {
          svg.append(svgNode('text', {x: xpos[index], y: bottom + 16, 'text-anchor': 'middle'}, labels[level]));
          svg.append(svgNode('text', {x: left - 8, y: ypos[index] + 4, 'text-anchor': 'end'}, labels[level]));
        });
        if (mode === 'marginal' || innerWidth <= 900) svg.append(svgNode('text', {x: (left + right) / 2, y: height - 2, 'text-anchor': 'middle', class: 'sgp-axis-title'}, 'Diabetes'));
        const cy = (top + bottom) / 2;
        if (mode === 'original' || innerWidth <= 900) svg.append(svgNode('text', {x: 11, y: cy, transform: `rotate(-90 11 ${cy})`, 'text-anchor': 'middle', class: 'sgp-axis-title'}, 'Heart disease'));
        const circles = [], valueLabels = [];
        state.counts.forEach((row, r) => row.forEach((n, c) => {
          const cell = svgNode('g', {'data-tooltip': `Heart disease: ${labels[['nao', 'sim'][r]]} · Diabetes: ${labels[['nao', 'sim'][c]]}\n${count(n)} of ${count(state.y_marginals[r])} records · ${percent(state.conditional_percent[r][c])} within this heart-disease group`, tabindex: 0});
          const radius = maxRadius * Math.sqrt(n / maximum);
          const circle = svgNode('circle', {cx: xpos[c], cy: ypos[r], r: radius, class: 'sgp-bubble' + (r === 1 && c === 1 ? ' sgp-both' : '')});
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
      svg.append(svgNode('title', {}, 'Repeated permutation importance of diabetes in the known-response SRAG subset'));
      svg.append(svgNode('desc', {}, `Baseline ${fixed(results.baseline, 8)}. ${rows.map(row => `${row.label}: mean extra log loss ${fixed(results[row.mode].difference_mean, 8)}, sample SD ${fixed(results[row.mode].difference_sd, 8)}`).join('. ')}. Both procedures use the same scale.`));
      for (let value = min; value <= max + step / 100; value += step) {
        svg.append(svgNode('line', {x1: x(value), x2: x(value), y1: 9, y2: bottom, class: 'sgp-grid'}), svgNode('text', {x: x(value), y: bottom + 18, 'text-anchor': 'middle', class: 'sgp-tick'}, fixed(value)));
      }
      svg.append(svgNode('line', {x1: x(0), x2: x(0), y1: 9, y2: bottom, class: 'sgp-zero'}));
      svg.append(svgNode('text', {x: (left + right) / 2, y: height - 3, 'text-anchor': 'middle', class: 'sgp-axis-title'}, 'Increase in log loss (PFI)'));
      rows.forEach((row, i) => {
        const result = results[row.mode], mean = result.difference_mean, sd = result.difference_sd, y = ys[i];
        svg.append(svgNode('text', {x: 0, y, class: 'sgp-method'}, compact && i === 0 ? 'Unrestricted' : row.label));
        svg.append(svgNode('text', {x: 0, y: y + 16, class: 'sgp-mean-loss'}, `Mean loss: ${fixed(result.after_mean)}`));
        svg.append(svgNode('line', {x1: x(mean - sd), x2: x(mean + sd), y1: y - 2, y2: y - 2, class: 'sgp-whisker'}));
        [mean - sd, mean + sd].forEach(value => svg.append(svgNode('line', {x1: x(value), x2: x(value), y1: y - 8, y2: y + 4, class: 'sgp-whisker'})));
        svg.append(svgNode('circle', {cx: x(mean), cy: y - 2, r: 4.5, class: row.mode === 'marginal' ? 'sgp-free-point' : 'sgp-within-point'}));
        const label = signed(mean) + ' ± ' + fixed(sd);
        svg.append(svgNode('text', compact ? {x: right - 1, y: y - 16, 'text-anchor': 'end', class: 'sgp-pfi-value'} : {x: width - 1, y: y + 3, 'text-anchor': 'end', class: 'sgp-pfi-value'}, label));
        svg.append(svgNode('circle', {cx: x(mean), cy: y - 2, r: 19, fill: 'transparent', tabindex: 0, 'data-tooltip': `${row.label}\nMean extra log loss: ${fixed(mean)}\nShuffle SD: ${fixed(sd)}\nMean ratio: ${fixed(result.ratio_mean)}\nRelative increase: ${fixed(result.relative_percent_mean, 2)}%`}));
      });
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
      within.overlay.replaceChildren(); within.highlight.setAttribute('height', 0);
      const row = motion.phase === 'group-no' ? 0 : motion.phase === 'group-yes' ? 1 : -1;
      if (row < 0) return;
      const flow = evidence.within_flows.groups.find(group => group.cardio === ['nao', 'sim'][row]);
      const y = within.ypos[row], upper = row === 0 ? within.midpoint : within.top, lower = row === 0 ? within.bottom : within.midpoint;
      within.highlight.setAttribute('y', upper); within.highlight.setAttribute('height', lower - upper);
      const radii = evidence.states.within.counts[row].map(value => within.maxRadius * Math.sqrt(value / maximum));
      const peak = Math.min(y - upper, lower - y) - 13, xmid = (within.xpos[0] + within.xpos[1]) / 2;
      [{from: 0, to: 1, sign: -1, n: flow.no_to_yes_n}, {from: 1, to: 0, sign: 1, n: flow.yes_to_no_n}].forEach(route => {
        const start = [within.xpos[route.from] + (route.from === 0 ? 1 : -1) * radii[route.from] * .6, y + route.sign * radii[route.from] * .8];
        const end = [within.xpos[route.to] + (route.to === 0 ? 1 : -1) * radii[route.to] * .6, y + route.sign * radii[route.to] * .8];
        const cy = 2 * (y + route.sign * peak) - (start[1] + end[1]) / 2;
        within.overlay.append(svgNode('path', {d: `M ${start[0]} ${start[1]} Q ${xmid} ${cy} ${end[0]} ${end[1]}`, class: 'sgp-flow', 'marker-end': `url(#${uid}-arrow)`}));
        const t = motion.progress, px = (1 - t) ** 2 * start[0] + 2 * (1 - t) * t * xmid + t * t * end[0], py = (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * cy + t * t * end[1];
        // Keep the aggregate count in the clear central corridor; only the flow marker moves.
        within.overlay.append(svgNode('circle', {cx: px, cy: py, r: 3.5, class: 'sgp-flow-marker'}));
        const packet = svgNode('g', {transform: `translate(${xmid} ${y + route.sign * peak})`, class: 'sgp-packet', 'data-flow-count': route.n}), value = count(route.n), boxWidth = value.length * 8 + 14;
        packet.append(svgNode('rect', {x: -boxWidth / 2, y: -10, width: boxWidth, height: 20, rx: 3}), svgNode('text', {x: 0, y: 4.5, 'text-anchor': 'middle'}, value)); within.overlay.append(packet);
      });
    }
    function controls() {
      pauseButton.disabled = motion.phase === 'finished' && !reduced.matches;
      pauseButton.textContent = reduced.matches ? (motion.phase === 'group-no' ? 'Next group' : motion.phase === 'group-yes' ? 'Finish' : 'Inspect flows') : motion.phase === 'finished' ? 'Finished' : motion.running ? 'Pause' : 'Resume';
      pauseButton.setAttribute('aria-pressed', String(motion.running));
    }
    function setPhase(phase, progress = 0) {
      const changed = phase !== motion.phase; motion.phase = phase; motion.progress = progress;
      if (changed) {
        tooltip.hidden = true;
        const phaseLabels = {original: 'Original inputs', free: '1 · Shuffle freely', 'free-done': '1 · One recorded shuffle', reset: 'Reset to original', 'group-no': '2 · Heart disease: No', 'group-yes': '2 · Heart disease: Yes', finished: 'Compare the two procedures'};
        $('[data-sgp-phase]').textContent = phaseLabels[phase];
        if (phase === 'original') $('[data-sgp-status]').textContent = 'Only diabetes will move. The model, outcomes and all other inputs stay fixed.';
        else if (phase === 'free') $('[data-sgp-status]').textContent = 'Redistribute diabetes across the whole known-response subset.';
        else if (phase === 'free-done') $('[data-sgp-status]').textContent = 'The unrestricted shuffle changes the observed relationship between the inputs.';
        else if (phase === 'reset') $('[data-sgp-status]').textContent = 'Start the grouped experiment again from the original inputs, not from the unrestricted shuffle.';
        else if (phase === 'finished') $('[data-sgp-status]').textContent = `Group counts and percentages are preserved, although ${count(evidence.states.within.changed_n)} diabetes responses changed.`;
        else {
          const flow = evidence.within_flows.groups.find(group => group.cardio === (phase === 'group-no' ? 'nao' : 'sim'));
          $('[data-sgp-status]').textContent = `${count(flow.no_to_yes_n)} No → Yes · ${count(flow.yes_to_no_n)} Yes → No. Labels count aggregate response changes.`;
        }
        renderBubbles(); controls();
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
      setPhase(reduced.matches ? 'finished' : 'original');
      if (motion.running) {motion.startedAt = performance.now(); motion.frame = requestAnimationFrame(tick);} controls();
    }
    function pause() {
      if (reduced.matches) {setPhase(motion.phase === 'group-no' ? 'group-yes' : motion.phase === 'group-yes' ? 'finished' : 'group-no', .5); controls(); return;}
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
    reduced.addEventListener('change', replay, listenerOptions);
    const observer = new ResizeObserver(entries => {const width = Math.round(entries[0].contentRect.width); if (width !== previousWidth) {previousWidth = width; resize();}}); observer.observe(root);
    render(); replay();
    return {dispose() {motion.disposed = true; motion.running = false; cancelAnimationFrame(motion.frame); if (resizeFrame !== null) cancelAnimationFrame(resizeFrame); observer.disconnect(); abort.abort(); tooltip.hidden = true;}};
  }
  window.PFISubgroupPFI = {mount};
})();
