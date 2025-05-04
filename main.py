import requests
import time
import threading
import logging
from telegram.ext import Updater, CommandHandler, CallbackContext
from flask import Flask
from threading import Thread
import traceback

# === CONFIG ===
TELEGRAM_BOT_TOKEN = "7308303366:AAH7F9WYzAgO59xM5YrbqlwlD--Zqj8uf3I"
DEXSCREENER_URL = "https://api.dexscreener.com/latest/dex/pairs/ethereum/0x3ebec0a1b4055c8d1180fce64db2a8c068170880"
user_id = 7669555692  # Your Telegram ID
token_holdings = 25473576

# === STATE ===
price_floor = None
sell_point = None
alert_percent = None
interval_minutes = None
floor_check_seconds = 30
last_price = None
chat_id = None
bot_running = False
regular_update_timer = None
setup_step = 0

# === PRICE FETCH ===
def fetch_price():
    try:
        res = requests.get(DEXSCREENER_URL).json()
        return float(res['pair']['priceUsd'])
    except:
        return None

# === ALERTS LOOP ===
def floor_alert_loop():
    global last_price
    while bot_running:
        price = fetch_price()
        if not price or not chat_id:
            time.sleep(floor_check_seconds)
            continue

        if sell_point and price > sell_point:
            msg = (
                "🎉 *PEPU SELL POINT REACHED!* 🎉\n"
                f"✅ ABOVE TARGET: ${sell_point:.6f}\n"
                f"📈 CURRENT: ${price:.6f}\n"
                "🪙 Consider locking in profits 🪙"
            )
            for _ in range(5):
                try:
                    updater.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
                except Exception as e:
                    print("Error sending sell alert:", e)
                time.sleep(3)

        if price_floor and price < price_floor:
            msg = (
                "🚨 *PEPU FLOOR BREACHED!* 🚨\n"
                f"❌ BELOW FLOOR: ${price_floor:.6f}\n"
                f"📉 CURRENT: ${price:.6f}\n"
                "⚠️ Watch closely or consider action"
            )
            for _ in range(5):
                try:
                    updater.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
                except Exception as e:
                    print("Error sending floor alert:", e)
                time.sleep(3)

        time.sleep(floor_check_seconds)

# === REGULAR PRICE UPDATE ===
def send_regular_update():
    global last_price, regular_update_timer
    print("🌀 Running send_regular_update...")

    if not chat_id:
        print("⚠️ No chat_id set. Skipping update.")
        return

    price = fetch_price()
    if price is None:
        print("⚠️ Could not fetch price.")
        return

    total_value = price * token_holdings
    message = (
        f"📈 PEPU Price: ${price:.6f}\n"
        f"📦 Holdings: {token_holdings:,} tokens\n"
        f"💵 Total Value: ${total_value:,.2f}"
    )

    if last_price:
        change = ((price - last_price) / last_price) * 100
        if alert_percent and abs(change) >= alert_percent:
            message += f"\n🚨 Price moved {change:.2f}% from ${last_price:.6f}"

    last_price = price

    try:
        updater.bot.send_message(chat_id=chat_id, text=message)
        print("✅ Sent regular update.")
    except Exception as e:
        print("❌ Error sending update:", e)

    regular_update_timer = threading.Timer(interval_minutes * 60, send_regular_update)
    regular_update_timer.start()

# === COMMANDS ===
def start(update, context):
    global chat_id, setup_step, bot_running
    if update.effective_user.id != user_id:
        update.message.reply_text("❌ Unauthorized.")
        return
    chat_id = update.effective_chat.id
    update.message.reply_text("👋 Hi Mark! Let's set up your PEPU bot.\nStep 1️⃣: Set your floor price using /setfloor <price>")
    setup_step = 1
    if not bot_running:
        bot_running = True
        threading.Thread(target=floor_alert_loop, daemon=True).start()

def set_floor(update, context):
    global price_floor, setup_step
    if update.effective_user.id != user_id:
        update.message.reply_text("❌ Unauthorized.")
        return
    try:
        price_floor = float(context.args[0])
        update.message.reply_text(f"🛑 Floor price set to ${price_floor:.6f}")
        if setup_step == 1:
            setup_step = 2
            update.message.reply_text("Step 2️⃣: Set your sell point using /setsellpoint <price>")
    except:
        update.message.re
