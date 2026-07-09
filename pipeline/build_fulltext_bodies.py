#!/usr/bin/env python3
# Ship judgment full-text bodies for B1 deep search (plain-JS engine).
# Default: ALL 14,031 判決。  Output: medlaw-qa/data/fulltext.json.gz = [{i:id, t:全文}, ...]
import json, gzip, os
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
JSONL=os.path.join(ROOT,"data","醫藥五法_判決全文_112-115.jsonl")
OUT=os.path.join(ROOT,"medlaw-qa","data","fulltext.json.gz")

def open_jsonl(path):  # repo 內保存的是 .gz;未壓縮版可能不存在
    if os.path.exists(path): return open(path,encoding="utf-8")
    if os.path.exists(path+".gz"): return gzip.open(path+".gz","rt",encoding="utf-8")
    raise FileNotFoundError(path+"(.gz)")

docs=[]; chars=0
with open_jsonl(JSONL) as f:
    for line in f:
        if not line.strip():continue
        r=json.loads(line)
        body=r.get("全文","")
        docs.append({"i":r["id"],"t":body}); chars+=len(body)
raw=json.dumps(docs,ensure_ascii=False,separators=(",",":")).encode("utf-8")
with gzip.open(OUT,"wb",compresslevel=9) as g: g.write(raw)
print(f"docs={len(docs)} chars={chars:,} raw={len(raw)/1e6:.1f}MB gz={os.path.getsize(OUT)/1e6:.1f}MB -> {OUT}")
