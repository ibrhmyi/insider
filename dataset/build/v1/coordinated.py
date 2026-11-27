"""PROTOCOL A13: coordinated-buyer candidates and their placebo-window false-positive rate, per t_news version.
Inputs: out/v1/fills/fills_case.parquet, data/markets.csv, data/wallet_labels.csv (trade_confirmed), <hf_pass_work>/P,
Gamma public profiles (fetched with build/pull_profiles.py into logs/gamma_raw/profile_<address>.json).
Outputs: data/coordinated_candidates.csv (one row per candidate x trigger x version), logs/coordinated_placebo.json.
Usage: python3 build/v1/coordinated.py <hf_pass_work_dir> <tmp_dir>
"""
import json, os, subprocess, sys
import duckdb, numpy as np, pandas as pd

D = os.path.join(os.path.dirname(__file__), "..", "..")
WORK, TMPD = sys.argv[1:3]
F = os.path.join(D, "out", "v1", "fills", "fills_case.parquet")
RAW = os.path.join(D, "logs", "gamma_raw")
SEED, WIN, AGE = 192, 600, 14 * 86400
c = duckdb.connect(); c.sql(f"SET memory_limit='10GB'; SET temp_directory='{TMPD}'; SET enable_progress_bar=false")
ep = lambda s: (pd.to_datetime(s.replace("", None), utc=True, errors="coerce", format="mixed") - pd.Timestamp("1970-01-01", tz="UTC")).dt.total_seconds().round().astype("Int64")
mk = pd.read_csv(os.path.join(D, "data", "markets.csv"), dtype=str, keep_default_na=False); mk["condition_id"] = mk.condition_id.str.lower()
W = pd.read_csv(os.path.join(D, "data", "wallet_labels.csv"), dtype=str, keep_default_na=False)
doc = W[(W.polarity == "suspected") & (W.trade_confirmed.str.lower() == "true") & (W.label_family == "informed_trading")]  # A19[["address", "case_id"]].drop_duplicates()
labelled = sorted(set(W[W.label_tier != "L4_coordinated"].address))
M = pd.concat([mk.assign(t_news_version=v, t_cut=ep(mk[col]))[["case_id", "condition_id", "t_news_version", "t_cut"]]
               for v, col in [("day", "t_news_market_day_utc"), ("precise", "t_news_market_utc")]])
c.register("M_df", M); c.sql("CREATE TABLE M AS SELECT * FROM M_df")
c.register("doc_df", doc); c.sql("CREATE TABLE DOC AS SELECT address wallet, case_id FROM doc_df")
c.execute("CREATE TABLE LAB(a VARCHAR)"); c.executemany("INSERT INTO LAB VALUES (?)", [(a,) for a in labelled])
sys.path.insert(0, os.path.dirname(__file__)); from econ_view import legs_sql  # A34
c.sql(f"CREATE VIEW legs AS SELECT condition_id, asset_id, ts, usdc, wallet, wallet_side, leg_id FROM {legs_sql(F)} WHERE wallet_side = 'BUY' AND wallet IS NOT NULL")
c.sql("""CREATE TABLE TRIG AS SELECT l.leg_id trigger_leg_id, d.wallet trigger_wallet, m.case_id, l.condition_id, l.asset_id, l.ts trigger_ts,
          l.usdc trigger_usdc, m.t_news_version, m.t_cut FROM legs l JOIN DOC d ON d.wallet = l.wallet
          JOIN M m ON m.case_id = d.case_id AND m.condition_id = l.condition_id WHERE l.ts < m.t_cut""")
print("triggers", c.sql("SELECT t_news_version, count(*) FROM TRIG GROUP BY 1").fetchall(), flush=True)
# placebo window centres: 5 per trigger, uniform in [first fill in the market, t_cut - 600]
T = c.sql("SELECT * FROM TRIG ORDER BY t_news_version, trigger_leg_id").df()
ff = c.sql(f"SELECT condition_id, min(ts) first_ts FROM '{F}' GROUP BY 1").df().set_index("condition_id").first_ts
rng = np.random.default_rng(SEED); pw = []
for r in T.itertuples():
    lo, hi = int(ff.get(r.condition_id, r.trigger_ts)), int(r.t_cut) - WIN
    for k in range(5):
        if hi > lo:
            pw.append((f"{r.trigger_leg_id}|{r.t_news_version}|p{k}", r.trigger_leg_id, r.trigger_wallet, r.case_id, r.condition_id, r.asset_id,
                       int(rng.integers(lo, hi)), r.trigger_usdc, r.t_news_version, int(r.t_cut)))
PW = pd.DataFrame(pw, columns=["window_id", "trigger_leg_id", "trigger_wallet", "case_id", "condition_id", "asset_id", "trigger_ts", "trigger_usdc", "t_news_version", "t_cut"])
c.register("pw_df", PW); c.sql("CREATE TABLE PW AS SELECT * FROM pw_df")
c.sql("CREATE TABLE RW AS SELECT trigger_leg_id || '|' || t_news_version window_id, * FROM TRIG")


def hits(win):
    return c.sql(f"""SELECT w.window_id, w.trigger_leg_id, w.trigger_wallet, w.case_id, w.condition_id, w.asset_id, w.trigger_ts, w.trigger_usdc,
                          w.t_news_version, l.wallet, sum(l.usdc) cand_usdc, min(l.ts) cand_first_buy_ts, count(*) cand_n_legs
                   FROM {win} w JOIN legs l ON l.condition_id = w.condition_id AND l.asset_id = w.asset_id
                        AND l.ts BETWEEN w.trigger_ts - {WIN} AND w.trigger_ts + {WIN} AND l.ts < w.t_cut
                   WHERE l.wallet <> w.trigger_wallet AND l.wallet NOT IN (SELECT a FROM LAB)
                   GROUP BY ALL HAVING sum(l.usdc) BETWEEN 0.5 * w.trigger_usdc AND 2 * w.trigger_usdc""").df()


R, P = hits("RW"), hits("PW")
print("size/time matches real", len(R), "placebo", len(P), flush=True)
allw = sorted(set(R.wallet) | set(P.wallet))
c.execute("CREATE TABLE AW(a VARCHAR)"); c.executemany("INSERT INTO AW VALUES (?)", [(a,) for a in allw])
first = c.sql(f"SELECT wallet, min(first_ts) f FROM read_parquet('{WORK}/P/*.parquet') WHERE wallet IN (SELECT a FROM AW) GROUP BY 1").df().set_index("wallet").f
for X in (R, P):
    X["first_fill_v1_ts"] = X.wallet.map(first)
    X["prefilter_pass"] = X.first_fill_v1_ts.isna() | (X.first_fill_v1_ts >= X.trigger_ts - AGE)
need = sorted(set(R.loc[R.prefilter_pass, "wallet"]) | set(P.loc[P.prefilter_pass, "wallet"]))
lst = os.path.join(TMPD, "coord_profiles.txt"); open(lst, "w").write("\n".join(need))
print("profile lookups", len(need), flush=True)
PC = os.path.join(RAW, "profiles_created_run7.csv")  # run-7 lookups keep only address and createdAt (raw profiles not committed)
PCD = {r[0]: r[1] for r in pd.read_csv(PC, dtype=str, keep_default_na=False).values} if os.path.exists(PC) else {}
todo = [a for a in need if a not in PCD]
if todo:
    open(lst, "w").write("\n".join(todo)); subprocess.run([sys.executable, os.path.join(D, "build", "pull_profiles.py"), lst], check=True)




def created(a):
    if a in PCD:
        return pd.Timestamp(PCD[a]).timestamp() if PCD[a] else None
    p = os.path.join(RAW, f"profile_{a}.json")
    d = json.load(open(p)) if os.path.exists(p) else {"error": "not_fetched"}
    t = d.get("createdAt") if isinstance(d, dict) else None
    return pd.Timestamp(t).timestamp() if t else None


cr = {a: created(a) for a in need}
for X in (R, P):
    X["profile_created_ts"] = X.wallet.map(cr)
    X["profile_missing"] = X.prefilter_pass & X.profile_created_ts.isna()
    X["is_candidate"] = X.prefilter_pass & X.profile_created_ts.notna() & (X.profile_created_ts <= X.cand_first_buy_ts) & (X.profile_created_ts >= X.trigger_ts - AGE)
C = R[R.is_candidate].copy()
for col in ["trigger_ts", "cand_first_buy_ts", "profile_created_ts", "first_fill_v1_ts"]:
    C[col.replace("_ts", "_utc")] = pd.to_datetime(C[col], unit="s", utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
C = C.rename(columns={"wallet": "candidate_wallet", "trigger_leg_id": "trigger_fill_leg_id"})
C = C[["candidate_wallet", "case_id", "condition_id", "asset_id", "t_news_version", "trigger_wallet", "trigger_fill_leg_id", "trigger_utc", "trigger_usdc",
       "cand_usdc", "cand_n_legs", "cand_first_buy_utc", "profile_created_utc", "first_fill_v1_utc"]].sort_values(["t_news_version", "case_id", "candidate_wallet", "trigger_utc"])
C.to_csv(os.path.join(D, "data", "coordinated_candidates.csv"), index=False)
rep = {}
for v in ["day", "precise"]:
    nt = int((T.t_news_version == v).sum()); npw = int((PW.t_news_version == v).sum())
    rc = R[(R.t_news_version == v) & R.is_candidate]; pc = P[(P.t_news_version == v) & P.is_candidate]
    rep[v] = dict(n_triggers=nt, n_placebo_windows=npw, candidate_pairs_real=len(rc), candidate_pairs_placebo=len(pc),
                  candidates_per_trigger=round(len(rc) / nt, 4) if nt else None, candidates_per_placebo_window=round(len(pc) / npw, 4) if npw else None,
                  share_triggers_with_candidate=round(rc.window_id.nunique() / nt, 4) if nt else None,
                  share_placebo_windows_with_candidate=round(pc.window_id.nunique() / npw, 4) if npw else None,
                  distinct_candidate_wallets=int(rc.wallet.nunique()), distinct_placebo_hit_wallets=int(pc.wallet.nunique()),
                  profile_missing_real=int(R[(R.t_news_version == v)].profile_missing.sum()))
    rep[v]["placebo_to_real_ratio"] = round(rep[v]["candidates_per_placebo_window"] / rep[v]["candidates_per_trigger"], 4) if rep[v]["candidates_per_trigger"] else None
json.dump(dict(rule="PROTOCOL A13", seed=SEED, **rep), open(os.path.join(D, "logs", "coordinated_placebo.json"), "w"), indent=1)
print(json.dumps(rep, indent=1))
