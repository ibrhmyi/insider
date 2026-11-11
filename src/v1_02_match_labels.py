"""Match documented labels to wallets using ONLY the frozen matching rule (rules/frozen_v1.md):
handle == name or pseudonym (case-insensitive) on that wallet's fills in the market; address prefix must be unique in the market.
Output: data/labels/documented_wallets_matched.csv"""
import pandas as pd
from common import CLEAN, DATA

L = pd.read_csv(DATA / "labels" / "documented_wallets.csv")
out = []
for _, r in L.iterrows():
    f = pd.read_csv(CLEAN / f"v1_fills_{r.market_key}.csv")
    ident = str(r.identifier).lower()
    if r.identifier_type == "handle":
        hit = f[(f["name"].astype(str).str.lower() == ident) | (f["pseudonym"].astype(str).str.lower() == ident)]
        ws = sorted(set(hit.proxy_wallet))
        how = "handle==name/pseudonym"
    else:
        ws = sorted({w for w in f.proxy_wallet.unique() if w.lower().startswith(ident)})
        how = "unique address prefix"
    status = "matched" if len(ws) == 1 else ("not found in this market" if not ws else f"ambiguous ({len(ws)} wallets)")
    out.append(dict(**r.to_dict(), match_rule=how, match_status=status, matched_wallet=ws[0] if len(ws) == 1 else "",
                    candidates=";".join(ws) if len(ws) > 1 else ""))
M = pd.DataFrame(out)
M.to_csv(DATA / "labels" / "documented_wallets_matched.csv", index=False)
print(M[["label_id", "identifier", "match_status", "matched_wallet"]].to_string())
