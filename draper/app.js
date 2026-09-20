const $=s=>document.querySelector(s);
const menu=$('.menu-toggle'),nav=$('#navigation');
function closeMenu(){nav.classList.remove('open');menu.setAttribute('aria-expanded','false');menu.setAttribute('aria-label','Open menu')}
menu.addEventListener('click',()=>{const open=menu.getAttribute('aria-expanded')!=='true';nav.classList.toggle('open',open);menu.setAttribute('aria-expanded',String(open));menu.setAttribute('aria-label',open?'Close menu':'Open menu')});nav.querySelectorAll('a').forEach(a=>a.addEventListener('click',closeMenu));document.addEventListener('keydown',e=>{if(e.key==='Escape')closeMenu()});
function wireTabs(selector,onSelect){const tabs=[...document.querySelectorAll(selector)];function select(i,focus=false){tabs.forEach((t,n)=>{t.setAttribute('aria-selected',String(i===n));t.tabIndex=i===n?0:-1});onSelect(i,tabs[i]);document.dispatchEvent(new CustomEvent('draper:select',{detail:{selector,index:i,tab:tabs[i]}}));if(focus)tabs[i].focus()}tabs.forEach((t,i)=>{t.addEventListener('click',()=>select(i));t.addEventListener('keydown',e=>{let n;if(['ArrowRight','ArrowDown'].includes(e.key))n=(i+1)%tabs.length;if(['ArrowLeft','ArrowUp'].includes(e.key))n=(i+tabs.length-1)%tabs.length;if(e.key==='Home')n=0;if(e.key==='End')n=tabs.length-1;if(n!==undefined){e.preventDefault();select(n,true)}})});return select}
const steps=[['Onboarding Sprint','We align on goals, voice, and strategy.'],['Profile Deep Dive','We review and optimise your LinkedIn profile.'],['Content Supercharged','We create a month of posts, carousels, infographics and short-form video.'],['Easy Approval','Review and provide async feedback so we get it right.'],['Experimentation','We run tests and optimise our strategy.'],['Pipeline Generation','Posts go live. Leads come in. You focus on building.']];let step=0;
const selectStep=wireTabs('[data-step]',(i,t)=>{step=i;$('#step-title').textContent=steps[i][0];$('#step-copy').textContent=steps[i][1];$('.page-number').textContent=String(i+1).padStart(2,'0');$('#step-count').textContent=`${i+1} of 6`;$('#process-panel').setAttribute('aria-labelledby',t.id)});$('#step-next').addEventListener('click',()=>selectStep((step+1)%6));$('#step-prev').addEventListener('click',()=>selectStep((step+5)%6));
const arcStories=[
 ['Earn trust.','The conviction behind the company.','The customer conversation that changed what we built.'],
 ['Make progress visible.','Decisions, evidence and work in motion.','What we changed after watching customers use the product.'],
 ['Lead the conversation.','An informed position on what comes next.','The assumption our industry needs to leave behind.']
];
const selectArc=wireTabs('[data-arc]',(i,t)=>{
 const a=arcStories[i];
 $('#arc-question').textContent=a[0];$('#arc-description').textContent=a[1];$('#arc-example').textContent=a[2];
 $('#arc-panel').setAttribute('aria-labelledby',t.id);$('.narrative-chart').dataset.arc=i;
});
const phases=[{mix:[60,30,10],copy:'First, give people a reason to trust you.'},{mix:[40,40,20],copy:'Then, let the work build your reputation.'},{mix:[10,20,70],copy:'Become a voice your market looks to.'}];
let arcFrame=0,currentMix=[60,30,10];
function drawArcs(mix){
 const right=[320,320-2.8*mix[0],40+2.8*mix[2],40],left=[320,176,104,80];
 const band=(i)=>`M0 ${left[i]} C280 ${left[i]} 520 ${right[i]} 800 ${right[i]} L800 ${right[i+1]} C520 ${right[i+1]} 280 ${left[i+1]} 0 ${left[i+1]}Z`;
 ['founder','builder','pulse'].forEach((name,i)=>{
  $('.'+name+'-area').setAttribute('d',band(i));
  const label=$('.'+name+'-label');label.setAttribute('x','690');label.setAttribute('y',String((right[i]+right[i+1])/2+7));
 });
 $('.pulse-hatch').setAttribute('d',band(2));
 $('.arc-stroke').setAttribute('d',[1,2,3].map(i=>`M0 ${left[i]} C280 ${left[i]} 520 ${right[i]} 800 ${right[i]}`).join(''));
 document.querySelectorAll('.phase-mix b').forEach((el,i)=>el.textContent=Math.round(mix[i])+'%');
 currentMix=mix;
}
wireTabs('[data-phase]',(i,t)=>{
 const phase=phases[i],from=[...currentMix];cancelAnimationFrame(arcFrame);
 $('#phase-description').textContent=phase.copy;$('#phase-panel').setAttribute('aria-labelledby',t.id);selectArc(i);
 $('.ramp-arcs').setAttribute('aria-label',`${t.firstChild.textContent}: Founder ${phase.mix[0]}%, Builder ${phase.mix[1]}%, Pulse ${phase.mix[2]}%. Illustrative editorial mix.`);
 if(matchMedia('(prefers-reduced-motion: reduce)').matches){drawArcs(phase.mix);return;}
 const start=performance.now();
 const frame=now=>{const t=Math.min(1,(now-start)/850),e=1-Math.pow(1-t,4);drawArcs(from.map((v,n)=>v+(phase.mix[n]-v)*e));if(t<1)arcFrame=requestAnimationFrame(frame);};
 arcFrame=requestAnimationFrame(frame);
});
drawArcs(currentMix);selectArc(0);


const packages=[{title:'Founder-led',desc:'Make the founder’s point of view a reason to choose the company.',seats:'Your voice. Your market position.',cta:'Book a call',features:['A clear position in your market','A narrative built from your expertise','Your LinkedIn channel, run end to end']},{title:'Executive-led',desc:'Turn leadership expertise into a shared market presence.',seats:'Distinct voices. A common direction.',cta:'Book a call',features:['Individual positioning for your executives','A coordinated company narrative','Leadership channels, run end to end']},{title:'Company-wide',desc:'Bring founder conviction, executive expertise and employee voices together.',seats:'The whole company. One channel strategy.',cta:'Book a call',features:['Founder, executive and employee narratives','Company page ownership','One accountable partner across LinkedIn']}];wireTabs('[data-package]',(i,t)=>{const p=packages[i];$('#package-title').textContent=p.title;$('#package-description').textContent=p.desc;$('#package-seat').textContent=p.seats;$('#package-cta').replaceChildren(document.createTextNode(p.cta+' '),Object.assign(document.createElement('span'),{textContent:'↗'}));$('#package-features').replaceChildren(...p.features.map(f=>Object.assign(document.createElement('li'),{textContent:f})));$('#package-panel').setAttribute('aria-labelledby',t.id)});
const dialog=$('#work-dialog');document.querySelectorAll('[data-image]').forEach(b=>b.addEventListener('click',()=>{$('#dialog-title').textContent=b.dataset.title;$('#dialog-image').src=b.dataset.image;$('#dialog-image').alt=b.dataset.title+' — LinkedIn post';dialog.showModal()}));$('.dialog-close').addEventListener('click',()=>dialog.close());dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close()}});
const ambientVideos=[...document.querySelectorAll('video[autoplay]')];if(matchMedia('(prefers-reduced-motion: reduce)').matches){ambientVideos.forEach(v=>{v.autoplay=false;v.pause()})}else if('IntersectionObserver'in window){const observer=new IntersectionObserver(entries=>{entries.forEach(({target,isIntersecting})=>{if(isIntersecting)target.play().catch(()=>{});else target.pause()})},{threshold:.15});ambientVideos.forEach(v=>observer.observe(v))}
const customers=[{name:'Ibrahim Khan',company:'Cur8 Capital · Asset management',quote:"Draper is quietly becoming indispensable. That's the best compliment I can give.",stat:'£3M',label:'new client investment',portrait:'assets/ibrahim-portrait-v4.webp',link:'https://www.linkedin.com/in/mibrahimkhan/'},{name:'Daniel Fraai',company:'YLookup · EQT Ventures',quote:'Something is working. You guys really tickled the algorithm there.',stat:'500K+',label:'impressions in three months',portrait:'assets/daniel-portrait-v9.webp',link:'https://www.linkedin.com/in/danieljfraai/'},{name:'Ammar Khan',company:'Sahl AI · HealthTech',quote:'Traced enterprise contracts directly to Draper + top talent reaching out to Sahl AI',stat:'$1.3M',label:'contract closed',portrait:'assets/ammar-portrait-v9.webp',link:'https://www.linkedin.com/in/ammarkhan14/'}];let customerIndex=0;
function showCustomerPortrait(){const c=customers[customerIndex],im=$('#customer-portrait');im.src=c.portrait;im.alt=c.name}
wireTabs('[data-customer]',(i,t)=>{customerIndex=i;const c=customers[i];$('#customer-quote').textContent='“'+c.quote+'”';$('#customer-name').textContent=c.name;$('#customer-company').textContent=c.company;$('#customer-stat').textContent=c.stat;$('#customer-stat-label').textContent=c.label;$('#customer-link').href=c.link;$('#testimonial-panel').setAttribute('aria-labelledby',t.id);showCustomerPortrait()});showCustomerPortrait();

wireTabs('[data-evidence]',(i)=>{document.querySelectorAll('.evidence-sheet').forEach((p,n)=>{p.hidden=n!==i})});
