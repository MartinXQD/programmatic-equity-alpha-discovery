"""Streaming full-calendar dual evaluation for the immutable primary 20,000 pool."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
from .common import ROOT,read_json,digest,sha
from .evaluator import demean_groups,rank_rows,row_corr
from .expressions import Interpreter,Cache

RUN='LOCAL_FIRST_FULL20K_V1'

class LazyFields(dict):
    def __missing__(self,key):
        path=ROOT/f'data/panel/{key}.npy'
        if not path.exists():raise KeyError('Unavailable source field: '+key)
        value=np.load(path,mmap_mode='r');self[key]=value;return value

class LocalPanel:
    def __init__(self):
        meta=read_json('data/panel/identity.json');self.identity=meta['identity']
        self.dates=pd.DatetimeIndex(meta['dates']);self.names=np.asarray(meta['names'])
        self.member=np.load(ROOT/'data/panel/member.npy',mmap_mode='r')
        self.groups=np.load(ROOT/'data/panel/groups.npy',mmap_mode='r')
        self.fields=LazyFields();self.shape=self.member.shape
    def frame(self,key):return pd.DataFrame(self.fields[key],index=self.dates,columns=self.names,copy=False)
    def labels(self):
        ret=self.fields['returns'];out=np.full(ret.shape,np.nan);out[:-1]=ret[1:];return out

class AuditedCache(Cache):
    def __init__(self,max_bytes):super().__init__(max_bytes);self.hits=0;self.misses=0
    def __getitem__(self,key):
        value=super().__getitem__(key);self.move_to_end(key);return value

class FullInterpreter(Interpreter):
    def __init__(self,panel,cache=None):
        super().__init__(panel,cache)
        policy=read_json('configs/local_first_protocol.json')
        self.context=digest(dict(data=panel.identity,operator_sha256=sha(Path(__file__).with_name('expressions.py')),evaluation_policy=digest(policy),universe='Frozen audited full PIT members',direction_policy=policy['direction'],numeric='float64'))
    def evaluate(self,e):
        if self.cache is not None:
            if (self.context,e.render()) in self.cache:self.cache.hits+=1
            else:self.cache.misses+=1
        return super().evaluate(e)


def group_totals(values,groups):
    codes=np.arange(len(values),dtype=np.int64)[:,None]*100+np.clip(groups,0,99)
    valid=(groups>=0)&np.isfinite(values)
    return np.bincount(codes[valid],weights=values[valid],minlength=len(values)*100).reshape(len(values),100)


def stable_group_center(values,groups,member,relative_tolerance):
    out=demean_groups(values,groups,member)
    codes=np.arange(len(values),dtype=np.int64)[:,None]*100+np.clip(groups,0,99)
    valid=np.isfinite(values)&member&(groups>=0)
    amplitude=np.zeros(len(values)*100)
    np.maximum.at(amplitude,codes[valid],np.abs(values[valid]))
    threshold=relative_tolerance*amplitude[codes]
    out[np.isfinite(out)&(np.abs(out)<=threshold)]=0.
    return out


def constrain(score,groups,cap,gross,tolerance,cap_tolerance,industry):
    denom=np.nansum(np.abs(score),axis=1)
    w=np.divide(np.nan_to_num(score),denom[:,None],out=np.zeros(score.shape),where=denom[:,None]>0)*gross
    net=w.sum(axis=1);g=np.abs(w).sum(axis=1);single=np.max(np.abs(w),axis=1)
    industry_max=np.max(np.abs(group_totals(w,groups)),axis=1)
    feasible=(denom>0)&(np.abs(net)<=tolerance)&(np.abs(g-gross)<=tolerance)&(single<=cap+cap_tolerance)
    if industry:feasible &= industry_max<=tolerance
    w[~feasible]=np.nan
    return w,dict(feasible=feasible,net=np.where(feasible,net,np.nan),gross=np.where(feasible,g,np.nan),single=np.where(feasible,single,np.nan),group_max=np.where(feasible,industry_max,np.nan))


def strict_book(w,labels,prev):
    held=np.isfinite(w)&(w!=0);defined=np.isfinite(w).all(axis=1)
    missing=(held&~np.isfinite(labels)).sum(axis=1)
    ret=np.sum(np.where(held&np.isfinite(labels),w*labels,0),axis=1)
    ret[(missing>0)|~defined]=np.nan
    previous=np.vstack([prev,w[:-1]])
    turnover=np.sum(np.abs(w-previous),axis=1)/2
    return ret,turnover,missing,held.sum(axis=1)


def summarize(values):
    a=np.asarray(values,dtype=float);valid=np.isfinite(a);x=a[valid];n=len(a)
    output=dict(expected_days=n,observed_days=int(len(x)),observability=float(valid.mean()) if n else None,complete_path=bool(n and valid.all()),observable_mean=None,observable_sharpe=None,observable_mdd=None,strict_mean=None,strict_sharpe=None,strict_mdd=None,strict_total_return=None,nav_scope='COMPLETE_PATH' if n and valid.all() else 'OBSERVABLE_DAYS_CONCATENATED_CONDITIONAL_DIAGNOSTIC')
    if len(x)>=2:
        sd=x.std(ddof=1);nav=np.r_[1.,np.cumprod(1+x)]
        output.update(observable_mean=float(x.mean()),observable_sharpe=float(x.mean()/sd*np.sqrt(252)) if sd>0 else None,observable_mdd=float(np.min(nav/np.maximum.accumulate(nav)-1)))
        if output['complete_path']:
            output.update(strict_mean=output['observable_mean'],strict_sharpe=output['observable_sharpe'],strict_mdd=output['observable_mdd'],strict_total_return=float(nav[-1]-1))
    return output


def ic_summary(values):
    a=np.asarray(values);x=a[np.isfinite(a)];sd=x.std(ddof=1) if len(x)>=2 else np.nan
    return dict(expected_days=len(a),finite_days=len(x),finite_fraction=float(len(x)/len(a)) if len(a) else None,mean=float(x.mean()) if len(x) else None,std=float(sd) if np.isfinite(sd) else None,icir_unannualized=float(x.mean()/sd) if np.isfinite(sd) and sd>0 else None,positive_day_fraction=float((x>0).mean()) if len(x) else None)


def fixed_direction(gross,turnover,train_mask,bps=5,fixed_source=None):
    valid=train_mask&np.isfinite(gross)&np.isfinite(turnover)
    x=gross[valid];cost=2*turnover[valid]*bps/10000
    if fixed_source in [-1,1]:sign=int(fixed_source);origin='EXPLICIT_ORIGINAL_FIXED_DIRECTION'
    elif len(x)<2:sign=0;origin='NO_RELIABLE_TRAIN_STATISTIC'
    else:
        difference=float(2*x.mean());tol=64*np.finfo(float).eps*float(np.mean(np.abs(x)))
        sign=int(np.sign(difference)) if abs(difference)>tol else 0;origin='2019_2021_LOCAL_WQ_NET_MEAN' if sign else 'TRAIN_DIRECTIONS_TIED'
    return sign,dict(source=origin,train_end='2021-12-31',valid_train_days=int(len(x)),positive_net_mean=float(np.mean(x-cost)) if len(x) else None,negative_net_mean=float(np.mean(-x-cost)) if len(x) else None,cost_bps=bps,directions_compared=1 if fixed_source in [-1,1] else 2,symmetry='Both signs derived from identical unsigned holdings and symmetric target turnover; engineering test checks actual sign reversal')


class DualEvaluator:
    def __init__(self,panel,block_days=128):
        self.p=panel;self.policy=read_json('configs/local_first_protocol.json');self.block_days=block_days
        self.labels=panel.labels();self.dates=panel.dates
        self.ends=pd.DatetimeIndex(pd.Series(self.dates).shift(-1))
        self.start=int(np.searchsorted(self.dates.to_numpy(),np.datetime64('2019-01-01')))
        self.stop=int(np.searchsorted(self.dates.to_numpy(),np.datetime64('2025-01-01')))
        self.positions=np.arange(self.start,self.stop)
        self.ii=(self.dates[self.positions]<='2024-12-31')&(self.ends[self.positions]<='2024-12-31')
    def books_at(self,a,ix):
        p=self.p;num=self.policy['numerical'];mem=np.asarray(p.member[ix]);groups=np.asarray(p.groups[ix])
        delayed=np.where(p.member[ix-1],a[ix-1],np.nan)
        decayed=delayed*0
        for lag in [1,2,3,4]:decayed=decayed+np.where(p.member[ix-lag],a[ix-lag],np.nan)*(5-lag)/10
        neutral=stable_group_center(decayed,groups,mem,num['group_residual_zero_relative_tolerance'])
        score=stable_group_center(rank_rows(neutral),groups,mem,num['group_residual_zero_relative_tolerance'])
        wq,wa=constrain(score,groups,.08,2.,1e-10,1e-12,True)
        baseline=rank_rows(np.where(mem,delayed,np.nan));valid=np.isfinite(baseline);count=valid.sum(axis=1)
        mean=np.divide(np.nansum(baseline,axis=1),count,out=np.zeros(len(baseline)),where=count>0)
        base_score=baseline-mean[:,None];base_score[np.isfinite(base_score)&(np.abs(base_score)<=num['group_residual_zero_relative_tolerance'])]=0
        tb,ta=constrain(base_score,groups,.08,2.,1e-10,1e-12,False)
        return delayed,decayed,neutral,{'transparent':(tb,ta),'wq':(wq,wa)}
    def compute(self,signal,row,retain_weights=False):
        a=np.asarray(signal,dtype=float);p=self.p;pol=self.policy;num=pol['numerical'];n=self.stop-self.start
        columns={k:np.full(n,np.nan) for k in ['coverage','raw_ic','aligned_ic','decayed_ic','neutral_ic']}
        for book in ['transparent','wq']:
            for k in ['gross_unsigned','turnover','missing_held','hold_count','net_exposure','gross_exposure','max_single','max_group','target_defined']:
                columns[book+'_'+k]=np.full(n,np.nan)
        # The preceding warmup target book supplies first-period turnover.
        *_,warmup=self.books_at(a,np.array([self.start-1]))
        previous={book:warmup[book][0][-1].copy() for book in ['transparent','wq']}
        all_weights={book:[] for book in ['transparent','wq']} if retain_weights else None
        for start in range(self.start,self.stop,self.block_days):
            end=min(start+self.block_days,self.stop);ix=np.arange(start,end);destination=slice(start-self.start,end-self.start)
            mem=np.asarray(p.member[start:end]);groups=np.asarray(p.groups[start:end]);raw=np.where(mem,a[start:end],np.nan)
            delayed,decayed,neutral,books=self.books_at(a,ix)
            labels=self.labels[start:end]
            columns['coverage'][destination]=np.divide(np.isfinite(raw).sum(axis=1),mem.sum(axis=1),out=np.zeros(len(mem),float),where=mem.sum(axis=1)>0)
            for key,values in [('raw_ic',raw),('aligned_ic',np.where(mem,delayed,np.nan)),('decayed_ic',np.where(mem,decayed,np.nan)),('neutral_ic',neutral)]:columns[key][destination]=row_corr(values,labels)
            for book,(w,audit) in books.items():
                ret,turn,missing,held=strict_book(w,labels,previous[book]);previous[book]=w[-1].copy()
                values=dict(gross_unsigned=ret,turnover=turn,missing_held=missing,hold_count=held,net_exposure=audit['net'],gross_exposure=audit['gross'],max_single=audit['single'],max_group=audit['group_max'],target_defined=audit['feasible'].astype(float))
                for key,value in values.items():columns[book+'_'+key][destination]=value
                if retain_weights:all_weights[book].append(w)
        # Signal and IC evidence at the terminal position is retained; no outside-period P&L.
        for book in ['transparent','wq']:columns[book+'_gross_unsigned'][~self.ii]=np.nan
        date=self.dates[self.positions];ends=self.ends[self.positions]
        masks={'full_2019_2024':self.ii,'common_2019_2023':self.ii&(ends<='2023-12-31'),'train_2019_2021':self.ii&(ends<='2021-12-31'),'development_2022_2024':self.ii&(date>='2022-01-01')}
        for year in range(2019,2025):masks[str(year)]=self.ii&(date.year==year)&(ends<=f'{year}-12-31')
        sign,direction_info=fixed_direction(columns['wq_gross_unsigned'],columns['wq_turnover'],masks['train_2019_2021'],5,row.get('fixed_direction'))
        fold_directions=[]
        for year in [2022,2023,2024]:
            training=self.ii&(ends<=f'{year-1}-12-31')
            s,info=fixed_direction(columns['wq_gross_unsigned'],columns['wq_turnover'],training,5)
            fold_directions.append(dict(year=year,train_end=f'{year-1}-12-31',direction=s,valid_train_days=info['valid_train_days'],purpose='DYNAMIC_DIAGNOSTIC_ONLY'))
        evaluations={}
        for book in ['transparent','wq']:
            unsigned=columns[book+'_gross_unsigned'];signed=sign*unsigned if sign else np.full(n,np.nan)
            columns[book+'_gross_fixed']=signed
            for bps in [0,5,10]:columns[book+f'_net{bps}_fixed']=signed-2*columns[book+'_turnover']*bps/10000
            wf=np.full(n,np.nan)
            for fold in fold_directions:
                mask=masks[str(fold['year'])]
                if fold['direction']:wf[mask]=fold['direction']*unsigned[mask]-.001*columns[book+'_turnover'][mask]
            columns[book+'_dynamic_net5_diagnostic']=wf
            periods={}
            for name,mask in masks.items():
                defined=columns[book+'_target_defined'][mask]==1;obs=np.isfinite(unsigned[mask]);total=int(mask.sum())
                periods[name]=dict(gross_unsigned=summarize(unsigned[mask]),gross_fixed=summarize(signed[mask]),cost={str(bps):summarize(columns[book+f'_net{bps}_fixed'][mask]) for bps in [0,5,10]},target_defined_days=int(defined.sum()),target_expected_days=total,target_defined_fraction=float(defined.mean()) if total else None,strict_observed_days=int(obs.sum()),strict_observability_conditional=float(obs.sum()/defined.sum()) if defined.sum() else None,strict_observability_unconditional=float(obs.mean()) if total else None,mean_target_turnover=float(np.nanmean(columns[book+'_turnover'][mask])) if np.isfinite(columns[book+'_turnover'][mask]).any() else None)
            full=masks['full_2019_2024'];defined=columns[book+'_target_defined'][full]==1
            audit={key:float(np.nanmax(np.abs(columns[book+'_'+key][full]))) if defined.any() else None for key in ['net_exposure','max_single','max_group']}
            audit['max_gross_error']=float(np.nanmax(np.abs(columns[book+'_gross_exposure'][full]-2))) if defined.any() else None
            audit.update(defined_days=int(defined.sum()),expected_days=int(full.sum()),constraint='Net and gross and cap; SIC2 final neutrality additionally for WQ',cap=.08)
            assert not defined.any() or (audit['net_exposure']<=1e-10 and audit['max_gross_error']<=1e-10 and audit['max_single']<=.08+1e-12 and (book=='transparent' or audit['max_group']<=1e-10))
            evaluations[book]=dict(periods=periods,weight_audit=audit,dynamic_walkforward_diagnostic=summarize(wf[masks['development_2022_2024']]))
        ic={name:{key:ic_summary(columns[key][mask]) for key in ['raw_ic','aligned_ic','decayed_ic','neutral_ic']} for name,mask in masks.items()}
        sufficient={name:dict(coverage_good_days=int((columns['coverage'][mask]>=.5).sum()),coverage_expected_days=int(mask.sum()),coverage_good_fraction=float((columns['coverage'][mask]>=.5).mean()) if mask.any() else None,finite_aligned_ic_fraction=ic[name]['aligned_ic']['finite_fraction'],target_defined_fraction=evaluations['wq']['periods'][name]['target_defined_fraction'],strict_observability_conditional=evaluations['wq']['periods'][name]['strict_observability_conditional']) for name,mask in masks.items()}
        dev=evaluations['wq']['periods']['development_2022_2024'];annual=[evaluations['wq']['periods'][str(y)]['cost']['5'] for y in [2022,2023,2024]]
        sharpes=[v['observable_sharpe'] for v in annual];finite=all(v is not None and np.isfinite(v) for v in sharpes)
        selection=dict(candidate_id=row['candidate_id'],fixed_direction=sign,gross_mean=dev['gross_fixed']['observable_mean'],net5_mean=dev['cost']['5']['observable_mean'],gross_sharpe=dev['gross_fixed']['observable_sharpe'],median_annual_net5_sharpe=float(np.median(sharpes)) if finite else None,worst_annual_net5_sharpe=float(min(sharpes)) if finite else None,abs_net5_mdd=abs(dev['cost']['5']['observable_mdd']) if dev['cost']['5']['observable_mdd'] is not None else None,positive_net5_years=sum(v['observable_mean'] is not None and v['observable_mean']>0 for v in annual),ranking_statistics_finite=finite and all(v is not None and np.isfinite(v) for v in [dev['gross_fixed']['observable_sharpe'],dev['cost']['5']['observable_mdd']]))
        for name,v in sufficient.items():
            for k,value in v.items():selection[name+'_'+k]=value
        daily=pd.DataFrame({'date':date,'return_end':ends,'registered_endpoint_valid':self.ii,**columns})
        status='DEGENERATE_NO_DEFINED_PORTFOLIO' if not (columns['wq_target_defined'][self.ii]==1).any() else 'FULL_EVALUATED_NEW'
        result=dict(computation_status=status,complete_calendar_evaluation=True,two_evaluators_complete=True,fixed_direction=sign,direction=direction_info,dynamic_fold_directions=fold_directions,evaluations=evaluations,ic=ic,data_sufficiency=sufficient,selection_metrics=selection,registered_days=int(self.ii.sum()),daily_rows=len(daily),signal_coverage_overall=float(np.isfinite(a[self.positions][p.member[self.positions]]).mean()),no_platform_outcome_inputs=True)
        if retain_weights:return result,daily,{book:np.concatenate(parts)*sign for book,parts in all_weights.items()}
        return result,daily
