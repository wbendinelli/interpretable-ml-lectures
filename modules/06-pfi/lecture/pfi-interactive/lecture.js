'use strict';
(()=>{
 const el=id=>document.getElementById(id);
 if('scrollRestoration' in history)history.scrollRestoration='manual';
 const routes=[
  ['cover','Permutation Feature Importance'],
  ['61','Where PFI fits'],['62','The permutation experiment'],['63','From error to importance'],['65','Importance and selection'],
  ['66','SRAG · data and inputs'],['66-selection','SRAG · model and evaluation'],
  ['67','Code · fitted model'],['68','Code · baseline'],['69','Code · shuffle'],['70','Code · evaluate'],['71','Code · repeats'],
  ['73','PFI · strengths and limits'],['dependence-results','SRAG · related inputs'],['thanks','Thank you']
 ].map(([key,title])=>({key,title}));
 const pages=routes.map(r=>r.key),mainCount=routes.length;
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');
 const nodes=[...document.querySelectorAll('.molnar-node')];
 let current=0,traced=false,selected=null,introStep=null;
 let introTimer=null;
 const pfiPath=['posthoc','agnostic','global','importance','pfi'];
 const explanations={
  posthoc:'Post-hoc: apply the interpretation method after model training.',
  agnostic:'Model-agnostic: use inputs and predictions without inspecting model internals.',
  global:'Global: summarize behavior across the evaluation data, rather than explain one prediction.',
  importance:'Feature importance: rank features using a stated definition of importance.',
  pfi:'PFI measures how shuffling a feature changes the prediction error of the fixed model.'
 };
 const introduction=pfiPath.map(concept=>({concept,caption:explanations[concept]}));
 const defaultCaption='Molnar’s taxonomy locates the method; this is not the PFI algorithm.';

 function remember(){
  const page=pages[current];
  history.replaceState(null,'',`#slide-${page}${page==='61'&&traced?'-path':''}`);
  if(window.openai?.setWidgetState)window.openai.setWidgetState({
   modelContent:{presentation:'PFI lecture',route:page,layout:'interactive adaptation',pfi_path_highlighted:traced,selected_concept:selected,introduction_step:introStep},
   privateContent:{page,traced,selected,introStep}
  }).catch(()=>{});
 }
 function updateFocus(){
  for(const node of nodes){
   const key=node.dataset.concept;
   node.classList.toggle('ancestor',traced&&pfiPath.includes(key));
   node.classList.toggle('current',selected===key);
   node.setAttribute('aria-pressed',String(selected===key));
  }
  const progress=traced?1:selected?Math.min(pfiPath.indexOf(selected),3)/3:0;
  el('map').style.setProperty('--route-progress',String(Math.max(0,progress)));
  el('concept-caption').textContent=introStep!==null?introduction[introStep].caption:selected?explanations[selected]:defaultCaption;
  el('status').textContent=el('concept-caption').textContent;
  remember();
 }
 function cancelIntroduction(){
  clearTimeout(introTimer);introTimer=null;introStep=null;
 }
 function runIntroduction(){
  cancelIntroduction();
  traced=false;selected=null;
  if(reduced.matches){updateFocus();return;}
  introStep=0;selected='posthoc';updateFocus();
  const delays=[1100,1400,1400,1500,1300];
  function advance(){
   if(introStep===null)return;
   if(introStep<introduction.length-1){
    introStep++;selected=introduction[introStep].concept;updateFocus();
    introTimer=setTimeout(advance,delays[introStep]);
   }else{
    introStep=null;introTimer=null;traced=true;selected=null;updateFocus();
   }
  }
  introTimer=setTimeout(advance,delays[0]);
 }
 function show(index){
  current=Math.max(0,Math.min(index,routes.length-1));
  const route=routes[current],key=route.key,page=Number(key);
  const isStudy=key==='66'||key==='66-selection'||key==='73'||key==='dependence-results'||key==='cover'||key==='thanks';
  cancelIntroduction();
  window.PFILesson?.stop();window.PFISequence?.stop();window.PFIStudy?.stop();
  el('context-slide').hidden=!(page===61);
  el('mechanism-slide').hidden=!(page===62);
  el('results-slide').hidden=!(page===63);
  el('bridge-slide').hidden=!(page===65);
  el('walkthrough-slide').hidden=!(page>=67&&page<=71);
  el('study-slide').hidden=!(isStudy);
  el('select').value=key;el('previous').disabled=current===0;el('next').disabled=current===routes.length-1;
  el('position').textContent=`${current+1} / ${mainCount}`;
  el('next').textContent=current===0?'Start →':current===mainCount-2?'Closing →':'Next slide →';
  window.scrollTo({top:0,behavior:'auto'});
  if(page===61)runIntroduction();
  else {remember();if(isStudy)window.PFIStudy?.start(key);else if(page<=63)window.PFILesson?.start(page);else window.PFISequence?.start(Number.isNaN(page)?key:page);}
 }
 for(const node of nodes.filter(n=>n.dataset.concept))node.addEventListener('click',()=>{
  cancelIntroduction();traced=false;selected=node.dataset.concept;
  updateFocus();
 });
 el('previous').addEventListener('click',()=>show(current-1));el('next').addEventListener('click',()=>show(current+1));
 el('select').innerHTML=routes.map(r=>`<option value="${r.key}">${r.title}</option>`).join('');
 window.PFINavigate=page=>{const index=pages.indexOf(String(page));if(index>=0)show(index);};
 el('select').addEventListener('change',()=>show(pages.indexOf(el('select').value)));
 document.addEventListener('keydown',e=>{
  if(['SELECT','INPUT','TEXTAREA','BUTTON'].includes(document.activeElement.tagName)||e.altKey||e.ctrlKey||e.metaKey)return;
  if(e.key==='ArrowRight'){e.preventDefault();show(current+1);}else if(e.key==='ArrowLeft'){e.preventDefault();show(current-1);}
 });
 function readRouteHash(){
  const incoming=location.hash.replace(/^#slide-/,'').replace(/-step-\d+$/,'');
  const raw=incoming.replace(/-(original|path)$/,'');
  const aliases={'66-treatment':'66','66-evaluation':'66-selection','dependence':'dependence-results','dependence-steps':'dependence-results','64':'65','appendix-oob':'66-selection','72':'73'};
  const base=aliases[raw]||raw;
  if(pages.includes(base)){current=pages.indexOf(base);traced=incoming.endsWith('-path');selected=traced?'pfi':null;}
 }
 readRouteHash();window.addEventListener('hashchange',()=>{readRouteHash();show(current);});
 reduced.addEventListener('change',()=>{if(reduced.matches&&pages[current]==='61'){cancelIntroduction();updateFocus();}});
 window.addEventListener('pagehide',()=>{cancelIntroduction();window.PFILesson?.stop();window.PFISequence?.stop();window.PFIStudy?.stop();});
 show(current);
})();
