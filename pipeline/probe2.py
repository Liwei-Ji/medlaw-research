#!/usr/bin/env python3
import urllib.request, urllib.parse, http.cookiejar, re

BASE="https://judgment.judicial.gov.tw/FJUD/"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
cj=http.cookiejar.CookieJar()
op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def get(url,ref=None):
    hd={"User-Agent":UA,"Accept-Language":"zh-TW"}
    if ref: hd["Referer"]=ref
    return op.open(urllib.request.Request(url,headers=hd),timeout=60).read().decode('utf-8','replace')
def post(url,fields,ref):
    body=urllib.parse.urlencode(fields).encode()
    return op.open(urllib.request.Request(url,data=body,headers={"User-Agent":UA,"Content-Type":"application/x-www-form-urlencoded","Referer":ref,"Accept-Language":"zh-TW"}),timeout=60).read().decode('utf-8','replace')

url1=BASE+"Default_AD.aspx"
html=get(url1)
def hid(n):
    m=re.search(r'id="%s"[^>]*value="([^"]*)"'%re.escape(n),html); return m.group(1) if m else ""
fields={"__VIEWSTATE":hid("__VIEWSTATE"),"__EVENTVALIDATION":hid("__EVENTVALIDATION"),
 "__VIEWSTATEGENERATOR":hid("__VIEWSTATEGENERATOR"),"__VIEWSTATEENCRYPTED":"",
 "jud_court":"","sel_judword":"","jud_sys":"","judtype":"","whosub":"0",
 "jud_kw":"藥師法","jud_year":"","jud_case":"","jud_no":"","jud_no_end":"",
 "jud_title":"","jud_jmain":"","dy1":"112","dm1":"","dd1":"","dy2":"115","dm2":"","dd2":"",
 "KbStart":"","KbEnd":"","ctl00$cp_content$btnQry":"送出查詢"}
r=post(url1,fields,url1)
m=re.search(r'(qryresultlst\.aspx\?ty=JUDBOOK&q=[0-9a-f]+)',r)
lst=BASE+m.group(1)
print("LIST URL:",lst)
page=get(lst,url1)
open("list1.html","w",encoding="utf-8").write(page)
print("list len",len(page))
mc=re.search(r'共\s*([\d,]+)\s*筆',page)
print("COUNT:", mc.group(0) if mc else "??")
# find pagination and item links
print("--- data.aspx links (first 5) ---")
for i,mm in enumerate(re.finditer(r'(data\.aspx\?[^"\'\s>]+)',page)):
    print(mm.group(1)[:120])
    if i>=4: break
# find how pages requested: look for OpenPage / page param / GetResult ajax
for pat in [r'id="hlLast"[^>]*href="([^"]+)"', r'page=\d+', r'OpenPage\([^)]*\)', r'jrecno', r'qryresultlst\.aspx\?[^"\']+']:
    ms=re.findall(pat,page)
    if ms: print("PAT",pat,"->",ms[:4])
