"""Writes release/notebooks/01_explore.ipynb and 02_baselines.ipynb (executed afterwards with nbconvert)."""
import os
import nbformat as nbf

D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
NB = os.path.join(D, "release", "notebooks")
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
a = nbf.v4.new_notebook(); a.cells = [
 md("# PMITC v1.0: load, join, plot a case\nLabels are allegations by the named sources (\"flagged by <source>\"), not findings. The tables hold no personal names."),
 code("import pandas as pd, numpy as np, matplotlib.pyplot as plt\nDATA = '../data'\ncases = pd.read_parquet(f'{DATA}/cases.parquet')\nclaims = pd.read_parquet(f'{DATA}/claims.parquet')\nwallets = pd.read_parquet(f'{DATA}/wallets.parquet')\nmarkets = pd.read_parquet(f'{DATA}/markets.parquet')\ncases[['case_id','case_grade','investigation_outcome','n_claims','n_documented_by_case','benchmark_split']].sort_values('n_documented_by_case', ascending=False).head(15)"),
 code("# claims per grade and stance\npd.crosstab(claims.evidence_grade, claims.stance)"),
 code("# documented wallets (suspected and trade-confirmed) per case\nwallets[wallets.is_documented].groupby('case_id').wallet.nunique().sort_values(ascending=False)"),
 md("## One case: the Maduro market\nMinute price path of the Yes token around both news times, with the pre-news buys of documented wallets."),
 code("CASE = 'maduro-2026-01'\nm = markets[markets.case_id == CASE]\nmm = pd.read_parquet(f'{DATA}/market_minutes.parquet', filters=[('case_id','==',CASE), ('market_set','==','case')])\ncid = mm[mm.t_news_version=='precise'].groupby('condition_id').usdc.sum().idxmax()\nprint(m.set_index('condition_id').loc[cid, ['question','t_news_utc','t_news_precise_utc','t_news_precise_precision']])"),
 code("pos = pd.read_parquet(f'{DATA}/positions.parquet', filters=[('case_id','==',CASE), ('condition_id','==',cid)])\nprint(pos.groupby('t_news_version').agg(buyers=('wallet','nunique'), documented=('is_documented','sum'), controls=('is_control','sum')))\nfig, ax = plt.subplots(figsize=(10,4))\nfor v, g in mm[mm.condition_id == cid].groupby('t_news_version'):\n    ax.plot(g.minute_utc, g.last_price, label=f'last price ({v} window)', alpha=.7)\nrow = m.set_index('condition_id').loc[cid]\nax.axvline(row.t_news_utc, color='k', ls='--', label='t_news (day)'); ax.axvline(row.t_news_precise_utc, color='r', ls='--', label='t_news_precise')\nd = pos[(pos.t_news_version=='precise') & pos.is_documented]\nax.scatter(pd.to_datetime(d.first_buy_ts, unit='s', utc=True), d.first_buy_price, color='m', zorder=5, label='first buy, documented wallets')\nax.legend(fontsize=8); ax.set_ylabel('price'); ax.set_title(CASE); plt.tight_layout()"),
 md("## Joins\n`positions` (all pre-news buyers) joins `wallets` on (wallet, case_id), `markets` on (case_id, condition_id), and `fills` on (condition_id, asset_id, wallet) with `ts < t_cut_ts`."),
 code("import duckdb\nduckdb.sql(f\"\"\"SELECT market_set, source, count(*) legs FROM read_parquet('{DATA}/fills_part*.parquet') GROUP BY ALL ORDER BY 1, 2\"\"\").df()"),
]
b = nbf.v4.new_notebook(); b.cells = [
 md("# PMITC v1.0 baselines (T1-T3)\nRuns `benchmarks/pmitc_bench.py` end to end on the released files (seed 192). Results are also in `benchmarks/baselines.json`."),
 code("import sys, json\nsys.path.insert(0, '../benchmarks')\nimport pandas as pd, pmitc_bench as B\nsplits = pd.read_csv('../benchmarks/splits.csv')[['case_id','split']]\nsplits.split.value_counts()"),
 code("r1 = B.t1('../data', splits, 'precise')\n{k: v for k, v in r1.items() if k.endswith('_test') or k.startswith('n_')}"),
 code("r2 = B.t2('../data', splits, 'precise')\nr2"),
 code("r3 = B.t3('../data', splits, 'precise')\nr3"),
 md("**Reading the results.** T2's base result: matched same-side controls win about as often as documented episodes, so outcome-based labels alone cannot separate them. T1 is a needle-in-a-haystack ranking problem; compare with the random and rule baselines."),
]
for nb, name in [(a, "01_explore.ipynb"), (b, "02_baselines.ipynb")]:
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nbf.write(nb, os.path.join(NB, name))
print("ok")
