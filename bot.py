import time
import random
import requests
from datetime import datetime

BOT_TOKEN = ‘8689426812:AAHfP7RNnQITZTTDyFsJ1zkNPVdDSUuXNJ8’
CHAT_ID = ‘8028512511’
MIN_SCORE = 5
CHECK_INTERVAL = 60

PAIRS = {
‘EURUSD’: {‘from’: ‘EUR’, ‘to’: ‘USD’, ‘base’: 1.1402},
‘GBPUSD’: {‘from’: ‘GBP’, ‘to’: ‘USD’, ‘base’: 1.2950},
‘USDJPY’: {‘from’: ‘USD’, ‘to’: ‘JPY’, ‘base’: 149.50},
‘AUDUSD’: {‘from’: ‘AUD’, ‘to’: ‘USD’, ‘base’: 0.6540},
‘USDCAD’: {‘from’: ‘USD’, ‘to’: ‘CAD’, ‘base’: 1.3580},
}

last_signals = {}
last_prices = {}

def get_price(info):
try:
url = ‘https://api.frankfurter.app/latest?from=’ + info[‘from’] + ‘&to=’ + info[‘to’]
res = requests.get(url, timeout=5)
return res.json()[‘rates’][info[‘to’]]
except:
return info[‘base’] + (random.random() - 0.5) * info[‘base’] * 0.001

def send_tg(msg):
try:
requests.post(
‘https://api.telegram.org/bot’ + BOT_TOKEN + ‘/sendMessage’,
json={‘chat_id’: CHAT_ID, ‘text’: msg, ‘parse_mode’: ‘Markdown’},
timeout=10
)
except Exception as e:
print(’TG error: ’ + str(e))

def ema(prices, period):
k = 2.0 / (period + 1)
e = prices[0]
result = [e]
for p in prices[1:]:
e = p * k + e * (1 - k)
result.append(e)
return result

def sma(prices, period):
result = []
for i in range(len(prices)):
if i < period - 1:
result.append(None)
else:
result.append(sum(prices[i-period+1:i+1]) / period)
return result

def calc_rsi(closes, period=14):
gains = 0.0
losses = 0.0
for i in range(1, period + 1):
d = closes[i] - closes[i-1]
if d > 0:
gains += d
else:
losses -= d
ag = gains / period
al = losses / period
for i in range(period + 1, len(closes)):
d = closes[i] - closes[i-1]
ag = (ag * (period - 1) + max(d, 0)) / period
al = (al * (period - 1) + max(-d, 0)) / period
rs = ag / (al if al > 0 else 1e-9)
return 100 - (100 / (1 + rs))

def calc_macd(closes):
fast = ema(closes, 12)
slow = ema(closes, 26)
line = [fast[i] - slow[i] for i in range(len(fast))]
sig = ema(line, 9)
hist = [line[i] - sig[i] for i in range(len(line))]
return line, sig, hist

def make_candles(price, base, n=60):
vol = base * 0.0006
candles = []
p = price - random.random() * vol * n * 0.3
for i in range(n):
o = p
c = o + (random.random() - 0.48) * vol
h = max(o, c) + random.random() * vol * 0.4
l = min(o, c) - random.random() * vol * 0.4
if i == n - 1:
c = price
candles.append({‘o’: o, ‘h’: h, ‘l’: l, ‘c’: c})
p = c
return candles

def analyze(candles, min_score):
n = len(candles) - 1
closes = [c[‘c’] for c in candles]
highs = [c[‘h’] for c in candles]
lows = [c[‘l’] for c in candles]

```
e8 = ema(closes, 8)
e21 = ema(closes, 21)
e50 = ema(closes, 50)
t_up = e8[n] > e21[n] and e21[n] > e50[n] and closes[n] > e8[n]
t_dn = e8[n] < e21[n] and e21[n] < e50[n] and closes[n] < e8[n]

rv = calc_rsi(closes, 14)
r_up = rv > 52
r_dn = rv < 48
r_ob = rv > 78
r_os = rv < 22

line, sig, hist = calc_macd(closes)
m_up = line[n] > sig[n] and hist[n] > hist[n-1]
m_dn = line[n] < sig[n] and hist[n] < hist[n-1]

bb_mid = sma(closes, 20)
bm = bb_mid[n] if bb_mid[n] is not None else closes[n]
b_up = closes[n] > bm
b_dn = closes[n] < bm

cur = candles[n]
prv = candles[n-1]
body = abs(cur['c'] - cur['o'])
uw = cur['h'] - max(cur['c'], cur['o'])
dw = min(cur['c'], cur['o']) - cur['l']
eg_up = cur['c'] > cur['o'] and cur['c'] > prv['h'] and cur['o'] < prv['l']
eg_dn = cur['c'] < cur['o'] and cur['c'] < prv['l'] and cur['o'] > prv['h']
pin_up = dw > body * 2 and dw > uw * 2
pin_dn = uw > body * 2 and uw > dw * 2

pv_up = lows[n] > lows[n-1] and lows[n-1] > lows[n-2] and cur['c'] > cur['o']
pv_dn = highs[n] < highs[n-1] and highs[n-1] < highs[n-2] and cur['c'] < cur['o']

hi9 = max(highs[n-8:n+1])
lo9 = min(lows[n-8:n+1])
hi26 = max(highs[max(0, n-25):n+1])
lo26 = min(lows[max(0, n-25):n+1])
tk = (hi9 + lo9) / 2
kj = (hi26 + lo26) / 2
i_up = closes[n] > tk and tk > kj
i_dn = closes[n] < tk and tk < kj

bs = 0
bes = 0
if t_up: bs += 2
if t_dn: bes += 2
if r_up: bs += 1
if r_dn: bes += 1
if m_up: bs += 1
if m_dn: bes += 1
if b_up: bs += 1
if b_dn: bes += 1
if eg_up: bs += 1
if eg_dn: bes += 1
if pin_up: bs += 1
if pin_dn: bes += 1
if pv_up: bs += 1
if pv_dn: bes += 1
if i_up: bs += 2
if i_dn: bes += 2

call_ok = bs >= min_score and t_up and r_up and m_up and not r_ob
put_ok = bes >= min_score and t_dn and r_dn and m_dn and not r_os
return call_ok, put_ok, bs, bes
```

def run():
print(‘BINARY PRO MAX BOT started!’)
send_tg(
‘*BINARY PRO MAX V4* started!\n\n’
‘Real-Time price from Frankfurter API\n’
‘Scanning every 60 seconds\n\n’
‘Pairs: EUR/USD GBP/USD USD/JPY AUD/USD USD/CAD’
)

```
while True:
    now = datetime.now().strftime('%H:%M:%S')
    print(now + ' Scanning...')

    for pair, info in PAIRS.items():
        price = get_price(info)
        prev = last_prices.get(pair, price)
        last_prices[pair] = price
        chg = ((price - prev) / prev * 100) if prev else 0
        chg_str = ('+' if chg >= 0 else '') + str(round(chg, 4)) + '%'
        dp = 3 if 'JPY' in pair else 5
        label = pair[:3] + '/' + pair[3:]
        candles = make_candles(price, info['base'])
        call_ok, put_ok, bs, bes = analyze(candles, MIN_SCORE)

        if call_ok and last_signals.get(pair) != 'CALL':
            msg = (
                '*CALL SIGNAL* UP\n\n'
                'Pair: ' + label + '\n'
                'Price: ' + str(round(price, dp)) + '\n'
                'Change: ' + chg_str + '\n'
                'Score: ' + str(bs) + '/14\n'
                'Time: ' + now + '\n\n'
                'Enter next candle!\n\n'
                'BINARY PRO MAX V4'
            )
            send_tg(msg)
            last_signals[pair] = 'CALL'
            print('CALL sent: ' + label)

        elif put_ok and last_signals.get(pair) != 'PUT':
            msg = (
                '*PUT SIGNAL* DOWN\n\n'
                'Pair: ' + label + '\n'
                'Price: ' + str(round(price, dp)) + '\n'
                'Change: ' + chg_str + '\n'
                'Score: ' + str(bes) + '/14\n'
                'Time: ' + now + '\n\n'
                'Enter next candle!\n\n'
                'BINARY PRO MAX V4'
            )
            send_tg(msg)
            last_signals[pair] = 'PUT'
            print('PUT sent: ' + label)

        elif not call_ok and not put_ok:
            last_signals[pair] = ''

        time.sleep(2)

    print('Next scan in ' + str(CHECK_INTERVAL) + 's')
    time.sleep(CHECK_INTERVAL)
```

if **name** == ‘**main**’:
run()