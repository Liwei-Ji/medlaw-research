#!/usr/bin/env python3
import json, csv, collections, re, os, config
HERE=config.HERE; BASE=config.CAUSE_INDEX[:-5]   # data/醫藥五法_判決索引_<suffix>
raw=json.load(open(os.path.join(HERE,"raw_cause.json"),encoding="utf-8"))
# swap in the COMPLETE 藥事法 set (raw_cause 藥事法 was truncated at the 500-record cap)
ys=json.load(open(os.path.join(HERE,"raw_yaoshifa_full.json"),encoding="utf-8"))
raw=[b for b in raw if b["law"]!="藥事法"]+[ys]
# flatten + dedup by id (merge law tags if a judgment appears under multiple queries)
by_id={}
for block in raw:
    for r in block["rows"]:
        rid=r["id"]
        if rid in by_id:
            if r["law"] not in by_id[rid]["laws"]:
                by_id[rid]["laws"].append(r["law"])
        else:
            rec=dict(r)
            rec["laws"]=[r.pop("law")]
            rec.pop("match_method",None)
            by_id[rid]=rec
records=list(by_id.values())
# backfill court name for titles with an extra 庭 segment (e.g. 高等行政法院 地方庭 ...)
import re as _re
TR=_re.compile(r'^(.*?(?:院|法庭|分署|檢察署)(?:\s*(?:地方庭|高等庭|簡易庭|智慧財產庭|勞動庭|家事庭))?)\s*\d+\s*年度?\s*(.*?)\s*字第')
for r in records:
    if not r["court"]:
        m=TR.match(r["title"])
        if m:
            r["court"]=_re.sub(r'\s+',' ',m.group(1)).strip()
# derive category from court_code suffix / word: M=刑事,V=民事,A=行政 heuristics via doctype/word
def category(r):
    d=r.get("doctype","")
    if "刑" in d: return "刑事"
    if "民" in d: return "民事"
    if "行" in d or r["court"].endswith("行政法院") or "行政法庭" in r["court"]: return "行政"
    cc=r.get("court_code","")
    if cc.endswith("M"): return "刑事"
    if cc.endswith("V"): return "民事"
    if cc.endswith("A"): return "行政"
    return "其他/未分類"
for r in records:
    r["category"]=category(r)
records.sort(key=lambda r:(r.get("jdate",""),r.get("id","")),reverse=True)

# summaries
per_law=collections.Counter()
for r in records:
    for l in r["laws"]: per_law[l]+=1
per_year=collections.Counter(r["case_year"] for r in records)
per_cat=collections.Counter(r["category"] for r in records)
per_court=collections.Counter(r["court"] for r in records)

meta={
 "title":"醫藥五法 判決索引（司法院裁判書系統，裁判日期 112-115 年）",
 "資料來源":"司法院裁判書查詢系統 https://judgment.judicial.gov.tw/FJUD/",
 "擷取日期":"2026-07-07",
 "查詢條件":{
   "裁判期間":"民國112年1月1日 – 115年12月31日（依裁判日期）",
   "藥事法/醫療器材管理法/醫療法/醫師法":"裁判案由 =「違反<法規>」（實際據該法起訴/裁罰之案件）",
   "藥師法":"全文含「藥師法」（案由無『違反藥師法』類別，違反藥師法案由查無資料，故採全文檢索，71筆）",
 },
 "方法說明":"以案由(裁判案由)鎖定『據各該法審理/裁罰』之案件，排除僅於文中順帶提及該法之判決（全文檢索藥事法達10,683筆，多為附帶引用，不納入）。各欄位（法院、年度、字別、案號、裁判日期）解析自結果清單之案件識別碼，未逐案下載全文。",
 "總筆數_去重後":len(records),
 "各法規筆數":dict(per_law),
 "案件類別分布":dict(per_cat),
 "各年度分布(案號年度)":dict(sorted(per_year.items())),
 "主要法院分布_前15":dict(per_court.most_common(15)),
}
out={"meta":meta,"records":records}
json.dump(out,open(BASE+".json","w",encoding="utf-8"),ensure_ascii=False,indent=2)

# ---- classified version: 法規 -> 類別 -> records ----
LAW_ORDER=["藥事法","醫療器材管理法","醫療法","醫師法","藥師法"]
CAT_ORDER=["刑事","民事","行政","其他/未分類"]
classified=[]
for law in LAW_ORDER:
    law_recs=[r for r in records if law in r["laws"]]
    cats=[]
    for cat in CAT_ORDER:
        sub=[r for r in law_recs if r["category"]==cat]
        if not sub: continue
        cats.append({"類別":cat,"筆數":len(sub),
            "判決":[{"法院":r["court"],"年度":r["case_year"],"字別":r["word"],"案號":r["case_no"],
                    "文別":r["doctype"],"裁判日期":r["jdate"],"案由":r["cause"],
                    "標題":r["title"],"摘要":r["snippet"],"連結":r["url"],
                    **({"跨法規":r["laws"]} if len(r["laws"])>1 else {})} for r in sub]})
    classified.append({"法規":law,"筆數":len(law_recs),
        "檢索方式":("案由「違反%s」"%law if law!="藥師法" else "全文含「藥師法」"),
        "類別分布":{c["類別"]:c["筆數"] for c in cats},"案件":cats})
json.dump({"meta":meta,"分類":classified},
    open(BASE+"_分類.json","w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("classified laws:",[(c["法規"],c["筆數"]) for c in classified])

# CSV
cols=["laws","category","court","case_year","word","case_no","doctype","jdate","cause","size","title","snippet","url","id"]
with open(BASE+".csv","w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f);w.writerow(["法規","類別","法院","年度","字別","案號","文別","裁判日期","案由","大小","標題","摘要","連結","識別碼"])
    for r in records:
        w.writerow(["、".join(r["laws"])]+[r.get(c,"") if c!="laws" else "" for c in cols[1:]])
print("records:",len(records))
print("per_law:",dict(per_law))
print("per_cat:",dict(per_cat))
print("per_year:",dict(sorted(per_year.items())))
