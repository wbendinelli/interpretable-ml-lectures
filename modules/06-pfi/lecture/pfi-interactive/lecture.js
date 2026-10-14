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
 const ns='http://www.w3.org/2000/svg';
 const nodes=[...document.querySelectorAll('.map-node')];
 let current=0,traced=false,selected=null,introStep=null;
 let introTimer=null;
 const pfiPath=['reduction','selection','wrapper','pfi'];
 const edges=[['reduction','selection'],['reduction','extraction'],['selection','filter'],['selection','embedded'],['selection','wrapper'],['filter','filter-examples'],['embedded','embedded-examples'],['wrapper','wrapper-examples'],['wrapper','pfi']];
 const explanations={
  reduction:'Dimensionality reduction uses fewer input dimensions.',
  selection:'Feature selection keeps a subset of the original input columns.',
  extraction:'In this reduction context, extraction builds a lower-dimensional representation.',
  filter:'Filter methods screen inputs using statistical criteria. Some criteria use the target.',
  embedded:'Embedded methods use selection mechanisms associated with fitting the model.',
  wrapper:'Wrapper methods use a learning algorithm to assess feature subsets.',
  pfi:'PFI measures how shuffling an input changes a trained model’s performance. It can support selection.'
 };
 const introduction=[
  {concept:'reduction',caption:'Dimensionality reduction: the overall goal is to use fewer input dimensions.'},
  {concept:'selection',caption:'Feature selection keeps selected original columns. Feature extraction builds a new representation.'},
  {concept:'filter',caption:'Filter methods use statistical criteria to screen the inputs.'},
  {concept:'embedded',caption:'Embedded methods use selection mechanisms associated with model fitting.'},
  {concept:'wrapper',caption:'Wrapper methods evaluate feature subsets using a learning algorithm. RFE and SFS are examples.'},
  {concept:'pfi',caption:'Raschka places PFI alongside wrappers. PFI measures a trained model’s reliance on an input and can support feature selection.'}
 ];
 const defaultCaption='PFI is shown here in the wrapper-method context of Raschka’s lecture.';

 function draw(){
  const svg=el('map-lines'),outer=el('map').getBoundingClientRect();
  if(!outer.width||!outer.height)return;
  svg.setAttribute('viewBox',`0 0 ${outer.width} ${outer.height}`);
  const previous=new Map([...svg.children].map(p=>[p.dataset.edge,p]));
  const horizontal=getComputedStyle(el('map')).getPropertyValue('--map-layout').trim()==='horizontal';
  for(const [a,b] of edges){
   const source=el('node-'+a),target=el('node-'+b);
   const from=source.getBoundingClientRect(),to=target.getBoundingClientRect(),key=a+'-'+b;
   let d;
   // In the flowing tree, parent rails run in the indentation beside children.
   const treeBranch=!horizontal&&(a==='reduction'||a==='selection'||to.left<from.right+12);
   if(treeBranch){
    const rail=from.left-outer.left+8,y1=from.bottom-outer.top+2;
    const x2=to.left-outer.left-5,y2=to.top+to.height/2-outer.top;
    d=`M${rail},${y1} V${y2} H${x2}`;
   }else{
    const x1=from.right-outer.left+4,y1=from.top+from.height/2-outer.top;
    const x2=to.left-outer.left-5,y2=to.top+to.height/2-outer.top,middle=(x1+x2)/2;
    d=`M${x1},${y1} H${middle} V${y2} H${x2}`;
   }
   let item=previous.get(key);
   if(!item){item=document.createElementNS(ns,'path');item.dataset.edge=key;svg.appendChild(item);}
   const visible=!source.classList.contains('unrevealed')&&!target.classList.contains('unrevealed');
   const active=traced&&pfiPath.includes(a)&&pfiPath.includes(b);
   item.setAttribute('class','map-path'+(active?' active-path':'')+(visible?'':' unrevealed'));
   item.setAttribute('d',d);

  }
 }
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
   const hidden=introStep!==null&&Number(node.dataset.reveal)>introStep;
   node.classList.toggle('unrevealed',hidden);
   node.inert=hidden;
   if(hidden)node.setAttribute('aria-hidden','true');else node.removeAttribute('aria-hidden');
   node.classList.toggle('ancestor',traced&&pfiPath.includes(key));
   node.classList.toggle('current',selected===key);
   if(key)node.setAttribute('aria-pressed',String(selected===key));
  }
  const presenting=introStep!==null;
  el('concept-caption').textContent=presenting?introduction[introStep].caption:selected?explanations[selected]:defaultCaption;
  el('status').textContent=el('concept-caption').textContent;
  draw();remember();
 }
 function cancelIntroduction(){
  clearTimeout(introTimer);introTimer=null;introStep=null;
 }
 function runIntroduction(){
  cancelIntroduction();
  traced=false;selected=null;
  if(reduced.matches){updateFocus();return;}
  introStep=0;selected='reduction';updateFocus();
  const delays=[1100,1400,1400,1400,1600,1000];
  function advance(){
   if(introStep===null)return;
   if(introStep<introduction.length-1){
    introStep++;selected=introduction[introStep].concept;updateFocus();
    introTimer=setTimeout(advance,delays[introStep]);
   }else{
    introStep=null;introTimer=null;traced=true;selected='pfi';updateFocus();
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
 const observer=new ResizeObserver(()=>draw());observer.observe(el('map'));
 for(const node of nodes)observer.observe(node);
 document.fonts.ready.then(()=>draw());show(current);
})();
