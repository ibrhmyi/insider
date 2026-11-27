"""A34: the economic view of the leg files. Builders read legs through legs_sql(), which swaps the econ columns into the
standard names (wallet_side, asset_id, outcome_label, price, usdc) and keeps econ_inferred. PMITC_RAW_VIEW=1 reads the raw fills
(for comparisons); the default is the econ view."""
import os

RAW = os.environ.get("PMITC_RAW_VIEW") == "1"


def legs_sql(paths):
    src = f"read_parquet({paths!r})" if isinstance(paths, list) else f"read_parquet('{paths}')"
    if RAW:
        return f"(SELECT * EXCLUDE (econ_side, econ_asset_id, econ_outcome_label, econ_price_usdc, econ_size_usdc, econ_inferred), false AS econ_inferred FROM {src})"
    return (f"(SELECT * EXCLUDE (econ_side, econ_asset_id, econ_outcome_label, econ_price_usdc, econ_size_usdc, econ_inferred) "
            f"REPLACE (econ_side AS wallet_side, econ_asset_id AS asset_id, econ_outcome_label AS outcome_label, econ_price_usdc AS price, econ_size_usdc AS usdc), "
            f"econ_inferred FROM {src})")
