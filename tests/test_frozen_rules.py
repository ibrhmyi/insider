"""Guards for the pre-registration rules (see HANDOFF.md, rule 2: freeze before validate).

These tests never touch the network and never import the pipeline. They only check
that the frozen artefacts are intact, so a change to a frozen definition fails CI
instead of silently changing results.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_measures_py_matches_frozen_v0_hash():
    frozen = json.loads((ROOT / "rules" / "frozen_v0.json").read_text())
    sha = hashlib.sha256((ROOT / "src" / "measures.py").read_bytes()).hexdigest()
    assert sha == frozen["measures_py_sha256"], (
        "src/measures.py changed after freezing. A change needs a new frozen version, "
        "committed before it is run, with a dated entry in log/process_log.md."
    )


def test_frozen_v0_has_required_parameters():
    frozen = json.loads((ROOT / "rules" / "frozen_v0.json").read_text())
    for key in ("seed_quantile", "ripple_window_min", "news_buffer_min", "alert_threshold_excess_wallets"):
        assert key in frozen, f"frozen_v0.json is missing {key}"


def test_frozen_rule_documents_exist():
    for name in ("labeling_rule.md", "frozen_v0.md", "frozen_v1.md"):
        assert (ROOT / "rules" / name).is_file(), f"rules/{name} is missing"


def test_documented_wallet_labels_cite_a_source():
    """Labels come only from public reporting (HANDOFF.md, rule 3)."""
    import csv

    path = ROOT / "data" / "labels" / "documented_wallets.csv"
    rows = list(csv.DictReader(path.open()))
    assert rows, "documented_wallets.csv is empty"
    columns = {c.lower() for c in rows[0]}
    assert any("url" in c or "source" in c for c in columns), "labels must carry a source column"
