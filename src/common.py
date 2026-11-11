"""Shared helpers: HTTP with retry/backoff, paths, time parsing.

All API endpoints follow docs.polymarket.com as read on 2026-11-09:
- Gamma:  https://gamma-api.polymarket.com  (market metadata; closed markets need closed=true;
          `limit` silently capped at 100; offset > ~2000 returns 422)
- Data API v2: https://data-api.polymarket.com/v2/...  (v1 retired 2026-11-02, returns 410)
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
CLEAN = DATA / "clean"
AUDIT = DATA / "audit"
FIG = ROOT / "figures"
RULES = ROOT / "rules"
LOG = ROOT / "log"
for p in (RAW, CLEAN, AUDIT, FIG):
    p.mkdir(parents=True, exist_ok=True)

GAMMA = "https://gamma-api.polymarket.com"
DATA_API = "https://data-api.polymarket.com/v2"

SESSION = requests.Session()
SESSION.headers["User-Agent"] = "cp191-capstone-research/0.1"

# every non-200 we see is appended here so the process log can cite it
HTTP_EVENTS = []


def get_json(url, params=None, max_tries=6, timeout=90):
    """GET with retry on 429/503 (honouring Retry-After) and on network errors."""
    delay = 2
    for attempt in range(1, max_tries + 1):
        try:
            r = SESSION.get(url, params=params, timeout=timeout)
        except requests.RequestException as e:  # network-level failure
            HTTP_EVENTS.append(dict(url=url, status="network", detail=str(e)[:200], attempt=attempt))
            time.sleep(delay)
            delay *= 2
            continue
        if r.status_code == 200:
            return r.json()
        HTTP_EVENTS.append(dict(url=url, params=str(params)[:200], status=r.status_code,
                                detail=r.text[:200], attempt=attempt,
                                trace=r.headers.get("x-trace-id")))
        if r.status_code in (429, 503) or r.status_code >= 500:
            wait = float(r.headers.get("Retry-After") or delay)
            time.sleep(wait)
            delay *= 2
            continue
        r.raise_for_status()
    raise RuntimeError(f"gave up after {max_tries} tries: {url} {params}")


def parse_ts(s):
    """Parse Gamma/Data timestamps ('2025-06-22 02:41:50+00', ISO 'Z', epoch str) to epoch seconds."""
    if s is None or s == "":
        return None
    s = str(s)
    if s.isdigit():
        return int(s)
    s = s.replace(" ", "T").replace("Z", "+00:00")
    if s.endswith("+00"):
        s += ":00"
    return int(datetime.fromisoformat(s).timestamp())


def iso(ts):
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def dump(obj, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=str)
