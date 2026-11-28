"""R6: builds release_safe/ from release/: every file except the data_api_v2 fill parts (hard links, no copies), plus
scripts/rebuild_data_api_fills.py, a note at the top of docs/README.md, its own MANIFEST (withheld_sources) and Kaggle metadata.
Usage: python3 build/v1/package_safe.py"""
import glob, os, shutil, subprocess, sys

D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC, DST = os.path.join(D, "release"), os.path.join(D, "release_safe")
shutil.rmtree(DST, ignore_errors=True)
for p in glob.glob(os.path.join(SRC, "**", "*"), recursive=True, include_hidden=True):
    rel = os.path.relpath(p, SRC); q = os.path.join(DST, rel)
    if os.path.isdir(p) or "__pycache__" in p or p.endswith(".pyc") or rel in ("MANIFEST.json", "dataset-metadata.json", "docs/README.md"):
        continue
    if os.path.basename(p).startswith("fills_part") and p.endswith("_data_api_v2.parquet"):
        continue
    os.makedirs(os.path.dirname(q), exist_ok=True); os.link(p, q)
os.makedirs(os.path.join(DST, "scripts"), exist_ok=True)
shutil.copy(os.path.join(D, "build", "v1", "rebuild_data_api_fills.py"), os.path.join(DST, "scripts", "rebuild_data_api_fills.py"))
NOTE = """> **release_safe (v1.0.1).** This package omits the fill files with `source = data_api_v2` (Polymarket Data API rows,
> whose redistribution terms were not verified). All other tables are identical to the full package; tables derived from
> those rows (`positions`, `episodes`, `controls`, `market_minutes`) still contain their aggregates. Rebuild the omitted
> files with `python3 scripts/rebuild_data_api_fills.py` (public API; results will differ slightly from the full package
> because the API keeps adding rows).

"""
os.makedirs(os.path.join(DST, "docs"), exist_ok=True)
open(os.path.join(DST, "docs", "README.md"), "w").write(NOTE + open(os.path.join(SRC, "docs", "README.md")).read())
# wallets whose trade confirmation rests only on the withheld Data API fills (listed so the quality gate can check them)
import duckdb, json
api = glob.glob(os.path.join(SRC, "data", "fills_part*_data_api_v2.parquet")); hf = glob.glob(os.path.join(SRC, "data", "fills_part*_hf_polymarket_v1.parquet"))
only = sorted({r[0] for r in duckdb.sql(f"""SELECT DISTINCT w.wallet FROM '{SRC}/data/wallets.parquet' w
          WHERE w.trade_confirmed AND w.wallet IN (SELECT wallet FROM read_parquet({api!r})) AND w.wallet NOT IN (SELECT wallet FROM read_parquet({hf!r}))""").fetchall()})
json.dump(only, open(os.path.join(D, "out", "v1", "safe_api_only_wallets.json"), "w"))
subprocess.run([sys.executable, os.path.join(D, "build", "v1", "kaggle_meta.py"), "release_safe"], check=True)
subprocess.run([sys.executable, os.path.join(D, "build", "v1", "codebook.py"), "release_safe"], check=True)
print("release_safe built")
