'use strict';
(()=>{
 const el=id=>document.getElementById(id);
 if('scrollRestoration' in history)history.scrollRestoration='manual';
 const routes=[
  ['cover','Permutation Feature Importance',null,0],
  ['61','Where PFI fits',61,0],['62','The permutation experiment',62,42],['63','From error to importance',63,116],['65','Importance and selection',65,178],
  ['66','SRAG · data and inputs',66,202],['66-selection','SRAG · model and evaluation',null,202],
  ['67','Code · fitted model',67,235],['68','Code · baseline',68,266],['69','Code · shuffle',69,303],['70','Code · evaluate',70,394],['71','Code · repeats',71,430],
  ['73','PFI · strengths and limits',73,777],['dependence-results','SRAG · related inputs',null,777],['thanks','Thank you',null,777]
 ].map(([key,title,source,time])=>({key,title,source,time,section:'lesson'}));
 const pages=routes.map(r=>r.key),mainCount=routes.length;
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');
 const ns='http://www.w3.org/2000/svg';
 const nodes=[...document.querySelectorAll('.map-node')];
 let current=0,originalMode=false,traced=false,selected=null,introStep=null;
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
  history.replaceState(null,'',`#slide-${page}${originalMode?'-original':page==='61'&&traced?'-path':''}`);
  if(window.openai?.setWidgetState)window.openai.setWidgetState({
   modelContent:{presentation:'PFI lecture',slide_original:page,layout:!originalMode?'interactive adaptation':'original',pfi_path_highlighted:traced,selected_concept:selected,introduction_step:introStep},
   privateContent:{page,originalMode,traced,selected,introStep}
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
  if(!route.source)originalMode=false;
  const interactive=!originalMode,isStudy=key==='66'||key==='66-selection'||key==='73'||key==='dependence-results'||key==='cover'||key==='thanks';
  cancelIntroduction();
  window.PFILesson?.stop();window.PFISequence?.stop();window.PFIStudy?.stop();
  el('context-slide').hidden=!(interactive&&page===61);
  el('mechanism-slide').hidden=!(interactive&&page===62);
  el('results-slide').hidden=!(interactive&&page===63);
  el('bridge-slide').hidden=!(interactive&&page===65);
  el('walkthrough-slide').hidden=!(interactive&&page>=67&&page<=71);
  el('study-slide').hidden=!(interactive&&isStudy);
  el('original-slide').hidden=interactive;
  el('original-toggle').hidden=!route.source;
  el('original-toggle').textContent=originalMode?'View interactive slide':'View original';
  el('original-toggle').setAttribute('aria-pressed',String(originalMode));
  if(route.source){el('original').src=`imagens/slide-${String(route.source).padStart(3,'0')}.png`;el('original').alt=`Original slide ${route.source}, Sebastian Raschka, STAT 451, Feature Selection`;}
  el('select').value=key;el('previous').disabled=current===0;el('next').disabled=current===routes.length-1;
  el('position').textContent=`${current+1} / ${mainCount}`;
  el('next').textContent=current===0?'Start →':current===mainCount-2?'Closing →':'Next slide →';
  el('section-label').textContent='Interpretable Machine Learning';
  el('video').href=`https://www.youtube.com/watch?v=VUvShOEFdQo&t=${route.time}s`;
  el('source').hidden=interactive;el('source').innerHTML=interactive?`${route.section==='appendix'?'Appendix · ':''}Based on Raschka’s sequence. Course book: <a href="https://christophm.github.io/interpretable-ml-book/feature-importance.html" target="_blank" rel="noreferrer">Molnar, PFI</a>`:`Original content and layout: Sebastian Raschka. <a href="https://sebastianraschka.com/pdf/lecture-notes/stat451fs21/13_feat-sele__slides.pdf#page=${route.source}" target="_blank" rel="noreferrer">Source slide ${route.source}</a>`;
  window.scrollTo({top:0,behavior:'auto'});
  if(interactive&&page===61)runIntroduction();
  else {remember();if(interactive){if(isStudy)window.PFIStudy?.start(key);else if(page<=63)window.PFILesson?.start(page);else window.PFISequence?.start(Number.isNaN(page)?key:page);}}
 }
 for(const node of nodes.filter(n=>n.dataset.concept))node.addEventListener('click',()=>{
  cancelIntroduction();traced=false;selected=node.dataset.concept;
  updateFocus();
 });
 el('original-toggle').addEventListener('click',()=>{originalMode=!originalMode;show(current);});
 el('reading-toggle').addEventListener('click',()=>{const open=el('readings').hidden;el('readings').hidden=!open;el('reading-toggle').setAttribute('aria-expanded',String(open));});
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
  if(pages.includes(base)){current=pages.indexOf(base);originalMode=incoming.endsWith('-original');traced=incoming.endsWith('-path');selected=traced?'pfi':null;}
 }
 readRouteHash();window.addEventListener('hashchange',()=>{readRouteHash();show(current);});
 reduced.addEventListener('change',()=>{if(reduced.matches&&pages[current]==='61'&&!originalMode){cancelIntroduction();updateFocus();}});
 window.addEventListener('pagehide',()=>{cancelIntroduction();window.PFILesson?.stop();window.PFISequence?.stop();window.PFIStudy?.stop();});
 const observer=new ResizeObserver(()=>draw());observer.observe(el('map'));
 for(const node of nodes)observer.observe(node);
 document.fonts.ready.then(()=>draw());show(current);
 for(const p of new Set(routes.map(r=>r.source).filter(Boolean))){const img=new Image();img.src=`imagens/slide-${String(p).padStart(3,'0')}.png`;}
})();
