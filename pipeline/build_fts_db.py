#!/usr/bin/env python3
# Build a SQLite FTS5 (trigram) full-text database from the judgment full-text archive,
# for browser-side deep full-text search via sql.js (Architecture B1).
#   python3 build_fts_db.py all     -> fulltext-all.db     (all 14,031)
#   python3 build_fts_db.py cause   -> fulltext-cause.db   (據案由起訴 subset)
import sqlite3, json, os, sys, time, gzip
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
JSONL=os.path.join(ROOT,"data","醫藥五法_判決全文_112-115.jsonl")
def open_jsonl(path):
    if os.path.exists(path): return open(path,encoding="utf-8")
    if os.path.exists(path+".gz"): return gzip.open(path+".gz","rt",encoding="utf-8")
    raise FileNotFoundError(path+"(.gz)")
IDXJSON=os.path.join(ROOT,"medlaw-qa","data","search-index.json")
mode=sys.argv[1] if len(sys.argv)>1 else "all"
OUT=os.path.join(HERE, "fulltext-%s.db"%mode)

cause_ids=None
if mode=="cause":
    idx=json.load(open(IDXJSON,encoding="utf-8"))
    cause_ids=set(r["i"] for r in idx if r.get("b"))   # 據案由起訴 non-empty
    print("cause-based ids:", len(cause_ids))

if os.path.exists(OUT): os.remove(OUT)
con=sqlite3.connect(OUT)
con.execute("PRAGMA journal_mode=OFF"); con.execute("PRAGMA synchronous=OFF")
con.execute("""CREATE VIRTUAL TABLE docs USING fts5(
  jid UNINDEXED, court UNINDEXED, cy UNINDEXED, word UNINDEXED, cno UNINDEXED,
  jdate UNINDEXED, cause UNINDEXED, laws UNINDEXED, cat UNINDEXED, arts UNINDEXED, res UNINDEXED, url UNINDEXED,
  body, tokenize='trigram')""")
t0=time.time(); n=0
cur=con.cursor()
with open_jsonl(JSONL) as f:
    for line in f:
        if not line.strip(): continue
        r=json.loads(line)
        if cause_ids is not None and r["id"] not in cause_ids: continue
        arts=r.get("適用條號") or {}
        arts_s=" ".join(f"{k}§{a}" for k,arr in arts.items() for a in arr)
        cur.execute("INSERT INTO docs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",(
            r["id"], r["court"], r["case_year"], r["word"], r["case_no"], r["jdate"],
            r["cause"], " ".join(r["laws"]), r.get("category",""), arts_s,
            r.get("判決結果摘要",""), r["url"], r.get("全文","")))
        n+=1
        if n%2000==0: con.commit(); print(f"  {n} rows...", flush=True)
con.commit()
con.execute("INSERT INTO docs(docs) VALUES('optimize')"); con.commit()
con.close()
sz=os.path.getsize(OUT)
print(f"DONE mode={mode} rows={n} time={time.time()-t0:.1f}s  {OUT}  {sz/1e6:.1f} MB")
