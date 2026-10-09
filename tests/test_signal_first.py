"""Guardrails for one-path score extraction and reversible similarity review."""
import types
import numpy as np
import pandas as pd
import pytest
from alpha_discovery import local_first_evaluator as le
from alpha_discovery.signal_first import extract_books,exact_daily,rank_proxy,ranks,weight_distance,retrieve_rank_pages




def fixture(n=160,t=320):
    rng=np.random.default_rng(729)
    p=types.SimpleNamespace(member=np.ones((t,n),bool),groups=np.tile(np.arange(n)%8,(t,1)))
    b=object.__new__(le.DualEvaluator);b.p=p
    b.policy={'numerical':{'group_residual_zero_relative_tolerance':1e-12}}
    return p,b,rng.normal(size=(t,n))


@pytest.mark.parametrize('direction',[-1,1])
def test_actual_capture_proportion_and_restore(direction):
    p,b,raw=fixture();ix=np.arange(10,40);original=le.constrain
    a=extract_books(raw,ix,direction,p,b)
    _,_,_,legacy=b.books_at(raw,ix)
    np.testing.assert_array_equal(a['weights'],legacy['wq'][0]*direction)
    assert le.constrain is original
    denominator=np.nansum(abs(a['score']),axis=1)
    np.testing.assert_allclose(a['weights'],np.nan_to_num(a['score'])/denominator[:,None]*2,atol=1e-12)
    for score,weights in zip(a['score'],a['weights']):
        # IEEE scaling can collapse or separate one-ULP near ties. Proportional
        # weights remain the exact original output; signal is not replaced by weights.
        m=np.isfinite(score);assert exact_daily(score[m],weights[m],100)[0] >= 1-1e-5


def test_undefined_book_is_not_zero():
    p,b,raw=fixture();raw[:]=1
    a=extract_books(raw,np.arange(10,20),1,p,b)
    assert not a['defined'].any()
    assert np.isnan(a['score']).all() and np.isnan(a['weights']).all()


def test_common_support_reranking_and_ties():
    x=np.array([1.,1,2,4,np.nan,6]);y=np.array([2.,2,3,np.nan,5,7])
    assert exact_daily(x,y,3)[0]==pytest.approx(1)
    assert np.isnan(exact_daily(x,y,100)[0])
    assert np.isnan(exact_daily(np.ones(120),np.arange(120.),100)[0])


def test_nonoverlap_unknown_and_negative_not_duplicate():
    x=np.arange(160,dtype=float);y=-x
    assert exact_daily(x,y)[0]==pytest.approx(-1)
    x[80:]=np.nan;y[:80]=np.nan
    assert np.isnan(exact_daily(x,y)[0])


def test_exact_positive_scale_preserves_actual_weights():
    p,b,raw=fixture();ix=np.arange(10,80)
    a=extract_books(raw,ix,1,p,b);c=extract_books(raw*7.5,ix,1,p,b)
    np.testing.assert_allclose(a['weights'],c['weights'],atol=1e-12,rtol=1e-10,equal_nan=True)
    assert np.array_equal(np.isnan(a['score']),np.isnan(c['score']))


def test_monotone_raw_rank_does_not_prove_final_equality():
    p,b,raw=fixture();ix=np.arange(10,80)
    np.testing.assert_array_equal(ranks(raw),ranks(np.exp(raw)))
    a=extract_books(raw,ix,1,p,b);c=extract_books(np.exp(raw),ix,1,p,b)
    assert not np.allclose(a['weights'],c['weights'],equal_nan=True)


def test_fixed_sign_not_daywise_absolute():
    x=np.arange(160,dtype=float)
    rho=np.array([exact_daily(x,x if i%2 else -x)[0] for i in range(20)])
    assert np.median(abs(rho))==pytest.approx(1.)
    assert np.median(rho)==pytest.approx(0.)


def test_normalized_l1_and_off_support_mass():
    a=np.array([1.,-1,0,0]);b=np.array([0,0,1.,-1])
    assert weight_distance(a,b)==pytest.approx(1.)
    assert weight_distance(a,a)==0
    assert np.isnan(weight_distance(a,np.full(4,np.nan)))


def test_no_similarity_transitive_merge():
    rng=np.random.default_rng(42);a=rng.normal(size=2000);c=rng.normal(size=2000);b=a+c
    ab=exact_daily(a,b)[0];bc=exact_daily(b,c)[0];ac=exact_daily(a,c)[0]
    assert ab>.6 and bc>.6 and abs(ac)<.1


def test_all_pages_no_nearest_k_truncation():
    x=np.tile(np.arange(160,dtype=np.float32),(20,1))
    reps=np.tile(x,(300,1,1));proxy,count=retrieve_rank_pages(x,reps,list(range(20)),page_size=17)
    assert len(proxy)==300 and (count==20).all()
    np.testing.assert_allclose(proxy,1.)


def test_low_date_coverage_is_unknown():
    x=np.tile(np.arange(160,dtype=np.float32),(20,1));b=x.copy();b[:10]=np.nan
    proxy,count=retrieve_rank_pages(x,b[None],list(range(20)))
    assert count[0]==10 and np.isnan(proxy[0])


def test_membership_masks_and_pre_history():
    p,b,raw=fixture();p.member[:10,:40]=False;raw[:8]=np.nan
    a=extract_books(raw,np.arange(10,20),1,p,b)
    assert not a['valid'][0,:40].any()
    assert np.isnan(a['weights'][0]).all()
    assert a['defined'][-1]


def test_unit_window_identity_with_missing_support():
    p,b,raw=fixture();raw[12:18,:16]=np.nan
    for operator in ['min','max']:
        simplified=getattr(pd.DataFrame(raw).rolling(1,min_periods=1),operator)().to_numpy()
        np.testing.assert_array_equal(raw,simplified)
        a=extract_books(raw,np.arange(10,80),1,p,b)
        c=extract_books(simplified,np.arange(10,80),1,p,b)
        np.testing.assert_array_equal(a['valid'],c['valid'])
        np.testing.assert_array_equal(a['weights'],c['weights'])


def test_full_continuous_warmup_not_sampled_dates():
    from alpha_discovery.expressions import Interpreter,parse
    p,b,raw=fixture(t=520)
    p.identity='synthetic-full-history'
    p.frame=lambda key:pd.DataFrame(raw)
    expression=parse('ts_mean(returns,252)')
    complete=Interpreter(p).evaluate(expression).to_numpy()
    positions=np.array([280,315,400,500])
    assert np.isfinite(complete[positions]).all()
    sampled=pd.DataFrame(raw[positions]).rolling(252,min_periods=252).mean().to_numpy()
    assert np.isnan(sampled).all()
