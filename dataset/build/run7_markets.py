"""Run 7: markets.csv additions (PROTOCOL A10, A12.6).

1. A12.6: attaches the weekly post-count markets of case tweet-count-self-2026-03 by condition_id only. The slug pattern
   that finds them names the subject, so it is given on the command line and never stored (argv[1], a SQL LIKE pattern
   on the Polymarket-v1 catalog slug); question, slug and event slug stay NULL and title_withheld = true.
   Selection: catalog markets matching the pattern with close_at between 2026-02-01 and 2026-03-10 23:59:59 UTC.
2. A10: adds t_news_precise_utc / _precision / _source / _verified from data/event_times.csv to every row.
Idempotent: withheld rows are rebuilt each run. Usage: python3 build/run7_markets.py '<like pattern>'
"""
import os, sys
import duckdb, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))

D = os.path.join(os.path.dirname(__file__), "..")
CASE = "tweet-count-self-2026-03"
mk = pd.read_csv(os.path.join(D, "data", "markets.csv"), dtype=str, keep_default_na=False)
mk = mk[mk.case_id != CASE]
for col in ["title_withheld", "t_news_precise_utc", "t_news_precise_precision", "t_news_precise_source", "t_news_precise_verified"]:
    if col in mk.columns:
        mk = mk.drop(columns=col)
mk["title_withheld"] = "false"
PATTERN = sys.argv[1] if len(sys.argv) > 1 else None
if PATTERN:
    c = duckdb.connect()
    cat = c.execute(f"""SELECT condition_id, string_agg(asset_id, ';' ORDER BY outcome_seq) token_ids,
                               string_agg(outcome_label, ';' ORDER BY outcome_seq) outcomes, any_value(winning_outcome_label) outcome,
                               min(opens_at) opens_at, max(close_at) close_at, max(resolved_at) resolved_at, any_value(neg_risk) neg_risk,
                               sum(usdc_volume) vol
                        FROM '{D}/out/hf_market_catalog.parquet'
                        WHERE market_slug LIKE ? AND close_at BETWEEN '2026-02-01' AND '2026-03-10 23:59:59+00'
                        GROUP BY condition_id ORDER BY close_at, condition_id""", [PATTERN]).df()
    f = lambda t: pd.Timestamp(t).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ") if pd.notna(t) else ""
    rows = [dict(case_id=CASE, condition_id=r.condition_id.lower(), question="", slug="", event_id="withheld-week-" + f(r.close_at)[:10],
                 event_slug="", series_id="", selected_as="withheld_pattern:A12.6", found_via="hf_slug_withheld",
                 reason="subject's weekly post-count market ending 2026-02-01..2026-03-10 (A12.6); title withheld (PROTOCOL 9)",
                 selection_level="event", created_utc=f(r.opens_at), deadline_utc=f(r.close_at), resolved_utc=f(r.resolved_at),
                 outcome=r.outcome or "", outcomes=r.outcomes, token_ids=r.token_ids, neg_risk=str(bool(r.neg_risk)), volume_gamma="",
                 volume_hf_usdc=str(round(r.vol, 2)), in_hf="True", ladder_rank="", t_news_utc="2026-02-01T00:00:00Z",
                 t_news_method="claim_min", t_news_precision="range", ff_tier="", ff_tier2_tnews="", title_withheld="true")
            for r in cat.itertuples()]
    mk = pd.concat([mk, pd.DataFrame(rows)], ignore_index=True)
    print("withheld markets attached:", len(rows))
# --- run-7 new cases (A6.5): Gamma events named by the claims
NEW_EVENTS = {"nvidia-ceo-return-2026-11": [("jensen-huang-rejoins-nvidia-byptptpt", "gamma_search",
              "claims name the CEO-return markets ('a Dec. 31 return', 'the November contract')")]}
import json, csv as _csv
sys.argv = sys.argv[:1] + ["/nonexistent"]  # build_markets reads argv[1] only for its ForesightFlow path
import build_markets as BM
from dates import parse_date
claims = list(_csv.DictReader(open(os.path.join(D, "data", "claims.csv"))))
mk = mk[~mk.case_id.isin(NEW_EVENTS)]
new = []
for case, specs in NEW_EVENTS.items():
    cl = [x for x in claims if x["case_id"] == case]
    ev = [parse_date(x["event_date"]) for x in cl]; cd = [parse_date(x["claim_date"]) for x in cl]
    cand = sorted([d for d in ev + cd if d[0] and d[1] == "day"] + ([d for d in ev if d[0]] if not any(d[1] == "day" for d in ev) else []))
    tn_day, tn_prec = cand[0] if cand else ("", "")
    for slug, via, why in specs:
        e = BM.event_by_slug(slug)
        ms = e.get("markets") or []; ends = sorted({(m.get("endDate") or "") for m in ms})
        for m in ms:
            outs, prices = json.loads(m.get("outcomes") or "[]"), json.loads(m.get("outcomePrices") or "[]")
            new.append(dict(case_id=case, condition_id=m["conditionId"].lower(), question=m.get("question", ""), slug=m.get("slug", ""),
                event_id=e.get("id", ""), event_slug=e.get("slug", ""), series_id="", selected_as=f"event:{slug}", found_via=via, reason=why,
                selection_level="event", created_utc=m.get("createdAt", ""), deadline_utc=m.get("endDate", ""), resolved_utc=m.get("closedTime") or "",
                outcome=(outs[prices.index("1")] if "1" in prices and m.get("closed") else ""), outcomes=";".join(outs),
                token_ids=";".join(json.loads(m.get("clobTokenIds") or "[]")), neg_risk=str(m.get("negRisk", "")), volume_gamma=str(m.get("volume", "")),
                volume_hf_usdc="", in_hf="False", ladder_rank=str(ends.index(m.get("endDate") or "") + 1) if len(ends) > 1 else "",
                t_news_utc=tn_day + "T00:00:00Z", t_news_method="claim_min", t_news_precision=tn_prec, ff_tier="", ff_tier2_tnews="", title_withheld="false"))
mk = pd.concat([mk, pd.DataFrame(new)], ignore_index=True)
print("new-case markets:", len(new))
# --- A10 precise times
et = pd.read_csv(os.path.join(D, "data", "event_times.csv"), dtype=str, keep_default_na=False)
ok = et[et.t_precision.isin(["minute", "approx_15min", "approx_hour"]) | et.t_precision.str.startswith("window_")]
ok = ok[ok.url.str.len() > 0].copy()
ok["t"] = pd.to_datetime(ok.t_utc, utc=True)
best = ok.sort_values("t").groupby("case_id").first()
prec = {"minute": "minute", "approx_15min": "quarter_hour", "approx_hour": "hour"}
def pp(p): return prec.get(p, "window" if p.startswith("window_") else p)
mk["t_news_precise_utc"] = [best.loc[c, "t"].strftime("%Y-%m-%dT%H:%M:%SZ") if c in best.index else t for c, t in zip(mk.case_id, mk.t_news_utc)]
mk["t_news_precise_precision"] = [pp(best.loc[c, "t_precision"]) if c in best.index else "day_fallback" for c in mk.case_id]
mk["t_news_precise_source"] = [best.loc[c, "url"] if c in best.index else "day_fallback" for c in mk.case_id]
mk["t_news_precise_verified"] = [best.loc[c, "verified"] if c in best.index else "" for c in mk.case_id]
# A12.7: withhold any title that names a person on the name-test list (hashes of lower-cased 1-3 word n-grams)
import hashlib, re
NH = {x.strip() for x in open(os.path.join(D, "tests", "name_hashes.txt")) if x.strip() and not x.startswith("#")}
def names_person(*vals):
    for v in vals:
        w = re.findall(r"[a-z]+", (v or "").lower())
        if any(hashlib.sha256(" ".join(w[i:i + n]).encode()).hexdigest() in NH for n in (1, 2, 3) for i in range(len(w) - n + 1)):
            return True
    return False
hit = [names_person(q, s_, e) for q, s_, e in zip(mk.question, mk.slug, mk.event_slug)]
mk.loc[hit, "title_withheld"] = "true"
for col in ["question", "slug", "event_slug"]:
    mk.loc[mk.title_withheld == "true", col] = ""
print("A12.7 titles withheld:", sum(hit))
mk = mk.sort_values(["case_id", "condition_id"]).reset_index(drop=True)
mk.to_csv(os.path.join(D, "data", "markets.csv"), index=False)
print(mk.groupby("case_id")[["t_news_utc", "t_news_precise_utc", "t_news_precise_precision"]].first().query("t_news_precise_precision != 'day_fallback'").to_string())
