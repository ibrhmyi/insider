"""Run 11 (A35, A4): second section of logs/blind_check_sample.csv for the human second extractor: a seed-192 random 20% of the
claim_positions rows (same draw method as section 1: random.Random(192).sample over row numbers), with claim_id, url and the claim text
only. The mapped market and side are NOT written; the extractor maps each claim to the market(s) and side it describes, blind, and the
answers are compared with data/claim_positions.csv by cp_row (the 1-based data row of that file). Idempotent: rewrites section 2 only.
Usage: python3 build/v1/blind_sample_positions.py"""
import csv, io, os, random

D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
P = os.path.join(D, "logs", "blind_check_sample.csv")
MARK = "# section 2"
cp = list(csv.DictReader(open(os.path.join(D, "data", "claim_positions.csv"))))
cl = {r["claim_id"]: r for r in csv.DictReader(open(os.path.join(D, "data", "claims.csv")))}
k = round(0.2 * len(cp))
pick = sorted(random.Random(192).sample(range(1, len(cp) + 1), k))
sec1 = open(P).read().split(MARK)[0].rstrip("\n") + "\n"
buf = io.StringIO(); w = csv.writer(buf)
w.writerow(["cp_row", "claim_id", "url", "claim_text"])
for i in pick:
    c = cp[i - 1]["claim_id"]
    w.writerow([i, c, cl[c]["url"], cl[c]["claim_text"]])
open(P, "w").write(sec1 + "\n" + f"{MARK}: claim_positions blind mapping (A35; seed 192; {k} of {len(cp)} rows; claim text only, no mapped market or side)\n" + buf.getvalue())
print("section 2 rows", k, "distinct claims", len({cp[i - 1]['claim_id'] for i in pick}))
