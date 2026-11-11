"""Task 2 helper (added after SOL control failed): screen control candidates for trade-feed
completeness and for 'contested' trading (price in [0.02, 0.98]).
usage: python 00b_screen_controls.py <gamma_id> ..."""
import json, sys, time
from common import DATA_API, GAMMA, RAW, dump, get_json, parse_ts, iso

def pull(cond, taker):
    rows, cur = [], None
    while True:
        p = dict(condition=cond, limit=1000, taker_only=taker) if cur is None else dict(condition=cond, cursor=cur, taker_only=taker)
        js = get_json(f"{DATA_API}/trades", params=p); rows += js.get("data") or []
        cur = (js.get("pagination") or {}).get("next_cursor")
        if not (js.get("pagination") or {}).get("has_more") or not cur: return rows
        time.sleep(0.2)

out = {}
for gid in sys.argv[1:]:
    m = get_json(f"{GAMMA}/markets/{gid}")
    t = pull(m["conditionId"], "true"); a = pull(m["conditionId"], "false")
    vol = float(m["volumeNum"]); op = parse_ts(m["startDate"])
    tn = sum(x["size"] * x["price"] for x in t)
    yes_p = [(x["price"] if x["outcome_index"] == 0 else 1 - x["price"], x["size"] * x["price"]) for x in t]
    contested = sum(n for p, n in yes_p if 0.02 <= p <= 0.98) / tn if tn else 0
    r = dict(gid=gid, q=m["question"], vol=vol, taker_rows=len(t),
             first_trade_h_after_open=round((min(x["timestamp"] for x in t) - op) / 3600, 1) if t else None,
             all_sides_ratio=round(sum(x["size"] * x["price"] for x in a) / vol, 3),
             contested_share=round(contested, 3))
    out[gid] = r; print(r, flush=True)
dump(out, RAW / f"control_screen_{'_'.join(sys.argv[1:])}.json")
