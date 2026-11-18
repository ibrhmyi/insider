"""v2 step 1b: category screen (text only) per rules/model_v2_universe.md. Output data/v2/markets_candidates.csv + exclusions.csv.gz"""
import json, glob, re
import pandas as pd
from common import *
rows = []
for f in glob.glob(str(RAW / "v2_gamma" / "*.json")):
    x = json.load(open(f))
    if len(x) < 1900: rows += x          # windows that hit the 2,000-row cap are replaced by the daily volume-ordered re-pull
for f in glob.glob(str(RAW / "v2_gamma_vol" / "*.json")): rows += json.load(open(f))
df = pd.DataFrame(rows).drop_duplicates("conditionId")
n_pulled = len(df)

EXCL = r"""\bvs\.?\b|\bup or down\b|\bhighest temperature\b|\blowest temperature\b|\bprice of\b|\babove \$|\bbelow \$|\bbetween \$|\bsay\b|\bmention|\btweet|\bposts?\b.*\bx\b|\bo/u\b|\bspread\b|\bwin on 20|\bwin the 20\d\d (nba|nfl|mlb|nhl|world series|super bowl|stanley|masters|us open|french open|wimbledon|champions league|premier league|la liga|serie a|bundesliga|f1|formula)|\bnba\b|\bnfl\b|\bmlb\b|\bnhl\b|\bufc\b|\bfifa\b|\bworld cup\b|\bclub world\b|\batp\b|\bwta\b|\btennis\b|\bgolf\b|\bf1\b|\bgrand prix\b|\besports?\b|\bcs2\b|\bvalorant\b|\bleague of legends\b|\bdota\b|\bbitcoin\b|\bethereum\b|\bsolana\b|\bxrp\b|\bdogecoin\b|\bcrypto price\b|\bbtc\b|\beth\b|\bhottest\b|\bhurricane\b|\bearthquake\b|\bsnow\b|\brain\b|\btemperature\b|\bprimary\b|\belection\b|\bwin the most seats\b|\bvote share\b|\bpoll\b|\bbox office\b|\bnetflix\b|\bspotify\b|\bgdp\b|\bcpi\b|\binflation\b|\bunemployment\b|\bjobs report\b|\bnonfarm\b|\bstock\b|\bclose (above|below)\b|\belected\b|\bmarket cap\b|\bwin the presidency\b|\bfantasy\b|\bnext (us )?president\b|\bparliament|\bmayor\b|\bgovernor\b|\bsenate\b|\bhouse seats\b|\bapproval rating\b|\btrending\b|\bsuper bowl\b|\bolympic|\bcoach\b|\btransfer\b|\bgolden globe|\bgrammy|\bemmy|\bmvp\b|\bheisman\b|\bbalon\b|\bplayoffs?\b|\bchampionship\b|\bseries winner\b|\bmatch\b|\bgame \d\b|\bg\d\b|\bover \d|\bunder \d|\bset \d|\bmap \d"""
INCL = {
 "military_gov": r"\b(strike|strikes|attack|invade|invasion|ceasefire|cease-fire|military|troops|sanction|sanctions|executive order|resign|resigns|removed|fired|impeach|pardon|pardons|annex|nuclear|missile|airstrike|bomb|war\b|arrest|extradit|indict|declassif|tariff|shutdown|default|veto|sign(s|ed)? (the|a) (bill|law)|out as|leave office|step down|out by|captured|killed|assassinat|martial law|embargo|blockade|strait of hormuz|regime|peace deal|treaty|summit|meet with|meeting with|visit)",
 "award_committee": r"\b(nobel|oscar|academy award|best picture|pulitzer|booker|time person of the year|person of the year|man of the year|word of the year|ig nobel|peace prize|palme)",
 "appointment": r"\b(nominate|nominee|nomination|appoint|appointed|confirmed|confirm|cabinet|secretary of|chair of the fed|fed chair|ambassador|director of|attorney general|supreme court|named|pick|prime minister|chancellor|president of|ceo of|ceo\b|chief)\b",
 "central_bank": r"\b(fed|federal reserve|fomc|ecb|bank of england|boe|bank of japan|boj|rate cut|rate hike|interest rate|bps|basis points|rbi|snb|boc|rba|pboc|rate decision)",
 "company": r"\b(release|released|launch|launches|announce|announces|announced|acquire|acquires|acquisition|merger|ipo|files for|partnership|open.?source|gpt|gemini|grok|claude|openai|anthropic|tesla|apple|google|microsoft|nvidia|spacex|starship|model|iphone|tiktok|deal|buy|ban|bankrupt|layoff|recall|approve|fda)",
}
def cat(text):
    t = text.lower()
    if re.search(EXCL, t): return None, "excluded:sports/crypto/election/weather/stat/mention/other keyword"
    for k, p in INCL.items():
        if re.search(p, t): return k, ""
    return None, "no_category_match"

df["closed_ts"] = df.closedTime.map(lambda s: parse_ts(s) if isinstance(s, str) else None)
df["end_ts"] = df.endDate.map(lambda s: parse_ts(s) if isinstance(s, str) else None)
df["res_ts"] = df.closed_ts.fillna(df.end_ts)
lo, hi = parse_ts("2025-01-01T00:00:00Z"), parse_ts("2026-11-01T00:00:00Z")
df["event_title"] = df.events.map(lambda e: (e or [{}])[0].get("title", "") if isinstance(e, list) else "")
df["text"] = df.question.fillna("") + " | " + df.event_title.fillna("")
ex = []
keep = []
for _, r in df.iterrows():
    reason = None
    if not (lo <= (r.res_ts or 0) < hi): reason = "resolution_date_outside_2025-01..2026-10"
    elif float(r.volumeNum or 0) < 20000: reason = "volume<20k"
    else:
        try: pr = [float(x) for x in json.loads(r.outcomePrices)]; oc = json.loads(r.outcomes)
        except Exception: pr, oc = [], []
        if oc != ["Yes", "No"]: reason = "not_Yes/No_binary"
        elif not (pr == [1.0, 0.0] or pr == [0.0, 1.0]): reason = "not_cleanly_resolved(prices=%s)" % (pr,)
        else:
            c, why = cat(r.text)
            if c is None: reason = why
            else: keep.append((r.conditionId, c))
    if reason: ex.append((r.conditionId, r.question[:120], reason))
kc = dict(keep)
df["category"] = df.conditionId.map(kc)
cand = df[df.conditionId.isin(kc)].copy()
cand["yes_won"] = cand.outcomePrices.map(lambda s: int(float(json.loads(s)[0]) == 1.0))
cand["yes_token"] = cand.clobTokenIds.map(lambda s: json.loads(s)[0]); cand["no_token"] = cand.clobTokenIds.map(lambda s: json.loads(s)[1])
# event cap (amendment 2026-11-18, before any trade pull): max 3 markets per event, highest volume first
cand = cand.sort_values("volumeNum", ascending=False)
cand["event_rank"] = cand.groupby(cand.event_title.where(cand.event_title != "", cand.question)).cumcount()
for _, r in cand[cand.event_rank >= 3].iterrows(): ex.append((r.conditionId, r.question[:120], "event_cap_3"))
cand = cand[cand.event_rank < 3]
out = cand[["conditionId","slug","question","event_title","category","res_ts","closed_ts","end_ts","volumeNum","yes_won","yes_token","no_token","negRisk"]]
(DATA / "v2").mkdir(exist_ok=True)
out.sort_values("volumeNum", ascending=False).to_csv(DATA / "v2" / "markets_candidates.csv", index=False)
pd.DataFrame(ex, columns=["conditionId","question","reason"]).to_csv(DATA / "v2" / "exclusions.csv.gz", index=False)
print("pulled", n_pulled, "candidates", len(out))
print(pd.DataFrame(ex, columns=["c","q","reason"]).reason.str[:40].value_counts().head(12))
print(out.category.value_counts())

# Amendment B ranking: volume <= 12M (page-cap proxy), by volume descending
rk = out[out.volumeNum <= 12e6].sort_values("volumeNum", ascending=False)
rk.to_csv(DATA / "v2" / "markets_ranked.csv", index=False)
print("ranked (<=12M):", len(rk), "dropped >12M:", int((out.volumeNum > 12e6).sum()))
