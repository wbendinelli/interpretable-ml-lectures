'use strict';
(()=>{
 const el=id=>document.getElementById(id),f=(value,digits=4)=>Number(value).toLocaleString('pt-BR',{minimumFractionDigits:digits,maximumFractionDigits:digits});
 let evidence=null;
 function tab(id){document.querySelectorAll('[data-guide-tab]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.guideTab===id)));document.querySelectorAll('[data-guide-panel]').forEach(panel=>panel.hidden=panel.dataset.guidePanel!==id);}
 document.querySelectorAll('[data-guide-tab]').forEach(button=>button.addEventListener('click',()=>tab(button.dataset.guideTab)));
 function note(route){document.querySelectorAll('[data-note]').forEach(article=>article.hidden=article.dataset.note!==route);document.querySelectorAll('[data-note-link]').forEach(link=>link.setAttribute('aria-current',String(link.dataset.noteLink===route)));el('teacher-slide').value=route;}
 el('teacher-slide').addEventListener('change',event=>note(event.target.value));
 document.querySelectorAll('[data-note-link]').forEach(link=>link.addEventListener('click',event=>{event.preventDefault();note(link.dataset.noteLink);}));
 function reading(){
  if(!evidence)return;
  const row=evidence.preview.rows[Number(el('case-select').value)],round=evidence.preview.rounds[Number(el('reading-feature').value)],i=Number(el('case-select').value),y=row.y_obito,p=round.probability[i],distance=Math.abs(p-y),loss=distance**2;
  el('read-y').textContent=y?'Óbito · 1':'Sobrevida · 0';el('read-p').textContent=f(p,3);el('read-distance').textContent=f(distance,3);el('read-loss').textContent=f(loss);
  el('original-reading').textContent=`Na previsão original: p = ${f(row.p_original,3)}; perda = ${f(row.brier_original)}. Depois desta troca: perda = ${f(loss)}.`;
  el('case-reading').textContent=loss>row.brier_original?'Nesta ficha, a probabilidade ficou mais distante do desfecho: a perda aumentou.':loss<row.brier_original?'Nesta ficha, a probabilidade ficou mais perto do desfecho: a perda diminuiu.':'Esta ficha recebeu a mesma entrada efetiva; sua probabilidade e sua perda ficaram iguais.';
  const value=round.shuffled_values[i],original=round.values[i],label=round.cell==='age'?'Idade de entrada (anos)':'Saturação baixa de entrada',display=v=>round.cell==='age'?f(v,2):({sim:'Sim',nao:'Não',desconhecido:'Desconhecido'}[v]);
  el('case-input').textContent=`Ficha ${row.record} · ${label}: ${display(original)} → ${display(value)}. O novo valor veio de outra linha do teste; a ficha observada continua a mesma.`;
  const px=70+p*570,yx=70+y*570;
  el('probability-diagram').innerHTML=`<title>Probabilidade após a troca e distância até o desfecho observado da ficha ${row.record}</title><line x1="70" y1="62" x2="640" y2="62" stroke="currentColor" opacity=".18"/><line x1="${px}" y1="62" x2="${yx}" y2="62" stroke="currentColor" stroke-width="5" opacity=".4"/><circle cx="${px}" cy="62" r="7" fill="currentColor"/><circle cx="${yx}" cy="62" r="8" fill="white" stroke="currentColor" stroke-width="2"/><text x="70" y="102" text-anchor="middle">0</text><text x="640" y="102" text-anchor="middle">1</text><text x="${px}" y="30" text-anchor="middle">p = ${f(p,3)}</text><text x="${yx}" y="130" text-anchor="middle">desfecho = ${y}</text>`;
 }
 el('case-select').addEventListener('change',reading);el('reading-feature').addEventListener('change',reading);
 Promise.all([fetch('data/pfi-aggregates.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error();return r.json();}),fetch('data/pfi-teaching-records.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error();return r.json();})]).then(([aggregate,cases])=>{
  evidence=cases;
  el('global-values').innerHTML=cases.preview.rounds.map(round=>{const r=round.full_test;return `<tr><td>${round.cell==='age'?'Idade':'Saturação baixa'}</td><td>${f(r.before)}</td><td>${f(round.full_test_single_brier)}</td><td>${f(r.after_mean)} ± ${f(r.after_sd)}</td><td>+${f(r.relative_increase_percent,2)}%</td></tr>`;}).join('');
  el('global-scope').textContent=`Teste temporal completo: ${aggregate.protocol.n_evaluation.toLocaleString('pt-BR')} registros; ${aggregate.protocol.repeats} permutações por variável. Porcentagens calculadas antes de arredondar. SD descreve a variação entre permutações, com modelo e teste fixos.`;
  el('case-select').innerHTML=cases.preview.rows.map((r,i)=>`<option value="${i}"${i===7?' selected':''}>Ficha ${r.record}</option>`).join('');
  reading();
 }).catch(()=>{el('guide-error').hidden=false;});
 const requested=location.hash.replace('#note-','');
 const known=[...document.querySelectorAll('[data-note]')].some(article=>article.dataset.note===requested);
 tab(known?'notes':location.hash==='#reading'?'reading':'audit');note(known?requested:'cover');
})();
