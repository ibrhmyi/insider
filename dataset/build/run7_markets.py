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

D = os.path.join(os.path.dirname(__file__), "..")
CASE = "tweet-count-self-2026-03"
mk = pd.read_csv(os.path.join(D, "data", "markets.csv"), dtype=str, keep_default_na=False)
mk = mk[mk.case_id != CASE]
for col in ["title_withheld", "t_news_precise_utc", "t_news_precise_precision", "t_news_precise_source", "t_news_precise_verified"]:
    if col in mk.columns:
        mk = mk.drop(columns=col)
mk["title_withheld"] = "false"
if len(sys.argv) > 1:
    c = duckdb.connect()
    cat = c.execute(f"""SELECT condition_id, string_agg(asset_id, ';' ORDER BY outcome_seq) token_ids,
                               string_agg(outcome_label, ';' ORDER BY outcome_seq) outcomes, any_value(winning_outcome_label) outcome,
                               min(opens_at) opens_at, max(close_at) close_at, max(resolved_at) resolved_at, any_value(neg_risk) neg_risk,
                               sum(usdc_volume) vol
                        FROM '{D}/out/hf_market_catalog.parquet'
                        WHERE market_slug LIKE ? AND close_at BETWEEN '2026-02-01' AND '2026-03-10 23:59:59+00'
                        GROUP BY condition_id ORDER BY close_at, condition_id""", [sys.argv[1]]).df()
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
mk = mk.sort_values(["case_id", "condition_id"]).reset_index(drop=True)
mk.to_csv(os.path.join(D, "data", "markets.csv"), index=False)
print(mk.groupby("case_id")[["t_news_utc", "t_news_precise_utc", "t_news_precise_precision"]].first().query("t_news_precise_precision != 'day_fallback'").to_string())
