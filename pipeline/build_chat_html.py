# -*- coding: utf-8 -*-
import json
demo=json.load(open("demo_data.json",encoding="utf-8"))
DEMO=json.dumps(demo,ensure_ascii=False)

HTML=r'''<div id="app" class="chat-root">
<style>
  .chat-root{
    --page:#f7f7f8; --surface:#ffffff; --surface-2:#f4f5f7; --bubble-user:#eef4fb;
    --ink:#1f2329; --ink-2:#4c525c; --muted:#8a909b; --hair:#e7e8ec; --hair-2:#eceef1;
    --accent:#2a6fd6; --accent-ink:#1c5cab; --ring:rgba(31,35,41,.10);
    --tag:#eaf1fb; --tag-ink:#1c5cab;
    --shadow:0 1px 2px rgba(16,19,25,.05); --shadow-lg:0 12px 40px rgba(16,19,25,.10);
    color-scheme:light;
  }
  @media (prefers-color-scheme:dark){ .chat-root{
    --page:#0f1012; --surface:#1a1c1f; --surface-2:#212327; --bubble-user:#243244;
    --ink:#ececed; --ink-2:#b6bbc4; --muted:#868c96; --hair:#2a2c31; --hair-2:#26282c;
    --accent:#4a92e8; --accent-ink:#7fb0ee; --ring:rgba(255,255,255,.12);
    --tag:#1b2735; --tag-ink:#8fbdf2;
    --shadow:0 1px 2px rgba(0,0,0,.4); --shadow-lg:0 16px 46px rgba(0,0,0,.5);
    color-scheme:dark;
  }}
  :root[data-theme="light"] .chat-root{--page:#f7f7f8;--surface:#ffffff;--surface-2:#f4f5f7;--bubble-user:#eef4fb;--ink:#1f2329;--ink-2:#4c525c;--muted:#8a909b;--hair:#e7e8ec;--hair-2:#eceef1;--accent:#2a6fd6;--accent-ink:#1c5cab;--ring:rgba(31,35,41,.10);--tag:#eaf1fb;--tag-ink:#1c5cab;color-scheme:light;}
  :root[data-theme="dark"] .chat-root{--page:#0f1012;--surface:#1a1c1f;--surface-2:#212327;--bubble-user:#243244;--ink:#ececed;--ink-2:#b6bbc4;--muted:#868c96;--hair:#2a2c31;--hair-2:#26282c;--accent:#4a92e8;--accent-ink:#7fb0ee;--ring:rgba(255,255,255,.12);--tag:#1b2735;--tag-ink:#8fbdf2;color-scheme:dark;}

  .chat-root *{box-sizing:border-box}
  .chat-root{font-family:system-ui,-apple-system,"Segoe UI","Noto Sans TC",sans-serif;background:var(--page);color:var(--ink);
    height:100vh;display:flex;flex-direction:column;-webkit-font-smoothing:antialiased;line-height:1.6}
  /* header */
  .hd{flex:none;display:flex;align-items:center;justify-content:space-between;gap:12px;
    padding:11px clamp(14px,4vw,26px);border-bottom:1px solid var(--hair);background:var(--surface)}
  .hd .brand{display:flex;align-items:center;gap:10px;min-width:0}
  .mark{width:30px;height:30px;border-radius:8px;flex:none;background:linear-gradient(150deg,var(--accent),var(--accent-ink));
    color:#fff;display:grid;place-items:center;font-weight:800;font-size:15px;box-shadow:var(--shadow)}
  .brand .t{font-weight:700;font-size:15px;letter-spacing:-.01em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .brand .s{font-size:11.5px;color:var(--muted);white-space:nowrap}
  .pill{font-size:10.5px;font-weight:700;letter-spacing:.04em;color:var(--tag-ink);background:var(--tag);
    padding:3px 8px;border-radius:999px;white-space:nowrap}
  .hbtn{border:1px solid var(--hair);background:var(--surface);color:var(--ink-2);border-radius:8px;padding:7px 10px;
    font-size:12px;font-weight:600;cursor:pointer}
  .hbtn:hover{border-color:var(--ring)}
  .hd .right{display:flex;align-items:center;gap:8px}
  @media(max-width:560px){.brand .s{display:none}.pill{display:none}}

  /* scroll area */
  .scroll{flex:1;overflow-y:auto;scroll-behavior:smooth}
  .col{max-width:760px;margin:0 auto;padding:26px clamp(14px,4vw,22px) 12px}

  /* empty state */
  .empty{min-height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;
    padding:6vh 0 4vh;gap:6px}
  .empty .bigmark{width:52px;height:52px;border-radius:14px;background:linear-gradient(150deg,var(--accent),var(--accent-ink));
    color:#fff;display:grid;place-items:center;font-weight:800;font-size:24px;box-shadow:var(--shadow-lg);margin-bottom:10px}
  .empty h1{font-size:clamp(20px,3vw,26px);font-weight:750;letter-spacing:-.015em;margin:0}
  .empty p{color:var(--ink-2);font-size:14px;max-width:46ch;margin:2px 0 0}
  .examples{display:grid;grid-template-columns:1fr 1fr;gap:10px;width:100%;max-width:560px;margin-top:22px}
  @media(max-width:520px){.examples{grid-template-columns:1fr}}
  .ex{text-align:left;border:1px solid var(--hair);background:var(--surface);border-radius:12px;padding:12px 14px;
    cursor:pointer;transition:border-color .12s,transform .06s;box-shadow:var(--shadow)}
  .ex:hover{border-color:var(--accent);transform:translateY(-1px)}
  .ex .q{font-size:13.5px;font-weight:600;color:var(--ink)}
  .ex .h{font-size:11.5px;color:var(--muted);margin-top:3px}

  /* messages */
  .msg{display:flex;gap:12px;margin:20px 0;align-items:flex-start}
  .msg.user{flex-direction:row-reverse}
  .av{width:30px;height:30px;border-radius:8px;flex:none;display:grid;place-items:center;font-weight:700;font-size:13px}
  .av.bot{background:linear-gradient(150deg,var(--accent),var(--accent-ink));color:#fff}
  .av.me{background:var(--surface-2);color:var(--ink-2);border:1px solid var(--hair)}
  .body{min-width:0;max-width:calc(100% - 44px)}
  .msg.user .body{display:flex;justify-content:flex-end}
  .bubble{border-radius:14px;padding:11px 15px;font-size:14.5px}
  .msg.user .bubble{background:var(--bubble-user);color:var(--ink);border-top-right-radius:5px;max-width:100%}
  .msg.bot .bubble{background:transparent;padding-left:0;padding-top:3px}
  .bubble p{margin:0 0 8px}.bubble p:last-child{margin-bottom:0}
  .bubble b{font-weight:700}
  .caret::after{content:'▍';color:var(--accent);animation:blink 1s steps(1) infinite}
  @keyframes blink{50%{opacity:0}}

  /* stat chip inside answer */
  .statline{display:flex;flex-wrap:wrap;gap:8px;margin:4px 0 10px}
  .stat{background:var(--surface-2);border:1px solid var(--hair);border-radius:10px;padding:8px 12px}
  .stat .n{font-size:19px;font-weight:770;font-variant-numeric:tabular-nums;color:var(--accent-ink)}
  .stat .l{font-size:11px;color:var(--muted);margin-top:1px}

  /* source cards */
  .src-h{font-size:11.5px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:12px 0 8px}
  .cards{display:flex;flex-direction:column;gap:8px}
  .card{border:1px solid var(--hair);background:var(--surface);border-radius:12px;padding:11px 13px;
    box-shadow:var(--shadow);transition:border-color .12s}
  .card:hover{border-color:var(--ring)}
  .card .top{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:4px}
  .tags{display:flex;gap:5px;flex-wrap:wrap}
  .lt{font-size:10.5px;font-weight:700;color:var(--tag-ink);background:var(--tag);padding:2px 7px;border-radius:999px}
  .card .num{font-size:13.5px;font-weight:680;color:var(--ink)}
  .card .meta{font-size:12px;color:var(--muted);margin-left:auto;font-variant-numeric:tabular-nums;white-space:nowrap}
  .card .zhu{font-size:12.5px;color:var(--ink-2);margin:2px 0 8px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
  .card .res{font-size:12px;color:var(--accent-ink);font-weight:600;margin-bottom:8px}
  .card a.open{display:inline-flex;align-items:center;gap:5px;font-size:12.5px;font-weight:650;color:var(--accent);
    text-decoration:none;border:1px solid var(--hair);border-radius:8px;padding:5px 10px}
  .card a.open:hover{border-color:var(--accent);background:var(--tag)}

  /* input dock */
  .dock{flex:none;background:linear-gradient(to top,var(--page) 70%,transparent);padding:6px clamp(14px,4vw,22px) 12px}
  .dockcol{max-width:760px;margin:0 auto}
  .inbox{display:flex;align-items:flex-end;gap:8px;background:var(--surface);border:1px solid var(--hair);
    border-radius:16px;padding:8px 8px 8px 16px;box-shadow:var(--shadow-lg)}
  .inbox:focus-within{border-color:var(--accent)}
  textarea{flex:1;border:0;outline:0;resize:none;background:transparent;color:var(--ink);font:inherit;font-size:15px;
    line-height:1.5;max-height:160px;padding:6px 0}
  textarea::placeholder{color:var(--muted)}
  .send{flex:none;width:36px;height:36px;border-radius:11px;border:0;background:var(--accent);color:#fff;cursor:pointer;
    display:grid;place-items:center;transition:opacity .12s,background .12s}
  .send:disabled{opacity:.4;cursor:default}
  .send:not(:disabled):hover{background:var(--accent-ink)}
  .disc{text-align:center;font-size:11px;color:var(--muted);margin-top:8px}
  .disc b{color:var(--ink-2);font-weight:650}
  @media (prefers-reduced-motion:reduce){.caret::after{animation:none}.ex:hover{transform:none}}
</style>

<header class="hd">
  <div class="brand">
    <div class="mark">醫</div>
    <div style="min-width:0">
      <div class="t">醫藥法規判決問答</div>
      <div class="s">司法院裁判書 · 藥事法・醫材法・醫療法・醫師法・藥師法 · 112–115 年</div>
    </div>
  </div>
  <div class="right">
    <span class="pill" id="pill">介面原型</span>
    <button class="hbtn" id="clearbtn" type="button">清除</button>
    <button class="hbtn" id="themebtn" type="button">◐</button>
  </div>
</header>

<main class="scroll" id="scroll">
  <div class="col" id="col">
    <div class="empty" id="empty">
      <div class="bigmark">醫</div>
      <h1>醫藥五法判決檢索問答</h1>
      <p>詢問條號、法院、年度或關鍵字，回覆相關判決並附上司法院裁判書連結。此為介面原型，示範資料 <b id="demoN">—</b> 筆。</p>
      <div class="examples" id="examples"></div>
    </div>
  </div>
</main>

<div class="dock">
  <div class="dockcol">
    <div class="inbox">
      <textarea id="ta" rows="1" placeholder="輸入問題，例如「藥事法第83條有幾件判決？」" aria-label="輸入問題"></textarea>
      <button class="send" id="send" type="button" disabled aria-label="送出">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
      </button>
    </div>
    <div class="disc">檢索式問答 · 答案來自司法院裁判書 · <b>不呼叫 AI</b>，可離線</div>
  </div>
</div>

<script>
const DEMO=__DEMO__;
const $=s=>document.querySelector(s);
const scroll=$('#scroll'),col=$('#col'),ta=$('#ta'),send=$('#send'),empty=$('#empty');
const reduce=matchMedia('(prefers-reduced-motion:reduce)').matches;
$('#demoN').textContent=DEMO.records.length;

const EXAMPLES=[
  {q:"藥事法第83條有幾件判決？",h:"統計 · 轉讓禁藥"},
  {q:"醫師法第28條 密醫罪的案例",h:"檢索 · 無照行醫"},
  {q:"醫療法第82條 醫療過失",h:"檢索 · 民事賠償"},
  {q:"妨害醫療業務 打醫護人員",h:"關鍵字 · 醫療法106"},
];
const exWrap=$('#examples');
EXAMPLES.forEach(e=>{const b=document.createElement('button');b.className='ex';b.type='button';
  b.innerHTML=`<div class="q"></div><div class="h"></div>`;
  b.querySelector('.q').textContent=e.q;b.querySelector('.h').textContent=e.h;
  b.onclick=()=>{ta.value=e.q;ask();};exWrap.appendChild(b);});

// ---------- deterministic demo responder (NO AI) ----------
const LAWS=["藥事法","醫療器材管理法","醫療法","醫師法","藥師法"];
const KW=[
  {re:/密醫|無照|無醫師資格|冒充醫師/, law:"醫師法", art:"28", name:"密醫罪（醫師法§28）"},
  {re:/禁藥|毒品|轉讓|安非他命|大麻|愷他命/, law:"藥事法", art:"83", name:"轉讓／販賣禁藥（藥事法§83）"},
  {re:/未經核准輸入|代購|走私|國外購/, law:"藥事法", art:"22", name:"未經核准輸入禁藥（藥事法§22）"},
  {re:/妨害醫療|打醫|傷醫|恐嚇.*醫|暴力.*醫護|醫護人員/, law:"醫療法", art:"106", name:"妨害醫療業務（醫療法§106）"},
  {re:/醫療過失|醫糾|醫療糾紛|醫療損害|過失.*醫療/, law:"醫療法", art:"82", name:"醫療過失責任（醫療法§82）"},
  {re:/病歷/, law:"醫師法", art:"12", name:"病歷製作（醫師法§12）"},
  {re:/醫療器材|醫材/, law:"醫療器材管理法", art:"62", name:"醫療器材管理法§62"},
  {re:/藥師|藥局|調劑/, law:"藥師法", art:null, name:"藥師法"},
];
function detectArticle(q){
  // explicit 法名 + 條號
  for(const law of LAWS){
    if(q.includes(law)){
      const m=q.match(/第?\s*(\d+)\s*(?:-|之)?\s*(\d+)?\s*條/);
      if(m){const art=m[1]+(m[2]?("-"+m[2]):"");return {law,art,name:`${law}§${art}`};}
    }
  }
  for(const k of KW){if(k.re.test(q))return {law:k.law,art:k.art,name:k.name};}
  return null;
}
function detectYear(q){const m=q.match(/(11[0-9])\s*年/);return m?m[1]:null;}
function detectCourt(q){const m=q.match(/([一-鿿]{2,4}(?:地方法院|高等法院|地院|高院))/);return m?m[1]:null;}
function recHasArt(r,law,art){const a=(r.arts||{})[law];return a&&(art?a.includes(art):true);}

function query(q){
  const hit=detectArticle(q), yr=detectYear(q), court=detectCourt(q);
  let pool=DEMO.records.slice();
  let intro="";
  if(hit){
    let cnt=null; if(hit.art&&DEMO.stats[hit.law]&&DEMO.stats[hit.law][hit.art]!=null)cnt=DEMO.stats[hit.law][hit.art];
    pool=pool.filter(r=>recHasArt(r,hit.law,hit.art));
    intro=`關於<b>「${hit.name}」</b>，112–115 年間`+(cnt!=null?`全庫共 <b>${cnt.toLocaleString()}</b> 件（依全文檢索）。`:`為你檢索到相關判決。`);
  }else{
    const kw=q.replace(/[？?。，,\s的有幾件是嗎請問給我列出關於]/g,"");
    if(kw)pool=pool.filter(r=>(r.cause+r.zhu+r.court+(r.laws||[]).join("")).includes(kw));
    intro=pool.length?`為你找到與「${q.trim()}」相關的判決。`:"";
  }
  if(yr)pool=pool.filter(r=>r.date.startsWith(String(1911+parseInt(yr))));
  if(court)pool=pool.filter(r=>r.court.includes(court.replace("地院","地方法院").replace("高院","高等法院")));
  return {hit,cnt:(hit&&hit.art&&DEMO.stats[hit.law])?DEMO.stats[hit.law][hit.art]:null,intro,pool:pool.slice(0,6),yr,court};
}
function answerText(r){
  if(r.pool.length===0 && !r.hit){
    return "此為介面原型，示範資料（"+DEMO.records.length+" 筆）尚未涵蓋這個問題。<br>正式版會檢索全部 <b>14,031</b> 筆判決，回覆符合條件者並附上每一筆的裁判書連結。";
  }
  let t=r.intro;
  if(r.pool.length){t+=`以下列出 ${r.pool.length} 件代表案例，可點開原始裁判書查核：`;}
  else{t+="示範資料中沒有完全符合的案例；正式版將涵蓋全部 14,031 筆。";}
  return t;
}

// ---------- rendering ----------
function addUser(text){
  killEmpty();
  const m=document.createElement('div');m.className='msg user';
  m.innerHTML=`<div class="av me">你</div><div class="body"><div class="bubble"></div></div>`;
  m.querySelector('.bubble').textContent=text;col.appendChild(m);toBottom();
}
function addBot(){
  const m=document.createElement('div');m.className='msg bot';
  m.innerHTML=`<div class="av bot">醫</div><div class="body"><div class="bubble"><span class="txt"></span></div></div>`;
  col.appendChild(m);toBottom();return m;
}
function statLine(r){
  if(!(r.hit&&r.cnt!=null))return null;
  const w=document.createElement('div');w.className='statline';
  w.innerHTML=`<div class="stat"><div class="n">${r.cnt.toLocaleString()}</div><div class="l">${r.hit.name} · 全庫件數</div></div>
               <div class="stat"><div class="n">${r.pool.length}</div><div class="l">本頁代表案例</div></div>`;
  return w;
}
function cards(pool){
  if(!pool.length)return null;
  const wrap=document.createElement('div');
  const h=document.createElement('div');h.className='src-h';h.textContent='資料來源 · 司法院裁判書';wrap.appendChild(h);
  const cs=document.createElement('div');cs.className='cards';
  pool.forEach(r=>{
    const c=document.createElement('div');c.className='card';
    const tags=(r.laws||[]).map(l=>`<span class="lt">${l}</span>`).join('');
    c.innerHTML=`<div class="top"><div class="tags">${tags}</div>
        <span class="num"></span><span class="meta">${r.date}</span></div>
        <div class="zhu"></div>${r.res?`<div class="res"></div>`:''}
        <a class="open" target="_blank" rel="noopener">開啟裁判書 ↗</a>`;
    c.querySelector('.num').textContent=`${r.court} ${r.y}年${r.w}字第${r.no}號`;
    c.querySelector('.zhu').textContent=r.zhu||r.cause;
    if(r.res)c.querySelector('.res').textContent='主文：'+r.res;
    c.querySelector('a.open').href=r.url;
    cs.appendChild(c);
  });
  wrap.appendChild(cs);return wrap;
}
function typeInto(el,html,done){
  if(reduce){el.innerHTML=html;done&&done();return;}
  // type plain text but allow simple <b>..</b>; we type on a temp text then set html at end
  const plain=html.replace(/<[^>]+>/g,'');
  let i=0;el.parentElement.classList.add('caret');
  const step=()=>{ i+=Math.max(1,Math.round(plain.length/60)); el.textContent=plain.slice(0,i); toBottom();
    if(i<plain.length){setTimeout(step,14);}else{el.innerHTML=html;el.parentElement.classList.remove('caret');done&&done();} };
  step();
}

let busy=false;
function ask(){
  const q=ta.value.trim(); if(!q||busy)return;
  busy=true;send.disabled=true;
  addUser(q); ta.value='';autosize();
  const r=query(q);
  setTimeout(()=>{
    const bot=addBot();const txt=bot.querySelector('.txt');
    typeInto(txt,answerText(r),()=>{
      const sl=statLine(r);if(sl)bot.querySelector('.body').appendChild(sl);
      const cd=cards(r.pool);if(cd)bot.querySelector('.body').appendChild(cd);
      toBottom();busy=false;send.disabled=ta.value.trim()==='';
    });
  }, reduce?0:260);
}
function killEmpty(){if(empty&&empty.parentElement){empty.remove();}}
function toBottom(){scroll.scrollTop=scroll.scrollHeight;}
function autosize(){ta.style.height='auto';ta.style.height=Math.min(160,ta.scrollHeight)+'px';}

ta.addEventListener('input',()=>{autosize();send.disabled=ta.value.trim()===''||busy;});
ta.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();ask();}});
send.addEventListener('click',ask);
$('#clearbtn').onclick=()=>{ if(busy)return; col.innerHTML='';col.appendChild(empty);empty.style.display='';
  // rebuild examples listeners lost? empty node retained, its buttons intact
  toBottom(); };
$('#themebtn').onclick=()=>{const root=document.documentElement;
  const cur=root.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');
  root.setAttribute('data-theme',cur==='dark'?'light':'dark');};
autosize();
</script>
</div>'''
HTML=HTML.replace("__DEMO__",DEMO)
open("/Users/akousist_xml7h/醫藥法規判決研究/判決問答_對話框.html","w",encoding="utf-8").write(HTML)
print("wrote chat html, demo records",len(demo["records"]))
