"""A34, A34.1: the economic view of the leg files. Builders read legs through legs_sql(), which swaps the econ columns into the
standard names (wallet_side, asset_id, outcome_label, price, usdc, shares), keeps econ_inferred, and expands an A34.1 partial leg into its
held SELL part and its inferred BUY part (leg_id suffixed ':x'). PMITC_RAW_VIEW=1 reads the raw fills (for comparisons)."""
import os

RAW = os.environ.get("PMITC_RAW_VIEW") == "1"
ECON = ["econ_side", "econ_asset_id", "econ_outcome_label", "econ_price_usdc", "econ_size_usdc", "econ_inferred", "econ_partial",
        "econ_excess_shares", "econ_excess_asset_id", "econ_excess_outcome_label", "econ_excess_price_usdc", "econ_excess_size_usdc"]


def legs_sql(paths):
    src = f"read_parquet({paths!r})" if isinstance(paths, list) else f"read_parquet('{paths}')"
    ex = ", ".join(ECON)
    if RAW:
        return f"(SELECT * EXCLUDE ({ex}), false AS econ_inferred FROM {src})"
    main = (f"SELECT * EXCLUDE ({ex}) REPLACE (econ_side AS wallet_side, econ_asset_id AS asset_id, econ_outcome_label AS outcome_label, "
            f"econ_price_usdc AS price, econ_size_usdc AS usdc, shares - coalesce(econ_excess_shares, 0) AS shares), econ_inferred FROM {src}")
    xs = (f"SELECT * EXCLUDE ({ex}) REPLACE ('BUY' AS wallet_side, econ_excess_asset_id AS asset_id, econ_excess_outcome_label AS outcome_label, "
          f"econ_excess_price_usdc AS price, econ_excess_size_usdc AS usdc, econ_excess_shares AS shares, leg_id || ':x' AS leg_id), true AS econ_inferred "
          f"FROM {src} WHERE econ_excess_shares > 0")
    return f"({main} UNION ALL BY NAME {xs})"
