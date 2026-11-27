"""PROTOCOL A21: hard negatives. Reads out/v1/positions.parquet, data/wallet_labels.csv, data/cases.csv, data/coordinated_candidates.csv,
Gamma public profiles (createdAt only; cached in logs/gamma_raw/profiles_created_run7.csv; raw profiles are not stored).
Writes data/hard_negatives.csv. Usage: python3 build/v1/hard_negatives.py <hf_pass_work_dir>"""
import concurrent.futures as cf, csv, json, os, sys, time, urllib.error, urllib.parse, urllib.request
import duckdb, pandas as pd

D = os.path.join(os.path.dirname(__file__), "..", "..")
WORK = sys.argv[1]
AGE = 14 * 86400
c = duckdb.connect(); c.sql("SET memory_limit='5GB'; SET enable_progress_bar=false")
W = pd.read_csv(os.path.join(D, "data", "wallet_labels.csv"), dtype=str, keep_default_na=False)
cs = pd.read_csv(os.path.join(D, "data", "cases.csv"), dtype=str, keep_default_na=False)
cleared = set(cs[cs.investigation_outcome.isin(["cleared_official", "cleared_analyst"])].case_id)
CC = pd.read_csv(os.path.join(D, "data", "coordinated_candidates.csv"), dtype=str)
excl = set(W.address) | set(CC.candidate_wallet)
c.execute("CREATE TABLE EX(a VARCHAR)"); c.executemany("INSERT INTO EX VALUES (?)", [(a,) for a in excl])
c.execute("CREATE TABLE CL(a VARCHAR)"); c.executemany("INSERT INTO CL VALUES (?)", [(a,) for a in cleared])
P = c.sql(f"""SELECT market_set, case_id, condition_id, asset_id, wallet, t_news_version, buy_usdc_pre, vwap_pre, first_buy_ts, won_post
              FROM '{D}/out/v1/positions.parquet'
              WHERE is_directional_position AND buy_usdc_pre >= 1000 AND vwap_pre <= 0.35 AND wallet NOT IN (SELECT a FROM EX)  -- A34.2
                AND ((market_set IN ('case', 'twin') AND case_id IN (SELECT a FROM CL))
                  OR (market_set IN ('case', 'twin') AND won_post = false)
                  OR (market_set = 'placebo' AND won_post = true))""").df()
P["rule"] = ["cleared_case_lookalike" if (m == "case" and k in cleared) else ("placebo_lookalike_winner" if m == "placebo" else "lookalike_loser")
             for m, k in zip(P.market_set, P.case_id)]
P = P[~((P.market_set == "twin") & P.case_id.isin(cleared) & (P.won_post != False))]  # twins of cleared cases only count as losers  # noqa: E712
print("profile-free matches", len(P), P.rule.value_counts().to_dict(), flush=True)
ws = sorted(set(P.wallet)); c.execute("CREATE TABLE WS(a VARCHAR)"); c.executemany("INSERT INTO WS VALUES (?)", [(a,) for a in ws])
first = c.sql(f"SELECT wallet, min(first_ts) f FROM read_parquet('{WORK}/P/*.parquet') WHERE wallet IN (SELECT a FROM WS) GROUP BY 1").df().set_index("wallet").f
P["first_fill_v1"] = P.wallet.map(first)
P = P[P.first_fill_v1.isna() | (P.first_fill_v1 >= P.first_buy_ts - AGE)]
CACHE = os.path.join(D, "logs", "gamma_raw", "profiles_created_run7.csv")
cache = {r[0]: r[1] for r in csv.reader(open(CACHE))}; cache.pop("address", None)
need = sorted(set(P.wallet) - set(cache))
print("after pre-filter", len(P), "wallets", P.wallet.nunique(), "to look up", len(need), flush=True)


def look(a):
    for i in range(5):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request("https://gamma-api.polymarket.com/public-profile?" + urllib.parse.urlencode({"address": a}),
                                                                        headers={"User-Agent": "curl/8.5.0"}), timeout=60))
            return a, d.get("createdAt") or "", ""
        except urllib.error.HTTPError as ex:
            if ex.code == 404:
                return a, "", "not_found"
            time.sleep(2 ** i)
        except Exception:
            time.sleep(2 ** i)
    return a, "", "fetch_failed"


new = []
with cf.ThreadPoolExecutor(4) as ex:
    for i, r in enumerate(ex.map(look, need), 1):
        new.append(r)
        if i % 1000 == 0:
            print("looked up", i, flush=True)
if new:
    rows = {r[0]: r for r in csv.reader(open(CACHE))}; hdr = rows.pop("address")
    for a, t, e in new:
        rows[a] = [a, t, e]
    with open(CACHE, "w", newline="") as f:
        w = csv.writer(f); w.writerow(hdr); w.writerows(sorted(rows.values()))
    cache.update({a: t for a, t, e in new})
P["profile_created_ts"] = P.wallet.map(lambda a: pd.Timestamp(cache[a]).timestamp() if cache.get(a) else None)
P = P[P.profile_created_ts.notna() & (P.profile_created_ts <= P.first_buy_ts) & (P.profile_created_ts >= P.first_buy_ts - AGE)].copy()
H = pd.DataFrame(dict(rule=P.rule, market_set=P.market_set, case_id=P.case_id, condition_id=P.condition_id, asset_id=P.asset_id, wallet=P.wallet,
                      t_news_version=P.t_news_version, pre_buy_usdc=P.buy_usdc_pre.round(2), vwap_price_usdc_pre=P.vwap_pre.round(6),
                      profile_created_utc=pd.to_datetime(P.profile_created_ts, unit="s", utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                      first_buy_utc=pd.to_datetime(P.first_buy_ts, unit="s", utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ"), won_post=P.won_post))
cw = W[W.case_id.isin(cleared)]
H = pd.concat([H, pd.DataFrame(dict(rule="cleared_case_wallet", case_id=cw.case_id, wallet=cw.address))], ignore_index=True)
H = H.sort_values(["rule", "case_id", "market_set", "condition_id", "wallet", "t_news_version"], na_position="first").reset_index(drop=True)
H.insert(0, "hard_negative_id", [f"HN{i:07d}" for i in range(1, len(H) + 1)])
H.to_csv(os.path.join(D, "data", "hard_negatives.csv"), index=False)
print(H.groupby(["rule", "t_news_version"], dropna=False).size().to_string()); print("wallets", H.wallet.nunique())
