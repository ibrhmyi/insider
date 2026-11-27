"""Phase F quality gates for the PMITC release packages. Run from dataset/:
    python3 -m pytest -q tests                              (release/, all files)
    PMITC_RELEASE=release_safe python3 -m pytest -q tests   (release_safe/, without data_api_v2 fill files)
Reads <package>/data, <package>/MANIFEST.json and the source CSVs. Each test names the gate it implements.
"""
import glob, hashlib, json, os, re, sys
import duckdb, pandas as pd, pyarrow.parquet as pq, pytest

D = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PKG = os.path.join(D, os.environ.get("PMITC_RELEASE", "release"))
R = os.path.join(PKG, "data")
MAN = json.load(open(os.path.join(PKG, "MANIFEST.json")))
WITHHELD = set(MAN.get("withheld_sources", []))  # release_safe: {"data_api_v2"}
sys.path.insert(0, os.path.join(D, "build", "v1"))
from schema import TABLES  # noqa

ARROW = {"string": "string", "int64": "int64", "float64": "double", "bool": "bool", "timestamp": "timestamp[s, tz=UTC]", "date": "date32[day]"}
ADDR = re.compile(r"^0x[0-9a-f]{40}$")
SINGLE = [t for t in TABLES if t != "fills"]


def load(t, cols=None):
    if t == "fills":
        return duckdb.sql(f"SELECT {', '.join(cols) if cols else '*'} FROM read_parquet('{R}/fills_part*.parquet')")
    return pd.read_parquet(os.path.join(R, f"{t}.parquet"), columns=cols)


def files_of(t):
    return sorted(glob.glob(os.path.join(R, "fills_part*.parquet"))) if t == "fills" else [os.path.join(R, f"{t}.parquet")]


@pytest.mark.parametrize("t", list(TABLES))
def test_schema_dtypes_and_columns(t):
    """Schema: explicit dtypes, snake_case, one CODEBOOK entry per column."""
    want = [(c["name"], ARROW[c["dtype"]]) for c in TABLES[t]["cols"]]
    for f in files_of(t):
        got = [(x.name, re.sub(r"timestamp\[(s|ms|us|ns), tz=UTC\]", "timestamp[s, tz=UTC]", str(x.type))) for x in pq.read_schema(f)]
        assert got == want, f
    assert all(re.fullmatch(r"[a-z][a-z0-9_@]*", c["name"]) for c in TABLES[t]["cols"])
    cb = open(os.path.join(PKG, "docs", "CODEBOOK.md")).read()
    for c in TABLES[t]["cols"]:
        assert f"| `{c['name']}` |" in cb.split(f"## {t}\n")[1].split("\n## ")[0], (t, c["name"])


@pytest.mark.parametrize("t", SINGLE)
def test_allowed_values_and_no_empty_strings(t):
    df = load(t)
    for c in TABLES[t]["cols"]:
        s = df[c["name"]]
        if c["dtype"] == "string":
            assert not (s == "").any(), (t, c["name"], "empty string instead of NULL")
        if c["allowed"] and c["dtype"] == "string" and c["name"] not in ("platform", "family"):
            vals = {tok for v in s.dropna() for tok in (v.split(";") if c["name"] == "label_family" else [v])}
            bad = vals - set(c["allowed"].split(";"))
            assert not bad, (t, c["name"], bad)


@pytest.mark.parametrize("t", list(TABLES))
def test_primary_keys_unique(t):
    pk = [c["name"] for c in TABLES[t]["cols"] if c["pk"]]
    if not pk:
        pytest.skip("no primary key declared")
    if t == "fills":
        n, u = duckdb.sql(f"SELECT count(*), count(DISTINCT leg_id) FROM read_parquet('{R}/fills_part*.parquet')").fetchall()[0]
        assert n == u
    else:
        assert not load(t).duplicated(pk).any()


def test_foreign_keys():
    cases = set(load("cases").case_id)
    assert set(load("claims").case_id) <= cases
    assert set(load("wallets").case_id) <= cases
    mk = load("markets"); mkeys = set(zip(mk.case_id, mk.condition_id))
    ep = load("episodes"); assert set(zip(ep.case_id, ep.condition_id)) <= mkeys
    ct = load("controls"); assert set(ct.episode_id) <= set(ep.episode_id.dropna())
    pos = load("positions", ["market_set", "case_id", "condition_id"]).drop_duplicates()
    assert set(map(tuple, pos[pos.market_set == "case"][["case_id", "condition_id"]].values)) <= mkeys
    pl = load("placebo_markets"); assert set(pos[pos.market_set == "placebo"].condition_id) <= set(pl.placebo_condition_id.dropna())
    assert set(load("contradictions").claim_id) <= set(load("claims").claim_id)


def test_every_wallet_in_fills_or_flagged():
    w = load("wallets")
    seen = {r[0] for r in duckdb.sql(f"SELECT DISTINCT wallet FROM read_parquet('{R}/fills_part*.parquet')").fetchall()}
    if WITHHELD:  # wallets whose only fills are in withheld files still appear in positions (derived aggregates)
        seen |= set(load("positions", ["wallet"]).wallet) | set(MAN.get("wallets_confirmed_only_by_withheld_sources", []))
    missing = w[~w.wallet.isin(seen)]
    assert (missing.trade_confirmed == False).all(), missing[["wallet", "case_id"]]  # noqa: E712


def test_address_format():
    """40 hex chars, lower case, in address columns; prefixes only in claims.subject / free text."""
    for t, cols in [("wallets", ["wallet"]), ("positions", ["wallet"]), ("episodes", ["wallet"]), ("controls", ["wallet"]), ("weak_labels", ["wallet"]), ("edges", ["src", "dst"])]:
        df = load(t, cols)
        for c in cols:
            s = df[c].dropna(); bad = s[~s.str.match(ADDR)]
            assert bad.empty, (t, c, bad.head().tolist())
    n_bad = duckdb.sql(f"""SELECT count(*) FROM read_parquet('{R}/fills_part*.parquet')
                          WHERE NOT regexp_full_match(wallet, '0x[0-9a-f]{{40}}')""").fetchall()[0][0]
    assert n_bad == 0
    for c in ["condition_id"]:
        s = load("markets")[c]; assert s.str.match(r"^0x[0-9a-f]{64}$").all()


NAMES = {x.strip() for x in open(os.path.join(D, "tests", "name_hashes.txt")) if x.strip() and not x.startswith("#")}


def ngrams(v, k=3):
    w = re.findall(r"[a-z]+", v.lower())
    return {" ".join(w[i:i + n]) for n in range(1, k + 1) for i in range(len(w) - n + 1)}
FREE = {"cases": ["title", "status_note"], "claims": ["subject", "claim_text", "source_name", "notes"], "wallets": ["handle", "notes", "source"],
        "markets": ["question", "reason"], "contradictions": ["evidence", "claimed_value", "observed_value"], "edges": ["source"]}


def test_no_personal_names():
    """Name-list test on every free-text column (URLs excluded: official file names and slugs may carry names)."""
    hits = []
    for t, cols in FREE.items():
        df = load(t)
        for c in cols:
            for v in df[c].dropna():
                for g in ngrams(v):
                    if hashlib.sha256(g.encode()).hexdigest() in NAMES:
                        hits.append((t, c, v[:80]))
    assert not hits, hits


def test_name_surname_pattern_reviewed():
    """Regex 'Name Surname' hits must all be in tests/name_review.csv (reviewed by hand: public figures, outlets, places)."""
    rev = pd.read_csv(os.path.join(D, "tests", "name_review.csv"), dtype=str)
    ok = set(rev.phrase)
    pat = re.compile(r"\b[A-Z][a-z]+(?: [A-Z][a-z]+)+\b")
    new = set()
    for t, cols in FREE.items():
        df = load(t)
        for c in cols:
            for v in df[c].dropna():
                new |= {m for m in pat.findall(v) if m not in ok}
    assert not new, sorted(new)


@pytest.mark.parametrize("v", ["day", "precise"])
def test_no_pre_news_feature_uses_post_news_fill(v):
    """Leakage: positions/episodes/controls pre features only use fills before the cut (both versions)."""
    p = load("positions", ["t_news_version", "first_buy_ts", "last_buy_ts", "t_cut_ts", "first_fill_in_market_ts"])
    p = p[p.t_news_version == v]
    assert (p.first_buy_ts < p.t_cut_ts).all() and (p.last_buy_ts < p.t_cut_ts).all() and (p.first_fill_in_market_ts < p.t_cut_ts).all()
    e = load("episodes"); e = e[e.t_news_version == v]
    assert (e.hours_first_buy_to_tnews.dropna() > 0).all() and (e.hours_last_buy_to_tnews.dropna() > 0).all()
    # recompute buy_usdc_pre for documented positions from fills with ts < cut
    pp = load("positions", ["market_set", "case_id", "condition_id", "asset_id", "wallet", "t_news_version", "t_cut_ts", "buy_usdc_pre", "is_documented"])
    pp = pp[(pp.t_news_version == v) & pp.is_documented]
    if WITHHELD:  # only positions whose pre-cut legs are all in shipped files can be recomputed
        src = load("positions", ["market_set", "case_id", "condition_id", "asset_id", "wallet", "t_news_version", "source_pre"])
        pp = pp.merge(src, on=["market_set", "case_id", "condition_id", "asset_id", "wallet", "t_news_version"])
        pp = pp[pp.source_pre == "hf_polymarket_v1"].drop(columns="source_pre")
    con = duckdb.connect(); con.register("pp", pp)
    d = con.sql(f"""SELECT pp.buy_usdc_pre, sum(f.usdc) re FROM pp JOIN read_parquet('{R}/fills_part*_case_*.parquet') f
                    ON f.condition_id = pp.condition_id AND f.asset_id = pp.asset_id AND f.wallet = pp.wallet AND f.wallet_side = 'BUY' AND f.ts < pp.t_cut_ts
                    GROUP BY pp.case_id, pp.condition_id, pp.asset_id, pp.wallet, pp.buy_usdc_pre""").df()
    assert len(d) == len(pp) and ((d.buy_usdc_pre - d.re).abs() < 1e-6 * (1 + d.re)).all()


def test_manifest_hashes():
    """Rebuild test (final stage): every file's SHA-256 matches MANIFEST.json (rebuild with build/v1/tables.py reproduces them)."""
    for f in MAN["files"]:
        p = os.path.join(PKG, f["path"])
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        assert h == f["sha256"], f["path"]


def test_fill_counts_reconcile():
    log = pd.read_csv(os.path.join(D, "logs", "fills_counts_by_case.csv"))
    log = log[~log.source.isin(WITHHELD)]
    mk = load("markets")[["case_id", "condition_id"]]
    con = duckdb.connect(); con.register("mk", mk)
    got = con.sql(f"""SELECT mk.case_id, f.source, count(*) legs FROM mk JOIN read_parquet('{R}/fills_part*_case_*.parquet') f USING (condition_id)
                      GROUP BY 1, 2""").df()
    m = log.merge(got, on=["case_id", "source"], how="outer", suffixes=("_log", "_rel"))
    assert (m.legs_log == m.legs_rel).all(), m[m.legs_log != m.legs_rel]


def test_amount_checks_recorded():
    a = pd.read_csv(os.path.join(D, "logs", "amount_checks.csv"))
    cx = load("contradictions")
    assert set(a[a.over_10pct].claim_id) <= set(cx[cx.phase == "run7_amount_check"].claim_id)


def test_no_bytecode_in_package():
    """R3: no __pycache__ or .pyc in the package or its manifest."""
    assert not [p for p in glob.glob(os.path.join(PKG, "**", "*"), recursive=True) if "__pycache__" in p or p.endswith(".pyc")]
    assert not [f for f in MAN["files"] if "__pycache__" in f["path"] or f["path"].endswith(".pyc")]


def test_rule_output_not_a_wallet_label():
    """A17: no L4_coordinated rows in wallets; the rule output lives in positions / weak_labels."""
    w = load("wallets")
    assert not (w.label_tier == "L4_coordinated").any()
    assert (w.is_documented == ((w.polarity == "suspected") & w.trade_confirmed & (w.label_family == "informed_trading"))).all()  # A19


def test_withheld_sources_absent():
    for s in WITHHELD:
        assert not glob.glob(os.path.join(R, f"fills_part*_{s}.parquet"))
        assert duckdb.sql(f"SELECT count(*) FROM read_parquet('{R}/fills_part*.parquet') WHERE source = '{s}'").fetchall()[0][0] == 0
