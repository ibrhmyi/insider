"""Phase 8: dereferenced upload copies of release/ in upload/ (not uploaded anywhere):
  upload/hf/      folders kept, dataset card at the root (README.md with the HF YAML header)
  upload/kaggle/  flat file names, folder-prefixed (data__cases.parquet, docs__CODEBOOK.md, ...), dataset-metadata.json with matching resources
  upload/zenodo/  pmitc-v1.2.0.zip + pmitc-v1.2.0.zip.sha256
Checks: every copied file matches release/MANIFEST.json (SHA-256); Kaggle resources cover every file; the zip lists every manifest file
with the same CRC-checked content. Quality-gate tests on upload/hf run separately (PMITC_RELEASE=upload/hf).
Usage: python3 build/v1/upload_copies.py"""
import glob, hashlib, json, os, shutil, zipfile

D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REL, UP = os.path.join(D, "release"), os.path.join(D, "upload")
shutil.rmtree(UP, ignore_errors=True); os.makedirs(UP)
man = json.load(open(os.path.join(REL, "MANIFEST.json")))
sha = {f["path"]: f["sha256"] for f in man["files"]}
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
files = [f["path"] for f in man["files"]]
# HF: same tree
for rel in files + ["MANIFEST.json"]:
    q = os.path.join(UP, "hf", rel); os.makedirs(os.path.dirname(q), exist_ok=True); shutil.copyfile(os.path.join(REL, rel), q)
# Kaggle: flat, folder-prefixed
km = json.load(open(os.path.join(REL, "dataset-metadata.json")))
os.makedirs(os.path.join(UP, "kaggle"))
flat = lambda rel: rel.replace("/", "__")
for rel in files + ["MANIFEST.json"]:
    if rel == "dataset-metadata.json":
        continue
    shutil.copyfile(os.path.join(REL, rel), os.path.join(UP, "kaggle", flat(rel)))
for r in km["resources"]:
    r["path"] = flat(r["path"])
json.dump(km, open(os.path.join(UP, "kaggle", "dataset-metadata.json"), "w"), indent=1)
# Zenodo: one zip + sha256
os.makedirs(os.path.join(UP, "zenodo")); z = os.path.join(UP, "zenodo", "pmitc-v1.2.0.zip")
with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
    for rel in files + ["MANIFEST.json"]:
        zf.write(os.path.join(REL, rel), "pmitc-v1.2.0/" + rel)
open(z + ".sha256", "w").write(f"{h(z)}  pmitc-v1.2.0.zip\n")
# checks
bad = [rel for rel in files if h(os.path.join(UP, "hf", rel)) != sha[rel]]
bad += [rel for rel in files if rel != "dataset-metadata.json" and h(os.path.join(UP, "kaggle", flat(rel))) != sha[rel]]
kres = {r["path"] for r in km["resources"]}
missing_res = sorted(flat(r) for r in files if r.startswith("data/") and flat(r) not in kres)
with zipfile.ZipFile(z) as zf:
    assert zf.testzip() is None
    names = set(zf.namelist())
    bad += [rel for rel in files if "pmitc-v1.2.0/" + rel not in names]
    bad += [rel for rel in files if hashlib.sha256(zf.read("pmitc-v1.2.0/" + rel)).hexdigest() != sha[rel]]
res = dict(hf_files=len(files), kaggle_files=len(os.listdir(os.path.join(UP, "kaggle"))), zip_bytes=os.path.getsize(z), mismatches=bad,
           kaggle_data_files_without_resource=missing_res)
json.dump(res, open(os.path.join(D, "logs", "upload_copies_check.json"), "w"), indent=1)
print(res)
assert not bad and not missing_res
