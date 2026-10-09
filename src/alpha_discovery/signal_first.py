"""Research functions extracted without numerical changes; see source_provenance.json."""
import math, threading
from unittest.mock import patch
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from . import local_first_evaluator as le
CAPTURE_LOCK=threading.RLock()
PANEL=BOOK=None

def clean(x):
    if isinstance(x, dict): return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [clean(v) for v in x]
    if isinstance(x, np.ndarray): return clean(x.tolist())
    if isinstance(x, (np.integer, np.bool_)): return x.item()
    if isinstance(x, (np.floating, float)): return float(x) if np.isfinite(x) else None
    return x

def extract_books(raw, positions, direction, panel=None, book=None):
    """Capture actual constrain inputs from ONE unchanged books_at invocation.

    The isolated worker is single-threaded; the patch is restored even on failure.
    Both historical books retain their original implementation. Only WQ scores
    and WQ weights are retained; no returns or IC are evaluated.
    """
    p = panel or PANEL; b = book or BOOK
    captured = []
    original = le.constrain
    def capture(score, *args, **kwargs):
        captured.append(score)
        return original(score, *args, **kwargs)
    with CAPTURE_LOCK, patch.object(le, 'constrain', capture):
        _, _, _, books = b.books_at(np.asarray(raw), np.asarray(positions))
    assert le.constrain is original and len(captured) == 2
    weights, audit = books['wq']
    membership = np.asarray(p.member[positions], dtype=bool)
    groups = np.asarray(p.groups[positions])
    score = np.asarray(captured[0]) * direction
    raw_signed = np.where(membership, np.asarray(raw)[positions] * direction, np.nan)
    # An undefined book is never filled with zeros or admitted as an effective score.
    valid = np.isfinite(score) & membership & (groups >= 0) & audit['feasible'][:, None]
    return dict(raw=raw_signed, score=np.where(valid, score, np.nan),
                weights=weights * direction, member=membership,
                valid=valid, defined=np.asarray(audit['feasible']))

def exact_daily(a, b, min_stocks=100):
    """Average-tie Spearman re-ranked on the common finite support."""
    common = np.isfinite(a) & np.isfinite(b)
    n = int(common.sum())
    if n < min_stocks: return np.nan, n
    x = rankdata(a[common], method='average'); y = rankdata(b[common], method='average')
    x -= x.mean(); y -= y.mean()
    den = np.linalg.norm(x) * np.linalg.norm(y)
    return (float(x @ y / den) if den > 0 else np.nan), n

def rank_proxy(a, b, min_stocks=100):
    common = np.isfinite(a) & np.isfinite(b); n = int(common.sum())
    if n < min_stocks: return np.nan, n
    x = a[common].astype(float); y = b[common].astype(float)
    x -= x.mean(); y -= y.mean(); den = np.linalg.norm(x) * np.linalg.norm(y)
    return (float(x @ y / den) if den > 0 else np.nan), n

def ranks(values):
    return pd.DataFrame(values).rank(axis=1, method='average', pct=True).to_numpy(dtype=np.float32)

def weight_distance(a, b):
    if not (np.isfinite(a).all() and np.isfinite(b).all()): return np.nan
    den = np.abs(a).sum() + np.abs(b).sum()
    return float(np.abs(a-b).sum()/den) if den > 0 else np.nan

def quality_order(rows):
    """Local-only, global Pareto layers, followed by declared transparent ties."""
    rows = [dict(q) for q in rows if q['representation_eligible']]
    for q in rows:
        s, m, t = q['dev_gross_sharpe'], q['gross_mean'], q['mean_target_turnover']
        q['local_fitness_estimate'] = s * math.sqrt(abs(m*252)/max(t, .125)) if s > 0 and m > 0 and t >= 0 else None
    columns = ['local_fitness_estimate', 'worst_annual_gross_sharpe',
               'dev_gross_sharpe', 'median_annual_gross_sharpe']
    points = np.array([[q[k] for k in columns] + [-q['abs_dev_gross_mdd']] for q in rows], float)
    # Five quality coordinates; input group and similarity are not ranking inputs.
    remaining = np.arange(len(rows)); layer = 0; ordered = []
    while len(remaining):
        layer += 1; front = []
        for i in remaining:
            v = points[remaining]
            if not np.any(np.all(v >= points[i], axis=1) & np.any(v > points[i], axis=1)): front.append(i)
        assert front
        front.sort(key=lambda i: (-rows[i]['positive_gross_years'], -rows[i]['local_fitness_estimate'],
                                  -rows[i]['worst_annual_gross_sharpe'], -rows[i]['dev_gross_sharpe'],
                                  rows[i]['nodes'], rows[i]['candidate_id']))
        for i in front:
            rows[i]['quality_pareto_layer'] = layer
            rows[i]['local_priority'] = len(ordered)+1
            # All eligible IDs remain in the audit. Platform spending targets the
            # nondominated quality frontier; dominated candidates remain available.
            rows[i]['platform_quality_frontier'] = layer == 1
            ordered.append(rows[i])
        remaining = remaining[~np.isin(remaining, front)]
    return ordered

def pair_sample(a,b,indices):
    rs=[];ns=[];ds=[];raws=[];support=[];outside=[]
    for j in indices:
        rho,n=exact_daily(a['score'][j],b['score'][j]);rs.append(rho);ns.append(n)
        raws.append(exact_daily(a['raw'][j],b['raw'][j])[0])
        ds.append(weight_distance(a['weights'][j],b['weights'][j]))
        common=np.isfinite(a['score'][j])&np.isfinite(b['score'][j])
        union=np.isfinite(a['score'][j])|np.isfinite(b['score'][j])
        support.append(common.sum()/max(1,union.sum()))
        outside.append(float((np.abs(a['weights'][j][~common]).sum()+np.abs(b['weights'][j][~common]).sum())/4)
                       if a['defined'][j] and b['defined'][j] else np.nan)
    return dict(rho=np.asarray(rs),common_stocks=np.asarray(ns),l1=np.asarray(ds),raw_rho=np.asarray(raws),
                common_support=np.asarray(support),outside_common_gross_fraction=np.asarray(outside))

def retrieve_rank_pages(current, representatives, first, min_stocks=100, page_size=128):
    """All retained representatives, paginated; common-support Pearson proxy.

    Full-PIT ranks are calculated before this routine. Missing coordinates stay
    missing. Proxy values only trigger exact re-ranking, never deferral.
    """
    medians=[];counts=[]
    for start in range(0,len(representatives),page_size):
        page=representatives[start:start+page_size]
        day_values=[]
        for j in range(len(first)):
            v=np.asarray(page[:,j],dtype=np.float32)
            x=current[j];valid=np.isfinite(v)&np.isfinite(x)[None,:]
            n=valid.sum(axis=1)
            xv=np.where(valid,x[None,:],0.).astype(np.float64)
            yv=np.where(valid,v,0.).astype(np.float64)
            sx=xv.sum(axis=1);sy=yv.sum(axis=1);safe=np.maximum(n,1)
            covariance=(xv*yv).sum(axis=1)-sx*sy/safe
            xx=(xv*xv).sum(axis=1)-sx*sx/safe;yy=(yv*yv).sum(axis=1)-sy*sy/safe
            denominator=np.sqrt(np.maximum(xx,0)*np.maximum(yy,0))
            corr=np.divide(covariance,denominator,out=np.full(len(v),np.nan),where=(denominator>0)&(n>=min_stocks))
            day_values.append(corr)
        day_values=np.asarray(day_values);finite=np.isfinite(day_values).sum(axis=0)
        with __import__('warnings').catch_warnings():
            __import__('warnings').simplefilter('ignore',RuntimeWarning)
            median=np.nanmedian(day_values,axis=0)
        median[finite<16]=np.nan;medians.extend(median);counts.extend(finite)
    return np.asarray(medians),np.asarray(counts)

def summarize_pair(values,years,expected_by_year):
    rho=values['rho'];valid=np.isfinite(rho);x=rho[valid];d=values['l1'];dv=d[np.isfinite(d)]
    return clean(dict(effective_days=int(valid.sum()),expected_days=len(rho),effective_fraction=float(valid.mean()),
        signed_median=float(np.median(x)) if len(x) else None,abs_median=float(np.median(np.abs(x))) if len(x) else None,
        signed_p10=float(np.quantile(x,.1)) if len(x) else None,signed_p90=float(np.quantile(x,.9)) if len(x) else None,
        positive_fraction=float((x>0).mean()) if len(x) else None,fraction_ge_090=float((x>=.9).mean()) if len(x) else None,
        weight_l1_median=float(np.median(dv)) if len(dv) else None,weight_l1_p90=float(np.quantile(dv,.9)) if len(dv) else None,
        weight_l1_p99=float(np.quantile(dv,.99)) if len(dv) else None,min_common_stocks=int(values['common_stocks'][valid].min()) if valid.any() else None,
        common_support_p10=float(np.nanquantile(values['common_support'][valid],.1)) if valid.any() else None,
        outside_common_gross_p90=float(np.nanquantile(values['outside_common_gross_fraction'],.9)) if np.isfinite(values['outside_common_gross_fraction']).any() else None,
        annual={str(y):dict(effective_days=int((valid&(years==y)).sum()),expected_days=int(expected_by_year[y]),
                    signed_median=float(np.median(rho[valid&(years==y)])) if (valid&(years==y)).any() else None) for y in expected_by_year}))
