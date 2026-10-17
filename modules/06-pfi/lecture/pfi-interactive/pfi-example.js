'use strict';
(()=>{
 const el=id=>document.getElementById(id);
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');
 const evidence=Promise.all([fetch('data/pfi-aggregates.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw new Error('SRAG evidence unavailable');return r.json();}),fetch('data/pfi-teaching-records.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw new Error('Teaching record evidence unavailable');return r.json();})]).then(([aggregate,teaching])=>{if(aggregate.protocol.primary_metric!=='logloss'||teaching.preview.metric!=='logloss')throw Error('Log loss evidence is required for this lecture.');return {...aggregate,preview:teaching.preview};});
 let activePage=null,generation=0,timers=[],data=null,frame=0,elapsed=0,lastTime=0,running=false,lastPhase='',roundIndex=-1;
 let chips=[],points=[],flowArrows=[],flowSvg=null,animations=[],chartGeneration=0,selectedFeature=0,chartBars=[],chartPaused=false,chartHovered=false;
 const f=(value,digits=4)=>Number(value).toFixed(digits);
 const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
 function cancelChart(){el('chart-tooltip').hidden=true;chartHovered=false;chartGeneration++;animations.forEach(a=>a.cancel());animations=[];}
 function stop(){generation++;activePage=null;timers.forEach(clearTimeout);timers=[];cancelAnimationFrame(frame);frame=0;running=false;cancelChart();}
 function later(callback,delay){const token=generation;timers.push(setTimeout(()=>{if(token===generation)callback();},delay));}
 const oxygen=value=>({sim:'Yes',nao:'No',desconhecido:'Unknown'}[value]||value);
 const featureValue=(round,value)=>round.cell==='age'?f(value,2):oxygen(value);
 function setPrediction(cell,index,permuted=false,pending=false){
  const row=data.preview.rows[index],round=data.preview.rounds[roundIndex];
  if(pending){cell.innerHTML='<span class="probability">—</span><span class="decision">After shuffle</span>';cell.classList.add('pending');cell.classList.remove('correct','wrong');cell.setAttribute('aria-label','Awaiting prediction after shuffle');return;}
  const probability=permuted?round.probability[index]:row.p_original,predicted=permuted?round.predicted[index]:row.class_original,correct=permuted?round.correct[index]:row.correct_original;
  cell.innerHTML=`<span class="probability">${f(probability,3)}</span><span class="decision">${predicted?'Died':'Survived'} ${correct?'✓':'×'}</span>`;
  cell.classList.remove('pending');cell.classList.toggle('correct',correct);cell.classList.toggle('wrong',!correct);
  cell.setAttribute('aria-label',`${permuted?'After shuffle':'Original'} death probability ${f(probability,3)}; predicts ${predicted?'death':'survival'}; ${correct?'correct':'incorrect'} at cutoff ${f(data.preview.threshold,2)}`);
 }
 function renderRecords(){
  el('patient-rows').innerHTML=data.preview.rows.map(row=>`<tr><th scope="row" data-label="Row">${row.record}</th><td class="age-cell" data-label="Age (years)"><span class="feature-value age-value">${f(row.idade_anos,2)}</span></td><td class="oxygen-cell" data-label="Low oxygen"><span class="feature-value oxygen-value">${oxygen(row.saturacao)}</span></td><td data-label="Observed outcome">${row.y_obito?'Died':'Survived'}</td><td data-label="Original p(death)" class="prediction-cell original-prediction"></td><td data-label="After shuffle p(death)" class="prediction-cell permuted-prediction"></td></tr>`).join('');
  [...document.querySelectorAll('.original-prediction')].forEach((cell,i)=>setPrediction(cell,i));
 }
 function beginRound(index){
  roundIndex=index;const round=data.preview.rounds[index];
  document.querySelectorAll('.feature-value').forEach(n=>n.classList.toggle('moving-value',n.classList.contains(`${round.cell}-value`)));
  document.querySelectorAll('.age-cell,.oxygen-cell').forEach(n=>n.classList.toggle('active-feature',n.classList.contains(`${round.cell}-cell`)));
  el('age-layer').innerHTML=[round.values,round.shuffled_values].map((values,layer)=>values.map(value=>`<span class="age-chip ${layer?'incoming-flow':'original-flow'}">${featureValue(round,value)}</span>`).join('')).join('');chips=[...el('age-layer').querySelectorAll('.age-chip')];
  flowSvg=document.createElementNS('http://www.w3.org/2000/svg','svg');
  flowSvg.classList.add('column-flow-arrows');flowSvg.setAttribute('aria-hidden','true');
  flowSvg.innerHTML='<defs><marker id="column-flow-tip" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z"/></marker></defs>';
  flowArrows=chips.map(()=>{const path=document.createElementNS('http://www.w3.org/2000/svg','path');path.classList.add('column-flow-arrow');path.setAttribute('marker-end','url(#column-flow-tip)');flowSvg.append(path);return path;});
  el('age-layer').prepend(flowSvg);
  [...document.querySelectorAll('.permuted-prediction')].forEach((cell,i)=>setPrediction(cell,i,true,true));
  el('mechanism-feature').value=String(index);
  el('error-comparison').classList.remove('ready');el('error-impact').textContent='';
  const result=round.full_test,max=Math.max(...data.preview.rounds.map(r=>r.full_test.after_mean+2*r.full_test.after_sd),result.before)*1.08;
  el('error-bars').innerHTML=[['Original',result.before,0,'original'],['After shuffle',result.after_mean,result.after_sd,'permuted']].map(([label,value,sd,kind])=>`<div class="error-bar-row ${kind}" aria-label="${label}: full-test log loss ${f(value)}${sd?`, shuffle standard deviation ${f(sd)}`:''}"><span>${label}</span><div class="error-bar-track"><div class="error-bar" style="width:${value/max*100}%"></div>${sd?`<span class="error-whisker" style="left:${(value-sd)/max*100}%;width:${2*sd/max*100}%"></span>`:''}</div><span class="error-bar-value">${f(value)}</span></div>`).join('');
  document.querySelector('.error-caption').textContent='Original log loss on the full test. Then reveal the mean after 50 shuffles.';
  measure();
 }
 function measure(){
  if(activePage!==62||el('mechanism-slide').hidden||roundIndex<0)return;
  const outer=document.querySelector('.patient-table-wrap').getBoundingClientRect(),cell=data.preview.rounds[roundIndex].cell;
  flowSvg?.setAttribute('viewBox',`0 0 ${outer.width} ${outer.height}`);
  points=[...document.querySelectorAll(`.${cell}-value`)].map(n=>{const b=n.getBoundingClientRect();return{x:b.left+b.width/2-outer.left,y:b.top+b.height/2-outer.top};});
  const header=document.querySelector('.patient-table thead').getBoundingClientRect();
  el('age-layer').style.clipPath=`inset(${Math.max(0,header.bottom-outer.top)}px 0 0 0)`;
 }
 function compare(){
  const round=data.preview.rounds[roundIndex],result=round.full_test;
  [...document.querySelectorAll('.permuted-prediction')].forEach((cell,i)=>setPrediction(cell,i,true));
  el('error-comparison').classList.add('ready');el('error-impact').textContent=`${result.relative_increase_percent>=0?'+':''}${f(result.relative_increase_percent,2)}% log loss error`;
  document.querySelector('.error-caption').textContent=`After: mean ± one shuffle SD (${f(result.after_sd)}). Full test: ${data.protocol.n_evaluation.toLocaleString('en-US')} rows.`;
  el('demo-global-reading').textContent=`Table: eight rows from recorded shuffle ${data.preview.displayed_repeat}. Chart: mean of ${data.protocol.repeats} full-test shuffles.`;
  measure();
 }
 function traceValue(path,point,startY,endY,bend,position,direction,opacity,chip){
  // A short local trail follows the value, never an invented donor-to-row pairing.
  const distance=Math.abs(endY-startY),gap=(chip.offsetHeight/2+4)/distance;
  const tip=Math.max(0,Math.min(1,position-direction*gap));
  const tail=Math.max(0,Math.min(1,tip-direction*34/distance));
  const at=t=>({x:point.x+bend*Math.sin(Math.PI*t),y:startY+(endY-startY)*t});
  const a=at(tail),b=at(tip),m=at((tail+tip)/2);
  path.setAttribute('d',`M ${a.x} ${a.y} Q ${2*m.x-(a.x+b.x)/2} ${2*m.y-(a.y+b.y)/2} ${b.x} ${b.y}`);
  path.setAttribute('opacity',String(opacity*(Math.abs(tip-tail)*distance<8?0:1)));
  path.setAttribute('stroke-dashoffset',String(-48*(direction>0?position:1-position)));
 }
 function paint(){
  const cycle=22,index=Math.floor(elapsed/cycle)%data.preview.rounds.length,t=elapsed%cycle;
  if(index!==roundIndex)beginRound(index);
  const round=data.preview.rounds[index],phase=t<3?0:t<6?1:t<14?2:t<17?3:4;
  const progress=phase===0||phase===4?0:phase===2?1:phase===1?(t-3)/3:1-(t-14)/3;
  const phaseKey=`${index}-${phase}`;
  if(phaseKey!==lastPhase){
   lastPhase=phaseKey;let title,input,caption,state;
   for(const r of data.preview.rounds){[...document.querySelectorAll(`.${r.cell}-value`)].forEach((n,i)=>n.textContent=featureValue(r,r.values[i]));}
   [...document.querySelectorAll(`.${round.cell}-value`)].forEach((n,i)=>n.textContent=featureValue(round,(phase===2?round.shuffled_values:round.values)[i]));
   for(const r of data.preview.rounds){[...document.querySelectorAll(`.${r.cell}-cell`)].forEach(n=>n.setAttribute('aria-label',`${r.label}: ${n.querySelector('.feature-value').textContent}${r.cell==='age'?' years':''}`));}
   if(phase===0){title='Start with original inputs';input='Original inputs';state=`Next: ${round.label}`;caption='Same model. Same full test. Eight receiver rows are visible.';el('demo-global-reading').textContent='Table: one recorded full-test shuffle. Chart: repeated full-test results.';}
   if(phase===1){title=`Shuffle only ${round.label.toLowerCase()}`;input=`${round.label} moving`;state=`${round.label} moving`;caption='The entire test column is shuffled. Values arriving here can come from rows outside this table.';}
   if(phase===2){title='Read the global error change';input=`${round.label} shuffled`;state=`${round.label} shuffled`;caption=round.cell==='oxygen'?'A category can remain the same after a shuffle. The probabilities shown come from recorded full-test shuffle 1.':'Original and shuffled predictions: the same eight receiver rows, from recorded full-test shuffle 1.';compare();}
   if(phase===3){
    [...document.querySelectorAll('.permuted-prediction')].forEach((cell,i)=>setPrediction(cell,i,true,true));
    el('error-comparison').classList.remove('ready');el('error-impact').textContent='';
    document.querySelector('.error-caption').textContent='Clear the new predictions; restore the inputs.';
    title='Restore the original inputs';input=`${round.label} returning`;state=`${round.label} returning`;caption='Restore every input before the next variable.';
   }
   if(phase===4){title='Ready for the next variable';input='Original inputs';state='Original inputs restored';caption='Age and low oxygen are separate experiments. Changes never accumulate.';}
   el('experiment-phase').textContent=title;el('model-input').textContent=input;el('shuffle-state').textContent=state;el('experiment-caption').textContent=caption;
   document.querySelector('.column-scene').dataset.phase=String(phase);
  }
  const n=points.length,top=points[0]?.y??0,bottom=points[n-1]?.y??0;
  const tracing=(phase===1||phase===3)&&!reduced.matches;
  if(flowSvg)flowSvg.style.visibility=tracing?'visible':'hidden';
  for(let i=0;i<n;i++){
   const point=points[i],original=chips[i],incoming=chips[i+n];if(!point||!original||!incoming)continue;
   const unchanged=round.values[i]===round.shuffled_values[i],p=Math.max(0,Math.min(1,progress)),lane=i%2===0?-12:12;
   const leaving=ease(p/.62),arriving=ease((p-.2)/.8);
   const exitY=i%2===0?top-36:bottom+36,entryY=i%2===0?bottom+36:top-36;
   const originalY=unchanged?point.y:point.y+(exitY-point.y)*leaving;
   const incomingY=entryY+(point.y-entryY)*arriving;
   original.style.opacity=String(unchanged?1:1-ease((leaving-.85)/.15));
   incoming.style.opacity=String(unchanged?0:ease(arriving/.08));
   original.style.transform=`translate(${point.x+(unchanged?0:lane*Math.sin(Math.PI*leaving))}px,${originalY}px) translate(-50%,-50%)`;
   incoming.style.transform=`translate(${point.x-lane*Math.sin(Math.PI*arriving)}px,${incomingY}px) translate(-50%,-50%)`;
   if(tracing){
    const direction=phase===1?1:-1;
    traceValue(flowArrows[i],point,point.y,exitY,lane,leaving,direction,unchanged?0:Number(original.style.opacity),original);
    traceValue(flowArrows[i+n],point,entryY,point.y,-lane,arriving,direction,unchanged?0:Number(incoming.style.opacity),incoming);
   }
  }
 }
 function tick(now){if(!running||activePage!==62)return;if(lastTime)elapsed+=(now-lastTime)/1000;lastTime=now;paint();frame=requestAnimationFrame(tick);}
 function mechanism(){
  el('mechanism-scope-values').innerHTML='<p>Eight processed SRAG receiver records: first four adults of each outcome, in original order. They illustrate one of the actual full-test shuffles. The whole evaluation column is shuffled before these receiver rows are selected for display. Donor values can come from other test rows.</p><p>The displayed predictions are from recorded shuffle 1, seed 42. The chart reports the full-test baseline and mean ± one shuffle SD across 50 repetitions. The fixed XGBoost receives all study inputs. No model is refitted.</p>';
  cancelAnimationFrame(frame);running=false;elapsed=0;lastTime=0;lastPhase='';roundIndex=-1;renderRecords();el('motion-pause').textContent=reduced.matches?'Play':'Pause';el('motion-pause').setAttribute('aria-pressed','false');paint();if(!reduced.matches){running=true;frame=requestAnimationFrame(tick);}
 }
 function nextPhase(){
  cancelAnimationFrame(frame);running=false;lastTime=0;el('motion-pause').textContent='Play';el('motion-pause').setAttribute('aria-pressed','true');
  const base=Math.floor(elapsed/22)*22,t=elapsed%22,next=[3,6,14,17,22].find(value=>value>t+.05)??22;
  elapsed=base+next;lastPhase='';paint();
 }
 function featureDetail(){
  const mode=el('error-scale').value,r=data.rows[selectedFeature];
  el('feature-result-title').textContent=`${r.label} · SRAG experiment`;
  el('age-before').textContent=f(r.before);el('age-after').textContent=f(r.after_mean);
  el('age-importance').textContent=mode==='ratio'?`${f(r.ratio_mean,3)} ×  ± ${f(r.ratio_sd,3)} SD`:`+${f(r.difference_mean)}  ± ${f(r.difference_sd)} SD`;
  el('age-interpretation').textContent=mode==='ratio'?`${f(r.relative_increase_percent,2)}% more log loss error after shuffling this feature. This is a relative change in error.`:'This is extra log loss error, not a change in the mortality rate.';
  chartBars.forEach((bar,i)=>{bar.style.fill=i===selectedFeature?'#212322':'#a2aeaf';bar.setAttribute('aria-pressed',String(i===selectedFeature));});
 }
 async function scale(){
  if(!data||activePage!==63)return;
  cancelChart();const chartToken=chartGeneration,token=generation,mode=el('error-scale').value;
  featureDetail();
  for(const item of document.querySelectorAll('.formula-reading'))item.classList.toggle('active',item.dataset.scale===mode);
  el('ranking-caption').textContent=`${data.protocol.repeats} permutations per feature · ${data.protocol.n_evaluation.toLocaleString('en-US')} records · ${data.protocol.period} · whiskers: ±1 shuffle SD. Rounded display; calculations use full precision.`;
  el('study-details').textContent=`Hospitalized COVID cohort in the SRAG study. Fixed reference XGBoost, without class weights or resampling. Temporal evaluation: ${data.protocol.period}. This previously observed holdout is exploratory. The table shows eight receiver rows from the first recorded full-test shuffle; the chart summarizes all repeats.`;
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
  el('scale-explanation').textContent=mode==='ratio'?'Ratio: 1 = unchanged error; above 1 = more error; below 1 = less error. The dashed line marks the original error.':'Difference: extra log loss error. Zero means no change.';
  chartPaused=false;el('ranking-pause').textContent='Pause';el('ranking-pause').setAttribute('aria-pressed','false');
  const tooltip=el('chart-tooltip'),container=document.querySelector('.chart-container');
  const showTooltip=(i,event)=>{
   chartHovered=true;const r=data.rows[i];
   tooltip.innerHTML=`<strong>${r.label}</strong><span>Original log loss: ${f(r.before)}</span><span>Permuted mean: ${f(r.after_mean)}</span><span>${mode==='ratio'?'Ratio':'Difference'}: ${f(r[mode+'_mean'],mode==='ratio'?3:4)} ± ${f(r[mode+'_sd'],mode==='ratio'?3:4)} SD</span>`;
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
 function logloss(){
  const i=data.preview.rows.length-1,row=data.preview.rows[i],round=data.preview.rounds[roundIndex>=0?roundIndex:0];
  const originalObserved=row.y_obito?row.p_original:1-row.p_original,afterObserved=row.y_obito?round.probability[i]:1-round.probability[i];
  el('logloss-example').innerHTML=`<p class="small-label">Real teaching row ${row.record} · observed outcome: ${row.y_obito?'died (1)':'survived (0)'}</p><div class="logloss-case-grid"><div><h3>Original prediction</h3><p class="case-probability">${f(row.p_original,3)}</p><p>Probability assigned to what happened: <strong>${f(originalObserved,3)}</strong></p><p>Penalty −ln(${f(originalObserved,3)}): <strong>${f(row.loss_original)}</strong></p></div><div><h3>${round.label} shuffled</h3><p class="case-probability">${f(round.probability[i],3)}</p><p>Probability assigned to what happened: <strong>${f(afterObserved,3)}</strong></p><p>Penalty −ln(${f(afterObserved,3)}): <strong>${f(round.individual_loss[i])}</strong></p></div></div><p>Log loss averages these penalties across every evaluated row. A lower probability assigned to the outcome that occurred gives a larger penalty.</p>`;
  el('logloss-dialog').showModal();
 }
 async function start(page){stop();activePage=page;const token=generation;if(page!==62&&page!==63)return;try{data=await evidence;if(token!==generation)return;if(page===62)mechanism();else{selectedFeature=0;await scale();}}catch(error){if(token!==generation)return;el('status').textContent='SRAG evidence could not be loaded.';console.error(error);}}
 el('error-scale').addEventListener('change',()=>scale().catch(console.error));el('ranking-replay').addEventListener('click',()=>scale().catch(console.error));
 el('ranking-pause').addEventListener('click',()=>{chartPaused=!chartPaused;animations.forEach(a=>chartPaused?a.pause():a.play());el('ranking-pause').textContent=chartPaused?'Resume':'Pause';el('ranking-pause').setAttribute('aria-pressed',String(chartPaused));});
 el('motion-pause').addEventListener('click',()=>{running=!running;cancelAnimationFrame(frame);lastTime=0;el('motion-pause').textContent=running?'Pause':'Resume';el('motion-pause').setAttribute('aria-pressed',String(!running));if(running)frame=requestAnimationFrame(tick);});
 el('motion-step').addEventListener('click',nextPhase);
 el('mechanism-feature').addEventListener('change',event=>{cancelAnimationFrame(frame);running=false;lastTime=0;elapsed=Number(event.target.value)*22;lastPhase='';paint();el('motion-pause').textContent='Play';el('motion-pause').setAttribute('aria-pressed','true');});
 el('logloss-open').addEventListener('click',()=>{if(running)el('motion-pause').click();logloss();});el('logloss-close').addEventListener('click',()=>el('logloss-dialog').close());
 reduced.addEventListener('change',()=>{if(activePage===62)mechanism();if(activePage===63)scale().catch(console.error);});
 new ResizeObserver(()=>{measure();if(activePage===62&&data)paint();}).observe(document.querySelector('.patient-table-wrap'));
 document.fonts.ready.then(()=>{measure();if(activePage===62&&data)paint();});
 window.PFILesson={start,stop};
})();
