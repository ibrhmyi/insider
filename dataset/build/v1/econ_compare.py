"""Run-11 report, A34/A34.1: per market set and news-time version, pre-news positions and buy USDC under raw vs econ,
share of econ-only positions; all wallets and non-market-makers (A34.1 rule). Raw BUYs are never re-read, so every raw position exists in econ
and raw buy USDC = buy_usdc_pre - econ_inferred_buy_usdc_pre."""
import duckdb, json, sys
import os
D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
c = duckdb.connect(); c.sql("SET memory_limit='4GB'")
q = c.sql(f"""SELECT p.market_set, p.t_news_version, coalesce(m.is_market_maker, false) mm,
                     count(*) FILTER (WHERE raw_view_prenews_buy) raw_positions, count(*) econ_positions,
                     count(*) FILTER (WHERE NOT raw_view_prenews_buy) econ_only,
                     count(*) FILTER (WHERE is_directional_position) directional_positions,
                     count(*) FILTER (WHERE is_directional_position AND NOT raw_view_prenews_buy) directional_econ_only,
                     sum(buy_usdc_pre - econ_inferred_buy_usdc_pre) raw_buy_usdc, sum(buy_usdc_pre) econ_buy_usdc
              FROM '{D}/out/v1/positions.parquet' p LEFT JOIN '{D}/out/v1/market_makers.parquet' m USING (wallet)
              GROUP BY ALL ORDER BY 1, 2, 3""").df()
out = {}
for (ms, v), g in q.groupby(["market_set", "t_news_version"]):
    def row(d):
        s = d.sum(numeric_only=True)
        return dict(raw_positions=int(s.raw_positions), econ_positions=int(s.econ_positions), econ_only_share=round(float(s.econ_only / s.econ_positions), 4),
                    growth=round(float(s.econ_positions / s.raw_positions - 1), 4), raw_buy_usdc=round(float(s.raw_buy_usdc)), econ_buy_usdc=round(float(s.econ_buy_usdc)),
                    buy_usdc_growth=round(float(s.econ_buy_usdc / s.raw_buy_usdc - 1), 4),
                    directional_positions=int(s.directional_positions), directional_econ_only_share=round(float(s.directional_econ_only / s.directional_positions), 4))
    out[f"{ms}/{v}"] = dict(all=row(g), non_market_maker=row(g[~g.mm]), market_maker=row(g[g.mm]))
print(json.dumps(out, indent=1))
json.dump(out, open(f"{D}/logs/econ_positions_compare.json", "w"), indent=1)
# labelled wallets: pre-news position gained / lost (precise, case markets, own case)
w = c.sql(f"SELECT address wallet, case_id, label_strict, label_standard, label_broad FROM read_csv('{D}/data/wallet_labels.csv', all_varchar=true) WHERE lower(label_broad) = 'true'").df()
c.register("w", w)
r = c.sql(f"""SELECT w.wallet, w.case_id, w.label_strict, w.label_standard, bool_or(p.raw_view_prenews_buy) raw_pre, coalesce(bool_or(p.is_directional_position), false) econ_pre,
                     sum(p.econ_inferred_buy_usdc_pre) inferred_usdc
              FROM w LEFT JOIN '{D}/out/v1/positions.parquet' p ON p.wallet = w.wallet AND p.case_id = w.case_id AND p.market_set = 'case' AND p.t_news_version = 'precise'
              GROUP BY ALL""").df()
r["raw_pre"] = r.raw_pre.fillna(False).astype(bool)
print("(econ_pre = a directional pre-news position, A34.2; raw_pre = a raw BUY before the cut)")
print("labelled gain:", r[~r.raw_pre & r.econ_pre][["wallet", "case_id", "label_strict", "label_standard", "inferred_usdc"]].to_string())
print("labelled lose:", r[r.raw_pre & ~r.econ_pre][["wallet", "case_id", "label_strict", "label_standard"]].to_string())
r.to_csv(os.path.join(D, "logs", "econ_labelled_prenews.csv"), index=False)
print("labelled with no pre-news position in either view:", r[~r.econ_pre][["wallet", "case_id"]].to_string())
