import os
import json
import time
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask, request, render_template_string, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
DATA_FILE = "users.json"
WITHDRAW_FILE = "withdraws.json"

app = Flask(__name__)

def load_json(file):
    if not os.path.exists(file): return {}
    try:
        with open(file,'r') as f: return json.load(f)
    except: return {}
def save_json(file,data):
    with open(file,'w') as f: json.dump(f,data,indent=2)

users = load_json(DATA_FILE)
withdraws = load_json(WITHDRAW_FILE)

HTML_PAGE = """<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Token Mining</title>
<script src="//libtl.com/sdk.js" data-zone="11950872" data-sdk="show_11950872"></script>
<style>body{background:#0f0f0f;color:#fff;font-family:Arial;text-align:center;padding:20px}
.card{background:#1a1a1a;padding:20px;border-radius:15px;margin:15px 0}
button{background:#00d084;color:#000;padding:15px 25px;border:none;border-radius:10px;font-weight:bold;width:100%;margin:10px 0}
input,select{padding:12px;width:90%;border-radius:8px;border:none;margin:8px 0}</style>
</head><body>
<h2>⛏️ TOKEN MINING BOT</h2>
<div class="card"><p>Username: <b>{{username}}</b></p><p>Balance: <b>{{balance}} TOKEN</b></p>
<p>Ads Watched: {{ads}}/10</p><p id="timer">{{timer_msg}}</p></div>
<div class="card"><button onclick="watchAd()">📺 WATCH AD ({{ads}}/10)</button>
<button onclick="claim()">💰 CLAIM 200 TOKEN</button>
<p><small>10 Ads = 2hrs = 200 TOKEN<br>12,000 in 5 Days</small></p></div>
<div class="card"><h3>💸 WITHDRAW</h3><p>Min: 12,000 | Network: BEP20</p>
<input id="wallet" placeholder="BEP20 Wallet Address (0x...)">
<select id="network"><option value="BEP20">BEP20 (BSC)</option></select>
<input id="amount" type="number" placeholder="Amount e.g. 12000">
<button onclick="withdraw()">REQUEST WITHDRAW</button>
<p>Referral Username: <b>{{ref_username}}</b></p></div>
<div class="card"><p>Referral Link:<br><small>https://t.me/{{bot_username}}?start={{user_id}}</small></p>
<p>Referrals: {{referrals}} | Bonus: {{ref_bonus}} TOKEN</p></div>
<script>
let userId="{{user_id}}";
function watchAd(){show_11950872().then(()=>{fetch('/api/watch?user_id='+userId,{method:'POST'}).then(r=>r.json()).then(d=>{alert(d.message);location.reload()})})}
function claim(){fetch('/api/claim?user_id='+userId,{method:'POST'}).then(r=>r.json()).then(d=>{alert(d.message);location.reload()})}
function withdraw(){let w=document.getElementById('wallet').value;let n=document.getElementById('network').value;let a=document.getElementById('amount').value;
if(!w||!a){alert('Fill wallet and amount');return;}fetch('/api/withdraw',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:userId,wallet:w,network:n,amount:a})}).then(r=>r.json()).then(d=>{alert(d.message)})}
</script></body></html>"""

@app.route('/')
def index():
    uid=request.args.get('user_id') or request.args.get('start') or 'guest'
    ref=request.args.get('ref')
    if uid not in users and uid!='guest':
        users[uid]={"username":request.args.get('username','User'+uid[:4]),"balance":0,"ads":0,"referrals":0,"ref_bonus":0,"last_claim":0,"referrer":ref,"ref_username":request.args.get('ref_username','')}
        if ref and ref in users: users[ref]["referrals"]=users[ref].get("referrals",0)+1; users[ref]["balance"]=users[ref].get("balance",0)+100; users[ref]["ref_bonus"]=users[ref].get("ref_bonus",0)+100
        save_json(DATA_FILE,users)
    u=users.get(uid,{"username":"Guest","balance":0,"ads":0,"referrals":0,"ref_bonus":0,"last_claim":0,"ref_username":""})
    timer_msg="Ready to mine"
    if u.get("last_claim"):
        diff=datetime.now()-datetime.fromtimestamp(u["last_claim"])
        if diff<timedelta(hours=2): remain=timedelta(hours=2)-diff; timer_msg=f"Wait {str(remain).split('.')[0]} to mine again"
    bot_username=os.getenv("BOT_USERNAME","your_bot")
    return render_template_string(HTML_PAGE,username=u.get("username"),balance=u.get("balance",0),ads=u.get("ads",0),referrals=u.get("referrals",0),ref_bonus=u.get("ref_bonus",0),user_id=uid,ref_username=u.get("ref_username","Not set"),timer_msg=timer_msg,bot_username=bot_username)

@app.route('/api/watch',methods=['POST'])
def api_watch():
    uid=request.args.get('user_id')
    if uid not in users: return jsonify({"message":"User not found, start bot first"})
    u=users[uid]
    if u.get("last_claim") and datetime.now()-datetime.fromtimestamp(u["last_claim"])<timedelta(hours=2) and u.get("ads",0)>=10: return jsonify({"message":"Mining cooldown - wait 2hrs"})
    u["ads"]=u.get("ads",0)+1
    if u["ads"]>10: u["ads"]=10
    save_json(DATA_FILE,users); return jsonify({"message":f"Ad {u['ads']}/10 watched! Watch {10-u['ads']} more"})

@app.route('/api/claim',methods=['POST'])
def api_claim():
    uid=request.args.get('user_id')
    if uid not in users: return jsonify({"message":"User not found"})
    u=users[uid]
    if u.get("ads",0)<10: return jsonify({"message":f"Watch {10-u.get('ads',0)} more ads"})
    if u.get("last_claim") and datetime.now()-datetime.fromtimestamp(u["last_claim"])<timedelta(hours=2): return jsonify({"message":"You already claimed, wait 2hrs"})
    u["balance"]=u.get("balance",0)+200; u["ads"]=0; u["last_claim"]=time.time(); save_json(DATA_FILE,users)
    return jsonify({"message":"200 TOKEN claimed! Balance updated"})

@app.route('/api/withdraw',methods=['POST'])
def api_withdraw():
    data=request.json; uid=data.get('user_id'); wallet=data.get('wallet','').strip(); network=data.get('network','BEP20'); amount=int(data.get('amount',0) or 0)
    if uid not in users: return jsonify({"message":"Start bot first"})
    u=users[uid]
    if u.get("balance",0)<12000: return jsonify({"message":f"Min withdraw 12,000. Your balance {u.get('balance',0)}"})
    if amount<12000: return jsonify({"message":"Amount must be >=12,000"})
    if amount>u.get("balance",0): return jsonify({"message":f"Insufficient balance. You have {u.get('balance',0)}"})
    if not wallet.startswith("0x") or len(wallet)<20: return jsonify({"message":"Invalid BEP20 address"})
    wid=str(int(time.time())); withdraws[wid]={"id":wid,"user_id":uid,"username":u.get("username"),"ref_username":u.get("ref_username",""),"balance":u.get("balance"),"amount":amount,"wallet":wallet,"network":network,"status":"pending","date":datetime.now().strftime("%d-%m-%Y %H:%M:%S")}
    save_json(WITHDRAW_FILE,withdraws); return jsonify({"message":f"Withdraw request of {amount} TOKEN submitted! Admin will approve soon."})

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    uid=str(update.effective_user.id); username=update.effective_user.username or update.effective_user.first_name; args=context.args; ref=args[0] if args else None
    if uid not in users:
        ref_username=""; 
        if ref and ref in users: ref_username=users[ref].get("username","")
        users[uid]={"username":username,"balance":0,"ads":0,"referrals":0,"ref_bonus":0,"last_claim":0,"referrer":ref,"ref_username":ref_username}
        if ref and ref in users and ref!=uid: users[ref]["referrals"]+=1; users[ref]["balance"]+=100; users[ref]["ref_bonus"]+=100
        save_json(DATA_FILE,users)
    u=users[uid]
    if not u.get("ref_username") and u.get("referrer") and u.get("referrer") in users: u["ref_username"]=users[u["referrer"]].get("username",""); save_json(DATA_FILE,users)
    web_url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME','your-app.onrender.com')}/?user_id={uid}&username={username}"
    keyboard=[[InlineKeyboardButton("⛏️ Open Mining Site",url=web_url)]]
    await update.message.reply_text(f"Welcome {username}!\n\nBalance: {u['balance']} TOKEN\nAds: {u.get('ads',0)}/10\nReferrals: {u.get('referrals',0)}\nRef Username: {u.get('ref_username','None')}\n\n10 Ads = 2hrs = 200 TOKEN\nMin Withdraw: 12,000 TOKEN (BEP20)\n\nYour Ref Link: https://t.me/{context.bot.username}?start={uid}",reply_markup=InlineKeyboardMarkup(keyboard))

async def withdraw_list(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id)!=str(ADMIN_ID): return
    if not withdraws: await update.message.reply_text("No pending withdraws"); return
    for wid,w in withdraws.items():
        if w["status"]!="pending": continue
        text=f"🔔 WITHDRAW REQUEST\n\nUsername: @{w['username']}\nUser ID: {w['user_id']}\nRef Username: {w.get('ref_username','')}\nCurrent Balance: {w['balance']} TOKEN\nWithdrawal Amount: {w['amount']} TOKEN\nNetwork: {w['network']}\nWallet Address:\n`{w['wallet']}`\n\nDate/Time: {w['date']}\nID: {wid}"
        kb=[[InlineKeyboardButton("✅ APPROVE",callback_data=f"approve_{wid}"),InlineKeyboardButton("❌ DECLINE",callback_data=f"decline_{wid}")]]
        await update.message.reply_text(text,reply_markup=InlineKeyboardMarkup(kb),parse_mode="Markdown")

async def handle_callback(update:Update,context:ContextTypes.DEFAULT_TYPE):
    query=update.callback_query; await query.answer(); data=query.data; action,wid=data.split("_",1)
    if wid not in withdraws: await query.edit_message_text("Not found"); return
    w=withdraws[wid]; uid=w["user_id"]
    if action=="approve":
        if uid in users: users[uid]["balance"]-=w["amount"]; save_json(DATA_FILE,users)
        w["status"]="approved"; save_json(WITHDRAW_FILE,withdraws)
        await query.edit_message_text(f"✅ APPROVED {w['amount']} TOKEN to {w['wallet']}")
        try: await context.bot.send_message(chat_id=int(uid),text=f"✅ Your withdraw of {w['amount']} TOKEN approved! Sent to {w['wallet']}")
        except: pass
    else:
        w["status"]="declined"; save_json(WITHDRAW_FILE,withdraws)
        await query.edit_message_text(f"❌ DECLINED {w['amount']} for @{w['username']}")
        try: await context.bot.send_message(chat_id=int(uid),text=f"❌ Your withdraw of {w['amount']} TOKEN was declined. Contact admin.")
        except: pass

def run_bot():
    if not BOT_TOKEN: print("No BOT_TOKEN set"); return
    from telegram.ext import Application
    application=Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start",start))
    application.add_handler(CommandHandler("balance",lambda u,c: c.bot.send_message(u.effective_chat.id,f"Balance: {users.get(str(u.effective_user.id),{}).get('balance',0)}")))
    application.add_handler(CommandHandler("withdraws",withdraw_list))
    application.add_handler(CommandHandler("admin",withdraw_list))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.run_polling()

def run_flask():
    port=int(os.environ.get("PORT",10000)); app.run(host="0.0.0.0",port=port)

if __name__=="__main__":
    Thread(target=run_flask,daemon=True).start(); run_bot()
