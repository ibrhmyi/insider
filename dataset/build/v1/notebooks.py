"""Writes release/notebooks/01_quickstart.ipynb, 02_case_study.ipynb, 03_benchmarks.ipynb (executed afterwards with nbconvert)."""
import glob, os
import nbformat as nbf

D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
NB = os.path.join(D, "release", "notebooks")
for f in glob.glob(os.path.join(NB, "*.ipynb")):
    os.remove(f)
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
q = nbf.v4.new_notebook(); q.cells = [
 md("# PMITC v1.2 quick start\nLoad, join, plot one case. Labels are allegations by named sources (\"flagged by <source>\"), not findings; tables hold no personal names."),
 code("import pandas as pd, matplotlib.pyplot as plt\nDATA = '../data'\ncases = pd.read_parquet(f'{DATA}/cases.parquet')\nwallets = pd.read_parquet(f'{DATA}/wallets.parquet')\nmarkets = pd.read_parquet(f'{DATA}/markets.parquet')\ncases[['case_id','case_grade','investigation_outcome','n_documented_by_case','benchmark_split']].sort_values('n_documented_by_case', ascending=False).head(10)"),
 code("# the three nested label sets (PROTOCOL A20)\nwallets[['label_strict','label_standard','label_broad']].sum()"),
 code("# join: documented wallets -> their pre-news positions in their case markets (precise news time)\npos = pd.read_parquet(f'{DATA}/positions.parquet', filters=[('market_set','==','case'), ('t_news_version','==','precise'), ('label_strict','==',True)])\npos.merge(markets[['case_id','condition_id','question']], on=['case_id','condition_id'])[['case_id','question','wallet','buy_usdc_pre','vwap_price_usdc_pre','account_age_days_at_first_buy']].head(10)"),
 code("CASE = 'zachxbt-axiom-2026-02'\nmm = pd.read_parquet(f'{DATA}/market_minutes.parquet', filters=[('case_id','==',CASE), ('market_set','==','case'), ('t_news_version','==','precise')])\ncid = mm.groupby('condition_id').usdc.sum().idxmax()\ng = mm[mm.condition_id == cid]\nfig, ax = plt.subplots(figsize=(9,3)); ax.plot(g.minutes_from_cut / 60, g.last_price_usdc); ax.axvline(0, color='r', ls='--', label='t_news_precise')\nax.set_xlabel('hours from the news'); ax.set_ylabel('Yes price'); ax.legend(); ax.set_title(markets.set_index(['case_id','condition_id']).loc[(CASE, cid), 'question'])"),
]
c = nbf.v4.new_notebook(); c.cells = [
 md("# Case study: the Maduro market (January 2026)\nThe Yes price path around the news, the buys of the wallet that official sources (CFTC, DOJ) describe, and its matched controls. The wallet is shown by address only; no identity work."),
 code("import pandas as pd, matplotlib.pyplot as plt, duckdb\nDATA = '../data'; CASE = 'maduro-2026-01'\nmarkets = pd.read_parquet(f'{DATA}/markets.parquet'); wallets = pd.read_parquet(f'{DATA}/wallets.parquet')\nlinks = pd.read_parquet(f'{DATA}/claim_wallet_links.parquet')\nw = wallets[(wallets.case_id == CASE) & wallets.label_strict]\nprint(w[['wallet','label_tier','wallet_grade','strict_basis']]); print(links[links.case_id == CASE])"),
 code("W = w.wallet.iloc[0]\nep = pd.read_parquet(f'{DATA}/episodes.parquet', filters=[('case_id','==',CASE), ('t_news_version','==','precise')])\ne = ep[(ep.wallet == W) & (ep.role == 'suspected')].sort_values('pre_buy_usdc', ascending=False).iloc[0]\ncid = e.condition_id; m = markets.set_index(['case_id','condition_id']).loc[(CASE, cid)]\nprint(m.question, '| t_news', m.t_news_utc, '| precise', m.t_news_precise_utc, m.t_news_precise_precision)\nctl = pd.read_parquet(f'{DATA}/controls.parquet', filters=[('t_news_version','==','precise'), ('episode_id','==',e.episode_id)])\nctl[['wallet','control_type','relaxation','first_buy_price_usdc','size_usdc']].head(12)"),
 code("f = duckdb.sql(f\"SELECT ts_utc, price_usdc, usdc, wallet_side FROM read_parquet('{DATA}/fills_part*_case_*.parquet') WHERE condition_id = '{cid}' AND wallet = '{W}' ORDER BY ts_unix\").df()\nmm = pd.read_parquet(f'{DATA}/market_minutes.parquet', filters=[('case_id','==',CASE), ('condition_id','==',cid), ('t_news_version','==','precise'), ('market_set','==','case')])\nfig, ax = plt.subplots(figsize=(10,4)); ax.plot(mm.minute_utc, mm.last_price_usdc, lw=0.8, label='Yes last price (48 h before to 24 h after the news)')\nb = f[f.wallet_side == 'BUY']; ax.scatter(b.ts_utc, b.price_usdc, s=10 + b.usdc / 200, color='m', label='the wallet\\'s buys')\nax.axvline(pd.Timestamp(m.t_news_precise_utc), color='r', ls='--', label='t_news_precise'); ax.legend(fontsize=8); ax.set_ylabel('price (USDC)')\nprint(len(f), 'legs of the wallet in this market; buys before the precise cut:', (b.ts_utc < pd.Timestamp(m.t_news_precise_utc)).sum())"),
 code("# the matched controls bought the same token, at a similar time, price and size; how did they do?\nep[ep.control_of == e.row_id].groupby('role').agg(n=('wallet','size'), won=('won_post','mean'), median_buy_usdc=('pre_buy_usdc','median'))"),
]
b = nbf.v4.new_notebook(); b.cells = [
 md("# PMITC v1.2 benchmarks\nResults of `benchmarks/pmitc_bench.py` (leave-one-case-out plus the time split, three label sets, seed 192). Headline tasks T1s, T2s, T2-open; trained on label_standard, label_strict evaluation-only, then a quick end-to-end re-run of T2 on the released files."),
 code("import json, sys, pandas as pd\nsys.path.insert(0, '../benchmarks'); import pmitc_bench as B\nres = json.load(open('../benchmarks/baselines.json'))\nrows = []\nfor s in B.SETS:\n    for t in ['T1s','T2s','T2open','T1','T2','T3','T3b']:\n        for m, r in res['precise'][s][t]['summary'].items():\n            rows.append(dict(label_set=s, task=t, model=m, loco_mean=r['loco_mean'], loco_sd=r['loco_sd'], n_folds=r['n_loco_folds'], time_split=r['time_split']))\npd.DataFrame(rows).pivot_table(index=['task','model'], columns='label_set', values='loco_mean')"),
 code("pd.DataFrame(rows)[lambda d: d.task.isin(['T1s','T2s','T2open'])]"),
 code("# known shortcuts and leakage lists\nres['known_shortcuts']"),
 code("# end-to-end re-run on the released files: T2s (age-matched controls), evaluated on label_strict, trained on label_standard; no gradient boosting\nsplits = pd.read_csv('../benchmarks/splits.csv')[['case_id','split']]\nr = B.t2('../data', splits, 'precise', 'label_strict', tune=False, quick=True, design='age_matched')\nr['summary']"),
]
for nb, name in [(q, "01_quickstart.ipynb"), (c, "02_case_study.ipynb"), (b, "03_benchmarks.ipynb")]:
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nbf.write(nb, os.path.join(NB, name))
print("ok")
