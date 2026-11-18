"""v2 step 1a: pull all closed Gamma markets with volume >= 20k, endDate 2025-01..2026-10, in weekly windows.
Raw -> data/raw/v2_gamma/*.json. Selection by category happens in v2_01_markets.py (text only)."""
import json, datetime as dt
from common import *
out = RAW / "v2_gamma"; out.mkdir(exist_ok=True)
d0, d1 = dt.date(2025,1,1), dt.date(2026,11,3)
w = d0; allm = []; capped = []
while w < d1:
    e = w + dt.timedelta(days=3)
    f = out / f"{w}.json"
    if f.exists():
        rows = json.load(open(f))
    else:
        rows = []
        for off in range(0, 2000, 100):
            try:
                r = get_json(GAMMA + "/markets", params=dict(closed="true", limit=100, offset=off, volume_num_min=20000,
                             end_date_min=str(w), end_date_max=str(e)))
            except Exception as ex:
                capped.append((str(w), off, str(ex)[:80])); break
            rows += r
            if len(r) < 100: break
        dump(rows, f)
    if len(rows) >= 1900: capped.append((str(w), "near cap", len(rows)))
    allm += rows; w = e
print(len(allm), "rows; cap/err events:", capped)
dump(allm, RAW / "v2_gamma_all.json")
