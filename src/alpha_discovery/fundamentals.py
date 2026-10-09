"""Reviewed R1 accounting ratios. No data rows are distributed."""
import pandas as pd

def numeric(series):
    return pd.to_numeric(series, errors="coerce").astype("float64")

def construct_factors(panel):
    result = panel.copy()
    at = numeric(result["at"])
    sale = numeric(result["sale"])
    close = numeric(result["dlyclose"])
    shares = numeric(result["shrout"])
    market_cap = close.abs() * shares / 1000.0
    result["market_cap_mil"] = market_cap.where(market_cap > 0)

    valid_at = at.notna() & at.gt(0)
    valid_sale = sale.notna() & sale.gt(0)
    valid_market_cap = result["market_cap_mil"].notna() & result["market_cap_mil"].gt(0)

    result["roa"] = (numeric(result["ni"]) / at).where(valid_at)
    result["operating_profitability"] = (numeric(result["oiadp"]) / at).where(valid_at)
    result["cashflow_to_assets"] = (numeric(result["oancf"]) / at).where(valid_at)
    result["asset_turnover"] = (sale / at).where(valid_at)

    debt_complete = result["dltt"].notna() & result["dlc"].notna()
    result["leverage"] = ((numeric(result["dltt"]) + numeric(result["dlc"])) / at).where(valid_at & debt_complete)
    result["cash_to_assets"] = (numeric(result["che"]) / at).where(valid_at)
    result["capex_to_assets"] = (numeric(result["capx"]) / at).where(valid_at)

    result["inventory_to_sales"] = (numeric(result["invt"]) / sale).where(valid_sale)
    result["receivables_to_sales"] = (numeric(result["rect"]) / sale).where(valid_sale)

    ceq = numeric(result["ceq"])
    result["book_to_market"] = (ceq / result["market_cap_mil"]).where(valid_market_cap & ceq.gt(0))
    result["earnings_yield"] = (numeric(result["ni"]) / result["market_cap_mil"]).where(valid_market_cap)
    result["cashflow_yield"] = (numeric(result["oancf"]) / result["market_cap_mil"]).where(valid_market_cap)
    return result
