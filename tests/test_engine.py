import numpy as np
import pandas as pd
import pytest
from concurrent.futures import ThreadPoolExecutor
from alpha_discovery.expressions import Expr,parse,unit,Interpreter,Cache,rank_equivalence
from alpha_discovery.evaluator import weights,strict_returns,target_turnover,statistics,row_corr,delay_decay,audit_weights

class Tiny:
    def __init__(self,a):
        self.fields={'returns':np.asarray(a,dtype=float),'volume':np.asarray(a,dtype=float)+10};self.member=np.ones_like(a,dtype=bool)
        self.groups=np.zeros_like(a,dtype=int);self.identity='tiny';self.dates=pd.date_range('2020-01-01',periods=len(a));self.names=np.arange(len(a[0]))
    def frame(self,k):return pd.DataFrame(self.fields[k],index=self.dates,columns=self.names)

def test_explicit_decay():
    got=delay_decay(np.array([[1.],[2.],[4.],[8.]]),1,2).ravel()
    np.testing.assert_allclose(got,[np.nan,np.nan,5/3,10/3],equal_nan=True)
def test_exact_missing_return_no_reallocation():
    w=np.array([[.5,-.5,0],[.5,-.5,0]])
    r,n=strict_returns(w,np.array([[.1,.2,np.nan],[.1,np.nan,.5]]))
    assert r[0]==pytest.approx(-.05) and np.isnan(r[1]) and n.tolist()==[0,1]
    np.testing.assert_array_equal(w,[[.5,-.5,0],[.5,-.5,0]])
def test_initial_nav_drawdown():assert statistics([-.1,.05])['mdd']==pytest.approx(-.1)
def test_target_turnover_hand():np.testing.assert_allclose(target_turnover(np.array([[.5,-.5],[-.5,.5]])),[.5,1])
def test_future_mutation_causality():
    a=np.arange(120,dtype=float).reshape(20,6)/100
    p=Tiny(a);q=Tiny(a.copy());q.fields['returns'][12:]*=100
    expr=parse('rank(ts_mean(returns,5))')
    np.testing.assert_allclose(Interpreter(p).evaluate(expr).iloc[:12],Interpreter(q).evaluate(expr).iloc[:12],equal_nan=True)
def test_operator_hand_mean_and_ranking():
    p=Tiny([[1,2,4],[2,2,1],[3,1,7]])
    got=Interpreter(p).evaluate(parse('rank(ts_mean(returns,2))')).to_numpy()
    np.testing.assert_allclose(got[1],[1/3,2/3,1]);np.testing.assert_allclose(got[2],[2/3,1/3,1])
def test_full_calendar_gap():
    p=Tiny([[1,2],[np.nan,3],[5,4],[6,5]])
    got=Interpreter(p).evaluate(parse('ts_mean(returns,2)')).to_numpy()
    assert np.isnan(got[2,0]);assert got[3,0]==5.5
def test_cache_and_parallel_independent_calls():
    p=Tiny(np.arange(240).reshape(40,6));es=[parse('rank(ts_mean(returns,5))'),parse('ts_delta(returns,2)')]
    serial=[Interpreter(p).evaluate(e) for e in es]
    cache=Cache(100000);cached=[Interpreter(p,cache).evaluate(e) for e in es]
    with ThreadPoolExecutor(2) as pool:parallel=list(pool.map(lambda e:Interpreter(p).evaluate(e),es))
    for a,b,c in zip(serial,cached,parallel):
        pd.testing.assert_frame_equal(a,b);pd.testing.assert_frame_equal(a,c)
def test_domain_and_structural_rules():
    for s in ['__import__("os")','ts_std(returns,1)','ts_mean(returns,4)','returns.__class__','eval(returns)']:
        with pytest.raises(ValueError):parse(s)
    with pytest.raises(ValueError):unit(parse('add(volume,returns)'))
    assert parse('add(returns,volume)').render()==parse('add(volume,returns)').render()
    assert rank_equivalence(parse('rank(ts_sum(returns,5))'))==rank_equivalence(parse('rank(ts_mean(returns,5))'))
def test_zero_division_and_ties():
    p=Tiny([[0,0,2],[1,1,1]])
    assert Interpreter(p).evaluate(parse('divide(returns,returns)')).iloc[0,:2].isna().all()
    np.testing.assert_allclose(Interpreter(p).evaluate(parse('rank(returns)')).iloc[1],[2/3]*3)
def test_final_weight_group_neutrality():
    a=np.tile(np.arange(60),(6,1));member=np.ones_like(a,dtype=bool);g=np.tile(np.repeat([1,2],30),(6,1))
    w,_=weights(a,member,g,delay=1,decay=1,cap=.08)
    audit=audit_weights(w,g)
    assert audit['defined_days']==5
    assert audit['max_abs_net']<1e-12 and audit['max_abs_group']<1e-12 and audit['max_gross_error']<1e-12 and audit['max_single_name']<=.08
    # Independently derive ranks 1..30 centered within each group.
    centered=np.tile(np.arange(1,31)-15.5,2);expected=centered/np.abs(centered).sum()*2
    np.testing.assert_allclose(w[-1],expected)
def test_cap_infeasible_not_silently_renormalized():
    w,_=weights(np.tile([1.,2.],(4,1)),np.ones((4,2),bool),np.zeros((4,2),int),delay=0,decay=1,cap=.08)
    assert np.isnan(w).all()
def test_labels_boundary_and_future_membership():
    from alpha_discovery.data import Panel
    p=object.__new__(Panel);p.fields={'returns':np.array([[.1,.2],[.3,np.nan],[.5,.6]])}
    labels=p.labels();np.testing.assert_allclose(labels,[[.3,np.nan],[.5,.6],[np.nan,np.nan]],equal_nan=True)
    # Forward membership never enters Panel.labels; raw security is retained.
def test_spearman_hand():assert row_corr(np.array([[2,1,3.]]),np.array([[1,2,3.]]))[0]==pytest.approx(.5)

def test_full_weight_future_independence():
    rng=np.random.default_rng(123);a=rng.normal(size=(30,100));b=a.copy();b[20:]*=20
    member=np.ones(a.shape,bool);groups=np.zeros(a.shape,int)
    wa,_=weights(a,member,groups);wb,_=weights(b,member,groups)
    np.testing.assert_allclose(wa[:20],wb[:20],equal_nan=True)



def test_constant_rank_roundoff_cannot_create_directional_book():
    # A constant 60-name vector has mathematically zero centered rank.
    # Repeated floating-point accumulation previously normalized tiny residuals
    # into equal positive 1/30 weights: cap passed while net exposure equaled 2.
    signal=np.ones((6,60));member=np.ones_like(signal,dtype=bool)
    groups=np.zeros_like(signal,dtype=int)
    w,layers=weights(signal,member,groups,delay=0,decay=1)
    assert not layers['feasible'].any() and np.isnan(w).all()
    r,_=strict_returns(w,np.full_like(w,.01))
    assert np.isnan(r).all()
