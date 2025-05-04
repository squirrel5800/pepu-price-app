import os
import logging
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

# === CONFIG ===
DEXSCREENER_URL = os.getenv("DEXSCREENER_URL", "https://api.dexscreener.com/latest/dex/pairs/ethereum/0x3ebec0a1b4055c8d1180fce64db2a8c068170880")

# === STATE ===
price_floor = None
sell_point = None
alert_percent = None
interval_minutes = None

# === LOGGING ===
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# === FLASK & BOT SETUP ===
app = Flask(__name__)
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=4, use_context=True)

# === COMMAND HANDLERS ===
def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Hello from PEPU Bot! I'm ready to track your token alerts.")

def signal(update: Update, context: CallbackContext):
    price = fetch_price()
    update.messag
