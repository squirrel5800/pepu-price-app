# PEPU Bot with Guided Setup Flow for Mark
import requests
import time
import threading
import logging
from telegram.ext import Updater, CommandHandler

# === CONFIG ===
TELEGRAM_BOT_TOKEN = '7308303366:AAEbl_qKx1UqCZU1OpXwX--IHuFtDJ0liF8'
DEXSCREENER_URL = "https://api.dexscreener.com/latest/dex/pairs/ethereum/0x3ebec0a1b4055c8d1180fce64db2a8c068170880"

# === STATE ===
price_floor = None
sell_point = None
alert_percent = None
interval_minutes = None
floor_check_seconds = 30
last_price = None
chat_id = None
user_id = 7669555692  # Your Telegram ID
bot_running = False
regular_update_timer = None
setup_step = 0  # 0: not started, 1: setfloor, 2: setsell, 3: setalert, 4: setinterval, 5: complete

# === USER HOLDINGS ===
token_holdings = 25473576

# === SETUP ===
logging.basicConfig(level=logging.INFO)
updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

def fetch_price():
    try:
        res = requests.get(DEXSCREENER_URL).json()
        return float(res['pair']['priceUsd'])
    except:
        return None

def floor_alert_loop():
    global last_price
    while bot_running:
        price = fetch_price()
        if not price or not chat_id or setup_step < 5:
            time.sleep(floor_check_seconds)
            continue

        if price_floor and price < price_floor:
            msg = (
                "🚨🚨 *PEPU PRICE DROP!* 🚨🚨\n"
                f"🔻 BELOW FLOOR: ${price_floor:.6f}\n"
                f"💥 CURRENT: ${price:.6f}\n"
                "⛔ TAKE ACTION NOW! ⛔"
            )
            for _ in range(5):
                updater.bot.send_message(chat_id=chat_id, text=msg.upper(), parse_mode='Markdown')
                time.sleep(3)

        if sell_point and price > sell_point:
            msg = (
                "🎉 *PEPU SELL POINT REACHED!* 🎉\n"
                f"✅ ABOVE TARGET: ${sell_point:.6f}\n"
                f"📈 CURRENT: ${price:.6f}\n"
                "🪙 Consider locking in profits 🪙"
            )
            for _ in range(5):
                updater.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
                time.sleep(3)

        time.sleep(floor_check_seconds)

def send_regular_update():
    global last_price, regular_update_timer
    if not chat_id or setup_step < 5:
        return

    price = fetch_price()
    if price is None:
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
    updater.bot.send_message(chat_id=chat_id, text=message)
    regular_update_timer = threading.Timer(interval_minutes * 60, send_regular_update)
    regular_update_timer.start()

# === COMMANDS ===
def start(update, context):
    global chat_id, bot_running, setup_step
    if update.effective_user.id != user_id:
        update.message.reply_text("❌ Unauthorized.")
        return

    chat_id = update.effective_chat.id
    setup_step = 1
    update.message.reply_text(
        "👋 *Hi Mark!* Let's set up your PEPU bot step by step.\n\n"
        "Step 1️⃣: Please set your floor price:\n`/setfloor <price>`",
        parse_mode='Markdown'
    )
    if not bot_running:
        bot_running = True
        threading.Thread(target=floor_alert_loop, daemon=True).start()

# Guided step progressors
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
            update.message.reply_text("Step 2️⃣: Set your sell point:\n`/setsellpoint <price>`", parse_mode='Markdown')
    except:
        update.message.reply_text("⚠️ Usage: /setfloor <price>")

def set_sell_point(update, context):
    global sell_point, setup_step
    if update.effective_user.id != user_id:
        update.message.reply_text("❌ Unauthorized.")
        return
    try:
        sell_point = float(context.args[0])
        update.message.reply_text(f"🚀 Sell point set to ${sell_point:.6f}")
        if setup_step == 2:
            setup_step = 3
            update.message.reply_text("Step 3️⃣: Set alert % threshold:\n`/setalert <percent>`", parse_mode='Markdown')
    except:
        update.message.reply_text("⚠️ Usage: /setsellpoint <price>")

def set_alert(update, context):
    global alert_percent, setup_step
    if update.effective_user.id != user_id:
        update.message.reply_text("❌ Unauthorized.")
        return
    try:
        alert_percent = float(context.args[0])
        update.message.reply_text(f"📉 Alert threshold set to {alert_percent}%")
        if setup_step == 3:
            setup_step = 4
            update.message.reply_text("Step 4️⃣: Set update interval in minutes:\n`/setinterval <minutes>`", parse_mode='Markdown')
    except:
        update.message.reply_text("⚠️ Usage: /setalert <percent>")

def set_interval(update, context):
    global interval_minutes, setup_step, regular_update_timer
    if update.effective_user.id != user_id:
        update.message.reply_text("❌ Unauthorized.")
        return
    try:
        interval_minutes = int(context.args[0])
        update.message.reply_text(f"⏱️ Update interval set to {interval_minutes} minutes.")
        if regular_update_timer:
            regular_update_timer.cancel()
        send_regular_update()
        if setup_step == 4:
            setup_step = 5
            updater.bot.send_message(chat_id=chat_id, text="✅ Setup complete! PEPU bot is now monitoring prices.")
            send_regular_update()
    except:
        update.message.reply_text("⚠️ Usage: /setinterval <minutes>")

# Status and basic commands
def price(update, context):
    if update.effective_user.id != user_id:
        update.message.reply_text("❌ Unauthorized.")
        return
    price = fetch_price()
    if price:
        total_value = price * token_holdings
        update.message.reply_text(
            f"💰 Current PEPU Price: ${price:.6f}\n"
            f"📦 Holdings: {token_holdings:,} tokens\n"
            f"💵 Total Value: ${total_value:,.2f}"
        )
    else:
        update.message.reply_text("❌ Could not fetch price.")

def status(update, context):
    update.message.reply_text(
        f"📊 Bot Status:\n"
        f"Floor: {price_floor}\nSell: {sell_point}\nAlert %: {alert_percent}\nInterval: {interval_minutes} min\nStep: {setup_step}/5"
    )

# Register handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("price", price))
dispatcher.add_handler(CommandHandler("status", status))
dispatcher.add_handler(CommandHandler("setfloor", set_floor))
dispatcher.add_handler(CommandHandler("setsellpoint", set_sell_point))
dispatcher.add_handler(CommandHandler("setalert", set_alert))
dispatcher.add_handler(CommandHandler("setinterval", set_interval))

# Start polling
updater.start_polling()
updater.idle()
