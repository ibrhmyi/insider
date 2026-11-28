"""PROTOCOL A35, A35.1: alleged (wallet, case, condition_id, side) from claim_positions. A wallet's alleged positions come from the claims
linked to it (claim_wallet_links); a wallet whose linked claims have no claim_positions row takes the rows of its case's cluster claims."""
import os
import pandas as pd


def alleged_positions(D):
    rd = lambda f: pd.read_csv(os.path.join(D, "data", f), dtype=str, keep_default_na=False)
    cp, links, cl, W = rd("claim_positions.csv"), rd("claim_wallet_links.csv"), rd("claims.csv"), rd("wallet_labels.csv")
    W = W[W.label_broad.str.lower() == "true"][["address", "case_id"]].rename(columns={"address": "wallet"}).assign(wallet=lambda d: d.wallet.str.lower())
    cp = cp.assign(condition_id=cp.condition_id.str.lower())
    own = links[["claim_id", "wallet", "case_id"]].assign(wallet=lambda d: d.wallet.str.lower()).drop_duplicates()
    own = own.merge(W, on=["wallet", "case_id"]).merge(cp[["claim_id", "condition_id", "side"]], on="claim_id")
    have = set(zip(own.wallet, own.case_id))
    clus = cp.merge(cl[cl.subject_type == "cluster"][["claim_id"]], on="claim_id")
    rest = W[[(w, k) not in have for w, k in zip(W.wallet, W.case_id)]].merge(clus[["claim_id", "case_id", "condition_id", "side"]], on="case_id")
    out = pd.concat([own.assign(basis="linked_claim"), rest.assign(basis="case_cluster_claim")], ignore_index=True)
    return out.drop_duplicates(["wallet", "case_id", "condition_id", "side"])[["wallet", "case_id", "condition_id", "side", "claim_id", "basis"]]


if __name__ == "__main__":
    D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    a = alleged_positions(D)
    print(len(a), "rows;", a.groupby(["wallet", "case_id"]).ngroups, "wallets;", a.groupby("basis")[["wallet", "case_id"]].apply(lambda d: d.drop_duplicates().shape[0]).to_dict())
    print(a.groupby("case_id")[["wallet"]].nunique().wallet.to_dict())
