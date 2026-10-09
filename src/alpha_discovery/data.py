"""Read-only CRSP/PIT layer on a complete observed market calendar."""
import gc, json
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from .common import ROOT,R1,DATA,sha,digest,write_json,read_json,now
FIELDS=['returns','retx','volume','close','market_cap','book_to_market','earnings_yield','cashflow_yield','roa','operating_profitability','cashflow_to_assets','asset_turnover','leverage','capex_to_assets','cash_to_assets']
FUND=FIELDS[5:]

class Panel:
    def __init__(self):
        meta=read_json('data/panel/identity.json');self.identity=meta['identity']
        self.dates=pd.DatetimeIndex(pd.to_datetime(meta['dates']));self.names=np.array(meta['names'])
        self.fields={k:np.load(ROOT/f'data/panel/{k}.npy',mmap_mode='r') for k in FIELDS}
        self.member=np.load(ROOT/'data/panel/member.npy',mmap_mode='r')
        self.groups=np.load(ROOT/'data/panel/groups.npy',mmap_mode='r')
        self.shape=self.member.shape
    def frame(self,k):return pd.DataFrame(self.fields[k],index=self.dates,columns=self.names,copy=False)
    def labels(self):
        # Exact next market date, independent of next-date universe membership.
        r=np.asarray(self.fields['returns']);out=np.full(r.shape,np.nan);out[:-1]=r[1:];return out

def build():
    dest=ROOT/'data/panel';dest.mkdir(parents=True,exist_ok=True)
    if (dest/'identity.json').exists():return Panel()
    protocol=read_json('configs/protocol.json'); sources=[]; audits=[]
    panelparts=[]; memberships=[]
    for year in range(2017,2025):
        if year>=2019:
            p=DATA/f'processed/top3000_with_fundamentals/top3000_with_fundamentals_{year}.parquet'
            cols=['date','permno','siccd','formation_date','available_date','datadate',*FUND]
            part=pd.read_parquet(p,columns=cols)
            assert not part.duplicated(['date','permno']).any()
            attached=part.available_date.notna()
            future=int((part.loc[attached,'available_date']>part.loc[attached,'date']).sum())
            badform=int((part.formation_date>=part.date).sum())
            assert future==badform==0
            ages=(part.date-part.datadate).dt.days
            stale=ages>protocol['fundamental_max_age_days']
            part.loc[stale,FUND]=np.nan
            audits.append(dict(year=year,rows=len(part),future_availability=future,noncausal_formation=badform,stale_rows=int(stale.sum()),fundamental_revisions='NOT_VINTAGE_PIT',max_age_days=730))
            panelparts.append(part)
            sources.append(dict(path=str(p.relative_to(R1)),sha256=sha(p),bytes=p.stat().st_size))
    panel=pd.concat(panelparts,ignore_index=True);del panelparts
    warm=DATA/'processed/top3000_price_volume/top3000_membership_2018.parquet'
    mem=pd.read_parquet(warm);sources.append(dict(path=str(warm.relative_to(R1)),sha256=sha(warm),bytes=warm.stat().st_size))
    names=np.array(sorted(set(panel.permno)|set(mem.permno)))
    rawparts=[];dates=[]
    for year in range(2017,2025):
        p=DATA/f'raw/crsp_daily/crsp_daily_{year}.parquet'
        raw=pd.read_parquet(p,columns=['date','permno','dlyret','dlyretx','dlyvol','dlyclose','shrout'])
        dates.extend(raw.date.unique());rawparts.append(raw.loc[raw.permno.isin(names)])
        sources.append(dict(path=str(p.relative_to(R1)),sha256=sha(p),bytes=p.stat().st_size))
    dates=pd.DatetimeIndex(sorted(set(dates)));raw=pd.concat(rawparts,ignore_index=True);del rawparts
    assert not raw.duplicated(['date','permno']).any()
    def wide(frame,col):return frame.pivot(index='date',columns='permno',values=col).reindex(index=dates,columns=names).to_numpy(dtype='float64')
    member=wide(panel.assign(member=1),'member')==1
    cal=pd.DataFrame({'date':dates[dates.year==2018]});cal['apply_month_start']=cal.date.dt.to_period('M').dt.to_timestamp()
    wm=cal.merge(mem,on='apply_month_start')[['date','permno']]
    member |= wide(wm.assign(member=1),'member')==1
    np.save(dest/'member.npy',member)
    grp=wide(panel,'siccd');grp=np.where((grp>=100)&(grp<=9999),np.floor(grp/100),-1).astype('int16');np.save(dest/'groups.npy',grp)
    for field,col in [('returns','dlyret'),('retx','dlyretx'),('volume','dlyvol'),('close','dlyclose')]:
        a=wide(raw,col)
        if field=='close':a=np.abs(a);a[a==0]=np.nan
        if field=='volume':a[a<0]=np.nan
        if field in ['returns','retx']:a[a< -1]=np.nan
        np.save(dest/f'{field}.npy',a)
    cap=wide(raw,'dlyclose');cap=np.abs(cap)*wide(raw,'shrout');cap[cap<=0]=np.nan;np.save(dest/'market_cap.npy',cap)
    for field in FUND:np.save(dest/f'{field}.npy',wide(panel,field))
    ident=digest(dict(sources=sources,protocol=protocol,layer='R2-calendar-v1'))
    write_json('data/panel/identity.json',dict(identity=ident,dates=dates.astype(str).tolist(),names=names.tolist(),sources=sources,created_at=now()))
    write_json('02/results/data_audit.json',dict(years=audits,dates=len(dates),storage_names=len(names),member_rows=int(member.sum()),shape=list(member.shape),sources=sources,identity=ident,limitations=['Accounting revisions are not historical vintages','180-day availability lag is an approximation','SIC2 differs from BRAIN subindustry','2017 prewarm prices available; cross-sectional warmup membership starts 2018','Raw CRSP return includes source return semantics; no independent delisting adjustment added']))
    return Panel()
