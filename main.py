import ccxt
import pandas as pd
import time
import requests
from flask import Flask
from threading import Thread

# Flask Web Server အသေးစားလေး တည်ဆောက်ခြင်း
app = Flask('')

@app.route('/')
def home():
    return "SOL 50x Micro Bot Is Alive and Running!"

def keep_alive():
    # Render ၏ Port အတွက် အလိုအလျောက် ပတ်ပေးမည့် စနစ်
    app.run(host='0.0.0.0', port=8080)

# ==========================================
# သင့်ရဲ့ API Keys များနှင့် Telegram အချက်အလက်များ ဖြည့်ပါ
# ==========================================
BINANCE_API_KEY = 'lOr2DkSKLA87uwksfJVdd0za7ZVQRmyicGWGPEGudODEAyrEQkcslpafTppj1ayx'
‎BINANCE_SECRET_KEY = 'PfYwxkPmp6OiIlojhBoR2ruq88Nn5jbvfMo7f1JI5'
‎TELEGRAM_TOKEN = '8389921513:AAHA5BN15MACWXlF7fKR'
‎TELEGRAM_CHAT_ID = '5063276801'

SYMBOL = 'SOL/USDT'
TIMEFRAME = '5m'
MARGIN_USDT = 0.2
LEVERAGE = 50

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try: requests.post(url, json=payload)
    except Exception as e: print(f"Telegram Error: {e}")

# Binance Futures ချိတ်ဆက်ခြင်း
exchange = ccxt.binance({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_SECRET_KEY,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

try:
    exchange.set_leverage(LEVERAGE, SYMBOL)
    print(f"✅ Leverage {LEVERAGE}x သတ်မှတ်ပြီးပါပြီ!")
except Exception as e:
    print(f"Leverage Error: {e}")

current_position = None

def get_market_data():
    bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=150)
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['MA19'] = df['close'].rolling(window=19).mean()
    df['MA29'] = df['close'].rolling(window=29).mean()
    df['MA119'] = df['close'].rolling(window=119).mean()
    return df

def run_bot():
    global current_position
    df = get_market_data()
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    
    price = last_row['close']
    ma19 = last_row['MA19']
    ma29 = last_row['MA29']
    ma119 = last_row['MA119']
    
    position_size_usdt = MARGIN_USDT * LEVERAGE
    trade_amount = round(position_size_usdt / price, 2)
    
    is_buy_cross = (prev_row['MA19'] <= prev_row['MA29']) and (ma19 > ma29)
    is_sell_cross = (prev_row['MA19'] >= prev_row['MA29']) and (ma19 < ma29)
    
    print(f"[{time.strftime('%H:%M:%S')}] Price: {price:.2f} | MA119: {ma119:.2f}")

    if price < ma119:
        if is_sell_cross and current_position is None:
            exchange.create_market_sell_order(SYMBOL, trade_amount)
            current_position = 'short'
            send_telegram(f"📉 [SHORT ENTRY] SOL Short ဝင်လိုက်ပါပြီ!\nစျေးနှုန်း: {price} USDT")
        elif is_buy_cross and current_position == 'short':
            exchange.create_market_buy_order(SYMBOL, trade_amount)
            current_position = None
            send_telegram(f"✅ [CLOSE SHORT] Short အော်ဒါ ပိတ်လိုက်ပါပြီ!")

    elif price > ma119:
        if is_buy_cross and current_position is None:
            exchange.create_market_buy_order(SYMBOL, trade_amount)
            current_position = 'long'
            send_telegram(f"📈 [LONG ENTRY] SOL Long ဝင်လိုက်ပါပြီ!\nစျေးနှုန်း: {price} USDT")
        elif is_sell_cross and current_position == 'long':
            exchange.create_market_sell_order(SYMBOL, trade_amount)
            current_position = None
            send_telegram(f"✅ [CLOSE LONG] Long အော်ဒါ ပိတ်လိုက်ပါပြီ!")

# Trading Loop ကို သီးသန့်မောင်းနှင်မည့် Function
def bot_loop():
    send_telegram("🚀 SOL 50x Render Bot စတင်လည်ပတ်ပါပြီ!")
    while True:
        try:
            run_bot()
            time.sleep(60)
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    # ၁။ Web Server ကို Background တွင် အလုပ်လုပ်ခိုင်းခြင်း
    t = Thread(target=keep_alive)
    t.start()
    
    # ၂။ Trading Bot Loop ကို မောင်းနှင်ခြင်း
    bot_loop()
