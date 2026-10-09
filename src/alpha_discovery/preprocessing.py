"""Portable input adapters for monthly PIT membership and available annual accounts.

These adapters express the reviewed R1 notebook rules in small callable functions.
They are checked with hand examples; they do not claim a new historical data audit.
"""
import numpy as np
import pandas as pd
from .fundamentals import construct_factors

def unique_keys(frame, keys):
    if frame[keys].isna().any().any() or frame.duplicated(keys).any():
        raise ValueError('Missing or duplicate data keys: ' + ', '.join(keys))

def monthly_membership(eligible, top_n=3000):
    """Rank at each month end, activate next month; PERMNO breaks size ties."""
    unique_keys(eligible, ['date', 'permno'])
    data=eligible.copy()
    data['formation_month']=data.date.dt.to_period('M')
    ends=data.groupby('formation_month',as_index=False).date.max().rename(columns={'date':'formation_date'})
    data=data.merge(ends,on='formation_month',validate='many_to_one')
    data['market_cap_proxy']=data.dlyclose.abs()*data.shrout
    data=data[(data.date==data.formation_date)&(data.market_cap_proxy>0)].copy()
    data=data.sort_values(['formation_date','market_cap_proxy','permno'],ascending=[True,False,True],kind='mergesort')
    data['market_cap_rank']=data.groupby('formation_date').cumcount()+1
    data=data[data.market_cap_rank<=top_n].copy()
    data['apply_month_start']=data.formation_date+pd.offsets.MonthBegin(1)
    return data[['formation_date','apply_month_start','permno','market_cap_rank']].reset_index(drop=True)

def apply_membership(eligible, membership):
    unique_keys(eligible,['date','permno'])
    unique_keys(membership,['apply_month_start','permno'])
    data=eligible.copy();data['apply_month_start']=data.date.dt.to_period('M').dt.to_timestamp()
    data=data.merge(membership,on=['apply_month_start','permno'],how='inner',validate='many_to_one')
    if (data.formation_date>=data.date).any(): raise ValueError('Noncausal universe formation')
    return data

def attach_accounts(panel, accounts):
    """Backward as-of by GVKEY; 180 calendar days, with a 730-day datadate mask."""
    unique_keys(panel,['date','permno'])
    unique_keys(accounts,['gvkey','datadate'])
    right=accounts.copy();right['available_date']=right.datadate+pd.Timedelta(days=180)
    left=panel.copy();left['_row_order']=np.arange(len(left))
    left['gvkey']=left.gvkey.astype(str);right['gvkey']=right.gvkey.astype(str)
    out=pd.merge_asof(left.sort_values(['date','gvkey']),right.sort_values(['available_date','gvkey']),
                      left_on='date',right_on='available_date',by='gvkey',direction='backward',allow_exact_matches=True)
    if (out.available_date.dropna()>out.loc[out.available_date.notna(),'date']).any():
        raise ValueError('Future accounting information')
    out=construct_factors(out).sort_values('_row_order').drop(columns='_row_order')
    fields=['roa','operating_profitability','cashflow_to_assets','asset_turnover','leverage','cash_to_assets',
            'capex_to_assets','book_to_market','earnings_yield','cashflow_yield']
    out.loc[(out.date-out.datadate).dt.days>730,fields]=np.nan
    unique_keys(out,['date','permno'])
    return out

class ArrayPanel:
    """Same matrix interface as the frozen R2 Panel, on the complete raw calendar."""
    def __init__(self, raw, selected, identity):
        unique_keys(raw,['date','permno']);unique_keys(selected,['date','permno'])
        self.dates=pd.DatetimeIndex(sorted(raw.date.unique()))
        self.names=np.asarray(sorted(raw.permno.unique()));self.identity=identity
        def wide(df,col):
            return df.pivot(index='date',columns='permno',values=col).reindex(index=self.dates,columns=self.names).to_numpy(dtype=float)
        self.member=wide(selected.assign(member=1),'member')==1
        sic=wide(selected,'siccd')
        self.groups=np.where((sic>=100)&(sic<=9999),np.floor(sic/100),-1).astype('int16')
        self.fields={key:wide(raw,col) for key,col in [('returns','dlyret'),('retx','dlyretx'),('volume','dlyvol'),('close','dlyclose')]}
        self.fields['close']=abs(self.fields['close']);self.fields['close'][self.fields['close']==0]=np.nan
        self.fields['volume'][self.fields['volume']<0]=np.nan
        for key in ['returns','retx']: self.fields[key][self.fields[key]<-1]=np.nan
        cap=abs(wide(raw,'dlyclose'))*wide(raw,'shrout');cap[cap<=0]=np.nan
        self.fields['market_cap']=cap
        for f in ['roa','operating_profitability','cashflow_to_assets','asset_turnover','leverage','cash_to_assets',
                  'capex_to_assets','book_to_market','earnings_yield','cashflow_yield']:
            self.fields[f]=wide(selected,f)
        self.shape=self.member.shape
    def frame(self,key): return pd.DataFrame(self.fields[key],index=self.dates,columns=self.names,copy=False)
    def labels(self):
        out=np.full(self.shape,np.nan);out[:-1]=self.fields['returns'][1:];return out
