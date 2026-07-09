#!/usr/bin/env python3
import urllib.request, urllib.parse, http.cookiejar, re, time, sys
BASE="https://judgment.judicial.gov.tw/FJUD/"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
def sess(): return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def get(op,u,ref=None):
    hd={"User-Agent":UA,"Accept-Language":"zh-TW"}
    if ref:hd["Referer"]=ref
    return op.open(urllib.request.Request(u,headers=hd),timeout=60).read().decode('utf-8','replace')
def post(op,u,f,ref):
    return op.open(urllib.request.Request(u,data=urllib.parse.urlencode(f).encode(),headers={"User-Agent":UA,"Content-Type":"application/x-www-form-urlencoded","Referer":ref}),timeout=90).read().decode('utf-8','replace')
def hid(h,n):
    m=re.search(r'id="%s"[^>]*value="([^"]*)"'%re.escape(n),h);return m.group(1) if m else ""
def count_for(kw, field):
    op=sess();u1=BASE+"Default_AD.aspx";h=get(op,u1)
    f={"__VIEWSTATE":hid(h,"__VIEWSTATE"),"__EVENTVALIDATION":hid(h,"__EVENTVALIDATION"),
       "__VIEWSTATEGENERATOR":hid(h,"__VIEWSTATEGENERATOR"),"__VIEWSTATEENCRYPTED":"",
       "jud_court":"","sel_judword":"","jud_sys":"","judtype":"","whosub":"0",
       "jud_kw":"","jud_year":"","jud_case":"","jud_no":"","jud_no_end":"",
       "jud_title":"","jud_jmain":"","dy1":"112","dm1":"","dd1":"","dy2":"115","dm2":"","dd2":"",
       "KbStart":"","KbEnd":"","ctl00$cp_content$btnQry":"送出查詢"}
    f[field]=kw
    r=post(op,u1,f,u1)
    m=re.search(r'qryresultlst\.aspx\?ty=JUDBOOK&q=([0-9a-f]+)',r)
    if not m: return None
    p=get(op,BASE+"qryresultlst.aspx?ty=JUDBOOK&q="+m.group(1),u1)
    mc=re.search(r'共\s*([\d,]+)\s*筆',p)
    return int(mc.group(1).replace(',','')) if mc else 0
LAWS=["藥事法","醫療器材管理法","醫療法","醫師法","藥師法"]
print("=== full-text (jud_kw) ===")
tot=0
for kw in LAWS:
    c=count_for(kw,"jud_kw");tot+=c or 0;print(f"{kw}\t{c}");time.sleep(1)
print("TOTAL(full-text, pre-dedup):",tot)
print("=== cause field (jud_title) '違反<law>' ===")
tot2=0
for kw in LAWS:
    c=count_for("違反"+kw,"jud_title");tot2+=c or 0;print(f"違反{kw}\t{c}");time.sleep(1)
print("TOTAL(cause-based):",tot2)
