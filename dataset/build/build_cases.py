"""Derive cases.csv from claims.csv (computed fields) plus a hand-written title and category per case."""
import csv, os
from collections import defaultdict

D = os.path.join(os.path.dirname(__file__), "..", "data")
claims = list(csv.DictReader(open(os.path.join(D, "claims.csv"))))
wallets = list(csv.DictReader(open(os.path.join(D, "wallet_labels.csv"))))
old = {r["case_id"]: r for r in csv.DictReader(open(os.path.join(D, "cases.csv")))}

NEW = {  # case_id: (title, category)
 "arbitrum-airdrop-2023": ("Arbitrum airdrop timing, March 2023", "crypto"),
 "campaign-staff-bets": ("Campaign staffers betting on own candidates", "political_election"),
 "coinbase-earnings-mentions": ("Earnings-call mention markets read aloud by a CEO", "corporate_disclosure"),
 "iran-military-trader-967k": ("One trader, Iran military bets since 2024 (about $967k)", "military_geopolitics"),
 "israel-election-2026-10": ("Israel general election, Oct 27 2026", "political_election"),
 "israel-strike-2025-06-week": ("Israel strikes Iran 'this week', June 2025 (13 users)", "military_geopolitics"),
 "kalshi-q1-2026-aggregate": ("Kalshi Q1 2026 enforcement statistics", "aggregate"),
 "kalshi-sotu-attendance": ("State of the Union attendance market (outcome maker)", "political_decision"),
 "kalshi-teleprompter-2026": ("Trump speech mention markets (teleprompter operator)", "political_decision"),
 "midterms-2026": ("US midterm elections 2026", "political_election"),
 "netanyahu-odds-support-2026": ("Pro-Netanyahu odds support bets, Oct 2026", "political_election"),
 "nyt-80-accounts": ("New York Times review: 80+ suspicious accounts", "aggregate"),
 "polymarket-referrals-aggregate": ("Polymarket referrals to law enforcement", "aggregate"),
 "polysights-flags-aggregate": ("Polysights flagged trades (Bloomberg analysis)", "aggregate"),
 "pope-conclave-2025": ("Papal conclave, May 2025", "award_leak"),
 "solidus-multichain": ("Solidus Labs multichain insider clusters", "aggregate"),
 "super-bowl-halftime-2025": ("Super Bowl LIX halftime performers", "celebrity"),
 "survivor-50-2026": ("Survivor 50 winner (pre-taped show)", "celebrity"),
 "tariff-decisions-2026": ("Tariff decision markets", "political_decision"),
 "trump-zelensky-meeting-2025-12": ("Trump meets Zelenskyy by Dec 31 2025", "political_decision"),
 "us-iran-strike-2025-06": ("US strike on Iran, June 21 2025", "military_geopolitics"),
 "vance-vp-2024": ("Trump VP pick, July 2024 (tip allegation)", "political_decision"),
 "walz-vp-2024": ("Harris VP pick, August 2024", "political_decision"),
 "fed-chair-nomination-2026": ("Trump's Fed chair nomination, January 2026", "political_decision"),
 "super-bowl-halftime-2026": ("Super Bowl LX halftime show performers and setlist, Feb 2026", "celebrity"),
 "openai-markets-aggregate": ("OpenAI release markets: Unusual Whales flags", "aggregate"),
 "nyt-siena-polls-2026": ("Bets before NYT/Siena Senate poll releases, 2026", "political_election"),
 "kalshi-q2q3-2026-aggregate": ("Kalshi Q2-Q3 2026 enforcement statistics", "aggregate"),
 "world-cup-2026-06": ("FIFA World Cup 2026 match markets, three linked accounts", "sports"),
 "tweet-count-self-2026-03": ("Weekly post-count markets traded by accounts linked to the subject", "celebrity"),
}
import sys
sys.path.insert(0, os.path.dirname(__file__))
from dates import parse_date, earliest  # noqa: E402


RANK = {"E1": 1, "E2": 2, "E3": 3, "E4": 4, "E5": 5, "E6": 6}

by = defaultdict(list)
for r in claims:
    by[r["case_id"]].append(r)
wal = defaultdict(set)
for r in wallets:
    if r["polarity"] in ("suspected", "ambiguous", "negative_control", "manipulation"):
        wal[r["case_id"]].add(r["address"])

def outcome(cl):
    """PROTOCOL A9.2, in priority order."""
    g = {x["evidence_grade"] for x in cl}
    st = [(x.get("stance", "alleges"), x.get("notes", "")) for x in cl]
    if "E1" in g: return "sanctioned"
    if "E2" in g: return "charged"
    if any(s == "clears" and ("clearing_party=official" in n or "clearing_party=platform" in n) for s, n in st): return "cleared_official"
    if any(s == "clears" for s, _ in st): return "cleared_analyst"
    if any(s == "disputes" for s, _ in st): return "disputed"
    if "E3" in g: return "under_investigation"
    return "unresolved"


out = []
for cid in sorted(by):
    cl = by[cid]
    o = old.get(cid, {})
    title, cat = (o.get("title"), o.get("category")) if o else NEW[cid]
    grades = sorted({x["evidence_grade"] for x in cl}, key=RANK.get)
    fam = sorted({x["family"] for x in cl})
    out.append(dict(
        case_id=cid, title=title, category=cat,
        platform=";".join(sorted({x["platform"] for x in cl})), family=";".join(fam),
        case_grade=grades[0], grades_present=";".join(grades),
        event_date=earliest(cl, "event_date")[0], event_date_earliest=earliest(cl, "event_date")[1],
        event_date_precision=earliest(cl, "event_date")[2],
        first_claim_date=earliest(cl, "claim_date")[0], first_claim_date_earliest=earliest(cl, "claim_date")[1],
        first_claim_date_precision=earliest(cl, "claim_date")[2],
        n_claims=len(cl), n_sources=len({x["url"] for x in cl}),
        n_wallet_addresses=len(wal.get(cid, ())),
        max_amount_claimed_usd=max((float(x["amount_claimed_usd"]) for x in cl if x["amount_claimed_usd"]), default=""),
        amounts_disagree=len({x["amount_claimed_usd"] for x in cl if x["amount_claimed_usd"]}) > 1,
        investigation_outcome=outcome(cl),
        status_note=o.get("notes", o.get("status_note", ""))))
f = list(out[0])
with open(os.path.join(D, "cases.csv"), "w", newline="") as h:
    w = csv.DictWriter(h, fieldnames=f); w.writeheader(); w.writerows(out)
g = defaultdict(int)
for r in out: g[r["case_grade"]] += 1
print(len(out), "cases; by grade", dict(sorted(g.items())))
