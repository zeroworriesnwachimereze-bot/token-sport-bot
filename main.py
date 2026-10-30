import os, json, asyncio, time
from threading import Thread
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN=os.environ.get("BOT_TOKEN")
ADMIN_ID=int(os.environ.get("ADMIN_ID","0"))
DB_FILE="db.json"
app=Flask(__name__)

def load_db():
    if not os.path.exists(DB_FILE): return {"users":{}}
    try:
        with open(DB_FILE,"r") as f: return json.load(f)
    except: return {"users":{}}
def save_db(d):
    with open(DB_FILE,"w") as f: json.dump(d,f)

HTML_PAGE = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Token Mining</title>
<script src="https://fpyf8.com/88/tag.min.js" data-zone="180690" async data-cfasync="false"></script>
<style>body{font-family:Arial;background:#0f172a;color:white;text-align:center;padding:20px}.card{background:#1e293b;padding:20px;border-radius:15px;max-width:400px;margin:auto}button{background:#22c55e;color:white;border:none;padding:15px 25px;border-radius:10px;width:100%;font-size:18px;margin-top:15px}#bal{font-size:32px;color:#facc15}</style>
</head><body><div class="card"><h2>⚽ Token Sport Mining</h2><p>Balance: <span id="bal">0</span> Tokens</p><p>5 Ads = 200 Tokens</p><button onclick="watchAd()">🎬 Watch Ad +40 Tokens</button><p id="msg" style="color:#22c55e;margin-top:10px"></p></div>
<script>
let uid=new URLSearchParams(location.search).get('user_id')||'0';
async function loadBal(){try{let r=await fetch('/get_balance?user_id='+uid);let j=await r.json();document.getElementById('bal').innerText=j.balance}catch(e){}}
async function watchAd(){
  try{if(typeof show_180690==='function'){await show_180690()}else{await new Promise(r=>setTimeout(r,3000))}}catch(e){}
  let res=await fetch('/add_token',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:uid})});
  let d=await res.json();document.getElementById('bal').innerText=d.balance;document.getElementById('msg').innerText='✅ +40 Added!';
}
loadBal();
</script></body></html>"""

@app.route("/")
def index(): return HTML_PAGE
@app.route("/<path:anything>")
def catch(anything): return HTML_PAGE
@app.errorhandler(404)
def nf(e): return HTML_PAGE

@app.route("/add_token",methods=["POST"])
def add_token():
    data=request.json; uid=str(data.get("user_id")); db=load_db()
    if uid not in db["users"]: db["users"][uid]={"balance":0}
    db["users"][uid]["balance"]+=40; save_db(db)
    return jsonify({"ok":True,"balance":db["users"][uid]["balance"]})
@app.route("/get_balance")
def get_balance():
    uid=str(request.args.get("user_id")); db=load_db()
    return jsonify({"balance":db["users"].get(uid,{}).get("balance",0)})

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    uid=str(update.effective_user.id); db=load_db()
    if uid not in db["users"]: db["users"][uid]={"balance":0}; save_db(db)
    bal=db["users"][uid]["balance"]; url=f"https://token-sport-bot-gitb0.onrender.com/?user_id={uid}"
    kb=[[InlineKeyboardButton("🎮 Open Mining Site",url=url)]]
    await update.message.reply_text(f"⚽ Welcome!\n\n💰 Balance: {bal}\n🎬 Watch Ad = +40 Tokens\n💡 5 Ads = 200 Tokens",reply_markup=InlineKeyboardMarkup(kb))
async def admin(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not admin"); return
    db=load_db(); users=len(db["users"]); total=sum(u.get("balance",0) for u in db["users"].values())
    await update.message.reply_text(f"👑 Admin\n👥 Users: {users}\n💰 Total: {total}\nPer Ad: 40")

def run_bot():
    while True:
        try:
            loop=asyncio.new_event_loop(); asyncio.set_event_loop(loop)
            application=Application.builder().token(BOT_TOKEN).build()
            application.add_handler(CommandHandler("start",start))
            application.add_handler(CommandHandler("admin",admin))
            print("Bot polling...")
            application.run_polling(drop_pending_updates=True)
        except Exception as e:
            print(f"Bot error {e}, retry 5s..."); time.sleep(5)

if __name__=="__main__":
    Thread(target=run_bot,daemon=True).start()
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)),use_reloader=False)
