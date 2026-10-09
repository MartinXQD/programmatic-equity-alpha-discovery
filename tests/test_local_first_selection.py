"""Hand-derived frozen-rule checks; no actual candidate performance is used."""
from alpha_discovery.local_first_selection import quality_reasons,pareto_order
from alpha_discovery.common import read_json

def good(cid,median,worst,drawdown,gross=1):
    return dict(candidate_id=cid,median_annual_net5_sharpe=median,worst_annual_net5_sharpe=worst,abs_net5_mdd=drawdown,gross_sharpe=gross)

def test_three_target_pareto_layers_and_frozen_tie_breaks():
    ordered=pareto_order([good('D',.5,.2,.3),good('C',1,.5,.1),good('B',2,1,.2),good('A',2,1,.2,2)])
    assert [r['candidate_id'] for r in ordered]==['A','B','C','D']
    assert [r['pareto_layer'] for r in ordered]==[1,1,1,2]
    chain=pareto_order([good('C',1,1,.3),good('B',2,2,.2),good('A',3,3,.1)])
    assert [r['pareto_layer'] for r in chain]==[1,2,3]

def test_no_platform_metrics_or_adaptive_quality_threshold():
    rules=read_json('configs/local_first_protocol.json')['selection']
    m=dict(gross_mean=.01,net5_mean=.001,positive_net5_years=2,ranking_statistics_finite=True,fixed_direction=1)
    for period in rules['coverage_periods']:
        for key,value in [('coverage_good_fraction',.8),('finite_aligned_ic_fraction',.8),('target_defined_fraction',.8),('strict_observability_conditional',.95)]:m[period+'_'+key]=value
    assert quality_reasons(m,rules)==[]
    m['gross_mean']=-.01;m['brain_fitness']=100;m['brain_sharpe']=100
    assert quality_reasons(m,rules)==['gross_mean_NOT_POSITIVE']
    m['full_2019_2024_strict_observability_conditional']=None
    assert 'full_2019_2024:strict_observability_conditional' in quality_reasons(m,rules)
