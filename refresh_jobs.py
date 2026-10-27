#!/usr/bin/env python3
"""Rebuild jobs.json from the ICH ATS XML feed (apply URLs carry the ICH source code suon7RAzw4M=).
Pay is not in the feed, so it is joined by job code from the public board scrape. Refuses to publish if fewer than 300 jobs."""
import re,html,json,urllib.request,datetime,os,sys,concurrent.futures as cf
BASE="https://staffmyagency.com/Main/JobSearch?Page=%d"
def get(u):
    r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 ICH-refresh"})
    return urllib.request.urlopen(r,timeout=30).read().decode("utf-8","replace")
def clean(s): return re.sub(r"\s+"," ",html.unescape(re.sub("<[^>]+>"," ",s))).strip()
def jtype(t,d):
    t=t.lower()
    if re.search(r"customer service|csr|service rep|account manager|service lead|office|admin|receptionist|assistant|retention|customer care|operations",t): return "Customer Service"
    if re.search(r"sales|producer|agent|marketing|telemarket|account executive|business development",t): return "Sales"
    if re.search(r"claim",t): return "Claims"
    if re.search(r"team member|representative|associate|specialist",t): return "Sales & Service"
    return "Other"
def lic(t,d):
    s=(t+" "+d).lower()
    if re.search(r"not required|no experience|will train|willing(ness)? to (obtain|get)|able to obtain|obtain within|we will help you get|paid licens|license(s)? (is |are )?(a plus|preferred)",s): return "no-experience"
    if re.search(r"licensed|license required|active .{0,30}licen|must (have|hold) .{0,30}licen|licen\w* required",s): return "licensed"
    return "either"
def parse(t):
    out=[]
    for c in t.split('<div class="glass-card card mb-3')[1:]:
        m=re.search(r'href="(https://staffmyagency.com/Main/ApplyForJob/([^/"]+)/[^"]*)">(.*?)<span[^>]*>\((.*?)\)</span>',c,re.S)
        if not m: continue
        url,jid,title,loc=m.groups()
        pay=re.search(r'fw-bold text-danger">(.*?)</span>',c,re.S); pay=clean(pay.group(1)) if pay else ""
        d=re.search(r'text-justify">(.*?)</div>',c,re.S); d=clean(d.group(1)) if d else ""
        ag=re.search(r'by <span class="text-danger">(.*?)</span>',c,re.S); ag=re.sub(r"\s+in\s*,?\s*,?\s*$","",clean(ag.group(1))) if ag else ""
        p=[x.strip() for x in loc.split(",")]; title=clean(title)
        out.append(dict(id=jid,title=title,agency=ag,city=p[0].title(),state=(p[1] if len(p)>1 else "").upper(),
            pay=pay,summary=(d[:240].rsplit(" ",1)[0]+"…") if len(d)>240 else d,type=jtype(title,d),experience=lic(title,d),apply_url=url.split("?")[0]))
    return out
def excluded(j):  # same exclusion as Job Content Studio (gen26.py)
    return "jantz" in j["agency"].lower() or "edmond" in j["city"].lower()
import xml.etree.ElementTree as ET
FEED="https://staffmyagency.com/Main/XMLJobFeed?Feed=ICH"
# Scrape board only for pay (not in feed); failures here are non-fatal
pay={}
try:
    first=get(BASE%1); pages=max([int(x) for x in re.findall(r"Page=(\d+)",first)]+[1])
    with cf.ThreadPoolExecutor(8) as ex: htmls=[first]+list(ex.map(lambda n:get(BASE%n),range(2,pages+1)))
    for h in htmls:
        for j in parse(h): pay[j["id"]]=j["pay"]
except Exception as e: print("board scrape failed (pay blank):",e,file=sys.stderr)
root=ET.fromstring(get(FEED).strip().encode())
jobs={}
for x in root.iter("job"):
    g=lambda k:(x.findtext(k) or "").strip()
    url=g("url"); m=re.search(r"/ApplyForJob/([^/]+)/",url)
    if not m or not url.endswith("/suon7RAzw4M="): continue
    jid=m.group(1); title=clean(g("title")); d=clean(g("description"))
    j=dict(id=jid,title=title,agency=clean(g("company")),city=clean(g("city")).title(),state=g("state").upper(),
        pay=pay.get(jid,""),summary=(d[:240].rsplit(" ",1)[0]+"\u2026") if len(d)>240 else d,
        type=jtype(title,d),experience=lic(title,d),apply_url=url)
    if not excluded(j): jobs[jid]=j
if len(jobs)<300: sys.exit(f"Only {len(jobs)} jobs found; keeping existing jobs.json")
out=os.path.join(os.path.dirname(os.path.abspath(__file__)),"jobs.json")
json.dump(dict(updated=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),count=len(jobs),jobs=sorted(jobs.values(),key=lambda j:(j["state"],j["city"]))),open(out+".tmp","w"),separators=(",",":"))
os.replace(out+".tmp",out); print(f"{len(jobs)} jobs from feed ({sum(1 for j in jobs.values() if j['pay'])} with pay) -> {out}")
