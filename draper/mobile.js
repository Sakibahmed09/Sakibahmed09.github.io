/* A mobile composition of the same material. Desktop placements are restored. */
(()=>{
 const $=s=>document.querySelector(s),mq=matchMedia('(max-width:760px)');
 const root=document.documentElement,disclosures=[],placements=[];
 document.querySelectorAll('h2 br').forEach(br=>br.before(document.createTextNode(' ')));
 function park(el){const marker=document.createComment('Original placement');el.before(marker);placements.push({el,marker});return el}
 function disclosure(el,label,className){
  const d=document.createElement('details'),s=document.createElement('summary');
  d.className=`mobile-disclosure ${className}`;s.textContent=label;el.before(d);d.append(s,el);disclosures.push(d);return d;
 }
 disclosure($('.hero-content>p'),'Your LinkedIn team','hero-explainer');
 disclosure($('.format-intro'),'Choosing the right format','format-explainer');
 disclosure($('.arc-intro'),'How the strategy works','arc-explainer');
 disclosure($('.arc-reading'),'Explore the three arcs','arc-deeper');
 disclosure($('#package-features'),"What’s included",'package-inclusions');
 disclosure($('.footer-description'),'About Draper','footer-explainer');

 const portfolio=park($('#case-studies')),results=park($('#results'));
 const customerTabs=park($('.customer-tabs')),outcome=park($('.customer-outcome'));

 // Native scrolling: examples remain real, inspectable and individually linked.
 const rails=[];
 function makeRail(selector,itemSelector,label){
  const rail=$(selector),items=[...rail.querySelectorAll(itemSelector)];
  const controls=document.createElement('div');controls.className='folio-controls mobile-only';
  const prev=document.createElement('button'),next=document.createElement('button'),count=document.createElement('span');
  prev.type=next.type='button';prev.textContent='←';next.textContent='→';
  prev.setAttribute('aria-label',`Previous ${label}`);next.setAttribute('aria-label',`Next ${label}`);
  count.setAttribute('aria-live','polite');count.setAttribute('aria-atomic','true');controls.append(prev,count,next);rail.after(controls);
  rail.setAttribute('role','region');
  rail.setAttribute('aria-label',label==='work example'?'Client work gallery':'Content formats gallery');
  let index=0,timer;
  function state(){count.textContent=`${String(index+1).padStart(2,'0')} / ${String(items.length).padStart(2,'0')}`;prev.disabled=index===0;next.disabled=index===items.length-1}
  function go(i){index=Math.max(0,Math.min(items.length-1,i));const left=items[index].offsetLeft-items[0].offsetLeft;rail.scrollTo({left,behavior:root.dataset.motion==='on'?'smooth':'instant'});state()}
  prev.addEventListener('click',()=>go(index-1));next.addEventListener('click',()=>go(index+1));
  rail.addEventListener('scroll',()=>{clearTimeout(timer);timer=setTimeout(()=>{const r=rail.getBoundingClientRect();index=items.reduce((best,el,i)=>Math.abs(el.getBoundingClientRect().left-r.left)<Math.abs(items[best].getBoundingClientRect().left-r.left)?i:best,0);state()},120)},{passive:true});
  rails.push({rail,reset:()=>{index=0;rail.scrollLeft=0;state()}});state();
 }
 makeRail('.post-composition','.post','work example');makeRail('.format-collection','article','format');

 const questions=[...document.querySelectorAll('.faq>details')];
 const more=document.createElement('button');more.type='button';more.className='faq-more mobile-only';more.setAttribute('aria-expanded','false');
 let allQuestions=false;
 function showQuestions(){questions.forEach((q,i)=>q.hidden=mq.matches&&!allQuestions&&i>2);more.textContent=allQuestions?'Show fewer questions':`See ${questions.length-3} more questions`;more.setAttribute('aria-expanded',String(allQuestions))}
 more.addEventListener('click',()=>{allQuestions=!allQuestions;showQuestions()});$('.faq').append(more);

 function apply(){
  root.classList.toggle('mobile-edition',mq.matches);
  disclosures.forEach(d=>{d.open=!mq.matches});
  if(mq.matches){
   $('.backers').after(portfolio);portfolio.after(results);
   $('#testimonial-panel').before(customerTabs);
   $('.testimonial-portrait').append(outcome);
  }else placements.forEach(({el,marker})=>marker.after(el));
  showQuestions();rails.forEach(r=>r.reset());
 }
 mq.addEventListener('change',apply);apply();
})();
