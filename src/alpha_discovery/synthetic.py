"""Completely synthetic securities and annual accounts, never calibrated to licensed rows."""
import numpy as np
import pandas as pd
from .preprocessing import monthly_membership, apply_membership, attach_accounts, ArrayPanel

def synthetic_inputs(seed=718,stocks=160):
    rng=np.random.default_rng(seed)
    dates=pd.bdate_range('2017-01-02','2024-12-31')
    names=np.arange(1,stocks+1)
    n=len(dates);r=rng.normal(0,.008,(n,stocks))
    close=30*np.cumprod(1+r,axis=0)
    raw=pd.DataFrame(dict(date=np.repeat(dates,stocks),permno=np.tile(names,n),
                         dlyret=r.ravel(),dlyretx=r.ravel(),dlyclose=close.ravel(),
                         dlyvol=rng.uniform(10000,100000,(n,stocks)).ravel(),
                         shrout=np.tile(1000+names*10,n),siccd=np.tile(1000+(names%4)*100,n),
                         gvkey=np.tile(['SYNTHETIC_'+str(i) for i in names],n)))
    # Unobservable raw returns are deliberate test cases; prices remain synthetic.
    raw.loc[(raw.date==pd.Timestamp('2023-07-10'))&(raw.permno==stocks),'dlyret']=np.nan
    a=pd.MultiIndex.from_product([raw.gvkey.unique(),pd.date_range('2016-12-31','2023-12-31',freq='YE')],names=['gvkey','datadate']).to_frame(index=False)
    count=len(a);a['at']=rng.uniform(200,800,count)
    for field,lo,hi in [('sale',.4,1.5),('ni',-.05,.15),('oiadp',-.03,.2),('oancf',-.05,.2),('dltt',.1,.4),('dlc',.01,.1),('che',.05,.3),('capx',.01,.1),('invt',.02,.2),('rect',.03,.25),('ceq',.3,.8)]:
        a[field]=a['at']*rng.uniform(lo,hi,count)
    a.loc[a.index[0],'dlc']=np.nan
    return raw,a

def make_panel(seed=718,stocks=160,top_n=120):
    raw,accounts=synthetic_inputs(seed,stocks)
    membership=monthly_membership(raw,top_n)
    selected=attach_accounts(apply_membership(raw,membership),accounts)
    panel=ArrayPanel(raw,selected,'SYNTHETIC-'+str(seed))
    return panel,raw,accounts,selected,membership
