# Reproduction guide

## Scope and environment

The released local numerical path is offline. Python 3.12/3.13 and dependencies are fixed in `pyproject.toml`. The tested release environment is recorded in `validation.md`. Install with `python -m pip install '.[dev]'`. Environment variables are read before importing the numerical modules; change them in a new process. No passwords or tokens are needed by this package.

## A. Synthetic Demo

```bash
alpha-discovery demo --output artifacts/demo
alpha-discovery generate --count 12 --output artifacts/generated
pytest -q
python scripts/verify_results.py
```

The demo uses eight declared teaching formulas and fully artificial inputs with synthetic identifiers. The generator command separately demonstrates the unchanged seeded generator. It creates a small registry and attempt ledger. The demo does not use saved real candidates. Its calendar consists of weekdays and does not reproduce exchange holidays.

Expected demo outputs: `summary.json`, candidate metrics, local Pareto order, redundancy decisions and eight daily CSVs. Every summary identifies `SYNTHETIC_DEMO`. Qualifiers are determined by actual frozen gates rather than forced to pass. Insufficient support remains unknown. This should run on a laptop within minutes, using hundreds of MB to approximately 1 GB depending on dataframe copies and the Python allocator.

The three notebooks use installed package functions and can run in any working directory. Outputs are cleared in Git. Execute them using `python scripts/execute_notebooks.py --output artifacts/notebooks`; output files remain outside the release whitelist.

## B. Licensed Research Reproduction

Obtain your own permitted data extracts. This repository contains no authorized data and makes no authenticated download requests. The historical input tables were CRSP `dsf_v2` (with `dlycaldt` renamed `date`), CRSP `dsenames`, Compustat annual fundamentals and the CCM historical linking table. Vendor schemas and entitlements may differ; verify your subscribed table definitions.

### Preparation requirements

1. Supply CRSP daily records for **2017–2024** with date-valid security eligibility. The original extraction restricted historical name rows to share codes 10/11 and exchange codes 1/2/3. Preserve missing raw returns and the entire observed market calendar.
2. Form monthly universe membership on the last eligible market date of each month, ranking positive `abs(dlyclose) * shrout` descending and PERMNO ascending for exact ties. Select the top 3,000; activate next month. Historical preparation needs 2017 membership to support January 2018, and subsequent memberships through 2024. This is a project-defined universe, not BRAIN TOP3000.
3. Link PERMNO to GVKEY using `LU/LC`, primary `P/C` CCM links with `linkdt <= date <= linkenddt`. Preserve open-ended links. Reject multiple distinct valid GVKEY targets, rather than selecting one silently. Provide sufficient annual account history (the original downloaded history begins in 2015) for 2019 signals.
4. Reject ambiguous GVKEY/datadate keys and use backward as-of accounting attachment with `available_date = datadate + 180 calendar days`. Preserve exact-match availability. Compute the reviewed R1 ratios from the fields in `data/schema.md`. The R2 builder masks fundamental fields when `date - datadate > 730` calendar days.
5. Retain formation and accounting dates as audit columns. The released panel builder consumes these prepared annual files and does not reconstruct CCM joins or licensed extracts automatically. The small preprocessing adapters and notebook demonstrate parts of preparation; they are not an audited replacement for the original whole extraction workflow.

### Required file layout

Point `--data-root` at an external directory containing:

```text
raw/crsp_daily/crsp_daily_2017.parquet ... crsp_daily_2024.parquet
processed/top3000_price_volume/top3000_membership_2018.parquet
processed/top3000_with_fundamentals/top3000_with_fundamentals_2019.parquet
... top3000_with_fundamentals_2024.parquet
```

These are **researcher-supplied prerequisites**, not files downloaded by a provided command. The historical R2 builder retains its original behavior: 2017 raw prewarm data; cross-sectional warmup via the 2018 membership file; 2019–2024 selected panels. It does not improve earlier warmup retrospectively. See `data/schema.md` for exact columns and units.

### Offline stage commands

```bash
export ALPHA_DATA_ROOT="$PWD/../licensed_data"
export ALPHA_WORK_DIR="$PWD/../local_reproduction"
alpha-discovery build-panel --data-root "$ALPHA_DATA_ROOT" --work-dir "$ALPHA_WORK_DIR"
alpha-discovery generate --count 12 --output "$ALPHA_WORK_DIR"
alpha-discovery evaluate --work-dir "$ALPHA_WORK_DIR" \
  --formula 'rank(ts_mean(returns,5))' --candidate-id LOCAL_USER_EXAMPLE
```

`build-panel` validates keys, formation timing and account availability, writes memory-mapped field matrices and an audit. `evaluate` creates a JSON result and daily parquet with both portfolio evaluations, fixed direction, endpoints, costs, observability and selection metrics. It evaluates the formula explicitly requested by the researcher.

For route screening, load a result and call `quality_reasons(result['selection_metrics'], rules)` and `route_b_reasons(result, rules)`. Qualified local rows can be ranked with `quality_order`; provided books can be compared with `extract_books`, `pair_sample`, `summarize_pair` and `confirm_pair`. Notebook 03 demonstrates these interfaces. Platform representability must be reviewed separately; the demo eligibility flag means only that its formulas run locally.

### Exact historical reconstruction requirements

The original frozen 20,000-candidate manifest, explicit original fixed-direction metadata, translator evidence, queue order and saved platform records are retained in the private research archive. They are not redistributed because candidate publication rights are unresolved. The seeded generator alone does not substitute for the authoritative frozen manifest. Therefore this release enables licensed local computations and method reproduction, but **does not provide a one-command exact reconstruction of every historical candidate identity or BRAIN outcome**.

Do not infer the historical 20,000 counts or 82 platform passes from demo outputs. Independently regenerated candidates define a separate experiment. Compare licensed reproductions against authorized original checkpoints only when you have permission to access them. Match formula/sign/settings identities, daily dates, finite-return support, weight constraints, turnover, fixed direction and metric definitions at `atol=1e-12`, `rtol=1e-10` before treating results as equivalent.

### Resources and platform stage

The original local protocol used a 24-GiB machine, at most three workers, at most 60% of memory, and a cumulative 48-hour computation allowance. These are historical safeguards, not runtime guarantees. Prepared panels and daily evidence can consume tens of GB; measure RSS and disk use on a pilot before any large reconstruction. This release executes one requested local formula at a time and has no large-run scheduler.

BRAIN uses its own data, universe, classification, portfolio implementation and observed simulation period. Use the normal authorized platform interface and applicable account limits. This package contains no simulation, submission, credential extraction or private-endpoint client. Published aggregates are saved observational evidence. An exact offline rebuild of platform outputs is unavailable.
