import os, json, threading, time
from flask import Flask, request, render_template_string, jsonify
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

BOT_TOKEN = os.getenv("BOT_TOKEN","").strip()
BOT_USERNAME = "token_sport_mining_bot"
ADMIN_ID = "7016458590"
app = Flask(__name__)

def load_refs():
    try:
        with open('referrals.json','r') as f: return json.load(f)
    except: return {}
def save_refs(d):
    with open('referrals.json','w') as f: json.dump(d,f)

HTML = """<!DOCTYPE html><html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>TOKEN SPORT MINING</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<script src="https://sad.adsgram.ai/js/sad.min.js"></script>
<style>
*{box-sizing:border-box}
body{background:#000;color:#fff;font-family:Arial,sans-serif;margin:0;padding:10px;text-align:center}
h1{color:#ffcc00;font-size:26px;margin:18px 0 14px 0}
.box{max-width:340px;margin:0 auto;background:#000;border:2px solid #ffcc00;border-radius:24px;padding:14px 12px 20px 12px}
.bal{font-size:44px;color:#00ff55;font-weight:900;margin:8px 0 12px 0}
.timer{background:#1a1a1a;color:#ffcc00;border:1px solid #2a2a2a;padding:12px;border-radius:14px;margin:0 4px 10px 4px;font-size:15px}
.prog{color:#9a9a9a;font-size:13px;margin:10px 0 8px 0}
.btn{width:100%;padding:14px;background:#ffcc00;color:#000;border:none;border-radius:28px;font-weight:900;font-size:14px;margin:5px 0;cursor:pointer}
.btn2{background:#000;color:#ffcc00;border:2px solid #ffcc00}
.btn:disabled{opacity:0.5}
.warn{background:#3d1a1a;color:#ff4444;padding:12px 10px;border-radius:12px;margin:10px 4px;font-size:14px;display:none;border:1px solid #5a2525}
.warn.ok{background:#102a1a;color:#33ff77;border-color:#1a4a2a}
.inp{width:100%;padding:12px 12px;border-radius:12px;border:1.5px solid #ffcc00;background:#000;color:#fff;margin:5px 0;font-size:13px;outline:none}
.small{color:#8a8a8a;font-size:12px;line-height:1.4;margin:6px 0}
</style>
</head><body>
<h1>TOKEN SPORT MINING</h1>
<div class="box">
<div class="bal" id="bal">0.00000000</div>
<div class="timer" id="timer">Paused - Watch 8 ADS (15s)</div>
<div class="prog" id="mProg">ADS: 0/8</div>
<button class="btn" id="mineBtn" onclick="mineClick()">MINE</button>
<button class="btn btn2" id="adBtn" onclick="watchAdMining()">WATCH AD 0/8 (15s)</button>
<div class="warn" id="warn"></div>
<input class="inp" id="refLink" readonly>
<button class="btn btn2" onclick="copyRef()">COPY INVITE LINK</button>
<div class="small" id="refStat">Friends: 0 | Ref Earned: 0.00000000<br>Bonus: 10% from friends mining<br>WD ADS: 0/5</div>
<button class="btn btn2" id="wdAdBtn" onclick="watchAdWD()">WATCH AD 0/5 (15s)</button>
<input class="inp" id="wallet" placeholder="Wallet">
<button class="btn" id="wdBtn" onclick="doWD()" style="background:#2a2a2a;color:#666;">WITHDRAW</button>
</div>
<script>
let bal=parseFloat(localStorage.getItem('bal')||'0');
let start=parseInt(localStorage.getItem('start')||'0');
let mAds=parseInt(localStorage.getItem('mAds')||'0');
let wAds=parseInt(localStorage.getItem('wAds')||'0');
let isMining=localStorage.getItem('isMining')==='true';
let wUnlock=localStorage.getItem('wUnlock')==='true';
let myId=localStorage.getItem('myId')||'user_'+Math.random().toString(36).substr(2,9);
let inviter=localStorage.getItem('inviter')||'';
localStorage.setItem('myId',myId);
const TWELVE=12*60*60*1000;
const TOKEN_PER_12H=0.857142857;
const RATE=TOKEN_PER_12H/(12*60*60);
const MINWD=12;
let AdController=null;
function initAdsgram(){try{if(window.Adsgram) AdController=window.Adsgram.init({ blockId: "51649" });}catch(e){} }
const up=new URLSearchParams(window.location.search);
let refFromUrl=up.get('ref');
if(refFromUrl && refFromUrl!==myId &&!inviter){inviter=refFromUrl; localStorage.setItem('inviter',inviter); fetch('/api/ref_join',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({newUser:myId,inviter:inviter})});}
function save(){localStorage.setItem('bal',bal);localStorage.setItem('start',start);localStorage.setItem('mAds',mAds);localStorage.setItem('wAds',wAds);localStorage.setItem('isMining',isMining);localStorage.setItem('wUnlock',wUnlock);}
function ui(){ document.getElementById('bal').innerText=bal.toFixed(8); document.getElementById('mProg').innerText=`ADS: ${mAds}/8`; document.getElementById('refLink').value=window.location.origin+'/?ref='+myId; }
function loadRefStats(){ fetch('/api/ref_stats?userId='+myId).then(r=>r.json()).then(d=>{ document.getElementById('refStat').innerHTML=`Friends: ${d.count} | Ref Earned: ${d.earned.toFixed(8)}<br>Bonus: 10% from friends mining<br>WD ADS: ${wAds}/5`; }); }
function showWarn(t,ok=false){let w=document.getElementById('warn'); w.style.display='block'; w.innerText=t; w.className=ok?'warn ok':'warn'; if(ok) setTimeout(()=>w.style.display='none',3500);}
function copyRef(){let i=document.getElementById('refLink'); i.select(); document.execCommand('copy'); showWarn('Invite Link Copied! Share = 10% bonus!',true);}
function watchAdMining(){ if(mAds>=8){startMining();return;} if(!AdController){showWarn('AD Error: Open inside Telegram!',false); initAdsgram(); return;} let btn=document.getElementById('adBtn'); btn.disabled=true; btn.innerText="Loading AD... Watch 15s!"; showWarn('MUST WATCH FULL 15s OR NO REWARD!',true); AdController.show().then((r)=>{ui(); if(r && r.done){mAds++; save(); ui(); showWarn(`AD ${mAds}/8 DONE!`,true); if(mAds>=8) startMining();} else{showWarn('Skip! MUST watch 15s! Locked 10s',false); btn.innerText="CHEAT! Wait 10s..."; let c=10; let iv=setInterval(()=>{c--; btn.innerText=`PUNISHED! Wait ${c}s...`; if(c<=0){clearInterval(iv); btn.disabled=false; ui();}},1000);}}).catch((e)=>{btn.disabled=false; ui(); showWarn('AD Error... Open in Telegram!',false);});}
function startMining(){start=Date.now(); isMining=true; mAds=0; save(); ui(); showWarn('12H Mining Started! 7 Days to 12!',true);}
function watchAdWD(){ if(wAds>=5){wUnlock=true; save(); ui(); return;} if(!AdController){showWarn('AD Error: Open in Telegram!',false); return;} let btn=document.getElementById('wdAdBtn'); btn.disabled=true; btn.innerText="Loading WD AD... 15s!"; showWarn('WD AD - MUST WATCH FULL 15s!',true); AdController.show().then((r)=>{ui(); if(r && r.done){wAds++; if(wAds>=5) wUnlock=true; save(); ui(); showWarn(`WD AD ${wAds}/5 DONE!`,true);} else{showWarn('Skip! MUST watch 15s! Locked 10s',false); btn.innerText="CHEAT! Wait 10s..."; let c=10; let iv=setInterval(()=>{c--; btn.innerText=`PUNISHED! Wait ${c}s...`; if(c<=0){clearInterval(iv); btn.disabled=false; ui();}},1000);}}).catch((e)=>{btn.disabled=false; ui(); showWarn('AD Error... Open in Telegram!',false);});}
function mineClick(){if(!isMining){showWarn('Watch 8 ADS (15s)!');return;} bal+=0.00002; save(); ui();}
function tick(){ if(isMining && start){ let el=Date.now()-start, left=TWELVE-el; if(left<=0){isMining=false; start=0; save(); document.getElementById('timer').innerText='Finished! Watch 8 ADS';} else{let add=RATE; bal+=add; if(inviter && Math.random()<0.1){fetch('/api/ref_mine',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({inviter:inviter,amount:add})});} save(); let h=Math.floor(left/3600000), m=Math.floor((left%3600000)/60000), s=Math.floor((left%60000)/1000); document.getElementById('timer').innerText=`Mining: ${h}h ${m}m ${s}s left - 0.86/12H`; document.getElementById('bal').innerText=bal.toFixed(8);} }else{document.getElementById('timer').innerText='Paused - Watch 8 ADS (15s) - 7 Days to 12 TOKEN';} }
function doWD(){ let w=document.getElementById('wallet').value.trim(); if(w.length<10){alert("Enter wallet");return;} if(bal<12){alert("Need 12 - 7 Days Mining");return;} if(!wUnlock){alert("Watch 5 ADS");return;} fetch('/api/withdraw',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({wallet:w,amount:bal,userId:myId,inviter:inviter})}).then(r=>r.json()).then(d=>{if(d.ok){bal=0;wAds=0;wUnlock=false;save();ui();alert('Sent!');}});}
ui(); loadRefStats(); setInterval(tick,1000); setInterval(loadRefStats,5000); tick(); setTimeout(initAdsgram,800);
if(window.Telegram && window.Telegram.WebApp){window.Telegram.WebApp.ready(); window.Telegram.WebApp.expand();}
</script></body></html>
"""
@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/api/ref_join', methods=['POST'])
def ref_join():
    data=request.get_json() or {}
    new_user=data.get('newUser',''); inviter=data.get('inviter','')
    if not new_user or not inviter or new_user==inviter: return jsonify({"ok":True})
    refs=load_refs()
    if inviter not in refs: refs[inviter]={'count':0,'earned':0,'users':[]}
    if new_user not in refs[inviter]['users']:
        refs[inviter]['users'].append(new_user)
        refs[inviter]['count']=len(refs[inviter]['users'])
        save_refs(refs)
    return jsonify({"ok":True})

@app.route('/api/ref_stats')
def ref_stats():
    user_id=request.args.get('userId','')
    refs=load_refs()
    data=refs.get(user_id, {'count':0,'earned':0})
    return jsonify({"count":data.get('count',0),"earned":data.get('earned',0)})

@app.route('/api/ref_mine', methods=['POST'])
def ref_mine():
    data=request.get_json() or {}
    inviter=data.get('inviter',''); amt=float(data.get('amount',0))
    if not inviter or amt<=0: return jsonify({"ok":True})
    refs=load_refs()
    if inviter not in refs: refs[inviter]={'count':0,'earned':0,'users':[]}
    refs[inviter]['earned']=refs[inviter].get('earned',0)+amt*0.10
    save_refs(refs)
    return jsonify({"ok":True})

@app.route('/api/reward', methods=['GET','POST'])
def reward_api():
    user_id = request.args.get('userId') or request.args.get('user_id') or ""
    if not user_id:
        try:
            j = request.get_json(silent=True) or {}
            user_id = j.get('userId','') or j.get('user_id','')
        except: pass
    print(f"REWARD OK for {user_id}")
    try:
        with open('ads_rewards.json','a') as f:
            f.write(json.dumps({"userId": user_id, "time": time.time()}) + "\n")
    except: pass
    return jsonify({"ok": True, "reward": 10000})

@app.route('/admin')
def admin_panel():
    key = request.args.get('key','')
    if key!= ADMIN_ID: return "Access Denied!", 403
    refs=load_refs()
    rewards=[]
    try:
        with open('ads_rewards.json','r') as f:
            for line in f:
                try: rewards.append(json.loads(line))
                except: pass
    except: pass
    html=f"<html><body style='background:#000;color:#fff;font-family:Arial;padding:15px'><h2 style='color:#ffd700'>BOSS ADMIN - 7 DAYS TO 12 - REF 10%</h2><div style='border:2px solid #ffd700;padding:10px;margin:10px 0'>Total Watches: {len(rewards)} | Referrers: {len(refs)}</div><pre style='background:#111;padding:10px;white-space:pre-wrap'>{json.dumps(refs, indent=2)}</pre></body></html>"
    return html

@app.route('/api/withdraw', methods=['POST'])
def wd():
    data=request.get_json() or {}
    wallet=data.get('wallet','')[:120]
    amt=float(data.get('amount',0))
    uid=data.get('userId','')
    msg=f"NEW WD! {amt:.8f} Wallet:{wallet} UID:{uid}"
    print(msg)
    if BOT_TOKEN and ADMIN_ID:
        try: telebot.TeleBot(BOT_TOKEN).send_message(int(ADMIN_ID), msg)
        except: pass
    return jsonify({"ok":True})

def bot_thread():
    if not BOT_TOKEN: return
    while True:
        try:
            bot=telebot.TeleBot(BOT_TOKEN)
            try: bot.delete_webhook(drop_pending_updates=True); time.sleep(2)
            except: pass
            print("Bot LIVE - 7 DAYS + 10% REF")
            @bot.message_handler(commands=['start'])
            def s(m):
                dom=os.getenv("RENDER_EXTERNAL_HOSTNAME","") or os.getenv("REPLIT_DEV_DOMAIN","")
                link=f"https://{dom}/?ref={m.chat.id}" if dom else f"https://t.me/{BOT_USERNAME}"
                kb=InlineKeyboardMarkup()
                kb.add(InlineKeyboardButton("OPEN MINING - 7 DAYS TO 12 + 10% REF", web_app=WebAppInfo(url=link)))
                bot.send_message(m.chat.id, f"TOKEN SPORT MINING\\n\\nNEW: 0.86 per 12H = 12 in 7 DAYS!\\nInvite friends = 10% bonus!\\n\\n{link}", reply_markup=kb)
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
        except Exception as e:
            print(f"Retry {e}"); time.sleep(10)

threading.Thread(target=bot_thread, daemon=True).start()
if __name__ == "__main__":
    port=int(os.getenv("PORT",8080))
    app.run(host="0.0.0.0", port=port)
