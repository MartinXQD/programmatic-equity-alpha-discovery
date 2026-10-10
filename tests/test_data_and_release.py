"""Boundary and behavioral tests for publication adapters and released totals."""
from pathlib import Path
import json, subprocess, sys
import numpy as np
import pandas as pd
import pytest
from alpha_discovery.preprocessing import unique_keys, monthly_membership, apply_membership, attach_accounts
from alpha_discovery.synthetic import synthetic_inputs
from alpha_discovery.common import read_json
from alpha_discovery.signal_first import quality_order, extract_books
from alpha_discovery.screening import confirm_pair, route_b_reasons
from alpha_discovery.local_first_evaluator import DualEvaluator

def test_pit_month_end_ranking_and_next_month_activation():
    raw=pd.DataFrame(dict(date=pd.to_datetime(['2018-12-28']*2+['2018-12-31']*2+['2019-01-02']*2),
                         permno=[1,2]*3,dlyclose=[9,8,3,4,1000,1],shrout=[1]*6))
    membership=monthly_membership(raw,1)
    dec=membership[membership.formation_date==pd.Timestamp('2018-12-31')]
    assert dec.permno.tolist()==[2]
    out=apply_membership(raw,membership)
    assert out[out.date==pd.Timestamp('2019-01-02')].permno.tolist()==[2]
    assert (out.formation_date<out.date).all()
    raw.loc[raw.date==pd.Timestamp('2019-01-02'),'dlyclose']=[1,1000000]
    assert monthly_membership(raw,1).iloc[0].permno==2

def test_missing_duplicate_keys_rejected_and_ties_deterministic():
    with pytest.raises(ValueError):unique_keys(pd.DataFrame({'date':[1,1],'permno':[1,1]}),['date','permno'])
    with pytest.raises(ValueError):unique_keys(pd.DataFrame({'date':[1],'permno':[np.nan]}),['date','permno'])
    raw=pd.DataFrame(dict(date=pd.to_datetime(['2018-12-31']*2),permno=[2,1],dlyclose=[5,5],shrout=[1,1]))
    assert monthly_membership(raw,1).permno.tolist()==[1]

def test_accounts_availability_day_staleness_and_missing_debt():
    raw,accounts=synthetic_inputs(stocks=4)
    first=accounts.iloc[[0]].copy();first['datadate']=pd.Timestamp('2018-12-31');first['dlc']=np.nan
    avail=first.datadate.iloc[0]+pd.Timedelta(days=180)
    panel=raw.iloc[:3].copy();panel['gvkey']=first.gvkey.iloc[0];panel['permno']=1
    panel['date']=[avail-pd.Timedelta(days=1),avail,first.datadate.iloc[0]+pd.Timedelta(days=731)]
    out=attach_accounts(panel,first)
    assert pd.isna(out.iloc[0].datadate) and np.isfinite(out.iloc[1].roa)
    assert out.iloc[1].available_date==avail
    assert np.isnan(out.iloc[1].leverage) and np.isnan(out.iloc[2].roa)

def test_qualifying_final_pareto_order_ignores_platform_scores():
    rows=[]
    for cid,s in [('B',1),('A',2),('C',.5)]:
        rows.append(dict(candidate_id=cid,representation_eligible=True,dev_gross_sharpe=s,gross_mean=.01*s,
                         mean_target_turnover=.2,worst_annual_gross_sharpe=s,median_annual_gross_sharpe=s,
                         abs_dev_gross_mdd=.1/s,positive_gross_years=3,nodes=2,brain_sharpe=1000/s))
    a=quality_order(rows)
    assert [x['candidate_id'] for x in a]==['A','B','C']
    assert [x['quality_pareto_layer'] for x in a]==[1,2,3]

def test_generation_deterministic_in_independent_work_directories(tmp_path):
    records=[]
    for i in range(2):
        out=tmp_path/str(i)
        subprocess.run([sys.executable,'-m','alpha_discovery.cli','generate','--count','12','--output',str(out)],check=True,capture_output=True)
        records.append(json.loads((out/'05/results/candidates_round1.json').read_text()))
    assert records[0]==records[1] and len(records[0])==12

def test_final_signal_confirmation_keeps_opposite_and_unknown():
    import types
    rng=np.random.default_rng(18);dates=pd.bdate_range('2018-12-01','2023-12-31');t=len(dates);n=160
    p=types.SimpleNamespace(member=np.ones((t,n),bool),groups=np.tile(np.arange(n)%4,(t,1)))
    ev=object.__new__(DualEvaluator);ev.p=p;ev.policy=read_json('configs/local_first_protocol.json')
    raw=rng.normal(size=(t,n));ix=np.flatnonzero(dates>='2019-01-01')
    a=extract_books(raw,ix,1,p,ev);b=extract_books(raw,ix,-1,p,ev)
    row=dict(local_fitness_estimate=1,worst_annual_gross_sharpe=1,dev_gross_sharpe=1,median_annual_gross_sharpe=1,abs_dev_gross_mdd=.1)
    rules=read_json('configs/signal_first.json')['confirmation']
    assert confirm_pair(a,a,dates[ix].year,row,row,rules)['status']=='HIGH_SIMILARITY_DEFERRED'
    assert confirm_pair(a,b,dates[ix].year,row,row,rules)['status']=='OPPOSITE_EXPOSURE_REVIEW'
    a['score'][:]=np.nan
    assert confirm_pair(a,b,dates[ix].year,row,row,rules)['status']=='PAIR_REVIEW_PENDING'

def test_frozen_aggregate_reconciliation():
    r=Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable,str(r/'scripts/verify_results.py')],check=True,capture_output=True)

def test_synthetic_schema_and_ratios_have_no_real_identifiers():
    raw,accounts=synthetic_inputs(stocks=4)
    assert raw.gvkey.str.startswith('SYNTHETIC_').all()
    assert set(raw.permno)=={1,2,3,4}
    unique_keys(accounts,['gvkey','datadate'])

def test_public_demo_runs_complete_pipeline(tmp_path):
    subprocess.run([sys.executable,'-m','alpha_discovery.cli','demo','--output',str(tmp_path)],check=True,capture_output=True)
    s=json.loads((tmp_path/'summary.json').read_text())
    assert s['mode']=='SYNTHETIC_DEMO' and s['formulas_evaluated']==8
    assert s['platform_evaluation']=='NOT_RUN'
    assert len(list(tmp_path.glob('*_daily.csv')))==8
    assert s['quality_qualified']==s['retained']+s['deferred']

def test_publication_ignore_rules_block_extracts_and_disguised_data():
    root=Path(__file__).resolve().parents[1]
    if not (root/'.git').exists():
        pytest.skip('Git ignore protection is validated from a repository checkout')
    blocked=['data/renamed_notes.md','data/example.json','data/raw/anything.txt',
             'docs/sample.csv','panel.csv.gz','accounts.tsv','dataset.dta',
             'dataset.sas7bdat','cache.feather','panel.hdf5','backup.zip',
             'records.pkl','.pgpass','.netrc','auth.pem','cookies.json','browser_session.json']
    allowed=['data/README.md','data/schema.md','results/pareto_layer_yield.csv']
    for path in blocked+allowed:
        result=subprocess.run(['git','check-ignore','--no-index','-q','--',path],cwd=root)
        assert result.returncode==(0 if path in blocked else 1),path
