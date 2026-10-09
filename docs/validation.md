# Release validation

This document records publication-time validation. It does not reinterpret an unexecuted stage as success.

| Validation scope | Status | What was checked |
|---|---|---|
| Synthetic Demo | PASS | Actual CLI, eight formulas, raw synthetic inputs, availability/membership, dual books, screening and pair review |
| Original retained numerical tests | PASS | Copied core tests with package import changes; private-ledger/remote tests excluded |
| Original-source regression | PASS | Frozen dual evaluator copied to a temporary package and run on a purely synthetic fixture; daily examples and selection metrics captured for public regression |
| Three notebooks | PASS | Each executed with a fresh kernel using the isolated release environment; no saved historical outputs |
| Historical aggregate reconciliation | PASS | Complete 40-layer sums, 20,000 flow, 3,285 new/reused split, 82 outcome definition |
| Full licensed historical reconstruction | NOT RUN | No rerun of the 20,000 research candidates; licensed data and frozen candidate manifest remain local |
| Historical BRAIN outcomes | SAVED EVIDENCE ONLY | Original recorded complete-cohort outcomes reused as aggregate evidence; zero new simulations or submissions |
| GitHub Actions | Configuration included | Local equivalent commands executed; remote run status reported separately after upload |

The fresh `.venv` uses Python 3.13.9, NumPy 2.3.5, pandas 2.2.3, SciPy 1.16.3, PyArrow 23.0.1, pytest 8.4.2, nbformat 5.10.4, nbclient 0.10.2 and ipykernel 7.1.0. The exact resolved release environment is in `requirements-validation.txt`. The original private lock file is archived separately; this release uses available verified pins rather than treating an old machine environment as portable.

Commands executed from the release root:

```bash
python -m pip install -e '.[dev]'
pytest -q
alpha-discovery demo --output artifacts/demo
python scripts/execute_notebooks.py --output artifacts/notebooks
python scripts/verify_results.py
python scripts/audit_release.py
```

Final local suite: **54 passed in 6.28 seconds**. Tests cover PIT monthly activation, identity/key uniqueness, 180-day availability, 730-day datadate masking, missing debt, future mutation causality, exact next-calendar-market labels independent of future membership, missing held returns, gross/net/group/cap constraints, target turnover and costs, generation determinism, both Pareto methods, score/weight capture, opposite/unknown pairs, data support and golden source regression. Excluded tests require private BRAIN ledgers, original preservation guards or historical snapshot caches; their omission is explicit in `source_provenance.json`.

Demo output: 333,920 artificial raw rows; 1,280 annual account rows; 247,800 selected rows; eight evaluated teaching formulas; four quality-qualified and retained; zero deferred. Those counts demonstrate the small public pipeline and have no historical-market interpretation. Duplicate deferral, opposite exposure and insufficient support are exercised independently by tests.

The first wrapper run exposed duplicate dictionary keyword fields in the new CLI/quality-row adapters. Those engineering errors were fixed and the public CLI was then added to the integration suite. No original numerical function or historical statistic changed.

The publication PDFs are generated with embedded fonts and native vector equations/figures, text-scanned for withheld material and rendered for page-level visual review. Original-source AST fingerprints verify the extracted numerical bodies; provenance records the intentional installed-operator hash path change.

The distribution wheel was built successfully, extracted outside the source tree, and imported with all three packaged configuration files available. The explicit whitelist and Git index contain 63 files. A separate scan compared the released text and PDF contents against all 3,285 recorded private Alpha identifiers and found zero matches; credentials, personal absolute paths and restricted data files were also absent. All 15 PDF pages were rendered and visually inspected.

Original-project preservation was checked against 319,450 file metadata records: no original file was missing and all extracted source hashes remained unchanged. Three runtime records changed while the release was being prepared. Read-only process inspection confirmed an existing `engine.platform_yield_statistics watch` process; its status reported statistics-only operation with browser actions, evaluation and queue mutation disabled. This release task did not start, stop or modify that process, and did not write to the original project. The runtime-record changes are recorded separately rather than claiming that every original file remained byte-for-byte static.
