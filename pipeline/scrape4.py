#!/usr/bin/env python3
# FULL-TEXT scrape: every judgment (112-115) whose text mentions each of the 5 laws.
# Adaptive date partitioning bypasses the 500-record pagination cap.
import config
import urllib.request, urllib.parse, http.cookiejar, re, time, json, sys, math, html as H, calendar
BASE="https://judgment.judicial.gov.tw/FJUD/"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
PER=20
QUERIES=[("藥事法","jud_kw","藥事法"),("醫療法","jud_kw","醫療法"),
         ("醫師法","jud_kw","醫師法"),("醫療器材管理法","jud_kw","醫療器材管理法"),
         ("藥師法","jud_kw","藥師法")]
def sess():return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def get(op,u,ref=None,tries=5):
    hd={"User-Agent":UA,"Accept-Language":"zh-TW"}
    if ref:hd["Referer"]=ref
    for t in range(tries):
        try:return op.open(urllib.request.Request(u,headers=hd),timeout=60).read().decode('utf-8','replace')
        except Exception:
            if t==tries-1:raise
            time.sleep(2+2*t)
def post(op,u,f,ref,tries=5):
    for t in range(tries):
        try:return op.open(urllib.request.Request(u,data=urllib.parse.urlencode(f).encode(),headers={"User-Agent":UA,"Content-Type":"application/x-www-form-urlencoded","Referer":ref,"Accept-Language":"zh-TW"}),timeout=90).read().decode('utf-8','replace')
        except Exception:
            if t==tries-1:raise
            time.sleep(2+2*t)
def hid(h,n):
    m=re.search(r'id="%s"[^>]*value="([^"]*)"'%re.escape(n),h);return m.group(1) if m else ""
ITEM_RE=re.compile(r'<a id="hlTitle"[^>]*href="data\.aspx\?ty=JD&amp;id=([^"&]+)&amp;ot=in"[^>]*>(.*?)</a>(?:（([^）]*)）)?\s*</td>\s*<td[^>]*>([^<]*)</td>\s*<td[^>]*>(.*?)</td>',re.S)
SNIP_RE=re.compile(r'<tr class="summary">.*?<span class="tdCut">(.*?)</span>',re.S)
def clean(s):return H.unescape(re.sub(r'<[^>]+>','',s or '')).strip()
def parse_title(t):
    m=re.match(r'^(.*?(?:院|法庭|分署|檢察署)(?:\s*(?:地方庭|高等庭|簡易庭|智慧財產庭|勞動庭|家事庭))?)\s*(\d+)\s*年度?\s*(.*?)\s*字第\s*([\d,]+)\s*號\s*(.*)$',t)
    return (re.sub(r'\s+',' ',m.group(1)).strip(),m.group(5).strip()) if m else ("","")
def parse_page(html):
    rows=[]
    for m in ITEM_RE.finditer(html):
        rid=urllib.parse.unquote(m.group(1));title=clean(m.group(2));size=(m.group(3) or "").strip()
        date=clean(m.group(4));cause=clean(m.group(5));idf=rid.split(',');idd=idf[4] if len(idf)>4 else ""
        court,doctype=parse_title(title)
        sm=SNIP_RE.search(html,m.end());snip=clean(sm.group(1)) if sm else ""
        rows.append({"id":rid,"court_code":idf[0] if idf else "","case_year":idf[1] if len(idf)>1 else "",
            "word":idf[2] if len(idf)>2 else "","case_no":idf[3] if len(idf)>3 else "",
            "jdate":(f"{idd[:4]}-{idd[4:6]}-{idd[6:8]}" if len(idd)==8 else date),
            "court":court,"doctype":doctype,"title":title,"cause":cause,"size":size,"snippet":snip,
            "url":BASE+"data.aspx?ty=JD&id="+urllib.parse.quote(rid,safe='')+"&ot=in"})
    return rows
def run_query(field,val,y1,m1,d1,y2,m2,d2):
    op=sess();u1=BASE+"Default_AD.aspx";h=get(op,u1)
    f={"__VIEWSTATE":hid(h,"__VIEWSTATE"),"__EVENTVALIDATION":hid(h,"__EVENTVALIDATION"),"__VIEWSTATEGENERATOR":hid(h,"__VIEWSTATEGENERATOR"),"__VIEWSTATEENCRYPTED":"","jud_court":"","sel_judword":"","jud_sys":"","judtype":"","whosub":"0","jud_kw":"","jud_year":"","jud_case":"","jud_no":"","jud_no_end":"","jud_title":"","jud_jmain":"","dy1":str(y1),"dm1":str(m1),"dd1":str(d1),"dy2":str(y2),"dm2":str(m2),"dd2":str(d2),"KbStart":"","KbEnd":"","ctl00$cp_content$btnQry":"送出查詢"}
    f[field]=val
    r=post(op,u1,f,u1);m=re.search(r'qryresultlst\.aspx\?ty=JUDBOOK&q=([0-9a-f]+)',r)
    if not m:return 0,None,op,None
    q=m.group(1);lst=BASE+f"qryresultlst.aspx?ty=JUDBOOK&q={q}";p1=get(op,lst,u1)
    mc=re.search(r'共\s*([\d,]+)\s*筆',p1);count=int(mc.group(1).replace(',','')) if mc else 0
    return count,p1,op,(q,lst)
def mdays(y,mon):return calendar.monthrange(y+1911,mon)[1]
def scrape_range(field,val,y1,m1,d1,y2,m2,d2,depth=0):
    count,p1,op,qi=run_query(field,val,y1,m1,d1,y2,m2,d2)
    tag=f"{y1}.{m1:02d}.{d1:02d}-{y2}.{m2:02d}.{d2:02d}"
    if count<=500:
        if count==0:return []
        q,lst=qi;rows=parse_page(p1);pages=max(1,math.ceil(count/PER))
        for pg in range(2,pages+1):
            rows+=parse_page(get(op,BASE+f"qryresultlst.aspx?q={q}&sort=DS&page={pg}",lst));time.sleep(0.4)
        print(f"  {'  '*depth}{tag} n={count} got={len(rows)}",file=sys.stderr);return rows
    a=y1*12+(m1-1);b=y2*12+(m2-1)
    if a>=b:  # single month still >500 -> split by day
        if d1>=d2:
            print(f"  {'  '*depth}{tag} n={count} >500 single-day CAP, taking 500",file=sys.stderr)
            q,lst=qi;rows=parse_page(p1)
            for pg in range(2,26):rows+=parse_page(get(op,BASE+f"qryresultlst.aspx?q={q}&sort=DS&page={pg}",lst));time.sleep(0.4)
            return rows
        print(f"  {'  '*depth}{tag} n={count} >500 -> split days",file=sys.stderr)
        half=(d1+d2)//2
        return scrape_range(field,val,y1,m1,d1,y1,m1,half,depth+1)+scrape_range(field,val,y1,m1,half+1,y2,m2,d2,depth+1)
    print(f"  {'  '*depth}{tag} n={count} >500 -> split months",file=sys.stderr)
    mid=(a+b)//2;fy,fm=mid//12,mid%12+1;ny,nm=(mid+1)//12,(mid+1)%12+1
    return scrape_range(field,val,y1,m1,d1,fy,fm,mdays(fy,fm),depth+1)+scrape_range(field,val,ny,nm,1,y2,m2,d2,depth+1)
if __name__=="__main__":
    only=sys.argv[1] if len(sys.argv)>1 else None
    out=[]
    for law,field,val in QUERIES:
        if only and law!=only:continue
        print(f"===[{law}] {field}={val}===",file=sys.stderr);sys.stderr.flush()
        rows=scrape_range(field,val,*config.START,*config.END)
        seen={};[seen.setdefault(r["id"],r) for r in rows];uniq=list(seen.values())
        for r in uniq:r["law"]=law
        out.append({"law":law,"field":field,"value":val,"unique":len(uniq),"raw":len(rows),"rows":uniq})
        print(f"===[{law}] DONE unique={len(uniq)} raw={len(rows)}===",file=sys.stderr);sys.stderr.flush()
        time.sleep(1)
    suffix=only or "all"
    json.dump(out,open(f"raw_fulltext_{suffix}.json","w",encoding="utf-8"),ensure_ascii=False)
    print("ALL DONE:",{o["law"]:o["unique"] for o in out},"sum=",sum(o["unique"] for o in out))
