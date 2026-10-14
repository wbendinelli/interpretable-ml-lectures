'use strict';
(()=>{
 const el=id=>document.getElementById(id),reduced=matchMedia('(prefers-reduced-motion: reduce)');
 const evidence=Promise.all([fetch('data/pfi-aggregates.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('Evidence unavailable');return r.json();}),fetch('data/pfi-teaching-records.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('Teaching records unavailable');return r.json();})]).then(([aggregate,teaching])=>({...aggregate,preview:teaching.preview}));
 const f=(x,digits=4)=>Number(x).toFixed(digits),count=x=>Number(x).toLocaleString('en-US');
 const escape=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
 let data=null,page=null,epoch=0,timers=[],paused=false,repeat=0,repeatNodes=[],svgReady=false,repeatRun=0;
 function stop(){epoch++;repeatRun++;page=null;timers.forEach(clearTimeout);timers=[];repeatNodes=[];svgReady=false;}
 function later(fn,ms){const token=epoch;timers.push(setTimeout(()=>{if(token===epoch)fn();},ms));}
 const bridges={
  65:{title:'Importance and feature selection',subtitle:'A ranking describes reliance. Selection needs a decision.',body:()=>`<div class="feature-stream">${data.rows.slice(0,5).map(r=>`<span>${r.label}</span>`).join('')}</div><div class="selection-path"><section><h3>Permutation importance</h3><p>Evaluate the fitted model with every input still available. Rank the change in error after each separate shuffle.</p><div class="code-balance">All original inputs remain in the model.</div></section><section><h3>A feature-selection study</h3><p>Choose candidate subsets, fit the candidate models and evaluate their predictive performance under a selection protocol.</p><div class="code-balance">A high PFI does not choose a subset for us.</div></section></div>`,takeaway:'Our top-feature chart explains the current model. We have not removed the remaining inputs or selected a new model.',molnar:'PFI gives a global view of predictive reliance. Its values depend on the fitted model and loss.',notes:'This develops Raschka’s warning that permutation importance is not itself feature selection. The ranking may inform a later selection study, but a top-feature cutoff requires a separate rule and evaluation. Redundant inputs and interactions can change how useful a subset is.'},

 };
 const codeStages=[
 '# From the training stage\nmodel = fitted_reference\nfeature = "idade_anos"',
 'p_original = np.asarray(\n    model.predict_proba(x_eval)[:, 1],\n    dtype=np.float64,\n)\ne_original = brier_score_loss(y_eval, p_original)',
 'errors = []\nfor order in orders:\n    x_permuted = x_eval.copy()\n    x_permuted[feature] = (\n        x_eval[feature].iloc[order]\n        .set_axis(x_eval.index)\n    )',
 '    p_permuted = np.asarray(\n        model.predict_proba(x_permuted)[:, 1],\n        dtype=np.float64,\n    )\n    errors.append(brier_score_loss(y_eval, p_permuted))',
 'delta = np.asarray(errors) - e_original\nmean = delta.mean()\nsd = delta.std(ddof=1)'
 ];
 function orderSetup(){return `rng = np.random.default_rng(${data.protocol.permutation_seed})\nrepeats = ${data.protocol.repeats}\norders = [rng.permutation(len(x_eval))\n          for _ in range(repeats)]`;}
 function fullAlgorithm(){return [codeStages[0],codeStages[1],orderSetup(),...codeStages.slice(2)].join('\n\n');}
 function repeatCode(){return `<div class="code-stage active repeat-executable"><p id="repeat-code-state" class="repeat-code-state">Prepare the recorded experiment</p><div class="repeat-block" data-repeat-phase="setup"><pre>${escape(orderSetup())}</pre></div><div class="repeat-loop"><pre>errors = []\nfor repeat, order in enumerate(orders, 1):</pre><div class="repeat-block" data-repeat-phase="shuffle"><pre>${escape('    x_perm = x_eval.copy()\n    shuffled = x_eval[feature].iloc[order]\n    x_perm[feature] = shuffled.set_axis(x_eval.index)')}</pre></div><div class="repeat-block" data-repeat-phase="predict"><pre>${escape('    p = model.predict_proba(x_perm)[:, 1]\n    p = np.asarray(p, dtype=np.float64)')}</pre></div><div class="repeat-block" data-repeat-phase="append"><pre>${escape('    errors.append(brier_score_loss(y_eval, p))')}</pre></div></div><div class="repeat-block repeat-summary" data-repeat-phase="summary"><p>After the loop</p><pre>${escape(codeStages[4])}</pre></div></div>`;}
 const steps=[
 {title:'A model fitted before PFI',subtitle:'The experiment receives an already trained predictor',molnar:'The input to PFI is an already trained model. Retraining answers a different question.',caption:'Training happens before the permutation loop. The loop contains predictions and error calculations, with no model refitting.',original:'Raschka starts with a fitted random forest. We use the fitted XGBoost reference from the SRAG training protocol.'},
 {title:'The original error',subtitle:'One reference for every input',molnar:'Evaluate loss on the original data first. This reference is shared across all inputs.',caption:'Brier needs predicted probabilities. A classifier’s default score method usually returns accuracy, so we calculate Brier explicitly.',original:'Raschka records accuracy on validation data. We record Brier on the temporal test. Higher accuracy is better; lower Brier is better.'},
 {title:'A separate shuffle for each input',subtitle:'The selected column moves. Outcomes stay in their rows.',molnar:'Permute only the selected input. Dependence between inputs can produce unrealistic combinations.',caption:'Every repeat copies the original evaluation matrix. Shuffling another variable starts again from that original matrix.',original:'The original diagram labels its rows “training examples” while the algorithm evaluates validation data. Here the table illustrates the real teaching subset of evaluation records. We keep y_eval unchanged, avoiding the ambiguous y_val_perm name.'},
 {title:'Error after one permutation',subtitle:'The same model evaluates the changed inputs',molnar:'Evaluate the perturbed inputs with the same model and observed outcomes.',caption:'This is one full-test shuffle. The next slide averages all recorded repeats. Its mean can differ from this individual result.',original:'For accuracy, importance is original score minus permuted score. For our Brier loss, importance is permuted error minus original error.'},
 {title:'Repeat the same experiment',subtitle:'A new row order, the original matrix, the same fitted model',molnar:'Repeat the shuffle and report its variation. The procedure is run separately for each input.',caption:'Our protocol uses 50 shuffles, each starting from the original inputs. The final mean and sample SD match the Age ranking. This repetition count is a choice, not proof of convergence.',original:'The motion replays our recorded full-test executions; it does not fit or run a model in the browser. Each dot is a complete Age shuffle, not an individual patient. The spread summarizes shuffling randomness, conditional on the fitted model and observed test set; it does not measure variation from retraining or from new patient samples.'}
 ];
 function bridge(){
  const b=bridges[page];el('bridge-title').textContent=b.title;el('bridge-subtitle').textContent=b.subtitle;el('bridge-content').innerHTML=b.body();el('bridge-takeaway').textContent=b.takeaway;el('bridge-molnar').textContent=b.molnar;el('bridge-notes').innerHTML=`<p>${b.notes}</p>`;
  if(!reduced.matches){[...el('bridge-content').children].forEach((n,i)=>n.animate([{opacity:0},{opacity:1}],{duration:850,delay:i*300,fill:'backwards'}));
   const routes=[...el('bridge-content').querySelectorAll('.method-route')];let step=0;function pulse(){routes.forEach(r=>[...r.children].forEach((n,i)=>n.classList.toggle('active',i===step)));step=(step+1)%3;later(pulse,2200);}if(routes.length)pulse();
   const features=[...el('bridge-content').querySelectorAll('.feature-stream span')];features.forEach((n,i)=>later(()=>n.classList.add('active'),i*500));
  }
 }
 function values(items){return `<dl class="execution-values">${items.map(([label,value,emphasis])=>`<dt>${label}</dt><dd${emphasis?' class="emphasis"':''}>${value}</dd>`).join('')}</dl>`;}
 function reading(index){
  const before=data.original.brier,trace=data.walkthrough,age=data.rows.find(r=>r.feature==='idade_anos');
  if(index===0)return `<p class="execution-label">SRAG reference</p><div class="code-lock">Same trained XGBoost<span>Parameters fixed throughout PFI</span></div>${values([['Training records',count(data.protocol.n_train)],['Model inputs',data.protocol.features.length]])}<p>The temporal evaluation records are separate from the records used to fit this model.</p>`;
  if(index===1)return `<p class="execution-label">Original temporal test</p><h3>Predict before changing any input</h3>${values([['Evaluation records',count(data.protocol.n_evaluation)],['Original Brier',f(before),true]])}<p>Death is the positive outcome. The probability is compared with the observed outcome for each record, then the squared errors are averaged.</p>`;
  if(index===2)return `<p class="execution-label">Eight receiver rows · full-test Age shuffle 1</p><table class="code-mini-table"><thead><tr><th>Row</th><th>Original age</th><th>Shuffled age</th><th>Low oxygen</th><th>Outcome</th></tr></thead><tbody>${data.preview.rows.map((row,i)=>`<tr><td>${row.record}</td><td>${f(row.idade_anos,2)}</td><td class="changed-value waiting">${f(data.preview.rounds[0].shuffled_values[i],2)}</td><td>${({sim:'Yes',nao:'No',desconhecido:'Unknown'}[row.saturacao])}</td><td class="unchanged-outcome">${row.y_obito?'Died':'Survived'}</td></tr>`).join('')}</tbody></table><p class="repeat-explanation">Only age moves. The whole test column is shuffled; these eight receiver rows are displayed.</p>`;
  if(index===3)return `<p class="execution-label">First recorded Age shuffle: full temporal test</p><h3>A single repeat has its own error</h3>${values([['Original Brier',f(before)],['Permuted Brier, repeat 1',f(trace.first_after)],['Difference, repeat 1','+'+f(trace.first_difference),true]])}<p>The first repeat and the overall mean are different quantities. The baseline remains ${f(before)} in both.</p>`;
  return `<p class="execution-label">Age · original Brier ${f(before)} · full temporal test</p><div id="repeat-chart" class="repeat-chart"></div><div class="repeat-controls"><label for="repeat-count">Completed</label><input id="repeat-count" type="range" min="0" max="${trace.after.length}" value="0" disabled><output id="repeat-counter">0 / ${trace.after.length}</output><button id="repeat-pause" aria-pressed="false" disabled>Pause</button><button id="repeat-next" disabled>Next repeat →</button></div><div id="repeat-latest" class="repeat-latest"></div><div id="repeat-values"></div><p id="repeat-reading" class="repeat-explanation"></p><button id="back-to-ranking" class="text-button">Compare with the ranking ↗</button>`;
 }
 function setRepeatPhase(phase,n){
  const labels={setup:'Create reproducible row orders',shuffle:'Copy + shuffle Age',predict:'Predict without refitting',append:'Store Brier error',summary:'Loop complete · summarize errors'};
  el('repeat-code-state').textContent=(phase==='setup'||phase==='summary'?'':`Repeat ${n} / ${data.walkthrough.after.length} · `)+labels[phase];
  el('walkthrough-code').querySelectorAll('[data-repeat-phase]').forEach(node=>node.classList.toggle('executing',node.dataset.repeatPhase===phase));
 }
 function syncRepeatControls(){
  el('repeat-pause').textContent=paused?(repeat===data.walkthrough.after.length?'Replay':'Resume'):'Pause';
  el('repeat-pause').setAttribute('aria-pressed',String(paused));
  el('repeat-pause').disabled=!svgReady;el('repeat-count').disabled=!svgReady;
  el('repeat-next').disabled=!svgReady||repeat===data.walkthrough.after.length;
 }
 function updateRepeats(n,updateCode=true){
  repeat=n;el('repeat-count').value=n;el('repeat-counter').textContent=`${n} / ${data.walkthrough.after.length}`;
  const valuesSoFar=data.walkthrough.difference.slice(0,n),mean=n?valuesSoFar.reduce((a,b)=>a+b,0)/n:null,sd=n>1?Math.sqrt(valuesSoFar.reduce((a,b)=>a+(b-mean)**2,0)/(n-1)):null;
  el('repeat-latest').innerHTML=n?`<p>Recorded repeat ${n}</p><div><span>Permuted Brier<strong>${f(data.walkthrough.after[n-1])}</strong></span><span>Increase in Brier<strong>+${f(data.walkthrough.difference[n-1])}</strong></span></div>`:'<p>The original error is ready. No permuted result has been recorded yet.</p>';
  el('repeat-values').innerHTML=values([['Running mean increase',mean===null?'—':'+'+f(mean),true],['Sample SD',sd===null?'—':f(sd)]]);
  repeatNodes.forEach((node,i)=>{node.style.opacity=i<n?'1':'0';});
  const complete=n===data.walkthrough.after.length;
  for(const id of ['repeat-mean','repeat-sd']){const node=el('repeat-chart').querySelector('#'+id);if(node)node.style.opacity=complete?'1':'0';}
  el('repeat-reading').textContent=complete?`All ${n} repeats: +${f(data.walkthrough.mean_difference)} ± ${f(data.walkthrough.sd_difference)} SD. Same full-precision values as the Age ranking.`:n?'Each new result enters the running mean. Sample SD needs more than one completed repeat.':'The seed makes the sequence reproducible. Each order rearranges all evaluation rows.';
  if(updateCode)setRepeatPhase(complete?'summary':n?'append':'setup',n);
  syncRepeatControls();
 }
 function repeatLoop(){
  const run=++repeatRun;
  function schedule(fn,ms){later(()=>{if(run===repeatRun&&!paused&&page===71&&svgReady)fn();},ms);}
  function begin(){
   const next=repeat+1;
   setRepeatPhase('shuffle',next);
   schedule(()=>{setRepeatPhase('predict',next);schedule(()=>{setRepeatPhase('append',next);updateRepeats(next,false);if(next===data.walkthrough.after.length){schedule(()=>{setRepeatPhase('summary',next);schedule(()=>{updateRepeats(0);schedule(begin,900);},8000);},500);}else schedule(begin,300);},300);},300);
  }
  if(repeat===data.walkthrough.after.length)updateRepeats(0);
  schedule(begin,repeat?300:900);
 }
 function pauseRepeats(){paused=true;repeatRun++;syncRepeatControls();}
 async function repeatChart(){
  const token=epoch,response=await fetch('figures/pfi-age-repeats.svg');if(!response.ok)throw Error('Recorded repeat chart unavailable');const source=await response.text();if(token!==epoch||page!==71)return;
  const doc=new DOMParser().parseFromString(source,'image/svg+xml').documentElement;doc.setAttribute('role','img');doc.setAttribute('aria-label','Age importance across recorded full-test permutations. Line is mean and band is one sample standard deviation.');el('repeat-chart').replaceChildren(document.importNode(doc,true));repeatNodes=[...el('repeat-chart').querySelectorAll('[id^="repeat-point-"]')];svgReady=true;
  paused=reduced.matches;updateRepeats(reduced.matches?data.walkthrough.after.length:0);if(!paused)repeatLoop();
 }
 function walkthrough(){
  const index=page-67,s=steps[index];el('walkthrough-title').textContent=s.title;el('walkthrough-subtitle').textContent=s.subtitle;el('code-step-label').textContent=`Step ${index+1} of ${steps.length}`;el('code-molnar').textContent=s.molnar;el('walkthrough-caption').textContent=s.caption;el('code-source-note').textContent=s.original;
  el('walkthrough-code').innerHTML=(index===4?repeatCode():codeStages.map((text,i)=>`<div class="code-stage ${i===index?'active':i<index?'past':''}"><pre>${escape(text)}</pre></div>`).join(''))+`<details class="code-complete"><summary>Full algorithm</summary><pre>${escape(fullAlgorithm())}</pre></details>`;el('code-reading').innerHTML=reading(index);
  if(!reduced.matches)el('code-reading').animate([{opacity:0},{opacity:1}],{duration:850});
  if(index===2)document.querySelectorAll('.changed-value').forEach((n,i)=>{if(reduced.matches)n.classList.remove('waiting');else later(()=>n.classList.remove('waiting'),500+i*250);});
  if(index===4){repeatChart().catch(console.error);el('repeat-count').addEventListener('input',event=>{pauseRepeats();updateRepeats(Number(event.target.value));});el('repeat-pause').addEventListener('click',()=>{if(!svgReady)return;if(paused){paused=false;syncRepeatControls();repeatLoop();}else pauseRepeats();});el('repeat-next').addEventListener('click',()=>{if(!svgReady)return;pauseRepeats();updateRepeats(Math.min(repeat+1,data.walkthrough.after.length));});el('back-to-ranking').addEventListener('click',()=>window.PFINavigate(63));}
 }
 async function start(next){stop();page=next;const token=epoch;try{data=await evidence;if(token!==epoch)return;if(Object.hasOwn(bridges,next))bridge();else walkthrough();}catch(error){console.error(error);el('status').textContent='Lesson evidence could not be loaded.';}}
 reduced.addEventListener('change',()=>{if(page!==null)start(page);});window.PFISequence={start,stop};
})();
