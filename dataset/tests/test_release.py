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
    tw = load("twin_markets"); assert set(pos[pos.market_set == "twin"].condition_id) <= set(tw.twin_condition_id.dropna())
    assert set(zip(tw.case_id, tw.case_condition_id)) <= mkeys and set(zip(pl.case_id, pl.case_condition_id)) <= mkeys
    hn = load("hard_negatives"); assert set(hn.case_id) <= cases
    wk = set(zip(load("wallets").wallet, load("wallets").case_id))
    lk = load("claim_wallet_links"); assert set(lk.claim_id) <= set(load("claims").claim_id) and set(zip(lk.wallet, lk.case_id)) <= wk
    assert set(load("cases").case_id) == cases and set(mk.case_id) <= cases
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
    p = load("positions", ["t_news_version", "first_buy_unix", "last_buy_unix", "t_cut_unix", "first_fill_in_market_unix"])
    p = p[p.t_news_version == v]
    assert (p.first_buy_unix < p.t_cut_unix).all() and (p.last_buy_unix < p.t_cut_unix).all() and (p.first_fill_in_market_unix < p.t_cut_unix).all()
    e = load("episodes"); e = e[e.t_news_version == v]
    assert (e.hours_first_buy_to_tnews.dropna() > 0).all() and (e.hours_last_buy_to_tnews.dropna() > 0).all()
    # recompute buy_usdc_pre for documented positions from fills with ts < cut
    pp = load("positions", ["market_set", "case_id", "condition_id", "asset_id", "wallet", "t_news_version", "t_cut_unix", "buy_usdc_pre", "is_documented"])
    pp = pp[(pp.t_news_version == v) & pp.is_documented]
    if WITHHELD:  # only positions whose pre-cut legs are all in shipped files can be recomputed
        src = load("positions", ["market_set", "case_id", "condition_id", "asset_id", "wallet", "t_news_version", "source_pre"])
        pp = pp.merge(src, on=["market_set", "case_id", "condition_id", "asset_id", "wallet", "t_news_version"])
        pp = pp[pp.source_pre == "hf_polymarket_v1"].drop(columns="source_pre")
    con = duckdb.connect(); con.register("pp", pp)
    d = con.sql(f"""SELECT pp.buy_usdc_pre, sum(f.usdc) re FROM pp JOIN read_parquet('{R}/fills_part*_case_*.parquet') f
                    ON f.condition_id = pp.condition_id AND f.asset_id = pp.asset_id AND f.wallet = pp.wallet AND f.wallet_side = 'BUY' AND f.ts_unix < pp.t_cut_unix
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


def test_label_sets_nested():
    """A20: strict <= standard <= broad = is_documented, in wallets, episodes and positions."""
    for t in ["wallets", "episodes", "positions"]:
        d = load(t, ["label_strict", "label_standard", "label_broad"] + (["is_documented"] if t != "episodes" else []))
        assert (~d.label_strict | d.label_standard).all() and (~d.label_standard | d.label_broad).all(), t
        if t != "episodes":
            assert (d.label_broad == d.is_documented).all(), t


def test_hard_negatives_are_never_positives():
    p = load("positions", ["hard_negative", "is_documented", "coordinated_rule_fired"])
    assert not (p.hard_negative & (p.is_documented | p.coordinated_rule_fired)).any()
    w = load("wallets"); assert not (w.hard_negative & w.label_broad).any()


def test_api_rows_have_null_role_fields():
    """A24: one fills schema; fields a source lacks are NULL with role_fields_available = false."""
    bad = duckdb.sql(f"""SELECT count(*) FROM read_parquet('{R}/fills_part*.parquet') WHERE (source = 'data_api_v2') AND
                         (role_fields_available OR wallet_role IS NOT NULL OR aggressor_side IS NOT NULL OR maker IS NOT NULL OR taker IS NOT NULL OR fee_usdc IS NOT NULL)""").fetchall()[0][0]
    assert bad == 0
    assert duckdb.sql(f"SELECT count(*) FROM read_parquet('{R}/fills_part*.parquet') WHERE source = 'hf_polymarket_v1' AND NOT role_fields_available").fetchall()[0][0] == 0


def test_no_duplicates_at_source_boundary():
    """A24: no Data API case row at or before the Polymarket-v1 end for a market in Polymarket-v1; no cross-source twins within 60 s."""
    if WITHHELD:
        pytest.skip("Data API rows withheld in this package")
    q = f"read_parquet('{R}/fills_part*.parquet')"
    early = duckdb.sql(f"""SELECT count(*) FROM {q} a WHERE a.source = 'data_api_v2' AND a.market_set = 'case' AND a.ts_unix <= 1777374040
                           AND a.condition_id IN (SELECT DISTINCT condition_id FROM {q} WHERE source = 'hf_polymarket_v1')""").fetchall()[0][0]
    assert early == 0
    dup = duckdb.sql(f"""WITH a AS (SELECT * FROM {q} WHERE source = 'data_api_v2' AND ts_unix BETWEEN 1777374040 - 3600 AND 1777374040 + 3600),
                              h AS (SELECT * FROM {q} WHERE source = 'hf_polymarket_v1' AND ts_unix BETWEEN 1777374040 - 3600 AND 1777374040 + 3600)
                         SELECT count(*) FROM a JOIN h ON a.condition_id = h.condition_id AND a.wallet = h.wallet AND a.wallet_side = h.wallet_side
                              AND abs(a.usdc - h.usdc) < 0.01 AND abs(a.ts_unix - h.ts_unix) <= 60""").fetchall()[0][0]
    assert dup == 0


UNIT = re.compile(r"(usdc|usd|shares|utc|unix|hours|days|minutes|price|share|rate|ratio|score|rank|decile|seq|number|year|hour_of_day|win_rate|cv_ratio)")


@pytest.mark.parametrize("t", list(TABLES))
def test_numeric_columns_carry_units(t):
    """A24: numeric amount, size, price, time or duration columns name their unit; counts start with n_."""
    bad = [c["name"] for c in TABLES[t]["cols"] if c["dtype"] in ("int64", "float64") and not c["name"].startswith("n_") and not UNIT.search(c["name"])
           and not c["name"].startswith(("f2_", "gate1_", "f5_"))]
    assert not bad, (t, bad)


def test_market_cut_not_after_sourced_case_time():
    """A25/A25.1: per-market cuts never fall after the case's sourced exact time nor after the day-level case date ends."""
    m = load("markets", ["question", "t_news_precision", "t_news_utc", "t_news_precise_utc", "t_news_precise_precision", "t_news_market_utc", "t_news_market_day_utc", "t_news_market_method"])
    m = m[m.t_news_market_utc.notna()]
    sourced = m.t_news_precise_precision != "day_fallback"
    assert (m[sourced].t_news_market_utc <= m[sourced].t_news_precise_utc).all()
    dl = m[m.t_news_market_method == "market_deadline"]
    assert (dl.t_news_precision != "day").all() and (dl.t_news_market_utc >= dl.t_news_utc).all()  # A25 rule 2: only inside a coarse date
    dq = re.compile(r"\b(?:by|before)\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec|end of|\d{4}|q[1-4])", re.I)
    assert not m[(m.t_news_market_method == "scheduled_start") & m.question.fillna("").str.contains(dq)].shape[0]  # A25.2
    assert (m[m.t_news_market_method == "case_time"].t_news_market_utc == m[m.t_news_market_method == "case_time"].t_news_precise_utc).all()


def test_positions_use_market_cut():
    """A25: positions' cut is the market's own cut in both versions."""
    m = load("markets", ["case_id", "condition_id", "t_news_market_utc", "t_news_market_day_utc"])
    p = load("positions", ["market_set", "case_id", "condition_id", "t_news_version", "t_cut_unix"])
    p = p[p.market_set == "case"].drop_duplicates(["case_id", "condition_id", "t_news_version"]).merge(m, on=["case_id", "condition_id"])
    exp = p.t_news_market_utc.where(p.t_news_version == "precise", p.t_news_market_day_utc)
    assert len(p) and (exp.map(lambda x: int(x.timestamp())).values == p.t_cut_unix.values).all()


def test_strict_requires_prenews_buy():
    """A26: every label_strict wallet bought before a case market's precise cut; strict_no_prenews is disjoint from strict and within standard."""
    w = load("wallets", ["wallet", "label_strict", "label_standard", "strict_no_prenews"])
    assert not (w.label_strict & w.strict_no_prenews).any() and (~w.strict_no_prenews | w.label_standard).all()
    p = load("positions", ["market_set", "wallet", "t_news_version"])
    pre = set(p[(p.market_set == "case") & (p.t_news_version == "precise")].wallet)
    assert set(w[w.label_strict].wallet) <= pre


def test_control_designs():
    """A27: three control designs; suspected episodes identical across designs; age-matched controls share the episode's age band."""
    e = load("episodes", ["t_news_version", "control_design", "role", "episode_id"])
    assert set(e.control_design) == {"standard", "age_matched", "winrate_matched", "open"}
    s = e[e.role == "suspected"].groupby(["t_news_version", "control_design"]).episode_id.apply(frozenset)
    for v in ["day", "precise"]:
        assert s[v]["standard"] == s[v]["age_matched"] == s[v]["winrate_matched"] == s[v]["open"]


def test_label_sets_exclude_non_informed_families():
    """A19/A28: only informed_trading wallets carry a label set."""
    w = load("wallets", ["label_family", "label_broad"])
    assert (w[w.label_broad].label_family == "informed_trading").all()


def test_relaxed_band_only_in_banded_designs():
    """A33: relaxed_band only on control rows of age_matched / winrate_matched."""
    e = load("episodes", ["control_design", "role", "relaxed_band"])
    assert not e[e.role == "suspected"].relaxed_band.any()
    assert not e[e.control_design.isin(["standard", "open"])].relaxed_band.any()
    c = load("controls", ["control_design", "relaxed_band"])
    assert not c[c.control_design.isin(["standard", "open"])].relaxed_band.any()


def test_t_news_reliable():
    """A29.1: per market; false only for a deadline-rule time; episodes carry their market's flag; placebo/twin rows their case market's."""
    m = load("markets", ["case_id", "condition_id", "t_news_reliable", "t_news_market_method", "t_news_deadline_rule_utc", "t_news_market_utc"])
    assert (m.t_news_reliable == (m.t_news_market_method != "market_deadline")).all()
    dl = m[m.t_news_market_method == "market_deadline"]
    assert (dl.t_news_deadline_rule_utc == dl.t_news_market_utc).all() and m[m.t_news_market_method != "market_deadline"].t_news_deadline_rule_utc.isna().all()
    rel = dict(zip(zip(m.case_id, m.condition_id), m.t_news_reliable))
    e = load("episodes", ["case_id", "condition_id", "t_news_reliable"]).drop_duplicates()
    assert (e.t_news_reliable.values == [rel.get(k, True) for k in zip(e.case_id, e.condition_id)]).all()
    for t in ["positions", "market_minutes"]:
        d = duckdb.sql(f"SELECT DISTINCT case_id, condition_id, t_news_reliable FROM read_parquet('{R}/{t}.parquet') WHERE market_set = 'case'").df()
        assert (d.t_news_reliable.values == [rel.get(k, True) for k in zip(d.case_id, d.condition_id)]).all(), t
        assert duckdb.sql(f"SELECT count(*) FROM (SELECT market_set, case_id, condition_id FROM read_parquet('{R}/{t}.parquet') GROUP BY ALL HAVING count(DISTINCT t_news_reliable) > 1)").fetchall()[0][0] == 0, t


def test_scheduled_starts_before_close():
    """A30: every scheduled-start cut is in logs/scheduled_start_check.csv with a close after it."""
    ck = pd.read_csv(os.path.join(D, "logs", "scheduled_start_check.csv"))
    m = load("markets", ["case_id", "condition_id", "t_news_market_method"])
    s = m[m.t_news_market_method == "scheduled_start"].merge(ck, on=["case_id", "condition_id"], how="left")
    assert s.decision.eq("scheduled_start").all() and (pd.to_datetime(s.scheduled_start_utc) < pd.to_datetime(s.close_utc)).all()
    bad = ck[ck.disagreement.astype(str) == "True"]
    assert not set(zip(bad.case_id, bad.condition_id)) & set(zip(s.case_id, s.condition_id))


def test_links_only_from_alleging_claims():
    """A31: claim_wallet_links only from claims with stance alleges or confirms."""
    L = load("claim_wallet_links", ["claim_id"]); c = load("claims", ["claim_id", "stance"])
    assert set(L.claim_id) <= set(c[c.stance.isin(["alleges", "confirms"])].claim_id)


def test_few_fold_results_have_no_headline_number():
    """A32: below 6 folds the summary carries fold values and min/max, no mean or SD."""
    B = json.load(open(os.path.join(PKG, "benchmarks", "baselines.json")))
    n = 0
    for v in ["precise", "day"]:
        for s_ in B["label_sets"]:
            for t, r in B[v][s_].items():
                for m, x in r["summary"].items():
                    if x["n_loco_folds"] < B["min_folds_for_summary"]:
                        assert "loco_mean" not in x and "loco_sd" not in x and "fold_values" in x, (v, s_, t, m); n += 1
    assert n > 0
