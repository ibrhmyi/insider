"""Build the seed label tables (wallets, edges, handles) from cloned public sources.

Inputs: repos cloned under EXT (see SOURCES at bottom). Outputs: ../data/*.csv
Every row carries the file it came from, so any label can be traced back.
"""
import csv, glob, json, os, re, sys
from collections import defaultdict

EXT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ext"
OUT = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(OUT, exist_ok=True)
SDC = os.path.join(EXT, "searadacunha_POLYMARKET-HOME-OF-THE-INSIDERS")
SDC_URL = "https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/blob/main/"
FIN = "research_notes/financial-links-replay-2026-11-07/data/"
ADDR = re.compile(r"^0x[0-9a-f]{40}$")

wallets = []   # one row per (address, case_id, role)
edges = []     # funding / transfer links
handles = []   # cases where only a username is public


def w(address, case_id, role, tier, polarity, handle, source, url, verification, notes=""):
    a = (address or "").strip().lower()
    if not ADDR.match(a):
        raise ValueError(f"bad address {address!r} for {case_id}")
    wallets.append(dict(address=a, handle=handle or "", case_id=case_id, role=role,
                        label_tier=tier, polarity=polarity, source=source,
                        source_url=url, verification=verification, notes=notes))


def e(src, dst, kind, case_id, chain, amount_usd, tx, utc, source, url):
    edges.append(dict(src=src.lower(), dst=dst.lower(), kind=kind, case_id=case_id,
                      chain=chain, amount_usd=amount_usd, tx=tx, utc=utc,
                      source=source, source_url=url))


def rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))

# 1. Vedant-29 known_insiders.json (8 wallets, each with an X post as source)
VED = os.path.join(EXT, "Vedant-29_polymarket-insider-detection/data/known_insiders.json")
ved_case = {
    "0xee50a31c3f5a7c77824b12a941a54388a2827ed6": ("google-yis-2025", "L2_official_case_analyst_wallet", "CONFLICT: press cites prefix 0xafEe for AlphaRaccoon; resolve with Gamma profile lookup"),
    "0xc51eedc01790252d571648cb4abd8e9876de5202": ("spotify-wrapped-2025", "L3_analyst_full_address", ""),
    "0x6baf05d193692bb208d616709e27442c910a94c5": ("maduro-2026-01", "L3_analyst_full_address", "SBet365; also in searadacunha Maduro pnl table"),
    "0x31a56e9e690c621ed21de08cb559e9524cdb8ed9": ("maduro-2026-01", "L2_official_case_analyst_wallet", "Repo labels it the charged account; CFTC names a different handle (Burdensome-Mix) per searadacunha intake; verify"),
    "0x0afc7ce56285bde1fbe3a75efaffdfc86d6530b2": ("israel-rising-lion-2025-06", "L2_official_case_analyst_wallet", "ricosuave666 / rundeep; court defendants unnamed"),
    "0x7f1329ade2ec162c6f8791dad99125e0dc49801c": ("trump-pardon-cz-2025", "L3_analyst_full_address", ""),
    "0x976685b6e867a0400085b1273309e84cd0fc627c": ("mstr-btc-sale", "L3_analyst_full_address", ""),
    "0x55ea982cebff271722419595e0659ef297b48d7c": ("draftkings-pm-launch", "L3_analyst_full_address", "Weakest evidence in that list: 'flagged by Polysights' only"),
}
for d in json.load(open(VED)):
    a = d["address"].lower()
    case, tier, note = ved_case[a]
    label = re.sub(r"\(federally indicted[^)]*\)", "(charged-case account per repo)", d["label"])  # no personal names
    w(a, case, "trader", tier, "suspected", label, "Vedant-29/polymarket-insider-detection data/known_insiders.json",
      d["source_url"], "secondary_list", note)

# 2. Single addresses published in the press or another repo
w("0x09d3273fa76282ce09f4f35a87d6f087c05f4e84", "bubblemaps-military-cluster", "trader", "L3_analyst_full_address", "suspected", "",
  "Bubblemaps via KuCoin/Foresight News", "https://www.kucoin.com/news/flash/nine-polymarket-accounts-allegedly-profit-2-4m-from-u-s-iran-war-predictions",
  "press", "1 of 9; other 8 not printed")
w("0x1d9af60c679cd0b577c3c4ccb4b1a4be4174426d", "zachxbt-axiom-2026-02", "trader", "L3_analyst_full_address", "suspected", "predictorxyz",
  "Lookonchain / DefiOasis via BeInCrypto", "https://beincrypto.com/polymarket-insiders-axiom-zachxbt-profit", "press", "Traded only the Axiom market; $411.6k")
w("0xe31b852756937aef6a047b8de0d36196804b3fb7", "zachxbt-axiom-2026-02", "trader", "L3_analyst_full_address", "suspected", "",
  "dipsylala/polymarket-monitor config.py WATCHLIST_WALLETS (citing Lookonchain)", "https://github.com/dipsylala/polymarket-monitor",
  "secondary_list", "")

# 3. searadacunha: G38 Iran February cohort (38 proxies)
for r in rows(os.path.join(SDC, "research_notes/x-history-2026-11-06/verification/data/g38_accounts.csv")):
    w(r["proxy"], "us-iran-strike-2026-02-28", "trader", "L4_cluster_member", "suspected", r["name"],
      "searadacunha G38 g38_accounts.csv", SDC_URL + "research_notes/x-history-2026-11-06/verification/data/g38_accounts.csv",
      "chain_replayed", f"created {r['created']}; markets {r['markets']}; no_before_yes {r['no_before_yes']}; image_pnl {r['image_pnl']}")
for r in rows(os.path.join(SDC, FIN + "g38_deposit_origins.csv")):
    if r.get("funding_wallet", "").startswith("0x"):
        e(r["funding_wallet"], r["proxy"], "relay_deposit", "us-iran-strike-2026-02-28", r["origin_chain_id"], "",
          r["relay_request_id"], r["created_utc"], "searadacunha g38_deposit_origins.csv", SDC_URL + FIN + "g38_deposit_origins.csv")

# 4. searadacunha: Maduro / Iran pnl table (network of 8 + other Maduro winners)
audit = json.load(open(os.path.join(SDC, "investigations/maduro-iran/results/accounting_audit_2026-11-04.json")))
network = {a.lower() for a in audit["wallets"]}
for r in rows(os.path.join(SDC, "investigations/maduro-iran/sources/phase2/pnl_summary.csv")):
    a = r["account"].lower()
    in_net = a in network
    w(a, "maduro-2026-01", "trader", "L4_cluster_member" if in_net else "L3_analyst_full_address", "suspected", r["name"],
      "searadacunha maduro-iran pnl_summary.csv", SDC_URL + "investigations/maduro-iran/sources/phase2/pnl_summary.csv",
      "chain_replayed", ("in 8-account funding network; " if in_net else "Maduro winner, not in network; ") + f"PnL {r['PnL']}; markets {r['markets']}")

# 5. searadacunha: Nobel 2025, 8 accounts and their Safe owner keys
for r in rows(os.path.join(SDC, "investigations/followup-20261113/sources/data/nobel_accounts.csv")):
    w(r["proxy"], "nobel-peace-2025", "trader", "L4_cluster_member", "suspected", r["handle"],
      "searadacunha followup nobel_accounts.csv", SDC_URL + "investigations/followup-20261113/sources/data/nobel_accounts.csv",
      "chain_replayed", f"funded {r['funded_usdc']}; first Machado buy {r['first_machado_buy_utc']} at {r['first_machado_buy_price']}")
    w(r["safe_owner"], "nobel-peace-2025", "owner_key", "L4_cluster_member", "context", r["handle"] + " owner",
      "searadacunha followup nobel_accounts.csv", SDC_URL + "investigations/followup-20261113/sources/data/nobel_accounts.csv",
      "chain_replayed", "owner_is_funder=" + r["owner_is_funder"])
    e(r["safe_owner"], r["proxy"], "safe_owner", "nobel-peace-2025", "polygon", r["funded_usdc"], r["first_machado_buy_tx"],
      r["first_funding_utc"], "searadacunha nobel_accounts.csv", SDC_URL + "investigations/followup-20261113/sources/data/nobel_accounts.csv")

# 6. searadacunha: KPMG cohort (22 proxies) and handoffs
kp = rows(os.path.join(SDC, FIN + "kpmg_accounts.csv"))
by_label = {}
for r in kp:
    by_label[r["public_label"]] = r["polygon_proxy"].lower()
    w(r["polygon_proxy"], "kpmg-earnings-2025-26", "trader", "L4_cluster_member", "suspected", r["public_label"],
      "searadacunha kpmg_accounts.csv", SDC_URL + FIN + "kpmg_accounts.csv", "chain_replayed", r["cohort_role"])
for r in rows(os.path.join(SDC, FIN + "kpmg_handoffs_verified.csv")):
    s, t = by_label.get(r["sender"]), by_label.get(r["recipient"])
    if s and t:
        e(s, t, "relay_handoff", "kpmg-earnings-2025-26", "polygon-solana-polygon", "", r["L1_polygon_tx"], r["L1_utc"],
          "searadacunha kpmg_handoffs_verified.csv", SDC_URL + FIN + "kpmg_handoffs_verified.csv")

# 7. searadacunha: Biden pardon accounts and the shared cash-out address
for r in rows(os.path.join(SDC, FIN + "biden_pardon_shared_deposit.csv")):
    e(r["proxy"], r["to"], "cashout", "biden-pardons", "polygon", int(r["amount_atomic"]) / 1e6, r["tx"], r["utc"],
      "searadacunha biden_pardon_shared_deposit.csv", SDC_URL + FIN + "biden_pardon_shared_deposit.csv")
for a, h in {(r["proxy"].lower(), r["account"]) for r in rows(os.path.join(SDC, FIN + "biden_pardon_shared_deposit.csv"))}:
    w(a, "biden-pardons", "trader", "L4_cluster_member", "suspected", h, "searadacunha biden_pardon_shared_deposit.csv",
      SDC_URL + FIN + "biden_pardon_shared_deposit.csv", "chain_replayed", "")

# 8. searadacunha: Railgun Venezuela tree (negative control)
for r in rows(os.path.join(SDC, FIN + "railgun_tree_accounts.csv")):
    w(r["proxy"], "railgun-venezuela-control", "trader", "NC_negative_control", "negative_control", "",
      "searadacunha railgun_tree_accounts.csv", SDC_URL + FIN + "railgun_tree_accounts.csv", "chain_replayed",
      f"one bet: {r['market'][:60]} {r['outcome']} at {r['price']}; won={r['won']}")
    if r["funding_wallet"].startswith("0x"):
        e(r["funding_wallet"], r["proxy"], "funding", "railgun-venezuela-control", "polygon", int(r["credited_atomic"] or 0) / 1e6,
          r["relay_payout_tx"], r["profile_created_utc"], "searadacunha railgun_tree_accounts.csv", SDC_URL + FIN + "railgun_tree_accounts.csv")

# 9. searadacunha: XFM collectors (manipulation family, not informed trading)
for r in rows(os.path.join(SDC, FIN + "xfm_collectors.csv")):
    w(r["account"], "xfm-self-trading", "trader", "M_manipulation", "manipulation", r["profile_name"],
      "searadacunha xfm_collectors.csv", SDC_URL + FIN + "xfm_collectors.csv", "chain_replayed", "")
    e(r["account"], r["collector"], "collector_payout", "xfm-self-trading", "polygon", r["amount_out"], r["payout_tx"], r["created_utc"],
      "searadacunha xfm_collectors.csv", SDC_URL + FIN + "xfm_collectors.csv")

# 10. searadacunha: Ballon d'Or case files (ambiguous)
for f in sorted(glob.glob(os.path.join(SDC, "investigations/ballon-dor-wallets/sources/cases/*.json"))):
    d = json.load(open(f))
    a = d.get("address") or ""
    if isinstance(d.get("wallet"), dict) and not a:
        a = d["wallet"].get("address", "")
    a = a if isinstance(a, str) else ""
    if ADDR.match(a.lower()):
        w(a, "ballon-dor-2026", "trader", "A_ambiguous", "ambiguous", d.get("label", ""),
          "searadacunha ballon-dor-wallets cases/" + os.path.basename(f), SDC_URL + "investigations/ballon-dor-wallets/sources/cases/" + os.path.basename(f),
          "chain_replayed", f"identity_level {d.get('identity_level','')}")

# 10b. searadacunha: Iran cluster E (Feb 2026 strike markets) and its transfers
CE = "research_notes/iran-cluster-e-network-2026-11-05/"
for r in rows(os.path.join(SDC, CE + "accounts.csv")):
    if ADDR.match(r["address"].lower()):
        w(r["address"], "us-iran-strike-2026-02-28", "trader", "L4_cluster_member", "suspected", r["account"],
          "searadacunha iran-cluster-e accounts.csv", SDC_URL + CE + "accounts.csv", "chain_replayed",
          f"cluster E group {r['group']}; created {r['profile_created']}; iran_buy_usdc {r['iran_buy_usdc']}")
for r in rows(os.path.join(SDC, CE + "transactions.csv")):
    a, b = r["from_address"].lower(), r["to_address"].lower()
    if ADDR.match(a) and ADDR.match(b):
        e(a, b, r["kind"], "us-iran-strike-2026-02-28", r["route"], r["amount"] if r["symbol"].upper().startswith("USD") else "",
          r["evidence"][:80], r["utc"], "searadacunha iran-cluster-e transactions.csv", SDC_URL + CE + "transactions.csv")

# 11. Handles only (need resolving through the Gamma public-search API)
for h, case, url in [
    ("djijaij83jdo4jdlwjflsg", "us-iran-ceasefire-2026-04-07", "https://finance.yahoo.com/markets/crypto/articles/potential-insiders-made-600k-predicting-171731685.html"),
    ("Elonfax89678", "us-iran-ceasefire-2026-04-07", "https://finance.yahoo.com/markets/crypto/articles/potential-insiders-made-600k-predicting-171731685.html"),
    ("Skoobidoobnj", "us-iran-ceasefire-2026-04-07", "https://ambcrypto.com/?p=576310"),
    ("ricosuave666", "israel-rising-lion-2025-06", "https://www.yahoo.com/news/articles/israel-arrests-members-military-placing-140548894.html"),
    ("rundeep", "israel-rising-lion-2025-06", "https://casinobeats.com/2026/03/27/details-emerge-israeli-military-profiting-from-polymarket-wagers-iran-strikes/"),
    ("AlphaRaccoon", "google-yis-2025", "https://crypto.news/polymarket-trader-accused-of-making-1-2m-using-google-insider-data/"),
    ("Burdensome-Mix", "maduro-2026-01", "https://en.wikipedia.org/wiki/Insider_trading_allegations_during_the_second_Trump_administration"),
    ("Magamyman", "us-iran-strike-2026-02-28", "https://www.npr.org/2026/03/01/nx-s1-5731568/polymarket-trade-iran-supreme-leader-killing"),
    ("Bama124", "walz-vp-2024", "https://benzinga.com/markets/cryptocurrency/24/08/40198371/vp-nominee-tim-walzs-chances-went-from-1-to-100-netting-polymarket-trader-617-000-in-profi"),
    ("romanticpaul", "taylor-swift-engagement", "https://www.sportsbookreview.com/news/polymarket-user-profits-from-swift-kelce-engagement-bet-aug-27-2025/"),
    ("OnlyBibi2026", "netanyahu-odds-support-2026", "https://www.webull.com/news/15340522763527168"),
    ("whopperlover", "bubblemaps-military-cluster", "https://www.ibtimes.co.uk/controversy-surrounds-prediction-markets-insider-trading-1797563"),
    ("aenews0", "nobel-peace-2025", "https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/blob/main/investigations/followup-20261113/FINDINGS.md"),
]:
    handles.append(dict(handle=h, case_id=case, source_url=url, resolved_address=""))

# write
def dump(name, data):
    if not data:
        return
    with open(os.path.join(OUT, name), "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(data[0]))
        wr.writeheader(); wr.writerows(data)

# de-duplicate exact repeats (same address, case, role)
seen, uniq = set(), []
for r in wallets:
    k = (r["address"], r["case_id"], r["role"])
    if k in seen:
        continue
    seen.add(k); uniq.append(r)
dump("wallet_labels.csv", uniq)
dump("wallet_edges.csv", edges)
dump("handles_to_resolve.csv", handles)

c = defaultdict(int)
for r in uniq:
    c[(r["polarity"], r["case_id"])] += 1
print("wallet rows", len(uniq), "unique addresses", len({r['address'] for r in uniq}), "edges", len(edges))
for k in sorted(c):
    print(f"  {k[0]:17s} {k[1]:32s} {c[k]}")
