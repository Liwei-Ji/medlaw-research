#!/usr/bin/env python3
# Scrape FJUD (judgment.judicial.gov.tw) structured index for the 5 medical/pharma laws, 112-115.
import urllib.request, urllib.parse, http.cookiejar, re, time, json, sys, math, html as H

BASE="https://judgment.judicial.gov.tw/FJUD/"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
LAWS=["藥事法","醫療器材管理法","醫療法","醫師法","藥師法"]
DY1,DY2="112","115"
PER=20

def new_session():
    cj=http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def get(op,url,ref=None,tries=4):
    hd={"User-Agent":UA,"Accept-Language":"zh-TW,zh;q=0.9"}
    if ref: hd["Referer"]=ref
    for t in range(tries):
        try:
            return op.open(urllib.request.Request(url,headers=hd),timeout=60).read().decode('utf-8','replace')
        except Exception as e:
            if t==tries-1: raise
            time.sleep(2+2*t)

def post(op,url,fields,ref,tries=4):
    body=urllib.parse.urlencode(fields).encode()
    for t in range(tries):
        try:
            return op.open(urllib.request.Request(url,data=body,headers={"User-Agent":UA,
              "Content-Type":"application/x-www-form-urlencoded","Referer":ref,
              "Accept-Language":"zh-TW,zh;q=0.9"}),timeout=90).read().decode('utf-8','replace')
        except Exception as e:
            if t==tries-1: raise
            time.sleep(2+2*t)

def hid(html,n):
    m=re.search(r'id="%s"[^>]*value="([^"]*)"'%re.escape(n),html); return m.group(1) if m else ""

ITEM_RE=re.compile(
    r'<a id="hlTitle"[^>]*href="data\.aspx\?ty=JD&amp;id=([^"&]+)&amp;ot=in"[^>]*>(.*?)</a>'
    r'(?:（([^）]*)）)?\s*</td>\s*'
    r'<td[^>]*>([^<]*)</td>\s*'
    r'<td[^>]*>(.*?)</td>', re.S)
SNIP_RE=re.compile(r'<tr class="summary">.*?<span class="tdCut">(.*?)</span>', re.S)

def clean(s):
    s=re.sub(r'<[^>]+>','',s or '')
    return H.unescape(s).strip()

def parse_title(t):
    # e.g. 最高行政法院 113 年度 上 字第 713 號裁定
    m=re.match(r'^(.*?院|.*?法庭|.*?分署|.*?檢察署)\s*(\d+)\s*年度?\s*(.*?)\s*字第\s*([\d,]+)\s*號\s*(.*)$',t)
    if m:
        return {"court":m.group(1).strip(),"c_year":m.group(2),"word":m.group(3).strip(),
                "c_no":m.group(4).replace(',',''),"doctype":m.group(5).strip()}
    return {"court":"","c_year":"","word":"","c_no":"","doctype":""}

def parse_page(html):
    rows=[]
    # iterate item blocks; snippet is in the following summary row
    parts=re.split(r'(<a id="hlTitle")',html)
    # simpler: find items, then find snippet after each item's position
    for m in ITEM_RE.finditer(html):
        rid=urllib.parse.unquote(m.group(1))
        title=clean(m.group(2))
        size=(m.group(3) or "").strip()
        date=clean(m.group(4))
        cause=clean(m.group(5))
        # id fields: COURT,YEAR,字,NO,YYYYMMDD,SEQ
        idf=rid.split(',')
        iddate=idf[4] if len(idf)>4 else ""
        tp=parse_title(title)
        # snippet: search after this match
        sm=SNIP_RE.search(html,m.end())
        snip=clean(sm.group(1)) if sm else ""
        rows.append({
            "id":rid,"court_code":idf[0] if idf else "","case_year":idf[1] if len(idf)>1 else "",
            "word":idf[2] if len(idf)>2 else "","case_no":idf[3] if len(idf)>3 else "",
            "jdate":(f"{iddate[:4]}-{iddate[4:6]}-{iddate[6:8]}" if len(iddate)==8 else date),
            "court":tp["court"],"doctype":tp["doctype"],"title":title,"cause":cause,
            "size":size,"snippet":snip,
            "url":BASE+"data.aspx?ty=JD&id="+urllib.parse.quote(rid,safe='')+"&ot=in",
        })
    return rows

def scrape_law(kw):
    op=new_session()
    u1=BASE+"Default_AD.aspx"
    html=get(op,u1)
    fields={"__VIEWSTATE":hid(html,"__VIEWSTATE"),"__EVENTVALIDATION":hid(html,"__EVENTVALIDATION"),
      "__VIEWSTATEGENERATOR":hid(html,"__VIEWSTATEGENERATOR"),"__VIEWSTATEENCRYPTED":"",
      "jud_court":"","sel_judword":"","jud_sys":"","judtype":"","whosub":"0",
      "jud_kw":kw,"jud_year":"","jud_case":"","jud_no":"","jud_no_end":"",
      "jud_title":"","jud_jmain":"","dy1":DY1,"dm1":"","dd1":"","dy2":DY2,"dm2":"","dd2":"",
      "KbStart":"","KbEnd":"","ctl00$cp_content$btnQry":"送出查詢"}
    r=post(op,u1,fields,u1)
    m=re.search(r'qryresultlst\.aspx\?ty=JUDBOOK&q=([0-9a-f]+)',r)
    if not m:
        print(f"  [{kw}] NO query hash returned",file=sys.stderr); return []
    q=m.group(1)
    lst=BASE+f"qryresultlst.aspx?ty=JUDBOOK&q={q}"
    p1=get(op,lst,u1)
    mc=re.search(r'共\s*([\d,]+)\s*筆',p1)
    count=int(mc.group(1).replace(',','')) if mc else 0
    pages=max(1,math.ceil(count/PER))
    print(f"  [{kw}] count={count} pages={pages}",file=sys.stderr)
    allrows=parse_page(p1)
    for pg in range(2,pages+1):
        purl=BASE+f"qryresultlst.aspx?q={q}&sort=DS&page={pg}"
        pg_html=get(op,purl,lst)
        rr=parse_page(pg_html)
        allrows+=rr
        if pg%10==0: print(f"    ..page {pg}/{pages} total_rows={len(allrows)}",file=sys.stderr)
        time.sleep(0.6)
    print(f"  [{kw}] parsed_rows={len(allrows)} (expected {count})",file=sys.stderr)
    return count,allrows

if __name__=="__main__":
    only=sys.argv[1] if len(sys.argv)>1 else None
    laws=[only] if only else LAWS
    out={}
    for kw in laws:
        cnt,rows=scrape_law(kw)
        out[kw]={"count":cnt,"rows":rows}
        time.sleep(1)
    json.dump(out,open("raw_%s.json"%(only or "all"),"w",encoding="utf-8"),ensure_ascii=False)
    print("DONE laws=",list(out.keys()),"total parsed=",sum(len(v["rows"]) for v in out.values()))
