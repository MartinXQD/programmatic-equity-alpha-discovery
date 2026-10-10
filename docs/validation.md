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

The distribution wheel was built successfully, extracted outside the source tree, and imported with all three packaged configuration files available. The initial explicit whitelist and Git index contained 63 files. A separate scan compared the released text and PDF contents against all 3,285 recorded private Alpha identifiers and found zero matches; credentials, personal absolute paths and restricted data files were also absent. All 15 PDF pages were rendered and visually inspected.

Original-project preservation was checked against 319,450 file metadata records: no original file was missing and all extracted source hashes remained unchanged. Three runtime records changed while the release was being prepared. Read-only process inspection confirmed an existing `engine.platform_yield_statistics watch` process; its status reported statistics-only operation with browser actions, evaluation and queue mutation disabled. This release task did not start, stop or modify that process, and did not write to the original project. The runtime-record changes are recorded separately rather than claiming that every original file remained byte-for-byte static.

## Upload and link repair: October 9, 2026

The initial GitHub branch contained five overview/dependency files, while all 63 reviewed release files were already committed locally. The original direct push failed for lack of Git credentials; browser upload committed only the five root files. Missing PDF/code targets were therefore a remote upload failure, not incorrect filenames, ignore rules or publication exclusions. The reviewed PDFs remain unchanged.

The whitelist now includes 65 files after adding the link-checking script and four behavioral tests. The checker reads committed Markdown when passed `--ref`, resolves relative paths and exact case, checks directories/images/PDFs/reference links/anchors, and can compare every target against a freshly fetched authenticated remote tree. It reports external URLs separately and never treats anonymous Private-repository HTTP responses as missing files.

The repair suite passed **58 tests in 5.84 seconds**. On the release machine, a filesystem hidden flag caused Python to skip the editable-install `.pth` file; installing the reviewed wheel as a normal package restored subprocess imports and CLI execution. README and CI installation commands now use a normal package install. This is an environment/packaging correction, with no change to numerical research functions. Incidental `.DS_Store` metadata is explicitly excluded from the whitelist audit and remains untracked.

Local link audit: 14 Markdown files, 27 internal link occurrences (21 in the two READMEs), zero local broken targets; all four external official URLs returned HTTP 200. Final authenticated remote counts, commit SHA, push status and target readbacks are recorded separately in the delivery audit after upload.

After the complete upload, authenticated Git and GitHub API readbacks confirmed all 65 files, all internal link targets, and unchanged reviewed PDF bytes. The post-push local suite passed 58 tests in 5.08 seconds, and the synthetic demo passed again.

The first GitHub CI run exposed a portability issue in the source-fingerprint test: [Python 3.13 changed AST dump formatting](https://docs.python.org/3.13/library/ast.html#ast.dump) to omit empty optional lists, while the runner uses Python 3.12. The test now serializes parsed AST fields in the recorded Python 3.13 format on both supported versions. Existing provenance hashes, golden results, source files and historical research outcomes are unchanged. The corrected remote CI result is recorded in the delivery audit.
