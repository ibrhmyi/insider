"""Partial-date helpers (PROTOCOL A6.3)."""
import re, datetime


def parse_date(v):
    """PROTOCOL A6.3: partial dates. Returns (earliest possible day as ISO string, precision) or ("", "").
    Accepts YYYY, YYYY-MM, YYYY-MM-DD, YYYY-Qn, and ranges A/B, YYYY-YYYY, YYYY-YYYY-MM-DD (earliest day of A)."""
    v = (v or "").strip()
    if not v:
        return "", ""
    m = re.fullmatch(r"(\d{4})-(\d{4}(?:-\d{2}){0,2})", v)
    if "/" in v or m:
        a = v.split("/")[0] if "/" in v else m.group(1)
        return parse_date(a)[0], "range"
    m = re.fullmatch(r"(\d{4})-Q([1-4])", v)
    if m:
        return f"{m.group(1)}-{3 * int(m.group(2)) - 2:02d}-01", "quarter"
    for fmt, prec, pad in (("%Y-%m-%d", "day", ""), ("%Y-%m", "month", "-01"), ("%Y", "year", "-01-01")):
        try:
            datetime.datetime.strptime(v, fmt)
            return v + pad, prec
        except ValueError:
            pass
    raise ValueError(f"unparseable date {v!r}")


def earliest(rows, key):
    """Earliest possible day among rows[key]; returns (original value, earliest day, precision)."""
    best = None
    for x in rows:
        d, p = parse_date(x[key])
        if d and (best is None or d < best[1]):
            best = (x[key], d, p)
    return best or ("", "", "")
