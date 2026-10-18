'use strict';
(() => {
  const NS = 'http://www.w3.org/2000/svg';
  const $ = id => document.getElementById(id);
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const modes = ['original', 'marginal', 'within'];
  const timeline = {intro: 1200, freeEnd: 3200, reset: 4700, groups: 5800, rowDuration: 3600, end: 13000};
  const fmt = (value, digits = 4) => {
    const number = Math.abs(value) < .5 * 10 ** -digits ? 0 : value;
    return number.toLocaleString('pt-BR', {minimumFractionDigits: digits, maximumFractionDigits: digits});
  };
  const count = value => value.toLocaleString('pt-BR');
  const node = (tag, attributes = {}, text) => {
    const element = document.createElementNS(NS, tag);
    Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
    if (text !== undefined) element.textContent = text;
    return element;
  };
  const clamp = value => Math.max(0, Math.min(1, value));
  const ease = value => value * value * (3 - 2 * value);
  let data, elapsed = timeline.end, playing = false, lastTime = null, frame = 0, resizeFrame = 0;
  let observer, previousPhase = '', lastPaint = 0, inspectStep = 5;

  function validate(study) {
    if (!study || !Array.isArray(study.bins) || study.bins.length !== 5 || study.metadata.repeats !== 50) throw Error('A evidência não contém o protocolo esperado.');
    const lower = [0, 18, 40, 60, 80], upper = [18, 40, 60, 80, null];
    study.bins.forEach((bin, i) => {
      if (bin.lower_inclusive !== lower[i] || bin.upper_exclusive !== upper[i]) throw Error('As faixas registradas diferem desta proposta.');
    });
    modes.forEach(mode => {
      const state = study.plot.states[mode];
      if (state.counts.length !== 2 || state.counts.some(row => row.length !== 5 || row.some(n => !Number.isInteger(n) || n < 0))) throw Error('Contagens incompletas na evidência.');
      if (state.counts.flat().reduce((sum, n) => sum + n, 0) !== study.metadata.n_cohort) throw Error('O total das bolhas não confere com o recorte.');
      state.counts.forEach((row, r) => row.forEach((n, c) => {
        if (Math.abs(100 * n / state.y_marginals[r] - state.conditional_percent[r][c]) > 1e-8) throw Error('Os percentuais não conferem com os grupos.');
      }));
    });
    if (JSON.stringify(study.plot.states.original.counts) !== JSON.stringify(study.plot.states.within.counts)) throw Error('O embaralhamento restrito não preservou a tabela agrupada.');
    ['marginal', 'within'].forEach(mode => {
      const result = study.results.global[mode];
      if (result.after.length !== study.metadata.repeats || !['difference_mean', 'difference_sd', 'after_mean', 'first_after'].every(key => Number.isFinite(result[key]))) throw Error('Os resultados de importância estão incompletos.');
    });
    if (!Number.isFinite(study.results.global.baseline) || !Number.isFinite(study.association.pearson_continuous_original)) throw Error('Falta o erro original ou a associação registrada do recorte.');
  }

  function stateAt(time) {
    if (time < timeline.intro) return {key: 'original', title: '1 · Partimos do original', detail: 'As duas operações começam nas mesmas fichas. Só a idade será redistribuída.', free: 0};
    if (time < timeline.freeEnd) return {key: 'free', title: '2 · Embaralhamento livre', detail: 'Uma ficha pode receber uma idade de outro grupo de cardiopatia.', free: ease(clamp((time - timeline.intro) / (timeline.freeEnd - timeline.intro)))};
    if (time < timeline.reset) return {key: 'free-done', title: '2 · Resultado do sorteio livre', detail: 'As proporções mudaram. Este desenho corresponde ao primeiro sorteio registrado.', free: 1};
    if (time < timeline.groups) return {key: 'reset', title: '3 · Restauramos o original', detail: 'A próxima operação não parte do resultado livre. Recuperamos as idades originais antes de restringir as trocas.', free: 1};
    if (time < timeline.groups + timeline.rowDuration) return {key: 'within-no', title: '4 · Dentro do grupo: Não', detail: 'Os valores de idade circulam apenas entre fichas sem cardiopatia registrada.', free: 1, row: 0, progress: (time - timeline.groups) / timeline.rowDuration};
    if (time < timeline.end) return {key: 'within-yes', title: '4 · Dentro do grupo: Sim', detail: 'Agora, apenas entre fichas com cardiopatia registrada. A outra linha permanece fixa.', free: 1, row: 1, progress: (time - timeline.groups - timeline.rowDuration) / timeline.rowDuration};
    return {key: 'finished', title: 'Comparação completa', detail: 'As contagens por faixa foram preservadas dentro dos grupos. As idades individuais podem ter mudado.', free: 1};
  }

  function focusedFlow(row, progress) {
    const table = data.flows.within.find(item => item.cardio === (row ? 'sim' : 'nao'));
    if (!table) return null;
    let best = null;
    table.counts.forEach((values, from) => values.forEach((n, to) => {
      if (from !== to && n > 0 && (!best || n > best.n)) best = {from, to, n};
    }));
    if (!best) return null;
    const reverseN = table.counts[best.to][best.from];
    const second = progress >= .5 && reverseN > 0;
    return second ? {from: best.to, to: best.from, n: reverseN, progress: (progress - .5) * 2} : {...best, progress: reverseN > 0 ? progress * 2 : progress};
  }

  function plot(mode, phase) {
    const host = $('plot-' + mode), width = host.getBoundingClientRect().width;
    if (width < 80) return;
    const stacked = innerWidth <= 960, height = stacked ? 275 : 245;
    const left = 45, right = width - 5, top = 13, bottom = height - 45;
    const cellWidth = (right - left) / 5;
    const xs = data.bins.map((_, i) => left + cellWidth * (i + .5));
    const ys = [top + (bottom - top) * .25, top + (bottom - top) * .75];
    const radius = Math.max(10, Math.min(stacked ? 34 : 29, cellWidth / 2 - 5, (bottom - top) / 4 - 8));
    const maximum = Math.max(...modes.flatMap(key => data.plot.states[key].counts.flat()));
    const before = data.plot.states.original, target = data.plot.states[mode];
    const freeProgress = mode === 'marginal' ? phase.free : mode === 'original' ? 0 : 1;
    const morphing = mode === 'marginal' && freeProgress > 0 && freeProgress < 1;
    const actualState = mode === 'marginal' && freeProgress === 0 ? before : target;
    const svg = node('svg', {viewBox: `0 0 ${width} ${height}`, height, role: 'img', 'aria-label': `${mode === 'original' ? 'Original' : mode === 'marginal' ? 'Embaralhamento livre' : 'Dentro dos grupos'}: faixas etárias por cardiopatia`});
    svg.append(node('title', {}, 'Idade por faixa e cardiopatia'), node('desc', {}, 'Cada bolha agrega registros. A área usa uma escala comum nos três painéis. Os percentuais usam o total da linha de cardiopatia.'));
    if (mode === 'within' && phase.row !== undefined) svg.append(node('rect', {x: left, y: top + phase.row * (bottom - top) / 2, width: right - left, height: (bottom - top) / 2, class: 'row-band'}));
    svg.append(node('rect', {x: left, y: top, width: right - left, height: bottom - top, class: 'frame'}));
    svg.append(node('line', {x1: left, x2: right, y1: (top + bottom) / 2, y2: (top + bottom) / 2, class: 'row-separator'}));
    ['Não', 'Sim'].forEach((label, r) => svg.append(node('text', {x: left - 7, y: ys[r] + 4, 'text-anchor': 'end', class: 'row-label'}, label)));
    svg.append(node('text', {x: 9, y: (top + bottom) / 2, transform: `rotate(-90 9 ${(top + bottom) / 2})`, 'text-anchor': 'middle', class: 'bin-label'}, 'Cardiopatia'));
    data.bins.forEach((bin, c) => svg.append(node('text', {x: xs[c], y: bottom + 19, 'text-anchor': 'middle', class: 'bin-label'}, bin.label)));
    svg.append(node('text', {x: (left + right) / 2, y: height - 3, 'text-anchor': 'middle', class: 'bin-label'}, 'Idade em anos · faixas apenas no desenho'));
    actualState.counts.forEach((values, r) => values.forEach((n, c) => {
      const value = mode === 'marginal' ? before.counts[r][c] + (target.counts[r][c] - before.counts[r][c]) * freeProgress : n;
      const mark = node('g');
      mark.append(node('title', {}, `${data.bins[c].label} anos; cardiopatia ${r ? 'Sim' : 'Não'}: ${count(n)} fichas; ${fmt(actualState.conditional_percent[r][c], 1)}% dentro do grupo.`));
      mark.append(node('circle', {cx: xs[c], cy: ys[r], r: radius * Math.sqrt(value / maximum), class: 'bubble' + (r ? ' row-yes' : '')}));
      const labels = node('g', {opacity: morphing ? 0 : 1});
      labels.append(node('text', {x: xs[c], y: ys[r] - 3, 'text-anchor': 'middle', class: 'cell-count'}, count(n)));
      labels.append(node('text', {x: xs[c], y: ys[r] + 14, 'text-anchor': 'middle', class: 'cell-percent'}, fmt(actualState.conditional_percent[r][c], 1) + '%'));
      mark.append(labels); svg.append(mark);
    }));
    if (mode === 'within' && phase.row !== undefined) {
      const flow = focusedFlow(phase.row, clamp(phase.progress));
      if (flow) {
        const y = ys[phase.row] - 23, controlY = y - 36, startX = xs[flow.from], endX = xs[flow.to];
        const path = `M ${startX} ${y} Q ${(startX + endX) / 2} ${controlY} ${endX} ${y}`;
        svg.append(node('path', {d: path, class: 'flow-line'}));
        const progress = ease(clamp(flow.progress));
        const px = (1 - progress) * (1 - progress) * startX + 2 * (1 - progress) * progress * (startX + endX) / 2 + progress * progress * endX;
        const py = (1 - progress) * (1 - progress) * y + 2 * (1 - progress) * progress * controlY + progress * progress * y;
        svg.append(node('circle', {cx: px, cy: py, r: 3.5, class: 'flow-dot'}));
        const badgeX = (startX + endX) / 2, badgeY = y - 20, badgeWidth = Math.max(34, String(flow.n).length * 7 + 12);
        const badge = node('g', {class: 'flow-label'});
        badge.append(node('rect', {x: badgeX - badgeWidth / 2, y: badgeY - 11, width: badgeWidth, height: 20, rx: 3}));
        badge.append(node('text', {x: badgeX, y: badgeY + 3, 'text-anchor': 'middle'}, count(flow.n)));
        badge.append(node('title', {}, `${count(flow.n)} fichas: faixa ${data.bins[flow.from].label} → ${data.bins[flow.to].label}, dentro do grupo cardiopatia ${phase.row ? 'Sim' : 'Não'}.`));
        svg.append(badge);
      }
    }
    host.replaceChildren(svg);
  }

  function drawLoss() {
    const host = $('error-plot'), width = host.getBoundingClientRect().width, compact = width < 600;
    const height = compact ? 180 : 148, left = compact ? 95 : 124, right = width - (compact ? 9 : 154);
    const results = data.results.global;
    const low = Math.min(0, ...['marginal', 'within'].map(mode => results[mode].difference_mean - results[mode].difference_sd));
    const high = Math.max(0, ...['marginal', 'within'].map(mode => results[mode].difference_mean + results[mode].difference_sd));
    const rough = (high - low) / 4 || .001, power = 10 ** Math.floor(Math.log10(rough));
    const step = [1, 2, 2.5, 5, 10].find(value => value * power >= rough) * power;
    const minimum = Math.floor(low / step) * step, rawMaximum = Math.ceil(high / step) * step;
    const maximum = rawMaximum > minimum ? rawMaximum : minimum + step;
    const x = value => left + 6 + (value - minimum) / (maximum - minimum) * (right - left - 12);
    const axisY = compact ? 148 : 119;
    const svg = node('svg', {viewBox: `0 0 ${width} ${height}`, height, role: 'img', 'aria-label': 'Aumento de log loss, média e um desvio padrão entre cinquenta embaralhamentos'});
    svg.append(node('title', {}, 'Importância da idade contínua: média de cinquenta embaralhamentos'), node('desc', {}, 'A mesma escala compara os procedimentos livre e dentro dos grupos. Os traços mostram um desvio padrão amostral, não intervalos de confiança.'));
    for (let tick = minimum; tick <= maximum + step / 100; tick += step) {
      svg.append(node('line', {x1: x(tick), x2: x(tick), y1: 8, y2: axisY - 19, class: tick === 0 ? 'zero' : 'grid'}));
      svg.append(node('text', {x: x(tick), y: axisY, 'text-anchor': 'middle', class: 'small'}, fmt(tick, 3)));
    }
    [['marginal', 'Livre'], ['within', 'Por grupo']].forEach(([mode, label], i) => {
      const result = results[mode], y = (compact ? 40 : 28) + i * (compact ? 66 : 52), mean = result.difference_mean, sd = result.difference_sd;
      svg.append(node('text', {x: 0, y, class: 'method'}, label));
      svg.append(node('text', {x: 0, y: y + 17, class: 'small'}, `Erro ${fmt(result.after_mean)}`));
      svg.append(node('line', {x1: x(mean - sd), x2: x(mean + sd), y1: y - 3, y2: y - 3, class: 'whisker'}));
      [mean - sd, mean + sd].forEach(value => svg.append(node('line', {x1: x(value), x2: x(value), y1: y - 9, y2: y + 3, class: 'whisker'})));
      const point = node('circle', {cx: x(mean), cy: y - 3, r: 4.5, class: mode});
      point.append(node('title', {}, `${label}: ${fmt(mean)} ± ${fmt(sd)} de aumento de log loss; erro após embaralhar ${fmt(result.after_mean)}.`)); svg.append(point);
      svg.append(node('text', {x: width - 1, y: compact ? y - 19 : y + 1, 'text-anchor': 'end', class: 'value'}, `${fmt(mean)} ± ${fmt(sd)}`));
    });
    svg.append(node('text', {x: (left + right) / 2, y: height - 5, 'text-anchor': 'middle'}, 'Aumento de log loss (PFI)'));
    host.replaceChildren(svg);
  }

  function render() {
    if (!data) return;
    const phase = stateAt(elapsed);
    if (phase.key !== previousPhase) {
      $('phase').textContent = phase.title; $('phase-detail').textContent = phase.detail; previousPhase = phase.key;
      document.querySelectorAll('.facet').forEach(panel => panel.dataset.active = String(phase.key.startsWith('free') ? panel.dataset.mode === 'marginal' : phase.key.startsWith('within') ? panel.dataset.mode === 'within' : phase.key === 'original' || phase.key === 'reset' ? panel.dataset.mode === 'original' : false));
    }
    if (phase.row !== undefined) {
      const flow = focusedFlow(phase.row, clamp(phase.progress));
      if (flow) $('phase-detail').textContent = `${phase.detail} Em foco: ${count(flow.n)} fichas mudam da faixa ${data.bins[flow.from].label} para ${data.bins[flow.to].label}.`;
    }
    modes.forEach(mode => plot(mode, phase));
  }

  function updateButtons() {
    $('play').textContent = reduced.matches ? 'Próximo momento' : playing ? 'Pausar' : elapsed >= timeline.end ? 'Reproduzir' : elapsed === 0 ? 'Reproduzir' : 'Continuar';
    $('play').setAttribute('aria-pressed', String(playing));
  }
  function pause() {playing = false; cancelAnimationFrame(frame); frame = 0; lastTime = null; updateButtons(); render();}
  function tick(time) {
    if (!playing) return;
    if (lastTime !== null) elapsed = Math.min(timeline.end, elapsed + time - lastTime);
    lastTime = time;
    if (time - lastPaint > 30 || elapsed >= timeline.end) {render(); lastPaint = time;}
    if (elapsed >= timeline.end) {playing = false; frame = 0; lastTime = null; updateButtons(); return;}
    frame = requestAnimationFrame(tick);
  }
  function start(reset) {
    cancelAnimationFrame(frame); lastTime = null; previousPhase = '';
    if (reset || elapsed >= timeline.end) elapsed = 0;
    if (reduced.matches) {playing = false; inspectStep = 0; render(); updateButtons(); return;}
    playing = true; render(); updateButtons(); frame = requestAnimationFrame(tick);
  }
  $('play').addEventListener('click', () => {
    if (reduced.matches) {
      const moments = [0, timeline.freeEnd + 1, timeline.reset + 1, timeline.groups + timeline.rowDuration * .24, timeline.groups + timeline.rowDuration * 1.24, timeline.end];
      inspectStep = (inspectStep + 1) % moments.length; elapsed = moments[inspectStep]; previousPhase = ''; render(); updateButtons();
    } else if (playing) pause(); else start(false);
  });
  $('replay').addEventListener('click', () => start(true));
  document.addEventListener('visibilitychange', () => {if (document.hidden && playing) pause();});
  reduced.addEventListener('change', () => {if (playing) pause(); updateButtons();});

  fetch(document.body.dataset.evidence, {cache: 'no-cache'}).then(response => {
    if (!response.ok) throw Error('A prévia aguarda a evidência registrada. Nenhum valor de demonstração foi incluído.');
    return response.json();
  }).then(study => {
    validate(study); data = study;
    $('study').hidden = false; $('load-status').hidden = true;
    const meta = data.metadata, original = data.plot.states.original;
    $('scope').textContent = `Teste ${meta.year || 2024} · ${count(meta.n_cohort)} fichas · ${count(meta.n_excluded)} excluídas deste recorte · cardiopatia conhecida e idade válida · semente ${meta.seed}`;
    $('association-note').textContent = `Idade real × cardiopatia: Pearson r = ${fmt(data.association.pearson_continuous_original, 3)}. A relação é moderada neste recorte. As faixas só facilitam a leitura.`;
    $('denominators').textContent = `Cardiopatia Não: n = ${count(original.y_marginals[0])} · Sim: n = ${count(original.y_marginals[1])}. Composições do primeiro sorteio registrado; abaixo, importância média dos ${count(meta.repeats)} sorteios.`;
    $('baseline').textContent = fmt(data.results.global.baseline);
    $('error-note').textContent = `Média de ${count(meta.repeats)} sorteios ±1 desvio padrão amostral. Mesmo modelo e mesmas fichas. No primeiro sorteio: erro livre ${fmt(data.first_losses.marginal)}; por grupo ${fmt(data.first_losses.within)}.`;
    $('source-note').textContent = 'Evidência: módulo 10, internals §9; importância contínua registrada na §8.';
    render(); drawLoss(); updateButtons();
    let lastWidth = 0;
    observer = new ResizeObserver(entries => {
      const width = Math.round(entries[0].contentRect.width);
      if (width !== lastWidth) {lastWidth = width; cancelAnimationFrame(resizeFrame); resizeFrame = requestAnimationFrame(() => {render(); drawLoss();});}
    }); observer.observe($('study'));
    window.addEventListener('pagehide', () => {cancelAnimationFrame(frame); cancelAnimationFrame(resizeFrame); observer.disconnect();}, {once: true});
  }).catch(error => {
    playing = false; cancelAnimationFrame(frame); $('study').hidden = true; $('load-status').hidden = false;
    $('load-status').textContent = error.message; $('load-status').className = 'error-state';
  });
})();
