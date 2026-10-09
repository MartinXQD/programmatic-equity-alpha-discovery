# Researcher-supplied input schema

No licensed rows are distributed. Keys must be unique and nonmissing. Dates are timezone-naive historical market dates; returns and ratios are decimals, not percentages.

| File/table | Required fields | Meaning and unit |
|---|---|---|
| Annual raw CRSP daily parquet | `date`, `permno`, `dlyret`, `dlyretx`, `dlyvol`, `dlyclose`, `shrout` | PERMNO security key; same-security daily return including/excluding distributions; volume in shares; dollar price; shares outstanding in thousands in the historical extract |
| Date-valid security names, preparation only | `permno`, `namedt`, `nameendt`, `shrcd`, `exchcd`, `siccd` | Historical identity and common-share/exchange eligibility; SIC2 = floor(SIC/100) |
| 2018 monthly membership | `permno`, `apply_month_start` | Membership formed at previous month end; preparation audit also retains `formation_date`, rank and capitalization |
| Prepared annual fundamental panels | `date`, `permno`, `siccd`, `formation_date`, `available_date`, `datadate`, all ten fundamental fields below | Unique date/security rows; no future membership formation or attached accounts |
| CCM, preparation only | `gvkey`, `permno` (normalized LPERMNO), `linkdt`, `linkenddt`, `linktype`, `linkprim` | Historical company/security links; LU/LC and P/C filters; ambiguity rejected |
| Annual Compustat, preparation only | `gvkey`, `datadate`, `fyear`, `at`, `sale`, `ni`, `oiadp`, `oancf`, `dltt`, `dlc`, `che`, `capx`, `ceq`, `invt`, `rect` | Annual monetary values in millions; preserve missingness and the source format identifiers needed for duplicate resolution |

The evaluator's fifteen fields are `returns`, `retx`, `volume`, `close`, `market_cap` and the ten accounting fields below. The generator uses a specified subset of twelve. The wider AST vocabulary includes fields not used by the main generator; these require additional licensed sources and are not assumed available.

| Fundamental field | Reviewed definition | Guard |
|---|---|---|
| `book_to_market` | CEQ / market_cap_mil | Positive CEQ and positive capitalization |
| `earnings_yield` | NI / market_cap_mil | Positive capitalization; negative NI retained |
| `cashflow_yield` | OANCF / market_cap_mil | Positive capitalization; negative cash flow retained |
| `roa` | NI / AT | Positive assets |
| `operating_profitability` | OIADP / AT | Positive assets |
| `cashflow_to_assets` | OANCF / AT | Positive assets |
| `asset_turnover` | SALE / AT | Positive assets |
| `leverage` | (DLTT + DLC) / AT | Both debt components observed and positive assets |
| `capex_to_assets` | CAPX / AT | Positive assets |
| `cash_to_assets` | CHE / AT | Positive assets |

`market_cap = abs(dlyclose) * shrout` retains the historical dollar-thousands scale; `market_cap_mil = market_cap / 1000` aligns valuation ratios to Compustat millions. Do not silently change the source share unit. Verify it against your licensed extract.

Available accounts are a 180-calendar-day proxy, not actual filing dates or historical vintages. R2 stale masking uses **date minus datadate**, not date minus available_date. Raw close is made absolute and zero becomes missing; negative volume and daily returns below -1 become missing. No independent delisting adjustment is added to the source return semantics. Exact next-market-day labels use raw same-PERMNO returns even after next-day membership exit.

`ArrayPanel` uses the complete supplied raw calendar. The historical builder derives storage names from selected 2019–2024 and 2018 membership names. This storage choice is not a signal membership rule. Synthetic examples use small artificial integer IDs and weekday calendars.
