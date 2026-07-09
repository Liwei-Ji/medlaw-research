#!/usr/bin/env python3
import urllib.request, urllib.parse, http.cookiejar, re, sys, gzip, io

BASE="https://judgment.judicial.gov.tw/FJUD/"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

cj=http.cookiejar.CookieJar()
op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), urllib.request.HTTPRedirectHandler())

def get(url):
    req=urllib.request.Request(url, headers={"User-Agent":UA,"Accept-Language":"zh-TW"})
    r=op.open(req, timeout=40)
    data=r.read()
    return r.geturl(), r.getcode(), data.decode('utf-8','replace')

def post(url, fields, referer):
    body=urllib.parse.urlencode(fields).encode()
    req=urllib.request.Request(url, data=body, headers={
        "User-Agent":UA,"Content-Type":"application/x-www-form-urlencoded",
        "Referer":referer,"Accept-Language":"zh-TW"})
    r=op.open(req, timeout=60)
    return r.geturl(), r.getcode(), r.read().decode('utf-8','replace')

# Step 1: GET advanced form
url1=BASE+"Default_AD.aspx"
u,c,html=get(url1)
print("GET",c,u)
def hid(name):
    m=re.search(r'id="%s"[^>]*value="([^"]*)"'%re.escape(name),html)
    return m.group(1) if m else ""
vs=hid("__VIEWSTATE"); ev=hid("__EVENTVALIDATION"); vg=hid("__VIEWSTATEGENERATOR")
print("tokens",len(vs),len(ev),vg)
print("cookies",[ck.name for ck in cj])

# Step 2: POST search for one law with date range 112-115
fields={
 "__VIEWSTATE":vs,"__EVENTVALIDATION":ev,"__VIEWSTATEGENERATOR":vg,
 "__VIEWSTATEENCRYPTED":"",
 "jud_court":"","sel_judword":"","jud_sys":"","judtype":"",
 "whosub":"0",
 "jud_kw":"藥師法",
 "jud_year":"","jud_case":"","jud_no":"","jud_no_end":"",
 "jud_title":"","jud_jmain":"",
 "dy1":"112","dm1":"","dd1":"","dy2":"115","dm2":"","dd2":"",
 "KbStart":"","KbEnd":"",
 "ctl00$cp_content$btnQry":"送出查詢",
}
u2,c2,html2=post(url1, fields, url1)
print("POST",c2,u2, "len",len(html2))
# Look for count / redirect target
m=re.search(r'共\s*([\d,]+)\s*筆',html2)
print("count in body:", m.group(0) if m else "no count")
# save
open("probe_post.html","w",encoding="utf-8").write(html2)
print("first 500:", html2[:500].replace("\n"," "))
