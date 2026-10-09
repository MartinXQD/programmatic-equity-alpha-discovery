"""Independent numerical examples and source regression for the full-pool path."""
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from alpha_discovery.local_first_evaluator import stable_group_center,constrain,group_totals,strict_book,summarize,ic_summary,fixed_direction,DualEvaluator,FullInterpreter,AuditedCache
from alpha_discovery.evaluator import weights
from alpha_discovery.expressions import parse

class SmallPanel:
    def __init__(self):
        self.dates=pd.bdate_range('2018-12-01','2024-12-31');self.names=np.arange(60)
        rng=np.random.default_rng(321);self.fields={'returns':rng.normal(0,.01,(len(self.dates),60)),'volume':rng.uniform(10,100,(len(self.dates),60))}
        self.member=np.ones(self.fields['returns'].shape,bool);self.groups=np.tile(np.repeat([1,2],30),(len(self.dates),1));self.identity='independent-small-pit'
    def frame(self,k):return pd.DataFrame(self.fields[k],index=self.dates,columns=self.names)
    def labels(self):
        out=np.full(self.member.shape,np.nan);out[:-1]=self.fields['returns'][1:];return out

def test_hand_rank_book_returns_and_cost():
    # Centered ranks 1..60 have absolute mass 900. Gross two gives this exact book.
    scores=(np.arange(1,61)-30.5)[None,:]/60
    w,a=constrain(scores,np.zeros((1,60),int),.08,2,1e-10,1e-12,False)
    expected=2*(np.arange(1,61)-30.5)/900
    np.testing.assert_allclose(w[0],expected)
    returns=np.arange(60)[None,:]/10000
    ret,turn,missing,held=strict_book(w,returns,np.zeros(60))
    np.testing.assert_allclose(ret,[sum(expected*np.arange(60)/10000)])
    np.testing.assert_allclose(turn,[1.]);np.testing.assert_allclose(ret-2*turn*5/10000,ret-.001)
    assert missing.tolist()==[0] and held.tolist()==[60]

def test_constant_and_nearzero_cancellation():
    g=np.tile(np.repeat([1,2],30),(3,1));m=np.ones_like(g,bool)
    for a in [np.ones(g.shape),np.ones(g.shape)+np.tile([0,np.finfo(float).eps],(3,30))]:
        out=stable_group_center(a,g,m,64*np.finfo(float).eps)
        assert np.nanmax(np.abs(out))==0
        w,au=constrain(out,g,.08,2,1e-10,1e-12,True)
        assert not au['feasible'].any() and np.isnan(w).all()

def test_infeasible_cap_and_missing_return():
    scores=np.array([[-1.,1.]]);g=np.zeros_like(scores,int)
    w,a=constrain(scores,g,.08,2,1e-10,1e-12,False);assert np.isnan(w).all()
    w=np.array([[.5,-.5,0.]]);copy=w.copy();ret,_,miss,_=strict_book(w,np.array([[.1,np.nan,.4]]),np.zeros(3))
    assert np.isnan(ret[0]) and miss[0]==1;np.testing.assert_array_equal(w,copy)

def test_initial_nav_and_strict_observable_distinction():
    a=summarize([-.1,.05]);assert abs(a['strict_mdd']+.1)<1e-12
    b=summarize([-.1,np.nan,.05]);assert b['strict_mdd'] is None and abs(b['observable_mdd']+.1)<1e-12 and not b['complete_path']
    ic=ic_summary([.1,.3,np.nan]);assert ic['finite_days']==2 and ic['icir_unannualized']>0

def test_direction_uses_only_training_net_and_symmetric_cost():
    r=np.array([.01,-.002,.01,-100]);t=np.array([1.,2.,1.,3.]);train=np.array([True,True,True,False])
    s,a=fixed_direction(r,t,train);assert s==1
    np.testing.assert_allclose(a['positive_net_mean'],np.mean(r[:3]-.001*t[:3]))
    r[-1]=100;assert fixed_direction(r,t,train)[0]==s
    assert fixed_direction(np.zeros(4),t,train)[0]==0

def test_source_weight_regression_and_direction_reversal():
    p=SmallPanel();signal=p.fields['volume']
    w,_=weights(signal,p.member,p.groups)
    neg,_=weights(-signal,p.member,p.groups)
    np.testing.assert_allclose(neg,-w,rtol=1e-10,atol=1e-12,equal_nan=True)
    ev=DualEvaluator(p,block_days=37);result,daily,books=ev.compute(signal,{'candidate_id':'TEST'},retain_weights=True)
    raw=books['wq']/result['fixed_direction']
    np.testing.assert_allclose(raw,w[ev.positions],rtol=1e-10,atol=1e-12,equal_nan=True)
    # Same raw labels and book reconstruct the saved continuous gross path.
    labels=p.labels()[ev.positions];expected=np.sum(np.where(np.isfinite(raw)&np.isfinite(labels),raw*labels,0),axis=1)
    expected[~np.isfinite(raw).all(axis=1)|~ev.ii]=np.nan
    np.testing.assert_allclose(daily.wq_gross_unsigned,expected,equal_nan=True)

def test_block_boundaries_warmup_and_future_perturbation():
    p=SmallPanel();signal=p.fields['volume'].copy();ev=DualEvaluator(p,37)
    r,d,w=ev.compute(signal,{'candidate_id':'TEST'},True);r2,d2,w2=DualEvaluator(p,113).compute(signal,{'candidate_id':'TEST'},True)
    pd.testing.assert_frame_equal(d,d2,check_exact=False,atol=1e-12,rtol=1e-10)
    assert d.loc[d.date==pd.Timestamp('2022-01-03'),'wq_target_defined'].iloc[0]==1
    cutoff=np.searchsorted(p.dates.to_numpy(),np.datetime64('2023-01-01'));changed=signal.copy();changed[cutoff:]*=13
    rc,dc,wc=ev.compute(changed,{'candidate_id':'TEST'},True)
    for book in ['wq','transparent']:np.testing.assert_allclose(w[book][d.date<'2023-01-01'],wc[book][d.date<'2023-01-01'],equal_nan=True,atol=1e-12)
    assert r['fixed_direction']==rc['fixed_direction']
    # Yearly labels ending in the next calendar year are purged.
    for y in range(2019,2025):
        assert r['evaluations']['wq']['periods'][str(y)]['target_expected_days']==int(((d.date.dt.year==y)&(d.return_end<=pd.Timestamp(f'{y}-12-31'))&d.registered_endpoint_valid).sum())

def test_cache_parallel_equal_and_full_calendar_gap():
    p=SmallPanel();p.fields['returns'][100,0]=np.nan
    expressions=[parse('rank(ts_mean(returns,5))'),parse('ts_rank(volume,20)')]
    serial=[FullInterpreter(p).evaluate(e) for e in expressions];cache=AuditedCache(10*1024**2)
    inter=FullInterpreter(p,cache);cached=[inter.evaluate(e) for e in expressions]
    again=[inter.evaluate(e) for e in expressions];assert cache.hits>=2
    with ThreadPoolExecutor(2) as pool:parallel=list(pool.map(lambda e:FullInterpreter(p).evaluate(e),expressions))
    for a,b,c,e in zip(serial,cached,again,parallel):
        pd.testing.assert_frame_equal(a,b);pd.testing.assert_frame_equal(a,c);pd.testing.assert_frame_equal(a,e)
    result=FullInterpreter(p).evaluate(parse('ts_mean(returns,5)'))
    assert result.iloc[104,0]!=result.iloc[104,0] and np.isfinite(result.iloc[105,0])


def test_empty_fundamental_warmup_bucket_remains_undefined():
    from alpha_discovery.evaluator import demean_groups
    a=np.full((2,60),np.nan);g=np.ones((2,60),int);m=np.ones((2,60),bool)
    assert np.isnan(demean_groups(a,g,m)).all()
    assert np.isnan(stable_group_center(a,g,m,64*np.finfo(float).eps)).all()
    p=SmallPanel();p.fields['volume'][:20]=np.nan
    result,daily=DualEvaluator(p).compute(p.fields['volume'],{'candidate_id':'TEST'})
    assert result['two_evaluators_complete'] and len(daily)>1500

def parallel_full_book_example(seed):
    p=SmallPanel();signal=p.fields['volume']*seed
    return DualEvaluator(p,37).compute(signal,{'candidate_id':'PROCESS_TEST'})

def test_actual_process_full_dual_evaluation_equals_serial():
    from concurrent.futures import ProcessPoolExecutor
    import multiprocessing
    serial=parallel_full_book_example(1)
    with ProcessPoolExecutor(2,mp_context=multiprocessing.get_context('spawn')) as pool:
        values=list(pool.map(parallel_full_book_example,[1,1]))
    for result,daily in values:
        assert result==serial[0]
        pd.testing.assert_frame_equal(daily,serial[1],check_exact=True)
