/* No animation dependency, scroll hijacking or autoplay testimonial rotation. */
(()=>{
 'use strict';
 const root=document.documentElement, hero=document.querySelector('.hero');
 const preference=matchMedia('(prefers-reduced-motion: reduce)');
 const finePointer=matchMedia('(hover: hover) and (pointer: fine)');
 const toggle=document.querySelector('.motion-toggle');
 const activeAnimations=new Set();
 let paused=false, heroVisible=true, lastY=scrollY, frame=0;
 try{paused=sessionStorage.getItem('draper-motion')==='paused'}catch{}
 const allowed=()=>!paused&&!preference.matches;
 // Load ambient footage after the page, and only when motion can actually play.
 const heroFilm=hero.querySelector('.hero-film'),connection=navigator.connection;
 let filmReadyToLoad=false,filmRequested=false,filmFailed=false;
 const saveBandwidth=()=>connection?.saveData||['slow-2g','2g'].includes(connection?.effectiveType);
 function syncHeroFilm(){
  if(!heroFilm)return;
  if(preference.matches||saveBandwidth()||filmFailed){heroFilm.pause();hero.classList.remove('has-film');return}
  const shouldPlay=allowed()&&heroVisible&&!document.hidden;
  if(!shouldPlay){heroFilm.pause();return}
  if(!filmReadyToLoad)return;
  if(!filmRequested){
   filmRequested=true;heroFilm.muted=true;
   const base=matchMedia('(max-width:760px)').matches?heroFilm.dataset.mobile:heroFilm.dataset.desktop;
   heroFilm.src=base+(heroFilm.canPlayType('video/webm; codecs=vp9')?'.webm':'.mp4');
   heroFilm.load();
  }
  if(heroFilm.paused)heroFilm.play().catch(()=>{hero.classList.remove('has-film')});
 }
 if(heroFilm){
  heroFilm.addEventListener('playing',()=>{
   if(!allowed()||!heroVisible||document.hidden||saveBandwidth()||filmFailed){heroFilm.pause();return}
   hero.classList.add('has-film');
  });
  heroFilm.addEventListener('error',()=>{filmFailed=true;hero.classList.remove('has-film')});
  connection?.addEventListener('change',syncHeroFilm);
  const enableFilm=()=>{filmReadyToLoad=true;syncHeroFilm()};
  const afterPage=()=>{'requestIdleCallback'in window?requestIdleCallback(enableFilm,{timeout:1800}):setTimeout(enableFilm,800)};
  if(document.readyState==='complete')afterPage();else addEventListener('load',afterPage,{once:true});
 }

 function animate(el,keyframes,options={}){
  if(!el||!allowed()||!el.animate)return;
  el.getAnimations().filter(a=>activeAnimations.has(a)).forEach(a=>a.cancel());
  const a=el.animate(keyframes,{duration:420,easing:'cubic-bezier(.22,1,.36,1)',...options});
  activeAnimations.add(a);a.finished.catch(()=>{}).finally(()=>activeAnimations.delete(a));return a;
 }
 function syncMotion(){
  root.dataset.motion=allowed()?'on':'paused';
  toggle.hidden=preference.matches;
  toggle.setAttribute('aria-pressed',String(paused));
  toggle.setAttribute('aria-label',paused?'Play motion':'Pause motion');
  toggle.querySelector('.motion-label').textContent=paused?'Play motion':'Pause motion';
  toggle.querySelector('.motion-symbol').textContent=paused?'▷':'Ⅱ';
  hero.classList.toggle('is-active',heroVisible&&!document.hidden);
  if(!allowed())activeAnimations.forEach(a=>a.finish());
  syncHeroFilm();
 }
 toggle.addEventListener('click',()=>{paused=!paused;try{sessionStorage.setItem('draper-motion',paused?'paused':'on')}catch{}syncMotion()});
 preference.addEventListener('change',syncMotion);document.addEventListener('visibilitychange',syncMotion);syncMotion();
 new IntersectionObserver(([entry])=>{heroVisible=entry.isIntersecting;syncMotion()},{threshold:0}).observe(hero);

 // A camera and a separate drafting layer respond in opposite directions.
 hero.addEventListener('pointermove',e=>{
  if(!allowed()||!finePointer.matches||e.pointerType==='touch')return;
  const r=hero.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;
  hero.style.setProperty('--hero-x',`${x*-16}px`);hero.style.setProperty('--hero-y',`${y*-12}px`);
  hero.style.setProperty('--draft-x',`${x*22}px`);hero.style.setProperty('--draft-y',`${y*16}px`);
 },{passive:true});
 hero.addEventListener('pointerleave',()=>['--hero-x','--hero-y','--draft-x','--draft-y'].forEach(p=>hero.style.setProperty(p,'0px')));
 if(scrollY<250){
  document.querySelectorAll('.hero-line>span').forEach((el,i)=>animate(el,[{transform:'translateY(105%)',opacity:.4},{transform:'translateY(0)',opacity:1}],{duration:900,delay:90+i*105,fill:'backwards'}));
  document.querySelectorAll('.hero-content>p,.hero-content>.button').forEach((el,i)=>animate(el,[{opacity:0,transform:'translateY(12px)'},{opacity:1,transform:'none'}],{duration:650,delay:420+i*100,fill:'backwards'}));
 }

 // Reveals never hide content in CSS, so no-JS and interrupted loads remain readable.
 const reveals=new IntersectionObserver(entries=>entries.forEach(entry=>{
  if(!entry.isIntersecting)return;
  reveals.unobserve(entry.target);
  animate(entry.target,[{opacity:.12,transform:'translateY(28px)'},{opacity:1,transform:'translateY(0)'}],{duration:720});
 }),{threshold:.1,rootMargin:'0px 0px -35px 0px'});
 document.querySelectorAll('main>section:not(.hero)>h2,.process-stage,.post,.format-collection article,.engineer-copy,.closing .endmark').forEach(el=>reveals.observe(el));
 const header=document.querySelector('.header');
 function onScroll(){
  frame=0;const y=scrollY,range=document.documentElement.scrollHeight-innerHeight;
  header.style.setProperty('--read-progress',range>0?y/range:0);
  if(Math.abs(y-lastY)>8){header.classList.toggle('is-away',y>lastY&&y>600&&!document.querySelector('#navigation').classList.contains('open'));lastY=y}
 }
 addEventListener('scroll',()=>{if(!frame)frame=requestAnimationFrame(onScroll)},{passive:true});onScroll();
 header.addEventListener('focusin',()=>header.classList.remove('is-away'));
 document.addEventListener('click',e=>{if(!header.contains(e.target)&&document.querySelector('#navigation').classList.contains('open'))document.querySelector('.menu-toggle').click()});
 document.querySelectorAll('a[href^="#"]').forEach(a=>a.addEventListener('click',()=>header.classList.remove('is-away')));

 const scrubber=document.querySelector('#arc-progress');
 const stageLabels=['Establishment, months 1 to 3','Growth, months 3 to 6','Thought Leader, month 6 onwards'];
 scrubber.addEventListener('input',()=>document.querySelector(`[data-phase="${scrubber.value}"]`).click());
 document.addEventListener('draper:select',({detail:{selector,index,tab}})=>{
  let targets=[];
  if(selector==='[data-step]'){
   targets=[document.querySelector('#step-title'),document.querySelector('#step-copy'),document.querySelector('.page-number')];
   const art=document.querySelector('.process-art');
   if(allowed())art.style.transform=`scale(${1+index*.007}) translateX(${-index*.25}%)`;
   const track=tab.parentElement;if(track.scrollWidth>track.clientWidth)track.scrollTo({left:tab.offsetLeft-track.offsetLeft-track.clientWidth/2+tab.clientWidth/2,behavior:allowed()?'smooth':'instant'});
  }
  if(selector==='[data-customer]')targets=[document.querySelector('.testimonial-copy')];
  if(selector==='[data-phase]'){targets=[document.querySelector('#phase-panel')];scrubber.value=index;scrubber.setAttribute('aria-valuetext',stageLabels[index]);}
  if(selector==='[data-arc]')targets=[document.querySelector('#arc-panel')];
  if(selector==='[data-package]')targets=[document.querySelector('.package-about'),document.querySelector('#package-features')];
  targets.forEach((el,i)=>animate(el,[{opacity:.15,transform:'translateY(10px)'},{opacity:1,transform:'translateY(0)'}],{duration:360,delay:i*35}));
 });
 const portrait=document.querySelector('#customer-portrait');
 portrait.addEventListener('load',()=>animate(portrait,[{opacity:.35},{opacity:1}],{duration:450}));
 document.querySelectorAll('.faq details').forEach(el=>el.addEventListener('toggle',()=>{if(el.open)animate(el.querySelector('p'),[{opacity:0,transform:'translateY(-5px)'},{opacity:1,transform:'none'}],{duration:280})}));

 // Horizontal gestures supplement, rather than replace, visible keyboard controls.
 function swipe(el,selector){
  let start;
  el.addEventListener('pointerdown',e=>{if(e.pointerType==='touch')start={x:e.clientX,y:e.clientY}},{passive:true});
  el.addEventListener('pointercancel',()=>{start=null});
  el.addEventListener('pointerup',e=>{
   if(!start)return;const dx=e.clientX-start.x,dy=e.clientY-start.y;start=null;
   if(Math.abs(dx)<55||Math.abs(dx)<Math.abs(dy)*1.7)return;
   const tabs=[...document.querySelectorAll(selector)],i=tabs.findIndex(t=>t.getAttribute('aria-selected')==='true');
   tabs[(i+(dx<0?1:tabs.length-1))%tabs.length].click();
  },{passive:true});
 }
 swipe(document.querySelector('.testimonial-portrait'),'[data-customer]');
 swipe(document.querySelector('.process-sheet'),'[data-step]');

 // Only warm the other portrait files when a visitor approaches this section.
 const portraitWarmup=new IntersectionObserver(([entry],observer)=>{if(entry.isIntersecting){observer.disconnect();if(!navigator.connection?.saveData)['daniel','ammar'].forEach(name=>{const im=new Image();im.src=`assets/${name}-portrait-v9.webp`})}},{rootMargin:'250px'});
 portraitWarmup.observe(document.querySelector('#results'));
})();
