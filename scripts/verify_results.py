"""Reconcile released aggregates; this is not a new platform evaluation."""
from pathlib import Path
import csv,json
r=Path(__file__).resolve().parents[1]
c=json.loads((r/'results/frozen_summary.json').read_text())['counts']
rows=list(csv.DictReader((r/'results/pareto_layer_yield.csv').open()))
assert [int(x['layer']) for x in rows]==list(range(1,41))
for column,key in [('mother','approximately_representable'),('retained','retained'),('deferred','deferred'),('valid_results','valid_platform_results'),('non_correlation_pass','recorded_non_correlation_pass'),('new_results','new_valid_results'),('reused_results','reused_valid_results')]:
    assert sum(int(x[column]) for x in rows)==c[key],column
assert c['regular']+c['degenerate']==20000
assert c['expression_review']+c['not_assessed']==20000
assert c['approximately_representable']+c['implementation_unconfirmed']==10117
assert c['retained']+c['deferred']==3562
assert c['new_valid_results']+c['reused_valid_results']==3285
assert 79+2+1==82
assert all(int(x['retained'])==int(x['valid_results']) for x in rows)
assert max(int(x['layer']) for x in rows if int(x['non_correlation_pass']))==33
print('PASS: completed-cohort counts, 40 layers, new/reused denominators and correlation-state distinctions')
