"""Cut times per (market_set, case_id, condition_id, t_news_version): case markets use the per-market cut (A25), placebo and twin
markets their t_ref (A14, A22). Shared by positions.py and directional.py (A34.2)."""
import os
import pandas as pd


def build_cuts(D):
    ts = lambda s: pd.to_datetime(s.replace("", None), utc=True, errors="coerce", format="mixed")
    ep = lambda s: (ts(s) - pd.Timestamp("1970-01-01", tz="UTC")).dt.total_seconds().round().astype("Int64")
    mk = pd.read_csv(os.path.join(D, "data", "markets.csv"), dtype=str, keep_default_na=False)
    mk["condition_id"] = mk.condition_id.str.lower()
    # Yes token = outcome 'Yes', else the first listed outcome (frozen v1 YES-direction convention)
    mk["yes_label"] = mk.outcomes.map(lambda s: "Yes" if "Yes" in s.split(";") else (s.split(";")[0] if s else ""))
    lad = mk.copy(); lad["lr"] = pd.to_numeric(lad.ladder_rank, errors="coerce")
    yes_res = lad[lad.outcome.str.lower().eq("yes") & lad.lr.notna()]
    short = set(map(tuple, yes_res.loc[yes_res.groupby(["case_id", "event_id"]).lr.idxmin(), ["case_id", "condition_id"]].values))
    rows = []
    for r in mk.itertuples():
        for v, col in [("day", "t_news_market_day_utc"), ("precise", "t_news_market_utc")]:
            rows.append(dict(market_set="case", case_id=r.case_id, condition_id=r.condition_id, t_news_version=v, t_cut=getattr(r, col),
                             event_id=r.event_id, yes_label=r.yes_label, is_shortest_sufficient=(r.case_id, r.condition_id) in short,
                             winning_outcome=r.outcome or None, resolved_utc=r.resolved_utc))
    pl = pd.read_csv(os.path.join(D, "data", "placebo_markets.csv"), dtype=str, keep_default_na=False)
    pl = pl[pl.placebo_condition_id != ""]
    for r in pl.itertuples():
        outs = r.placebo_outcomes.split(";")
        for v in ["day", "precise"]:
            rows.append(dict(market_set="placebo", case_id=r.case_id, condition_id=r.placebo_condition_id, t_news_version=v,
                             t_cut=getattr(r, f"t_ref_{v}_utc"), event_id=None, yes_label="Yes" if "Yes" in outs else outs[0],
                             is_shortest_sufficient=False, winning_outcome=r.placebo_outcome, resolved_utc=r.placebo_end_utc))
    tw = pd.read_csv(os.path.join(D, "data", "twin_markets.csv"), dtype=str, keep_default_na=False)
    tw = tw[tw.twin_condition_id != ""]
    for r in tw.itertuples():  # A22: twin markets, cut at t_ref
        outs = r.twin_outcomes.split(";")
        for v in ["day", "precise"]:
            rows.append(dict(market_set="twin", case_id=r.case_id, condition_id=r.twin_condition_id, t_news_version=v,
                             t_cut=getattr(r, f"t_ref_{v}_utc"), event_id=None, yes_label="Yes" if "Yes" in outs else outs[0],
                             is_shortest_sufficient=False, winning_outcome=r.twin_outcome, resolved_utc=r.twin_end_utc))
    M = pd.DataFrame(rows); M["t_cut_ts"] = ep(M.t_cut); M["resolved_ts"] = ep(M.resolved_utc)
    return M, mk
