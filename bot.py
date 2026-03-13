# -*- coding: utf-8 -*-

import os,sys,base64,urllib.request,json,time
from datetime import datetime
_c=lambda s:s
T=os.environ.get(_c(‘TELEGRAM_TOKEN’),_c(’’))
C=os.environ.get(_c(‘CHAT_ID’),_c(’’))
K=os.environ.get(_c(‘TWELVE_API_KEY’),_c(’’))
MIN_SCORE=8
INTERVAL=30
PAIRS=[_c(‘EUR/USD’),_c(‘GBP/USD’),_c(‘USD/JPY’),_c(‘AUD/USD’),_c(‘USD/CAD’),_c(‘USD/CHF’),_c(‘NZD/USD’),_c(‘EUR/GBP’),_c(‘EUR/JPY’),_c(‘GBP/JPY’),_c(‘AUD/JPY’),_c(‘EUR/AUD’),_c(‘EUR/CHF’),_c(‘GBP/CHF’),_c(‘CAD/JPY’),_c(‘AUD/CAD’),_c(‘AUD/CHF’),_c(‘AUD/NZD’),_c(‘CAD/CHF’),_c(‘CHF/JPY’),_c(‘GBP/AUD’),_c(‘GBP/CAD’),_c(‘GBP/NZD’),_c(‘EUR/CAD’),_c(‘EUR/NZD’)]
SIG={}
def tg(m):
u=_c(‘https://api.telegram.org/bot’)+T+_c(’/sendMessage’)
d=json.dumps({_c(‘chat_id’):C,_c(‘text’):m,_c(‘parse_mode’):_c(‘Markdown’)}).encode()
try:urllib.request.urlopen(urllib.request.Request(u,d,{_c(‘Content-Type’):_c(‘application/json’)}),timeout=10)
except Exception as e:print(e)
def gc(sym,n=100):
s=sym.replace(_c(’/’),_c(’’))
u=_c(‘https://api.twelvedata.com/time_series?symbol=’)+s+_c(’&interval=1min&outputsize=’)+str(n)+_c(’&apikey=’)+K
try:
r=urllib.request.urlopen(u,timeout=10)
d=json.loads(r.read())
if _c(‘values’) not in d:return None
return [{_c(‘o’):float(v[_c(‘open’)]),_c(‘h’):float(v[_c(‘high’)]),_c(‘l’):float(v[_c(‘low’)]),_c(‘c’):float(v[_c(‘close’)])} for v in reversed(d[_c(‘values’)])]
except:return None
def ema(p,n):
k=2.0/(n+1);e=p[0];r=[e]
for x in p[1:]:e=x*k+e*(1-k);r.append(e)
return r
def sma(p,n):
r=[]
for i in range(len(p)):r.append(None if i<n-1 else sum(p[i-n+1:i+1])/n)
return r
def rsi(c,n=14):
g=l=0.0
for i in range(1,n+1):
d=c[i]-c[i-1]
if d>0:g+=d
else:l-=d
ag=g/n;al=l/n
for i in range(n+1,len(c)):
d=c[i]-c[i-1];ag=(ag*(n-1)+max(d,0))/n;al=(al*(n-1)+max(-d,0))/n
rs=ag/(al if al>0 else 1e-9)
return 100-(100/(1+rs))
def macd(c):
f=ema(c,12);s=ema(c,26);l=[a-b for a,b in zip(f,s)];sg=ema(l,9);h=[a-b for a,b in zip(l,sg)]
return l,sg,h
def stoch(cs,kp=14,dp=3):
ks=[]
for i in range(len(cs)):
if i<kp-1:ks.append(None);continue
hi=max(x[_c(‘h’)] for x in cs[i-kp+1:i+1]);lo=min(x[_c(‘l’)] for x in cs[i-kp+1:i+1]);cl=cs[i][_c(‘c’)]
ks.append((cl-lo)/(hi-lo)*100 if hi!=lo else 50.0)
v=[x for x in ks if x is not None]
return v,sma(v,dp)
def atr(cs,n=14):
t=[]
for i in range(1,len(cs)):t.append(max(cs[i][_c(‘h’)]-cs[i][_c(‘l’)],abs(cs[i][_c(‘h’)]-cs[i-1][_c(‘c’)]),abs(cs[i][_c(‘l’)]-cs[i-1][_c(‘c’)])))
if len(t)<n:return sum(t)/len(t)
a=sum(t[:n])/n
for x in t[n:]:a=(a*(n-1)+x)/n
return a
def wr(cs,n=14):
i=len(cs)-1;hi=max(x[_c(‘h’)] for x in cs[i-n+1:i+1]);lo=min(x[_c(‘l’)] for x in cs[i-n+1:i+1])
return (hi-cs[i][_c(‘c’)])/(hi-lo)*-100 if hi!=lo else -50.0
def analyze(cs):
n=len(cs)-1;cl=[x[_c(‘c’)] for x in cs];hi=[x[_c(‘h’)] for x in cs];lo=[x[_c(‘l’)] for x in cs]
e8=ema(cl,8);e21=ema(cl,21);e50=ema(cl,50)
tu=e8[n]>e21[n] and e21[n]>e50[n] and cl[n]>e8[n]
td=e8[n]<e21[n] and e21[n]<e50[n] and cl[n]<e8[n]
rv=rsi(cl);ru=rv>52;rd=rv<48;rob=rv>75;ros=rv<25
ml,ms,mh=macd(cl);mu=ml[n]>ms[n] and mh[n]>mh[n-1];md=ml[n]<ms[n] and mh[n]<mh[n-1]
bb=sma(cl,20);bv=bb[n] if bb[n] else cl[n];bu=cl[n]>bv;bd=cl[n]<bv
cur=cs[n];prv=cs[n-1];body=abs(cur[_c(‘c’)]-cur[_c(‘o’)]);uw=cur[_c(‘h’)]-max(cur[_c(‘c’)],cur[_c(‘o’)]);dw=min(cur[_c(‘c’)],cur[_c(‘o’)])-cur[_c(‘l’)]
egu=cur[_c(‘c’)]>cur[_c(‘o’)] and cur[_c(‘c’)]>prv[_c(‘h’)] and cur[_c(‘o’)]<prv[_c(‘l’)]
egd=cur[_c(‘c’)]<cur[_c(‘o’)] and cur[_c(‘c’)]<prv[_c(‘l’)] and cur[_c(‘o’)]>prv[_c(‘h’)]
pu=dw>body*2 and dw>uw*2;pd=uw>body*2 and uw>dw*2
pvu=lo[n]>lo[n-1] and lo[n-1]>lo[n-2] and cur[_c(‘c’)]>cur[_c(‘o’)]
pvd=hi[n]<hi[n-1] and hi[n-1]<hi[n-2] and cur[_c(‘c’)]<cur[_c(‘o’)]
h9=max(hi[n-8:n+1]);l9=min(lo[n-8:n+1]);h26=max(hi[max(0,n-25):n+1]);l26=min(lo[max(0,n-25):n+1])
tk=(h9+l9)/2;kj=(h26+l26)/2;iu=cl[n]>tk and tk>kj;id=cl[n]<tk and tk<kj
kv,dv=stoch(cs);kc=kv[-1] if kv else 50;dc=dv[-1] if dv else 50
stu=kc>dc and kc<80;std=kc<dc and kc>20
w=wr(cs);wu=-50<w<=-20;wd=-80<=w<-50
av=atr(cs);vol=(av/cl[n])*100>0.003
bs=bes=0
for f,b in [(tu,2),(ru,1),(mu,1),(bu,1),(egu,1),(pu,1),(pvu,1),(iu,2),(stu,2),(wu,2)]:
if f:bs+=b
for f,b in [(td,2),(rd,1),(md,1),(bd,1),(egd,1),(pd,1),(pvd,1),(id,2),(std,2),(wd,2)]:
if f:bes+=b
call=bs>=MIN_SCORE and tu and ru and mu and stu and not rob and vol
put=bes>=MIN_SCORE and td and rd and md and std and not ros and vol
return call,put,bs,bes
def run():
print(_c(‘BINARY PRO MAX V5 ULTRA started!’))
tg(_c(‘BINARY PRO MAX V5 ULTRA started! ‘)+str(len(PAIRS))+_c(’ pairs | every ‘)+str(INTERVAL)+_c(‘s | min ‘)+str(MIN_SCORE)+_c(’/20’))
while True:
now=datetime.now().strftime(_c(’%H:%M:%S’))
for sym in PAIRS:
try:
cs=gc(sym)
if not cs or len(cs)<50:time.sleep(1);continue
call,put,bs,bes=analyze(cs)
p=cs[-1][_c(‘c’)];dp=3 if _c(‘JPY’) in sym else 5;key=sym.replace(_c(’/’),_c(’’));ps=str(round(p,dp))
if call and SIG.get(key)!=_c(‘CALL’):
tg(_c(‘CALL SIGNAL\n’)+sym+_c(’\nPrice: ‘)+ps+_c(’\nScore: ‘)+str(bs)+_c(’/20\nTime: ‘)+now+_c(’\nEnter next candle!’))
SIG[key]=_c(‘CALL’)
elif put and SIG.get(key)!=_c(‘PUT’):
tg(_c(‘PUT SIGNAL\n’)+sym+_c(’\nPrice: ‘)+ps+_c(’\nScore: ‘)+str(bes)+_c(’/20\nTime: ‘)+now+_c(’\nEnter next candle!’))
SIG[key]=_c(‘PUT’)
elif not call and not put:SIG[key]=_c(’’)
time.sleep(1)
except Exception as e:print(str(e));continue
time.sleep(INTERVAL)
if **name**==_c(’**main**’):run()
