# Frozen methods and engineering adaptations

## Formula language and timing

`expressions.py` preserves the reviewed R2 AST parser, unit checks and causal matrix operators. Limits are depth 6, ten operation nodes, three fields and interaction order 2. Windows are 1, 2, 3, 5, 10, 20, 40, 60, 120 and 252 observations. Rolling statistics require complete windows; division by zero and unsupported finite domains become missing. Generation seed is 20260929 + round ID, so main round 1 uses 20260930. Commutative addition/multiplication are canonically sorted.

`DualEvaluator` uses information through t-1, holds at close t, and earns raw same-security return at the next market close. Expression lags remain additional. Both position date and return endpoint must lie in a summary period. Continuous history and preceding warmup weights carry across year and block boundaries. Terminal signals can remain recorded while outside-period P&L is missing.

## Books, costs and direction

The transparent book centers eligible cross-sectional ranks. The WQ-style local book combines delays 1–4 with weights 4:3:2:1, removes SIC2 score means, ranks, and removes SIC2 rank means. Both normalize absolute target exposure to 2 and net to zero. Single-name cap is 0.08. The WQ-style book also requires zero group net exposure. Infeasible days become undefined; weights are not clipped or optimized into feasibility.

Any missing return on a nonzero holding makes strict daily P&L missing. A nonheld missing return is harmless. Target turnover is `0.5 * sum(abs(w_t - w_previous))`, excluding price drift. Per-side cost is `2 * turnover * bps / 10000` at 0/5/10 bps. Direction comes from explicit original metadata when present; otherwise choose once from 2019–2021 WQ-style train mean under symmetric costs. Later returns cannot select the sign. Dynamic fold directions are diagnostics only.

Finite-date statistics are conditional observable summaries. Complete-path return, Sharpe and drawdown are available only when the entire path is observed, starting NAV at 1. Gaps are not silently turned into a continuous investable history.

## Screening evolution

R1 established monthly PIT membership, historical links and baseline factor evaluation. R2 added bounded AST generation and causal portfolio evaluation. `LOCAL_FIRST_FULL20K_V1` froze both full-calendar evaluations and train-only direction. Its net-cost route A required positive gross and net5 means, at least two positive net5 years and finite ranking statistics.

`LOCAL_RESELECTION_V2` preserved those evaluations and added gross route B: positive gross mean and Sharpe, at least two positive gross years, finite annual Sharpe/drawdown, at least 126 annual observed days, and the same technical coverage gates. Route A's 2,227 qualifiers are contained in B's 10,117. The final `SIGNAL_FIRST_SCREENING_V1` ranks approximately representable candidates using five coordinates: local Fitness, worst annual gross Sharpe, pooled gross Sharpe, median annual gross Sharpe, and negative absolute gross drawdown. Tie order: positive gross years, Fitness, worst year, pooled Sharpe descending; nodes and candidate ID ascending. This is the final 40-layer method, distinct from the earlier three-target cost Pareto routine retained for evolution/regression.

Local Fitness is `S * sqrt(abs(252 * mean_gross_return) / max(mean_target_turnover, .125))`. Its gross/turnover denominators are not proven harmonized with BRAIN. Platform Sharpe, Fitness and check outcomes never rank local candidates.

Data gates in both full and development periods: at least 80% of dates with signal coverage at least 50%; at least 80% aligned finite-IC dates; at least 80% defined target-book dates; strict return observability at least 95% conditional on defined target dates. Unknown data quality fails eligibility rather than becoming a zero statistic.

## Signal-first decisions

Effective scores are captured from one unchanged `books_at` call and direction is applied after the nonlinear construction. Signed scores and actual weights share a computation path; they are not independent pieces of evidence. Retrieval uses fixed quarter/month snapshots over 2019–2023 and an absolute-correlation proxy, then exact Spearman re-ranks common finite stocks with average ties. Retrieval never proves deferral.

Full confirmation requires at least 100 common stocks per usable day; at least 126 usable days in each year and at least 70% annual coverage; at least 80% full-date support; median signed rho at least .97; at least 80% of usable rhos at least .90; normalized final-weight L1 median at most .05, p90 at most .10 and p99 at most .20; common-support p10 at least .90; equal defined-book masks; raw coverage difference at most .02; and no improvement beyond 1e-10 on any quality coordinate. Opposite, unknown or quality-tradeoff pairs remain available. Every deferred candidate links directly to a retained higher-priority representative; similarity chains cannot remove it.

`confirm_pair` is a small array adapter of the original file-backed confirmation logic. Saved-return correlation is a diagnostic and excluded from that adapter; it is not an eligibility gate. The demo compares full histories because its pool is tiny; it does not claim to reproduce the original snapshot retrieval scheduler.

## Publication engineering

No numerical edits were made to copied AST, generator, data builder, dual evaluation or extracted helper bodies. Path configuration moves to environment variables and package resources. `FullInterpreter` hashes the installed sibling operator module, replacing a project-layout path. Private ledgers, platform orchestration, browser captures and large-run scheduling are omitted. Notebook adaptations replace private outputs with synthetic calls.

New adapters implement small monthly/accounting preprocessing interfaces, route-B screening, array-based confirmation and explicit CLI dispatch. These are separately tested and identified in provenance. The original full research manifest and outputs remain authoritative; no historical experiment result was recomputed or overwritten during publication.
