"""Seeded bounded generation; no model, arbitrary eval or remote dependency."""
import random,time
from .common import *
from .expressions import *
BASE=['returns','retx','volume','market_cap','book_to_market','earnings_yield','roa','operating_profitability','cashflow_to_assets','asset_turnover','leverage','cash_to_assets']
OPS=['ts_mean','ts_std','ts_delta','ts_rank','ts_delay','ts_min','ts_max']
WIN=[1,2,3,5,10,20,40,60,120,252]

def generate(count=20000,round_id=1,parents=None):
    rng=random.Random(20260929+round_id);seen={};attempts=[];start=time.monotonic()
    def temporal():
        op=rng.choice(OPS);w=rng.choice(WIN if op!='ts_std' else WIN[1:]);return f'{op}({rng.choice(BASE)},{w})'
    while len(seen)<count and len(attempts)<1000000:
        family=rng.choice(['scratch','interaction','condition','relative','mutation','reference'])
        a=temporal();b=temporal();parent=None
        if family=='scratch':s=f'{rng.choice(["rank","zscore","negate"])}({a})'
        elif family=='interaction':s=f'{rng.choice(["add","subtract","multiply"])}(rank({a}),rank({b}))'
        elif family=='condition':s=f'condition(rank({a}),rank({b}),rank(returns))'
        elif family=='relative':s=f'{rng.choice(["group_residual","rank"])}(subtract(rank({a}),rank({b})))'
        elif family=='mutation':
            parent='R1_REFERENCE_REVERSAL_1D';s=f'multiply(rank(ts_mean(returns,{rng.choice(WIN)})),rank({a}))'
        else:
            parent='R1_REFERENCE_VOLUME_SHOCK_20D';s=f'subtract(rank(divide(volume,ts_mean(volume,{rng.choice(WIN[1:])}))),rank({a}))'
        try:
            e=parse(s);unit(e);key=e.render()
            status='STRUCTURAL_DUPLICATE' if key in seen else 'STRUCTURAL_UNIQUE'
            if status=='STRUCTURAL_UNIQUE':seen[key]=dict(candidate_id=e.identity,formula=key,family=family,parent_id=parent,round=round_id,depth=e.depth,operators=e.nodes,fields=sorted(e.fields),lookback=e.lookback,interaction_order=e.interactions,rank_equivalence=rank_equivalence(e),generation_seed=20260929+round_id,status='GENERATED_NOT_EVALUATED',reference_quality='PROJECT_DEFINED_VARIANT' if parent else None)
            attempts.append(dict(attempt=len(attempts)+1,status=status,candidate_id=e.identity,formula=s))
        except ValueError as ex:attempts.append(dict(attempt=len(attempts)+1,status='STRUCTURAL_REJECT',formula=s,reason=str(ex)))
    path=ROOT/'05/results';path.mkdir(parents=True,exist_ok=True)
    with (path/f'attempts_round{round_id}.jsonl').open('w') as f:
        for row in attempts:f.write(json.dumps(row)+'\n')
    write_json(f'05/results/candidates_round{round_id}.json',list(seen.values()))
    summary=dict(round=round_id,raw_attempts=len(attempts),structural_unique=len(seen),structural_duplicates=sum(a['status']=='STRUCTURAL_DUPLICATE' for a in attempts),illegal_attempts=sum(a['status']=='STRUCTURAL_REJECT' for a in attempts),rank_equivalence_unique=len({r['rank_equivalence'] for r in seen.values()}),elapsed_seconds=time.monotonic()-start,registry_sha256=sha(path/f'candidates_round{round_id}.json'),completed_at=now())
    write_json('05/results/generation_summary.json',summary);state(generated_unique=len(seen));return summary
if __name__=='__main__':source_guard();print(generate())
