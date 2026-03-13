import time
import urllib.request
import json
from datetime import datetime
import os

BOT_TOKEN  = os.environ.get(“TELEGRAM_TOKEN”, “”)
CHAT_ID    = os.environ.get(“CHAT_ID”, “”)
TWELVE_KEY = os.environ.get(“TWELVE_API_KEY”, “”)

MIN_SCORE      = 8
CHECK_INTERVAL = 30

PAIRS = [
“EUR/USD”, “GBP/USD”, “USD/JPY”, “AUD/USD”, “USD/CAD”,
“USD/CHF”, “NZD/USD”, “EUR/GBP”, “EUR/JPY”, “GBP/JPY”,
“AUD/JPY”, “EUR/AUD”, “EUR/CHF”, “GBP/CHF”, “CAD/JPY”,
“AUD/CAD”, “AUD/CHF”, “AUD/NZD”, “CAD/CHF”, “CHF/JPY”,
“GBP/AUD”, “GBP/CAD”, “GBP/NZD”, “EUR/CAD”, “EUR/NZD”,
]

last_signals = {}

def send_telegram(msg):
url = “https://api.telegram.org/bot” + BOT_TOKEN + “/sendMessage”
body = json.dumps({
“chat_id”: CHAT_ID,
“text”: msg,
“parse_mode”: “Markdown”
}).encode(“utf-8”)
try:
req = urllib.request.Request(
url, body, {“Content-Type”: “application/json”}
)
urllib.request.urlopen(req, timeout=10)
except Exception as err:
print(“Telegram error: “ + str(err))

def get_candles(symbol):
sym = symbol.replace(”/”, “”)
url = (
“https://api.twelvedata.com/time_series”
“?symbol=” + sym +
“&interval=1min”
“&outputsize=100”
“&apikey=” + TWELVE_KEY
)
try:
res  = urllib.request.urlopen(url, timeout=15)
data = json.loads(res.read().decode(“utf-8”))
if “values” not in data:
return None
candles = []
for v in reversed(data[“values”]):
candles.append({
“o”: float(v[“open”]),
“h”: float(v[“high”]),
“l”: float(v[“low”]),
“c”: float(v[“close”]),
})
return candles
except Exception as err:
print(“API error “ + symbol + “: “ + str(err))
return None

def ema(prices, period):
k = 2.0 / (period + 1)
val = prices[0]
out = [val]
for p in prices[1:]:
val = p * k + val * (1.0 - k)
out.append(val)
return out

def sma(prices, period):
out = []
for i in range(len(prices)):
if i < period - 1:
out.append(None)
else:
out.append(sum(prices[i - period + 1:i + 1]) / period)
return out

def rsi(closes, period=14):
gain = 0.0
loss = 0.0
for i in range(1, period + 1):
d = closes[i] - closes[i - 1]
if d > 0:
gain += d
else:
loss -= d
ag = gain / period
al = loss / period
for i in range(period + 1, len(closes)):
d = closes[i] - closes[i - 1]
ag = (ag * (period - 1) + max(d, 0.0)) / period
al = (al * (period - 1) + max(-d, 0.0)) / period
rs = ag / (al if al > 0 else 1e-9)
return 100.0 - (100.0 / (1.0 + rs))

def macd(closes):
fast   = ema(closes, 12)
slow   = ema(closes, 26)
line   = [f - s for f, s in zip(fast, slow)]
sig    = ema(line, 9)
hist   = [l - s for l, s in zip(line, sig)]
return line, sig, hist

def stoch(candles, kp=14, dp=3):
ks = []
for i in range(len(candles)):
if i < kp - 1:
ks.append(None)
continue
hi = max(c[“h”] for c in candles[i - kp + 1:i + 1])
lo = min(c[“l”] for c in candles[i - kp + 1:i + 1])
cl = candles[i][“c”]
ks.append(((cl - lo) / (hi - lo) * 100.0) if hi != lo else 50.0)
valid = [v for v in ks if v is not None]
ds    = sma(valid, dp)
return valid, ds

def atr(candles, period=14):
trs = []
for i in range(1, len(candles)):
trs.append(max(
candles[i][“h”] - candles[i][“l”],
abs(candles[i][“h”] - candles[i - 1][“c”]),
abs(candles[i][“l”] - candles[i - 1][“c”]),
))
if len(trs) < period:
return sum(trs) / len(trs)
a = sum(trs[:period]) / period
for t in trs[period:]:
a = (a * (period - 1) + t) / period
return a

def williams_r(candles, period=14):
n  = len(candles) - 1
hi = max(c[“h”] for c in candles[n - period + 1:n + 1])
lo = min(c[“l”] for c in candles[n - period + 1:n + 1])
if hi == lo:
return -50.0
return (hi - candles[n][“c”]) / (hi - lo) * -100.0

def analyze(candles):
n      = len(candles) - 1
closes = [c[“c”] for c in candles]
highs  = [c[“h”] for c in candles]
lows   = [c[“l”] for c in candles]

```
# EMA trend
e8  = ema(closes, 8)
e21 = ema(closes, 21)
e50 = ema(closes, 50)
t_up = e8[n] > e21[n] and e21[n] > e50[n] and closes[n] > e8[n]
t_dn = e8[n] < e21[n] and e21[n] < e50[n] and closes[n] < e8[n]

# RSI
rv   = rsi(closes)
r_up = rv > 52
r_dn = rv < 48
r_ob = rv > 75
r_os = rv < 25

# MACD
ml, ms, mh = macd(closes)
m_up = ml[n] > ms[n] and mh[n] > mh[n - 1]
m_dn = ml[n] < ms[n] and mh[n] < mh[n - 1]

# Bollinger
bb = sma(closes, 20)
bb_val = bb[n] if bb[n] is not None else closes[n]
b_up = closes[n] > bb_val
b_dn = closes[n] < bb_val

# Candle patterns
cur  = candles[n]
prv  = candles[n - 1]
body = abs(cur["c"] - cur["o"])
uw   = cur["h"] - max(cur["c"], cur["o"])
dw   = min(cur["c"], cur["o"]) - cur["l"]
eg_up  = cur["c"] > cur["o"] and cur["c"] > prv["h"] and cur["o"] < prv["l"]
eg_dn  = cur["c"] < cur["o"] and cur["c"] < prv["l"] and cur["o"] > prv["h"]
pin_up = dw > body * 2 and dw > uw * 2
pin_dn = uw > body * 2 and uw > dw * 2

# Structure
pv_up = lows[n] > lows[n-1] and lows[n-1] > lows[n-2] and cur["c"] > cur["o"]
pv_dn = highs[n] < highs[n-1] and highs[n-1] < highs[n-2] and cur["c"] < cur["o"]

# Ichimoku
hi9  = max(highs[n - 8:n + 1])
lo9  = min(lows[n - 8:n + 1])
hi26 = max(highs[max(0, n - 25):n + 1])
lo26 = min(lows[max(0, n - 25):n + 1])
tk   = (hi9 + lo9) / 2.0
kj   = (hi26 + lo26) / 2.0
i_up = closes[n] > tk and tk > kj
i_dn = closes[n] < tk and tk < kj

# Stochastic
kv, dv = stoch(candles)
kc = kv[-1] if kv else 50.0
dc = dv[-1] if dv else 50.0
st_up = kc > dc and kc < 80
st_dn = kc < dc and kc > 20

# Williams %R
wr    = williams_r(candles)
wr_up = -50 < wr <= -20
wr_dn = -80 <= wr < -50

# ATR volatility filter
av      = atr(candles)
has_vol = (av / closes[n]) * 100.0 > 0.003

# Score
bs  = 0
bes = 0
if t_up:   bs  += 2
if t_dn:   bes += 2
if r_up:   bs  += 1
if r_dn:   bes += 1
if m_up:   bs  += 1
if m_dn:   bes += 1
if b_up:   bs  += 1
if b_dn:   bes += 1
if eg_up:  bs  += 1
if eg_dn:  bes += 1
if pin_up: bs  += 1
if pin_dn: bes += 1
if pv_up:  bs  += 1
if pv_dn:  bes += 1
if i_up:   bs  += 2
if i_dn:   bes += 2
if st_up:  bs  += 2
if st_dn:  bes += 2
if wr_up:  bs  += 2
if wr_dn:  bes += 2

call_ok = bs  >= MIN_SCORE and t_up and r_up and m_up and st_up and not r_ob and has_vol
put_ok  = bes >= MIN_SCORE and t_dn and r_dn and m_dn and st_dn and not r_os and has_vol

return call_ok, put_ok, bs, bes
```

def run():
print(”=” * 50)
print(”  BINARY PRO MAX V5 ULTRA”)
print(”  Pairs    : “ + str(len(PAIRS)))
print(”  Interval : “ + str(CHECK_INTERVAL) + “s”)
print(”  Min Score: “ + str(MIN_SCORE) + “/20”)
print(”=” * 50)

```
send_telegram(
    "*BINARY PRO MAX V5 ULTRA* started!\n"
    + str(len(PAIRS)) + " pairs | every " + str(CHECK_INTERVAL) + "s\n"
    "Min score: " + str(MIN_SCORE) + "/20\n"
    "EMA RSI MACD Stoch WilliamsR ATR Ichimoku"
)

while True:
    now = datetime.now().strftime("%H:%M:%S")
    print("[" + now + "] scanning...")

    for symbol in PAIRS:
        try:
            candles = get_candles(symbol)
            if candles is None or len(candles) < 50:
                time.sleep(1)
                continue

            call_ok, put_ok, bs, bes = analyze(candles)
            price = candles[-1]["c"]
            dp    = 3 if "JPY" in symbol else 5
            key   = symbol.replace("/", "")
            p_str = str(round(price, dp))

            if call_ok and last_signals.get(key) != "CALL":
                print("  CALL " + symbol + " score=" + str(bs) + "/20")
                send_telegram(
                    "CALL SIGNAL\n"
                    + symbol + "\n"
                    "Price: " + p_str + "\n"
                    "Score: " + str(bs) + "/20\n"
                    "Time:  " + now + "\n"
                    "Enter next candle!\n"
                    "BINARY PRO MAX V5"
                )
                last_signals[key] = "CALL"

            elif put_ok and last_signals.get(key) != "PUT":
                print("  PUT  " + symbol + " score=" + str(bes) + "/20")
                send_telegram(
                    "PUT SIGNAL\n"
                    + symbol + "\n"
                    "Price: " + p_str + "\n"
                    "Score: " + str(bes) + "/20\n"
                    "Time:  " + now + "\n"
                    "Enter next candle!\n"
                    "BINARY PRO MAX V5"
                )
                last_signals[key] = "PUT"

            elif not call_ok and not put_ok:
                last_signals[key] = ""

            time.sleep(1)

        except Exception as err:
            print("Error " + symbol + ": " + str(err))
            continue

    time.sleep(CHECK_INTERVAL)
```

if **name** == “**main**”:
run()