"""Research functions extracted without numerical changes; see source_provenance.json."""
import numpy as np
import pandas as pd

def demean_groups(a,groups,eligible):
    a=np.asarray(a,dtype=float);valid=np.isfinite(a)&eligible&(groups>=0)
    # Each date/group is an independent bucket. Missing securities never count.
    codes=np.arange(len(a),dtype=np.int64)[:,None]*100+np.clip(groups,0,99)
    c=codes[valid];n=np.bincount(c,minlength=len(a)*100)
    sums=np.bincount(c,weights=a[valid],minlength=len(a)*100)
    # Empty warmup buckets make bincount return integers even with weights.
    mean=np.divide(sums,n,out=np.zeros(len(sums),dtype=float),where=n>0)
    out=np.full(a.shape,np.nan);out[valid]=a[valid]-mean[c]
    out[valid&(n[codes]<2)]=np.nan
    return out

def rank_rows(a):return pd.DataFrame(a).rank(axis=1,method='average',pct=True).to_numpy()

def row_corr(a,b,rank=True):
    valid=np.isfinite(a)&np.isfinite(b)
    a=np.where(valid,a,np.nan);b=np.where(valid,b,np.nan)
    if rank:a=rank_rows(a);b=rank_rows(b)
    count=valid.sum(axis=1)
    am=np.divide(np.nansum(a,axis=1),count,out=np.zeros(len(a)),where=count>0)
    bm=np.divide(np.nansum(b,axis=1),count,out=np.zeros(len(a)),where=count>0)
    da=np.where(valid,a-am[:,None],0);db=np.where(valid,b-bm[:,None],0)
    den=np.sqrt((da*da).sum(axis=1)*(db*db).sum(axis=1))
    return np.divide((da*db).sum(axis=1),den,out=np.full(len(a),np.nan),where=(den>0)&(count>=3))

def delay_decay(signal,delay=1,decay=4):
    s=pd.DataFrame(signal).shift(delay);v=s*0
    for lag in range(decay):v=v+s.shift(lag)*(decay-lag)/(decay*(decay+1)/2)
    return v.to_numpy()

def weights(signal,member,groups,delay=1,decay=4,cap=.08,gross=2.):
    delayed=pd.DataFrame(signal).shift(delay).to_numpy()
    decayed=delay_decay(signal,delay,decay)
    neutral=demean_groups(decayed,groups,member)
    ranked=rank_rows(neutral)
    # Ranking alters group exposure; project again before a single scale factor.
    score=demean_groups(ranked,groups,member)
    denom=np.nansum(np.abs(score),axis=1)
    w=np.divide(np.nan_to_num(score),denom[:,None],out=np.zeros(score.shape),where=denom[:,None]>0)*gross
    # Near-constant scores can amplify roundoff into a directional book. Validate
    # the actual final book; cap feasibility alone cannot establish neutrality.
    codes=np.arange(len(w),dtype=np.int64)[:,None]*100+np.clip(groups,0,99)
    valid_group=groups>=0
    group_totals=np.bincount(codes[valid_group],weights=w[valid_group],minlength=len(w)*100).reshape(len(w),100)
    feasible=(denom>0)&(np.max(np.abs(w),axis=1)<=cap+1e-12)
    feasible &= (np.abs(w.sum(axis=1))<=1e-10)&(np.max(np.abs(group_totals),axis=1)<=1e-10)
    feasible &= np.abs(np.abs(w).sum(axis=1)-gross)<=1e-10
    w[~feasible]=np.nan
    return w,dict(delayed=delayed,decayed=decayed,neutral=neutral,feasible=feasible)

def strict_returns(w,labels):
    held=np.isfinite(w)&(w!=0)
    missing=held&~np.isfinite(labels)
    defined=np.isfinite(w).all(axis=1)
    r=np.sum(np.where(held&np.isfinite(labels),w*labels,0),axis=1)
    r[(missing.sum(axis=1)>0)|~defined]=np.nan
    return r,missing.sum(axis=1)

def target_turnover(w):
    prev=np.vstack([np.zeros((1,w.shape[1])),w[:-1]])
    # Half traded notional with fixed target book; excludes price drift.
    return np.sum(np.abs(w-prev),axis=1)/2

def statistics(r):
    r=np.asarray(r);ok=np.isfinite(r);x=r[ok]
    if len(x)<2:return dict(n=int(len(x)),sharpe=None,mean=None,mdd=None,observability=float(ok.mean()) if len(ok) else 0)
    sd=x.std(ddof=1);nav=np.r_[1.,np.cumprod(1+x)]
    return dict(n=int(len(x)),sharpe=float(x.mean()/sd*np.sqrt(252)) if sd>0 else None,mean=float(x.mean()),mdd=float(np.min(nav/np.maximum.accumulate(nav)-1)),observability=float(ok.mean()),nav_scope='OBSERVABLE_DAYS_CONCATENATED' if not ok.all() else 'COMPLETE_PATH')

def audit_weights(w,groups,cap=.08):
    defined=np.isfinite(w).all(axis=1);v=w[defined];g=groups[defined]
    maxgrp=0.
    for k in np.unique(g):
        if k>=0:maxgrp=max(maxgrp,float(np.max(np.abs(np.where(g==k,v,0).sum(axis=1)),initial=0)))
    return dict(defined_days=int(defined.sum()),infeasible_days=int((~defined).sum()),max_abs_net=float(np.max(np.abs(v.sum(axis=1)),initial=0)),max_gross_error=float(np.max(np.abs(np.abs(v).sum(axis=1)-2),initial=0)),max_single_name=float(np.max(np.abs(v),initial=0)),max_abs_group=maxgrp,cap=cap)
