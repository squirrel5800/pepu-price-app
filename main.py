import os
import time
import threading
import logging
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, CallbackContext
from dotenv import load_dotenv

# === LOAD ENV ===
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DEXSCREENER_URL = os.getenv("DEXSCREENER_URL")
USER_ID = int(os.getenv("USER_ID"))
TOKEN_HOLDINGS = float(os.getenv("TOKEN_HOLDINGS", 0))

# === GLOBALS ===
price_floor = None
sell_point = None
interval_minutes = 1
alert_percent = None
last_checked_price = None

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === FLASK + TELEGRAM ===
app = Flask(__name__)
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=4, use_context=True)

# === PRICE FETCH ===
def fetch_price():
    try:
        res = requests.get(DEXSCREENER_URL).json()
        return float(res['pair']['priceUsd'])
    except:
        return None

# === COMMANDS ===
def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Hello from PEPU Bot!")

def price(update: Update, context: CallbackContext):
    price = fetch_price()
    if price:
        total = TOKEN_HOLDINGS * price
        update.message.reply_text(
            f"📈 PEPU Price: ${price:.6f}\n"
            f"📦 Holdings: {int(TOKEN_HOLDINGS):,} tokens\n"
            f"💵 Total Value: ${total:,.2f}"
        )
    else:
        update.message.reply_text("❌ Could not fetch price.")

def set_floor(update: Update, context: CallbackContext):
    global price_floor
    try:
        price_floor = float(context.args[0])
        update.message.reply_text(f"📉 Price floor set to ${price_floor}")
    except:
        update.message.reply_text("❌ Usage: /setfloor 0.0012")

def set_sell_point(update: Update, context: CallbackContext):
    global sell_point
    try:
        sell_point = float(context.args[0])
        update.message.reply_text(f"💰 Sell point set to ${sell_point}")
    except:
        update.message.reply_text("❌ Usage: /setsellpoint 0.005")

def set_interval(update: Update, context: CallbackContext):
    global interval_minutes
    try:
        interval_minutes = int(context.args[0])
        update.message.reply_text(f"⏱️ Check interval set to {interval_minutes} minutes.")
    except:
        update.message.reply_text("❌ Usage: /setinterval 5")

def set_alerts(update: Update, context: CallbackContext):
    global alert_percent
    try:
        alert_percent = float(context.args[0])
        update.message.reply_text(f"🚨 Alert percent change set to {alert_percent}%")
    except:
        update.message.reply_text("❌ Usage: /setalerts 7")

# === BACKGROUND CHECK ===
def price_watcher():
    global last_checked_price
    while True:
        time.sleep(interval_minutes * 60)
        price = fetch_price()
        if not price:
            continue
        try:
            if price_floor and price < price_floor:
                bot.send_message(chat_id=USER_ID, text=f"⚠️ Price dropped below floor: ${price:.6f}")
            if sell_point and price > sell_point:
                bot.send_message(chat_id=USER_ID, text=f"🚀 Price above sell point: ${price:.6f}")
            if alert_percent and last_checked_price:
                change = abs((price - last_checked_price) / last_checked_price) * 100
                if change >= alert_percent:
                    icon = "📈" if price > last_checked_price else "📉"
                    bot.send_message(chat_id=USER_ID, text=f"{icon} Price changed {change:.2f}% to ${price:.6f}")
            last_checked_price = price
        except Exception as e:
            print("Watcher error:", e)

# === THREAD START ===
threading.Thread(target=price_watcher, daemon=True).start()

# === ROUTES ===
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/", methods=["GET"])
def root():
    return "PEPU Bot is live."

@app.route("/ping", methods=["GET"])
def ping():
    return "pong", 200

@app.before_first_request
def setup_webhook():
    bot.delete_webhook()
    bot.set_webhook(url=f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/{TOKEN}")

# === COMMAND HANDLERS ===
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("price", price))
dispatcher.add_handler(CommandHandler("setfloor", set_floor))
dispatcher.add_handler(CommandHandler("setsellpoint", set_sell_point))
dispatcher.add_handler(CommandHandler("setinterval", set_interval))
dispatcher.add_handler(CommandHandler("setalerts", set_alerts))

# === RUN APP ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
