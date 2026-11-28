"""PROTOCOL A35, A35.1: claim_positions, the (market, side) each claim describes, mapped by hand from the claim text and the market
questions. The SPEC below was written from claims.subject / claim_text / notes and markets.question only; this script reads only
questions, structural deadlines (markets.deadline_utc) and token labels, never outcomes, resolutions, prices or fills.
kinds: market = the one market whose question matches the pattern; ladder = every Yes rung whose question matches and whose deadline is on
or after the claim's event_date (A35.1); only = the case's single market. Claims not listed get no row (A35.1 (2)).
Writes data/claim_positions.csv. Usage: python3 build/v1/claim_positions.py"""
import os, re
import pandas as pd

D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STRIKE, CEASE, MADURO, ISRAEL = r"^US strikes Iran by ", r"^US x Iran ceasefire by ", r"^Maduro out by ", r"^Israel military action against Iran"
SPEC = [
    # maduro-2026-01
    ("CL0001", "ladder", MADURO, "Yes", "Maduro-related bets on classified operation knowledge (event 2026-01-03)"),
    ("CL0002", "market", r"^Maduro out by January 31, 2026\?", "Yes", "claim names 'Maduro out by Jan 31, 2026', Yes shares"),
    ("CL0003", "market", r"^Maduro out by January 31, 2026\?", "Yes", "claim names 'Maduro out by end of January'"),
    ("CL0005", "ladder", MADURO, "Yes", "three wallets on the Maduro capture"),
    ("CL0085", "ladder", MADURO, "Yes", "betting on Maduro's removal hours before the arrest"),
    # us-iran-strike-2026-02-28
    ("CL0022", "market", r"^US strikes Iran by February 28, 2026\?", "Yes", "claim names 'US strikes Iran by Feb 28', bought Yes"),
    ("CL0023", "ladder", STRIKE, "Yes", "bet before strike news (market not named; Khamenei bets are not in this case)"),
    ("CL0024", "ladder", STRIKE, "Yes", "netted over $2M on the Feb 28 strikes"),
    ("CL0026", "ladder", STRIKE, "Yes", "bet the strike would come the next day"),
    # us-iran-ceasefire-2026-04-07
    ("CL0032", "ladder", CEASE, "Yes", "Yes bets before the ceasefire post"),
    ("CL0033", "ladder", CEASE, "Yes", "made about $611k on the ceasefire"),
    ("CL0034", "ladder", CEASE, "Yes", "April 2026 ceasefire bet"),
    ("CL0088", "ladder", CEASE, "Yes", "bought before the ceasefire at low odds"),
    ("CL0089", "ladder", CEASE, "Yes", "netted about $194k on the US-Iran ceasefire"),
    # bubblemaps-military-cluster
    ("CL0028", "ladder", STRIKE, "Yes", "bets on US military actions (strike)"),
    ("CL0028", "market", r"^Khamenei out as Supreme Leader of Iran", "Yes", "bets on US military actions (Khamenei)"),
    # israel-rising-lion-2025-06
    ("CL0014", "ladder", ISRAEL, "Yes", "friend bet on the launch date (event 2025-06-13); daily 'strike on <date>' markets not mapped"),
    ("CL0015", "ladder", ISRAEL, "Yes", "bets on Israel-Iran war timing"),
    # google-yis-2025
    ("CL0011", "market", r"^Will d4vd be the #1 searched person", "Yes", "d4vd bet at 0.2% (the #1-searched market)"),
    # nobel-peace-2025
    ("CL0046", "market", r"^Will María Corina Machado win the Nobel Peace Prize", "Yes", "Machado odds jumped before the announcement"),
    ("CL0047", "market", r"^Will María Corina Machado win the Nobel Peace Prize", "Yes", "eight accounts funded before the announcement (Machado market)"),
    ("CL0100", "market", r"^Will María Corina Machado win the Nobel Peace Prize", "Yes", "bet only on her (Machado)"),
    # walz-vp-2024
    ("CL0040", "market", r"^Will Tim Walz be the 2024 Democratic VP nominee", "Yes", "as Walz went from under 1% to 100%"),
    # zachxbt-axiom-2026-02
    ("CL0056", "market", r"^Will Axiom be accused of insider trading", "Yes", "which company ZachXBT would expose (Axiom)"),
    ("CL0057", "market", r"^Will Axiom be accused of insider trading", "Yes", "traded only the Axiom market"),
    ("CL0090", "market", r"^Will Axiom be accused of insider trading", "Yes", "top Axiom-market winners"),
    # taylor-swift-engagement
    ("CL0048", "only", None, "Yes", "heavy Yes buying before the announcement"),
    # trump-pardon-cz-2025
    ("CL0051", "market", r"^Will Trump pardon Changpeng Zhao", "Yes", "bought Yes from Sept 28"),
    # A48 completeness audit (logs/claim_positions_audit.csv): claims of cases without labelled wallets, from the text only
    ("CL0018", "only", None, "Yes", "bet that Israel would strike Iran that week (the case's one market)"),
    ("CL0019", "ladder", r"^US military action against Iran ", "Yes", "won longshot bets on the June 21 strike"),
    ("CL0020", "ladder", r"^US military action against Iran ", "Yes", "timing a June 2025 strike (month-level event date: rungs from June 1)"),
    ("CL0030", "market", r"^Khamenei out as Supreme Leader of Iran by March 31\?", "Yes", "bet that Khamenei would be out by end of March"),
    ("CL0031", "market", r"^US x Iran ceasefire by March 31\?", "Yes", "bet on a ceasefire by March 31"),
    ("CL0035", "ladder", CEASE, "Yes", "five-figure ceasefire bets in April"),
    ("CL0036", "market", r"^Will Trump meet with Zelenskyy by December 31\?", "Yes", "claim names 'Trump meets Zelenskyy by Dec 31'"),
    ("CL0054", "market", r"^OpenAI browser by October 31\?", "Yes", "bet that OpenAI would launch a browser that month (October 2025)"),
    ("CL0118", "ladder", r"^Will Jensen Huang rejoin NVIDIA by ", "Yes", "bet on the CEO's return before the announcement"),
    ("CL0119", "ladder", r"^Will Jensen Huang rejoin NVIDIA by ", "Yes", "bets on the CEO's return (the no-successor market is not in this case)"),
]
MON = "January February March April May June July August September October November December".split()


def qdate(q, ev):
    """Deadline stated in the question ('by March 31, 2026', 'by April 10' (year of the event), 'before July' (1 July)); None if absent."""
    m = re.search(r"\bby (%s) (\d{1,2})(?:, (\d{4}))?" % "|".join(MON), q)
    if m:
        return pd.Timestamp(int(m.group(3) or ev.year), MON.index(m.group(1)) + 1, int(m.group(2)), 23, 59, tz="UTC")
    m = re.search(r"\bbefore (%s)\b" % "|".join(MON), q)
    if m:
        return pd.Timestamp(ev.year, MON.index(m.group(1)) + 1, 1, tz="UTC") - pd.Timedelta(seconds=1)
    return pd.NaT


cl = pd.read_csv(os.path.join(D, "data", "claims.csv"), dtype=str, keep_default_na=False).set_index("claim_id")
mk = pd.read_csv(os.path.join(D, "data", "markets.csv"), dtype=str, keep_default_na=False)
rows = []
for cid, kind, pat, side, note in SPEC:
    case = cl.loc[cid, "case_id"]; g = mk[mk.case_id == case]
    if kind == "only":
        assert len(g) == 1, (cid, len(g)); hit = g; basis = "only_case_market"
    else:
        hit = g[g.question.str.contains(pat, regex=True)]
        if kind == "market":
            assert hit.condition_id.nunique() == 1, (cid, pat, len(hit)); basis = "named_market"
        else:
            ev = pd.Timestamp(cl.loc[cid, "event_date"], tz="UTC")
            dl = pd.Series([qdate(q, ev) for q in hit.question], index=hit.index)  # the question's own date first
            gd = pd.to_datetime(hit.deadline_utc.replace("", None), utc=True, errors="coerce", format="mixed")
            dl = dl.fillna(gd)
            hit = hit[dl >= ev]; basis = "event_ladder_rungs_after_event_date"
            assert len(hit), (cid, pat)
    for r in hit.itertuples():
        outs = r.outcomes.split(";"); assert side in outs, (cid, r.question, outs)
        rows.append(dict(claim_id=cid, case_id=case, condition_id=r.condition_id.lower(), side=side, mapping_basis=basis,
                         mapping_note=note, question=r.question))
out = pd.DataFrame(rows).drop_duplicates(["claim_id", "condition_id", "side"])
out.drop(columns="question").to_csv(os.path.join(D, "data", "claim_positions.csv"), index=False)
print(len(out), "rows;", out.claim_id.nunique(), "claims;", out.groupby("case_id").condition_id.nunique().to_dict())
print(out.groupby(["claim_id", "mapping_basis"]).size().to_string())
