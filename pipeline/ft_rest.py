import scrape4, json, sys
laws=[("醫療法","jud_kw","醫療法"),("醫師法","jud_kw","醫師法"),
      ("醫療器材管理法","jud_kw","醫療器材管理法"),("藥師法","jud_kw","藥師法")]
out=[]
for law,field,val in laws:
    print(f"===[{law}]===",file=sys.stderr);sys.stderr.flush()
    rows=scrape4.scrape_range(field,val,112,1,1,115,12,31)
    seen={};[seen.setdefault(r["id"],r) for r in rows];uniq=list(seen.values())
    for r in uniq:r["law"]=law
    out.append({"law":law,"field":field,"value":val,"unique":len(uniq),"raw":len(rows),"rows":uniq})
    print(f"===[{law}] DONE unique={len(uniq)}===",file=sys.stderr);sys.stderr.flush()
json.dump(out,open("raw_fulltext_rest.json","w",encoding="utf-8"),ensure_ascii=False)
print("REST DONE:",{o['law']:o['unique'] for o in out})
