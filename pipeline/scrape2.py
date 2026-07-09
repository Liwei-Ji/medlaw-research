#!/usr/bin/env python3
# Cause-of-action index for the 5 medical/pharma laws, judgment date 112-115.
import config
import urllib.request, urllib.parse, http.cookiejar, re, time, json, sys, math, html as H
BASE="https://judgment.judicial.gov.tw/FJUD/"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
PER=20
# (law_label, form_field, search_value, method_note)
QUERIES=[
 ("藥事法","jud_title","違反藥事法","案由"),
 ("醫療器材管理法","jud_title","違反醫療器材管理法","案由"),
 ("醫療法","jud_title","違反醫療法","案由"),
 ("醫師法","jud_title","違反醫師法","案由"),
 ("藥師法","jud_kw","藥師法","全文(案由無違反藥師法類別)"),
]
def sess():return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def get(op,u,ref=None,tries=4):
    hd={"User-Agent":UA,"Accept-Language":"zh-TW,zh;q=0.9"}
    if ref:hd["Referer"]=ref
    for t in range(tries):
        try:return op.open(urllib.request.Request(u,headers=hd),timeout=60).read().decode('utf-8','replace')
        except Exception:
            if t==tries-1:raise
            time.sleep(2+2*t)
def post(op,u,f,ref,tries=4):
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
    m=re.match(r'^(.*?院|.*?法庭|.*?分署|.*?檢察署)\s*(\d+)\s*年度?\s*(.*?)\s*字第\s*([\d,]+)\s*號\s*(.*)$',t)
    if m:return m.group(1).strip(),m.group(5).strip()
    return "",""
def parse_page(html):
    rows=[]
    for m in ITEM_RE.finditer(html):
        rid=urllib.parse.unquote(m.group(1));title=clean(m.group(2));size=(m.group(3) or "").strip()
        date=clean(m.group(4));cause=clean(m.group(5));idf=rid.split(',')
        idd=idf[4] if len(idf)>4 else "";court,doctype=parse_title(title)
        sm=SNIP_RE.search(html,m.end());snip=clean(sm.group(1)) if sm else ""
        rows.append({"id":rid,"court_code":idf[0] if idf else "","case_year":idf[1] if len(idf)>1 else "",
            "word":idf[2] if len(idf)>2 else "","case_no":idf[3] if len(idf)>3 else "",
            "jdate":(f"{idd[:4]}-{idd[4:6]}-{idd[6:8]}" if len(idd)==8 else date),
            "court":court,"doctype":doctype,"title":title,"cause":cause,"size":size,"snippet":snip,
            "url":BASE+"data.aspx?ty=JD&id="+urllib.parse.quote(rid,safe='')+"&ot=in"})
    return rows
def scrape(field,val):
    op=sess();u1=BASE+"Default_AD.aspx";h=get(op,u1)
    f={"__VIEWSTATE":hid(h,"__VIEWSTATE"),"__EVENTVALIDATION":hid(h,"__EVENTVALIDATION"),"__VIEWSTATEGENERATOR":hid(h,"__VIEWSTATEGENERATOR"),"__VIEWSTATEENCRYPTED":"","jud_court":"","sel_judword":"","jud_sys":"","judtype":"","whosub":"0","jud_kw":"","jud_year":"","jud_case":"","jud_no":"","jud_no_end":"","jud_title":"","jud_jmain":"","dy1":str(config.START[0]),"dm1":str(config.START[1]),"dd1":str(config.START[2]),"dy2":str(config.END[0]),"dm2":str(config.END[1]),"dd2":str(config.END[2]),"KbStart":"","KbEnd":"","ctl00$cp_content$btnQry":"送出查詢"}
    f[field]=val
    r=post(op,u1,f,u1)
    m=re.search(r'qryresultlst\.aspx\?ty=JUDBOOK&q=([0-9a-f]+)',r)
    if not m:return 0,[]
    q=m.group(1);lst=BASE+f"qryresultlst.aspx?ty=JUDBOOK&q={q}"
    p1=get(op,lst,u1);mc=re.search(r'共\s*([\d,]+)\s*筆',p1)
    count=int(mc.group(1).replace(',','')) if mc else 0
    pages=max(1,math.ceil(count/PER));rows=parse_page(p1)
    print(f"    count={count} pages={pages}",file=sys.stderr)
    for pg in range(2,pages+1):
        ph=get(op,BASE+f"qryresultlst.aspx?q={q}&sort=DS&page={pg}",lst)
        rows+=parse_page(ph)
        if pg%20==0:print(f"    page {pg}/{pages} rows={len(rows)}",file=sys.stderr)
        time.sleep(0.5)
    return count,rows
if __name__=="__main__":
    out=[]
    for law,field,val,note in QUERIES:
        print(f"[{law}] {field}={val}",file=sys.stderr)
        cnt,rows=scrape(field,val)
        for row in rows:row["law"]=law;row["match_method"]=note
        out.append({"law":law,"field":field,"value":val,"method":note,"count":cnt,"parsed":len(rows),"rows":rows})
        print(f"[{law}] done parsed={len(rows)}/{cnt}",file=sys.stderr)
        time.sleep(1)
    json.dump(out,open("raw_cause.json","w",encoding="utf-8"),ensure_ascii=False)
    print("ALL DONE. per-law:",{o["law"]:(o["count"],o["parsed"]) for o in out})
    print("total parsed:",sum(o["parsed"] for o in out))
