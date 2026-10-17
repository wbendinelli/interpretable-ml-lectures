'use strict';
(() => {
  const ns = 'http://www.w3.org/2000/svg';
  const $ = id => document.getElementById(id);
  const number = (v, digits = 4) => {
    const value = Math.abs(Number(v)) < .5 * 10 ** -digits ? 0 : Number(v);
    return value.toLocaleString('pt-BR', {minimumFractionDigits: digits, maximumFractionDigits: digits});
  };
  const count = v => Number(v).toLocaleString('pt-BR');
  const node = (tag, attrs = {}, text) => {
    const element = document.createElementNS(ns, tag);
    Object.entries(attrs).forEach(([key, value]) => element.setAttribute(key, value));
    if (text !== undefined) element.textContent = text;
    return element;
  };
  let study, selected, observer;
  function bubbleFigure(candidate, mode, title) {
    const section = document.createElement('section'); section.className = 'composition';
    const heading = document.createElement('h3'); heading.textContent = title;
    const svg = node('svg', {role: 'img', 'aria-label': `${title}: ${candidate.feature_label} por ${candidate.group_label}`});
    section.append(heading, svg); $('compositions').append(section);
    const width = section.getBoundingClientRect().width, height = 246;
    const left = 68, right = width - 10, top = 9, bottom = height - 42;
    const xs = [left + (right - left) / 4, left + 3 * (right - left) / 4];
    const ys = [top + (bottom - top) * .75, top + (bottom - top) * .25];
    const plot = candidate.plot, state = plot.states[mode];
    const largest = Math.max(...Object.values(plot.states).flatMap(s => s.counts.flat()));
    const radius = Math.max(12, Math.min(36, (right - left) / 4 - 8, (bottom - top) / 4 - 8));
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`); svg.setAttribute('height', height);
    svg.append(node('title', {}, title), node('desc', {}, 'A área conta registros. Cada percentual usa o total do respectivo grupo, representado por uma linha.'));
    svg.append(node('rect', {x: left, y: top, width: right - left, height: bottom - top, class: 'chart-frame'}));
    svg.append(node('line', {x1: (left + right) / 2, x2: (left + right) / 2, y1: top, y2: bottom, class: 'grid-line'}));
    svg.append(node('line', {x1: left, x2: right, y1: (top + bottom) / 2, y2: (top + bottom) / 2, class: 'grid-line'}));
    ['Não', 'Sim'].forEach((label, i) => {
      svg.append(node('text', {x: xs[i], y: bottom + 19, 'text-anchor': 'middle'}, label));
      svg.append(node('text', {x: left - 9, y: ys[i] + 4, 'text-anchor': 'end'}, label));
    });
    svg.append(node('text', {x: (left + right) / 2, y: height - 2, 'text-anchor': 'middle', class: 'axis-label'}, candidate.feature_label));
    svg.append(node('text', {x: 14, y: (top + bottom) / 2, transform: `rotate(-90 14 ${(top + bottom) / 2})`, 'text-anchor': 'middle', class: 'axis-label'}, candidate.group_label));
    state.counts.forEach((row, r) => row.forEach((value, col) => {
      const mark = node('g');
      const share = state.conditional_percent[r][col];
      mark.append(node('title', {}, `${candidate.group_label}: ${r ? 'Sim' : 'Não'}; ${candidate.feature_label}: ${col ? 'Sim' : 'Não'}. ${count(value)} registros, ${number(share, 1)}% dentro do grupo.`));
      mark.append(node('circle', {cx: xs[col], cy: ys[r], r: radius * Math.sqrt(value / largest), class: 'bubble' + (r === 1 && col === 1 ? ' both' : '')}));
      mark.append(node('text', {x: xs[col], y: ys[r] - 2, 'text-anchor': 'middle', class: 'cell-number'}, count(value)));
      mark.append(node('text', {x: xs[col], y: ys[r] + 16, 'text-anchor': 'middle', class: 'cell-percent'}, number(share, 1) + '%'));
      svg.append(mark);
    }));
  }
  function drawLoss(candidate) {
    const host = $('loss-chart'); host.replaceChildren();
    const svg = node('svg', {role: 'img', 'aria-label': 'PFI média livre e por grupo, com um desvio padrão entre as permutações'});
    host.append(svg);
    const width = host.getBoundingClientRect().width, compact = width < 700;
    const height = 186, left = compact ? 116 : 210, right = width - (compact ? 12 : 175);
    const results = candidate.results.global, rows = [['marginal', 'Livre'], ['within', 'Por grupo']];
    const low = Math.min(0, ...rows.map(([mode]) => results[mode].difference_mean - results[mode].difference_sd));
    const high = Math.max(0, ...rows.map(([mode]) => results[mode].difference_mean + results[mode].difference_sd));
    const rough = (high - low) / 4 || .001, power = 10 ** Math.floor(Math.log10(rough));
    const step = [1, 2, 2.5, 5, 10].find(v => v * power >= rough) * power;
    const min = Math.floor(low / step) * step, rawMax = Math.ceil(high / step) * step, max = rawMax > min ? rawMax : min + step;
    const scale = value => left + 10 + (value - min) / (max - min) * (right - left - 20);
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`); svg.setAttribute('height', height);
    svg.append(node('title', {}, 'Aumento médio de log loss após embaralhar a entrada'));
    for (let tick = min; tick <= max + step / 100; tick += step) {
      svg.append(node('line', {x1: scale(tick), x2: scale(tick), y1: 12, y2: 137, class: 'grid-line'}));
      svg.append(node('text', {x: scale(tick), y: 157, 'text-anchor': 'middle', class: 'tick'}, number(tick)));
    }
    rows.forEach(([mode, label], i) => {
      const result = results[mode], y = i ? 106 : 43, mean = result.difference_mean, sd = result.difference_sd;
      svg.append(node('text', {x: 0, y, class: 'method'}, label));
      svg.append(node('text', {x: 0, y: y + 17, class: 'tick'}, `Erro: ${number(result.after_mean)}`));
      svg.append(node('line', {x1: scale(mean - sd), x2: scale(mean + sd), y1: y - 3, y2: y - 3, class: 'whisker'}));
      [mean - sd, mean + sd].forEach(v => svg.append(node('line', {x1: scale(v), x2: scale(v), y1: y - 10, y2: y + 4, class: 'whisker'})));
      const point = node('circle', {cx: scale(mean), cy: y - 3, r: 5, class: mode === 'marginal' ? 'free' : 'within'});
      point.append(node('title', {}, `${label}: ${number(mean)} ± ${number(sd)} de aumento de log loss.`)); svg.append(point);
      svg.append(node('text', {x: width - 1, y: compact ? y - 18 : y + 2, 'text-anchor': 'end', class: 'value'}, `${number(mean)} ± ${number(sd)}`));
    });
    svg.append(node('text', {x: (left + right) / 2, y: 181, 'text-anchor': 'middle'}, 'Aumento de log loss (PFI)'));
  }
  function draw() {
    const candidate = selected;
    if (!candidate) return;
    $('compositions').replaceChildren();
    if (candidate.kind === 'binary' && candidate.plot) {
      [['original', 'Original'], ['marginal', 'Embaralhamento livre'], ['within', 'Dentro dos grupos']].forEach(([mode, title]) => bubbleFigure(candidate, mode, title));
      $('composition-note').textContent = `Embaralhamos ${candidate.feature_label.toLowerCase()}. Os grupos são as linhas de ${candidate.group_label.toLowerCase()}. As duas operações começam nas entradas originais. Composições do primeiro sorteio registrado; a PFI abaixo resume os ${count(study.metadata.repeats)} sorteios. Percentuais dentro de cada grupo; áreas proporcionais às contagens.`;
    } else {
      const p = document.createElement('p'); p.className = 'numeric-note secondary';
      p.textContent = 'Aqui a entrada embaralhada é numérica: a idade em anos. Usamos os valores reais, sem convertê-los em faixas. Em cada procedimento, somente as idades são redistribuídas. O gráfico abaixo compara as duas importâncias.';
      $('compositions').append(p); $('composition-note').textContent = '';
    }
    drawLoss(candidate);
  }
  function choose(id) {
    const candidate = study.candidates.find(c => c.id === id);
    if (!candidate) return;
    selected = candidate; $('candidate').value = id;
    $('comparison-title').textContent = `${candidate.feature_label} dentro dos grupos de ${candidate.group_label.toLowerCase()}`;
    $('candidate-purpose').textContent = candidate.rationale;
    const cohort = candidate.cohort, nFull = cohort.n + cohort.n_excluded;
    $('scope').textContent = `Teste ${study.metadata.year || study.metadata.period} · ${count(cohort.n)} de ${count(nFull)} registros · ${count(cohort.n_excluded)} excluídos deste recorte · Pearson r = ${number(candidate.association.pearson_r, 3)} · ${candidate.kind === 'binary' ? 'Somente respostas Sim/Não nas duas entradas' : 'Idade válida e grupo com resposta Sim/Não'}`;
    $('baseline').textContent = `Log loss original deste recorte: ${number(candidate.results.global.baseline)}`;
    const readings = {
      saturacao__by__desc_resp: 'Neste recorte, os dois procedimentos aumentam o erro. A diferença entre suas importâncias é pequena e a associação observada é modesta. A literatura torna a coocorrência plausível; este gráfico não demonstra uma grande correção do método.',
      perd_olft__by__perd_pala: 'A associação entre as entradas é mais visível, mas as duas importâncias ficam próximas de zero neste modelo. Estar relacionado com outra entrada não garante uma contribuição importante para o desempenho do preditor.',
      perd_pala__by__perd_olft: 'A associação entre as entradas é mais visível, mas as duas importâncias ficam próximas de zero neste modelo. Estar relacionado com outra entrada não garante uma contribuição importante para o desempenho do preditor.',
      idade_anos__by__cardiopati: 'A idade apresenta PFI positiva nos dois procedimentos deste recorte. As estimativas continuam próximas. Antes de substituir o slide, precisamos observar a distribuição das idades e as combinações alteradas.'
    };
    $('reading').textContent = readings[candidate.id] || 'O gráfico compara a perda do mesmo preditor nas mesmas fichas. Os procedimentos redistribuem a informação sob regras diferentes; o modelo permanece fixo. A diferença pode ter qualquer sinal e precisa ser lida junto da relação observada e da variação entre os sorteios.';
    document.querySelectorAll('#results-body tr').forEach(row => row.dataset.selected = String(row.dataset.id === id));
    draw();
    const url = new URL(location.href); url.searchParams.set('pair', id); history.replaceState(null, '', url);
  }
  function resultsTable() {
    const body = $('results-body'); body.replaceChildren();
    study.candidates.forEach(candidate => {
      const row = document.createElement('tr'); row.dataset.id = candidate.id;
      const first = document.createElement('td'), button = document.createElement('button'); button.type = 'button'; button.textContent = candidate.feature_label;
      button.addEventListener('click', () => {choose(candidate.id); $('comparison').scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});}); first.append(button); row.append(first);
      const result = candidate.results.global;
      const cells = [candidate.group_label, count(candidate.cohort.n), number(candidate.association.pearson_r, 3), `${number(result.marginal.difference_mean)} ± ${number(result.marginal.difference_sd)}`, `${number(result.within.difference_mean)} ± ${number(result.within.difference_sd)}`, number(result.gap.mean)];
      cells.forEach(value => {const td = document.createElement('td'); td.textContent = value; row.append(td);}); body.append(row);
    });
  }
  $('candidate').addEventListener('change', event => choose(event.target.value));
  fetch(document.body.dataset.evidence, {cache: 'no-cache'}).then(response => {
    if (!response.ok) throw Error('A evidência da comparação ainda não está disponível.');
    return response.json();
  }).then(data => {
    if (!Array.isArray(data.candidates) || !data.candidates.length) throw Error('Não há comparações registradas.');
    study = data;
    for (const c of study.candidates) {
      if (!Number.isFinite(c.results.global.baseline) || c.results.global.marginal.after.length !== study.metadata.repeats || c.results.global.within.after.length !== study.metadata.repeats) throw Error('Evidência incompleta.');
      const option = document.createElement('option'); option.value = c.id; option.textContent = `${c.feature_label} — grupos: ${c.group_label}`; $('candidate').append(option);
    }
    $('load-status').hidden = true; $('comparison').hidden = false; $('all-results').hidden = false;
    $('protocol-summary').textContent = `${count(study.candidates.length)} direções avaliadas · ${count(study.metadata.repeats)} sorteios por procedimento · semente ${study.metadata.seed}`;
    resultsTable();
    const requested = new URL(location.href).searchParams.get('pair');
    choose(study.candidates.some(c => c.id === requested) ? requested : study.candidates.find(c => c.feature === 'diabetes' && c.group_feature === 'cardiopati')?.id || study.candidates[0].id);
    let width = 0;
    observer = new ResizeObserver(entries => {const next = Math.round(entries[0].contentRect.width); if (next !== width) {width = next; requestAnimationFrame(draw);}}); observer.observe($('comparison'));
  }).catch(error => {$('load-status').textContent = error.message; $('load-status').className = 'error-state';});
})();
