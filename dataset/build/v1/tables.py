"""v1.0 release tables (Phase D): casts every table to the schema in build/v1/schema.py, checks keys, writes
release/data/<table>.parquet (fills and other large tables in parts) and <table>.csv when under 50 MB.
Usage: python3 build/v1/tables.py
"""
import hashlib, json, os, re, shutil, sys
import duckdb, numpy as np, pandas as pd, pyarrow as pa, pyarrow.parquet as pq

sys.path.insert(0, os.path.dirname(__file__))
from schema import TABLES, RENAME  # noqa

D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(D, "release", "data"); os.makedirs(OUT, exist_ok=True)
V1 = os.path.join(D, "out", "v1")
PART_ROWS = 15_000_000  # fills parts; see release/docs/README (Kaggle per-file limits)
rd = lambda p: pd.read_csv(os.path.join(D, p), dtype=str, keep_default_na=False)
nul = lambda df: df.replace({"": None})
ARROW = {"string": pa.string(), "int64": pa.int64(), "float64": pa.float64(), "bool": pa.bool_(), "timestamp": pa.timestamp("s", tz="UTC"), "date": pa.date32()}


def is_text(s):
    return s.dtype == object or pd.api.types.is_string_dtype(s)


def cast(name, df):
    df = df.rename(columns=RENAME.get(name, {}))  # A24: units in names
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
            s = pd.to_numeric(s.astype(object).replace({"": None}) if is_text(s) else s, errors="raise")
            s = s.round().astype("Int64") if c["dtype"] == "int64" else s.astype("float64")
        elif c["dtype"] == "bool":
            if not pd.api.types.is_bool_dtype(s):
                s = s.astype(object).map(lambda x: None if x is None or x == "" or (isinstance(x, float) and np.isnan(x)) else str(x).strip().lower() in ("true", "1"))
            s = s.astype("boolean")
        elif c["dtype"] == "timestamp":
            s = pd.to_datetime(s.astype(object).replace({"": None}) if is_text(s) else s, utc=True, errors="raise", format="mixed").dt.floor("s")
        elif c["dtype"] == "date":
            s = pd.to_datetime(s.astype(object).replace({"": None}), errors="raise").dt.date
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


# ---------- run-11 audit helpers
from question_type import qtype  # A38
from alleged import alleged_positions  # A35
NAMES = {x.strip() for x in open(os.path.join(D, "tests", "name_hashes.txt")) if x.strip() and not x.startswith("#")}
def has_name(v):  # A39: same n-gram hash test as the name gate
    w = re.findall(r"[a-z]+", str(v).lower())
    return any(hashlib.sha256(" ".join(w[i:i + n]).encode()).hexdigest() in NAMES for n in (1, 2, 3) for i in range(len(w) - n + 1))
def scrub(df, cols):  # A39: NULL category / slug values that contain a withheld name
    for c_ in cols:
        if c_ in df:
            df.loc[df[c_].map(lambda v: bool(v) and has_name(v)), c_] = ""
    return df
SPL = pd.read_csv(os.path.join(D, "release", "benchmarks", "splits.csv"), dtype=str).set_index("case_id")  # A37 (build/v1/splits.py)
ALG = alleged_positions(D)
CP = rd("data/claim_positions.csv"); CP["condition_id"] = CP.condition_id.str.lower()
# ---------- small tables
mk = rd("data/markets.csv"); mk["condition_id"] = mk.condition_id.str.lower()
mk["question_type"] = mk.question.map(qtype)
_res = mk.drop_duplicates("condition_id").set_index("condition_id")
cl = rd("data/claims.csv"); W = rd("data/wallet_labels.csv"); cs = rd("data/cases.csv")
cl["right_of_reply"] = ""  # A24: no reply received yet (not_built, A43)
# A42: claim timing against the claim's alleged markets; A44: duplicates
_cpm = CP.merge(_res[["resolved_utc", "outcome"]].reset_index(), on="condition_id", how="left")
_cpm["res"] = pd.to_datetime(_cpm.resolved_utc.replace("", None), utc=True, errors="coerce", format="mixed")
_cpm["won"] = [None if (o == "" or pd.isna(o)) else (sd.lower() == o.lower()) for sd, o in zip(_cpm.side, _cpm.outcome)]
_ct = _cpm.groupby("claim_id").agg(first_res=("res", "min"), n_unres=("won", lambda x: int(sum(v is None for v in x))), all_won=("won", lambda x: all(v for v in x if v is not None)))
_cd = pd.to_datetime(cl.claim_date.where(cl.claim_date.str.len() >= 10, None), utc=True, errors="coerce", format="mixed")
cl["claim_timing"] = [("" if k not in _ct.index or pd.isna(_ct.at[k, "first_res"]) or pd.isna(d) else ("ex_ante" if d < _ct.at[k, "first_res"] else "ex_post"))
                      for k, d in zip(cl.claim_id, _cd)]
cl["alleged_side_won"] = [("" if k not in _ct.index or _ct.at[k, "n_unres"] > 0 else ("true" if _ct.at[k, "all_won"] else "false")) for k in cl.claim_id]
cl["duplicate_of"] = cl.claim_id.map({"CL0124": "CL0091"}).fillna("")
cl["post_url"] = cl.notes.map(lambda n: (re.search(r"post_url=(\S+?)(?:;|\s|$)", n) or [None, None])[1])
write("claims", nul(cl))
RANK = {g: i for i, g in enumerate("E1 E2 E3 E4 E5 E6".split())}
direct = cl[~cl.subject_type.isin(["aggregate", "market"])]
dg = direct.groupby("case_id").evidence_grade.agg(lambda s: min(s, key=RANK.get))
W = W.rename(columns={"address": "wallet"})
W = W[W.label_tier != "L4_coordinated"]  # A17: rule output is not a wallet label
W["is_documented"] = (W.polarity == "suspected") & (W.trade_confirmed == "true") & (W.label_family == "informed_trading")  # A19
HN = rd("data/hard_negatives.csv")  # A21
cw = set(zip(HN[HN.rule == "cleared_case_wallet"].wallet, HN[HN.rule == "cleared_case_wallet"].case_id))
W["hard_negative"] = [(a, k) in cw for a, k in zip(W.wallet, W.case_id)]
W["hard_negative_rule"] = np.where(W.hard_negative, "cleared_case_wallet", "")
W = W.drop(columns=["case_market_traded", "case_check_note"])
wallets = write("wallets", nul(W))
split = SPL.split.to_dict()  # A37: whole connected groups
cs["benchmark_split"] = cs.case_id.map(split)
cs["benchmark_group_id"] = cs.case_id.map(SPL.group_id)
_tn = mk.groupby("case_id").t_news_utc.first()
cs["event_occurred_utc"] = cs.case_id.map(_tn).fillna("")  # A44
_dl = CP.merge(_res[["deadline_utc"]].reset_index(), on="condition_id", how="left")
_dl["dl"] = pd.to_datetime(_dl.deadline_utc.replace("", None), utc=True, errors="coerce", format="mixed")
cs["market_deadline_utc"] = cs.case_id.map(_dl.groupby("case_id").dl.min().dt.strftime("%Y-%m-%dT%H:%M:%SZ")).fillna("")
_ea = cl[cl.claim_timing == "ex_ante"]
cs["n_claims_ex_ante"] = cs.case_id.map(_ea.groupby("case_id").size()).fillna(0)
_eaw = _ea[_ea.alleged_side_won != ""]
cs["ex_ante_win_rate"] = cs.case_id.map(_eaw.groupby("case_id").alleged_side_won.apply(lambda x: (x == "true").mean()))
cs = cs.drop(columns=["event_date"])
cs["n_markets"] = cs.case_id.map(mk.groupby("case_id").size()).fillna(0)
g = wallets.groupby("case_id")
cs["n_wallets_suspected"] = cs.case_id.map(wallets[wallets.polarity == "suspected"].groupby("case_id").size()).fillna(0)
cs["n_documented_by_case"] = cs.case_id.map(wallets[wallets.is_documented].groupby("case_id").size()).fillna(0)
CC = pd.read_csv(os.path.join(D, "data", "coordinated_candidates.csv"), dtype=str, keep_default_na=False)
cs["n_wallets_coordinated_rule"] = cs.case_id.map(CC.groupby("case_id").candidate_wallet.nunique()).fillna(0)
PR = json.load(open(os.path.join(D, "logs", "coordinated_placebo.json")))
cs = cs.drop(columns=["n_wallet_addresses"])
write("cases", nul(cs))
mk["is_placebo_market"] = "false"
mk = mk.drop(columns=["series_id"])
for c_ in ["question", "slug", "event_slug"]:
    mk.loc[mk.title_withheld == "true", c_] = ""
mk = scrub(mk, ["slug", "event_slug", "category", "category_refined"])  # A39
write("markets", nul(mk))
pl = scrub(rd("data/placebo_markets.csv"), ["placebo_slug", "placebo_category"]); pl["benchmark_split"] = pl.case_id.map(split)
pl.insert(0, "placebo_row_id", [f"PR{i:05d}" for i in range(1, len(pl) + 1)])
write("placebo_markets", nul(pl))
write("contradictions", nul(rd("data/contradictions.csv")))
ed = rd("data/wallet_edges.csv")
blk = ed.utc.str.extract(r"^block (\d+)$")[0]
ed["block_number"] = blk.fillna(""); ed.loc[blk.notna(), "utc"] = ""  # some sources give a block number instead of a time
ed.insert(0, "edge_id", [f"ED{i:04d}" for i in range(1, len(ed) + 1)])
write("edges", nul(ed))
tw = scrub(rd("data/twin_markets.csv"), ["twin_slug", "category_refined"]); tw["benchmark_split"] = tw.case_id.map(split)  # A22, A39
tw.insert(0, "twin_row_id", [f"TR{i:05d}" for i in range(1, len(tw) + 1)])
write("twin_markets", nul(tw))
write("hard_negatives", nul(HN))
write("claim_wallet_links", nul(rd("data/claim_wallet_links.csv")))
write("claim_positions", nul(CP))  # A35
# ---------- large tables via parquet
c = duckdb.connect(); c.sql("SET memory_limit='4GB'; SET enable_progress_bar=false")
# controls / episodes (both versions)
DES = ["standard", "age_matched", "winrate_matched", "open"]  # A27, A33
_m = rd("data/markets.csv"); _m["condition_id"] = _m.condition_id.str.lower()
REL_M = {(a, b): v == "true" for a, b, v in zip(_m.case_id, _m.condition_id, _m.t_news_reliable)}  # A29.1: per-market flag
_ref = pd.concat([rd("data/placebo_markets.csv").rename(columns={"placebo_condition_id": "cid"})[["case_id", "case_condition_id", "cid"]].assign(market_set="placebo"),
                  rd("data/twin_markets.csv").rename(columns={"twin_condition_id": "cid"})[["case_id", "case_condition_id", "cid"]].assign(market_set="twin")])
_ref = _ref[_ref.cid != ""].assign(cid=lambda d: d.cid.str.lower(), case_condition_id=lambda d: d.case_condition_id.str.lower())
_ref["rel"] = [REL_M.get((a, b), True) for a, b in zip(_ref.case_id, _ref.case_condition_id)]
REL_REF = _ref.groupby(["market_set", "case_id", "cid"]).rel.any().to_dict()  # placebo / twin: reliable if any matched case market is
def rel_of(ms, case, cid):
    return REL_M.get((case, cid), True) if ms == "case" else REL_REF.get((ms, case, cid), True)
ctrl = pd.concat([pd.read_parquet(os.path.join(V1, f"controls_{v}_{d}.parquet")) for v in ["day", "precise"] for d in DES], ignore_index=True)
ep_ids = {}
for v in ["day", "precise"]:
    for d in DES:
        ep_ids[(v, d)] = pd.read_parquet(os.path.join(V1, f"episodes_{v}_{d}.parquet"))
epi = pd.concat(ep_ids.values(), ignore_index=True)
LS = wallets[["wallet", "case_id", "label_strict", "label_standard", "label_broad"]]
epi = epi.merge(LS, on=["wallet", "case_id"], how="left")
for x in ["label_strict", "label_standard", "label_broad"]:  # A20: only suspected rows carry a label set (before the A35 role split below)
    epi[x] = epi[x].fillna(False).astype(bool) & (epi.role == "suspected")
epi["t_news_reliable"] = [REL_M.get((a, b), True) for a, b in zip(epi.case_id, epi.condition_id.str.lower())]
epi["case_share_of_lifetime_volume"] = epi.case_share_of_lifetime_volume.clip(upper=1.0)  # A43: the lifetime denominator is rounded to cents
_alg = set(zip(ALG.wallet, ALG.case_id, ALG.condition_id, ALG.side.str.lower()))  # A35
epi["is_alleged_position"] = [(w.lower(), k, cid.lower(), str(o).lower()) in _alg for w, k, cid, o in zip(epi.wallet, epi.case_id, epi.condition_id, epi.outcome_label)]
epi["is_alleged_position"] = epi.is_alleged_position & (epi.role == "suspected")
epi.loc[(epi.role == "suspected") & ~epi.is_alleged_position, "role"] = "labelled_other_position"
write("controls", ctrl)
write("episodes", epi.drop(columns=[x for x in epi.columns if x not in [k["name"] for k in TABLES["episodes"]["cols"]] and x not in RENAME["episodes"]]))
# positions with label columns, assembled in DuckDB and streamed to parquet (pandas does not fit the memory limit)
DT = {"string": "VARCHAR", "int64": "BIGINT", "float64": "DOUBLE", "bool": "BOOLEAN", "timestamp": "TIMESTAMPTZ"}
doc = wallets[wallets.is_documented][["wallet", "case_id", "doc_grade"]].assign(is_documented=True)
fr = CC.sort_values("trigger_utc").drop_duplicates(["candidate_wallet", "case_id", "condition_id", "asset_id", "t_news_version"])
fr = fr.rename(columns={"candidate_wallet": "wallet", "trigger_wallet": "triggering_suspect"})[["wallet", "case_id", "condition_id", "asset_id", "t_news_version", "triggering_suspect"]]
fr = fr.assign(placebo_rate=fr.t_news_version.map(lambda v: PR[v]["placebo_to_real_ratio"]))
hn = HN[HN.rule != "cleared_case_wallet"][["market_set", "case_id", "condition_id", "asset_id", "wallet", "t_news_version", "rule"]].rename(columns={"rule": "hard_negative_rule"})
ctl = ctrl[ctrl.control_design == "standard"][["t_news_version", "case_id", "condition_id", "wallet"]].drop_duplicates()
rel = pd.DataFrame([dict(market_set="case", case_id=a, condition_id=b, rel=v) for (a, b), v in REL_M.items()]
                   + [dict(market_set=ms, case_id=a, condition_id=b, rel=v) for (ms, a, b), v in REL_REF.items()])
alg_df = ALG[["wallet", "case_id", "condition_id", "side"]].drop_duplicates().assign(side=lambda d: d.side.str.lower())
for nm, df in [("doc_df", doc), ("fr_df", fr), ("ls_df", LS), ("hn_df", hn), ("ctl_df", ctl), ("rel_df", rel), ("alg_df", alg_df)]:
    c.register(nm, df)
c.sql(f"""CREATE TEMP VIEW pos_v AS SELECT p.*, d.doc_grade AS doc_grade_d, (d.wallet IS NOT NULL) AS doc_hit,
            (f.wallet IS NOT NULL) AS coordinated_rule_fired, f.triggering_suspect, f.placebo_rate,
            coalesce(l.label_strict, false) ls_s, coalesce(l.label_standard, false) ls_t, coalesce(l.label_broad, false) ls_b,
            h.hard_negative_rule, (h.hard_negative_rule IS NOT NULL) AS hard_negative, (k.wallet IS NOT NULL) AS ctl_hit, coalesce(r.rel, true) AS t_news_reliable,
            (p.market_set = 'case' AND ag.wallet IS NOT NULL) AS is_alleged_position
          FROM '{V1}/positions.parquet' p
          LEFT JOIN alg_df ag ON ag.wallet = p.wallet AND ag.case_id = p.case_id AND ag.condition_id = lower(p.condition_id) AND ag.side = lower(p.outcome_label)
          LEFT JOIN rel_df r ON r.market_set = p.market_set AND r.case_id = p.case_id AND r.condition_id = lower(p.condition_id)
          LEFT JOIN doc_df d ON d.wallet = p.wallet AND d.case_id = p.case_id
          LEFT JOIN fr_df f ON p.market_set = 'case' AND f.wallet = p.wallet AND f.case_id = p.case_id AND f.condition_id = p.condition_id AND f.asset_id = p.asset_id AND f.t_news_version = p.t_news_version
          LEFT JOIN ls_df l ON l.wallet = p.wallet AND l.case_id = p.case_id
          LEFT JOIN hn_df h ON h.market_set = p.market_set AND h.case_id = p.case_id AND h.condition_id = p.condition_id AND h.asset_id = p.asset_id AND h.wallet = p.wallet AND h.t_news_version = p.t_news_version
          LEFT JOIN ctl_df k ON k.t_news_version = p.t_news_version AND k.case_id = p.case_id AND k.condition_id = p.condition_id AND k.wallet = p.wallet""")
expr = dict(is_documented="(market_set = 'case' AND doc_hit)", doc_grade="CASE WHEN market_set = 'case' THEN doc_grade_d END",
            label_strict="(market_set = 'case' AND ls_s)", label_standard="(market_set = 'case' AND ls_t)", label_broad="(market_set = 'case' AND ls_b)",
            is_control="(market_set = 'case' AND ctl_hit)", is_placebo_market="(market_set = 'placebo')", is_twin_market="(market_set = 'twin')")
inv = {v: k for k, v in RENAME["positions"].items()}
sel = ", ".join(f"CAST({expr.get(col['name'], inv.get(col['name'], col['name']))} AS {DT[col['dtype']]}) AS {col['name']}" for col in TABLES["positions"]["cols"])
c.sql(f"COPY (SELECT {sel} FROM pos_v ORDER BY market_set, case_id, condition_id, t_news_version, wallet, asset_id) TO '{OUT}/positions.parquet' (FORMAT parquet, COMPRESSION zstd)")
if any(col["dtype"] == "timestamp" for col in TABLES["positions"]["cols"]):  # DuckDB writes TIMESTAMPTZ in microseconds; cast to the schema (seconds, UTC)
    _src = os.path.join(OUT, "positions.parquet"); _tmp = _src + ".cast_tmp"; _sch = schema_of("positions")
    with pq.ParquetWriter(_tmp, _sch, compression="zstd") as _w:
        for _b in pq.ParquetFile(_src).iter_batches(batch_size=500_000):
            _w.write_table(pa.Table.from_batches([_b]).cast(_sch))
    os.replace(_tmp, _src)
print("positions", c.sql(f"SELECT count(*) FROM '{OUT}/positions.parquet'").fetchall(), flush=True)
# weak labels + gate counts
gc = c.sql(f"""SELECT wallet, t_news_version, sum(gate1::INT) gate1, sum(gate2a::INT) gate2a, sum(gate2b::INT) gate2b
               FROM '{OUT}/positions.parquet' GROUP BY 1, 2""").df().set_index(["wallet", "t_news_version"]).unstack()
gc.columns = [f"{a}_n" + ("" if b == "precise" else "_day") for a, b in gc.columns]
wl = pd.read_parquet(os.path.join(D, "out", "weak_labels.parquet")).rename(columns={"address": "wallet"})
wl = wl.merge(gc.reset_index(), on="wallet", how="left")
wf = CC.assign(v_rank=CC.t_news_version.map({"precise": 0, "day": 1})).sort_values(["v_rank", "trigger_utc"])
first = wf.drop_duplicates("candidate_wallet").set_index("candidate_wallet")
wl["coordinated_rule_fired"] = wl.wallet.isin(set(CC[CC.t_news_version == "precise"].candidate_wallet))
wl["coordinated_rule_fired_day"] = wl.wallet.isin(set(CC[CC.t_news_version == "day"].candidate_wallet))
wl["triggering_suspect"] = wl.wallet.map(first.trigger_wallet)
wl["placebo_rate"] = wl.wallet.map(first.t_news_version).map(lambda v: PR[v]["placebo_to_real_ratio"] if isinstance(v, str) else np.nan)
wl["gate_scope"] = np.where(wl.gate1_n.notna(), "case_placebo_or_twin_markets", "not_in_case_placebo_or_twin_markets")
wl["acdc_class"] = wl.acdc_class.replace("", None)
_mm = pd.read_parquet(os.path.join(V1, "market_makers.parquet"), columns=["wallet", "is_market_maker"])  # A34.1 reporting flag
wl = wl.merge(_mm, on="wallet", how="left"); wl["is_market_maker"] = wl.is_market_maker.fillna(False).astype(bool)
wl = cast("weak_labels", wl)
pq.write_table(pa.Table.from_pandas(wl, schema=schema_of("weak_labels"), preserve_index=False), os.path.join(OUT, "weak_labels.parquet"), compression="zstd")
print("weak_labels", len(wl), flush=True)
del wl
mm = pd.read_parquet(os.path.join(V1, "market_minutes.parquet")).rename(columns={})
mm["t_news_reliable"] = [rel_of(a, b, c_.lower()) for a, b, c_ in zip(mm.market_set, mm.case_id, mm.condition_id)]  # A29.1
write("market_minutes", mm)
# fills: written by build/v1/fills_release.py (streaming COPY)
