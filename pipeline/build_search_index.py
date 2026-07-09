#!/usr/bin/env python3
# Build the front-end search index (A / MiniSearch-class) + precomputed stats
# from data/醫藥五法_結構化_112-115.json.
# Output: medlaw-qa/data/search-index.json  (compact per-record, metadata + 條號 + 案由 + 判決結果摘要)
#         medlaw-qa/data/stats.json         (aggregate counts for statistical answers)
import json, collections, os
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.dirname(HERE)
SRC=os.path.join(ROOT,"data","醫藥五法_結構化_112-115.json")
OUTDIR=os.path.join(ROOT,"medlaw-qa","data")
os.makedirs(OUTDIR,exist_ok=True)

recs=json.load(open(SRC,encoding="utf-8"))["records"]
print("loaded",len(recs))
# 據案由起訴 lives in the full-text total index, not in 結構化 — merge it in by id
FULL=os.path.join(ROOT,"data","醫藥五法_全文總索引_112-115.json")
cause_map={r["id"]: r.get("據案由起訴",[]) for r in json.load(open(FULL,encoding="utf-8"))["records"]}
print("據案由起訴 mapped:", sum(1 for v in cause_map.values() if v))

def arts_str(a):  # {"藥事法":["83","22"]} -> "藥事法§83 藥事法§22"
    out=[]
    for law,arr in (a or {}).items():
        for art in arr: out.append(f"{law}§{art}")
    return out

index=[]
for r in recs:
    arts=arts_str(r.get("適用條號"))
    index.append({
        "i": r["id"],
        "c": r["court"],
        "y": r["case_year"],
        "w": r["word"],
        "n": r["case_no"],
        "d": r["jdate"],
        "u": r["cause"],
        "l": r["laws"],
        "g": r["category"],
        "a": arts,
        "r": r.get("判決結果摘要",""),
        "b": cause_map.get(r["id"],[]),   # laws for which cause targets that law (據案由起訴)
        "url": r["url"],
    })
idx_json=json.dumps(index, ensure_ascii=False, separators=(",",":"))
open(os.path.join(OUTDIR,"search-index.json"),"w",encoding="utf-8").write(idx_json)
# JS-global variant so index.html works from file:// (fetch is CORS-blocked on double-click)
open(os.path.join(OUTDIR,"search-index.js"),"w",encoding="utf-8").write("window.SEARCH_INDEX="+idx_json+";\n")

# ---- aggregate stats ----
art_by_law=collections.defaultdict(collections.Counter)
per_law=collections.Counter(); per_court=collections.Counter()
per_year=collections.Counter(); per_cat=collections.Counter()
per_law_year=collections.defaultdict(collections.Counter)
for r in recs:
    for l in r["laws"]: per_law[l]+=1
    per_court[r["court"]]+=1; per_cat[r["category"]]+=1
    try: ry=int(r["jdate"][:4])-1911
    except: ry=None
    if ry: per_year[ry]+=1
    for law,arr in (r.get("適用條號") or {}).items():
        for art in arr:
            art_by_law[law][art]+=1
            if ry: per_law_year[f"{law}"][ry]+=1
stats={
    "total": len(recs),
    "snapshot":"2026-07-07",
    "per_law": dict(per_law),
    "per_category": dict(per_cat),
    "per_year": {str(k):v for k,v in sorted(per_year.items())},
    "top_courts": dict(per_court.most_common(20)),
    "article_counts": {law:dict(c.most_common(40)) for law,c in art_by_law.items()},
}
stats_json=json.dumps(stats, ensure_ascii=False, separators=(",",":"))
open(os.path.join(OUTDIR,"stats.json"),"w",encoding="utf-8").write(stats_json)
open(os.path.join(OUTDIR,"stats.js"),"w",encoding="utf-8").write("window.STATS="+stats_json+";\n")

# subset for the Artifact single-file preview (full 4.9MB is too heavy to inline);
# take the most recent 2000 by judgment date so live search still feels real.
subset=sorted(index, key=lambda r:r["d"], reverse=True)[:2000]
open(os.path.join(OUTDIR,"search-index.subset.js"),"w",encoding="utf-8").write(
    "window.SEARCH_INDEX="+json.dumps(subset,ensure_ascii=False,separators=(",",":"))+";\n")

si=os.path.getsize(os.path.join(OUTDIR,"search-index.json"))
st=os.path.getsize(os.path.join(OUTDIR,"stats.json"))
print(f"search-index.json {si/1e6:.2f} MB  ({len(index)} records)")
print(f"stats.json {st/1e3:.1f} KB")
print("sample:", json.dumps(index[0], ensure_ascii=False)[:300])
