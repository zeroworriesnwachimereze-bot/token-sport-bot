import os
import json
import asyncio
from threading import Thread
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
DB_FILE = "db.json"

app = Flask(__name__)

# --- DB ---
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

# --- WEBSITE HTML (No need templates folder) ---
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Token Sport Mining</title>
<script src="https://fpyf8.com/88/tag.min.js" data-zone="180690" async data-cfasync="false"></script>
<style>
body{font-family:Arial;background:#0f172a;color:white;text-align:center;padding:20px}
.card{background:#1e293b;padding:20px;border-radius:15px;max-width:400px;margin:auto}
button{background:#22c55e;color:white;border:none;padding:15px 25px;border-radius:10px;font-size:18px;width:100%;margin-top:10px}
#bal{font-size:32px;color:#facc15}
</style>
</head>
<body>
<div class="card">
<h2>⚽ Token Sport Mining</h2>
<p>Balance: <span id="bal">0</span> Tokens</p>
<p>Ads Watched: <span id="wat">0</span>/10</p>
<button onclick="watchAd()">🎬 Watch Ad +20 Tokens</button>
<p id="msg"></p>
</div>
<script>
let userId = new URLSearchParams(window.location.search).get('user_id') || '0';
async function loadBal(){
  let r = await fetch('/get_balance?user_id='+userId);
  let j = await r.json();
  document.getElementById('bal').innerText=j.balance;
  document.getElementById('wat').innerText=Math.floor(j.balance/20)%10;
}
async function watchAd(){
  if(typeof show_180690 === 'function'){ await show_180690(); }
  else { await new Promise(r=>setTimeout(r,3000)); }
  let res = await fetch('/add_token',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:userId})});
  let data = await res.json();
  document.getElementById('bal').innerText=data.balance;
  document.getElementById('msg').innerText='✅ +20 Tokens Added!';
  loadBal();
}
loadBal();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return HTML_PAGE

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

# --- BOT ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    db = load_db()
    if user_id not in db["users"]:
        db["users"][user_id] = {"balance": 0, "watched": 0}
        save_db(db)
    bal = db["users"][user_id]["balance"]
    web_url = f"https://token-sport-bot-gitb0.onrender.com/?user_id={user_id}"
    keyboard = [[InlineKeyboardButton("🎮 Open Mining Site", url=web_url)]]
    text = f"⚽ Welcome!\n\n💰 Balance: {bal} Tokens\n🎬 Watch Ad = +20 Tokens\n\nClick below:"
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    print("Bot is starting polling...")
    application.run_polling()

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    run_bot()
