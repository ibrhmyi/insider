"""v2 step 1f/2/3 prep: modelling table. Unit = wallet x market x side with a net-long position at the decision time T_dec.
Writes data/v2/units.csv.gz with the 8 features + won + excess."""
import numpy as np, pandas as pd
from common import *
from v2_features import *
P = pd.read_csv(DATA / "v2" / "positions.csv.gz")
MI = pd.read_csv(DATA / "v2" / "market_info.csv")
CAND = pd.read_csv(DATA / "v2" / "markets_ranked.csv", usecols=["conditionId", "end_ts"])
MI = MI.merge(CAND, on="conditionId"); MI["event_key"] = MI.event_title.fillna(MI.question)
WS = pd.read_csv(DATA / "v2" / "wallet_stats.csv")
log = {}
u = P[(P.net_shares_dec > 1e-6) & (P.usd_bought_dec > 0)].copy()
log["units_net_long_at_decision"] = len(u)
u = u.merge(MI[["conditionId", "res_ts", "end_ts", "event_key", "category", "t_dec"]].rename(columns={"t_dec": "t_dec_m"}), on="conditionId")
u["price"] = u.vwap_dec.clip(0.01, 0.99); u["excess"] = u.won - u.price
u["t_first"] = u.first_buy_ts_dec; u["t_last"] = u.last_buy_ts_dec
# track record on every net-long unit (any size), before size filter
u["n_prior"], u["prior_excess"] = prior_track(u[["proxy_wallet", "conditionId", "res_ts", "t_first", "excess"]])
# size filter and wallet stats (join date needed for account age)
u = u[u.usd_bought_dec >= 100].copy(); log["units_ge_100usd"] = len(u)
u = u.merge(WS[["wallet", "known", "join_date", "n_markets", "life_volume_usdc"]].rename(columns={"wallet": "proxy_wallet"}), on="proxy_wallet", how="left")
nostat = (u.known != True) | u.join_date.isna(); log["units_no_wallet_stats"] = int(nostat.sum()); u = u[~nostat].copy()
u["age_days"] = ((u.t_first - u.join_date.astype(float)) / 86400).clip(lower=0)
u["log_age"] = np.log1p(u.age_days)
buys = pd.read_csv(DATA / "v2" / "buys.csv.gz"); buys = buys[buys.pre]
buys = buys.merge(MI[["conditionId", "event_key"]], on="conditionId")
buys = buys[buys.proxy_wallet.isin(set(u.proxy_wallet))]
u["share_event"] = share_event(buys, u)
u["log_usd"] = np.log(u.usd_bought_dec)
med = u.groupby("conditionId").usd_bought_dec.transform("median"); u["log_rel_size"] = np.log(u.usd_bought_dec / med)
u["conviction"] = (u.net_shares_dec / u.shares_bought_dec).clip(0, 1)
u["log_hours_to_end"] = np.log1p(((u.end_ts - u.t_first) / 3600).clip(lower=0, upper=24 * 365))
u["log_prior_markets"] = np.log1p(u.n_prior)
log["units_modelled"] = len(u); log["wallets_modelled"] = int(u.proxy_wallet.nunique()); log["markets"] = int(u.conditionId.nunique())
log["missing_share_event"] = int(u.share_event.isna().sum()); u["share_event"] = u.share_event.fillna(1.0)
keep = ["proxy_wallet", "conditionId", "side_name", "res_ts", "t_first", "t_last", "usd_bought_dec", "price", "won", "excess", "n_prior", "event_key", "category"] + FEATS
u[keep].to_csv(DATA / "v2" / "units.csv.gz", index=False, compression="gzip")
dump(log, DATA / "v2" / "units_log.json"); print(log)
