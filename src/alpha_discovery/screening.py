"""Final local quality routes and conservative Signal-first confirmation adapters."""
import numpy as np
from .local_first_selection import quality_reasons
from .signal_first import pair_sample, summarize_pair

def route_b_reasons(result, rules):
    metrics=result['selection_metrics'];reasons=[]
    for period in rules['coverage_periods']:
        for measure,key in [('coverage_good_fraction','signal_coverage_days_fraction_min'),('finite_aligned_ic_fraction','trading_aligned_finite_ic_fraction_min'),('target_defined_fraction','target_defined_fraction_min'),('strict_observability_conditional','strict_observability_conditional_min')]:
            v=metrics.get(period+'_'+measure)
            if v is None or not np.isfinite(v) or v<rules[key]:reasons.append(period+':'+measure)
    if result['fixed_direction'] not in [-1,1]:reasons.append('FIXED_DIRECTION_UNDEFINED')
    periods=result['evaluations']['wq']['periods'];gross=periods['development_2022_2024']['gross_fixed']
    annual=[periods[str(y)]['gross_fixed'] for y in [2022,2023,2024]]
    if gross['observable_mean'] is None or gross['observable_mean']<=0:reasons.append('GROSS_MEAN_NOT_POSITIVE')
    if gross['observable_sharpe'] is None or not np.isfinite(gross['observable_sharpe']) or gross['observable_sharpe']<=0:reasons.append('GROSS_SHARPE_NOT_POSITIVE')
    if sum(x['observable_mean'] is not None and x['observable_mean']>0 for x in annual)<2:reasons.append('FEWER_THAN_TWO_POSITIVE_GROSS_YEARS')
    if any(x['observable_sharpe'] is None or not np.isfinite(x['observable_sharpe']) for x in annual) or gross['observable_mdd'] is None:reasons.append('NONFINITE_ANNUAL_OR_DRAWDOWN')
    if any(x['observed_days']<126 for x in annual):reasons.append('ANNUAL_SUPPORT_INSUFFICIENT')
    return reasons

def quality_row(row, result):
    p=result['evaluations']['wq']['periods'];g=p['development_2022_2024']['gross_fixed']
    annual=[p[str(y)]['gross_fixed'] for y in [2022,2023,2024]]
    return {**row,**result['selection_metrics'],'representation_eligible':True,
            'representation_scope':'SYNTHETIC_LOCAL_DEMO_ONLY_NOT_BRAIN_REVIEW',
            'dev_gross_sharpe':g['observable_sharpe'],'gross_mean':g['observable_mean'],
            'mean_target_turnover':p['development_2022_2024']['mean_target_turnover'],
            'worst_annual_gross_sharpe':min(x['observable_sharpe'] for x in annual),
            'median_annual_gross_sharpe':float(np.median([x['observable_sharpe'] for x in annual])),
            'positive_gross_years':sum(x['observable_mean']>0 for x in annual),
            'abs_dev_gross_mdd':abs(g['observable_mdd']),'nodes':row['operators']}

def confirm_pair(a,b,years,row,representative,rules):
    """Apply the frozen full-pair decision thresholds to provided local books.

    The original file-backed orchestration is excluded. The evidence and numeric
    gates follow full_pair in signal_first.py; saved-return diagnostics are optional
    and no unsupported pair is interpreted as an independent signal.
    """
    years=np.asarray(years)
    expected={y:int((years==y).sum()) for y in range(2019,2024)}
    vals=pair_sample(a,b,np.arange(len(years)));s=summarize_pair(vals,years,expected)
    annual_ok=all(v['effective_days']>=rules['min_days_each_year'] and v['expected_days']>0 and v['effective_days']/v['expected_days']>=rules['min_fraction_each_year'] for v in s['annual'].values())
    coords=['local_fitness_estimate','worst_annual_gross_sharpe','dev_gross_sharpe','median_annual_gross_sharpe']
    tradeoff=any(row[k]>representative[k]+1e-10 for k in coords) or row['abs_dev_gross_mdd']<representative['abs_dev_gross_mdd']-1e-10
    support=np.array_equal(a['defined'],b['defined']) and s['common_support_p10'] is not None and s['common_support_p10']>=rules['common_stock_fraction_min']
    coverage_diff=float(np.nanmax(abs(np.isfinite(a['raw']).mean(axis=1)-np.isfinite(b['raw']).mean(axis=1))))
    complete=s['effective_fraction']>=rules['min_full_date_fraction'] and annual_ok and s['effective_days']>=126
    numeric=complete and s['signed_median']>=.97 and s['fraction_ge_090']>=.8 and s['weight_l1_median']<=.05 and s['weight_l1_p90']<=.10 and s['weight_l1_p99']<=.20
    deferred=numeric and support and coverage_diff<=.02 and not tradeoff
    status='HIGH_SIMILARITY_DEFERRED' if deferred else 'SECONDARY_DIVERSITY_REVIEW' if numeric and tradeoff else 'PAIR_REVIEW_PENDING' if not complete else 'OPPOSITE_EXPOSURE_REVIEW' if s['signed_median']<=-.8 else 'NO_HIGH_SIMILARITY_DETECTED'
    return dict(status=status,summary=s,quality_tradeoff=tradeoff,defined_masks_equal=bool(np.array_equal(a['defined'],b['defined'])),coverage_difference_max=coverage_diff)
