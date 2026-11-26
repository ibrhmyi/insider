"""Phase 2: markets.csv, one row per (case, market), with the full Gamma-event ladder and t_news (PROTOCOL A6.5, A6.6).

Every case is listed in CASE_MARKETS (selected Gamma events / FFIC prefixes / HF slugs, each with found_via and a
reason taken from the claims) or in NO_MARKET (with the reason no market is attached). Nothing is attached by guess.
Inputs: data/cases.csv, data/claims.csv, out/hf_market_catalog.parquet (build/hf_catalog.py), ForesightFlow clone
(argv[1], for FFIC and t_news files). Gamma responses are cached under logs/gamma_raw/events/.
Outputs: data/markets.csv, logs/markets_not_found.csv
"""
import csv, json, os, re, sys, time, urllib.parse, urllib.request
import duckdb

sys.path.insert(0, os.path.dirname(__file__))
from dates import parse_date  # noqa: E402  (PROTOCOL A6.3 parser)

D = os.path.join(os.path.dirname(__file__), "..")
FF = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ext/ForesightFlow_datasets"
CACHE = os.path.join(D, "logs", "gamma_raw", "events"); os.makedirs(CACHE, exist_ok=True)
CAT = os.path.join(D, "out", "hf_market_catalog.parquet")

E, P, S = "event", "ffic_prefix", "hf_slug"
# case_id: [(kind, value, found_via, reason)]
CASE_MARKETS = {
 "maduro-2026-01": [(E, "maduro-out-in-2025", "gamma_search+claimed_wallets", "claims name 'Maduro out by January 31, 2026'; 7 of 12 case wallets traded this event")],
 "railgun-venezuela-control": [(E, "maduro-out-in-2025", "claimed_wallets", "37 of 71 one-bet accounts"),
                               (E, "us-x-venezuela-military-engagement-by", "claimed_wallets", "21 of 71 accounts"),
                               (E, "us-forces-in-venezuela-by", "claimed_wallets", "8 of 71 accounts")],
 "us-iran-strike-2026-02-28": [(E, "us-strikes-iran-by", "gamma_search+claimed_wallets", "claims name 'US strikes Iran by Feb 28'; 52 of 60 case wallets")],
 "bubblemaps-military-cluster": [(E, "us-strikes-iran-by", "claimed_wallets", "claims name strike markets; 2 of 2 wallets"),
                                 (E, "khamenei-out-as-supreme-leader-of-iran-by-march-31", "claimed_wallets", "claims name Khamenei markets; wallet traded"),
                                 (E, "us-x-iran-ceasefire-by", "gamma_search", "claims name ceasefire markets")],
 "khamenei-removal-2026": [(E, "khamenei-out-as-supreme-leader-of-iran-by-march-31", "gamma_search", "claim: out by end of March")],
 "us-iran-ceasefire-2026-03": [(E, "us-x-iran-ceasefire-by", "gamma_search", "claim: ceasefire by March 31")],
 "us-iran-ceasefire-2026-04-07": [(E, "us-x-iran-ceasefire-by", "gamma_search+claimed_wallets", "3 of 3 case wallets; FFIC lists 'US x Iran ceasefire by April 7'")],
 "us-iran-strike-2025-06": [(E, "us-military-action-against-iran-by-friday", "gamma_search", "claims: bets on the June 21 2025 strike"),
                            (E, "us-military-action-against-iran-by-saturday", "gamma_search", "same"),
                            (E, "us-military-action-against-iran-by-sunday-225", "gamma_search", "same"),
                            (E, "us-military-action-against-iran-before-july", "gamma_search", "same")],
 "israel-rising-lion-2025-06": [(E, "israel-military-action-against-iran-by-friday-477", "claimed_wallets", "case wallet traded; June 13 2025 strike"),
                                (E, "israel-strike-on-iran-on", "claimed_wallets", "case wallet's largest buy"),
                                (E, "israel-military-action-against-iran-before-july", "claimed_wallets", "case wallet traded")],
 "israel-strike-2025-06-week": [(E, "israel-military-action-against-iran-by-friday-477", "gamma_search", "claim: Israel would strike Iran that week (June 11-13 2025)")],
 "iran-strike-2024-10": [(P, "0xc1b6d712", "ffic_prefix", "FFIC fficd-002"), (P, "0x93727420", "ffic_prefix", "FFIC fficd-002"), (P, "0xc8312853", "ffic_prefix", "FFIC fficd-002")],
 "election-2024": [(P, "0xdd22472e", "ffic_prefix", "FFIC fficd-001"), (P, "0xc6485bb7", "ffic_prefix", "FFIC fficd-001"),
                   (P, "0x55c55189", "ffic_prefix", "FFIC fficd-001"), (P, "0x230144e3", "ffic_prefix", "FFIC fficd-001")],
 "btc-etf-2024": [(P, "0xb36886bb", "ffic_prefix", "FFIC fficd-005")],
 "ftx-sbf": [(P, "0xf4078ddd", "ffic_prefix", "FFIC fficd-007"), (P, "0x2b8608c1", "ffic_prefix", "FFIC fficd-007"), (P, "0x02c8326d", "ffic_prefix", "FFIC fficd-007")],
 "romania-2024": [(P, "0x9872fe47", "ffic_prefix", "FFIC fficd-008")],
 "google-yis-2025": [(E, "1-searched-person-on-google-this-year", "claimed_wallets", "d4vd #1 market; case wallet"),
                     (E, "top-5-most-searched-people-on-google-2025", "claimed_wallets", "d4vd Top-5 market; case wallet")],
 "gemini3-release-2025": [(E, "gemini-3pt0-released-by", "gamma_search+claimed_wallets", "claim: Gemini 3.0 release date; AlphaRaccoon proxy traded"),
                          (E, "what-day-will-gemini-3pt0-be-released", "gamma_search+claimed_wallets", "same")],
 "spotify-wrapped-2025": [(E, "3-most-streamed-spotify-artist-2025", "claimed_wallets", "claim CL for 0xc51e: #3 artist market; case wallet traded")],
 "openai-browser-2025-10": [(E, "openai-browser-by-october-31", "gamma_search", "claim: browser launch by end of October 2025")],
 "openai-gpt52-2025-12": [(E, "will-openai-release-a-new-frontier-model-by-december-13", "gamma_search", "claim: new model by Dec 13 2025")],
 "zachxbt-axiom-2026-02": [(E, "which-crypto-company-will-zachxbt-expose-for-insider-trading", "claimed_wallets", "2 of 2 case wallets; claims name this market")],
 "nobel-peace-2025": [(E, "nobel-peace-prize-winner-2025", "claimed_wallets", "8 of 8 case wallets")],
 "taylor-swift-engagement": [(E, "taylor-swift-and-travis-kelce-engaged-in-2025", "gamma_search", "claim: engagement announcement Aug 26 2025")],
 "super-bowl-halftime-2025": [(E, "who-will-perform-during-super-bowl-lix-half-time-show", "gamma_search", "claim: Super Bowl LIX halftime performer markets")],
 "trump-pardon-cz-2025": [(E, "who-will-trump-pardon-in-2025", "claimed_wallets", "case wallet bought Yes from Sept 28 in this event")],
 "trump-zelensky-meeting-2025-12": [(S, "will-trump-meet-with-zelenskyy-by-december-31-194-484", "hf_slug", "claim names 'Trump meets Zelenskyy by Dec 31'")],
 "biden-pardons": [(E, "who-will-biden-pardon", "gamma_search+claimed_wallets", "2 of 2 case wallets"),
                   (E, "will-joe-pardon-hunter-biden", "claimed_wallets", "2 of 2 case wallets")],
 "walz-vp-2024": [(E, "democratic-vp-nominee", "gamma_search", "claim: Walz went from under 1% to 100%")],
 "vance-vp-2024": [(E, "republican-vp-nominee", "gamma_search", "claim: Trump VP pick July 2024")],
 "pope-conclave-2025": [(E, "who-will-be-the-next-pope", "gamma_search", "claim: odds on the eventual winner before the announcement")],
 "uma-ukraine-minerals-2025": [(E, "ukraine-agrees-to-give-trump-rare-earth-metals-before-april", "gamma_search", "claim: $7M mineral-deal market")],
 "arbitrum-airdrop-2023": [(E, "arbitrum-airdrop-by-march-31st", "gamma_search", "claim: Yes spiked before the ARB airdrop announcement")],
 "mstr-btc-sale": [(E, "microstrategy-sell-any-bitcoin-in-2025", "gamma_search+claimed_wallets", "case title: BTC sale; case wallet traded")],
 "draftkings-pm-launch": [(E, "will-draftkings-launch-a-prediction-market-in-2025", "gamma_search+claimed_wallets", "claim + case wallet")],
 "survivor-50-2026": [(E, "survivor-50-winner", "gamma_search", "claim: Survivor 50 winner (Polymarket side)")],
 "ballon-dor-2026": [(E, "ballon-dor-2026-kylian-mbappe-or-lamine-yamal-to-finish-higher", "claimed_wallets", "11 of 11 case wallets"),
                     (E, "ballon-dor-winner-2026", "claimed_wallets", "5 of 11 case wallets")],
 "world-cup-2026-06": [(E, s, "claimed_wallets", "case wallets traded (Data API v2)") for s in
                       ("fifwc-irn-nzl-2026-06-15", "fifwc-cze-rsa-2026-06-18", "fifwc-uzb-col-2026-06-17",
                        "fifwc-ksa-ury-2026-06-15", "fifwc-ksa-ury-2026-06-15-more-markets", "fifwc-usa-par-2026-06-12", "fifwc-kr-cze-2026-06-11")],
 "kpmg-earnings-2025-26": "WALLET_EARNINGS",  # every *quarterly-earnings* event traded by any of the 22 case wallets (A6.5)
}
NO_MARKET = {
 "acdc-orcas": "aggregate (rule-defined wallets)", "inca-digital-39": "aggregate", "nyt-80-accounts": "aggregate; accounts not public",
 "polymarket-referrals-aggregate": "aggregate", "polysights-flags-aggregate": "aggregate", "solidus-multichain": "aggregate",
 "mitts-ofir-composite": "aggregate (rule-defined pairs)", "kalshi-q1-2026-aggregate": "Kalshi aggregate",
 "kalshi-candidate-own-race": "Kalshi; no public account or trade IDs", "kalshi-mrbeast-2025": "Kalshi; no public account or trade IDs",
 "kalshi-sotu-attendance": "Kalshi; no public account or trade IDs", "kalshi-teleprompter-2026": "Kalshi; no public account or trade IDs",
 "coinbase-earnings-mentions": "Kalshi; no public account or trade IDs",
 "campaign-staff-bets": "claims name no market or account",
 "iran-military-trader-967k": "one trader across many markets; no account or market named",
 "israel-iaf-officer-2": "claims name no market or account",
 "israel-election-2026-10": "claims name no specific market",
 "netanyahu-odds-support-2026": "market for 'Netanyahu staying PM' ambiguous (several candidate markets); handle unresolved",
 "midterms-2026": "claims name no specific market",
 "tariff-decisions-2026": "claims name no specific market",
 "xfm-self-trading": "self-trading pattern across many unrelated markets; no market identified",
 "tweet-count-self-2026-03": "DECISION NEEDED: the market names the person the claim alleges controls the accounts (PROTOCOL 9)",
}


def get(url, cache):
    p = os.path.join(CACHE, cache)
    if os.path.exists(p):
        return json.load(open(p))
    for i in range(6):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "curl/8.5.0"}), timeout=60))
            json.dump(d, open(p, "w")); time.sleep(0.3)
            return d
        except Exception:
            time.sleep(2 ** i)
    raise RuntimeError(url)


def event_by_slug(slug):
    d = get("https://gamma-api.polymarket.com/events?" + urllib.parse.urlencode({"slug": slug}), f"event_{slug}.json")
    return d[0] if d else None


def market_by_condition(cid):
    d = get("https://gamma-api.polymarket.com/markets?" + urllib.parse.urlencode({"condition_ids": cid}), f"market_{cid}.json")
    if not d:  # Gamma hides closed markets unless asked
        d = get("https://gamma-api.polymarket.com/markets?" + urllib.parse.urlencode({"condition_ids": cid, "closed": "true"}), f"market_{cid}_closed.json")
    return d[0] if d else None


def market_by_slug(slug):
    d = get("https://gamma-api.polymarket.com/markets?" + urllib.parse.urlencode({"slug": slug}), f"mslug_{slug}.json")
    if not d:
        d = get("https://gamma-api.polymarket.com/markets?" + urllib.parse.urlencode({"slug": slug, "closed": "true"}), f"mslug_{slug}_closed.json")
    return d[0] if d else None


def main():
    con = duckdb.connect()
    cat = {r[0]: r for r in con.sql(f"""select condition_id, any_value(market_slug), max(winning_outcome_label), any_value(resolution_status),
           min(resolved_at)::varchar, sum(usdc_volume) from '{CAT}' group by 1""").fetchall()}
    cases = {r["case_id"]: r for r in csv.DictReader(open(os.path.join(D, "data", "cases.csv")))}
    claims = list(csv.DictReader(open(os.path.join(D, "data", "claims.csv"))))
    missing = set(cases) - set(CASE_MARKETS) - set(NO_MARKET)
    assert not missing, f"cases with no market decision: {missing}"
    # ForesightFlow t_news
    ff = {}
    for r in csv.DictReader(open(os.path.join(FF, "polymarket-tnews-tevent-recovery", "data", "tnews_tevent_recovery_v1.csv"))):
        ff[r["market_id"].lower()] = r
    # earning events for kpmg: from case wallets' Data API activity
    import gzip
    wl = [r["address"] for r in csv.DictReader(open(os.path.join(D, "data", "wallet_labels.csv"))) if r["case_id"] == "kpmg-earnings-2025-26"]
    earn = set()
    for a in wl:
        for x in json.load(gzip.open(os.path.join(D, "logs", "gamma_raw", f"activity_{a}.json.gz"), "rt")):
            if x["type"] == "TRADE" and "quarterly-earnings" in (x.get("event_slug") or ""):
                earn.add(x["event_slug"])
    CASE_MARKETS["kpmg-earnings-2025-26"] = [(E, s, "claimed_wallets", "quarterly-earnings event traded by a case wallet") for s in sorted(earn)]

    rows, notfound = [], []
    for case, specs in CASE_MARKETS.items():
        cl = [c for c in claims if c["case_id"] == case]
        ev = [parse_date(c["event_date"]) for c in cl]; cd = [parse_date(c["claim_date"]) for c in cl]
        cand = [d for d in ev + cd if d[0] and d[1] == "day"]   # PROTOCOL A7
        if not any(d[1] == "day" for d in ev):
            cand += [d for d in ev if d[0]]
        cand.sort()
        tn_day, tn_prec = (cand[0] if cand else ("", ""))
        for kind, val, via, why in specs:
            events, sel_cid = [], ""
            if kind == E:
                ev = event_by_slug(val)
                if not ev:
                    notfound.append((case, kind, val, "gamma event slug not found")); continue
                events.append(ev)
            else:
                if kind == P:
                    hits = [c for c in cat if c.lower().startswith(val.lower())]
                    if len(hits) != 1:
                        notfound.append((case, kind, val, f"{len(hits)} catalog condition_ids match prefix")); continue
                    m = market_by_condition(hits[0])
                else:
                    m = market_by_slug(val)
                if not m:
                    notfound.append((case, kind, val, "gamma market not found")); continue
                evs = m.get("events") or []
                ev = event_by_slug(evs[0]["slug"]) if evs else {"id": "", "slug": "", "markets": [m]}
                events.append(ev)
                sel_cid = (m.get("conditionId") or "").lower()
            for ev in events:
                mk = ev.get("markets") or []
                ends = sorted({(m.get("endDate") or "") for m in mk})
                ranked = len(ends) > 1
                for m in mk:
                    cid = (m.get("conditionId") or "").lower()
                    if not cid:
                        continue
                    hc = cat.get(cid) or cat.get(m.get("conditionId")) or (None,) * 6
                    outs, prices = json.loads(m.get("outcomes") or "[]"), json.loads(m.get("outcomePrices") or "[]")
                    win = hc[2] or (outs[prices.index("1")] if "1" in prices else "")
                    f = ff.get(cid, {})
                    tier = f.get("tier", "")
                    if tier in ("tier1_uma", "tier3_llm"):
                        t_news, method, prec = f["recovered_timestamp"], "ff_" + tier.split("_")[0], "timestamp"
                    else:
                        t_news, method, prec = (tn_day + "T00:00:00Z" if tn_day else ""), "claim_min", tn_prec
                    tok = json.loads(m.get("clobTokenIds") or "[]")
                    rows.append(dict(
                        case_id=case, condition_id=cid, question=m.get("question", ""), slug=m.get("slug", ""),
                        event_id=ev.get("id", ""), event_slug=ev.get("slug", ""),
                        series_id=";".join(str(s.get("id")) for s in (ev.get("series") or [])),
                        selected_as=f"{kind}:{val}", found_via=via, reason=why,
                        selection_level="event" if kind == E else ("market" if cid == sel_cid else "ladder"),
                        created_utc=m.get("createdAt", ""), deadline_utc=m.get("endDate", ""),
                        resolved_utc=m.get("closedTime") or (hc[4] or ""), outcome=win, outcomes=";".join(outs),
                        token_ids=";".join(tok), neg_risk=m.get("negRisk", ""),
                        volume_gamma=m.get("volume", ""), volume_hf_usdc=round(hc[5], 2) if hc[5] else "",
                        in_hf=hc[0] is not None,
                        ladder_rank=(ends.index(m.get("endDate") or "") + 1) if ranked else "",
                        t_news_utc=t_news, t_news_method=method, t_news_precision=prec,
                        ff_tier=tier, ff_tier2_tnews=f.get("recovered_timestamp", "") if tier == "tier2_gdelt_proxy" else ""))
    # de-duplicate (case, condition_id)
    seen, out = set(), []
    for r in rows:
        k = (r["case_id"], r["condition_id"])
        if k not in seen:
            seen.add(k); out.append(r)
    with open(os.path.join(D, "data", "markets.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    with open(os.path.join(D, "logs", "markets_not_found.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["case_id", "kind", "value", "reason"])
        for c, why in sorted(NO_MARKET.items()):
            w.writerow([c, "no_market_found", "", why])
        w.writerows(notfound)
    print(len(out), "market rows;", len({r["case_id"] for r in out}), "cases;", len({r["condition_id"] for r in out}), "distinct markets;",
          len(notfound), "lookups failed")


if __name__ == "__main__":
    main()
