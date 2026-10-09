"""Whitelisted AST, conservative canonicalization and causal matrix operators."""
from dataclasses import dataclass
import ast, json
from collections import OrderedDict
import numpy as np
import pandas as pd
from .common import digest

WINDOWS={1,2,3,5,10,20,40,60,120,252}
TS={'ts_mean','ts_sum','ts_std','ts_delta','ts_rank','ts_delay','ts_min','ts_max','decay_linear','compound_return'}
UNARY={'rank','zscore','negate','abs','group_residual'}
BINARY={'add','subtract','multiply','divide','ts_corr'}
FIELDS={'returns','retx','volume','close','market_cap','book_to_market','earnings_yield','cashflow_yield','roa','operating_profitability','cashflow_to_assets','asset_turnover','leverage','capex_to_assets','cash_to_assets','open','high','low','shares_outstanding'}
UNITS={k:'ratio' for k in FIELDS};UNITS.update(close='price',open='price',high='price',low='price',volume='shares',market_cap='capitalization',shares_outstanding='shares_unit')
@dataclass(frozen=True)
class Expr:
    op:str
    args:tuple=()
    window:int|None=None
    def render(self):
        if not self.args:return self.op
        args=[a.render() for a in self.args]
        if self.op in {'add','multiply'}:args=sorted(args)
        if self.window is not None:args.append(str(self.window))
        return self.op+'('+','.join(args)+')'
    @property
    def identity(self):return 'R2_'+digest(self.render())[:20]
    @property
    def depth(self):return 0 if not self.args else 1+max(a.depth for a in self.args)
    @property
    def nodes(self):return int(bool(self.args))+sum(a.nodes for a in self.args)
    @property
    def fields(self):return {self.op} if not self.args else set().union(*(a.fields for a in self.args))
    @property
    def interactions(self):return int(self.op in {'multiply','divide','condition'})+max([a.interactions for a in self.args] or [0])
    @property
    def lookback(self):return max([a.lookback for a in self.args] or [0])+(self.window if self.op in {'ts_delta','ts_delay'} else max(0,(self.window or 1)-1))

def parse(text):
    def read(n):
        if isinstance(n,ast.Name) and n.id in FIELDS:return Expr(n.id)
        if not isinstance(n,ast.Call) or not isinstance(n.func,ast.Name) or n.keywords:raise ValueError('Unsupported AST')
        op=n.func.id;args=n.args;w=None
        if op in TS or op=='ts_corr':
            if not isinstance(args[-1],ast.Constant) or type(args[-1].value)!=int:raise ValueError('Window must be integer')
            w=args[-1].value;args=args[:-1]
            if w not in WINDOWS or (op in {'ts_std','ts_corr'} and w<2):raise ValueError('Invalid window')
        arity=1 if op in TS|UNARY else 2 if op in BINARY else 3 if op in {'condition','range_guard'} else 2 if op=='turnover_guard' else -1
        if len(args)!=arity:raise ValueError('Unsupported operator or arity: '+op)
        out=Expr(op,tuple(read(a) for a in args),w)
        if out.depth>6 or out.nodes>10 or len(out.fields)>3 or out.interactions>2:raise ValueError('Complexity limit')
        return out
    return read(ast.parse(text,mode='eval').body)

def unit(e):
    if not e.args:return UNITS[e.op]
    u=[unit(a) for a in e.args]
    if e.op in {'rank','zscore','ts_rank','ts_corr','compound_return','range_guard','turnover_guard'}:return 'ratio'
    if e.op in {'add','subtract'} and u[0]!=u[1]:raise ValueError('Incompatible additive units')
    if e.op=='multiply':
        if u[0]!='ratio' or u[1]!='ratio':raise ValueError('Generated products require dimensionless inputs')
        return 'ratio'
    if e.op=='divide':
        if u[0]==u[1]:return 'ratio'
        if u[1]=='ratio':return u[0]
        raise ValueError('Undefined ratio unit')
    if e.op=='condition':
        if u[0]!='ratio' or u[1]!=u[2]:raise ValueError('Invalid conditional units')
        return u[1]
    return u[0]

class Cache(OrderedDict):
    def __init__(self,max_bytes=512*1024**2):super().__init__();self.max_bytes=max_bytes;self.bytes=0
    def __setitem__(self,k,v):
        if k in self:self.bytes-=self[k].values.nbytes;super().__delitem__(k)
        size=v.values.nbytes
        if size>self.max_bytes:return
        super().__setitem__(k,v);self.bytes+=size
        while self.bytes>self.max_bytes:
            _,old=self.popitem(last=False);self.bytes-=old.values.nbytes

def group_demean(x,groups,member):
    from .evaluator import demean_groups
    return pd.DataFrame(demean_groups(x.to_numpy(),groups,member),index=x.index,columns=x.columns)

class Interpreter:
    def __init__(self,panel,cache=None):
        self.p=panel;self.cache=cache
        self.member=panel.member
        self.context=digest({'data':panel.identity,'operator':'R2-ops-1.0','universe':'PIT-full','timing':'close-information'})
    def evaluate(self,e):
        key=(self.context,e.render())
        if self.cache is not None and key in self.cache:return self.cache[key]
        if not e.args:return self.p.frame(e.op)
        args=[self.evaluate(a) for a in e.args];x=args[0];op=e.op;w=e.window
        if op=='rank':out=x.where(self.member).rank(axis=1,method='average',pct=True)
        elif op=='zscore':
            v=x.where(self.member);sd=v.std(axis=1,ddof=1);out=v.sub(v.mean(axis=1),axis=0).div(sd.where(sd!=0),axis=0)
        elif op=='group_residual':out=group_demean(x,self.p.groups,self.member)
        elif op=='negate':out=-x
        elif op=='abs':out=x.abs()
        elif op=='ts_delay':out=x.shift(w)
        elif op=='ts_delta':out=x-x.shift(w)
        elif op in TS:
            roll=x.rolling(w,min_periods=w)
            if op=='ts_rank':out=roll.rank(method='average',pct=True)
            elif op=='decay_linear':
                out=x*0
                for lag in range(w):out=out+x.shift(lag)*(w-lag)/(w*(w+1)/2)
            elif op=='compound_return':
                gross=(1+x).where(x>=-1);zero=gross.eq(0).where(gross.notna()).rolling(w,min_periods=w).sum()
                logs=np.log(gross.where(gross>0,1)).where(gross.notna()).rolling(w,min_periods=w).sum()
                out=np.expm1(logs).where(zero==0,-1).where(zero.notna())
            else:out=getattr(roll,{'ts_mean':'mean','ts_sum':'sum','ts_std':'std','ts_min':'min','ts_max':'max'}[op])()
        elif op=='ts_corr':out=x.rolling(w,min_periods=w).corr(args[1])
        elif op=='add':out=x+args[1]
        elif op=='subtract':out=x-args[1]
        elif op=='multiply':out=x*args[1]
        elif op=='divide':out=x/args[1].where(args[1]!=0)
        elif op=='condition':out=args[1].where(x>.5,args[2]).where(x.notna()&args[1].notna()&args[2].notna())
        elif op=='range_guard':out=((x-args[2])/(args[1]-args[2]).where(args[1]>args[2]));out=out.where((out>=0)&(out<=1))
        elif op=='turnover_guard':out=(x/args[1].where(args[1]>0)).where(x>=0)
        else:raise ValueError(op)
        out=out.where(np.isfinite(out))
        if self.cache is not None and e.depth<=2:self.cache[key]=out
        return out

def rank_equivalence(e):
    # Full-window sum/mean differ by positive scale only under outer rank.
    if e.op=='rank' and e.args[0].op=='ts_sum':
        a=e.args[0];return Expr('rank',(Expr('ts_mean',a.args,a.window),)).render()
    return e.render()
