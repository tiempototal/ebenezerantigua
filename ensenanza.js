/* Índice lateral interactivo: resalta la sección activa al hacer scroll y funciona como menú */
(function(){
  var toc=document.querySelector('.tocs .toc');if(!toc)return;
  var lis=[].slice.call(toc.querySelectorAll('li'));
  var items=lis.map(function(li){var a=li.querySelector('a[href^="#"]');var el=a&&document.getElementById(a.getAttribute('href').slice(1));return el?{li:li,a:a,el:el}:null}).filter(Boolean);
  if(!items.length)return;
  var list=toc.querySelector('ol'),fill=toc.querySelector('.tp i'),pct=toc.querySelector('.tp em'),cur=-1,tick=false;
  var art=document.querySelector('.art article');
  function offset(){return innerWidth<=900?150:130}
  function activate(i){
    if(i===cur)return;cur=i;
    items.forEach(function(it,k){it.li.classList.toggle('on',k===i);it.li.classList.toggle('done',k<i);if(k===i)it.a.setAttribute('aria-current','location');else it.a.removeAttribute('aria-current')});
    var a=items[i].a;
    if(innerWidth<=900){var ar=a.getBoundingClientRect(),lr=list.getBoundingClientRect();list.scrollTo({left:list.scrollLeft+(ar.left-lr.left)-(list.clientWidth-ar.width)/2,behavior:'smooth'})}
    else{var t=toc,r=a.getBoundingClientRect(),tr=t.getBoundingClientRect();if(r.top<tr.top+40||r.bottom>tr.bottom-60)t.scrollTo({top:a.offsetTop-t.clientHeight/2,behavior:'smooth'})}
  }
  function update(){
    tick=false;var o=offset(),idx=0;
    for(var k=0;k<items.length;k++){if(items[k].el.getBoundingClientRect().top<=o)idx=k}
    if(innerHeight+scrollY>=document.documentElement.scrollHeight-4)idx=items.length-1;
    activate(idx);
    if(art){var r=art.getBoundingClientRect(),tot=r.height-innerHeight*.6,p=Math.min(1,Math.max(0,(-r.top+innerHeight*.25)/Math.max(tot,1)));var v=Math.round(p*100);if(fill)fill.style.width=v+'%';if(pct)pct.textContent=v+'%'}
  }
  function req(){if(!tick){tick=true;requestAnimationFrame(update)}}
  addEventListener('scroll',req,{passive:true});addEventListener('resize',req);
  items.forEach(function(it,k){it.a.addEventListener('click',function(){activate(k)})});
  update();
})();
