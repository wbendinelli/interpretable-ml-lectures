'use strict';
(()=>{
 const el=id=>document.getElementById(id);
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');
 const evidence=fetch('../../gold/pfi_slide_explainer.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw new Error('SRAG evidence unavailable');return r.json();});
 let activePage=null,generation=0,timers=[],data=null,frame=0,elapsed=0,lastTime=0,running=false,lastPhase='',roundIndex=-1;
 let chips=[],points=[],animations=[],chartGeneration=0,selectedFeature=0,chartBars=[],chartPaused=false,chartHovered=false;
 const f=(value,digits=4)=>Number(value).toFixed(digits);
 const oxygen=value=>({sim:'Yes',nao:'No',desconhecido:'Unknown'})[value]||value;
 const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
 function cancelChart(){el('chart-tooltip').hidden=true;chartHovered=false;chartGeneration++;animations.forEach(a=>a.cancel());animations=[];}
 function stop(){generation++;activePage=null;timers.forEach(clearTimeout);timers=[];cancelAnimationFrame(frame);frame=0;running=false;cancelChart();}
 function later(callback,delay){const token=generation;timers.push(setTimeout(()=>{if(token===generation)callback();},delay));}
 function prediction(p,cls,correct,pending=false){return pending?'<span class="probability">—</span><span class="decision">After shuffle</span>':`<span class="probability">${f(p,4)}</span><span class="decision">${cls?'Death':'Survived'} ${correct?'✓':'✕'}</span>`;}
 function setPrediction(cell,p,cls,correct,pending=false){cell.innerHTML=prediction(p,cls,correct,pending);cell.classList.toggle('pending',pending);cell.classList.toggle('correct',!pending&&correct);cell.classList.toggle('wrong',!pending&&!correct);cell.setAttribute('aria-label',pending?'Awaiting permutation':`Death probability ${f(p,4)}, predicted ${cls?'death':'survival'}, ${correct?'correct':'wrong'} at cutoff 0.50`);}
 function renderRecords(){
  el('patient-rows').innerHTML=data.preview.rows.map(r=>`<tr><th scope="row" data-label="Row">${r.record}</th><td class="age-cell" data-label="Age (years)"><span class="feature-value age-value">${f(r.idade_anos,2)}</span></td><td class="oxygen-cell" data-label="Low oxygen"><span class="feature-value oxygen-value">${oxygen(r.saturacao)}</span></td><td data-label="Observed">${r.y_obito?'Died':'Survived'}</td><td data-label="Original P(death)" class="prediction-cell original-prediction"></td><td data-label="Permuted P(death)" class="prediction-cell permuted-prediction"></td></tr>`).join('');
  [...document.querySelectorAll('.original-prediction')].forEach((cell,i)=>{const r=data.preview.rows[i];setPrediction(cell,r.p_original,r.class_original,r.correct_original);});
 }
 function beginRound(index){
  roundIndex=index;const round=data.preview.rounds[index];
  document.querySelectorAll('.feature-value').forEach(n=>n.classList.toggle('moving-value',n.classList.contains(`${round.cell}-value`)));
  document.querySelectorAll('.age-cell,.oxygen-cell').forEach(n=>n.classList.toggle('active-feature',n.classList.contains(`${round.cell}-cell`)));
  el('age-layer').innerHTML=round.values.map(v=>`<span class="age-chip">${round.cell==='age'?f(v,2):oxygen(v)}</span>`).join('');chips=[...el('age-layer').children];
  [...document.querySelectorAll('.permuted-prediction')].forEach(cell=>setPrediction(cell,0,0,false,true));
  el('error-comparison').classList.remove('ready');el('error-impact').textContent='';
  const r=round.full_test,max=.18;
  el('error-bars').innerHTML=[['Original',r.before,0,'original'],[`${round.label} shuffled`,r.after_mean,r.after_sd,'permuted']].map(([label,mean,sd,kind])=>`<div class="error-bar-row ${kind}" aria-label="${label}: mean Brier ${f(mean)}, shuffle SD ${f(sd)}"><span>${label}</span><div class="error-bar-track"><div class="error-bar" style="width:${mean/max*100}%"></div>${sd?`<span class="error-whisker" style="left:${(mean-sd)/max*100}%;width:${2*sd/max*100}%"></span>`:''}</div><span class="error-bar-value">${f(mean)}</span></div>`).join('');
  document.querySelector('.error-caption').textContent='Original error on the full temporal test set. The selected subset illustrates the operation only.';
  measure();
 }
 function measure(){
  if(activePage!==62||el('mechanism-slide').hidden||roundIndex<0)return;
  const outer=document.querySelector('.patient-table-wrap').getBoundingClientRect(),cell=data.preview.rounds[roundIndex].cell;
  points=[...document.querySelectorAll(`.${cell}-value`)].map(n=>{const b=n.getBoundingClientRect();return{x:b.left+b.width/2-outer.left,y:b.top+b.height/2-outer.top};});
 }
 function compare(){
  const round=data.preview.rounds[roundIndex],r=round.full_test;
  [...document.querySelectorAll('.permuted-prediction')].forEach((cell,i)=>setPrediction(cell,round.probability[i],round.predicted[i],round.correct[i]));
  el('error-comparison').classList.add('ready');el('error-impact').textContent=`+${f(r.relative_increase_percent,2)}% Brier error`;
  document.querySelector('.error-caption').textContent=`Full study test: ${data.protocol.n_evaluation.toLocaleString('en-US')} records. After ${data.protocol.repeats} shuffles, mean ± SD: ${f(r.after_mean)} ± ${f(r.after_sd)}. Separate full-test experiment, not this eight-row shuffle.`;
  measure();
 }
 function paint(){
  const cycle=20,index=Math.floor(elapsed/cycle)%data.preview.rounds.length,t=elapsed%cycle;
  if(index!==roundIndex)beginRound(index);
  const round=data.preview.rounds[index],phase=t<3?0:t<6?1:t<13?2:t<16?3:4;
  const progress=phase===0||phase===4?0:phase===2?1:phase===1?(t-3)/3:1-(t-13)/3;
  const phaseKey=`${index}-${phase}`;
  if(phaseKey!==lastPhase){
   lastPhase=phaseKey;let title,input,caption,state;
   [...document.querySelectorAll(`.${round.cell}-value`)].forEach((n,i)=>{const v=round.values[phase===2||phase===3?data.preview.permutation[i]:i];n.textContent=round.cell==='age'?f(v,2):oxygen(v);});
   if(phase===0){title='Start with original inputs';input='Original inputs';state=`Next: ${round.label}`;caption=`Original data restored. This round will shuffle only ${round.label.toLowerCase()}; all other inputs and outcomes remain fixed.`;}
   if(phase===1){title=`Shuffle only ${round.label.toLowerCase()}`;input=`${round.label} moving`;state=`${round.label} values moving`;caption='Move values between rows, preserving the values in the column. Use the same trained model to make new predictions.';}
   if(phase===2){title='Compare both predictions';input=`${round.label} permuted`;state=`${round.label} permuted`;caption='Read the observed outcome, then compare both probabilities. ✓ and ✕ use the 0.50 cutoff; Brier measures probability error continuously.';compare();}
   if(phase===3){
    [...document.querySelectorAll('.permuted-prediction')].forEach(cell=>setPrediction(cell,0,0,false,true));
    el('error-comparison').classList.remove('ready');el('error-impact').textContent='';
    document.querySelector('.error-caption').textContent='Return to the original inputs. Permuted predictions are cleared before the next experiment.';
    title='Restore the original inputs';input=`${round.label} returning`;state=`${round.label} returning`;caption='Return this column before starting the next experiment. We never accumulate shuffles across variables.';}
   if(phase===4){title='Ready for the next variable';input='Original inputs';state='Original inputs restored';caption='The original data are back and permuted predictions are cleared. The next variable starts a separate experiment.';}
   el('experiment-phase').textContent=title;el('model-input').textContent=input;el('shuffle-state').textContent=state;el('experiment-caption').textContent=caption;
  }
  for(let i=0;i<chips.length;i++){
   const from=points[i],to=points[data.preview.permutation.indexOf(i)];if(!from||!to)continue;
   const vertical=ease((progress-.2)/.6),sideways=ease(progress/.2)*(1-ease((progress-.8)/.2))*(i%2===0?-12:12);
   chips[i].style.transform=`translate(${from.x+(to.x-from.x)*vertical+sideways}px,${from.y+(to.y-from.y)*vertical}px) translate(-50%,-50%)`;
  }
 }
 function tick(now){if(!running||activePage!==62)return;if(lastTime)elapsed+=(now-lastTime)/1000;lastTime=now;paint();frame=requestAnimationFrame(tick);}
 function mechanism(){const previewBefore=data.preview.rows.reduce((sum,row)=>sum+row.brier_original,0)/data.preview.rows.length,ageRound=data.preview.rounds.find(round=>round.cell==='age');el('mechanism-scope-values').innerHTML=`<p>Eight-row preview: original Brier ${f(previewBefore)}, after the shown age shuffle ${f(ageRound.sample_brier_mean)}. Full test: original ${f(data.original.brier)}, mean after repeated age shuffles ${f(ageRound.full_test.after_mean)}.</p><p>A single shuffle on an outcome-selected subset can reduce its error. Global PFI uses repeated shuffles on the full temporal test. These are different evaluations.</p>`;cancelAnimationFrame(frame);running=false;elapsed=0;lastTime=0;lastPhase='';roundIndex=-1;renderRecords();el('motion-pause').hidden=reduced.matches;el('motion-pause').textContent='Pause';el('motion-pause').setAttribute('aria-pressed','false');if(reduced.matches)elapsed=8;paint();if(!reduced.matches){running=true;frame=requestAnimationFrame(tick);}}
 function featureDetail(){
  const mode=el('error-scale').value,r=data.rows[selectedFeature];
  el('feature-result-title').textContent=`${r.label} · SRAG experiment`;
  el('age-before').textContent=f(r.before);el('age-after').textContent=f(r.after_mean);
  el('age-importance').textContent=mode==='ratio'?`${f(r.ratio_mean,3)} ×  ± ${f(r.ratio_sd,3)} SD`:`+${f(r.difference_mean)}  ± ${f(r.difference_sd)} SD`;
  el('age-interpretation').textContent=mode==='ratio'?`${f(r.relative_increase_percent,2)}% more Brier error after shuffling this feature. This is a relative change in error.`:'This is extra Brier error, not a change in the mortality rate.';
  chartBars.forEach((bar,i)=>{bar.style.fill=i===selectedFeature?'#212322':'#a2aeaf';bar.setAttribute('aria-pressed',String(i===selectedFeature));});
 }
 async function scale(){
  if(!data||activePage!==63)return;
  cancelChart();const chartToken=chartGeneration,token=generation,mode=el('error-scale').value;
  featureDetail();
  for(const item of document.querySelectorAll('.formula-reading'))item.classList.toggle('active',item.dataset.scale===mode);
  el('ranking-caption').textContent=`${data.protocol.repeats} permutations per feature · ${data.protocol.n_evaluation.toLocaleString('en-US')} records · ${data.protocol.period} · whiskers: ±1 shuffle SD. Rounded display; calculations use full precision.`;
  el('study-details').textContent=`Hospitalized COVID cohort in the SRAG study. Fixed reference XGBoost, without class weights or resampling. Temporal evaluation: ${data.protocol.period}. This previously observed holdout is exploratory. The teaching subset uses the first adult records per outcome and does not represent prevalence or performance.`;
  const response=await fetch(`../../figures/pfi-slide-${mode}.svg`),source=await response.text();
  if(token!==generation||chartToken!==chartGeneration)return;
  const svg=new DOMParser().parseFromString(source,'image/svg+xml').documentElement;
  svg.setAttribute('role','group');svg.setAttribute('aria-label',`Real SRAG PFI ranking by ${mode}; select a bar to inspect its error.`);
  el('ranking-chart').replaceChildren(document.importNode(svg,true));
  const live=el('ranking-chart').firstElementChild;
  chartBars=[...live.querySelectorAll('g[id^="patch_"] > path[clip-path]')];
  chartBars.forEach((bar,i)=>{
   bar.classList.add('ranking-bar');bar.setAttribute('role','button');bar.setAttribute('tabindex','0');bar.setAttribute('aria-label',`${data.rows[i].label}: ${f(data.rows[i][mode+'_mean'])}, standard deviation ${f(data.rows[i][mode+'_sd'])}`);
   const choose=()=>{selectedFeature=i;featureDetail();};bar.addEventListener('click',choose);bar.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();choose();}});
  });
  featureDetail();
  const whiskers=[...live.querySelectorAll('g[id^="LineCollection_"]'),...live.querySelectorAll('g[id^="line2d_"]')].filter(n=>n.id.startsWith('LineCollection_')||n.querySelector('g[clip-path] use'));
  const labels=[...live.querySelectorAll('g[id^="pfi-value-"]')];
  el('scale-explanation').textContent=mode==='ratio'?'Ratio: 1 = unchanged error; above 1 = more error; below 1 = less error. The dashed line marks the original error.':'Difference: extra Brier error. Zero means no change.';
  chartPaused=false;el('ranking-pause').textContent='Pause';el('ranking-pause').setAttribute('aria-pressed','false');
  const tooltip=el('chart-tooltip'),container=document.querySelector('.chart-container');
  const showTooltip=(i,event)=>{
   chartHovered=true;const r=data.rows[i];
   tooltip.innerHTML=`<strong>${r.label}</strong><span>Original Brier: ${f(r.before)}</span><span>Permuted mean: ${f(r.after_mean)}</span><span>${mode==='ratio'?'Ratio':'Difference'}: ${f(r[mode+'_mean'],mode==='ratio'?3:4)} ± ${f(r[mode+'_sd'],mode==='ratio'?3:4)} SD</span>`;
   tooltip.hidden=false;const bounds=container.getBoundingClientRect();
   tooltip.style.left=`${Math.max(0,Math.min((event.clientX||bounds.left+30)-bounds.left+12,bounds.width-240))}px`;
   tooltip.style.top=`${Math.max(0,(event.clientY||bounds.top+30)-bounds.top-100)}px`;
  };
  // Invisible row targets make the bar, value and narrow SD whisker easy to inspect.
  const clip=live.querySelector('clipPath rect'),plotWidth=Number(clip.getAttribute('width'));
  chartBars.forEach((bar,i)=>{
   const box=bar.getBBox(),target=document.createElementNS('http://www.w3.org/2000/svg','rect');
   target.setAttribute('x',box.x);target.setAttribute('y',box.y-5);target.setAttribute('width',plotWidth);target.setAttribute('height',box.height+10);target.setAttribute('fill','transparent');target.setAttribute('aria-hidden','true');target.classList.add('chart-hit');target.dataset.feature=String(i);
   target.addEventListener('pointerenter',event=>showTooltip(i,event));target.addEventListener('pointermove',event=>showTooltip(i,event));target.addEventListener('pointerleave',()=>{chartHovered=false;tooltip.hidden=true;});target.addEventListener('click',()=>{selectedFeature=i;featureDetail();});
   bar.addEventListener('focus',event=>showTooltip(i,event));bar.addEventListener('blur',()=>{chartHovered=false;tooltip.hidden=true;});
   live.querySelector('g[id="axes_1"]').append(target);
  });
  function animateCycle(){
   if(chartToken!==chartGeneration||activePage!==63)return;
   if(chartPaused||chartHovered){later(animateCycle,1500);return;}
   animations.forEach(a=>a.cancel());animations=[];
   if(reduced.matches){el('chart-state').textContent='Hover or select a row to inspect its values.';return;}
   el('chart-state').textContent='First: mean importance across shuffles.';
   chartBars.forEach((bar,i)=>animations.push(bar.animate([{transform:'scaleX(0)'},{transform:'scaleX(1)'}],{duration:1300,delay:i*350,easing:'cubic-bezier(.2,.7,.3,1)',fill:'backwards'})));
   labels.forEach((label,i)=>animations.push(label.animate([{opacity:0},{opacity:1}],{duration:450,delay:1300+i*350,fill:'backwards'})));
   whiskers.forEach((n,i)=>animations.push(n.animate([{opacity:0},{opacity:1}],{duration:900,delay:5000+Math.floor(i/3)*180,fill:'backwards'})));
   later(()=>{if(chartToken===chartGeneration&&!chartPaused)el('chart-state').textContent='Then: SD whiskers show variation between shuffles.';},5000);
   later(()=>{if(chartToken===chartGeneration&&!chartPaused)el('chart-state').textContent='Hover for values · select a row to compare errors.';},8000);
   later(animateCycle,18000);
  }
  animateCycle();
 }
 function brier(){
  const r=data.preview.rows.find(row=>row.y_obito===1 && row.brier_after_age>row.brier_original)||data.preview.rows[0];
  el('brier-example').innerHTML=`<p class="small-label">Real record ${r.record} · observed death, y = ${r.y_obito}</p><div class="brier-pair"><div><h3>Original prediction</h3><p>P(death) = <strong>${f(r.p_original,4)}</strong></p><p>(${f(r.p_original,4)} − ${r.y_obito})² ≈ <strong>${f(r.brier_original,4)}</strong></p></div><div><h3>After shuffling age</h3><p>P(death) = <strong>${f(r.p_after_age,4)}</strong></p><p>(${f(r.p_after_age,4)} − ${r.y_obito})² ≈ <strong>${f(r.brier_after_age,4)}</strong></p></div></div><p>The probability moved farther from the observed outcome. Its squared error increased. The full Brier score averages this calculation over all evaluation records.</p>`;
  el('brier-dialog').showModal();
 }
 async function start(page){stop();activePage=page;const token=generation;if(page!==62&&page!==63)return;try{data=await evidence;if(token!==generation)return;if(page===62)mechanism();else{selectedFeature=0;await scale();}}catch(error){if(token!==generation)return;el('status').textContent='SRAG evidence could not be loaded.';console.error(error);}}
 el('error-scale').addEventListener('change',()=>scale().catch(console.error));el('ranking-replay').addEventListener('click',()=>scale().catch(console.error));
 el('ranking-pause').addEventListener('click',()=>{chartPaused=!chartPaused;animations.forEach(a=>chartPaused?a.pause():a.play());el('ranking-pause').textContent=chartPaused?'Resume':'Pause';el('ranking-pause').setAttribute('aria-pressed',String(chartPaused));});
 el('motion-pause').addEventListener('click',()=>{running=!running;cancelAnimationFrame(frame);lastTime=0;el('motion-pause').textContent=running?'Pause':'Resume';el('motion-pause').setAttribute('aria-pressed',String(!running));if(running)frame=requestAnimationFrame(tick);});
 el('brier-open').addEventListener('click',()=>{if(running)el('motion-pause').click();brier();});el('brier-close').addEventListener('click',()=>el('brier-dialog').close());
 reduced.addEventListener('change',()=>{if(activePage===62)mechanism();if(activePage===63)scale().catch(console.error);});
 new ResizeObserver(()=>{measure();if(activePage===62&&data)paint();}).observe(document.querySelector('.patient-table-wrap'));
 document.fonts.ready.then(()=>{measure();if(activePage===62&&data)paint();});
 window.PFILesson={start,stop};
})();
