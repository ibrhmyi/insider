"""v1.0 release tables (Phase D): casts every table to the schema in build/v1/schema.py, checks keys, writes
release/data/<table>.parquet (fills and other large tables in parts) and <table>.csv when under 50 MB.
Usage: python3 build/v1/tables.py
"""
import hashlib, json, os, re, shutil, sys
import duckdb, numpy as np, pandas as pd, pyarrow as pa, pyarrow.parquet as pq

sys.path.insert(0, os.path.dirname(__file__))
from schema import TABLES  # noqa

D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(D, "release", "data"); os.makedirs(OUT, exist_ok=True)
V1 = os.path.join(D, "out", "v1")
PART_ROWS = 15_000_000  # fills parts; see release/docs/README (Kaggle per-file limits)
rd = lambda p: pd.read_csv(os.path.join(D, p), dtype=str, keep_default_na=False)
nul = lambda df: df.replace({"": None})
ARROW = {"string": pa.string(), "int64": pa.int64(), "float64": pa.float64(), "bool": pa.bool_(), "timestamp": pa.timestamp("s", tz="UTC"), "date": pa.date32()}


def cast(name, df):
    spec = TABLES[name]["cols"]; names = [c["name"] for c in spec]
    missing = [n for n in names if n not in df.columns]; extra = [c for c in df.columns if c not in names]
    assert not missing and not extra, f"{name}: missing {missing} extra {extra}"
    df = df[names].copy()
    for c in spec:
        s = df[c["name"]]
        if c["dtype"] == "string":
            s = s.astype("object").where(s.notna(), None)
            s = s.map(lambda x: None if x is None or (isinstance(x, float) and np.isnan(x)) or x == "" else str(x))
        elif c["dtype"] in ("int64", "float64"):
            s = pd.to_numeric(s.replace({"": None}) if s.dtype == object else s, errors="raise")
            s = s.round().astype("Int64") if c["dtype"] == "int64" else s.astype("float64")
        elif c["dtype"] == "bool":
            if s.dtype == object:
                s = s.map(lambda x: None if x is None or x == "" or (isinstance(x, float) and np.isnan(x)) else str(x).strip().lower() in ("true", "1"))
            s = s.astype("boolean")
        elif c["dtype"] == "timestamp":
            s = pd.to_datetime(s.replace({"": None}) if s.dtype == object else s, utc=True, errors="raise", format="mixed").dt.floor("s")
        elif c["dtype"] == "date":
            s = pd.to_datetime(s.replace({"": None}), errors="raise").dt.date
        df[c["name"]] = s
    pk = [c["name"] for c in spec if c["pk"]]
    if pk:
        d = df.duplicated(pk).sum(); assert d == 0, f"{name}: {d} duplicate keys on {pk}"
    return df


def schema_of(name):
    return pa.schema([(c["name"], ARROW[c["dtype"]]) for c in TABLES[name]["cols"]])


def write(name, df):
    df = cast(name, df)
    t = pa.Table.from_pandas(df, schema=schema_of(name), preserve_index=False)
    pq.write_table(t, os.path.join(OUT, f"{name}.parquet"), compression="zstd")
    csvp = os.path.join(OUT, f"{name}.csv")
    df.to_csv(csvp, index=False, date_format="%Y-%m-%dT%H:%M:%SZ")
    if os.path.getsize(csvp) > 50 * 2**20:
        os.remove(csvp)
    print(name, len(df), flush=True)
    return df


# ---------- small tables
mk = rd("data/markets.csv"); mk["condition_id"] = mk.condition_id.str.lower()
cl = rd("data/claims.csv"); W = rd("data/wallet_labels.csv"); cs = rd("data/cases.csv")
cl["post_url"] = cl.notes.map(lambda n: (re.search(r"post_url=(\S+?)(?:;|\s|$)", n) or [None, None])[1])
write("claims", nul(cl))
RANK = {g: i for i, g in enumerate("E1 E2 E3 E4 E5 E6".split())}
direct = cl[~cl.subject_type.isin(["aggregate", "market"])]
dg = direct.groupby("case_id").evidence_grade.agg(lambda s: min(s, key=RANK.get))
W = W.rename(columns={"address": "wallet"})
W["is_documented"] = (W.polarity == "suspected") & (W.trade_confirmed == "true")
W["is_candidate_coordinated"] = W.polarity == "candidate"
W["doc_grade"] = np.where(W.polarity.isin(["suspected", "ambiguous"]), W.case_id.map(dg), None)
W = W.drop(columns=["case_market_traded", "case_check_note"])
wallets = write("wallets", nul(W))
split = {r.case_id: ("test" if r.first_claim_date_earliest >= "2026-03-01" else "train") for r in cs.itertuples()}
cs["benchmark_split"] = cs.case_id.map(split)
cs["n_markets"] = cs.case_id.map(mk.groupby("case_id").size()).fillna(0)
g = wallets.groupby("case_id")
cs["n_wallets_suspected"] = cs.case_id.map(wallets[wallets.polarity == "suspected"].groupby("case_id").size()).fillna(0)
cs["n_wallets_documented"] = cs.case_id.map(wallets[wallets.is_documented].groupby("case_id").size()).fillna(0)
cs["n_wallets_candidate"] = cs.case_id.map(wallets[wallets.is_candidate_coordinated].groupby("case_id").size()).fillna(0)
cs = cs.drop(columns=["n_wallet_addresses"])
write("cases", nul(cs))
mk["is_placebo_market"] = "false"
mk = mk.drop(columns=["series_id"])
for c_ in ["question", "slug", "event_slug"]:
    mk.loc[mk.title_withheld == "true", c_] = ""
write("markets", nul(mk))
pl = rd("data/placebo_markets.csv"); pl["benchmark_split"] = pl.case_id.map(split)
write("placebo_markets", nul(pl))
write("contradictions", nul(rd("data/contradictions.csv")))
write("edges", nul(rd("data/wallet_edges.csv")))
# ---------- large tables via parquet
c = duckdb.connect(); c.sql("SET memory_limit='10GB'; SET enable_progress_bar=false")
# controls / episodes (both versions)
ctrl = pd.concat([pd.read_parquet(os.path.join(V1, f"controls_{v}.parquet")) for v in ["day", "precise"]], ignore_index=True)
ep_ids = {}
for v in ["day", "precise"]:
    e = pd.read_parquet(os.path.join(V1, f"episodes_{v}.parquet"))
    ep_ids[v] = e
epi = pd.concat(ep_ids.values(), ignore_index=True)
write("controls", ctrl)
write("episodes", epi.drop(columns=[x for x in epi.columns if x not in [k["name"] for k in TABLES["episodes"]["cols"]]]))
# positions with label columns
pos = pd.read_parquet(os.path.join(V1, "positions.parquet"))
doc = wallets[wallets.is_documented][["wallet", "case_id", "doc_grade"]].assign(is_documented=True)
cand = wallets[wallets.is_candidate_coordinated][["wallet", "case_id"]].drop_duplicates().assign(is_candidate_coordinated=True)
pos = pos.merge(doc, on=["wallet", "case_id"], how="left").merge(cand, on=["wallet", "case_id"], how="left")
pos.loc[pos.market_set == "placebo", ["is_documented", "is_candidate_coordinated", "doc_grade"]] = [False, False, None]
ctl = ctrl[["t_news_version", "case_id", "condition_id", "wallet"]].drop_duplicates().assign(is_control=True)
pos = pos.merge(ctl, on=["t_news_version", "case_id", "condition_id", "wallet"], how="left")
pos.loc[pos.market_set == "placebo", "is_control"] = False
for x in ["is_documented", "is_candidate_coordinated", "is_control"]:
    pos[x] = pos[x].fillna(False).astype(bool)
pos["is_placebo_market"] = pos.market_set == "placebo"
pos = cast("positions", pos)
pq.write_table(pa.Table.from_pandas(pos, schema=schema_of("positions"), preserve_index=False), os.path.join(OUT, "positions.parquet"), compression="zstd")
print("positions", len(pos), flush=True)
# weak labels + gate counts
gc = pos[pos.market_set.isin(["case", "placebo"])].groupby(["wallet", "t_news_version"])[["gate1", "gate2a", "gate2b"]].sum().unstack()
gc.columns = [f"{a}_n" + ("" if b == "precise" else "_day") for a, b in gc.columns]
wl = pd.read_parquet(os.path.join(D, "out", "weak_labels.parquet")).rename(columns={"address": "wallet"})
wl = wl.merge(gc.reset_index(), on="wallet", how="left")
wl["gate_scope"] = np.where(wl.gate1_n.notna(), "case_or_placebo_markets", "not_in_case_or_placebo_markets")
wl["acdc_class"] = wl.acdc_class.replace("", None)
wl = cast("weak_labels", wl)
pq.write_table(pa.Table.from_pandas(wl, schema=schema_of("weak_labels"), preserve_index=False), os.path.join(OUT, "weak_labels.parquet"), compression="zstd")
print("weak_labels", len(wl), flush=True)
del wl, pos
mm = pd.read_parquet(os.path.join(V1, "market_minutes.parquet")).rename(columns={})
write("market_minutes", mm)
# fills: parts of PART_ROWS rows, ordered as written by build/v1/fills.py
for f in sorted(os.listdir(OUT)):
    if f.startswith("fills_part"):
        os.remove(os.path.join(OUT, f))
n_part = 0; total = 0
for ms in ["case", "placebo", "label_other"]:
  for src in ["hf_polymarket_v1", "data_api_v2"]:  # separate files per source, so data_api_v2 rows can be withheld if its terms require
    p0 = os.path.join(V1, "fills", f"fills_{ms}.parquet")
    p = f"(SELECT * FROM '{p0}' WHERE source = '{src}')"
    n = c.sql(f"SELECT count(*) FROM {p}").fetchall()[0][0]
    for off in range(0, n, PART_ROWS):
        n_part += 1
        t = c.sql(f"""SELECT market_set, leg_id, source, fill_id, tx_hash, ts, to_timestamp(ts) ts_utc, condition_id, asset_id, outcome_label, outcome_seq,
                     price, usdc, shares, fee_usdc, wallet, wallet_role, wallet_side, aggressor_side, maker, taker, market_slug
                     FROM {p} LIMIT {PART_ROWS} OFFSET {off}""").arrow()
        t = t.cast(schema_of("fills"))
        pq.write_table(t, os.path.join(OUT, f"fills_part{n_part:03d}_{ms}_{src}.parquet"), compression="zstd", row_group_size=500_000)
        total += t.num_rows
print("fills", total, "rows in", n_part, "parts")
