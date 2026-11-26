"""Writes release/dataset-metadata.json (Kaggle format; not uploaded). Column descriptions are copied from build/v1/schema.py,
the source of release/docs/CODEBOOK.md. Usage: python3 build/v1/kaggle_meta.py"""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from schema import TABLES  # noqa

D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REL = os.path.join(D, "release")
KT = {"string": "string", "int64": "integer", "float64": "numeric", "bool": "boolean", "timestamp": "datetime", "date": "datetime"}
res = []
for p in sorted(glob.glob(os.path.join(REL, "data", "*"))):
    f = os.path.basename(p); t = "fills" if f.startswith("fills_part") else f.rsplit(".", 1)[0]
    if t not in TABLES:
        continue
    res.append(dict(path=f"data/{f}", description=TABLES[t]["desc"] + (" (part of table 'fills')" if t == "fills" else ""),
                    schema=dict(fields=[dict(name=c["name"], type=KT[c["dtype"]],
                                             description=(c["desc"] + (f" Unit: {c['unit']}." if c["unit"] else "") + (f" Allowed: {c['allowed'].replace(';', ', ')}." if c["allowed"] else "") + f" Leakage: {c['leak']}.")[:255])
                                        for c in TABLES[t]["cols"]])))
for p in ["benchmarks/README.md", "benchmarks/splits.csv", "benchmarks/baselines.json", "benchmarks/pmitc_bench.py", "notebooks/01_explore.ipynb", "notebooks/02_baselines.ipynb",
          "docs/README.md", "docs/DATASHEET.md", "docs/CODEBOOK.md", "docs/PROTOCOL.md", "docs/CHANGELOG.md", "docs/LICENSE.md", "docs/CITATION.cff", "docs/LICENSES_UPSTREAM.md"]:
    res.append(dict(path=p, description={"benchmarks/splits.csv": "Frozen case-grouped, time-ordered split (PROTOCOL A15)"}.get(p, os.path.basename(p))))
meta = dict(title="PMITC: Prediction-Market Informed-Trading Casebook", subtitle="Documented suspected insider trading on Polymarket and Kalshi, with trades, placebos and benchmarks",
            id="<kaggle-username>/pmitc-prediction-market-informed-trading", licenses=[{"name": "CC-BY-4.0"}],
            keywords=["finance", "prediction markets", "crypto", "anomaly detection", "tabular", "fraud detection"],
            description=open(os.path.join(REL, "docs", "README.md")).read(), resources=res, isPrivate=True)
json.dump(meta, open(os.path.join(REL, "dataset-metadata.json"), "w"), indent=1)
print(len(res), "resources")
