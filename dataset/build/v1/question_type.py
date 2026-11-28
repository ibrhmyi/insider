"""PROTOCOL A38: question_type of a market from its question, by fixed keyword rules (first match wins; case-insensitive).
weather and crypto_price are the placebo categories (A14) and never twins. Import qtype(question) or run to print the case-market counts."""
import re

RULES = [
    ("weather", r"\btemperature\b|\bweather\b|\brain(fall)?\b|\bsnow\b|°[cf]\b|\bhottest\b"),
    ("crypto_price", r"\b(bitcoin|btc|ethereum|eth|solana|sol|xrp|doge|bnb)\b.*\b(above|below|price|up or down|reach|hit|dip)\b|\bprice of\b|\bup or down\b"),
    ("sports", r"\bvs\.?\b|\bo/u\b|\bspread\b|\bboth teams\b|\bwin the (super bowl|world cup|nba|nfl|stanley cup|champions league|world series|final)\b|\bmatch\b|\bgame \d\b"),
    ("legal_action", r"\bpardon\b|\bindict|\bcharged\b|\bsentenc|\bconvict|\baccused\b|\blawsuit\b|\bsue[sd]?\b|\barrest|\btrial\b|\bextradit|\bjail\b|\bprison\b"),
    ("appointment", r"\bnominate\b|\bappoint|\bfed chair\b|\bresign|\bout as\b|\bout by\b|\bout in\b|\bfired\b|\bstep down\b|\bleave office\b|\bremoved\b|\bsupreme leader\b"),
    ("election", r"\belection\b|\bnominee\b|\bprimary\b|\bmayor\b|\bgovernor\b|\bsenate\b|\bparliament\b|\bpresident\b|\bvote\b|\bwin .* seat\b"),
    ("award", r"\bwin the .*(prize|award|ballon|trophy|oscar|grammy)\b|\bnobel\b|\bballon d'or\b|\boscar\b|\bgrammy\b|\bperson of the year\b|\bmvp\b|\bemmy\b|\bgolden globe\b"),
    ("military_action", r"\bstrike[s]?\b|\bmilitary\b|\bwar\b|\binvade|\binvasion\b|\battack\b|\bceasefire\b|\btroops\b|\bmissile\b|\bbomb"),
    ("corporate_release", r"\blaunch\b|\brelease\b|\bannounce\b|\bunveil\b|\bipo\b|\bearnings\b|\bbeat quarterly\b|\bsells any\b|\bacquire\b|\bmerger\b|\bwrapped\b|\bproduct\b"),
    ("crypto_project", r"\btoken\b|\bairdrop\b|\bfdv\b|\bmainnet\b|\bmemecoin\b|\btge\b|\bprotocol\b|\bstablecoin\b"),
]
PLACEBO_TYPES = {"weather", "crypto_price"}


def qtype(question):
    q = (question or "").lower()
    for name, pat in RULES:
        if re.search(pat, q):
            return name
    return "other"


if __name__ == "__main__":
    import os
    import pandas as pd
    D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    mk = pd.read_csv(os.path.join(D, "data", "markets.csv"), dtype=str, keep_default_na=False)
    mk["question_type"] = mk.question.map(qtype)
    print(mk.groupby("question_type").case_id.nunique().to_dict(), mk.question_type.value_counts().to_dict())
