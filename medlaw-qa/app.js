// medlaw-qa — deterministic retrieval responder (Architecture A, NO AI at runtime)
const $=s=>document.querySelector(s);
const scroll=$('#scroll'),col=$('#col'),ta=$('#ta'),send=$('#send'),empty=$('#empty');
const reduce=matchMedia('(prefers-reduced-motion:reduce)').matches;

// 機械鍵盤打字音效(Web Audio 合成,無外部檔、可離線;由使用者送出的手勢啟動)
let _actx=null, _lastTick=0, _noiseBuf=null, soundOn=false;   // 音效預設關閉(改 true 可重新啟用)
function _noise(ctx){
  if(_noiseBuf) return _noiseBuf;
  const len=Math.floor(ctx.sampleRate*0.05), b=ctx.createBuffer(1,len,ctx.sampleRate), d=b.getChannelData(0);
  for(let i=0;i<len;i++) d[i]=Math.random()*2-1;
  return (_noiseBuf=b);
}
function typeTick(){
  if(!soundOn) return;
  try{
    const AC=window.AudioContext||window.webkitAudioContext; if(!AC) return;
    if(!_actx) _actx=new AC();
    if(_actx.state==='suspended') _actx.resume();
    const now=performance.now(); if(now-_lastTick<55) return; _lastTick=now;
    const ctx=_actx, t=ctx.currentTime;
    // click:帶通濾波的白噪短爆點(軸的喀噠)
    const src=ctx.createBufferSource(); src.buffer=_noise(ctx);
    const bp=ctx.createBiquadFilter(); bp.type='bandpass'; bp.frequency.value=2200+Math.random()*800; bp.Q.value=0.7;
    const cg=ctx.createGain();
    cg.gain.setValueAtTime(0.0001,t);
    cg.gain.exponentialRampToValueAtTime(0.13,t+0.001);
    cg.gain.exponentialRampToValueAtTime(0.0001,t+0.035);
    src.connect(bp).connect(cg).connect(ctx.destination); src.start(t); src.stop(t+0.05);
    // thock:低頻鍵帽觸底的厚度
    const o=ctx.createOscillator(), tg=ctx.createGain();
    o.type='sine'; o.frequency.value=145+Math.random()*45;
    tg.gain.setValueAtTime(0.0001,t);
    tg.gain.exponentialRampToValueAtTime(0.06,t+0.002);
    tg.gain.exponentialRampToValueAtTime(0.0001,t+0.05);
    o.connect(tg).connect(ctx.destination); o.start(t); o.stop(t+0.06);
  }catch(e){}
}
const IDX=(window.SEARCH_INDEX||[]);
const STATS=(window.STATS||{});
SearchEngine.build(IDX);
const IDX_BY_ID=Object.create(null); IDX.forEach(r=>{IDX_BY_ID[r.i]=r;});
const _n=$('#corpusN'); if(_n) _n.textContent=(STATS.total||IDX.length).toLocaleString();

const EXAMPLES=[
  {q:"藥事法第83條有幾件判決？",h:"統計 · 轉讓禁藥"},
  {q:"醫師法第28條 密醫案",h:"檢索 · 無照行醫"},
  {q:"醫療法第82條 醫療過失",h:"檢索 · 民事賠償"},
  {q:"114年 臺中地方法院 藥事法",h:"篩選 · 年度＋法院"},
];
const exWrap=$('#examples');
EXAMPLES.forEach(e=>{const b=document.createElement('button');b.className='ex';b.type='button';
  b.innerHTML=`<div class="q"></div><div class="h"></div>`;
  b.querySelector('.q').textContent=e.q;b.querySelector('.h').textContent=e.h;
  b.onclick=()=>{ta.value=e.q;ask();};exWrap.appendChild(b);});

// ---------- search mode: fast (A index) vs deep (B1 full-text) ----------
let mode='fast', lastTerms=[];
(function initModes(){
  const box=document.getElementById('modes'); if(!box) return;
  if(!(window.FTS && FTS.available())){ box.style.display='none'; return; }  // no sql.js (e.g. artifact) -> A only
  box.querySelectorAll('.mode').forEach(btn=>btn.addEventListener('click',()=>{
    if(busy) return;
    mode=btn.dataset.mode;
    box.querySelectorAll('.mode').forEach(b=>b.classList.toggle('on', b===btn));
    ta.placeholder = mode==='deep'
      ? '全文深搜：輸入裁判書內文任意字詞，例如「甲基安非他命」'
      : '輸入問題，例如「藥事法第83條有幾件判決？」';
  }));
})();

// ---------- intent parsing -> structured filter + free text ----------
const LAWS=["藥事法","醫療器材管理法","醫療法","醫師法","藥師法"];
const KW=[  // topic keyword -> law/article, used as a filter
  {re:/密醫|無照|無醫師資格|冒充醫師/, law:"醫師法", art:"28", name:"密醫罪（醫師法§28）"},
  {re:/禁藥|毒品|轉讓|安非他命|大麻|愷他命/, law:"藥事法", art:"83", name:"轉讓／販賣禁藥（藥事法§83）"},
  {re:/未經核准輸入|代購|走私|國外購/, law:"藥事法", art:"22", name:"未經核准輸入（藥事法§22）"},
  {re:/妨害醫療|打醫|傷醫|恐嚇.*醫|暴力.*醫護|醫護人員/, law:"醫療法", art:"106", name:"妨害醫療業務（醫療法§106）"},
  {re:/醫療過失|醫糾|醫療糾紛|醫療損害|過失.*醫療/, law:"醫療法", art:"82", name:"醫療過失責任（醫療法§82）"},
  {re:/病歷/, law:"醫師法", art:"12", name:"病歷（醫師法§12）"},
  {re:/醫療器材|醫材/, law:"醫療器材管理法", art:null, name:"醫療器材管理法"},
  {re:/藥師|藥局|調劑/, law:"藥師法", art:null, name:"藥師法"},
];
const CATS=["刑事","民事","行政","懲戒","憲法法庭"];
function detectYear(q){const m=q.match(/(1[01][0-9])\s*年/);return m?parseInt(m[1],10):null;}
function detectCourt(q){const m=q.match(/([一-鿿]{2,5}(?:地方法院|高等法院|地院|高院|最高法院|最高行政法院|憲法法庭))/);
  return m?m[0].replace('地院','地方法院').replace('高院','高等法院'):null;}
function detectCategory(q){for(const c of CATS){if(q.includes(c))return c;}return null;}
function parseIntent(q){
  const filt={}; let label=null;
  for(const law of LAWS){
    if(q.includes(law)){
      filt.laws=[law];
      const m=q.match(/第?\s*(\d+)\s*(?:-|之)\s*(\d+)\s*條|第?\s*(\d+)\s*條/);
      if(m){const a=m[1]?(m[1]+'-'+m[2]):m[3]; filt.article={law,art:a}; label=`${law}§${a}`;}
      else label=law;
      break;
    }
  }
  if(!filt.article && !filt.laws){
    for(const k of KW){ if(k.re.test(q)){ if(k.art){filt.article={law:k.law,art:k.art};} else {filt.laws=[k.law];} label=k.name; break; } }
  }
  const cm=q.match(/違反(藥事法|醫療器材管理法|醫療法|醫師法|藥師法)/);  // 據該法起訴
  if(cm){ filt.causeLaw=cm[1]; if(!filt.laws) filt.laws=[cm[1]]; }
  const yr=detectYear(q); if(yr) filt.year=yr;
  const court=detectCourt(q); if(court) filt.court=court;
  const cat=detectCategory(q); if(cat) filt.category=cat;
  return {filt,label};
}
function query(q){
  const {filt,label}=parseIntent(q);
  let res=SearchEngine.search(q, filt, 8);
  if(res.total===0 && Object.keys(filt).length) res=SearchEngine.search('', filt, 8); // filters set but free-text matched nothing
  let statLabel=null, statCount=null;
  if(filt.article){
    const ac=STATS.article_counts&&STATS.article_counts[filt.article.law];
    statCount=(ac&&ac[filt.article.art]!=null)?ac[filt.article.art]:SearchEngine.count({article:filt.article});
    statLabel=`${filt.article.law}§${filt.article.art}`;
  }else if(filt.laws&&filt.laws.length===1){
    statCount=(STATS.per_law&&STATS.per_law[filt.laws[0]]!=null)?STATS.per_law[filt.laws[0]]:SearchEngine.count({laws:filt.laws});
    statLabel=filt.laws[0];
  }
  const fbits=[]; if(filt.causeLaw)fbits.push('據該法起訴'); if(filt.year)fbits.push(filt.year+'年'); if(filt.court)fbits.push(filt.court); if(filt.category)fbits.push(filt.category);
  return {q,filt,label,statLabel,statCount,total:res.total,hits:res.hits,fbits};
}
function answerText(r){
  if(r.deep && !r.freeText){
    return '全文深搜請輸入裁判書<b>內文關鍵字</b>（例如「甲基安非他命」「血氧」）；年度／法院／類別可一併加上作為篩選。';
  }
  if(r.total===0){
    return r.deep ? `在裁判書全文中找不到「${r.freeText}」${r.fbits.length?`（${r.fbits.join('、')}）`:''}。可換個詞或縮短關鍵字。`
                  : `找不到符合「${r.q.trim()}」的判決。可換個關鍵字，或用「法規＋條號」（例如「藥事法第83條」）、法院、年度來查。`;
  }
  let t;
  if(r.statLabel && r.statCount!=null){
    t=`關於<b>「${r.label||r.statLabel}」</b>，112–115 年間全庫共 <b>${r.statCount.toLocaleString()}</b> 件`+
      (r.fbits.length?`；在此條件（${r.fbits.join('、')}）下符合 <b>${r.total.toLocaleString()}</b> 件。`:`。`);
  }else if(r.deep){
    t=`在裁判書<b>全文</b>中找到與「${r.freeText}」相關的 <b>${r.total.toLocaleString()}</b> 件`+
      (r.fbits.length?`（${r.fbits.join('、')}）`:'')+
      `。<span class="muted-note">全文深搜涵蓋全部 14,031 筆判決全文</span>`;
  }else{
    t=`為你找到與「${r.q.trim()}」相關的 <b>${r.total.toLocaleString()}</b> 件判決。`;
  }
  t+=`以下列出前 ${r.hits.length} 件${r.deep?'（含全文命中片段，可載入更多）':'（依關聯度、新到舊排序）'}，可點開查核：`;
  return t;
}

// ---------- rendering ----------
function addUser(text){
  killEmpty();
  const m=document.createElement('div');m.className='msg user';
  m.innerHTML=`<div class="body"><div class="bubble"></div></div>`;
  m.querySelector('.bubble').textContent=text;col.appendChild(m);toBottom();
}
function addBot(){
  const m=document.createElement('div');m.className='msg bot';
  m.innerHTML=`<div class="body"><div class="bubble"><span class="txt"></span></div></div>`;
  col.appendChild(m);toBottom();return m;
}
function statLine(r){
  if(!(r.statLabel&&r.statCount!=null))return null;
  const w=document.createElement('div');w.className='statline';
  w.innerHTML=`<div class="stat"><div class="n">${r.statCount.toLocaleString()}</div><div class="l">${r.statLabel} · 全庫件數</div></div>
               <div class="stat"><div class="n">${r.total.toLocaleString()}</div><div class="l">符合此查詢</div></div>`;
  return w;
}
// 【】-marked snippet -> fragment with <mark>
function hlMarks(s){
  const frag=document.createDocumentFragment(), parts=String(s).split('【');
  parts.forEach((part,idx)=>{
    if(idx===0){frag.appendChild(document.createTextNode(part));return;}
    const j=part.indexOf('】');
    if(j<0){frag.appendChild(document.createTextNode(part));return;}
    const m=document.createElement('mark');m.textContent=part.slice(0,j);frag.appendChild(m);
    frag.appendChild(document.createTextNode(part.slice(j+1)));
  });
  return frag;
}
// highlight given substrings inside plain text -> fragment with <mark>
function hlTerms(text, terms){
  const frag=document.createDocumentFragment();
  if(!terms||!terms.length){frag.appendChild(document.createTextNode(text));return frag;}
  const re=new RegExp('('+terms.map(t=>t.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).join('|')+')','g');
  let last=0,m;
  while((m=re.exec(text))){
    if(m.index>last)frag.appendChild(document.createTextNode(text.slice(last,m.index)));
    const mk=document.createElement('mark');mk.textContent=m[0];frag.appendChild(mk);
    last=m.index+m[0].length; if(m.index===re.lastIndex)re.lastIndex++;
  }
  if(last<text.length)frag.appendChild(document.createTextNode(text.slice(last)));
  return frag;
}
// break a run-on judgment body into readable paragraphs (headings, 中華民國 signature, numbered items)
function paragraphs(text){
  const D='';
  const t=String(text)
    .replace(/(主\s*文)/g, D+'$1')
    .replace(/(犯\s*罪\s*事\s*實|事\s*實\s*及\s*理\s*由)/g, D+'$1')
    .replace(/(中\s*華\s*民\s*國)/g, D+'$1')
    .replace(/(附\s*錄|附\s*表)/g, D+'$1')
    .replace(/([一二三四五六七八九十]{1,3}、)/g, D+'$1')
    .replace(/([（(][一二三四五六七八九十0-9]{1,3}[）)])/g, D+'$1')
    .replace(/(\s\d{1,3}[、.．])/g, ' '+D+'$1');
  const parts=t.split(D).map(s=>s.trim()).filter(Boolean);
  return parts.length?parts:[String(text)];
}
function buildCard(r){
  const c=document.createElement('div');c.className='card';
  const tags=(r.l||[]).map(l=>`<span class="lt">${l}</span>`).join('');
  c.innerHTML=`<div class="top"><div class="tags">${tags}</div>
      <span class="num"></span><span class="meta">${r.d}</span></div>
      <div class="zhu"></div>${r.r?`<div class="res"></div>`:''}
      <button class="open" type="button">開啟裁判書</button>`;
  c.querySelector('.num').textContent=`${r.c} ${r.y}年${r.w}字第${r.n}號`;
  c.querySelector('.zhu').textContent=(r.u||'')+((r.a&&r.a.length)?('　'+r.a.join('、')):'');
  if(r.r)c.querySelector('.res').textContent='主文：'+r.r;
  if(r.snip){const sp=document.createElement('div');sp.className='snip';sp.appendChild(hlMarks(r.snip));
    c.insertBefore(sp, c.querySelector('.open'));}
  c.querySelector('button.open').addEventListener('click',()=>openPreview(r,c));
  return c;
}
// paginated source block with a 載入更多 button. onFirst() fires after page 1 revealed.
const PAGE=8, REVEAL_MS=420;
function buildSourceBlock(hits, onFirst){
  const wrap=document.createElement('div');
  const h=document.createElement('div');h.className='src-h';h.textContent='資料來源 · 司法院裁判書';wrap.appendChild(h);
  const cs=document.createElement('div');cs.className='cards';wrap.appendChild(cs);
  const more=document.createElement('button');more.className='more';more.type='button';more.style.display='none';wrap.appendChild(more);
  let shown=0;
  function updateMore(){const rem=hits.length-shown;
    if(rem>0){more.style.display='';more.textContent=`載入更多（還有 ${rem.toLocaleString()} 件）`;}else more.style.display='none';}
  // scrollMode: 'bottom' = follow to bottom (fresh answer) | 'follow' = gently keep each new card in view (load-more)
  function renderPage(done, scrollMode){
    const slice=hits.slice(shown,shown+PAGE);
    const els=slice.map(r=>{const el=buildCard(r);el.classList.add('reveal');cs.appendChild(el);return el;});
    shown+=slice.length;
    const finishPage=()=>{ updateMore(); done&&done(); };   // reveal 載入更多 only after the page's cards finish
    if(reduce){els.forEach(el=>el.classList.add('in'));finishPage();return;}
    let i=0;(function tick(){
      if(i<els.length){
        const el=els[i]; el.classList.add('in'); i++;
        if(scrollMode==='bottom') toBottom();
        else if(scrollMode==='follow') el.scrollIntoView({block:'nearest',behavior:'smooth'});
        setTimeout(tick,REVEAL_MS);
      } else finishPage();
    })();
  }
  more.addEventListener('click',()=>{ if(more.disabled)return; more.disabled=true; renderPage(()=>{more.disabled=false;}, 'follow'); });
  renderPage(onFirst, 'bottom');
  return wrap;
}
// B: narrowing chips (progressive filter) — appends a term to the query and re-asks
function narrowChips(r){
  if(r.total<=12) return null;
  const law=r.filt.laws&&r.filt.laws[0];
  const chips=[];
  if(!r.deep && law && law!=='藥師法' && !r.filt.causeLaw) chips.push({t:'只看據該法起訴', add:'違反'+law});
  if(!r.filt.year) [112,113,114,115].forEach(y=>chips.push({t:y+'年',add:y+'年'}));
  if(!r.filt.category) ['刑事','民事','行政'].forEach(c=>chips.push({t:c,add:c}));
  if(!chips.length) return null;
  const w=document.createElement('div');w.className='narrow';
  const lbl=document.createElement('span');lbl.className='nl';lbl.textContent='縮小範圍：';w.appendChild(lbl);
  chips.forEach(c=>{const b=document.createElement('button');b.className='nchip';b.type='button';b.textContent=c.t;
    b.addEventListener('click',()=>{ if(busy)return; ta.value=(r.q+' '+c.add).trim(); ask(); });
    w.appendChild(b);});
  return w;
}
function typeInto(el,html,done){
  if(reduce){el.innerHTML=html;done&&done();return;}
  // type plain text but allow simple <b>..</b>; we type on a temp text then set html at end
  const plain=html.replace(/<[^>]+>/g,'');
  let i=0;el.parentElement.classList.add('caret');
  const step=()=>{ i+=Math.max(1,Math.round(plain.length/110)); el.textContent=plain.slice(0,i); typeTick(); toBottom();
    if(i<plain.length){setTimeout(step,30);}else{el.innerHTML=html;el.parentElement.classList.remove('caret');done&&done();} };
  step();
}

// strip recognised filter tokens so only free text goes to the full-text engine
function deepFreeText(q){
  let s=' '+q+' ';
  LAWS.forEach(l=>{s=s.split('違反'+l).join(' ').split(l).join(' ');});
  s=s.replace(/第?\s*\d+\s*(?:-|之)?\s*\d*\s*條/g,' ');
  s=s.replace(/1[01][0-9]\s*年/g,' ');
  CATS.forEach(c=>{s=s.split(c).join(' ');});
  s=s.replace(/[一-鿿]{2,5}(?:地方法院|高等法院|地院|高院|最高法院|最高行政法院|憲法法庭)/g,' ');
  return s.replace(/\s+/g,' ').trim();
}
function passDeepFilter(r, filt){
  if(filt.laws&&filt.laws.length && !(r.l||[]).some(l=>filt.laws.indexOf(l)>=0)) return false;
  if(filt.year){ const ry=parseInt((r.d||'').slice(0,4),10)-1911; if(ry!==filt.year) return false; }
  if(filt.category && r.g!==filt.category) return false;
  if(filt.court && (r.c||'').indexOf(filt.court)<0) return false;
  return true;
}
function deepQuery(q){
  const {filt}=parseIntent(q);
  const ft=deepFreeText(q);
  const res=ft?FTS.search(ft):{total:0,hits:[],terms:[]};
  lastTerms=res.terms||[];
  let hits=res.hits.map(h=>Object.assign({}, IDX_BY_ID[h.i]||{i:h.i}, {snip:h.snip}));
  hits=hits.filter(r=>passDeepFilter(r,filt));
  const fbits=[]; if(filt.laws)fbits.push(filt.laws[0]); if(filt.year)fbits.push(filt.year+'年'); if(filt.court)fbits.push(filt.court); if(filt.category)fbits.push(filt.category);
  return {q, deep:true, freeText:ft, filt, label:null, statLabel:null, statCount:null, total:hits.length, hits, fbits};
}
// shared reveal of stat / narrow chips / paginated sources
function renderExtras(bot, r){
  const bodyEl=bot.querySelector('.body');
  const finish=()=>{busy=false;send.disabled=ta.value.trim()==='';toBottom();};
  const sl=statLine(r);
  if(sl){sl.classList.add('reveal');bodyEl.appendChild(sl);requestAnimationFrame(()=>sl.classList.add('in'));}
  if(!r.hits.length){finish();return;}
  const load=document.createElement('div');load.className='src-loading';
  load.innerHTML='<span class="dots"><i></i><i></i><i></i></span><span>檢索資料來源…</span>';
  bodyEl.appendChild(load);toBottom();
  setTimeout(()=>{
    load.remove();
    bodyEl.appendChild(buildSourceBlock(r.hits, ()=>{
      const nc=narrowChips(r);  // bottom: broaden(載入更多) vs narrow(縮小範圍) — both modes
      if(nc){nc.classList.add('reveal');bodyEl.appendChild(nc);requestAnimationFrame(()=>nc.classList.add('in'));}
      finish();
    }));
  }, reduce?0:(r.deep?400:1000));
}
// 「思考中」+ 可展開的「思考過程」(首次深搜載入全文時)
function makeThinking(bodyEl){
  const el=document.createElement('div');el.className='thinking';
  el.innerHTML=`<div class="th-head"><span class="dots"><i></i><i></i><i></i></span><span>思考中</span>`+
    `<button class="th-toggle" type="button" aria-label="思考過程">▾</button></div>`+
    `<div class="th-detail" hidden>`+
      `<div class="th-step" data-k="dl">⋯ 載入判決全文庫</div>`+
      `<div class="th-step" data-k="dz">⋯ 解壓縮</div>`+
      `<div class="th-step" data-k="ix">⋯ 建立全文檢索</div></div>`;
  const detail=el.querySelector('.th-detail'), toggle=el.querySelector('.th-toggle');
  toggle.addEventListener('click',()=>{const hid=detail.hasAttribute('hidden');
    if(hid)detail.removeAttribute('hidden');else detail.setAttribute('hidden','');
    toggle.textContent=(hid?'▴':'▾');});
  bodyEl.prepend(el); toBottom();
  const set=(k,t)=>{const s=el.querySelector('.th-step[data-k="'+k+'"]');if(s)s.textContent=t;};
  return {
    update(ev){
      if(ev.t==='dl') set('dl','⋯ 載入判決全文庫'+(ev.pct!=null?' …… '+ev.pct+'%':' ……'));
      else if(ev.t==='dl_done'){ set('dl','✓ 載入判決全文庫 …… 78MB'); set('dz','✓ 解壓縮'); }
      else if(ev.t==='idx') set('ix','⋯ 建立全文檢索');
      else if(ev.t==='idx_done') set('ix','✓ 建立全文檢索');
      toBottom();
    },
    remove(){ el.remove(); }
  };
}
let busy=false;
async function ask(){
  const q=ta.value.trim(); if(!q||busy)return;
  busy=true;send.disabled=true;
  addUser(q); ta.value='';autosize();
  const bot=addBot();const txt=bot.querySelector('.txt');
  let r;
  if(mode==='deep'){
    if(!FTS.ready()){
      const think=makeThinking(bot.querySelector('.body'));
      try{
        await FTS.load(ev=>think.update(ev));
        think.remove();
      }catch(e){
        think.remove();
        txt.innerHTML='全文深搜需以<b>本機伺服器</b>開啟:在<b>專案根目錄</b>執行 <code>python3 -m http.server</code>,再開 <b>http://localhost:8000/medlaw-qa/</b>(直接雙擊檔案無法載入資料庫)。';
        busy=false;send.disabled=ta.value.trim()==='';return;
      }
    }
    r=deepQuery(q);
    typeInto(txt,answerText(r),()=>renderExtras(bot,r));
  }else{
    r=query(q);
    setTimeout(()=>typeInto(txt,answerText(r),()=>renderExtras(bot,r)), reduce?0:260);
  }
}
function killEmpty(){if(empty&&empty.parentElement){empty.remove();}}
function toBottom(){scroll.scrollTop=scroll.scrollHeight;}
function autosize(){ta.style.height='auto';ta.style.height=Math.min(160,ta.scrollHeight)+'px';}

ta.addEventListener('input',()=>{autosize();send.disabled=ta.value.trim()===''||busy;});
ta.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing&&e.keyCode!==229){e.preventDefault();ask();}});
send.addEventListener('click',ask);
$('#clearbtn').onclick=()=>{ if(busy)return; col.innerHTML='';col.appendChild(empty);empty.style.display='';
  // rebuild examples listeners lost? empty node retained, its buttons intact
  toBottom(); };
$('#themebtn').onclick=()=>{const root=document.documentElement;
  const cur=root.getAttribute('data-theme')||'light';
  root.setAttribute('data-theme',cur==='dark'?'light':'dark');};

// ---------- right-side judgment preview drawer ----------
const preview=$('#preview'),scrim=$('#pv-scrim'),appEl=document.getElementById('app');
let activeCard=null;
function metaRow(dt,dd){
  const t=document.createElement('dt');t.textContent=dt;
  const d=document.createElement('dd');
  if(typeof dd==='string'){d.textContent=dd;}else{d.appendChild(dd);}
  return [t,d];
}
function openPreview(r,cardEl){
  $('#pv-title').textContent=`${r.c} ${r.y}年${r.w}字第${r.n}號`;
  const body=$('#pv-body');body.innerHTML='';
  const dl=document.createElement('dl');dl.className='pv-meta';
  const tags=document.createElement('div');tags.className='pv-tags';
  (r.l||[]).forEach(l=>{const s=document.createElement('span');s.className='lt';s.textContent=l;tags.appendChild(s);});
  const rows=[metaRow('裁判日期',r.d),metaRow('類別',r.g||'—'),metaRow('案由',r.u||'—'),metaRow('法規',tags)];
  if(r.a&&r.a.length) rows.push(metaRow('適用條號',r.a.join('、')));
  if(r.r) rows.push(metaRow('判決結果',r.r));
  if(r.b&&r.b.length) rows.push(metaRow('據該法起訴',r.b.join('、')));
  rows.forEach(([t,d])=>{dl.appendChild(t);dl.appendChild(d);});
  body.appendChild(dl);
  if(window.FTS && FTS.ready()){
    const sec=document.createElement('div');sec.className='pv-sec';sec.textContent='裁判書全文';body.appendChild(sec);
    const full=document.createElement('div');full.className='pv-full';
    const txt=FTS.getBody(r.i);
    if(txt){ paragraphs(txt).forEach(p=>{const el=document.createElement('p');el.className='pv-p';el.appendChild(hlTerms(p,lastTerms));full.appendChild(el);}); }
    else { full.textContent='（全文資料庫未收錄此筆）'; }
    body.appendChild(full);
    const fm=full.querySelector('mark');                       // auto-scroll to first hit
    if(fm) setTimeout(()=>fm.scrollIntoView({block:'center',behavior:'smooth'}), 90);
    else body.scrollTop=0;
  }else{
    const note=document.createElement('div');note.className='pv-note';
    note.textContent='整篇裁判書全文需切換到「全文深搜」載入全文資料庫後於此顯示；目前請點下方開啟司法院原文。';
    body.appendChild(note);
  }
  $('#pv-src').href=r.url;
  appEl.classList.add('drawer-open');
  preview.classList.add('open');scrim.classList.add('open');preview.setAttribute('aria-hidden','false');
  if(activeCard) activeCard.classList.remove('active');
  activeCard=cardEl||null;
  if(activeCard){ activeCard.classList.add('active'); activeCard.scrollIntoView({block:'nearest'}); }
}
function closePreview(){
  appEl.classList.remove('drawer-open');
  preview.classList.remove('open');scrim.classList.remove('open');preview.setAttribute('aria-hidden','true');
  if(activeCard){ activeCard.classList.remove('active'); activeCard=null; }
}
$('#pv-close').addEventListener('click',closePreview);
scrim.addEventListener('click',closePreview);
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&preview.classList.contains('open'))closePreview();});
autosize();
