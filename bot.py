import telebot
import requests
import json
import os
import datetime
import qrcode
import secrets
import base64
from io import BytesIO
from flask import Flask
from threading import Thread

# --- CONFIG ---
API_TOKEN = '8746522340:AAHWK-qbfQ2GW0FiPo5f1iF8X45H9nGQ8ro'
ADMIN_ID = 1753188343
bot = telebot.TeleBot(API_TOKEN)

# --- KEEP ALIVE ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Running!"
def run_web(): app.run(host='0.0.0.0', port=10000)

# --- KEYGEN & HANDLERS ---
# (အရင်ပေးထားတဲ့ Code ထဲကအတိုင်း Keygen အပိုင်းကို ဒီမှာ ထည့်ထားပေးပါမယ်)
def generate_keys():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import x25519
    priv_key = x25519.X25519PrivateKey.generate()
    pub_key = priv_key.public_key()
    priv_b64 = base64.b64encode(priv_key.private_bytes(encoding=serialization.Encoding.Raw, format=serialization.PrivateFormat.Raw, encryption_algorithm=serialization.NoEncryption())).decode()
    pub_b64 = base64.b64encode(pub_key.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)).decode()
    return priv_b64, pub_b64

def get_warp_config(priv, pub):
    install_id = secrets.token_hex(11)
    body = {"key": pub, "install_id": install_id, "fcm_token": f"{install_id}:APA91b{secrets.token_urlsafe(67)}", "tos": datetime.datetime.now().isoformat() + "Z", "model": "Android", "type": "Android", "locale": "en_US"}
    headers = {"User-Agent": "okhttp/3.12.1", "Content-Type": "application/json; charset=UTF-8"}
    try:
        res = requests.post("https://api.cloudflareclient.com/v0a884/reg", json=body, headers=headers, timeout=15)
        if res.status_code == 200:
            d = res.json()
            config = f"[Interface]\nPrivateKey = {priv}\nAddress = {d['config']['interface']['addresses']['v4']}/32\nAddress = {d['config']['interface']['addresses']['v6']}/128\nDNS = 1.1.1.1, 1.0.0.1\nMTU = 1280\n\n[Peer]\nPublicKey = {d['config']['peers'][0]['public_key']}\nAllowedIPs = 0.0.0.0/0\nAllowedIPs = ::/0\nEndpoint = 162.159.192.1:500"
            return config
    except: return None

@bot.message_handler(commands=['start'])
def start(m):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🔑 Get WireGuard Key", callback_data="gen"))
    bot.send_message(m.chat.id, "ဟယ်လို! Render Server ကနေ အလုပ်လုပ်နေပါပြီ။", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "gen")
def handle_gen(call):
    bot.edit_message_text("⏳ Generating...", call.message.chat.id, call.message.message_id)
    priv, pub = generate_keys()
    config = get_warp_config(priv, pub)
    if config:
        qr = qrcode.make(config)
        qr_io = BytesIO(); qr.save(qr_io, 'PNG'); qr_io.seek(0)
        bot.send_photo(call.message.chat.id, qr_io, caption="📸 Scan with WireGuard")
    else:
        bot.send_message(call.message.chat.id, "❌ Error. Try again later.")

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.infinity_polling()
