"""PROTOCOL A20: claim-wallet links, wallet_grade and the three nested label sets. Reads claims, wallet_labels, handle tables;
writes data/claim_wallet_links.csv and adds doc_grade, wallet_grade, label_broad, label_standard, label_strict, strict_basis to
data/wallet_labels.csv. No claim is edited. Usage: python3 build/v1/label_sets.py"""
import os, re
import pandas as pd

D = os.path.join(os.path.dirname(__file__), "..", "..")
rd = lambda p: pd.read_csv(os.path.join(D, p), dtype=str, keep_default_na=False)
cl, W = rd("data/claims.csv"), rd("data/wallet_labels.csv")
h1, h7, hc = rd("data/handles_to_resolve.csv"), rd("logs/handle_checks_run7.csv"), rd("logs/handle_checks.csv")
RANK = {g: i for i, g in enumerate("E1 E2 E3 E4 E5 E6".split())}
cl["post_url"] = cl.notes.str.extract(r"post_url=(\S+?)(?:;|\s|$)")[0].fillna("")
named = cl[~cl.subject_type.isin(["aggregate", "market"])]
handle_of = {}
for r in h1.itertuples():
    if r.resolved_address and r.status.startswith("resolved"):
        handle_of.setdefault(r.resolved_address.lower(), set()).add(r.handle.lower())
for r in h7.itertuples():
    if r.address and r.result.startswith("resolved"):
        handle_of.setdefault(r.address.lower(), set()).add(r.subject.lower())
src_handle = {}
for r in W.itertuples():  # handle tokens as recorded by the wallet's label source
    toks = {t.strip().lower() for t in re.split(r"[()/;,]| and ", r.handle) if re.fullmatch(r"[A-Za-z0-9_.\-]{3,}", t.strip())}
    src_handle[(r.address.lower(), r.case_id)] = toks
tok = lambda s: {t.lower() for t in re.findall(r"[A-Za-z0-9_.\-]{3,}", s)}
links = []
for w in W.itertuples():
    a = w.address.lower()
    for c in named[named.case_id == w.case_id].itertuples():
        text = (c.subject + " " + c.claim_text + " " + c.notes).lower()
        st = tok(c.subject)
        if a in text:
            links.append((c.claim_id, a, w.case_id, "address_in_claim"))
        if handle_of.get(a, set()) & st:
            links.append((c.claim_id, a, w.case_id, "resolved_handle"))
        elif src_handle.get((a, w.case_id), set()) & st:
            links.append((c.claim_id, a, w.case_id, "label_source_handle"))
        if w.source_url and w.source_url in (c.url, c.post_url):
            links.append((c.claim_id, a, w.case_id, "source_url"))
for r in hc[hc.check_type.str.contains("complaint|official", case=False) & hc.result.str.contains("match|accept", case=False)].itertuples():
    for c in cl[(cl.case_id == r.case_id) & cl.source_class.eq("S1") & ~cl.subject_type.isin(["aggregate", "market"])].itertuples():
        links.append((c.claim_id, r.address.lower(), r.case_id, "official_figures_match"))
L = pd.DataFrame(links, columns=["claim_id", "wallet", "case_id", "link_type"]).drop_duplicates()
L = L.merge(cl[["claim_id", "evidence_grade", "subject_type"]], on="claim_id")
L.sort_values(["case_id", "wallet", "claim_id", "link_type"]).to_csv(os.path.join(D, "data", "claim_wallet_links.csv"), index=False)
best = lambda s: min(s, key=RANK.get) if len(s) else ""
wg = L.groupby(["wallet", "case_id"]).evidence_grade.agg(best)
dg = named.groupby("case_id").evidence_grade.agg(best)
W["doc_grade"] = [dg.get(c, "") if p in ("suspected", "ambiguous") else "" for p, c in zip(W.polarity, W.case_id)]
W["wallet_grade"] = [wg.get((a.lower(), c), "") for a, c in zip(W.address, W.case_id)]
base = (W.trade_confirmed == "true") & (W.label_family == "informed_trading") & (W.polarity == "suspected")
W["label_broad"] = base & W.doc_grade.isin(["E1", "E2", "E3", "E4", "E5"])
W["label_standard"] = W.label_broad & W.doc_grade.isin(["E1", "E2", "E3", "E4"])
e4 = L[(L.evidence_grade == "E4") & L.link_type.isin(["address_in_claim", "resolved_handle", "label_source_handle", "source_url"])
       & L.subject_type.isin(["address", "handle", "account", "cluster"])]
e4set = set(zip(e4.wallet, e4.case_id))
strict_g = W.wallet_grade.isin(["E1", "E2", "E3"])
strict_e4 = pd.Series([(a.lower(), c) in e4set for a, c in zip(W.address, W.case_id)], index=W.index)
strict_rule = W.label_standard & (strict_g | strict_e4)
# A26: strict also needs >= 1 BUY in a market of its case before that market's precise cut (positions hold exactly the pre-cut buyers)
POS = os.path.join(D, "out", "v1", "positions.parquet")
import duckdb
pre = {(a, k) for a, k in duckdb.sql(f"SELECT DISTINCT wallet, case_id FROM '{POS}' WHERE market_set = 'case' AND t_news_version = 'precise'").fetchall()}
has_pre = pd.Series([(a.lower(), k) in pre for a, k in zip(W.address, W.case_id)], index=W.index)
W["label_strict"] = strict_rule & has_pre
W["strict_no_prenews"] = (strict_rule & ~has_pre).map({True: "true", False: "false"})
W["strict_basis"] = [("wallet_grade_" + g if s and g in ("E1", "E2", "E3") else ("named_in_E4_claim" if s else "")) for s, g in zip(W.label_strict, W.wallet_grade)]
print("strict_no_prenews", list(W[W.strict_no_prenews == "true"][["address", "case_id"]].itertuples(index=False)))
for c_ in ["label_broad", "label_standard", "label_strict"]:
    W[c_] = W[c_].map({True: "true", False: "false"})
W.to_csv(os.path.join(D, "data", "wallet_labels.csv"), index=False)
print("links", len(L), L.link_type.value_counts().to_dict())
s = W[W.label_broad == "true"]
print("broad", len(s), "standard", (W.label_standard == "true").sum(), "strict", (W.label_strict == "true").sum(), W.strict_basis.value_counts().to_dict())
print(s.groupby("case_id")[["label_broad", "label_standard", "label_strict"]].agg(lambda x: (x == "true").sum()).to_string())
