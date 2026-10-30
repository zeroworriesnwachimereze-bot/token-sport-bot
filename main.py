import os
import json
import asyncio
from threading import Thread
from flask import Flask, render_template, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
DB_FILE = "db.json"

app = Flask(__name__)

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "withdraws": []}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "withdraws": []}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# --- Flask Routes ---
@app.route("/")
def index():
    user_id = request.args.get("user_id", "0")
    db = load_db()
    balance = db["users"].get(str(user_id), {}).get("balance", 0)
    return render_template("index.html", balance=balance, user_id=user_id)

@app.route("/add_token", methods=["POST"])
def add_token():
    data = request.json
    user_id = str(data.get("user_id"))
    db = load_db()
    if user_id not in db["users"]:
        db["users"][user_id] = {"balance": 0, "watched": 0}
    db["users"][user_id]["balance"] += 20
    db["users"][user_id]["watched"] += 1
    save_db(db)
    return jsonify({"ok": True, "balance": db["users"][user_id]["balance"]})

@app.route("/get_balance")
def get_balance():
    user_id = str(request.args.get("user_id"))
    db = load_db()
    bal = db["users"].get(user_id, {}).get("balance", 0)
    return jsonify({"balance": bal})

# --- Telegram Bot ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    db = load_db()
    if user_id not in db["users"]:
        db["users"][user_id] = {"balance": 0, "watched": 0}
        save_db(db)
    
    bal = db["users"][user_id]["balance"]
    url = f"https://{request.host if False else 'token-sport-bot-gitb0.onrender.com'}?user_id={user_id}"
    # Use your render URL
    web_url = f"https://token-sport-bot-gitb0.onrender.com/?user_id={user_id}"
    
    keyboard = [[InlineKeyboardButton("🎮 Open Mining Site", url=web_url)]]
    text = f"⚽ Welcome to Token Sport Bot!\n\n💰 Balance: {bal} Tokens\n🎬 Watch 10 ads = 200 Tokens\n\nClick below to start mining:"
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    db = load_db()
    bal = db["users"].get(user_id, {}).get("balance", 0)
    await update.message.reply_text(f"💰 Your balance: {bal} Tokens")

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

async def run_bot_async():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance_cmd))
    print("Bot is starting polling...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.idle()

def run_bot():
    asyncio.run(run_bot_async())

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    run_bot()
