import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime
from config import TOKEN, CHAT_ID

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

def calcular_RSI(df, period=14):
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def detectar_ruptura_tendencia(df, periodos=5):
    highs = df['High'].rolling(window=periodos).max()
    tendencia = highs.shift(1)
    precio_actual = df['Close'].iloc[-1]
    if precio_actual > tendencia.iloc[-1]:
        return True
    return False

def get_signal(symbol="XAUUSD=X", ema_short=9, ema_long=21):
    df = yf.download(symbol, interval="1h", period="7d")
    df.dropna(inplace=True)

    df['EMA_short'] = df['Close'].ewm(span=ema_short).mean()
    df['EMA_long'] = df['Close'].ewm(span=ema_long).mean()
    df = calcular_RSI(df)

    curr = df.iloc[-1]
    prev = df.iloc[-2]

    # Condiciones
    cruza_alcista = prev.EMA_short < prev.EMA_long and curr.EMA_short > curr.EMA_long
    cruce_bajista = prev.EMA_short > prev.EMA_long and curr.EMA_short < curr.EMA_long
    ruptura = detectar_ruptura_tendencia(df)
    rsi_valido = curr['RSI'] < 70 and curr['RSI'] > 30

    entry = curr['Close']
    sl = entry * 0.99
    tp1 = entry * 1.01
    tp2 = entry * 1.02
    tp3 = entry * 1.03

    signal = "⏸ Sin señal clara"
    if cruza_alcista and ruptura and rsi_valido:
        signal = "🟢 Entrada LARGA"
    elif cruce_bajista and ruptura and rsi_valido:
        signal = "🔴 Entrada CORTA"

    mensaje = f"""
📈 Señal para: {symbol}
🕒 Hora: {datetime.now().strftime('%Y-%m-%d %H:%M')}
💵 Precio actual: {round(entry, 2)}
📊 Señal: {signal}
📉 RSI: {round(curr['RSI'], 2)}
🛑 SL: {round(sl, 2)}
🎯 TP1: {round(tp1, 2)}
🎯 TP2: {round(tp2, 2)}
🎯 TP3: {round(tp3, 2)}
"""
    return mensaje

# Ejecutar señales para una lista de activos
symbols = ["XAUUSD=X", "BTC-USD", "ETH-USD"]
for symbol in symbols:
    mensaje = get_signal(symbol)
    send_telegram(mensaje)
    print(f"✅ Señal enviada para {symbol}")
