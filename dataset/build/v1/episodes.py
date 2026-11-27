"""Phases 6 and 7: matched controls (PROTOCOL A6.10) and episode features (A6.11 / PIPELINE step 7).

Episode = (case_id, wallet, condition_id, asset_id) with at least one BUY leg before the market's t_news (markets.csv).
Inputs: out/fills/case_market_legs.parquet, data/markets.csv, data/wallet_labels.csv, data/wallet_labels_expanded.csv (if any),
        out/weak_labels.parquet, <hf_pass_work>/P/*.parquet (prior-market history), logs/gamma_raw/activity_*.json.gz (redemptions).
Outputs: out/controls.parquet, out/episodes.parquet, logs/controls_summary.json
Usage: python3 build/v1/episodes.py <hf_pass_work_dir> <day|precise>
v1.0 (run 7): t_news version as argument (A10.2); suspected = is_documented (A12.5: suspected and trade_confirmed);
coordinated-buyer candidates (A13) join the control-pool exclusions; legs from out/v1/fills/fills_case.parquet;
stable episode_id = hash of (case, wallet, condition, token). Outputs out/v1/episodes_<v>.parquet, out/v1/controls_<v>.parquet.
"""
import csv, gzip, json, os, sys
import duckdb, numpy as np, pandas as pd

D = os.path.join(os.path.dirname(__file__), "..", "..")
WORK, VER = sys.argv[1], sys.argv[2]
MODE = sys.argv[3] if len(sys.argv) > 3 else "standard"  # A27: standard | age_matched | open; A33: winrate_matched
assert MODE in ("standard", "age_matched", "open", "winrate_matched")
BANDED = MODE in ("age_matched", "winrate_matched")
OUT0 = os.path.join(D, "out")
OUT = os.path.join(D, "out", "v1")
sys.path.insert(0, os.path.dirname(__file__)); from econ_view import legs_sql  # A34: economic view
LEGS_FILE = os.path.join(OUT, "fills", "fills_case.parquet")
import hashlib
SEED = 192
c = duckdb.connect(); c.sql(f"SET memory_limit='5GB'; SET enable_progress_bar=false; SET temp_directory='{WORK}/tmp'")
c.sql(f"CREATE VIEW legs_v AS SELECT * FROM {legs_sql(LEGS_FILE)}"); LEGS = "legs_v"

# --- markets with t_news (epoch) per case
mk = pd.read_csv(os.path.join(D, "data", "markets.csv"), dtype=str)
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")
def secs(x):  # tz-aware datetimes -> epoch seconds (unit-independent)
    return (pd.to_datetime(x, utc=True, errors="coerce", format="mixed") - EPOCH).dt.total_seconds()
mk["condition_id"] = mk["condition_id"].str.lower()
mk["t_news"] = secs(mk["t_news_market_day_utc" if VER == "day" else "t_news_market_utc"])  # A25.round().astype("Int64")
mk["resolved_ts"] = secs(mk["resolved_utc"]).round().astype("Int64")
c.register("mk_df", mk[["case_id", "condition_id", "event_slug", "ladder_rank", "deadline_utc", "outcome", "t_news", "resolved_ts", "t_news_precision"]])
c.sql("CREATE TABLE mk AS SELECT * FROM mk_df")

# --- label sets
W = pd.read_csv(os.path.join(D, "data", "wallet_labels.csv"), dtype=str)
labelled = set(W["address"])
exp_p = os.path.join(D, "data", "wallet_labels_expanded.csv")
expanded = set(pd.read_csv(exp_p, dtype=str)["address"]) if os.path.exists(exp_p) else set()
weak_flag = {r[0] for r in c.sql(f"SELECT address FROM '{OUT0}/weak_labels.parquet' WHERE acdc_class = 'Orca' OR inca_flag").fetchall()}
cands = set(pd.read_csv(os.path.join(D, "data", "coordinated_candidates.csv"), dtype=str).candidate_wallet)  # A13 / A17: rule-fired wallets
excluded = labelled | expanded | cands | (set() if MODE == "open" else weak_flag)  # A27: T2-open lets Orca/Inca wallets be controls
c.execute("CREATE TABLE excl(a VARCHAR)"); c.executemany("INSERT INTO excl VALUES (?)", [(a,) for a in excluded])
sus = W[(W["polarity"] == "suspected") & (W["trade_confirmed"].astype(str).str.lower() == "true") & (W["label_family"] == "informed_trading")][["address", "case_id"]].drop_duplicates()
cand = pd.read_csv(exp_p, dtype=str)[["address"]].assign(case_id="") if expanded else pd.DataFrame(columns=["address", "case_id"])

# --- per (case, market, token, wallet): pre-news BUY aggregates for every wallet in every case market
c.sql(f"""CREATE TABLE pre AS
  SELECT m.case_id, l.condition_id, l.asset_id, any_value(l.outcome_label) outcome_label, l.wallet,
         min(l.ts) first_buy_ts, arg_min(l.price, l.ts) first_buy_price, sum(l.usdc) size_usdc, sum(l.shares) shares,
         count(*) n_buys
  FROM {LEGS} l JOIN mk m USING (condition_id)
  WHERE l.wallet_side = 'BUY' AND l.ts < m.t_news AND l.wallet <> ''
  GROUP BY ALL""")
n_pre = c.sql("SELECT count(*) FROM pre").fetchall()[0][0]

# --- episodes of suspected (case-matched) and candidate wallets
c.register("sus_df", sus); c.sql("CREATE TABLE sus AS SELECT address wallet, case_id FROM sus_df")
ep = c.sql("SELECT p.*, 'suspected' polarity FROM pre p JOIN sus s USING (wallet, case_id)").df()
ep["episode_id"] = ["EP_" + hashlib.sha1(f"{a}|{b}|{c_}|{d}".encode()).hexdigest()[:12] for a, b, c_, d in zip(ep.case_id, ep.wallet, ep.condition_id, ep.asset_id)]
print("episodes", len(ep), flush=True)

# --- controls
rng = np.random.default_rng(SEED)
BANDS = [(-1e18, 1, "lt_1d"), (1, 7, "1_7d"), (7, 30, "7_30d"), (30, 180, "30_180d"), (180, 1e18, "ge_180d")]
c.sql(f"CREATE TABLE ffw AS SELECT address wallet, epoch(first_fill_utc)::BIGINT ffts FROM '{OUT0}/weak_labels.parquet'")
def age_band(df):  # A27: days from first Polymarket-v1 fill to first pre-cut buy; 'unknown' without v1 history
    d = (df["first_buy_ts"] - df["ffts"]) / 86400
    return [("unknown" if pd.isna(x) else next(n for lo, hi, n in BANDS if lo <= x < hi)) for x in d]
ffw = c.sql("SELECT * FROM ffw WHERE wallet IN (SELECT DISTINCT wallet FROM pre)").df().set_index("wallet").ffts
ep["ffts"] = ep.wallet.map(ffw); ep["age_band"] = age_band(ep)
pre_df = c.sql("SELECT * FROM pre WHERE wallet NOT IN (SELECT a FROM excl)").df()
pre_df["ffts"] = pre_df.wallet.map(ffw); pre_df["age_band"] = age_band(pre_df)
AGE_ORDER = [n for _, _, n in BANDS]; WR_ORDER = ["lt_0.25", "0.25_0.5", "0.5_0.75", "ge_0.75"]
def near(b, order):  # A33: the band and its neighbours; unknown / none have no neighbour
    if b not in order:
        return {b}
    i = order.index(b); return set(order[max(0, i - 1): i + 2])
if MODE == "winrate_matched":  # A33: prior win-rate band, computed as episodes.prior_net_long_win_rate, for episodes and candidates in episode markets
    em = ep[["case_id", "condition_id"]].drop_duplicates(); c.register("em_df", em)
    c.register("ep_q", ep[["wallet", "condition_id", "first_buy_ts"]])
    c.sql("""CREATE TABLE q AS SELECT DISTINCT wallet, condition_id, first_buy_ts FROM (
               SELECT p.wallet, p.condition_id, p.first_buy_ts FROM pre p JOIN em_df USING (case_id, condition_id) WHERE p.wallet NOT IN (SELECT a FROM excl)
               UNION ALL SELECT wallet, condition_id, first_buy_ts FROM ep_q)""")
    # same quantity as the episode feature (avg over net-long resolved (market, token) rows with first trade before t, other markets only),
    # computed with cumulative counts and an ASOF join instead of a candidate x prior-market join (disk)
    NB = 32; parts = []  # wallet-hash buckets keep the DuckDB spill within the disk allowance
    c.sql("SET preserve_insertion_order = false")
    for bkt in range(NB):
        c.sql(f"CREATE OR REPLACE TABLE qb AS SELECT * FROM q WHERE hash(wallet) % {NB} = {bkt}")
        c.sql(f"""CREATE OR REPLACE TABLE pm AS
            WITH p AS (SELECT wallet, condition_id, asset_id, min(first_ts) fts, sum(buy_shares) bs, sum(sell_shares) ss
                       FROM read_parquet('{WORK}/P/*.parquet') WHERE hash(wallet) % {NB} = {bkt} AND wallet IN (SELECT DISTINCT wallet FROM qb) GROUP BY 1, 2, 3),
                 r AS (SELECT asset_id, condition_id, any_value(outcome_label) ol, any_value(winning_outcome_label) wl, any_value(resolution_status) st
                       FROM '{OUT0}/hf_market_catalog.parquet' GROUP BY 1, 2)
            SELECT p.wallet, p.condition_id, p.fts, CASE WHEN r.st = 'resolved' AND r.wl IS NOT NULL AND p.bs > p.ss THEN (r.ol = r.wl)::INT END win
            FROM p LEFT JOIN r ON r.asset_id = p.asset_id AND r.condition_id = p.condition_id""")
        c.sql("""CREATE OR REPLACE TABLE cum AS SELECT wallet, fts, sum(n) OVER w cn, sum(k) OVER w ck FROM
                   (SELECT wallet, fts, count(win) n, sum(win) k FROM pm GROUP BY 1, 2) WINDOW w AS (PARTITION BY wallet ORDER BY fts ROWS UNBOUNDED PRECEDING)""")
        parts.append(c.sql("""WITH a AS (SELECT qb.wallet, qb.condition_id, qb.first_buy_ts, coalesce(cum.cn, 0) cn, coalesce(cum.ck, 0) ck
                                         FROM qb ASOF LEFT JOIN cum ON cum.wallet = qb.wallet AND cum.fts < qb.first_buy_ts),
                                   o AS (SELECT qb.wallet, qb.condition_id, qb.first_buy_ts, count(pm.win) on_, coalesce(sum(pm.win), 0) ok
                                         FROM qb JOIN pm ON pm.wallet = qb.wallet AND pm.condition_id = qb.condition_id AND pm.fts < qb.first_buy_ts GROUP BY 1, 2, 3)
                              SELECT a.wallet, a.condition_id, a.first_buy_ts,
                                     (a.ck - coalesce(o.ok, 0))::DOUBLE / nullif(a.cn - coalesce(o.on_, 0), 0) wr
                              FROM a LEFT JOIN o USING (wallet, condition_id, first_buy_ts)""").df())
    c.sql("DROP TABLE pm; DROP TABLE cum; DROP TABLE qb")
    wr = pd.concat(parts, ignore_index=True)
    wr = wr.set_index(["wallet", "condition_id", "first_buy_ts"]).wr
    band = lambda x: "none" if pd.isna(x) else ("lt_0.25" if x < 0.25 else "0.25_0.5" if x < 0.5 else "0.5_0.75" if x < 0.75 else "ge_0.75")
    for df_ in (ep, pre_df):
        df_["wr_band"] = [band(wr.get((a, b, t_), np.nan)) for a, b, t_ in zip(df_.wallet, df_.condition_id, df_.first_buy_ts)]
    print("win-rate bands (episodes)", ep.wr_band.value_counts().to_dict(), flush=True)
pre_by = {k: g for k, g in pre_df.groupby(["case_id", "condition_id"])}
LADDER = [("base", 86400, 0.05, (0.5, 2.0)), ("window_72h", 3 * 86400, 0.05, (0.5, 2.0)),
          ("price_0.10", 3 * 86400, 0.10, (0.5, 2.0)), ("size_0.25_4x", 3 * 86400, 0.10, (0.25, 4.0))]
ctrl = []
def pick(g, e):
    same = g[g["asset_id"] == e["asset_id"]]
    picked, used = pd.DataFrame(), "none_available"
    for name, win, dp, (lo, hi) in LADDER:
        q = same[(abs(same["first_buy_ts"] - e["first_buy_ts"]) <= win) & (abs(same["first_buy_price"] - e["first_buy_price"]) <= dp)
                 & (same["size_usdc"] >= lo * e["size_usdc"]) & (same["size_usdc"] <= hi * e["size_usdc"])]
        if len(q) >= 10 or name == LADDER[-1][0]:
            picked, used = q, name
            break
    return picked, used
for _, e in ep.iterrows():
    g0 = g = pre_by.get((e["case_id"], e["condition_id"]))
    if g is None:
        continue
    relaxed = False
    if BANDED:  # exact band(s) first
        m = g0["age_band"] == e["age_band"]
        if MODE == "winrate_matched":
            m &= g0["wr_band"] == e["wr_band"]
        g = g0[m]
    picked, used = pick(g, e)
    if BANDED and len(picked) == 0:  # A33: one retry with the adjacent band(s)
        m = g0["age_band"].isin(near(e["age_band"], AGE_ORDER))
        if MODE == "winrate_matched":
            m &= g0["wr_band"].isin(near(e["wr_band"], WR_ORDER))
        g2 = g0[m]; p2, u2 = pick(g2, e)
        if len(p2):
            g, picked, used, relaxed = g2, p2, u2, True
    if len(picked) > 10:
        picked = picked.iloc[rng.choice(len(picked), 10, replace=False)]
    for _, r in picked.iterrows():
        ctrl.append(dict(episode_id=e["episode_id"], control_type="same_side", relaxation=used, n_eligible=len(picked), relaxed_band=relaxed,
                         **{k: r[k] for k in ("case_id", "condition_id", "asset_id", "outcome_label", "wallet", "first_buy_ts",
                                               "first_buy_price", "size_usdc", "n_buys")}))
    other = g[(g["asset_id"] != e["asset_id"]) & (abs(g["first_buy_ts"] - e["first_buy_ts"]) <= 86400)].nlargest(10, "size_usdc")
    for _, r in other.iterrows():
        ctrl.append(dict(episode_id=e["episode_id"], control_type="other_side_large_buyer", relaxation="base", n_eligible=len(other), relaxed_band=relaxed,
                         **{k: r[k] for k in ("case_id", "condition_id", "asset_id", "outcome_label", "wallet", "first_buy_ts",
                                               "first_buy_price", "size_usdc", "n_buys")}))
ctrl = pd.DataFrame(ctrl)
ctrl["t_news_version"] = VER; ctrl["control_design"] = MODE
ctrl.to_parquet(os.path.join(OUT, f"controls_{VER}_{MODE}.parquet"), index=False)
summ = dict(seed=SEED, n_episodes=len(ep), n_controls=len(ctrl), n_pre_rows=n_pre, n_excluded_addresses=len(excluded),
            episodes_with_same_side_controls=int(ctrl[ctrl.control_type == "same_side"].episode_id.nunique()) if len(ctrl) else 0,
            relaxation_counts=ctrl[ctrl.control_type == "same_side"].groupby("episode_id").relaxation.first().value_counts().to_dict() if len(ctrl) else {},
            n_episodes_without_same_side=int(len(ep) - (ctrl[ctrl.control_type == "same_side"].episode_id.nunique() if len(ctrl) else 0)),
            n_episodes_relaxed_band=int(ctrl[ctrl.relaxed_band].episode_id.nunique()) if len(ctrl) else 0)
print(summ, flush=True)

# --- episode feature rows: suspected episodes + their controls (one row per wallet x case x market x token)
rows = ep.assign(role="suspected", control_of="")
if len(ctrl):
    cr = ctrl.rename(columns={"episode_id": "control_of"}).assign(role=lambda d: "control_" + d["control_type"])
    rows = pd.concat([rows.assign(relaxed_band=False), cr[["case_id", "condition_id", "asset_id", "outcome_label", "wallet", "first_buy_ts", "first_buy_price",
                                "size_usdc", "n_buys", "role", "control_of", "relaxed_band"]]], ignore_index=True)
rows = rows.drop_duplicates(["case_id", "condition_id", "asset_id", "wallet", "role", "control_of"])
rows["row_id"] = ["ER%06d" % i for i in range(1, len(rows) + 1)]
c.register("rows_df", rows[["row_id", "case_id", "condition_id", "asset_id", "wallet", "role", "control_of", "first_buy_ts"]])
c.sql("CREATE TABLE er AS SELECT * FROM rows_df")
c.sql(f"""CREATE TABLE el AS SELECT er.row_id, l.* , m.t_news, m.resolved_ts FROM er
          JOIN {LEGS} l ON l.condition_id = er.condition_id AND l.asset_id = er.asset_id AND l.wallet = er.wallet
          JOIN mk m ON m.case_id = er.case_id AND m.condition_id = er.condition_id""")

F = c.sql("""
  SELECT row_id,
    -- entry (pre t_news)
    min(ts) FILTER (WHERE wallet_side='BUY' AND ts < t_news) first_buy_ts,
    arg_min(price, ts) FILTER (WHERE wallet_side='BUY' AND ts < t_news) first_price,
    sum(usdc) FILTER (WHERE wallet_side='BUY' AND ts < t_news) / nullif(sum(shares) FILTER (WHERE wallet_side='BUY' AND ts < t_news), 0) vwap,
    max(price) FILTER (WHERE wallet_side='BUY' AND ts < t_news) max_price_paid,
    count(*) FILTER (WHERE wallet_side='BUY' AND ts < t_news) n_buy_fills,
    median(usdc) FILTER (WHERE wallet_side='BUY' AND ts < t_news) median_fill_usdc,
    stddev_samp(usdc) FILTER (WHERE wallet_side='BUY' AND ts < t_news) / nullif(avg(usdc) FILTER (WHERE wallet_side='BUY' AND ts < t_news), 0) fill_size_cv,
    avg((wallet_role='taker')::INT) FILTER (WHERE wallet_side='BUY' AND ts < t_news AND wallet_role <> 'unknown') taker_share,
    sum(usdc) FILTER (WHERE wallet_side='BUY' AND ts < t_news) pre_buy_usdc,
    sum(shares) FILTER (WHERE wallet_side='BUY' AND ts < t_news) pre_buy_shares,
    sum(shares) FILTER (WHERE wallet_side='SELL' AND ts < t_news) pre_sell_shares,
    max(ts) FILTER (WHERE wallet_side='BUY' AND ts < t_news) last_buy_ts,
    regr_slope(usdc, price) FILTER (WHERE wallet_side='BUY' AND ts < t_news) size_price_slope,
    any_value(t_news) t_news, any_value(resolved_ts) resolved_ts,
    -- post
    sum(shares) FILTER (WHERE wallet_side='SELL' AND (resolved_ts IS NULL OR ts < resolved_ts)) sold_shares_before_resolution_post,
    sum(shares) FILTER (WHERE wallet_side='BUY') buy_shares_all_post,
    sum(usdc) FILTER (WHERE wallet_side='BUY') buy_usdc_all_post, sum(usdc) FILTER (WHERE wallet_side='SELL') sell_usdc_all_post,
    sum(shares) FILTER (WHERE wallet_side='SELL') sell_shares_all_post,
    any_value(source) FILTER (WHERE ts < t_news) source_pre, any_value(outcome_label) outcome_label,
    coalesce(sum(usdc) FILTER (WHERE wallet_side='BUY' AND ts < t_news AND econ_inferred), 0) econ_inferred_buy_usdc_pre,
    count(*) FILTER (WHERE wallet_side='BUY' AND ts < t_news AND NOT econ_inferred) > 0 raw_view_prenews_buy
  FROM el GROUP BY row_id""").df()
# Signal A: bought again at >= 1.5x the first price (pre t_news)
sa = c.sql("""SELECT e.row_id, bool_or(e.price >= 1.5 * f.fp) signal_a_rebuy_1_5x
              FROM el e JOIN (SELECT row_id, arg_min(price, ts) fp, min(ts) fts FROM el WHERE wallet_side='BUY' AND ts < t_news GROUP BY 1) f USING (row_id)
              WHERE e.wallet_side='BUY' AND e.ts < e.t_news AND e.ts > f.fts GROUP BY 1""").df()
# followers: other wallets' BUY legs on the same token within 60 min after each pre-news buy fill
fol = c.sql(f"""WITH b AS (SELECT row_id, condition_id, asset_id, wallet, ts FROM el WHERE wallet_side='BUY' AND ts < t_news)
  SELECT b.row_id, count(DISTINCT l.wallet) follower_wallets_60m, sum(l.usdc) follower_buy_usdc_60m
  FROM b JOIN {LEGS} l ON l.condition_id = b.condition_id AND l.asset_id = b.asset_id AND l.wallet_side = 'BUY'
       AND l.wallet <> b.wallet AND l.ts > b.ts AND l.ts <= b.ts + 3600
  GROUP BY 1""").df()
X = rows.merge(F, on="row_id", how="left", suffixes=("", "_f")).merge(sa, on="row_id", how="left").merge(fol, on="row_id", how="left")
X["signal_a_rebuy_1_5x"] = X["signal_a_rebuy_1_5x"].fillna(False)
X["hour_of_day_first_buy"] = pd.to_datetime(X["first_buy_ts_f"], unit="s", utc=True).dt.hour
X["hours_first_buy_to_tnews"] = (X["t_news"] - X["first_buy_ts_f"]) / 3600
X["hours_last_buy_to_tnews"] = (X["t_news"] - X["last_buy_ts"]) / 3600
X["share_sold_before_resolution_post"] = X["sold_shares_before_resolution_post"].fillna(0) / X["buy_shares_all_post"]

# wallet history: account age, prior markets, prior win share, case share of lifetime volume
wl = c.sql(f"SELECT address wallet, first_fill_utc, n_markets lifetime_markets, buy_usdc + sell_usdc lifetime_usdc FROM '{OUT0}/weak_labels.parquet' WHERE address IN (SELECT DISTINCT wallet FROM er)").df()
X = X.merge(wl, on="wallet", how="left")
X["account_age_days_at_first_buy"] = (X["first_buy_ts_f"] - secs(X["first_fill_utc"])) / 86400
hist = c.sql(f"""WITH p AS (SELECT wallet, condition_id, asset_id, min(first_ts) fts, sum(buy_shares) bs, sum(sell_shares) ss
                  FROM read_parquet('{WORK}/P/*.parquet') WHERE wallet IN (SELECT DISTINCT wallet FROM er) GROUP BY 1, 2, 3),
                 r AS (SELECT asset_id, condition_id, any_value(outcome_label) ol, any_value(winning_outcome_label) wl, any_value(resolution_status) st
                       FROM '{OUT0}/hf_market_catalog.parquet' GROUP BY 1, 2)
  SELECT er.row_id, count(DISTINCT p.condition_id) prior_markets,
         avg(CASE WHEN r.st = 'resolved' AND r.wl IS NOT NULL AND p.bs > p.ss THEN (r.ol = r.wl)::INT END) prior_net_long_win_rate
  FROM er JOIN p ON p.wallet = er.wallet AND p.fts < er.first_buy_ts AND p.condition_id <> er.condition_id
  LEFT JOIN r ON r.asset_id = p.asset_id AND r.condition_id = p.condition_id GROUP BY 1""").df()
X = X.merge(hist, on="row_id", how="left")
X["prior_markets"] = X["prior_markets"].fillna(0).astype(int)  # no earlier market in Polymarket-v1 -> 0
if MODE == "winrate_matched":  # A33 self-check: the matching band equals the band of the episode's own feature
    chk = X[X.role == "suspected"]  # carries wr_band from the episode rows
    mism = int((chk.prior_net_long_win_rate.map(band) != chk.wr_band).sum())
    print("A33 band self-check: suspected rows", len(chk), "mismatches", mism, flush=True)
    assert mism == 0
case_vol = c.sql("SELECT row_id, sum(usdc) case_usdc FROM el GROUP BY 1").df()
X = X.merge(case_vol, on="row_id", how="left")
X["case_share_of_lifetime_volume"] = X["case_usdc"] / X["lifetime_usdc"]

# deadline choice (Signal B): ladder rank and whether this market is the shortest sufficient deadline in its event
mkx = mk.copy(); mkx["ladder_rank"] = pd.to_numeric(mkx["ladder_rank"], errors="coerce")
yes_res = mkx[mkx["outcome"].str.lower().eq("yes") & mkx["ladder_rank"].notna()]
shortest = yes_res.loc[yes_res.groupby(["case_id", "event_slug"])["ladder_rank"].idxmin(), ["case_id", "condition_id"]].assign(is_shortest_sufficient=True)
X = X.merge(mkx[["case_id", "condition_id", "event_slug", "ladder_rank", "outcome"]].rename(columns={"outcome": "market_outcome"}),
            on=["case_id", "condition_id"], how="left").merge(shortest, on=["case_id", "condition_id"], how="left")
X["is_shortest_sufficient"] = X["is_shortest_sufficient"].fillna(False)
ev = X.groupby(["wallet", "case_id", "event_slug", "role", "control_of"])["pre_buy_usdc"].transform("sum")
X["share_on_this_ladder_market"] = X["pre_buy_usdc"] / ev

# outcome (_post)
X["won_post"] = X["outcome_label"].fillna("").str.lower() == X["market_outcome"].fillna("~").str.lower()
held = (X["buy_shares_all_post"].fillna(0) - X["sell_shares_all_post"].fillna(0)).clip(lower=0)
X["pnl_post"] = X["sell_usdc_all_post"].fillna(0) - X["buy_usdc_all_post"].fillna(0) + np.where(X["won_post"], held, 0)
red = {}
for a in X.loc[X["role"] == "suspected", "wallet"].unique():
    p = os.path.join(D, "logs", "gamma_raw", f"activity_{a}.json.gz")
    if os.path.exists(p):
        for x in json.load(gzip.open(p, "rt")):
            if x["type"] == "REDEEM":
                k = (a, x["condition_id"].lower()); red[k] = min(red.get(k, 9e18), x["timestamp"])
X["redemption_delay_hours_post"] = [((red.get((w, cid)) - r) / 3600) if (w, cid) in red and pd.notna(r) else np.nan
                                   for w, cid, r in zip(X["wallet"], X["condition_id"], X["resolved_ts"])]
X["hours_funding_to_first_trade"] = np.nan; X["funding_source_type"] = None; X["funder_shared_with_labelled"] = None  # phase 4 blocked
keep = ["row_id", "role", "control_of", "case_id", "condition_id", "event_slug", "asset_id", "outcome_label", "wallet", "source_pre",
        "account_age_days_at_first_buy", "prior_markets", "prior_net_long_win_rate", "case_share_of_lifetime_volume",
        "first_price", "vwap", "max_price_paid", "n_buy_fills", "median_fill_usdc", "fill_size_cv", "taker_share", "hour_of_day_first_buy",
        "pre_buy_usdc", "pre_buy_shares", "signal_a_rebuy_1_5x", "size_price_slope", "hours_last_buy_to_tnews", "ladder_rank",
        "is_shortest_sufficient", "share_on_this_ladder_market", "hours_first_buy_to_tnews", "hours_funding_to_first_trade",
        "funding_source_type", "funder_shared_with_labelled", "follower_wallets_60m", "follower_buy_usdc_60m",
        "share_sold_before_resolution_post", "won_post", "pnl_post", "redemption_delay_hours_post", "relaxed_band",
        "econ_inferred_buy_usdc_pre", "raw_view_prenews_buy"]
X = X.rename(columns={})[keep]
X = X.merge(ep[["episode_id", "case_id", "condition_id", "asset_id", "wallet"]], on=["case_id", "condition_id", "asset_id", "wallet"], how="left")
X.loc[X.role != "suspected", "episode_id"] = None
X["t_news_version"] = VER; X["control_design"] = MODE
X.to_parquet(os.path.join(OUT, f"episodes_{VER}_{MODE}.parquet"), index=False)
summ.update(n_episode_rows=len(X), rows_by_role=X["role"].value_counts().to_dict(),
            suspected_episodes_by_case=X[X.role == "suspected"]["case_id"].value_counts().to_dict())
json.dump(summ, open(os.path.join(D, "logs", f"controls_summary_{VER}_{MODE}.json"), "w"), indent=1, default=str)
print(json.dumps(summ, indent=1, default=str))
