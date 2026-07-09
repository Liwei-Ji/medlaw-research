#!/usr/bin/env python3
import json, csv, collections, re
# --- load full-text blocks ---
blocks=json.load(open("raw_fulltext_藥事法.json",encoding="utf-8"))+json.load(open("raw_fulltext_rest.json",encoding="utf-8"))
# --- cause-based id sets (for flagging 據該法起訴) ---
cause_ids=collections.defaultdict(set)
cb=json.load(open("raw_cause.json",encoding="utf-8"))
yb=json.load(open("raw_yaoshifa_full.json",encoding="utf-8"))
for blk in cb:
    if blk["law"]=="藥事法":continue      # use complete set below
    for r in blk["rows"]:cause_ids[blk["law"]].add(r["id"])
for r in yb["rows"]:cause_ids["藥事法"].add(r["id"])

by_id={}
per_law_raw=collections.Counter()
for block in blocks:
    law=block["law"];per_law_raw[law]=block["unique"]
    for r in block["rows"]:
        rid=r["id"]
        if rid in by_id:
            if law not in by_id[rid]["laws"]:by_id[rid]["laws"].append(law)
        else:
            rec={k:v for k,v in r.items() if k!="law"};rec["laws"]=[law];by_id[rid]=rec
records=list(by_id.values())
def category(r):
    d=r.get("doctype","")
    if "懲戒" in d or "懲戒" in r.get("court",""):return "懲戒"
    if "刑" in d:return "刑事"
    if "民" in d:return "民事"
    if "行" in d or r["court"].endswith("行政法院") or "行政" in r["court"]:return "行政"
    cc=r.get("court_code","")
    if cc.endswith("M"):return "刑事"
    if cc.endswith("V"):return "民事"
    if cc.endswith("A"):return "行政"
    if "憲" in r.get("court",""):return "憲法法庭"
    return "其他/未分類"
for r in records:
    r["category"]=category(r)
    # per-law flag: does this judgment's cause指向該法 (實際據該法起訴/裁罰)
    r["據案由起訴"]=sorted([l for l in r["laws"] if r["id"] in cause_ids.get(l,())])
records.sort(key=lambda r:(r.get("jdate",""),r.get("id","")),reverse=True)

per_law=collections.Counter()
for r in records:
    for l in r["laws"]:per_law[l]+=1
per_cat=collections.Counter(r["category"] for r in records)
per_year=collections.Counter(r["case_year"] for r in records)
per_court=collections.Counter(r["court"] for r in records)
n_multi=sum(1 for r in records if len(r["laws"])>1)
n_cause=sum(1 for r in records if r["據案由起訴"])

meta={
 "title":"醫藥五法 全文檢索判決總索引（司法院裁判書系統，裁判日期 112-115 年）",
 "資料來源":"司法院裁判書查詢系統 https://judgment.judicial.gov.tw/FJUD/",
 "擷取日期":"2026-07-07",
 "查詢條件":{"裁判期間":"民國112/1/1 – 115/12/31（依裁判日期）",
   "檢索方式":"五法各以『全文內容(jud_kw)』包含該法名稱檢索，凡判決文中提及該法即納入（含附帶引用）",
   "克服上限":"系統結果清單僅開放前500筆分頁；已對每一查詢自動遞迴切分裁判日期區間使每段≤500筆後合併"},
 "各法規全文筆數_未跨法去重":dict(per_law_raw),
 "各法規全文筆數合計_未去重":sum(per_law_raw.values()),
 "去重後總筆數":len(records),
 "跨法規重複(同一判決列於多法)":n_multi,
 "其中實際據該法起訴裁罰(案由指向該法)":n_cause,
 "各法規筆數_去重內":dict(per_law),
 "案件類別分布":dict(per_cat),
 "各年度分布(案號年度)":dict(sorted(per_year.items())),
 "主要法院分布_前15":dict(per_court.most_common(15))}
json.dump({"meta":meta,"records":records},open("醫藥五法_全文總索引_112-115.json","w",encoding="utf-8"),ensure_ascii=False,indent=2)

# classified 法規->類別
LAW_ORDER=["藥事法","醫療器材管理法","醫療法","醫師法","藥師法"]
CAT_ORDER=["刑事","民事","行政","懲戒","憲法法庭","其他/未分類"]
classified=[]
for law in LAW_ORDER:
    lr=[r for r in records if law in r["laws"]];cats=[]
    for cat in CAT_ORDER:
        sub=[r for r in lr if r["category"]==cat]
        if not sub:continue
        cats.append({"類別":cat,"筆數":len(sub),"判決":[{"法院":r["court"],"年度":r["case_year"],"字別":r["word"],"案號":r["case_no"],"文別":r["doctype"],"裁判日期":r["jdate"],"案由":r["cause"],"據該法起訴":law in r["據案由起訴"],"標題":r["title"],"摘要":r["snippet"],"連結":r["url"],**({"跨法規":r["laws"]} if len(r["laws"])>1 else {})} for r in sub]})
    classified.append({"法規":law,"筆數":len(lr),"類別分布":{c["類別"]:c["筆數"] for c in cats},"案件":cats})
json.dump({"meta":meta,"分類":classified},open("醫藥五法_全文總索引_112-115_分類.json","w",encoding="utf-8"),ensure_ascii=False,indent=2)

# CSV
with open("醫藥五法_全文總索引_112-115.csv","w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f);w.writerow(["法規","據該法起訴","類別","法院","年度","字別","案號","文別","裁判日期","案由","大小","標題","摘要","連結","識別碼"])
    for r in records:
        w.writerow(["、".join(r["laws"]),"、".join(r["據案由起訴"]),r["category"],r["court"],r["case_year"],r["word"],r["case_no"],r["doctype"],r["jdate"],r["cause"],r["size"],r["title"],r["snippet"],r["url"],r["id"]])
print("unique records:",len(records))
print("per_law (dedup):",dict(per_law))
print("per_law raw:",dict(per_law_raw),"sum",sum(per_law_raw.values()))
print("multi-law:",n_multi,"| cause-based:",n_cause)
print("per_cat:",dict(per_cat))
