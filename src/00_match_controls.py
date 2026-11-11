"""Task 2 helper: rank candidate insider-impossible control markets for each target (score in data/control_match_table.md)."""
import json,requests,re,time,math
from datetime import datetime,timedelta,timezone
def ts(s): return datetime.fromisoformat(s.replace(' ','T').replace('Z','+00:00').replace('+00','+00:00') if not s.endswith('+00:00') else s).timestamp()
def closed_ts(m): 
    s=m['closedTime'].replace(' ','T'); s=s if s.endswith('+00:00') else s.replace('+00','+00:00'); return datetime.fromisoformat(s).timestamp()
def gm(lo,hi):
    out=[];off=0
    while off<2000:
        r=requests.get("https://gamma-api.polymarket.com/markets",params=dict(closed="true",end_date_min=lo,end_date_max=hi,limit=100,offset=off,order="volumeNum",ascending="false"),timeout=60)
        if r.status_code==422: break
        r.raise_for_status(); d=r.json(); out+=d
        if len(d)<100: break
        off+=100
    return out
def stats(m):
    tok=json.loads(m['clobTokenIds'])[0]
    js=requests.get("https://data-api.polymarket.com/v2/prices-history",params=dict(token_id=tok,interval="max",bucket_seconds=10800),timeout=60).json()
    end=closed_ts(m); ps=[p['price'] for p in (js.get('data') or []) if p['timestamp']<end-3*3600]
    if not ps: return None
    ps=sorted(ps); return dict(pmin=ps[0],pmax=ps[-1],pmed=ps[len(ps)//2],n=len(ps))
targets={'554012':'2025-06-22','560868':'2025-10-10','916440':'2026-01-03'}
used=set(); res={}
for mid,d in targets.items():
    t=requests.get(f"https://gamma-api.polymarket.com/markets/{mid}",timeout=60).json(); ts_=stats(t); tv=float(t['volumeNum'])
    day=datetime.fromisoformat(d+"T00:00:00+00:00")
    ms=gm((day-timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"),(day+timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"))
    c=[m for m in ms if re.search(r"(Bitcoin|Ethereum|Solana|XRP).*(above)",m.get('question',''),re.I) and float(m.get('volumeNum') or 0)>2e5]
    c.sort(key=lambda m:-float(m['volumeNum'])); c=c[:40]
    rows=[]
    for m in c:
        s=stats(m); time.sleep(0.15)
        if not s: continue
        dd=abs(closed_ts(m)-closed_ts(t))/86400
        score=abs(math.log(float(m['volumeNum'])/tv))+5*abs(s['pmed']-ts_['pmed'])+0.1*dd
        rows.append((score,m['id'],m['question'],float(m['volumeNum']),s,dd,m['conditionId']))
    rows.sort()
    print(f"===== TARGET {mid} {t['question']} vol {tv/1e6:.2f}M pre-res {ts_}  candidates={len(rows)}")
    for r in rows[:6]: print(f"  score {r[0]:.3f} | {r[1]} | {r[2][:58]:58s} | {r[3]/1e6:.2f}M | med {r[4]['pmed']:.3f} [{r[4]['pmin']:.3f},{r[4]['pmax']:.3f}] | {r[5]:.1f}d")
    res[mid]=[dict(score=r[0],id=r[1],q=r[2],vol=r[3],**r[4],days=r[5],cond=r[6]) for r in rows[:6]]
    res[mid+'_target']=dict(vol=tv,**ts_)
import pathlib; json.dump(res,open(pathlib.Path(__file__).resolve().parents[1]/'data/raw/control_match_candidates.json','w'),indent=1)
