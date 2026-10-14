'use strict';
(()=>{
 const el=id=>document.getElementById(id);
 if('scrollRestoration' in history)history.scrollRestoration='manual';
 const pages=Array.from({length:13},(_,i)=>61+i);
 const times=[0,42,116,143,178,202,235,266,303,394,430,638,777];
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
  history.replaceState(null,'',`#slide-${page}${page<=63&&originalMode?'-original':page===61&&traced?'-path':''}`);
  if(window.openai?.setWidgetState)window.openai.setWidgetState({
   modelContent:{presentation:'PFI lecture',slide_original:page,layout:page<=63&&!originalMode?'interactive adaptation':'original',pfi_path_highlighted:traced,selected_concept:selected,introduction_step:introStep},
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
  current=Math.max(0,Math.min(index,pages.length-1));
  const page=pages[current],interactive=page<=63&&!originalMode;
  cancelIntroduction();
  window.PFILesson?.stop();
  el('context-slide').hidden=!(interactive&&page===61);
  el('mechanism-slide').hidden=!(interactive&&page===62);
  el('results-slide').hidden=!(interactive&&page===63);
  el('original-slide').hidden=interactive;
  el('original-toggle').hidden=page>63;
  el('original-toggle').textContent=originalMode?'View interactive slide':'View original';
  el('original-toggle').setAttribute('aria-pressed',String(originalMode));
  el('original').src=`imagens/slide-${String(page).padStart(3,'0')}.png`;
  el('original').alt=`Original slide ${page}, Sebastian Raschka, STAT 451, Feature Selection`;
  el('select').value=String(page);el('previous').disabled=current===0;el('next').disabled=current===pages.length-1;
  el('position').textContent=`${current+1} / ${pages.length}`;
  el('video').href=`https://www.youtube.com/watch?v=VUvShOEFdQo&t=${times[current]}s`;
  el('source').innerHTML=interactive?'Based on Raschka’s sequence. Course book: <a href="https://christophm.github.io/interpretable-ml-book/feature-importance.html" target="_blank" rel="noreferrer">Molnar, PFI</a>':`Original content and layout: Sebastian Raschka. <a href="https://sebastianraschka.com/pdf/lecture-notes/stat451fs21/13_feat-sele__slides.pdf#page=${page}" target="_blank" rel="noreferrer">Source slide ${page}</a>`;
  window.scrollTo({top:0,behavior:'auto'});
  if(interactive&&page===61)runIntroduction();
  else {remember();if(interactive)window.PFILesson?.start(page);}
 }
 for(const node of nodes.filter(n=>n.dataset.concept))node.addEventListener('click',()=>{
  cancelIntroduction();traced=false;selected=node.dataset.concept;
  updateFocus();
 });
 el('original-toggle').addEventListener('click',()=>{originalMode=!originalMode;show(current);});
 el('reading-toggle').addEventListener('click',()=>{const open=el('readings').hidden;el('readings').hidden=!open;el('reading-toggle').setAttribute('aria-expanded',String(open));});
 el('previous').addEventListener('click',()=>show(current-1));el('next').addEventListener('click',()=>show(current+1));
 el('select').innerHTML=pages.map(n=>`<option value="${n}">${n===61?'Context · adapted':n===62?'Experiment · adapted':n===63?'Importance · adapted':'Original slide '+n}</option>`).join('');
 el('select').addEventListener('change',()=>show(pages.indexOf(Number(el('select').value))));
 document.addEventListener('keydown',e=>{
  if(['SELECT','INPUT','TEXTAREA','BUTTON'].includes(document.activeElement.tagName)||e.altKey||e.ctrlKey||e.metaKey)return;
  if(e.key==='ArrowRight'){e.preventDefault();show(current+1);}else if(e.key==='ArrowLeft'){e.preventDefault();show(current-1);}
 });
 const hash=location.hash.match(/^#slide-(\d+)(?:-(original|path)|-step-\d+)?$/);
 if(hash&&pages.includes(Number(hash[1]))){current=pages.indexOf(Number(hash[1]));originalMode=hash[2]==='original';traced=hash[2]==='path';selected=traced?'pfi':null;}
 reduced.addEventListener('change',()=>{if(reduced.matches&&current===0&&!originalMode){cancelIntroduction();updateFocus();}});
 window.addEventListener('pagehide',()=>{cancelIntroduction();window.PFILesson?.stop();});
 const observer=new ResizeObserver(()=>draw());observer.observe(el('map'));
 for(const node of nodes)observer.observe(node);
 document.fonts.ready.then(()=>draw());show(current);
 for(const p of pages){const img=new Image();img.src=`imagens/slide-${String(p).padStart(3,'0')}.png`;}
})();
