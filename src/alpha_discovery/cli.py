"""Explicit offline entry points. No BRAIN connector, simulation or submission."""
import argparse, json, os
from pathlib import Path
import numpy as np

def demo(output):
    from .synthetic import make_panel
    from .expressions import parse, Interpreter
    from .local_first_evaluator import DualEvaluator
    from .local_first_selection import quality_reasons
    from .screening import route_b_reasons, quality_row, confirm_pair
    from .signal_first import clean, quality_order, extract_books
    from .common import read_json
    p,raw,accounts,selected,membership=make_panel()
    # Freshly declared teaching formulas; no saved historical candidate registry.
    formulas=['rank(ts_mean(returns,5))','rank(ts_delta(returns,2))','rank(ts_rank(volume,20))',
              'rank(ts_mean(volume,5))','rank(ts_mean(roa,5))','rank(ts_mean(asset_turnover,5))',
              'rank(ts_delta(market_cap,5))','rank(ts_mean(leverage,5))']
    inter=Interpreter(p);ev=DualEvaluator(p);rules=read_json('configs/local_first_protocol.json')['selection']
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    metrics=[];qualified=[];signals={};records={}
    for i,formula in enumerate(formulas,1):
        e=parse(formula);row=dict(candidate_id='SYNTHETIC_DEMO_'+str(i),formula=formula,operators=e.nodes)
        signal=inter.evaluate(e).to_numpy();result,daily=ev.compute(signal,row)
        daily.to_csv(out/(row['candidate_id']+'_daily.csv'),index=False)
        a=quality_reasons(result['selection_metrics'],rules);b=route_b_reasons(result,rules)
        metrics.append(dict(synthetic=True,route_A=not a,route_B=not b,
                            route_A_reasons=a,route_B_reasons=b,**result['selection_metrics']))
        if not a or not b:
            qualified.append(quality_row(row,result));signals[row['candidate_id']]=signal;records[row['candidate_id']]=result
    ordered=quality_order(qualified)
    confirmation=read_json('configs/signal_first.json')['confirmation']
    ix=np.flatnonzero((p.dates>='2019-01-01')&(p.dates<='2023-12-31'))
    retained=[];deferred=[];comparisons=[];books={}
    for row in ordered:
        cid=row['candidate_id'];books[cid]=extract_books(signals[cid],ix,records[cid]['fixed_direction'],p,ev)
        match=None
        for representative in retained:
            result=confirm_pair(books[cid],books[representative['candidate_id']],p.dates[ix].year,row,representative,confirmation)
            comparisons.append(dict(candidate_id=cid,representative_id=representative['candidate_id'],**result))
            if result['status']=='HIGH_SIMILARITY_DEFERRED':match=representative['candidate_id'];break
        if match:deferred.append(dict(candidate_id=cid,representative_id=match))
        else:retained.append(row)
    summary=dict(mode='SYNTHETIC_DEMO',seed=718,generated_data_rows=len(raw),account_rows=len(accounts),selected_rows=len(selected),
                 formulas_evaluated=len(formulas),quality_qualified=len(ordered),retained=len(retained),deferred=len(deferred),
                 platform_evaluation='NOT_RUN',historical_reconstruction='NOT_RUN',market_calendar='SYNTHETIC_WEEKDAYS_NOT_EXCHANGE_HOLIDAYS',
                 interpretation='Synthetic numbers demonstrate code behavior and have no market-performance interpretation.')
    for name,value in [('summary',summary),('metrics',metrics),('local_priority',ordered),('redundancy',dict(deferred=deferred,comparisons=comparisons))]:
        (out/(name+'.json')).write_text(json.dumps(clean(value),indent=2,allow_nan=False)+'\n')
    print(json.dumps(summary,indent=2));return summary

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    d=sub.add_parser('demo');d.add_argument('--output',default='artifacts/demo')
    g=sub.add_parser('generate');g.add_argument('--count',type=int,default=8);g.add_argument('--output',default='artifacts/generated')
    b=sub.add_parser('build-panel');b.add_argument('--data-root',required=True);b.add_argument('--work-dir',required=True)
    e=sub.add_parser('evaluate');e.add_argument('--work-dir',required=True);e.add_argument('--formula',required=True);e.add_argument('--candidate-id',default='LOCAL_USER_EXAMPLE')
    args=parser.parse_args()
    if args.action=='demo':demo(args.output)
    elif args.action=='generate':
        if not 1<=args.count<=20000:parser.error('count must be between 1 and 20000')
        os.environ['ALPHA_WORK_DIR']=str(Path(args.output).resolve())
        from .generator import generate
        print(json.dumps(generate(args.count)))
    elif args.action=='build-panel':
        os.environ['ALPHA_DATA_ROOT']=args.data_root;os.environ['ALPHA_WORK_DIR']=args.work_dir
        from .data import build
        p=build();print(json.dumps(dict(shape=list(p.shape),identity=p.identity,mode='LICENSED_LOCAL_ONLY')))
    elif args.action=='evaluate':
        os.environ['ALPHA_WORK_DIR']=args.work_dir
        from .local_first_evaluator import LocalPanel,FullInterpreter,DualEvaluator
        from .expressions import parse
        from .common import write_json,ROOT
        from .signal_first import clean
        row=dict(candidate_id=args.candidate_id)
        result,daily=DualEvaluator(LocalPanel()).compute(FullInterpreter(LocalPanel()).evaluate(parse(args.formula)).to_numpy(),row)
        write_json('evaluations/'+args.candidate_id+'.json',clean(result))
        daily.to_parquet(ROOT/'evaluations'/f'{args.candidate_id}.parquet',index=False)
        print(json.dumps(clean(result['selection_metrics']),indent=2))

if __name__=='__main__':main()
