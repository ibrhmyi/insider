"""Task 2: market selection -> data/markets.csv, data/control_match_table.md

Market choices are fixed here (with reasons); every metadata field is pulled live from
Gamma + Data API v2 /resolutions so the CSV is reproducible.
Control matching scores come from src/00_match_controls.py
(data/raw/control_match_candidates.json).
"""
import json

import pandas as pd

from common import DATA, DATA_API, GAMMA, RAW, dump, get_json, iso, parse_ts

# ---------------------------------------------------------------------------
# Selected markets. label + justification follow rules/labeling_rule.md.
# ---------------------------------------------------------------------------
MARKETS = [
    dict(key="iran", gamma_id="554012", label="insider-possible", role="development",
         label_justification="Resolves on a US military strike decision; known in advance to the US chain of command.",
         news=[("2025-06-21T23:46:00Z",
                "Trump Truth Social post announcing strikes on Fordow/Natanz/Esfahan (reported 7:46-7:50pm EDT)",
                "https://www.pbs.org/newshour/world/trump-says-u-s-has-struck-3-iranian-nuclear-sites-joining-israeli-military-campaign | time: https://www.thejournal.ie/donald-trump-announcement-bomb-iran-6740123-Jun2025/ ; https://wbgsv0a.gigazine.net/gsc_news/en/20250624-donald-trump-truth-social-down")],
         matched_control="551260"),
    dict(key="maduro", gamma_id="916440", label="insider-possible", role="blind-validation",
         label_justification="Resolves on Maduro leaving power; the Jan-3-2026 US operation was known in advance to US planners.",
         news=[("2026-01-03T06:00:00Z",
                "First public reports of explosions over Caracas (~2:00am VET); approximate",
                "https://chequeado.com/el-explicador/que-sabemos-de-los-bombardeos-en-venezuela-y-la-captura-de-nicolas-maduro-anunciada-por-donald-trump/"),
               ("2026-01-03T09:21:00Z",
                "Trump Truth Social post: Maduro captured and flown out (4:21am ET)",
                "https://talkingpointsmemo.com/news/trump-says-us-has-captured-venezuelas-president-maduro")],
         matched_control="1058617"),
    dict(key="nobel", gamma_id="560868", label="insider-possible", role="comparison",
         label_justification="Resolves on the Norwegian Nobel Committee's private decision; known to the committee before announcement.",
         news=[("2025-10-10T09:00:00Z",
                "Official announcement in Oslo, 11:00 CEST (minute single-sourced)",
                "https://www.nobelprize.org/prizes/peace/2025/prize-announcement/ | time: https://www.pw.live/upsc/exams/nobel-prize-in-peace-2025-winners")],
         matched_control="632731"),
    dict(key="ctrl_btc110k_jun17", gamma_id="551260", label="insider-impossible", role="control",
         label_justification="Resolves mechanically on Binance BTC/USDT price at a fixed reference time; nobody knows it early.",
         news=[], matched_control=None, matched_to="iran"),
    dict(key="ctrl_btc94k_jan5", gamma_id="1058617", label="insider-impossible", role="control",
         label_justification="Resolves mechanically on Binance BTC/USDT price at a fixed reference time; nobody knows it early.",
         news=[], matched_control=None, matched_to="maduro"),
    dict(key="ctrl_btcupdown_oct14", gamma_id="632731", label="insider-impossible", role="control",
         label_justification="Resolves mechanically on Binance BTC/USDT 1h candle (close vs open) at a fixed reference time; nobody knows it early.",
         news=[], matched_control=None, matched_to="nobel"),
    # REJECTED (kept for the record, not used): 620852 "Solana above $280 on Oct 10" - best score on
    # volume/median price, but 0% of taker notional at contested prices (all trading = No at 0.999
    # carry), feed starts 133h after open, maker+taker notional = 1.98x Gamma volume. Same pattern in
    # every Oct-2025 "price above" candidate screened (see data/raw/control_screen_*.json).
]


def main():
    rows, news_rows = [], []
    for spec in MARKETS:
        m = get_json(f"{GAMMA}/markets/{spec['gamma_id']}")
        dump(m, RAW / "gamma" / f"{spec['gamma_id']}.json")
        cond = m["conditionId"]
        res = get_json(f"{DATA_API}/resolutions", params=dict(condition=cond))
        dump(res, RAW / "resolutions" / f"{spec['gamma_id']}.json")
        r = (res.get("data") or [{}])[0]
        toks = json.loads(m["clobTokenIds"])
        outs = json.loads(m["outcomes"])
        prices = json.loads(m["outcomePrices"])
        winner = outs[prices.index("1")] if "1" in prices else "UNRESOLVED"
        res_ts = parse_ts(r.get("resolved_at")) or parse_ts(r.get("last_update_timestamp")) or parse_ts(m.get("closedTime"))
        # Control markets: the public "news" is the price reference time = market endDate.
        news = spec["news"]
        if spec["label"] == "insider-impossible":
            news = [(iso(parse_ts(m["endDate"])), "Price reference time (outcome becomes public)",
                     "market rules: " + (m.get("resolutionSource") or "see description"))]
            if "Up or Down" in m["question"]:  # 1h candle: outcome becomes public progressively from candle open
                news.insert(0, (iso(parse_ts(m["endDate"]) - 3600), "1h candle opens (outcome starts becoming public)",
                                "market rules: " + (m.get("resolutionSource") or "see description")))
        for t, what, src in news:
            news_rows.append(dict(market_key=spec["key"], condition_id=cond, news_utc=t,
                                  news_epoch=parse_ts(t), description=what, source_url=src))
        rows.append(dict(
            market_key=spec["key"], role=spec["role"], label=spec["label"],
            label_justification=spec["label_justification"],
            market_name=m["question"], gamma_market_id=m["id"], slug=m["slug"],
            condition_id=cond, token_id_yes=toks[0], token_id_no=toks[1],
            outcome_0=outs[0], outcome_1=outs[1],
            volume_usd=round(float(m["volumeNum"]), 2),
            open_utc=iso(parse_ts(m.get("startDate"))), end_date_utc=iso(parse_ts(m["endDate"])),
            closed_utc=iso(parse_ts(m["closedTime"])),
            resolution=winner, resolution_utc=iso(res_ts) if res_ts else "",
            resolution_epoch=res_ts, resolution_source_api="data-api v2 /resolutions + gamma closedTime",
            uma_status=r.get("status"), was_disputed=r.get("was_disputed"),
            neg_risk=m.get("negRisk"),
            first_news_utc=min(n[0] for n in news) if news else "",
            news_source_url=" || ".join(n[2] for n in news),
            matched_control_gamma_id=spec.get("matched_control") or "",
            matched_to=spec.get("matched_to", ""),
            metadata_source="Polymarket Gamma API /markets/{id} (2026-11-09)",
        ))
    df = pd.DataFrame(rows)
    df.to_csv(DATA / "markets.csv", index=False)
    pd.DataFrame(news_rows).to_csv(DATA / "news_events.csv", index=False)
    print(df[["market_key", "label", "volume_usd", "open_utc", "resolution", "resolution_utc"]].to_string())

    # ---- control match table ----
    import math
    screens = {}
    for f in RAW.glob("control_screen_*.json"):
        screens.update(json.load(open(f)))

    def pstats(gid):
        m = get_json(f"{GAMMA}/markets/{gid}")
        js = get_json(f"{DATA_API}/prices-history", params=dict(token_id=json.loads(m["clobTokenIds"])[0], interval="max", bucket_seconds=10800))
        end = parse_ts(m["closedTime"])
        ps = sorted(p["price"] for p in (js.get("data") or []) if p["timestamp"] < end - 3 * 3600)
        return dict(q=m["question"], vol=float(m["volumeNum"]), pmed=ps[len(ps) // 2], pmin=ps[0], pmax=ps[-1], end=end)
    by = {r["market_key"]: r for r in rows}
    lines = ["# Control match table", "",
             "Score = |ln(vol_control/vol_target)| + 5*|median_pre_price_control - median_pre_price_target| + 0.1*days_between_closes.",
             "Pre-resolution price = YES-token price-history points (12h grain, the only grain still available for these dates) excluding the final 3h before close.",
             "Candidate pool: Gamma crypto 'X above $Y' markets closing within +-7 days of the target, volume > $200k, top-40 by volume. Lowest score chosen.", "",
             "Added screen (after the first Nobel control failed): control must have maker+taker notional / Gamma volume ~1 (feed complete) and a meaningful share of taker notional at contested prices 0.02-0.98.", "",
             "| Insider-possible market | Vol | Pre-res YES median [min,max] | Matched control | Vol | Pre-res YES median [min,max] | Days apart | Score | Feed ratio | Contested share | Match quality / caveat |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    notes = {"iran": "WEAK: control 3.8x smaller volume, closes 4.4 days earlier; no crypto-threshold market in Jun 15-29 2025 matched the 10-17% price band with similar volume.",
             "nobel": "SUBSTITUTE: first choice (Solana >$280 Oct 10, score 0.09) rejected - 0% contested trading, incomplete-looking feed. All Oct-2025 'price above' markets failed the same screen. This hourly Up/Down market passes the screen but trades near 0.5, not Machado's low band, and is 0.41x the volume.",
             "maduro": "WEAK on volume: control 9.4x smaller (largest crypto-threshold market that week was ~$1.2M). Price band and calendar close."}
    for tk in ["iran", "nobel", "maduro"]:
        t = by[tk]; tgt = pstats(t["gamma_market_id"]); cid = t["matched_control_gamma_id"]; c = pstats(cid)
        days = abs(c["end"] - tgt["end"]) / 86400
        score = abs(math.log(c["vol"] / tgt["vol"])) + 5 * abs(c["pmed"] - tgt["pmed"]) + 0.1 * days
        sc = screens.get(cid, {})
        lines.append(f"| {t['market_name']} | ${tgt['vol']/1e6:.2f}M | {tgt['pmed']:.3f} [{tgt['pmin']:.3f},{tgt['pmax']:.3f}] | {c['q']} | ${c['vol']/1e6:.2f}M | {c['pmed']:.3f} [{c['pmin']:.3f},{c['pmax']:.3f}] | {days:.1f} | {score:.2f} | {sc.get('all_sides_ratio','-')} | {sc.get('contested_share','-')} | {notes[tk]} |")
    lines += ["", "Runner-up candidates are stored in `data/raw/control_match_candidates.json`."]
    (DATA / "control_match_table.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
