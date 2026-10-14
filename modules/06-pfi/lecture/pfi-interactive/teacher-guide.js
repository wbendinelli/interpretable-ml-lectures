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
  const row=evidence.preview.rows[Number(el('case-select').value)],round=evidence.preview.rounds[Number(el('reading-feature').value)],i=Number(el('case-select').value),y=row.y_obito,p=round.probability[i],q=y?p:1-p,originalQ=y?row.p_original:1-row.p_original,loss=round.individual_loss[i];
  el('read-y').textContent=y?'Óbito · 1':'Sobrevida · 0';el('read-p').textContent=f(p,3);el('read-observed').textContent=f(q,3);el('read-loss').textContent=f(loss);
  el('original-reading').textContent=`Original: p(óbito) = ${f(row.p_original,3)}; probabilidade do resultado ocorrido = ${f(originalQ,3)}; perda = ${f(row.loss_original)}. Após a troca: perda = ${f(loss)}.`;
  el('case-reading').textContent=loss>row.loss_original?'Nesta ficha, o modelo deu menos probabilidade ao desfecho ocorrido: a perda aumentou.':loss<row.loss_original?'Nesta ficha, o modelo deu mais probabilidade ao desfecho ocorrido: a perda diminuiu.':'Esta ficha recebeu a mesma entrada efetiva; sua probabilidade e sua perda ficaram iguais.';
  const value=round.shuffled_values[i],original=round.values[i],label=round.cell==='age'?'Idade de entrada (anos)':'Saturação baixa de entrada',display=v=>round.cell==='age'?f(v,2):({sim:'Sim',nao:'Não',desconhecido:'Desconhecido'}[v]);
  el('case-input').textContent=`Ficha ${row.record} · ${label}: ${display(original)} → ${display(value)}. O novo valor veio de outra linha do teste; a ficha observada continua a mesma.`;
  const x=value=>80+value*550,maxLoss=Math.max(5,loss,row.loss_original),yp=value=>185-value/maxLoss*145;
  const path=Array.from({length:100},(_,j)=>{const v=.01+j*.01;return `${j?'L':'M'}${x(v)} ${yp(-Math.log(v))}`;}).join(' ');
  el('probability-diagram').innerHTML=`<title>Log loss da ficha ${row.record}: penalidade em função da probabilidade do resultado ocorrido</title><path d="M80 35 V185 H630" fill="none" stroke="currentColor" opacity=".2"/><path d="${path}" fill="none" stroke="currentColor" opacity=".5" stroke-width="2"/><circle cx="${x(originalQ)}" cy="${yp(row.loss_original)}" r="6" fill="currentColor" opacity=".35"/><circle cx="${x(q)}" cy="${yp(loss)}" r="7" fill="currentColor"/><line x1="${x(q)}" y1="${yp(loss)}" x2="${x(q)}" y2="185" stroke="currentColor" opacity=".2" stroke-dasharray="3 4"/><text x="80" y="25">Perda · −ln(q)</text><text x="76" y="203" text-anchor="end">0</text><text x="630" y="203" text-anchor="middle">1</text><text x="350" y="230" text-anchor="middle">q: probabilidade atribuída ao desfecho ocorrido</text><text x="500" y="40">● Original · cinza</text><text x="500" y="62">● Após a troca · escuro</text>`;
 }
 el('case-select').addEventListener('change',reading);el('reading-feature').addEventListener('change',reading);
 Promise.all([fetch('data/pfi-aggregates.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error();return r.json();}),fetch('data/pfi-teaching-records.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error();return r.json();})]).then(([aggregate,cases])=>{
  if(aggregate.protocol.primary_metric!=='logloss'||cases.preview.metric!=='logloss')throw Error('Metric mismatch');
  evidence=cases;
  el('global-values').innerHTML=cases.preview.rounds.map(round=>{const r=round.full_test;return `<tr><td>${round.cell==='age'?'Idade':'Saturação baixa'}</td><td>${f(r.before)}</td><td>${f(round.full_test_single_loss)}</td><td>${f(r.after_mean)} ± ${f(r.after_sd)}</td><td>+${f(r.relative_increase_percent,2)}%</td></tr>`;}).join('');
  el('global-scope').textContent=`Teste temporal completo: ${aggregate.protocol.n_evaluation.toLocaleString('pt-BR')} registros; ${aggregate.protocol.repeats} permutações por variável. Porcentagens calculadas antes de arredondar. SD descreve a variação entre permutações, com modelo e teste fixos.`;
  el('case-select').innerHTML=cases.preview.rows.map((r,i)=>`<option value="${i}"${i===7?' selected':''}>Ficha ${r.record}</option>`).join('');
  reading();
 }).catch(()=>{el('guide-error').hidden=false;});
 const requested=location.hash.replace('#note-','');
 const known=[...document.querySelectorAll('[data-note]')].some(article=>article.dataset.note===requested);
 tab(known?'notes':location.hash==='#reading'?'reading':'audit');note(known?requested:'cover');
})();
