import time
import urllib.request
import json
from datetime import datetime
import os

BOT_TOKEN = os.environ.get(“TELEGRAM_TOKEN”, “”)
CHAT_ID = os.environ.get(“CHAT_ID”, “”)
TWELVE_KEY = os.environ.get(“TWELVE_API_KEY”, “”)
MIN_SCORE = 8
CHECK_INTERVAL = 30

PAIRS = [
“EUR/USD”,“GBP/USD”,“USD/JPY”,“AUD/USD”,“USD/CAD”,
“USD/CHF”,“NZD/USD”,“EUR/GBP”,“EUR/JPY”,“GBP/JPY”,
“AUD/JPY”,“EUR/AUD”,“EUR/CHF”,“GBP/CHF”,“CAD/JPY”,
“AUD/CAD”,“AUD/CHF”,“AUD/NZD”,“CAD/CHF”,“CHF/JPY”,
“GBP/AUD”,“GBP/CAD”,“GBP/NZD”,“EUR/CAD”,“EUR/NZD”,
]

last_signals = {}

def send_telegram(message):
url = “https://api.telegram.org/bot” + BOT_TOKEN + “/sendMessage”
data = json.dumps({“chat_id”: CHAT_ID, “text”: message, “parse_mode”: “Markdown”}).encode()
try:
req = urllib.request.Request(url, data, {“Content-Type”: “application/json”})
urllib.request.urlopen(req, timeout=10)
except Exception as e:
print(“Telegram Error: “ + str(e))

def get_candles(symbol, outputsize=100):
sym = symbol.replace(”/”, “”)
url = “https://api.twelvedata.com/time_series?symbol=” + sym + “&interval=1min&outputsize=” + str(outputsize) + “&apikey=” + TWELVE_KEY
try:
res = urllib.request.urlopen(url, timeout=10)
data = json.loads(res.read())
if “values” not in data:
print(“No data “ + symbol)
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
except Exception as e:
print(“API Error “ + symbol + “: “ + str(e))
return None

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
gains, losses = 0.0, 0.0
for i in range(1, period + 1):
d = closes[i] - closes[i-1]
if d > 0:
gains += d
else:
losses -= d
avg_gain = gains / period
avg_loss = losses / period
for i in range(period + 1, len(closes)):
d = closes[i] - closes[i-1]
avg_gain = (avg_gain * (period-1) + max(d, 0)) / period
avg_loss = (avg_loss * (period-1) + max(-d, 0)) / period
rs = avg_gain / (avg_loss if avg_loss > 0 else 1e-9)
return 100 - (100 / (1 + rs))

def calc_macd(closes):
fast = ema(closes, 12)
slow = ema(closes, 26)
line = [f - s for f, s in zip(fast, slow)]
signal = ema(line, 9)
hist = [l - s for l, s in zip(line, signal)]
return line, signal, hist

def calc_stochastic(candles, kp=14, dp=3):
ks = []
for i in range(len(candles)):
if i < kp - 1:
ks.append(None)
continue
hi = max(c[“h”] for c in candles[i-kp+1:i+1])
lo = min(c[“l”] for c in candles[i-kp+1:i+1])
cl = candles[i][“c”]
if hi != lo:
ks.append((cl - lo) / (hi - lo) * 100.0)
else:
ks.append(50.0)
valid = [v for v in ks if v is not None]
ds = sma(valid, dp)
return valid, ds

def calc_atr(candles, period=14):
trs = []
for i in range(1, len
