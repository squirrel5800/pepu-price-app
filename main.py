import os
import logging
import json
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import CommandHandler, Dispatcher, CallbackContext
import requests
from dotenv import load_dotenv

# === LOAD ENV VARIABLES ===
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME", "pepubot")
PORT = int(os.environ.get('PORT', 10000))
DEXSCREENER_URL = os.getenv("DEXSCREENER_URL", "https://api.dexscreener.com/latest/dex/pairs/ethereum/0x3ebec0a1b4055c8d1180fce64db2a8c068170880")

# === STATE ===
SETTINGS_FILE = "settings.json"
price_floor = None
sell_point = None
alert_percent = None
interval_minutes = None

# === LOAD SETTINGS ON START ===
def load_settings():
    global price_floor, sell_point, alert_percent, interval_minutes
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            price_floor = data.get("price_floor")
            sell_point = data.get("sell_point")
            alert_percent = data.get("alert_percent")
            interval_minutes = data.get("interval_minutes")

def save_settings():
    with open(SETTINGS_FILE, "w") as f:
        json.dump({
            "price_floor": price_floor,
            "sell_point": sell_point,
            "alert_percent": alert_percent,
            "interval_minutes": interval_minutes
        }, f)

# === LOGGING ===
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# === FLASK & TELEGRAM BOT ===
app = Flask(__name__)
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=4, use_context=True)

# === HANDLERS ===
def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Hello from PEPU Bot! Previous settings restored.")

def signal(update: Update, context: CallbackContext):
    price = fetch_price()
    update.message.reply_text(f"📈 Current PEPU Price: ${price:.6f}" if price else "❌ Could not fetch price.")

def fetch_price():
    try:
        res = requests.get(DEXSCREENER_URL).json()
        return float(res['pair']['priceUsd'])
    except:
        return None

def set_floor(update: Update, context: CallbackContext):
    global price_floor
    try:
        price_floor = float(context.args[0])
        save_settings()
        update.message.reply_text(f"📉 Price floor set to ${price_floor}")
    except:
        update.message.reply_text("❌ Usage: /setfloor 0.0012")

def set_sell_point(update: Update, context: CallbackContext):
    global sell_point
    try:
        sell_point = float(context.args[0])
        save_settings()
        update.message.reply_text(f"💰 Sell point set to ${sell_point}")
    except:
        update.message.reply_text("❌ Usage: /setsellpoint 0.0020")

def set_interval(update: Update, context: CallbackContext):
    global interval_minutes
    try:
        interval_minutes = int(context.args[0])
        save_settings()
        update.message.reply_text(f"⏱️ Check interval set to {interval_minutes} minutes.")
    except:
        update.message.reply_text("❌ Usage: /setinterval 15")

def set_alerts(update: Update, context: CallbackContext):
    global alert_percent
    try:
        alert_percent = float(context.args[0])
        save_settings()
        update.message.reply_text(f"🚨 Alert percent change set to {alert_percent}%")
    except:
        update.message.reply_text("❌ Usage: /setalerts 7")

def price(update: Update, context: CallbackContext):
    price = fetch_price()
    try:
        holdings = float(os.getenv("TOKEN_HOLDINGS", 0))
        total_value = holdings * price
        update.message.reply_text(
            f"📈 PEPU Price: ${price:.6f}\n"
            f"📦 Holdings: {int(holdings):,} tokens\n"
            f"💵 Total Value: ${total_value:,.2f}"
        )
    except:
        update.message.reply_text(f"📈 PEPU Price: ${price:.6f}" if price else "❌ Could not fetch price.")

# === REGISTER HANDLERS ===
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("signal", signal))
dispatcher.add_handler(CommandHandler("setfloor", set_floor))
dispatcher.add_handler(CommandHandler("setsellpoint", set_sell_point))
dispatcher.add_handler(CommandHandler("setinterval", set_interval))
dispatcher.add_handler(CommandHandler("setalerts", set_alerts))
dispatcher.add_handler(CommandHandler("price", price))

# === WEBHOOK ENDPOINTS ===
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

@app.route("/", methods=["GET"])
def index():
    return "PEPU Bot is live."

@app.route("/ping")

