"""Writes release/docs/CODEBOOK.md from build/v1/schema.py (one entry per column: type, unit, allowed values, source, leakage note)
and release/MANIFEST.json (rows, bytes, SHA-256 of every released file). Usage: python3 build/v1/codebook.py"""
import glob, hashlib, json, os, sys
import pyarrow.parquet as pq

sys.path.insert(0, os.path.dirname(__file__))
from schema import TABLES  # noqa

D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REL = os.path.join(D, sys.argv[1] if len(sys.argv) > 1 else "release"); os.makedirs(os.path.join(REL, "docs"), exist_ok=True)
LEAK = {"pre": "pre-cut feature", "post": "OUTCOME: uses data at/after the cut or resolution; never a feature", "label": "LABEL / target; never a feature",
        "meta": "identifier or provenance", "static": "known at market creation"}
L = ["# PMITC v1.0 codebook", "", "Generated from `build/v1/schema.py`. Every released column is listed with its type, unit, allowed values, source and a",
     "leakage note. Missing values are NULL (never empty strings). Timestamps are UTC (`timestamp[s, tz=UTC]` in parquet, ISO-8601 `...Z` in CSV).",
     "Addresses are lower-case `0x` + 40 hex. `PK` marks primary-key columns.", "",
     "Leakage notes: `pre` = computed only from data before the row's cut time; `post` = outcome column; `label` = label or target; `static` = known at creation; `meta` = id/provenance.", ""]
for t, spec in TABLES.items():
    L += [f"## {t}", "", spec["desc"], "", "| column | type | unit | allowed values | source | leakage | description |", "|---|---|---|---|---|---|---|"]
    for c in spec["cols"]:
        L.append(f"| `{c['name']}` | {c['dtype']}{' (PK)' if c['pk'] else ''} | {c['unit']} | {c['allowed'].replace(';', ', ')} | {c['source']} | {c['leak']} | {c['desc'].replace('|', '/')} |")
    L.append("")
open(os.path.join(REL, "docs", "CODEBOOK.md"), "w").write("\n".join(L) + "\n")
files = []
for p in sorted(glob.glob(os.path.join(REL, "**", "*"), recursive=True, include_hidden=True)):
    if os.path.isdir(p) or p.endswith("MANIFEST.json") or "/.ipynb_checkpoints/" in p or "__pycache__" in p or p.endswith(".pyc"):
        continue
    rel = os.path.relpath(p, REL)
    rows = pq.ParquetFile(p).metadata.num_rows if p.endswith(".parquet") else (sum(1 for _ in open(p, "rb")) - 1 if p.endswith(".csv") else None)
    files.append(dict(path=rel, rows=rows, bytes=os.path.getsize(p), sha256=hashlib.sha256(open(p, "rb").read()).hexdigest()))
json.dump(dict(name="PMITC", version="1.2.0", package=os.path.basename(REL), withheld_sources=["data_api_v2"] if os.path.basename(REL) == "release_safe" else [],
               wallets_confirmed_only_by_withheld_sources=json.load(open(os.path.join(D, "out", "v1", "safe_api_only_wallets.json"))) if os.path.basename(REL) == "release_safe" else [], hf_source="TimeSeventeen/Polymarket-v1 @ 6d1bcd5279cbbd8e833feaeba9a56a0aee139144",
               generated_by="build/v1/codebook.py", files=files), open(os.path.join(REL, "MANIFEST.json"), "w"), indent=1)
print(len(files), "files in manifest")
