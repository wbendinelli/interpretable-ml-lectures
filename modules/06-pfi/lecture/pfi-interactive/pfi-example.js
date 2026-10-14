'use strict';
(()=>{
 const el=id=>document.getElementById(id);
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');
 const evidence=fetch('data/pfi-aggregates.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw new Error('SRAG evidence unavailable');return r.json();});
 let activePage=null,generation=0,timers=[],data=null,frame=0,elapsed=0,lastTime=0,running=false,lastPhase='',roundIndex=-1;
 let chips=[],points=[],animations=[],chartGeneration=0,selectedFeature=0,chartBars=[],chartPaused=false,chartHovered=false;
 const f=(value,digits=4)=>Number(value).toFixed(digits);
 const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
 function cancelChart(){el('chart-tooltip').hidden=true;chartHovered=false;chartGeneration++;animations.forEach(a=>a.cancel());animations=[];}
 function stop(){generation++;activePage=null;timers.forEach(clearTimeout);timers=[];cancelAnimationFrame(frame);frame=0;running=false;cancelChart();}
 function later(callback,delay){const token=generation;timers.push(setTimeout(()=>{if(token===generation)callback();},delay));}
 const schematicOrder=[1,0,3,2];
 const schematicRounds=[{cell:'age',feature:'idade_anos',label:'Age',prefix:'a'},{cell:'oxygen',feature:'saturacao',label:'Low oxygen',prefix:'o'}];
 const symbol=(prefix,index)=>`${prefix}<sub>${index+1}</sub>`;
 function setPrediction(cell,index,permuted=false,pending=false){
  const argument=permuted?`x<sub>${index+1}</sub><sup>perm</sup>`:`x<sub>${index+1}</sub>`;
  cell.innerHTML=pending?'<span class="probability">—</span><span class="decision">After shuffle</span>':`<span class="probability schematic-function">f(${argument})</span><span class="decision">Symbolic prediction</span>`;
  cell.classList.toggle('pending',pending);cell.classList.remove('correct','wrong');
  cell.setAttribute('aria-label',pending?'Awaiting symbolic permutation':`Symbolic model function for row ${index+1}; no patient probability`);
 }
 function renderRecords(){
  el('patient-rows').innerHTML=Array.from({length:4},(_,i)=>`<tr><th scope="row" data-label="Row">${symbol('r',i)}</th><td class="age-cell" data-label="Age"><span class="feature-value age-value">${symbol('a',i)}</span></td><td class="oxygen-cell" data-label="Low oxygen"><span class="feature-value oxygen-value">${symbol('o',i)}</span></td><td data-label="Target">${symbol('y',i)}</td><td data-label="Original f(x)" class="prediction-cell original-prediction"></td><td data-label="Permuted f(x)" class="prediction-cell permuted-prediction"></td></tr>`).join('');
  [...document.querySelectorAll('.original-prediction')].forEach((cell,i)=>setPrediction(cell,i));
 }
 function beginRound(index){
  roundIndex=index;const round=schematicRounds[index],r=data.rows.find(row=>row.feature===round.feature);
  document.querySelectorAll('.feature-value').forEach(n=>n.classList.toggle('moving-value',n.classList.contains(`${round.cell}-value`)));
  document.querySelectorAll('.age-cell,.oxygen-cell').forEach(n=>n.classList.toggle('active-feature',n.classList.contains(`${round.cell}-cell`)));
  el('age-layer').innerHTML=Array.from({length:4},(_,i)=>`<span class="age-chip">${symbol(round.prefix,i)}</span>`).join('');chips=[...el('age-layer').children];
  [...document.querySelectorAll('.permuted-prediction')].forEach((cell,i)=>setPrediction(cell,i,true,true));
  el('error-comparison').classList.remove('ready');el('error-impact').textContent='';
  const max=.18;
  el('error-bars').innerHTML=[['Original',r.before,0,'original'],[`${round.label} shuffled`,r.after_mean,r.after_sd,'permuted']].map(([label,mean,sd,kind])=>`<div class="error-bar-row ${kind}" aria-label="${label}: mean Brier ${f(mean)}, shuffle SD ${f(sd)}"><span>${label}</span><div class="error-bar-track"><div class="error-bar" style="width:${mean/max*100}%"></div>${sd?`<span class="error-whisker" style="left:${(mean-sd)/max*100}%;width:${2*sd/max*100}%"></span>`:''}</div><span class="error-bar-value">${f(mean)}</span></div>`).join('');
  document.querySelector('.error-caption').textContent='Recorded full-test errors. They are separate from the symbolic row diagram.';
  measure();
 }
 function measure(){
  if(activePage!==62||el('mechanism-slide').hidden||roundIndex<0)return;
  const outer=document.querySelector('.patient-table-wrap').getBoundingClientRect(),cell=schematicRounds[roundIndex].cell;
  points=[...document.querySelectorAll(`.${cell}-value`)].map(n=>{const b=n.getBoundingClientRect();return{x:b.left+b.width/2-outer.left,y:b.top+b.height/2-outer.top};});
 }
 function compare(){
  const round=schematicRounds[roundIndex],r=data.rows.find(row=>row.feature===round.feature);
  [...document.querySelectorAll('.permuted-prediction')].forEach((cell,i)=>setPrediction(cell,i,true));
  el('error-comparison').classList.add('ready');el('error-impact').textContent=`+${f(r.relative_increase_percent,2)}% Brier error`;
  document.querySelector('.error-caption').textContent=`Measured full test: ${data.protocol.n_evaluation.toLocaleString('en-US')} records; ${data.protocol.repeats} shuffles; mean ± SD ${f(r.after_mean)} ± ${f(r.after_sd)}. These errors were not calculated from the symbolic rows.`;
  measure();
 }
 function paint(){
  const cycle=20,index=Math.floor(elapsed/cycle)%schematicRounds.length,t=elapsed%cycle;
  if(index!==roundIndex)beginRound(index);
  const round=schematicRounds[index],phase=t<3?0:t<6?1:t<13?2:t<16?3:4;
  const progress=phase===0||phase===4?0:phase===2?1:phase===1?(t-3)/3:1-(t-13)/3;
  const phaseKey=`${index}-${phase}`;
  if(phaseKey!==lastPhase){
   lastPhase=phaseKey;let title,input,caption,state;
   [...document.querySelectorAll(`.${round.cell}-value`)].forEach((n,i)=>n.innerHTML=symbol(round.prefix,phase===2||phase===3?schematicOrder[i]:i));
   if(phase===0){title='Start with original inputs';input='Original inputs';state=`Next: ${round.label}`;caption=`Symbolic diagram: shuffle only ${round.label.toLowerCase()}. All other inputs and outcomes stay fixed.`;}
   if(phase===1){title=`Shuffle only ${round.label.toLowerCase()}`;input=`${round.label} moving`;state=`${round.label} symbols moving`;caption='The symbols show column values exchanging rows. No patient values or row-level probabilities are displayed.';}
   if(phase===2){title='Predict with the same model';input=`${round.label} permuted`;state=`${round.label} permuted`;caption='f(x) is a symbolic model prediction. The measured Brier comparison comes from the separate full temporal test.';compare();}
   if(phase===3){
    [...document.querySelectorAll('.permuted-prediction')].forEach((cell,i)=>setPrediction(cell,i,true,true));
    el('error-comparison').classList.remove('ready');el('error-impact').textContent='';
    document.querySelector('.error-caption').textContent='Clear the symbolic permuted predictions and restore the selected column before the next experiment.';
    title='Restore the original inputs';input=`${round.label} returning`;state=`${round.label} returning`;caption='Return the selected column before starting another experiment. Shuffles never accumulate across variables.';
   }
   if(phase===4){title='Ready for the next variable';input='Original inputs';state='Original inputs restored';caption='Original symbolic inputs are back. The next variable starts its own separate experiment.';}
   el('experiment-phase').textContent=title;el('model-input').textContent=input;el('shuffle-state').textContent=state;el('experiment-caption').textContent=caption;
  }
  for(let i=0;i<chips.length;i++){
   const from=points[i],to=points[schematicOrder.indexOf(i)];if(!from||!to)continue;
   const vertical=ease((progress-.2)/.6),sideways=ease(progress/.2)*(1-ease((progress-.8)/.2))*(i%2===0?-12:12);
   chips[i].style.transform=`translate(${from.x+(to.x-from.x)*vertical+sideways}px,${from.y+(to.y-from.y)*vertical}px) translate(-50%,-50%)`;
  }
 }
 function tick(now){if(!running||activePage!==62)return;if(lastTime)elapsed+=(now-lastTime)/1000;lastTime=now;paint();frame=requestAnimationFrame(tick);}
 function mechanism(){
  el('mechanism-scope-values').innerHTML='<p>The row diagram is schematic: its symbols illustrate a permutation and do not represent patient records. It has no row-level probabilities, classification decisions or subset error.</p><p>The chart replays measured errors from the complete temporal evaluation, using the same fitted model and the recorded repeated permutations. All empirical values are aggregates.</p>';
  cancelAnimationFrame(frame);running=false;elapsed=0;lastTime=0;lastPhase='';roundIndex=-1;renderRecords();el('motion-pause').hidden=reduced.matches;el('motion-pause').textContent='Pause';el('motion-pause').setAttribute('aria-pressed','false');if(reduced.matches)elapsed=8;paint();if(!reduced.matches){running=true;frame=requestAnimationFrame(tick);}
 }
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
  el('study-details').textContent=`Hospitalized COVID cohort in the SRAG study. Fixed reference XGBoost, without class weights or resampling. Temporal evaluation: ${data.protocol.period}. This previously observed holdout is exploratory. The row animations are schematic and are separate from these measured aggregate results.`;
  const response=await fetch(`figures/pfi-slide-${mode}.svg`),source=await response.text();
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
  const age=data.rows.find(row=>row.feature==='idade_anos');
  el('brier-example').innerHTML=`<p class="small-label">Measured full temporal test · aggregate errors</p><div class="schematic-brier-grid"><div><h3>Original inputs</h3><p>Original Brier<strong>${f(data.original.brier)}</strong></p></div><div><h3>Age shuffled</h3><p>Mean Brier across ${data.protocol.repeats} shuffles<strong>${f(age.after_mean)}</strong></p></div></div><p>The formula compares each predicted probability with its observed outcome, squares the difference and averages it. No individual probability or outcome is provided by this public package.</p>`;
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
