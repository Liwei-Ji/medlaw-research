#!/usr/bin/env python3
import json, csv, collections, re, config
BASE=config.STRUCTURED[:-5]   # data/醫藥五法_結構化_<suffix>
with config.open_jsonl(config.FULLTEXT_JSONL) as _f:
    rows=[json.loads(l) for l in _f]
rows.sort(key=lambda r:(r.get("jdate",""),r.get("id","")),reverse=True)
print("loaded",len(rows))

# ---- improved re-parse of 主文 / 判決結果 from stored 全文 (no re-download) ----
_CN={'零':0,'一':1,'二':2,'兩':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,
     '壹':1,'貳':2,'參':3,'叁':3,'肆':4,'伍':5,'陸':6,'柒':7,'捌':8,'玖':9,'０':0,'１':1,'２':2,'３':3,'４':4,'５':5,'６':6,'７':7,'８':8,'９':9}
def num(s):
    if s is None:return 0
    s=s.strip()
    if re.fullmatch(r'[0-9]+',s):return int(s)
    if all(c in '０１２３４５６７８９' for c in s):return int(''.join(str(_CN[c]) for c in s))
    # chinese with 十/百
    total=0;section=0;i=0
    if s=='十':return 10
    for c in s:
        if c=='十':section=(section or 1)*10
        elif c=='百':section=(section or 1)*100
        elif c in _CN:section=_CN[c] if section< 10 else section+_CN[c]
    return section or total
HZ=re.compile(r'主\s*文');HE=re.compile(r'事\s*實|理\s*由|犯\s*罪\s*事\s*實|事實及理由|附錄|附表')
def zhuwen(t):
    m=HZ.search(t)
    if not m:return ""
    s=m.end();e=HE.search(t,s);return t[s:(e.start() if e else min(len(t),s+2500))].strip()
NUMTOK=r'[0-9０-９一二三四五六七八九十百零壹貳參叁肆伍陸柒捌玖兩]+'
def penalty(z):
    d={};
    terms=[]
    for m in re.finditer(r'有期徒刑\s*(?:('+NUMTOK+r')\s*年)?\s*(?:('+NUMTOK+r')\s*月)?(?:\s*(?:又|)\s*('+NUMTOK+r')\s*日)?',z):
        if not (m.group(1) or m.group(2) or m.group(3)):continue
        terms.append({"年":num(m.group(1)),"月":num(m.group(2)),"日":num(m.group(3))})
    if terms:d["有期徒刑"]=terms
    elif '有期徒刑' in z:d["有期徒刑"]=True
    kd=[num(m.group(1)) for m in re.finditer(r'拘役\s*('+NUMTOK+r')\s*日',z)]
    if kd:d["拘役日"]=kd
    elif '拘役' in z:d["拘役"]=True
    if '得易科罰金' in z or '易科罰金' in z:d["得易科罰金"]=True
    mm=re.search(r'緩刑\s*('+NUMTOK+r')\s*年',z)
    if mm:d["緩刑年"]=num(mm.group(1))
    for k,kw in[("無罪","無罪"),("免訴","免訴"),("不受理","不受理"),("駁回","駁回"),("無期徒刑","無期徒刑"),("死刑","死刑")]:
        if kw in z:d[k]=True
    # amounts: accept Arabic OR Chinese (新臺幣…元)
    def amts(label):
        out=[]
        for m in re.finditer(label+r'[^。，]{0,8}?(?:新臺幣|新台幣)?\s*('+NUMTOK+r'(?:,[0-9]{3})*)\s*元',z):
            v=num(re.sub(r',','',m.group(1)))
            if v>=100:out.append(v)
        return out
    if amts('罰金'):d["罰金額"]=amts('罰金')
    if amts('罰鍰'):d["罰鍰額"]=amts('罰鍰')
    if amts('沒收'):d["沒收金額"]=amts('沒收')
    elif '沒收' in z:d["沒收"]=True
    return d
for r in rows:
    z=zhuwen(r.get("全文",""))
    r["主文"]=z[:1500]
    r["判決結果"]=penalty(z if z else r.get("全文","")[:2500])

def pen_summary(d):
    if not d:return ""
    parts=[]
    if isinstance(d.get("有期徒刑"),list):
        for t in d["有期徒刑"]:
            s="有期徒刑"+(f"{t['年']}年" if t['年'] else "")+(f"{t['月']}月" if t['月'] else "")
            parts.append(s)
    elif d.get("有期徒刑"):parts.append("有期徒刑")
    if d.get("拘役日"):parts.append("拘役"+"/".join(str(x)+"日" for x in d["拘役日"]))
    elif d.get("拘役"):parts.append("拘役")
    if d.get("得易科罰金"):parts.append("得易科罰金")
    if d.get("緩刑年"):parts.append(f"緩刑{d['緩刑年']}年")
    if d.get("罰金額"):parts.append("罰金"+"/".join(f"{x:,}" for x in d["罰金額"])+"元")
    if d.get("罰鍰額"):parts.append("罰鍰"+"/".join(f"{x:,}" for x in d["罰鍰額"])+"元")
    if d.get("沒收金額"):parts.append("沒收"+"/".join(f"{x:,}" for x in d["沒收金額"])+"元")
    elif d.get("沒收"):parts.append("沒收")
    for k in("無罪","免訴","不受理","駁回","無期徒刑","死刑"):
        if d.get(k):parts.append(k)
    return "；".join(parts)

# ---- structured JSON (no full text) ----
structured=[]
for r in rows:
    structured.append({k:r[k] for k in["id","laws","category","court","case_year","word","case_no","doctype","jdate","cause","url","適用條號","承審法官","書記官","檢察官"]}|{"主文":r["主文"],"判決結果":r["判決結果"],"判決結果摘要":pen_summary(r["判決結果"]),"全文長度":r["全文長度"]})

# ---- aggregates ----
art_by_law=collections.defaultdict(collections.Counter)
for r in rows:
    for law,arts in (r["適用條號"] or {}).items():
        for a in arts:art_by_law[law][a]+=1
pen=collections.Counter()
imp_terms=[]
fines=[];conf=[]
for r in rows:
    d=r["判決結果"] or {}
    for k in("得易科罰金","沒收","無罪","駁回","不受理","免訴"):
        if d.get(k):pen[k]+=1
    if d.get("緩刑年"):pen["緩刑"]+=1
    if isinstance(d.get("有期徒刑"),list):
        pen["有期徒刑"]+=1
        for t in d["有期徒刑"]:imp_terms.append(t["年"]*12+t["月"])
    elif d.get("有期徒刑"):pen["有期徒刑"]+=1
    for x in (d.get("罰金額") or []):fines.append(x)
    for x in (d.get("沒收金額") or []):conf.append(x)
stats={
 "總筆數":len(rows),
 "有解析出五法條號":sum(1 for r in rows if r["適用條號"]),
 "各法規最常適用條號_前12":{law:dict(c.most_common(12)) for law,c in art_by_law.items()},
 "判決結果統計":dict(pen),
 "有期徒刑月數_樣本數":len(imp_terms),
 "有期徒刑月數_中位數":(sorted(imp_terms)[len(imp_terms)//2] if imp_terms else None),
 "罰金筆數":len(fines),"罰金_最高元":(max(fines) if fines else None),
 "沒收金額筆數":len(conf),"沒收_最高元":(max(conf) if conf else None),
}
meta={"title":"醫藥五法 判決全文結構化資料（112-115）","資料來源":"司法院裁判書系統","擷取日期":"2026-07-07",
 "說明":"逐案下載裁判書全文並解析結構欄位。適用條號=全文中出現之五法條號；主文/判決結果解析自主文段；承審法官/書記官/檢察官解析自裁判書。承審法官涵蓋率約9成（少數法院逐字加標籤者未解析，全文欄位可回溯）。",
 "統計":stats}
json.dump({"meta":meta,"records":structured},open(BASE+".json","w",encoding="utf-8"),ensure_ascii=False,indent=2)

# CSV (flat, no full text)
with open(BASE+".csv","w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f);w.writerow(["法規","類別","法院","年度","字別","案號","文別","裁判日期","案由","適用五法條號","判決結果摘要","承審法官","書記官","檢察官","主文","連結","識別碼"])
    for r in structured:
        arts="；".join(f"{k} §{'、'.join(v)}" for k,v in (r["適用條號"] or {}).items())
        w.writerow(["、".join(r["laws"]),r["category"],r["court"],r["case_year"],r["word"],r["case_no"],r["doctype"],r["jdate"],r["cause"],arts,r["判決結果摘要"],"、".join(r["承審法官"]),r["書記官"],"、".join(r["檢察官"]),r["主文"][:200],r["url"],r["id"]])
print(json.dumps(stats,ensure_ascii=False,indent=2))
