"""Research functions extracted without numerical changes; see source_provenance.json."""
import numpy as np

def quality_reasons(metrics,rules):
    reasons=[]
    requirements=[('coverage_good_fraction','signal_coverage_days_fraction_min'),('finite_aligned_ic_fraction','trading_aligned_finite_ic_fraction_min'),('target_defined_fraction','target_defined_fraction_min'),('strict_observability_conditional','strict_observability_conditional_min')]
    for period in rules['coverage_periods']:
        for measure,threshold in requirements:
            value=metrics.get(period+'_'+measure)
            if value is None or not np.isfinite(value) or value<rules[threshold]:reasons.append(period+':'+measure)
    for key in ['gross_mean','net5_mean']:
        if metrics.get(key) is None or not np.isfinite(metrics[key]) or metrics[key]<=0:reasons.append(key+'_NOT_POSITIVE')
    if metrics.get('positive_net5_years',0)<2:reasons.append('FEWER_THAN_TWO_POSITIVE_DEVELOPMENT_YEARS')
    if not metrics.get('ranking_statistics_finite'):reasons.append('NONFINITE_RANKING_STATISTICS')
    if metrics.get('fixed_direction') not in [-1,1]:reasons.append('FIXED_DIRECTION_UNDEFINED')
    return reasons

def pareto_order(records):
    # Lexicographic order ensures every strict dominator precedes its dominated row.
    ordered=sorted(records,key=lambda r:(-r['median_annual_net5_sharpe'],-r['worst_annual_net5_sharpe'],r['abs_net5_mdd'],r['candidate_id']))
    if not ordered:return []
    values=np.asarray([[r['median_annual_net5_sharpe'],r['worst_annual_net5_sharpe'],-r['abs_net5_mdd']] for r in ordered]);levels=np.zeros(len(ordered),int)
    for i in range(1,len(ordered)):
        dominates=np.all(values[:i]>=values[i],axis=1)&np.any(values[:i]>values[i],axis=1)
        if dominates.any():levels[i]=1+int(levels[:i][dominates].max())
    for row,level in zip(ordered,levels):row['pareto_layer']=int(level+1)
    ordered.sort(key=lambda r:(r['pareto_layer'],-r['median_annual_net5_sharpe'],-r['worst_annual_net5_sharpe'],-r['gross_sharpe'],r['abs_net5_mdd'],r['candidate_id']))
    for index,row in enumerate(ordered,1):row['local_priority']=index
    return ordered
