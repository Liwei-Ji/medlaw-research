#!/usr/bin/env python3
# Download every judgment's full text (data.aspx) and parse structured fields. Resumable, concurrent.
import urllib.request, urllib.parse, http.cookiejar, re, time, json, sys, threading, html as H
from concurrent.futures import ThreadPoolExecutor
BASE="https://judgment.judicial.gov.tw/FJUD/"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
INDEX="醫藥五法_全文總索引_112-115.json"
OUT="fulltext.jsonl"
WORKERS=6
LAW_NAMES=["藥事法","醫療器材管理法","醫療法","醫師法","藥師法"]
_tls=threading.local()
def opener():
    op=getattr(_tls,"op",None)
    if op is None:
        cj=http.cookiejar.CookieJar();op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        try:op.open(urllib.request.Request(BASE+"Default_AD.aspx",headers={"User-Agent":UA}),timeout=40).read()
        except Exception:pass
        _tls.op=op
    return op
def fetch(url,tries=4):
    for t in range(tries):
        try:return opener().open(urllib.request.Request(url,headers={"User-Agent":UA,"Referer":BASE,"Accept-Language":"zh-TW"}),timeout=60).read().decode('utf-8','replace')
        except Exception:
            if t==tries-1:raise
            time.sleep(1.5+1.5*t)
def jud_block(h):
    i=h.find('id="jud"')
    if i<0:return ""
    start=h.find('>',i)+1
    ends=[p for p in (h.find('id="JudHis"'),h.find('id="JudrelaLaw"'),h.find('id="JudRelaMoj"'),h.find('id="HisMemo"')) if p!=-1]
    end=min(ends) if ends else len(h)
    end=h.rfind('<div',start,end)  # back up to the panel's own opening div
    if end<=start:end=len(h)
    return h[start:end]
def clean(x):return re.sub(r'[ \t　]+',' ',H.unescape(re.sub(r'<[^>]+>','',x or ''))).strip()
LAW_ART=re.compile(r'(藥事法|醫療器材管理法|醫療法|醫師法|藥師法|刑法|全民健康保險法|食品安全衛生管理法|專利法)(?:第[一二三四五六七八九十百]*[0-9]*條(?:之[0-9一二三四五六七八九十]+)?(?:第[0-9一二三四五六七八九十]+項)?(?:第[0-9一二三四五六七八九十]+款)?)')
ART_ONLY=re.compile(r'第([0-9一二三四五六七八九十百]+)條(?:之([0-9一二三四五六七八九十]+))?')
def cn2int(s):
    if s.isdigit():return int(s)
    m={'零':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
    if s=='十':return 10
    if '十' in s:
        a,_,b=s.partition('十');return (m.get(a,1) if a else 1)*10+(m.get(b,0) if b else 0)
    return sum(m.get(c,0) for c in s)
def parse_articles(text,laws):
    # return dict law -> sorted list of article numbers cited
    out={}
    for m in re.finditer(r'(藥事法|醫療器材管理法|醫療法|醫師法|藥師法)第([0-9一二三四五六七八九十百]+)條(?:之([0-9一二三四五六七八九十]+))?',text):
        law=m.group(1);art=str(cn2int(m.group(2)))+("-"+str(cn2int(m.group(3))) if m.group(3) else "")
        out.setdefault(law,set()).add(art)
    return {k:sorted(v,key=lambda a:[int(x) for x in a.split('-')]) for k,v in out.items()}
HEAD_ZHU=re.compile(r'主\s*文')
HEAD_END=re.compile(r'事\s*實|理\s*由|犯\s*罪\s*事\s*實|事實及理由')
def extract_zhuwen(text):
    m=HEAD_ZHU.search(text)
    if not m:return ""
    start=m.end()
    e=HEAD_END.search(text,start)
    end=e.start() if e else min(len(text),start+2000)
    return text[start:end].strip()
def parse_penalty(zhuwen):
    d={}
    # 刑度 durations
    terms=[]
    for m in re.finditer(r'有期徒刑\s*([一二三四五六七八九十百零]+)年?(?:([一二三四五六七八九十百零]+)月)?(?:又)?(?:([一二三四五六七八九十百零]+)日)?',zhuwen):
        y=cn2int(m.group(1)) if m.group(1) else 0
        mo=cn2int(m.group(2)) if m.group(2) else 0
        terms.append({"年":y,"月":mo})
    if terms:d["有期徒刑"]=terms
    for m in re.finditer(r'拘役\s*([一二三四五六七八九十百零]+)日',zhuwen):
        d.setdefault("拘役日",[]).append(cn2int(m.group(1)))
    if '有期徒刑' in zhuwen and "有期徒刑" not in d:d["有期徒刑"]=True
    if '拘役' in zhuwen and "拘役日" not in d:d["拘役"]=True
    if '無期徒刑' in zhuwen:d["無期徒刑"]=True
    if '死刑' in zhuwen:d["死刑"]=True
    if '得易科罰金' in zhuwen or '易科罰金' in zhuwen:d["得易科罰金"]=True
    mm=re.search(r'緩刑([一二三四五六七八九十]+)年',zhuwen)
    if mm:d["緩刑年"]=cn2int(mm.group(1))
    if '無罪' in zhuwen:d["無罪"]=True
    if '免訴' in zhuwen:d["免訴"]=True
    if '公訴不受理' in zhuwen:d["不受理"]=True
    if '駁回' in zhuwen:d["駁回"]=True
    # 罰金/罰鍰 amounts (阿拉伯數字)
    fines=re.findall(r'罰金(?:新臺幣)?\s*([0-9,]{2,})\s*元',zhuwen)
    if fines:d["罰金額"]=[int(x.replace(',','')) for x in fines]
    fh=re.findall(r'罰鍰(?:新臺幣)?\s*([0-9,]{2,})\s*元',zhuwen)
    if fh:d["罰鍰額"]=[int(x.replace(',','')) for x in fh]
    conf=re.findall(r'沒收[^。]{0,40}?([0-9,]{3,})\s*元',zhuwen)
    if conf:d["沒收金額"]=[int(x.replace(',','')) for x in conf]
    elif '沒收' in zhuwen:d["沒收"]=True
    return d
def parse(rec,html):
    raw=H.unescape(jud_block(html))   # tags kept -> reliable name boundaries at '<'
    jt=clean(raw)
    # strip leading metadata labels
    body=jt
    for lbl in ["裁判字號：","裁判日期：","裁判案由："]:
        pass
    zhuwen=extract_zhuwen(jt)
    TERM=r'(?=以上|中\s*華\s*民\s*國|書\s*記\s*官|法\s*官|審判長|附表|上訴|抗告|如不服|\s|，|。|$)'
    JUNK={"釋字","大法","本院","獨任","受命","陪席","審判","起訴","上訴","到庭","提起","實行","移送","聲請","偵查","亦未","起訴書","上訴者","被告","如不","獨任逕","逕以","法官"}
    # judges/clerk from RAW block: name ends at next tag '<' (reliable), tolerate full-width spaces
    ENDN=r'(?:以上|附錄|附表|中\s*華|書\s*記|法\s*官|審判長|<)'
    SP=r'[\s　 ]*'  # ascii / ideographic / no-break spaces
    def destrip(x):return re.sub(r'[\s　 ]','',x)
    # method A: name (possibly char-spaced) in plain text after 法官 label
    jA=[destrip(j) for j in re.findall(r'法\s*官'+SP+r'((?:[一-鿿]'+SP+r'){2,4}?)'+ENDN,raw)]
    jA=[j for j in jA if j not in JUNK]
    # method B: name wrapped in <span class="jud_authCopy"> (tags between label and name)
    jB=[destrip(s) for s in re.findall(r'jud_authCopy"?[^>]*>([^<]+)</span>',raw)]
    jB=[s for s in jB if re.fullmatch(r'[一-鿿]{2,4}',s) and s not in JUNK]
    cm=re.search(r'書\s*記\s*官'+SP+r'((?:[一-鿿]'+SP+r'){2,4}?)'+r'(?:以上|附|中\s*華|<)',raw)
    if not cm:
        cm=re.search(r'書\s*記\s*官(?:(?!書\s*記|法\s*官).)*?jud_authCopy"?[^>]*>([一-鿿]{2,4})</span>',raw,re.S)
    clerk_name=destrip(cm.group(1)) if cm else ""
    judges=[j for j in dict.fromkeys(jA+jB) if j!=clerk_name]
    # 檢察官: high-precision — name must be immediately followed by an action verb
    pros=[p for p in re.findall(r'檢察官[\s　]*([一-鿿]{2,3})(?=提起公訴|聲請以簡易判決|實行公訴|到庭|移送|偵查終結|於本院|於原審)',jt) if p not in JUNK]
    return {
        "id":rec["id"],"laws":rec["laws"],"category":rec.get("category"),
        "court":rec["court"],"case_year":rec["case_year"],"word":rec["word"],"case_no":rec["case_no"],
        "doctype":rec["doctype"],"jdate":rec["jdate"],"cause":rec["cause"],"url":rec["url"],
        "適用條號":parse_articles(jt,rec["laws"]),
        "主文":zhuwen[:1500],
        "判決結果":parse_penalty(zhuwen if zhuwen else jt[:2000]),
        "承審法官":judges,
        "書記官":clerk_name,
        "檢察官":list(dict.fromkeys(pros)),
        "全文":jt,"全文長度":len(jt),
    }
_lock=threading.Lock()
_done=set()
def work(rec):
    try:
        h=fetch(rec["url"])
        obj=parse(rec,h)
        line=json.dumps(obj,ensure_ascii=False)
        with _lock:
            with open(OUT,"a",encoding="utf-8") as f:f.write(line+"\n")
        time.sleep(0.15)
        return True
    except Exception as e:
        with _lock:
            with open("download_errors.log","a",encoding="utf-8") as f:f.write(rec["id"]+"\t"+repr(e)[:120]+"\n")
        return False
if __name__=="__main__":
    recs=json.load(open(INDEX,encoding="utf-8"))["records"]
    limit=int(sys.argv[1]) if len(sys.argv)>1 else 0
    import os
    if os.path.exists(OUT):
        for ln in open(OUT,encoding="utf-8"):
            try:_done.add(json.loads(ln)["id"])
            except Exception:pass
    todo=[r for r in recs if r["id"] not in _done]
    if limit:todo=todo[:limit]
    print(f"total={len(recs)} done={len(_done)} todo={len(todo)} workers={WORKERS}",flush=True)
    n=0;t0=time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for ok in ex.map(work,todo):
            n+=1
            if n%200==0:
                el=time.time()-t0;print(f"  {n}/{len(todo)} rate={n/el:.1f}/s eta={ (len(todo)-n)/(n/el)/60:.1f}min",flush=True)
    print("DOWNLOAD DONE processed=",n,flush=True)
