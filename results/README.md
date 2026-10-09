# Saved research aggregates

`frozen_summary.json` records candidate flow, snapshot, periods, final experiment versions, source hashes and interpretation. `pareto_layer_yield.csv` records all 40 completed layers, with retained/valid/new/reused and non-correlation-pass counts. These are author-created aggregate selections from saved evidence, not a new BRAIN run or independently reproduced historical experiment.

Run `python scripts/verify_results.py` to check totals, layer coverage and accounting identities. Demo outputs go to ignored `artifacts/` and are never mixed with historical results. The two figures in `docs/assets/` are rendered from the released aggregates. Rates use summed passes divided by summed valid results, including matching historical reuse.
