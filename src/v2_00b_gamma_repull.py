"""v2 step 1a (repair): 3-day windows that hit the 2,000-row offset cap (95 of 224) are re-pulled in 1-day windows,
ordered by volumeNum descending, stopping when volume < 20k. Raw -> data/raw/v2_gamma_vol/."""
import json, glob, datetime as dt
from concurrent.futures import ThreadPoolExecutor
from common import *
out = RAW / "v2_gamma_vol"; out.mkdir(exist_ok=True)
capped = [f for f in sorted(glob.glob(str(RAW / "v2_gamma" / "*.json"))) if len(json.load(open(f))) >= 1900]
days = []
for f in capped:
    d = dt.date.fromisoformat(Path(f).stem)
    days += [d + dt.timedelta(days=i) for i in range(3)]
def one(d):
    f = out / f"{d}.json"
    if f.exists(): return d, len(json.load(open(f))), False
    rows, hit_cap = [], False
    for off in range(0, 2100, 100):
        try:
            r = get_json(GAMMA + "/markets", params=dict(closed="true", limit=100, offset=off, order="volumeNum", ascending="false",
                         end_date_min=str(d), end_date_max=str(d + dt.timedelta(days=1))))
        except Exception as ex:
            hit_cap = off >= 2000; break
        rows += r
        if len(r) < 100 or float(r[-1].get("volumeNum") or 0) < 20000: break
    else: hit_cap = True
    dump(rows, f); return d, len(rows), hit_cap
with ThreadPoolExecutor(6) as ex: res = list(ex.map(one, days))
print(len(days), "days;", sum(n for _, n, _ in res), "rows; cap hit:", [str(d) for d, _, h in res if h])
