from flask import Flask, request
import requests
import json
import os
import time
import hmac
import hashlib
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
BITUNIX_API_KEY = os.getenv("BITUNIX_API_KEY")
BITUNIX_API_SECRET = os.getenv("BITUNIX_API_SECRET")

DATA_FILE = "operaciones.json"
PRECIOS_FILE = "ultimos_precios.json"

if not TELEGRAM_TOKEN or not BITUNIX_API_KEY or not BITUNIX_API_SECRET:
    raise ValueError("Debes definir TELEGRAM_TOKEN, BITUNIX_API_KEY y BITUNIX_API_SECRET en las variables de entorno.")

operaciones_abiertas = {}
ultimos_precios = {}

def cargar_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

def guardar_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def send_telegram_message_with_button(text, chat_id, button_text, callback_data):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [[{"text": button_text, "callback_data": callback_data}]]
    }
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(keyboard)
    }
    try:
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error enviando mensaje a Telegram: {e}")

def send_telegram_message(text, chat_id=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id if chat_id else CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error enviando mensaje a Telegram: {e}")

def bitunix_headers(path, method, body=""):
    timestamp = str(int(time.time() * 1000))
    prehash = f"{timestamp}{method}{path}{body}"
    signature = hmac.new(
        BITUNIX_API_SECRET.encode(),
        prehash.encode(),
        hashlib.sha256
    ).hexdigest()
    return {
        "BITUNIX-API-KEY": BITUNIX_API_KEY,
        "BITUNIX-API-TIMESTAMP": timestamp,
        "BITUNIX-API-SIGN": signature,
        "Content-Type": "application/json"
    }

def bitunix_close_order(symbol, side):
    path = "/api/v1/order"
    url = "https://api.bitunix.com" + path
    data = {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "reduceOnly": True
    }
    body = json.dumps(data)
    headers = bitunix_headers(path, "POST", body)
    try:
        resp = requests.post(url, headers=headers, data=body)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error ejecutando orden de cierre en Bitunix: {e}")
        return None

operaciones_abiertas = cargar_json(DATA_FILE)
ultimos_precios = cargar_json(PRECIOS_FILE)

# Webhook de TradingView
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data:
        return {"status": "error", "msg": "No JSON"}, 400

    ticker = data.get("ticker", "CRYPTO?")
    signal = data.get("signal", "").upper()
    extra = data.get("extra", "")
    precio_actual = float(data.get("price", 0))

    ultimos_precios[ticker] = precio_actual
    guardar_json(PRECIOS_FILE, ultimos_precios)

    mensaje = (
        f"📢 Señal detectada\n"
        f"🪙 <b>{ticker}</b>\n"
        f"📈 Señal: <b>{signal}</b>\n"
        f"{extra}"
    )

    # Si hay operación abierta y la señal es contraria, cerrar automáticamente
    if ticker in operaciones_abiertas:
        tipo_abierto = operaciones_abiertas[ticker]["signal"]
        precio_entrada = operaciones_abiertas[ticker]["precio_entrada"]

        if tipo_abierto != signal:
            # Ejecutar orden de cierre en Bitunix
            side = "SELL" if tipo_abierto == "LONG" else "BUY"
            resultado = bitunix_close_order(ticker, side)
            # Calcular PnL (solo informativo, ya que no hay tamaño)
            if tipo_abierto == "LONG":
                pnl = precio_actual - precio_entrada
            else:
                pnl = precio_entrada - precio_actual

            color = "🟢" if pnl > 0 else "🔴"
            estado = "GANANCIA" if pnl > 0 else "PÉRDIDA"
            send_telegram_message(
                f"{color} <b>OPERACIÓN CERRADA AUTOMÁTICAMENTE</b>\n"
                f"🪙 <b>{ticker}</b>\n"
                f"Tipo: <b>{tipo_abierto}</b>\n"
                f"Precio entrada: <b>{precio_entrada}</b>\n"
                f"Precio cierre: <b>{precio_actual}</b>\n"
                f"<b>{estado}</b> PnL: <b>{pnl:.4f}</b>"
            )
            if resultado and resultado.get("success"):
                send_telegram_message(f"🔄 Orden de cierre ejecutada en Bitunix para {ticker}")
            else:
                send_telegram_message(f"⚠️ Error cerrando operación en Bitunix para {ticker}")

            del operaciones_abiertas[ticker]
            guardar_json(DATA_FILE, operaciones_abiertas)
        else:
            send_telegram_message(mensaje)
    else:
        # Si no hay operación abierta, enviar botón para abrir (registrar)
        button_text = f"/abrir {ticker} {signal}"
        callback_data = f"abrir|{ticker}|{signal}|{precio_actual}|{extra}"
        send_telegram_message_with_button(mensaje, CHAT_ID, button_text, callback_data)

    return {"status": "ok"}, 200

# Endpoint para manejar el botón /abrir (callback_query)
@app.route(f"/{TELEGRAM_TOKEN}", methods=['POST'])
def recibir_telegram():
    data = request.get_json()
    # Si es un callback_query (botón)
    if "callback_query" in data:
        callback = data["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        data_parts = callback["data"].split("|")
        if data_parts[0] == "abrir":
            cripto, signal, precio_entrada, extra = data_parts[1], data_parts[2], float(data_parts[3]), data_parts[4]
            operaciones_abiertas[cripto] = {
                "ticker": cripto,
                "signal": signal,
                "precio_entrada": precio_entrada,
                "extra": extra
            }
            guardar_json(DATA_FILE, operaciones_abiertas)
            send_telegram_message(
                f"✅ Operación registrada:\n"
                f"🪙 <b>{cripto}</b>\n"
                f"Tipo: <b>{signal}</b>\n"
                f"Precio entrada: <b>{precio_entrada}</b>\n"
                f"{extra}",
                chat_id
            )
        # Responde al callback para quitar el "relojito" de Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
        requests.post(url, json={"callback_query_id": callback["id"]})
        return {"status": "ok"}, 200

    return {"status": "ok"}, 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
