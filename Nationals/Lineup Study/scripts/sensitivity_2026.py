import itertools
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parent.parent
ROWS = []
def load(n,f):
    spec=importlib.util.spec_from_file_location(n,f); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
m3=load('m3',str(ROOT/'scripts/03_player_seasons.py'))
lu=pd.read_parquet(ROOT/'data/lineup_model.parquet')
d0=lu[(lu.season==2026)&(lu.n_nonX==9)].copy()
ps=pd.read_parquet(ROOT/'data/player_seasons.parquet'); ps=ps[ps.season==2026].set_index('player_id')
W=np.array([4.65,4.55,4.44,4.33,4.22,4.10,3.99,3.87,3.75])
ids=d0[[f'p{k}_id' for k in range(1,10)]].values
SH=np.array([[b=='P' for b in bits] for bits in itertools.product('PC',repeat=9)])
idxA=[i for i,b in enumerate(itertools.product('PC',repeat=9)) if ''.join(b)=='PPCCPCCPC'][0]
idxB=[i for i,b in enumerate(itertools.product('PC',repeat=9)) if ''.join(b)=='PCPCPCCPC'][0]
idxC=[i for i,b in enumerate(itertools.product('PC',repeat=9)) if ''.join(b)=='CPCPCCPCP'][0]
def slopes(isP, y, cl):
    D=(isP[:,None,:]!=SH[None,:,:]).sum(2).astype(float)
    x=D-D.mean(0); b=(x*y[:,None]).sum(0)/(x*x).sum(0)
    e=(y-y.mean())[:,None]-b*x
    g=pd.DataFrame(x*e).groupby(cl).sum().values
    se=np.sqrt((g**2).sum(0))/(x*x).sum(0)
    return b,se
def report(name,isP,y,cl):
    b,se=slopes(isP,y,cl); rk=b.argsort().argsort()+1
    ROWS.append({'variant':name,'slope_A':b[idxA],'se_A':se[idxA],'rank_A':int(rk[idxA]),'slope_B':b[idxB],'se_B':se[idxB],'rank_B':int(rk[idxB]),'slope_C':b[idxC],'rank_C':int(rk[idxC]),'best_shape':''.join('P' if v else 'C' for v in SH[b.argmin()]),'best_slope':b.min()})
    print(ROWS[-1])
def tags(slg_prior=200,k_prior=60,weighted=False,value='SLG',pool_min=250, shrink_n='PA'):
    d=ps.copy(); pool=d[d.PA>=pool_min]
    def mean(c): return np.average(pool[c],weights=pool.PA) if weighted else pool[c].mean()
    n=d[shrink_n].values
    vs=(d[value].fillna(mean(value))*n+mean(value)*slg_prior)/(n+slg_prior)
    ks=(d.K_pct.fillna(mean('K_pct'))*d.PA+mean('K_pct')*k_prior)/(d.PA+k_prior)
    vp=m3.pct_against(vs.values,pool[value].dropna()); cp=100-m3.pct_against(ks.values,pool.K_pct.dropna())
    return pd.Series(vp>cp,index=d.index)
def isP_of(t): return np.array([[t[i] for i in row] for row in ids])
def rot_of(talent):
    X=pd.get_dummies(d0[['park']].astype(str),drop_first=True,dtype=float); X['t']=talent; X['f']=d0.opp_fip.values; X['r']=d0.opp_ra_g.values; X['h']=d0.home.values.astype(float)
    X=sm.add_constant(X); return d0.runs.values-sm.OLS(d0.runs.values.astype(float),X.values).fit().fittedvalues
y=d0.rot.values; cl=d0.team_season.values
base=isP_of(tags())
report('baseline',base,y,cl)
report('pool mean PA weighted',isP_of(tags(weighted=True)),y,cl)
report('shrink by AB',isP_of(tags(shrink_n='AB')),y,cl)
report('no shrink',isP_of(tags(0,0)),y,cl)
report('pool 300 PA',isP_of(tags(pool_min=300)),y,cl)
report('pool 200 PA',isP_of(tags(pool_min=200)),y,cl)
rel=ps.OBP/ps.OBP.mul(ps.PA).sum()*ps.PA.sum()
lgO=(ps.H+ps.BB+ps.HBP).sum()/(ps.AB+ps.BB+ps.HBP+ps.SF).sum(); lgS=ps.TB.sum()/ps.AB.sum()
r=(ps.OBP/lgO+ps.SLG/lgS-1)
for nm,val in [('talent shrink to 1.0',(r.fillna(1)*ps.PA+200)/(ps.PA+200)),('talent unshrunk',r.fillna(1)),('talent raw OPS', (ps.OBP+ps.SLG).fillna(0.7)),('talent OPS shrunk mean', ((ps.OBP+ps.SLG).fillna(.7)*ps.PA+200*(ps.OBP+ps.SLG).mul(ps.PA).sum()/ps.PA.sum())/(ps.PA+200))]:
    t=np.array([[val.get(i,np.nan) for i in row] for row in ids]); t=np.where(np.isnan(t),np.nanmean(t),t)
    report(nm,base,rot_of(t@W/W.sum()),cl)
X=d0[['talent']].copy(); X['h']=d0.home; X=sm.add_constant(X.astype(float))
report('model with talent and home only',base,d0.runs.values-sm.OLS(d0.runs.values.astype(float),X.values).fit().fittedvalues,cl)
report('raw runs, no expected runs model',base,d0.runs.values-d0.runs.mean(),cl)
def rot_spec(cols, park=True, talent=None):
    X=pd.get_dummies(d0[['park']].astype(str),drop_first=True,dtype=float) if park else pd.DataFrame(index=d0.index)
    X['t']=d0.talent.values if talent is None else talent
    for c in cols: X[c]=d0[c].values.astype(float)
    X=sm.add_constant(X); return d0.runs.values-sm.OLS(d0.runs.values.astype(float),X.values).fit().fittedvalues
report('no park',base,rot_spec(['opp_fip','opp_ra_g','home'],park=False),cl)
report('no opp_ra_g',base,rot_spec(['opp_fip','home']),cl)
report('no opp_fip',base,rot_spec(['opp_ra_g','home']),cl)
pit=pd.read_parquet(ROOT/'data/pitcher_seasons.parquet'); pit=pit[pit.season==2026].set_index('player_id')
raw=d0.opp_sp_id.map(pit.FIP).fillna(pit.lgERA.iloc[0]).values
d0['fip_raw']=np.clip(raw,0,15)
report('opp fip unshrunk',base,rot_spec(['fip_raw','opp_ra_g','home']),cl)
s100=d0.opp_sp_id.map((pit.FIP.fillna(pit.lgERA)*pit.IP+100*pit.lgERA)/(pit.IP+100)).fillna(pit.lgERA.iloc[0]).values
d0['fip100']=s100
report('opp fip prior 100 IP',base,rot_spec(['fip100','opp_ra_g','home']),cl)
report('xwOBA talent rot_x',base,np.nan_to_num(d0.rot_x.values),cl)
report('dropped feed gap lineups',base[~d0.feed_gap_first9.astype(bool).values],y[~d0.feed_gap_first9.astype(bool).values],cl[~d0.feed_gap_first9.astype(bool).values])

pd.DataFrame(ROWS).to_csv(ROOT/'out/tables/sensitivity_2026.csv', index=False)
