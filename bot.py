# -*- coding: utf-8 -*-
# بوت رشق الإحالات — النسخة الكاملة النهائية
# تعليقات صحيحة + Log مطوّر + اسم المشرف + روابط

import os, sys, subprocess

def install_requirements():
    for pkg in ["pyrogram", "tgcrypto"]:
        try: __import__(pkg); print(f"✅ {pkg}")
        except:
            print(f"📦 تثبيت {pkg}...")
            try: subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", pkg, "--quiet"]); print(f"✅ {pkg}")
            except: print(f"⚠️ {pkg} فشل")

print("="*50)
print("🤖 بوت رشق الإحالات")
print("="*50)
install_requirements()
print("⏳ تشغيل...\n")

import asyncio, sqlite3, time, random, base64, json, re, glob, zipfile, shutil
import inspect as _inspect
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType
from pyrogram.errors import FloodWait, SessionPasswordNeeded, UserAlreadyParticipant, UserDeactivated
import logging

logging.basicConfig(level=logging.WARNING)

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BOT_TOKEN = "8993039335:AAGukJhQTWPcyZXioh98zGg4OnEo58fAQR8"
OWNER_ID = 8741814745

RESET_DB = False

BASE = "/storage/emulated/0/TelegramBot"
DATA = os.path.join(BASE, "data")
SESSIONS = os.path.join(BASE, "sessions")
BACKUPS = os.path.join(BASE, "backups")
TEMP = os.path.join(BASE, "temp")
PHOTOS_DIR = os.path.join(BASE, "photos")
DB_FILE = os.path.join(DATA, "bot.db")

for p in [BASE, DATA, SESSIONS, BACKUPS, TEMP, PHOTOS_DIR]:
    try: os.makedirs(p, exist_ok=True)
    except: BASE="."; DATA="./data"; SESSIONS="./sessions"; BACKUPS="./backups"; TEMP="./temp"; PHOTOS_DIR="./photos"; DB_FILE="./data/bot.db"
    for d in [DATA, SESSIONS, BACKUPS, TEMP, PHOTOS_DIR]: os.makedirs(d, exist_ok=True)

if RESET_DB:
    try:
        if os.path.exists(DB_FILE): os.remove(DB_FILE); print("🗑 حُذفت القاعدة")
        for f in glob.glob(f"{SESSIONS}/*"):
            try: os.remove(f)
            except: pass
    except Exception as e: print(f"⚠️ {e}")

try:
    _HAS_STYLE = "style" in _inspect.signature(InlineKeyboardButton.__init__).parameters
except Exception:
    _HAS_STYLE = False

def KbBtn(text, callback_data=None, url=None, style=None):
    if _HAS_STYLE and style:
        try: return InlineKeyboardButton(text, callback_data=callback_data, url=url, style=style)
        except TypeError: pass
    return InlineKeyboardButton(text, callback_data=callback_data, url=url)

NORMAL_EMOJIS = ["👍", "👎", "❤️", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱", "🤬", "😢", "🎉", "🤩", "🤮", "💩", "🙏", "👌", "😍", "💋", "🏆", "⚡️", "🍾", "💊", "😎", "🗿", "🆒", "💘", "🦄", "😘"]
SPECIAL_EMOJIS = ["🤍", "🖤", "🤎", "💜", "🧡", "💛", "💚", "💙", "❤️‍🔥", "🌟", "✨", "💫", "🎯", "🏅", "🥇", "🥈", "🥉", "🎖", "💪", "🤝", "🙌", "💢", "💥", "💦", "💨", "🌀", "🌈", "☀️", "💧", "💤", "🎵", "🎶", "🎧", "🎤", "🎬", "🎭", "🎨"]

class DB:
    def __init__(self):
        self.c = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.c.row_factory = sqlite3.Row
        self.c.execute("CREATE TABLE IF NOT EXISTS acc (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT, username TEXT, first_name TEXT, user_id INTEGER UNIQUE, session_string TEXT, two_step TEXT, created_at TEXT)")
        self.c.execute("CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY, expiry_date TEXT, added_by INTEGER, added_at TEXT)")
        self.c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        self.c.execute("INSERT OR IGNORE INTO admins VALUES (?, NULL, ?, ?)", (OWNER_ID, OWNER_ID, datetime.now().isoformat()))
        try: self.c.execute("ALTER TABLE acc ADD COLUMN two_step TEXT")
        except: pass
        self.c.commit()
    def add_acc(self, phone, username, first_name, user_id, session, two_step=""):
        self.c.execute("INSERT OR REPLACE INTO acc VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)", (phone, username, first_name, user_id, session, two_step, datetime.now().isoformat()))
        self.c.commit()
    def all_acc(self):
        accs = [dict(r) for r in self.c.execute("SELECT * FROM acc").fetchall()]
        try: accs.sort(key=lambda a: int(re.findall(r'\d+', a.get('first_name') or '')[-1]) if re.findall(r'\d+', a.get('first_name') or '') else 0)
        except: pass
        return accs
    def count(self): return self.c.execute("SELECT COUNT(*) as c FROM acc").fetchone()['c']
    def get_by_uid(self, uid):
        r = self.c.execute("SELECT * FROM acc WHERE user_id=?", (uid,)).fetchone()
        return dict(r) if r else None
    def get_by_id(self, aid):
        r = self.c.execute("SELECT * FROM acc WHERE id=?", (aid,)).fetchone()
        return dict(r) if r else None
    def del_acc(self, aid): self.c.execute("DELETE FROM acc WHERE id=?", (aid,)); self.c.commit()
    def del_acc_by_uid(self, uid):
        self.c.execute("DELETE FROM acc WHERE user_id=?", (uid,)); self.c.commit()
    def del_all(self): self.c.execute("DELETE FROM acc"); self.c.commit()
    def is_admin(self, uid):
        if uid == OWNER_ID: return True
        r = self.c.execute("SELECT expiry_date FROM admins WHERE user_id=?", (uid,)).fetchone()
        if not r: return False
        if r['expiry_date']:
            try:
                if datetime.now() > datetime.fromisoformat(r['expiry_date']):
                    self.remove_admin(uid); return False
            except: pass
        return True
    def add_admin(self, uid, expiry=None, added_by=OWNER_ID):
        self.c.execute("INSERT OR REPLACE INTO admins VALUES (?, ?, ?, ?)", (uid, expiry, added_by, datetime.now().isoformat()))
        self.c.commit()
    def remove_admin(self, uid):
        if uid != OWNER_ID: self.c.execute("DELETE FROM admins WHERE user_id=?", (uid,)); self.c.commit()
    def all_admins(self): return [dict(r) for r in self.c.execute("SELECT * FROM admins").fetchall()]
    def check_expired(self):
        now = datetime.now().isoformat()
        expired = self.c.execute("SELECT user_id FROM admins WHERE expiry_date IS NOT NULL AND expiry_date < ? AND user_id != ?", (now, OWNER_ID)).fetchall()
        for e in expired: self.remove_admin(e['user_id'])
        self.c.commit()
    def set_setting(self, key, value):
        self.c.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (key, str(value)))
        self.c.commit()
    def get_setting(self, key, default=None):
        r = self.c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return r['value'] if r else default
    def get_log_chat(self):
        v = self.get_setting("log_chat_id")
        try: return int(v) if v else None
        except: return None
    def set_log_chat(self, chat_id): self.set_setting("log_chat_id", chat_id)

db = DB()

# ═══════════════════════════════════════════════════════════
# 📢 Log — مع كاش لأسماء المشرفين
# ═══════════════════════════════════════════════════════════
_user_cache = {}

async def get_user_info(uid):
    """جلب اسم ومعرف المستخدم مع كاش"""
    if uid in _user_cache:
        return _user_cache[uid]
    try:
        cli = getattr(send_log, "_client", None)
        if cli is None:
            return f"`{uid}`", f"`{uid}`"
        user = await cli.get_users(uid)
        name = user.first_name or "بدون اسم"
        if user.last_name: name += f" {user.last_name}"
        username = f"@{user.username}" if user.username else "بدون معرف"
        _user_cache[uid] = (name, username)
        return name, username
    except Exception:
        return f"`{uid}`", f"`{uid}`"

async def send_log(text, silent=False):
    """إرسال رسالة للقروب المرتبط"""
    try:
        chat_id = db.get_log_chat()
        if not chat_id: return
        cli = getattr(send_log, "_client", None)
        if cli is None: return
        await cli.send_message(chat_id, text, disable_notification=silent)
    except Exception as e:
        print(f"⚠️ send_log فشل: {e}")

def build_link(channel_id, msg_id):
    """بناء رابط قابل للنقر من channel_id + msg_id"""
    try:
        if isinstance(channel_id, int) or (isinstance(channel_id, str) and channel_id.startswith("-100")):
            cid = str(channel_id).replace("-100", "")
            return f"https://t.me/c/{cid}/{msg_id}"
        else:
            ch = str(channel_id).replace("@", "").strip()
            return f"https://t.me/{ch}/{msg_id}"
    except:
        return f"{channel_id}/{msg_id}"
# ═══════════════════════════════════════════════════════════

KEY = "Tx9$kL2@mN7#pQ4"
def enc(t):
    try: return base64.b64encode(''.join(chr(ord(c)^ord(KEY[i%len(KEY)])) for i,c in enumerate(t)).encode()).decode()
    except: return t
def dec(t):
    try: return ''.join(chr(ord(c)^ord(KEY[i%len(KEY)])) for i,c in enumerate(base64.b64decode(t.encode()).decode()))
    except: return t

def export_sessions_json():
    try:
        accs = db.all_acc()
        data = [{"phone": a['phone'], "username": a['username'], "first_name": a['first_name'], "user_id": a['user_id'], "session_string": a['session_string'], "two_step": a.get('two_step','')} for a in accs]
        path = f"{BACKUPS}/sessions_{int(time.time())}.json"
        with open(path, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)
        return True, path, len(data)
    except Exception as e: return False, str(e), 0

def import_sessions_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f: data = json.load(f)
        cnt = 0
        for a in data:
            if 'session_string' in a:
                uid = a.get('user_id', 0)
                if uid and db.get_by_uid(uid): continue
                db.add_acc(a.get('phone',''), a.get('username',''), a.get('first_name',''), uid, a['session_string'], a.get('two_step',''))
                cnt += 1
        return True, cnt
    except Exception as e: return False, str(e)

def solve_captcha_numbers(text):
    if not text: return None
    for p in [r'كم ناتج[:\s]*(\d+)\s*([+\-*])\s*(\d+)', r'حل المسألة[:\s]*(\d+)\s*([+\-*])\s*(\d+)', r'حل المسأله[:\s]*(\d+)\s*([+\-*])\s*(\d+)', r'الرقم التالي[:\s]*(\d{4,6})', r'أرسل الرقم[:\s]*(\d{4,6})', r'ارسل الرقم[:\s]*(\d{4,6})', r'(\d{4,6})']:
        m = re.search(p, text)
        if m:
            if len(m.groups()) >= 2 and m.group(2):
                n1, op, n2 = int(m.group(1)), m.group(2), int(m.group(3))
                return str(n1+n2) if op=='+' else str(n1-n2) if op=='-' else str(n1*n2)
            return m.group(1)
    math_match = re.search(r'(\d+)\s*([+\-*])\s*(\d+)', text)
    if math_match:
        n1, n2, op = int(math_match.group(1)), int(math_match.group(3)), math_match.group(2)
        return str(n1+n2) if op=='+' else str(n1-n2) if op=='-' else str(n1*n2)
    return None

def extract_emoji_from_captcha(text):
    if not text: return None
    for p in [r'\(([^\w\s]{1,3})\)', r'هذا الإيموجي\s*\(([^\w\s]{1,3})\)', r'يشبه\s*\(([^\w\s]{1,3})\)', r'اضغط على الزر اللي يشبه هذا الإيموجي\s*\(([^\w\s]{1,3})\)']:
        m = re.search(p, text)
        if m: return m.group(1).strip()
    return None

DECOR_EMOJIS = {"🎯", "🔮", "🛡", "⚔️", "🔰", "⭐", "🌟", "✨", "🔔", "📌", "📍", "🔍", "🎲", "🎰", "🎁", "🏆", "🥇", "🎖", "🏅", "💠", "🔷", "🔶", "🔸", "🔹", "🔺", "🔻", "◾", "◽", "▪️", "▫️", "⬛", "⬜"}

def extract_all_emojis(text):
    if not text: return []
    emojis = []
    for ch in text:
        cp = ord(ch)
        if (0x1F300 <= cp <= 0x1FAFF or 0x2600 <= cp <= 0x27BF or
            0x1F000 <= cp <= 0x1F2FF or 0x2B00 <= cp <= 0x2BFF or
            0x1F1E6 <= cp <= 0x1F1FF or
            cp in (0x2764, 0x2763, 0x2762, 0x203C, 0x2049, 0x2122, 0x2139)):
            emojis.append(ch)
    return emojis

def normalize_emoji(e):
    if not e: return ""
    return e.replace("\ufe0f", "").replace("\ufe0e", "").replace("\u200d", "").strip()

def extract_target_emoji(text):
    if not text: return None
    patterns = [
        r'الهدف[:\s]*([^\w\s]{1,5})', r'الرمز[:\s]*([^\w\s]{1,5})',
        r'اضغط على[^\w\s]*([^\w\s]{1,5})', r'الإيموجي[:\s]*([^\w\s]{1,5})',
        r'المشابه[:\s]*([^\w\s]{1,5})', r'يشبه[:\s]*([^\w\s]{1,5})',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            candidate = m.group(1).strip()
            found = extract_all_emojis(candidate)
            if found: return found[0]
    emojis = extract_all_emojis(text)
    filtered = [e for e in emojis if e not in DECOR_EMOJIS]
    if filtered: return filtered[-1]
    if emojis: return emojis[0]
    return None

def find_emoji_button(buttons, target_emoji):
    if not target_emoji or not buttons: return None
    target_norm = normalize_emoji(target_emoji)
    for row in buttons:
        for btn in row:
            btn_text = btn.text or ""
            if target_emoji in btn_text: return btn
            btn_norm = normalize_emoji(btn_text)
            if target_norm and target_norm in btn_norm: return btn
            for be in extract_all_emojis(btn_text):
                if normalize_emoji(be) == target_norm: return btn
    return None

def solve_math_captcha(text):
    if not text: return None
    m = re.search(r'(\d+)\s*([+\-*×x÷/])\s*(\d+)', text)
    if m:
        try:
            n1 = int(m.group(1)); op = m.group(2); n2 = int(m.group(3))
            if op == '+': return n1 + n2
            if op == '-': return n1 - n2
            if op in ('*', '×', 'x'): return n1 * n2
            if op == '/': return n1 // n2 if n2 else 0
            if op == '÷': return n1 // n2 if n2 else 0
        except: pass
    return None

def is_emoji_captcha_text(text):
    if not text: return False
    keywords = ["الرمز", "الهدف", "الإيموجي", "الايموجي", "اضغط على", "المشابه", "يشبه", "اختر", "تحقق", "لست روبوت", "ليس روبوت"]
    return any(k in text for k in keywords)

def parse_message_link(link):
    link = link.replace("https://t.me/", "").replace("http://t.me/", "").strip()
    parts = link.split("/")
    if parts[0] == "c" and len(parts) >= 3:
        chat_id = int("-100" + parts[1]); msg_id = int(parts[2])
        return chat_id, msg_id
    elif len(parts) >= 2:
        try: return parts[0], int(parts[1])
        except: return None, None
    return None, None

# ═══════════════════════════════════════════════════════════
# ✅ post_comment v4 — تعليق حقيقي تحت المنشور
# ═══════════════════════════════════════════════════════════
async def post_comment(client, channel_id, msg_id, text, name=""):
    """نشر تعليق — النسخة الصحيحة"""
    try:
        if isinstance(channel_id, str) and channel_id.lstrip("-").isdigit():
            target = int(channel_id)
        else:
            target = channel_id
    except Exception:
        target = channel_id

    # ═══ الطريقة الرسمية الصحيحة ═══
    discussion_msg = None
    try:
        discussion_msg = await client.get_discussion_message(target, msg_id)
    except Exception as e:
        print(f"⚠️ [{name}] get_discussion_message: {type(e).__name__}: {e}")

    if discussion_msg:
        # انضم لمجموعة النقاش
        try:
            await client.join_chat(discussion_msg.chat.id)
            await asyncio.sleep(0.8)
        except UserAlreadyParticipant:
            pass
        except Exception:
            pass

        # الرد على رسالة المنشور في مجموعة النقاش = تعليق حقيقي
        try:
            await discussion_msg.reply(text)
            return True
        except Exception as e:
            print(f"⚠️ [{name}] reply فشل: {type(e).__name__}: {e}")

    # ═══ fallback عبر linked_chat ═══
    try:
        chat = await client.get_chat(target)
        linked = getattr(chat, "linked_chat", None)
        if linked and getattr(linked, "id", None):
            await client.join_chat(linked.id)
            await asyncio.sleep(0.5)
            await client.send_message(linked.id, text, reply_to_message_id=msg_id)
            return True
    except Exception as e:
        print(f"⚠️ [{name}] fallback: {type(e).__name__}: {e}")

    return False
# ═══════════════════════════════════════════════════════════

cancel_flags = {}

class AM:
    def __init__(self): self.clients={}
    async def send_code(self, phone):
        try:
            phone=phone.strip().replace(" ","")
            if not phone.startswith("+"): phone="+"+phone
            c=Client(f"{SESSIONS}/p_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, in_memory=False)
            await c.connect(); s=await c.send_code(phone)
            return {"ok":True, "client":c, "hash":s.phone_code_hash}
        except Exception as e: return {"ok":False, "err":str(e)}
    async def sign_in(self, c, phone, h, code):
        try:
            u=await c.sign_in(phone, h, code); ses=await c.export_session_string()
            db.add_acc(phone, u.username, u.first_name, u.id, enc(ses)); self.clients[u.id]=c
            return {"ok":True, "name":u.first_name}
        except SessionPasswordNeeded: return {"ok":False, "need_pass":True, "client":c}
        except Exception as e: return {"ok":False, "err":str(e)}
    async def check_pass(self, c, pw):
        try:
            u=await c.check_password(pw); ses=await c.export_session_string()
            db.add_acc("", u.username, u.first_name, u.id, enc(ses), pw); self.clients[u.id]=c
            return {"ok":True, "user_id": u.id}
        except Exception as e: return {"ok":False, "err":str(e)}
    def remove_account_session(self, uid):
        for pattern in [f"{SESSIONS}/l_{uid}*", f"{SESSIONS}/c_{uid}*", f"{SESSIONS}/p_{uid}*"]:
            for path in glob.glob(pattern):
                try:
                    if os.path.isdir(path): shutil.rmtree(path, ignore_errors=True)
                    else: os.remove(path)
                except: pass
    async def handle_deactivated(self, uid):
        self.clients.pop(uid, None)
        db.del_acc_by_uid(uid)
        self.remove_account_session(uid)
    async def get_client(self, uid):
        if uid in self.clients:
            try:
                await self.clients[uid].get_me()
                return self.clients[uid]
            except UserDeactivated:
                await self.handle_deactivated(uid); return None
            except Exception:
                try: del self.clients[uid]
                except: pass
        a = db.get_by_uid(uid)
        if a and a['session_string']:
            try:
                c = Client(f"{SESSIONS}/c_{uid}", api_id=API_ID, api_hash=API_HASH, session_string=dec(a['session_string']))
                await c.start(); self.clients[uid] = c; return c
            except UserDeactivated:
                await self.handle_deactivated(uid); return None
            except Exception: pass
        return None
    async def load_all(self):
        accs = db.all_acc()
        if not accs: return 0
        loaded = 0; removed = 0
        for a in accs:
            uid = a['user_id']
            name = a.get('first_name') or a.get('phone') or str(uid)
            try:
                c = Client(f"{SESSIONS}/l_{uid}", api_id=API_ID, api_hash=API_HASH, session_string=dec(a['session_string']))
                await c.start(); self.clients[uid] = c; loaded += 1
            except UserDeactivated:
                removed += 1
                await self.handle_deactivated(uid)
                print(f"🗑 حذف جلسة معطلة: {name} | {uid}")
            except Exception as e:
                print(f"⚠️ تعذر تشغيل جلسة {name} | {uid}: {e}")
        if removed: print(f"🧹 تم تنظيف {removed} جلسة معطلة")
        return loaded
    async def import_session_file(self, filepath):
        try:
            temp_client = Client(filepath, api_id=API_ID, api_hash=API_HASH, in_memory=False, no_updates=True)
            await temp_client.start()
            me = await temp_client.get_me()
            existing = db.get_by_uid(me.id)
            if existing:
                await temp_client.stop(); return False, "موجود مسبقاً", None
            session_string = await temp_client.export_session_string()
            db.add_acc(getattr(me, 'phone_number', '') or '', getattr(me, 'username', '') or '',
                       getattr(me, 'first_name', '') or os.path.splitext(os.path.basename(filepath))[0],
                       me.id, enc(session_string), "")
            self.clients[me.id] = temp_client
            return True, f"✅ {me.first_name}", me.id
        except UserDeactivated:
            try: await temp_client.stop()
            except: pass
            return False, "الحساب محذوف أو معطل", None
        except Exception as e:
            return False, str(e), None
    async def join_ch(self, client, channel):
        try: await client.join_chat(channel.strip() if channel.startswith("@") else "@"+channel.strip()); return True
        except UserAlreadyParticipant: return True
        except FloodWait as e: await asyncio.sleep(0.3); return await self.join_ch(client, channel)
        except: return False
    async def click_button_by_text(self, client, msg, bot_username, target_text):
        if not msg.reply_markup: return False
        for row in msg.reply_markup.inline_keyboard:
            for btn in row:
                if target_text in (btn.text or "") or (btn.text or "") == target_text:
                    try: await msg.click(btn.text); await asyncio.sleep(0.3); return True
                    except:
                        try: await client.request_callback_answer(bot_username, msg.id, btn.callback_data); await asyncio.sleep(0.3); return True
                        except: pass
        return False
    async def click_button_obj(self, client, msg, bot_username, btn):
        try:
            await client.request_callback_answer(bot_username, msg.id, btn.callback_data)
            await asyncio.sleep(0.3); return True
        except:
            try:
                if btn.text:
                    await msg.click(btn.text); await asyncio.sleep(0.3); return True
            except: pass
        return False
    async def solve_captcha_buttons(self, client, bot_username, name=""):
        try:
            await asyncio.sleep(0.5)
            async for msg in client.get_chat_history(bot_username, limit=10):
                if not msg.text and not msg.caption: continue
                text = msg.text or msg.caption or ""
                result = solve_math_captcha(text)
                if result is not None:
                    if await self.click_button_by_text(client, msg, bot_username, str(result)): return True, f"✅ {name} - رياضيات: {result}"
                target_emoji = extract_emoji_from_captcha(text)
                if target_emoji:
                    if await self.click_button_by_text(client, msg, bot_username, target_emoji): return True, f"✅ {name} - إيموجي: {target_emoji}"
                code = solve_captcha_numbers(text)
                if code:
                    if await self.click_button_by_text(client, msg, bot_username, code): return True, f"✅ {name} - رقم: {code}"
            return True, f"✅ {name} - بدون كابتشا"
        except Exception as e: return False, f"❌ {name} - {str(e)}"
    async def do_ref_with_captcha(self, client, bot_link, channels, name=""):
        try:
            if channels:
                for ch in channels: await self.join_ch(client, ch)
            link = bot_link.replace("https://t.me/","").replace("http://t.me/","")
            if "?" in link:
                bot_username, param = link.split("?",1); bot_username = bot_username.strip(); start_param = param.replace("start=","").strip()
            else: bot_username = link.strip(); start_param = ""
            await client.send_message(bot_username, f"/start {start_param}" if start_param else "/start")
            await asyncio.sleep(0.5)
            return await self.solve_captcha_buttons(client, bot_username, name)
        except Exception as e: return False, f"❌ {name} - {str(e)}"
    async def mass_ref_with_captcha(self, uid, accs, link, channels, msg=None):
        async def func(c, name): return await self.do_ref_with_captcha(c, link, channels, name)
        return await self.mass_execute(uid, accs, func, msg, "🚀🔐", 100)
    async def do_giveaway_with_captcha(self, client, channel, giveaway_link, name=""):
        try:
            await self.join_ch(client, channel); await asyncio.sleep(0.3)
            link = giveaway_link.replace("https://t.me/","").replace("http://t.me/","")
            if "?" in link:
                bot_username, param = link.split("?",1); bot_username = bot_username.strip(); start_param = param.replace("start=","").strip()
            else: bot_username = link.strip(); start_param = ""
            await client.send_message(bot_username, f"/start {start_param}" if start_param else "/start")
            await asyncio.sleep(0.5)
            async for msg in client.get_chat_history(bot_username, limit=10):
                if not msg.text and not msg.caption: continue
                text = msg.text or msg.caption or ""
                result = solve_math_captcha(text)
                if result is not None:
                    if await self.click_button_by_text(client, msg, bot_username, str(result)): return True, f"✅ {name} - كابتشا: {result}"
                target_emoji = extract_emoji_from_captcha(text)
                if target_emoji:
                    if await self.click_button_by_text(client, msg, bot_username, target_emoji): return True, f"✅ {name} - إيموجي: {target_emoji}"
                code = solve_captcha_numbers(text)
                if code:
                    if await self.click_button_by_text(client, msg, bot_username, code): return True, f"✅ {name} - رقم: {code}"
            return True, f"✅ {name} - بدون كابتشا"
        except Exception as e: return False, f"❌ {name} - {str(e)}"
    async def mass_giveaway_with_captcha(self, uid, accs, channel, giveaway_link, msg=None):
        async def func(c, name): return await self.do_giveaway_with_captcha(c, channel, giveaway_link, name)
        return await self.mass_execute(uid, accs, func, msg, "🎁🔐", 100)
    async def vote_with_captcha_buttons(self, client, channel, vote_link, name=""):
        try:
            await self.join_ch(client, channel); await asyncio.sleep(0.3)
            link = vote_link.replace("https://t.me/","").replace("http://t.me/","")
            if "?" not in link: return False, f"❌ {name} - رابط غير صالح"
            bot_username, param = link.split("?", 1)
            bot_username = bot_username.strip(); start_param = param.replace("start=", "").strip()
            send_time = time.time()
            await client.send_message(bot_username, f"/start {start_param}")
            await asyncio.sleep(1.2)
            target_msg = None
            async for msg in client.get_chat_history(bot_username, limit=10):
                if msg.date and msg.date.timestamp() < send_time - 5: continue
                text = msg.text or msg.caption or ""
                if msg.reply_markup and text:
                    target_msg = msg; break
            if not target_msg: return True, f"✅ {name} - بدون كابتشا"
            text = target_msg.text or target_msg.caption or ""
            buttons = target_msg.reply_markup.inline_keyboard
            result = solve_math_captcha(text)
            if result is not None:
                if await self.click_button_by_text(client, target_msg, bot_username, str(result)):
                    await asyncio.sleep(0.5); return True, f"✅ {name} - رياضيات: {result}"
            target = extract_target_emoji(text)
            if target:
                btn = find_emoji_button(buttons, target)
                if btn:
                    if await self.click_button_obj(client, target_msg, bot_username, btn):
                        await asyncio.sleep(0.5); return True, f"✅ {name} - إيموجي: {target}"
            if is_emoji_captcha_text(text) and buttons:
                return await self._premium_emoji_trial(client, target_msg, bot_username, name)
            code = solve_captcha_numbers(text)
            if code:
                if await self.click_button_by_text(client, target_msg, bot_username, code):
                    await asyncio.sleep(0.5); return True, f"✅ {name} - رقم: {code}"
            return True, f"✅ {name} - بدون كابتشا"
        except Exception as e:
            return False, f"❌ {name} - {str(e)}"
    async def _premium_emoji_trial(self, client, target_msg, bot_username, name=""):
        try:
            current_msg = target_msg
            total_tries = 0; max_tries = 12
            visited_msg_ids = set()
            while total_tries < max_tries:
                if not current_msg.reply_markup: break
                if current_msg.id in visited_msg_ids: break
                visited_msg_ids.add(current_msg.id)
                buttons = current_msg.reply_markup.inline_keyboard
                all_btns = [b for row in buttons for b in row if b.callback_data]
                if not all_btns: break
                advanced_to_new = False
                for idx, btn in enumerate(all_btns):
                    total_tries += 1
                    if total_tries > max_tries: break
                    try: await client.request_callback_answer(bot_username, current_msg.id, btn.callback_data)
                    except: continue
                    await asyncio.sleep(0.8)
                    latest = None
                    try:
                        async for nm in client.get_chat_history(bot_username, limit=4):
                            if nm.id == current_msg.id: continue
                            latest = nm; break
                    except: pass
                    if not latest: continue
                    latest_text = latest.text or latest.caption or ""
                    if not is_emoji_captcha_text(latest_text):
                        return True, f"✅ {name} - إيموجي"
                    if latest.reply_markup and is_emoji_captcha_text(latest_text):
                        current_msg = latest; advanced_to_new = True; break
                if not advanced_to_new: break
            return False, f"❌ {name} - فشل الإيموجي"
        except Exception as e:
            return False, f"❌ {name} - {str(e)}"
    async def mass_vote_captcha_turbo(self, uid, accs, channel, vote_link, required_votes, msg=None):
        successful = 0; failed = 0; used_indices = set(); cancel_flags[uid] = False; start = time.time()
        async def process_vote(acc):
            client = await self.get_client(acc['user_id'])
            if not client: return False
            name = acc['first_name'] or str(acc['user_id'])
            success, _ = await self.vote_with_captcha_buttons(client, channel, vote_link, name)
            return success
        while successful < required_votes and len(used_indices) < len(accs):
            if cancel_flags.get(uid, False): break
            available = [i for i in range(len(accs)) if i not in used_indices]
            if not available: break
            batch_indices = available[:20]
            for idx in batch_indices: used_indices.add(idx)
            results = await asyncio.gather(*[process_vote(accs[idx]) for idx in batch_indices])
            for success in results:
                if success:
                    successful += 1
                    if successful >= required_votes: break
                else: failed += 1
            if msg:
                try: await msg.edit_text(f"🗳⚡ {successful}/{required_votes}\n❌ {failed}", reply_markup=cancel_button())
                except: pass
        return successful, failed, time.time()-start, cancel_flags.get(uid, False)
    async def mass_vote_scheduled(self, uid, accs, channel, vote_link, votes_per_interval, interval_seconds, msg=None):
        successful = 0; failed = 0; used_indices = set(); cancel_flags[uid] = False; start = time.time()
        while not cancel_flags.get(uid, False):
            batch_success = 0; tasks = []
            for _ in range(votes_per_interval):
                if cancel_flags.get(uid, False): break
                available = [i for i in range(len(accs)) if i not in used_indices]
                if not available: used_indices.clear(); available = list(range(len(accs)))
                idx = random.choice(available); used_indices.add(idx); acc = accs[idx]
                client = await self.get_client(acc['user_id'])
                if not client: failed += 1; continue
                name = acc['first_name'] or str(acc['user_id'])
                tasks.append(self.vote_with_captcha_buttons(client, channel, vote_link, name))
            if tasks:
                results = await asyncio.gather(*tasks)
                for success, _ in results:
                    if success: successful += 1; batch_success += 1
                    else: failed += 1
            if msg:
                try: await msg.edit_text(f"🗳⏰ ✅ {successful}\n📊 {batch_success}/{votes_per_interval}", reply_markup=cancel_button())
                except: pass
            await asyncio.sleep(interval_seconds)
        return successful, failed, time.time()-start, True
    async def do_roulette(self, client, roulette_link, name=""):
        try:
            link = roulette_link.replace("https://t.me/", "").replace("http://t.me/", "").strip()
            parts = link.split("/")
            if parts[0] == "c" and len(parts) >= 3:
                chat_id = int("-100" + parts[1]); msg_id = int(parts[2])
            elif len(parts) >= 2:
                chat_id = parts[0]; msg_id = int(parts[1])
            else: return False, f"❌ {name} - رابط غير صالح"
            if not str(chat_id).startswith("-100"):
                try: await client.join_chat(f"@{chat_id}")
                except UserAlreadyParticipant: pass
                except Exception: pass
            await asyncio.sleep(1)
            msg = None
            for attempt in range(3):
                try:
                    msg = await client.get_messages(chat_id, msg_id)
                    if msg: break
                except: await asyncio.sleep(1)
            if not msg: return False, f"❌ {name} - لا يمكن قراءة الرسالة"
            here_url = None
            for ent in (msg.entities or msg.caption_entities or []):
                url = getattr(ent, 'url', None)
                if url and "t.me/" in url: here_url = url; break
            if not here_url and msg.reply_markup:
                for row in msg.reply_markup.inline_keyboard:
                    for btn in row:
                        if btn.url and "t.me/" in btn.url: here_url = btn.url; break
                    if here_url: break
            if not here_url:
                text = msg.text or msg.caption or ""
                url_match = re.search(r'https?://t\.me/[^\s]+', text)
                if url_match: here_url = url_match.group(0)
            if here_url: await self._follow_and_handle_conditions(client, here_url, name)
            await asyncio.sleep(3)
            try:
                msg_fresh = await client.get_messages(chat_id, msg_id)
                if msg_fresh and msg_fresh.reply_markup:
                    for row in msg_fresh.reply_markup.inline_keyboard:
                        for btn in row:
                            txt = (btn.text or "").strip()
                            if any(k in txt for k in ["المشاركة", "شارك", "سحب", "اشترك"]):
                                try:
                                    if btn.callback_data:
                                        await client.request_callback_answer(chat_id, msg_id, btn.callback_data)
                                    elif btn.url:
                                        await self._follow_and_handle_conditions(client, btn.url, name)
                                    await asyncio.sleep(1)
                                except: pass
                                break
            except: pass
            return True, f"✅ {name}"
        except Exception as e:
            return False, f"❌ {name} - {str(e)}"
    async def _follow_and_handle_conditions(self, client, url, name=""):
        try:
            clean = url.replace("https://t.me/", "").replace("http://t.me/", "").strip()
            if "?" in clean:
                bot_username, param = clean.split("?", 1)
                param = param.replace("start=", "").replace("startgroup=", "").strip()
                send_time = time.time()
                await client.send_message(bot_username.strip(), f"/start {param}")
                await asyncio.sleep(3)
                await self._process_bot_flow(client, bot_username.strip(), name, send_time, max_rounds=8)
                return
            elif clean.count("/") >= 1:
                parts = clean.split("/")
                if parts[0] == "c" and len(parts) >= 3:
                    inner_chat = int("-100" + parts[1]); inner_id = int(parts[2])
                else:
                    inner_chat = parts[0]; inner_id = int(parts[1])
                if not str(inner_chat).startswith("-100"):
                    try: await client.join_chat(f"@{inner_chat}"); await asyncio.sleep(1.5)
                    except: pass
                try:
                    inner_msg = await client.get_messages(inner_chat, inner_id)
                    if inner_msg and inner_msg.reply_markup:
                        for row in inner_msg.reply_markup.inline_keyboard:
                            for btn in row:
                                if btn.url and "t.me/" in btn.url:
                                    await self._follow_and_handle_conditions(client, btn.url, name); return
                                elif btn.callback_data:
                                    try:
                                        await client.request_callback_answer(inner_chat, inner_id, btn.callback_data)
                                        await asyncio.sleep(1)
                                    except: pass
                                    return
                except: pass
        except: pass
    async def _process_bot_flow(self, client, bot_username, name="", send_time=None, max_rounds=8):
        if send_time is None: send_time = time.time()
        for round_num in range(max_rounds):
            target_msg = None
            try:
                async for m in client.get_chat_history(bot_username, limit=8):
                    if m.date and m.date.timestamp() < send_time - 10: continue
                    if m.reply_markup: target_msg = m; break
            except: pass
            if not target_msg: break
            text = target_msg.text or target_msg.caption or ""
            buttons = target_msg.reply_markup.inline_keyboard
            is_join_request = any(k in text for k in ["انضم", "اشترك", "قناة", "قناه", "تفضل بالانضمام", "يجب الانضمام", "شترك بالقناه", "عليك الانضمام", "الاشتراك", "للاشتراك", "كون مشترك"])
            if is_join_request:
                channels = re.findall(r'@([A-Za-z0-9_]{4,})', text)
                links = re.findall(r't\.me/([A-Za-z0-9_]+)', text)
                all_channels = list(set(channels + links))
                skip = ["joinchat", "addstickers", "share", "c", "s", "iv", "proxy"]
                all_channels = [c for c in all_channels if c.lower() not in skip]
                joined_any = False
                for ch in all_channels:
                    try: await client.join_chat(f"@{ch}"); joined_any = True; await asyncio.sleep(1.2)
                    except UserAlreadyParticipant: joined_any = True
                    except FloodWait: await asyncio.sleep(2)
                    except: pass
                await asyncio.sleep(0.5)
                verify_clicked = False
                for row in buttons:
                    for btn in row:
                        btn_text = (btn.text or "").strip()
                        if any(k in btn_text for k in ["تحقق", "تأكيد", "انضممت", "تم", "متابعة", "متابعه", "التحقق"]):
                            try:
                                if btn.callback_data:
                                    await client.request_callback_answer(bot_username, target_msg.id, btn.callback_data)
                                elif btn.url:
                                    await self._follow_and_handle_conditions(client, btn.url, name)
                                await asyncio.sleep(2); verify_clicked = True; send_time = time.time()
                            except: pass
                            break
                    if verify_clicked: break
                if joined_any:
                    await asyncio.sleep(2); send_time = time.time(); continue
                else: break
            result = solve_math_captcha(text)
            if result is not None:
                if await self.click_button_by_text(client, target_msg, bot_username, str(result)):
                    await asyncio.sleep(2); send_time = time.time(); continue
            tgt = extract_target_emoji(text)
            if tgt:
                btn = find_emoji_button(buttons, tgt)
                if btn:
                    if await self.click_button_obj(client, target_msg, bot_username, btn):
                        await asyncio.sleep(2); send_time = time.time(); continue
            if is_emoji_captcha_text(text) and buttons:
                await self._premium_emoji_trial(client, target_msg, bot_username, name)
                await asyncio.sleep(2); send_time = time.time(); continue
            code = solve_captcha_numbers(text)
            if code:
                if await self.click_button_by_text(client, target_msg, bot_username, code):
                    await asyncio.sleep(2); send_time = time.time(); continue
            success_btn = False
            for row in buttons:
                for btn in row:
                    btn_text = (btn.text or "").strip()
                    if any(k in btn_text for k in ["المشاركة", "اشترك", "شارك", "سجل", "تسجيل"]):
                        try:
                            if btn.callback_data:
                                await client.request_callback_answer(bot_username, target_msg.id, btn.callback_data)
                            elif btn.url:
                                await self._follow_and_handle_conditions(client, btn.url, name)
                            await asyncio.sleep(1.5); send_time = time.time(); success_btn = True
                        except: pass
                        break
                if success_btn: break
            if success_btn: continue
            break
    async def mass_roulette_scheduled(self, uid, accs, roulette_link, interval_seconds, msg=None):
        successful = 0; failed = 0
        cancel_flags[uid] = False
        start = time.time()
        total = len(accs)
        for i, acc in enumerate(accs):
            if cancel_flags.get(uid, False): break
            client = await self.get_client(acc['user_id'])
            if not client:
                failed += 1
                await send_log(f"❌ [{acc.get('first_name') or acc['user_id']}] جلسة غير شغالة", silent=True)
            else:
                name = acc['first_name'] or str(acc['user_id'])
                try:
                    success, _ = await self.do_roulette(client, roulette_link, name)
                    if success:
                        successful += 1
                        await send_log(f"✅ [{name}] روليت ناجح", silent=True)
                    else:
                        failed += 1
                        await send_log(f"❌ [{name}] فشل", silent=True)
                except Exception as e:
                    failed += 1
                    await send_log(f"❌ [{name}] استثناء: `{type(e).__name__}`", silent=True)
            if msg:
                try: await msg.edit_text(f"🎰 {i+1}/{total}\n✅ {successful} | ❌ {failed}\n⏱ كل {interval_seconds}ث", reply_markup=cancel_button())
                except: pass
            if i < total - 1:
                for _ in range(interval_seconds):
                    if cancel_flags.get(uid, False): break
                    await asyncio.sleep(1)
        return successful, failed, time.time() - start, cancel_flags.get(uid, False)

    # ═══════════════════════════════════════════════════════════
    # 💬 رشق التعليقات — v4 (تعليق تحت المنشور + Log كامل)
    # ═══════════════════════════════════════════════════════════
    async def mass_comment_multi(self, uid, accs, channel_id, msg_id, words, interval_seconds, msg=None):
        successful = 0; failed = 0
        cancel_flags[uid] = False
        start = time.time()
        total = len(accs)
        for i, acc in enumerate(accs):
            if cancel_flags.get(uid, False): break
            client = await self.get_client(acc['user_id'])
            name = acc['first_name'] or str(acc['user_id'])
            if not client:
                failed += 1
                await send_log(f"❌ [{name}] جلسة غير شغالة", silent=True)
            else:
                try:
                    await client.join_chat(channel_id)
                    await asyncio.sleep(0.5)
                except UserAlreadyParticipant: pass
                except Exception as e:
                    await send_log(f"⚠️ [{name}] فشل انضمام: `{type(e).__name__}`", silent=True)
                word = random.choice(words)
                try:
                    success = await post_comment(client, channel_id, msg_id, word, name)
                except Exception as e:
                    success = False
                    await send_log(f"❌ [{name}] استثناء: `{type(e).__name__}: {str(e)[:80]}`", silent=True)
                if success:
                    successful += 1
                    await send_log(f"✅ [{name}] نُشر تحت المنشور: `{word}`", silent=True)
                else:
                    failed += 1
                    await send_log(f"❌ [{name}] فشل التعليق", silent=True)
            if msg:
                try: await msg.edit_text(f"💬 {i+1}/{total}\n✅ {successful} | ❌ {failed}\n⏱ كل {interval_seconds}ث", reply_markup=cancel_button())
                except: pass
            if i < total - 1:
                for _ in range(interval_seconds):
                    if cancel_flags.get(uid, False): break
                    await asyncio.sleep(1)
        return successful, failed, time.time() - start, cancel_flags.get(uid, False)

    async def mass_comment_single(self, uid, accs, channel_id, msg_id, word, interval_seconds, msg=None):
        successful = 0; failed = 0
        cancel_flags[uid] = False
        start = time.time()
        total = len(accs)
        for i, acc in enumerate(accs):
            if cancel_flags.get(uid, False): break
            client = await self.get_client(acc['user_id'])
            name = acc['first_name'] or str(acc['user_id'])
            if not client:
                failed += 1
                await send_log(f"❌ [{name}] جلسة غير شغالة", silent=True)
            else:
                try:
                    await client.join_chat(channel_id)
                    await asyncio.sleep(0.5)
                except UserAlreadyParticipant: pass
                except Exception as e:
                    await send_log(f"⚠️ [{name}] فشل انضمام: `{type(e).__name__}`", silent=True)
                try:
                    success = await post_comment(client, channel_id, msg_id, word, name)
                except Exception as e:
                    success = False
                    await send_log(f"❌ [{name}] استثناء: `{type(e).__name__}: {str(e)[:80]}`", silent=True)
                if success:
                    successful += 1
                    await send_log(f"✅ [{name}] نُشر تحت المنشور: `{word}`", silent=True)
                else:
                    failed += 1
                    await send_log(f"❌ [{name}] فشل التعليق", silent=True)
            if msg:
                try: await msg.edit_text(f"💬 {i+1}/{total}\n✅ {successful} | ❌ {failed}\n📝 {word}", reply_markup=cancel_button())
                except: pass
            if i < total - 1:
                for _ in range(interval_seconds):
                    if cancel_flags.get(uid, False): break
                    await asyncio.sleep(1)
        return successful, failed, time.time() - start, cancel_flags.get(uid, False)
    # ═══════════════════════════════════════════════════════════

    async def clean_account_fast(self, client, name=""):
        left_count = 0; failed_count = 0
        try:
            dialogs = []
            async for dialog in client.get_dialogs():
                if dialog.chat.type in [ChatType.CHANNEL, ChatType.SUPERGROUP, ChatType.GROUP]: dialogs.append(dialog.chat.id)
            if dialogs:
                results = await asyncio.gather(*[client.leave_chat(chat_id) for chat_id in dialogs], return_exceptions=True)
                for r in results:
                    if isinstance(r, Exception): failed_count += 1
                    else: left_count += 1
            return True, left_count, failed_count
        except: return False, left_count, failed_count
    async def mass_clean_accounts_turbo(self, uid, accs, msg=None):
        successful = 0; failed = 0; total_left = 0; total_failed = 0
        cancel_flags[uid] = False; start = time.time()
        for i in range(0, len(accs), 50):
            if cancel_flags.get(uid, False): break
            batch = accs[i:i+50]
            async def process_acc(acc):
                client = await self.get_client(acc['user_id'])
                if not client: return None
                return await self.clean_account_fast(client)
            results = await asyncio.gather(*[process_acc(acc) for acc in batch])
            for result in results:
                if result is None: failed += 1
                else:
                    success, left_count, fail_count = result
                    if success: successful += 1; total_left += left_count; total_failed += fail_count
                    else: failed += 1
            if msg:
                try: await msg.edit_text(f"🧹⚡ {successful}/{len(accs)}", reply_markup=cancel_button())
                except: pass
        return successful, failed, total_left, total_failed, time.time()-start, cancel_flags.get(uid, False)
    async def mass_execute(self, uid, accs, func, msg=None, label="⚡", batch_size=200):
        total = len(accs); ok, fail = 0, 0; start = time.time(); cancel_flags[uid] = False
        for i in range(0, total, batch_size):
            if cancel_flags.get(uid, False):
                if msg: await msg.edit_text(f"⏹ ألغي\n✅ {ok} | ❌ {fail}")
                return ok, fail, time.time()-start, True
            batch = accs[i:i+batch_size]
            async def prep(a):
                c = await self.get_client(a['user_id'])
                return c, a['first_name'] or a['phone'] or str(a['user_id'])
            prepped = await asyncio.gather(*[prep(a) for a in batch])
            tasks = [func(c, name) for c, name in prepped if c]
            fail += sum(1 for c, _ in prepped if not c)
            if tasks:
                results = await asyncio.gather(*tasks)
                for success, _ in results:
                    if success: ok += 1
                    else: fail += 1
            if msg:
                try: await msg.edit_text(f"{label} {min(i+batch_size, total)}/{total}\n✅ {ok} | ❌ {fail}", reply_markup=cancel_button())
                except: pass
        return ok, fail, time.time()-start, False
    async def do_ref(self, client, bot_link, channels, name=""):
        try:
            if channels:
                for ch in channels: await self.join_ch(client, ch)
            link = bot_link.replace("https://t.me/","").replace("http://t.me/","")
            if "?" in link:
                bot, param = link.split("?",1); await client.send_message(bot.strip(), f"/start {param.replace('start=','').strip()}")
            else: await client.send_message(link.strip(), "/start")
            return True, f"✅ {name}"
        except: return False, f"❌ {name}"
    async def mass_ref(self, uid, accs, link, channels, msg=None):
        async def func(c, name): return await self.do_ref(c, link, channels, name)
        return await self.mass_execute(uid, accs, func, msg, "⚡", 200)
    async def send_reaction(self, client, post_link, emoji, name=""):
        try:
            parts = post_link.replace("https://t.me/","").replace("http://t.me/","").split("/")
            if len(parts) >= 2: chat_username, message_id = parts[0], int(parts[1])
            else: return False
            await client.send_reaction(chat_username, message_id, emoji)
            return True, f"✅ {name}"
        except: return False
    async def mass_reactions_turbo(self, uid, accs, post_link, emoji_list=None, random_emoji=False, msg=None):
        successful = 0; failed = 0; cancel_flags[uid] = False; start = time.time()
        async def process_acc(acc):
            client = await self.get_client(acc['user_id'])
            if not client: return False
            if random_emoji: emoji = random.choice(SPECIAL_EMOJIS)
            elif emoji_list: emoji = random.choice(emoji_list)
            else: emoji = random.choice(NORMAL_EMOJIS)
            return await self.send_reaction(client, post_link, emoji)
        for i in range(0, len(accs), 100):
            if cancel_flags.get(uid, False): break
            results = await asyncio.gather(*[process_acc(acc) for acc in accs[i:i+100]])
            for r in results:
                if r: successful += 1
                else: failed += 1
            if msg:
                try: await msg.edit_text(f"🎭⚡ {min(i+100, len(accs))}/{len(accs)}", reply_markup=cancel_button())
                except: pass
        return successful, failed, time.time()-start, cancel_flags.get(uid, False)
    async def mass_reactions(self, uid, accs, post_link, emoji=None, random_emoji=False, emoji_list=None, msg=None, turbo=False):
        return await self.mass_reactions_turbo(uid, accs, post_link, emoji_list=emoji_list, random_emoji=random_emoji, msg=msg)
    async def turbo_join(self, uid, channels, msg=None):
        accs = db.all_acc()
        if not accs: return 0, 0, 0
        ok, fail = 0, 0; start = time.time()
        for ch in channels:
            ch = ch.strip()
            if not ch.startswith("@"): ch = "@" + ch
            clients = []
            for acc in accs:
                client = await self.get_client(acc['user_id'])
                if client: clients.append(client)
            results = await asyncio.gather(*[self.join_ch(client, ch) for client in clients])
            for success in results:
                if success: ok += 1
                else: fail += 1
        return ok, fail, time.time()-start
    async def check_spam(self, bot_client, msg):
        accs = db.all_acc()
        if not accs: await msg.edit_text("❌ لا حسابات"); return
        ok_count = banned_count = 0
        for acc in accs:
            client = await self.get_client(acc['user_id'])
            if not client: banned_count += 1; continue
            try:
                await client.send_message("SpamBot", "/start"); await asyncio.sleep(0.3)
                async for spam_msg in client.get_chat_history("SpamBot", limit=1):
                    if spam_msg.text:
                        if "رائع" in spam_msg.text or "free" in spam_msg.text.lower(): ok_count += 1
                        else: banned_count += 1
            except: banned_count += 1
        await msg.edit_text(f"🔍 ✅ {ok_count} | ⚠️ {banned_count}", reply_markup=menu(OWNER_ID))
    async def get_otp_for_account(self, acc):
        client = await self.get_client(acc['user_id'])
        if not client: return False, "الحساب غير شغال", None
        otp_code = None; two_step = acc.get('two_step', '')
        try:
            async for dialog in client.get_dialogs(limit=20):
                if dialog.chat.type == ChatType.PRIVATE:
                    try:
                        async for msg in client.get_chat_history(dialog.chat.id, limit=15):
                            if msg.text:
                                for pat in [r'(?:login code|code|otp|رمز)[:\s]*(\d{5,6})', r'\b(\d{5,6})\b']:
                                    m = re.search(pat, msg.text, re.IGNORECASE)
                                    if m: otp_code = m.group(1); break
                                if otp_code: break
                    except: pass
                if otp_code: break
            if otp_code: return True, otp_code, two_step
            return False, "لا يوجد رمز OTP", two_step
        except Exception as e: return False, str(e), two_step

am = AM()
states = {}; tmp = {}

def cancel_button():
    return InlineKeyboardMarkup([[KbBtn("⏹ إلغاء", callback_data="cancel_op", style="danger")]])

def menu(uid):
    btns = [
        [KbBtn("👤 الحسابات", callback_data="menu_acc", style="primary")],
        [KbBtn("🚀 رشق إحالات", callback_data="menu_ref", style="primary")],
        [KbBtn("🗳 تصويتات السراب وتناهيد ✨", callback_data="menu_vote", style="primary")],
        [KbBtn("🎰 رشق روليتات + تعليقات", callback_data="menu_roulette", style="primary")],
        [KbBtn("🎭 التفاعلات", callback_data="menu_react", style="primary")],
        [KbBtn("🛠 أدوات", callback_data="menu_tools", style="primary")],
    ]
    if uid == OWNER_ID:
        btns.append([KbBtn("👑 المشرفين", callback_data="admin_manage", style="primary")])
        btns.append([KbBtn("📢 اللوق", callback_data="log_menu", style="primary")])
    btns.append([KbBtn("❌ حذف الجميع", callback_data="delete_all", style="danger")])
    return InlineKeyboardMarkup(btns)

def menu_acc():
    return InlineKeyboardMarkup([
        [KbBtn("➕ إضافة حساب", callback_data="add", style="success"), KbBtn("👤 عرض الحسابات", callback_data="list", style="primary")],
        [KbBtn("🔑 جلب OTP", callback_data="otp", style="primary")],
        [KbBtn("📥 استيراد JSON", callback_data="import_s", style="success"), KbBtn("📤 تصدير JSON", callback_data="export_json", style="primary")],
        [KbBtn("🔙 رجوع", callback_data="main", style="primary")],
    ])
def menu_ref():
    return InlineKeyboardMarkup([
        [KbBtn("🚀 رشق عادي", callback_data="ref", style="primary"), KbBtn("⚡ رشق فائق", callback_data="ref_turbo", style="primary")],
        [KbBtn("🔐 رشق بكابتشا", callback_data="ref_captcha", style="primary")],
        [KbBtn("🔙 رجوع", callback_data="main", style="primary")],
    ])
def menu_vote():
    return InlineKeyboardMarkup([
        [KbBtn("🗳 تصويت عادي", callback_data="vote", style="primary"), KbBtn("⚡ تصويت فائق", callback_data="vote_fast", style="primary")],
        [KbBtn("⏰ تصويت بمدة", callback_data="vote_scheduled", style="primary")],
        [KbBtn("🔙 رجوع", callback_data="main", style="primary")],
    ])
def menu_roulette():
    return InlineKeyboardMarkup([
        [KbBtn("🎰 رشق روليت مع شرط", callback_data="roulette", style="primary")],
        [KbBtn("💬 رشق تعليقات متعددة", callback_data="comment_multi", style="primary")],
        [KbBtn("💬 رشق تعليق واحد", callback_data="comment_single", style="primary")],
        [KbBtn("🔙 رجوع", callback_data="main", style="primary")],
    ])
def menu_react():
    return InlineKeyboardMarkup([
        [KbBtn("🎭 تفاعل عادي", callback_data="react_normal", style="primary"), KbBtn("⚡ تفاعل فائق", callback_data="react_turbo", style="primary")],
        [KbBtn("🔙 رجوع", callback_data="main", style="primary")],
    ])
def menu_tools():
    return InlineKeyboardMarkup([
        [KbBtn("📢 رشق قنوات", callback_data="join_ch", style="primary")],
        [KbBtn("🧹 تنظيف الحسابات", callback_data="clean_accounts", style="danger")],
        [KbBtn("🛡 فحص سبام", callback_data="spam_check", style="primary")],
        [KbBtn("🔙 رجوع", callback_data="main", style="primary")],
    ])
def admin_manage_menu():
    return InlineKeyboardMarkup([
        [KbBtn("➕ إضافة مشرف", callback_data="admin_add", style="success")],
        [KbBtn("📋 قائمة المشرفين", callback_data="admin_list", style="primary")],
        [KbBtn("🗑 حذف مشرف", callback_data="admin_remove", style="danger")],
        [KbBtn("🔙 رجوع", callback_data="main", style="primary")],
    ])
def log_menu():
    current = db.get_log_chat()
    status = f"`{current}`" if current else "❌ غير مربوط"
    return InlineKeyboardMarkup([
        [KbBtn(f"📍 الحالة: {status}", callback_data="noop", style="primary")],
        [KbBtn("🧪 اختبار", callback_data="log_test", style="success"), KbBtn("🗑 إلغاء الربط", callback_data="log_unlink", style="danger")],
        [KbBtn("🔙 رجوع", callback_data="main", style="primary")],
    ])
def duration_menu():
    return InlineKeyboardMarkup([
        [KbBtn("⏱ دقائق", callback_data="dur_minutes", style="primary"), KbBtn("⏰ ساعات", callback_data="dur_hours", style="primary")],
        [KbBtn("📅 أيام", callback_data="dur_days", style="primary"), KbBtn("📅 أسابيع", callback_data="dur_weeks", style="primary")],
        [KbBtn("📅 شهور", callback_data="dur_months", style="primary"), KbBtn("♾ دائم", callback_data="dur_forever", style="success")],
    ])
def otp_accounts_menu(page=0):
    accs = db.all_acc()
    if not accs: return None, 0
    per_page = 10
    total_pages = (len(accs) + per_page - 1) // per_page
    page = max(0, min(page, total_pages - 1))
    start_idx = page * per_page; end_idx = min(start_idx + per_page, len(accs))
    btns = []
    for acc in accs[start_idx:end_idx]:
        name = acc['first_name'] or acc['phone'] or str(acc['user_id'])
        btns.append([KbBtn(f"👤 {name}", callback_data=f"otp_acc_{acc['id']}", style="primary")])
    nav_btns = []
    if page > 0: nav_btns.append(KbBtn("⬅️", callback_data=f"otp_page_{page-1}", style="primary"))
    if page < total_pages - 1: nav_btns.append(KbBtn("➡️", callback_data=f"otp_page_{page+1}", style="primary"))
    if nav_btns: btns.append(nav_btns)
    btns.append([KbBtn("🔙 رجوع", callback_data="main", style="primary")])
    return InlineKeyboardMarkup(btns), page

async def start_msg(c, m):
    uid = m.from_user.id
    if not db.is_admin(uid): return await m.reply("⛔ غير مصرح")
    db.check_expired(); cancel_flags[uid] = True; states.pop(uid, None); tmp.pop(uid, None)
    text = (
        "<b>╔══════════════════════╗</b>\n"
        "<b>   🤖 بوت رشق الإحالات</b>\n"
        "<b>╚══════════════════════╝</b>\n\n"
        f"<blockquote>👥 <b>الحسابات:</b> <code>{db.count()}</code>\n"
        f"👑 <b>المالك:</b> <code>{OWNER_ID}</code>\n"
        f"⚡ <b>الحالة:</b> <i>يعمل ✅</i></blockquote>\n\n"
        "<b>📋 اختر القسم المطلوب من الأسفل 👇</b>"
    )
    await m.reply(text, reply_markup=menu(uid))

async def l_command(c, m):
    uid = m.from_user.id
    if not db.is_admin(uid): return await m.reply("⛔ غير مصرح")
    parts = m.text.split()
    if len(parts) < 2: return await m.reply("📝 `/l @BotUsername`")
    bot = parts[1].strip(); msg = await m.reply(f"🔍 فحص {bot}...")
    accs = db.all_acc(); active = inactive = 0
    for acc in accs:
        client = await am.get_client(acc['user_id'])
        if client:
            try: await client.send_message(bot, "/start"); active += 1
            except: inactive += 1
        else: inactive += 1
    await msg.edit_text(f"🔍 **{bot}**\n✅ {active} | ❌ {inactive}", reply_markup=menu(uid))

async def spam_command(c, m):
    uid = m.from_user.id
    if not db.is_admin(uid): return await m.reply("⛔ غير مصرح")
    msg = await m.reply("🛡 جاري فحص السبام...")
    await am.check_spam(c, msg)

async def cb_handler(c, cb):
    uid = cb.from_user.id
    if not db.is_admin(uid): return await cb.answer("⛔ غير مصرح", show_alert=True)
    d = cb.data; mu = menu(uid)
    if d == "cancel_op": cancel_flags[uid] = True; await cb.answer("⏹"); return
    if d == "main": await cb.message.edit_text("📋:", reply_markup=mu)
    elif d == "noop": await cb.answer("📋", show_alert=True)
    elif d == "menu_acc": await cb.message.edit_text("👤 **الحسابات**\n\nاختر:", reply_markup=menu_acc())
    elif d == "menu_ref": await cb.message.edit_text("🚀 **رشق إحالات**\n\nاختر:", reply_markup=menu_ref())
    elif d == "menu_vote": await cb.message.edit_text("🗳 **تصويتات**\n\nاختر:", reply_markup=menu_vote())
    elif d == "menu_roulette": await cb.message.edit_text("🎰 **رشق روليتات + تعليقات**\n\nاختر:", reply_markup=menu_roulette())
    elif d == "menu_react": await cb.message.edit_text("🎭 **التفاعلات**\n\nاختر:", reply_markup=menu_react())
    elif d == "menu_tools": await cb.message.edit_text("🛠 **أدوات**\n\nاختر:", reply_markup=menu_tools())
    elif d == "log_menu":
        if uid != OWNER_ID: return await cb.answer("🔒", show_alert=True)
        await cb.message.edit_text("📢 **إعدادات اللوق**\n\nلربط: أرسل `/setlog` في القروب\nاللوق يعرض: اسم المشرف + الرابط + كل حساب", reply_markup=log_menu())
    elif d == "log_test":
        if uid != OWNER_ID: return await cb.answer("🔒", show_alert=True)
        name, username = await get_user_info(uid)
        await send_log(f"🧪 **تجربة اللوق**\n👤 {name} | {username}\n⏰ `{datetime.now().strftime('%H:%M:%S')}`")
        await cb.answer("✅ تم الإرسال", show_alert=True)
    elif d == "log_unlink":
        if uid != OWNER_ID: return await cb.answer("🔒", show_alert=True)
        db.set_setting("log_chat_id", "")
        await cb.message.edit_text("✅ **تم إلغاء الربط**", reply_markup=log_menu())
    elif d == "delete_all":
        db.del_all()
        name, username = await get_user_info(uid)
        await send_log(f"🗑 **حذف جميع الحسابات**\n👤 {name} | {username}")
        await cb.message.edit_text("🗑 **تم حذف جميع الحسابات!**", reply_markup=menu(uid))
    elif d == "add": states[uid] = "phone"; await cb.message.edit_text("📱 أرسل رقم الهاتف:", reply_markup=menu_acc())
    elif d == "list":
        accs = db.all_acc()
        txt = f"👤 **{len(accs)} حساب**\n\n" + "\n".join([f"{i}. {a['first_name'] or 'بدون'}" for i, a in enumerate(accs, 1)]) if accs else "❌ لا توجد حسابات"
        await cb.message.edit_text(txt, reply_markup=menu_acc())
    elif d == "otp":
        if db.count() == 0: return await cb.message.edit_text("❌ لا توجد حسابات", reply_markup=menu_acc())
        otp_menu, page = otp_accounts_menu(0)
        await cb.message.edit_text(f"🔑 **اختر الحساب:**", reply_markup=otp_menu)
    elif d.startswith("otp_page_"):
        page = int(d.split("_")[2]); otp_menu, current_page = otp_accounts_menu(page)
        await cb.message.edit_text(f"🔑 **اختر الحساب:**", reply_markup=otp_menu)
    elif d.startswith("otp_acc_"):
        acc_id = int(d.split("_")[2]); acc = db.get_by_id(acc_id)
        if not acc: return await cb.answer("❌ الحساب غير موجود", show_alert=True)
        name = acc['first_name'] or acc['phone'] or str(acc['user_id'])
        phone = acc['phone'] or 'بدون'; user_id = acc['user_id'] or 'غير معروف'
        username = acc['username'] or 'بدون'; two_step = acc.get('two_step', '')
        info_text = f"👤 **معلومات الحساب**\n\n📱 الرقم: {phone}\n👤 الاسم: {name}\n🆔 الآيدي: {user_id}\n📝 اليوزر: @{username}\n"
        if two_step: info_text += f"🔐 2FA: {two_step}\n"
        kb = InlineKeyboardMarkup([
            [KbBtn("🔑 جلب OTP", callback_data=f"get_otp_{acc_id}", style="success")],
            [KbBtn("➡️ الحساب التالي", callback_data=f"next_acc_{acc_id}", style="primary")],
            [KbBtn("🔙 رجوع", callback_data="otp", style="primary")]
        ])
        await cb.message.edit_text(info_text, reply_markup=kb)
    elif d.startswith("next_acc_"):
        current_id = int(d.split("_")[2]); accs = db.all_acc()
        if not accs: return await cb.answer("❌", show_alert=True)
        next_acc = None; found_current = False
        for acc in accs:
            if found_current: next_acc = acc; break
            if acc['id'] == current_id: found_current = True
        if not next_acc: next_acc = accs[0]
        name = next_acc['first_name'] or next_acc['phone'] or str(next_acc['user_id'])
        phone = next_acc['phone'] or 'بدون'; user_id = next_acc['user_id'] or 'غير معروف'
        username = next_acc['username'] or 'بدون'; two_step = next_acc.get('two_step', '')
        info_text = f"👤 **معلومات الحساب**\n\n📱 الرقم: {phone}\n👤 الاسم: {name}\n🆔 الآيدي: {user_id}\n📝 اليوزر: @{username}\n"
        if two_step: info_text += f"🔐 2FA: {two_step}\n"
        kb = InlineKeyboardMarkup([
            [KbBtn("🔑 جلب OTP", callback_data=f"get_otp_{next_acc['id']}", style="success")],
            [KbBtn("➡️ الحساب التالي", callback_data=f"next_acc_{next_acc['id']}", style="primary")],
            [KbBtn("🔙 رجوع", callback_data="otp", style="primary")]
        ])
        await cb.message.edit_text(info_text, reply_markup=kb)
    elif d.startswith("get_otp_"):
        acc_id = int(d.split("_")[2]); acc = db.get_by_id(acc_id)
        if not acc: return await cb.answer("❌", show_alert=True)
        msg = await cb.message.edit_text("🔑 جاري جلب OTP...")
        success, result, two_step = await am.get_otp_for_account(acc)
        name = acc['first_name'] or acc['phone'] or str(acc['user_id']); phone = acc['phone'] or 'بدون'
        if success:
            text = f"✅ **{name}**\n📱 {phone}\n🔑 **رمز OTP:** `{result}`\n\n"
            if two_step: text += f"🔐 **2FA:** `{two_step}`\n"
        else:
            text = f"❌ **{name}**\n📱 {phone}\n{result}\n"
            if two_step: text += f"🔐 **2FA:** `{two_step}`\n"
        kb = InlineKeyboardMarkup([
            [KbBtn("🔑 جلب مرة أخرى", callback_data=f"get_otp_{acc_id}", style="primary")],
            [KbBtn("➡️ الحساب التالي", callback_data=f"next_acc_{acc_id}", style="primary")],
            [KbBtn("🔙 رجوع", callback_data="otp", style="primary")]
        ])
        await msg.edit_text(text, reply_markup=kb)
    elif d == "ref": states[uid] = "ref_link"; tmp[uid] = {}; await cb.message.edit_text("🚀 أرسل رابط البوت:")
    elif d == "ref_turbo": states[uid] = "ref_link"; tmp[uid] = {}; await cb.message.edit_text("⚡ أرسل رابط البوت:")
    elif d == "ref_captcha":
        if db.count() == 0: return await cb.message.edit_text("❌", reply_markup=menu_ref())
        states[uid] = "ref_link"; tmp[uid] = {"mode": "captcha"}; await cb.message.edit_text("🚀🔐 أرسل رابط البوت:")
    elif d == "join_ch":
        if db.count() == 0: return await cb.message.edit_text("❌", reply_markup=menu_tools())
        states[uid] = "channels"; await cb.message.edit_text("📢 أرسل يوزرات القنوات:")
    elif d == "vote":
        if db.count() == 0: return await cb.message.edit_text("❌", reply_markup=menu_vote())
        states[uid] = "vote_channel"; await cb.message.edit_text("🗳 أرسل يوزر القناة:")
    elif d == "vote_fast":
        if db.count() == 0: return await cb.message.edit_text("❌", reply_markup=menu_vote())
        states[uid] = "vote_channel"; tmp[uid] = {"mode": "fast"}; await cb.message.edit_text("🗳⚡ أرسل يوزر القناة:")
    elif d == "vote_scheduled":
        if db.count() == 0: return await cb.message.edit_text("❌", reply_markup=menu_vote())
        states[uid] = "vote_channel"; tmp[uid] = {"mode": "scheduled"}; await cb.message.edit_text("🗳⏰ أرسل يوزر القناة:")
    elif d == "roulette":
        if db.count() == 0: return await cb.message.edit_text("❌", reply_markup=menu_roulette())
        states[uid] = "roulette_link"; tmp[uid] = {}; await cb.message.edit_text("🎰 أرسل رابط رسالة الروليت:")
    elif d == "comment_multi":
        if db.count() == 0: return await cb.message.edit_text("❌", reply_markup=menu_roulette())
        states[uid] = "comment_multi_link"; tmp[uid] = {}; await cb.message.edit_text("💬 أرسل رابط الرسالة:")
    elif d == "comment_single":
        if db.count() == 0: return await cb.message.edit_text("❌", reply_markup=menu_roulette())
        states[uid] = "comment_single_link"; tmp[uid] = {}; await cb.message.edit_text("💬 أرسل رابط الرسالة:")
    elif d == "react_normal":
        if db.count() == 0: return await cb.message.edit_text("❌", reply_markup=menu_react())
        states[uid] = "react_link"; await cb.message.edit_text("🎭 أرسل رابط المنشور:")
    elif d == "react_turbo":
        if db.count() == 0: return await cb.message.edit_text("❌", reply_markup=menu_react())
        states[uid] = "react_link"; tmp[uid] = {"turbo": True}; await cb.message.edit_text("🎭⚡ أرسل رابط المنشور:")
    elif d == "clean_accounts":
        if db.count() == 0: return await cb.message.edit_text("❌", reply_markup=menu_tools())
        accs = db.all_acc(); msg = await cb.message.edit_text("🧹⚡ جاري تنظيف...", reply_markup=cancel_button())
        ok, fail, total_left, total_failed, elapsed, cancelled = await am.mass_clean_accounts_turbo(uid, accs, msg)
        await msg.edit_text(f"🧹⚡ **تم!**\n✅ {ok}\n📤 {total_left}\n❌ {fail}", reply_markup=menu_tools())
    elif d == "import_s": states[uid] = "import_file"; await cb.message.edit_text("📥 أرسل ملف JSON:")
    elif d == "export_json":
        msg = await cb.message.edit_text("⏳..."); ok, path, cnt = export_sessions_json()
        if ok: await cb.message.reply_document(path, caption=f"✅ {cnt}"); await msg.edit_text(f"✅ {cnt}", reply_markup=menu_acc())
    elif d == "spam_check":
        if db.count() == 0: return await cb.message.edit_text("❌", reply_markup=menu_tools())
        msg = await cb.message.edit_text("🛡 جاري فحص السبام...")
        await am.check_spam(c, msg)
    elif d == "admin_manage":
        if uid != OWNER_ID: return await cb.answer("🔒", show_alert=True)
        await cb.message.edit_text("👑 **إدارة المشرفين**", reply_markup=admin_manage_menu())
    elif d == "admin_add":
        if uid != OWNER_ID: return await cb.answer("🔒", show_alert=True)
        states[uid] = "admin_add_id"; await cb.message.edit_text("👑 أرسل ايدي المشرف:")
    elif d == "admin_list":
        admins = db.all_admins(); txt = "👑 **المشرفين:**\n\n"
        for a in admins:
            role = "👑 مالك" if a['user_id'] == OWNER_ID else "👤 مشرف"
            exp = a['expiry_date'][:16] if a['expiry_date'] else "♾ دائم"
            txt += f"• `{a['user_id']}` - {role} | {exp}\n"
        await cb.message.edit_text(txt, reply_markup=admin_manage_menu())
    elif d == "admin_remove":
        admins = db.all_admins()
        btns = [[KbBtn(f"🗑 {a['user_id']}", callback_data=f"admin_del_{a['user_id']}", style="danger")] for a in admins if a['user_id'] != OWNER_ID]
        btns.append([KbBtn("🔙 رجوع", callback_data="admin_manage", style="primary")])
        await cb.message.edit_text("اختر:", reply_markup=InlineKeyboardMarkup(btns))
    elif d.startswith("admin_del_"):
        db.remove_admin(int(d.split("_")[2])); await cb.message.edit_text("✅", reply_markup=admin_manage_menu())
    elif d == "dur_forever":
        new_id = tmp.get(uid, {}).get("admin_id")
        if new_id:
            db.add_admin(new_id, None, uid); await cb.message.edit_text(f"✅ دائم", reply_markup=admin_manage_menu())
        else: await cb.answer("❌", show_alert=True)
        tmp.pop(uid, None); states.pop(uid, None)
    elif d == "dur_minutes": states[uid] = "dur_input"; tmp[uid] = {'dur_unit': "minute"}; await cb.message.edit_text("⏱ أرسل عدد الدقائق:")
    elif d == "dur_hours": states[uid] = "dur_input"; tmp[uid] = {'dur_unit': "hour"}; await cb.message.edit_text("⏰ أرسل عدد الساعات:")
    elif d == "dur_days": states[uid] = "dur_input"; tmp[uid] = {'dur_unit': "day"}; await cb.message.edit_text("📅 أرسل عدد الأيام:")
    elif d == "dur_weeks": states[uid] = "dur_input"; tmp[uid] = {'dur_unit': "week"}; await cb.message.edit_text("📅 أرسل عدد الأسابيع:")
    elif d == "dur_months": states[uid] = "dur_input"; tmp[uid] = {'dur_unit': "month"}; await cb.message.edit_text("📅 أرسل عدد الشهور:")
    elif d == "delete":
        accs = db.all_acc()
        if accs:
            btns = [[KbBtn(f"🗑 {a['first_name'] or a['phone']}", callback_data=f"del_{a['id']}", style="danger")] for a in accs[:30]]
            btns.append([KbBtn("🔙 رجوع", callback_data="main", style="primary")])
            await cb.message.edit_text("اختر:", reply_markup=InlineKeyboardMarkup(btns))
        else: await cb.message.edit_text("❌", reply_markup=mu)
    elif d.startswith("del_"): db.del_acc(int(d.split("_")[1])); await cb.message.edit_text("✅", reply_markup=menu(uid))

async def msg_handler(c, m):
    uid = m.from_user.id
    if not db.is_admin(uid): return
    s = states.get(uid); t = m.text.strip() if m.text else ""; mu = menu(uid)
    if s == "admin_add_id":
        try:
            new_id = int(t); tmp[uid] = {"admin_id": new_id}; states[uid] = "admin_duration"
            await m.reply("⏰ **اختر المدة:**", reply_markup=duration_menu())
        except: await m.reply("❌"); states.pop(uid, None)
        return
    if s == "dur_input":
        try:
            val = int(t)
            if val <= 0: raise ValueError
            unit = tmp[uid]['dur_unit']
            if unit == "minute": expiry = (datetime.now() + timedelta(minutes=val)).isoformat(); label = f"{val} دقيقة"
            elif unit == "hour": expiry = (datetime.now() + timedelta(hours=val)).isoformat(); label = f"{val} ساعة"
            elif unit == "day": expiry = (datetime.now() + timedelta(days=val)).isoformat(); label = f"{val} يوم"
            elif unit == "week": expiry = (datetime.now() + timedelta(weeks=val)).isoformat(); label = f"{val} أسبوع"
            else: expiry = (datetime.now() + timedelta(days=val*30)).isoformat(); label = f"{val} شهر"
            db.add_admin(tmp[uid]['admin_id'], expiry, uid)
            name, username = await get_user_info(uid)
            await send_log(f"👑 **مشرف جديد**\n🆔 `{tmp[uid]['admin_id']}`\n⏰ {label}\n👤 بواسطة: {name} | {username}")
            await m.reply(f"✅ تم!\n🆔 {tmp[uid]['admin_id']}\n⏰ {label}", reply_markup=admin_manage_menu())
        except: await m.reply("❌ رقم غير صحيح")
        states.pop(uid, None); tmp.pop(uid, None); return
    if s == "import_file":
        if m.document:
            msg = await m.reply("⏳..."); fp = await m.download(file_name=f"{BACKUPS}/imp_{int(time.time())}.json")
            ok, result = import_sessions_json(fp)
            if ok:
                await msg.edit_text(f"✅ {result}\n⏳ تحميل...", reply_markup=menu_acc())
                loaded = await am.load_all()
                name, username = await get_user_info(uid)
                await send_log(f"📥 **استيراد JSON**\n👤 {name} | {username}\n✅ {result} | 🚀 {loaded}")
                await msg.edit_text(f"✅ {result} | 🚀 {loaded}", reply_markup=menu_acc())
            else: await msg.edit_text(f"❌ {result}", reply_markup=menu_acc())
            states.pop(uid, None)
        return
    if not t: return
    if s == "password" and t.lower() in ["تخطي","skip"]:
        temp_data = tmp.get(uid)
        if temp_data and 'client' in temp_data: await temp_data['client'].stop()
        states.pop(uid, None); tmp.pop(uid, None); return await m.reply("⚠️ تم", reply_markup=menu_acc())
    if s == "phone":
        phone = t.replace(" ","")
        if not phone.startswith("+"): phone = "+" + phone
        msg = await m.reply("⏳..."); result = await am.send_code(phone)
        if result['ok']:
            tmp[uid] = {"client": result['client'], "phone": phone, "hash": result['hash']}
            states[uid] = "code"; await msg.edit_text("📨 أرسل الكود:")
        else: await msg.edit_text(f"❌ {result['err']}"); states.pop(uid, None)
    elif s == "code":
        temp_data = tmp.get(uid)
        if not temp_data: states.pop(uid, None); return await m.reply("❌")
        msg = await m.reply("⏳..."); result = await am.sign_in(temp_data['client'], temp_data['phone'], temp_data['hash'], t)
        if result['ok']:
            await msg.edit_text(f"✅ {result['name']}", reply_markup=menu_acc())
            name, username = await get_user_info(uid)
            await send_log(f"➕ **حساب جديد**\n👤 الاسم: {result['name']}\n📱 `{temp_data['phone']}`\nبواسطة: {name} | {username}")
            states.pop(uid, None); tmp.pop(uid, None)
        elif result.get('need_pass'): states[uid] = "password"; await msg.edit_text("🔐 كلمة المرور:")
        else: await msg.edit_text(f"❌ {result['err']}"); states.pop(uid, None); tmp.pop(uid, None)
    elif s == "password":
        temp_data = tmp.get(uid)
        if not temp_data: states.pop(uid, None); return await m.reply("❌")
        msg = await m.reply("⏳..."); result = await am.check_pass(temp_data['client'], t)
        if result['ok']: await msg.edit_text("✅", reply_markup=menu_acc())
        else: await msg.edit_text(f"❌ {result['err']}")
        states.pop(uid, None); tmp.pop(uid, None)
    elif s == "channels":
        chs = [l.strip() for l in t.split("\n") if l.strip().startswith("@") or "t.me/" in l.strip()]
        if not chs: return await m.reply("❌")
        name, username = await get_user_info(uid)
        await send_log(f"📢 **بدأ رشق قنوات**\n👤 {name} | {username}\n📊 {len(chs)} قناة\n📋 `{', '.join(chs[:5])}`")
        msg = await m.reply(f"📢 جاري...", reply_markup=cancel_button())
        ok, fail, elapsed = await am.turbo_join(uid, chs, msg)
        await send_log(f"📢 **انتهى رشق القنوات**\n✅ {ok} | ❌ {fail}\n⏱ {int(elapsed)}ث")
        await msg.edit_text(f"📢 **تم!**\n✅ {ok} | ❌ {fail}", reply_markup=menu_tools()); states.pop(uid, None)
    # ═══ التعليقات ═══
    elif s == "comment_multi_link":
        if "t.me/" not in t: return await m.reply("❌ رابط غير صحيح")
        chat_id, msg_id = parse_message_link(t)
        if not chat_id: return await m.reply("❌ رابط غير صالح")
        tmp[uid]['comment_chat_id'] = chat_id
        tmp[uid]['comment_msg_id'] = msg_id
        states[uid] = "comment_multi_count"
        await m.reply(f"💬 الحسابات: {db.count()}\nكم حساب؟")
    elif s == "comment_multi_count":
        total = db.count()
        cnt = total if t in ["الكل", "all", "كل"] else (int(t) if t.isdigit() and int(t) <= total else total)
        tmp[uid]['comment_count'] = cnt
        states[uid] = "comment_multi_interval"
        await m.reply("⏱ ثواني بين كل حساب (1-60):")
    elif s == "comment_multi_interval":
        interval = int(t) if t.isdigit() and 1 <= int(t) <= 60 else 5
        tmp[uid]['comment_interval'] = interval
        states[uid] = "comment_multi_words"
        await m.reply("📝 أرسل الكلمات (كل كلمة بسطر):")
    elif s == "comment_multi_words":
        words = [w.strip() for w in t.split("\n") if w.strip()]
        if not words: return await m.reply("❌")
        chat_id = tmp[uid]['comment_chat_id']
        msg_id = tmp[uid]['comment_msg_id']
        cnt = tmp[uid]['comment_count']
        interval = tmp[uid]['comment_interval']
        accs = db.all_acc()[:cnt]
        link = build_link(chat_id, msg_id)
        name, username = await get_user_info(uid)
        await send_log(
            f"💬 **بدأ رشق تعليقات متعددة**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 **المنفذ:** {name}\n"
            f"🆔 **المعرف:** {username} | `{uid}`\n"
            f"📊 **الحسابات:** {cnt}\n"
            f"🔗 **الرابط:** {link}\n"
            f"📝 **الكلمات ({len(words)}):** {', '.join(words[:8])}\n"
            f"⏱ **الفاصل:** {interval} ثانية\n"
            f"⏰ **البدء:** `{datetime.now().strftime('%H:%M:%S')}`"
        )
        msg = await m.reply(f"💬 جاري...", reply_markup=cancel_button())
        ok, fail, elapsed, cancelled = await am.mass_comment_multi(uid, accs, chat_id, msg_id, words, interval, msg)
        await send_log(
            f"💬 **انتهى رشق التعليقات المتعددة**\n"
            f"👤 {name} | {username}\n"
            f"🔗 {link}\n"
            f"✅ {ok} | ❌ {fail}\n"
            f"⏱ {int(elapsed)}ث"
        )
        await msg.edit_text(f"💬 **تم!**\n✅ {ok} | ❌ {fail}\n⏱ {int(elapsed)}ث", reply_markup=menu_roulette())
        states.pop(uid, None); tmp.pop(uid, None)
    elif s == "comment_single_link":
        if "t.me/" not in t: return await m.reply("❌")
        chat_id, msg_id = parse_message_link(t)
        if not chat_id: return await m.reply("❌")
        tmp[uid]['comment_chat_id'] = chat_id
        tmp[uid]['comment_msg_id'] = msg_id
        states[uid] = "comment_single_count"
        await m.reply(f"💬 الحسابات: {db.count()}\nكم حساب؟")
    elif s == "comment_single_count":
        total = db.count()
        cnt = total if t in ["الكل", "all", "كل"] else (int(t) if t.isdigit() and int(t) <= total else total)
        tmp[uid]['comment_count'] = cnt
        states[uid] = "comment_single_interval"
        await m.reply("⏱ ثواني بين كل حساب (1-60):")
    elif s == "comment_single_interval":
        interval = int(t) if t.isdigit() and 1 <= int(t) <= 60 else 5
        tmp[uid]['comment_interval'] = interval
        states[uid] = "comment_single_word"
        await m.reply("📝 أرسل الكلمة:")
    elif s == "comment_single_word":
        word = t.strip()
        if not word: return await m.reply("❌")
        chat_id = tmp[uid]['comment_chat_id']
        msg_id = tmp[uid]['comment_msg_id']
        cnt = tmp[uid]['comment_count']
        interval = tmp[uid]['comment_interval']
        accs = db.all_acc()[:cnt]
        link = build_link(chat_id, msg_id)
        name, username = await get_user_info(uid)
        await send_log(
            f"💬 **بدأ رشق تعليق واحد**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 **المنفذ:** {name}\n"
            f"🆔 **المعرف:** {username} | `{uid}`\n"
            f"📊 **الحسابات:** {cnt}\n"
            f"🔗 **الرابط:** {link}\n"
            f"📝 **الكلمة:** `{word}`\n"
            f"⏱ **الفاصل:** {interval} ثانية\n"
            f"⏰ **البدء:** `{datetime.now().strftime('%H:%M:%S')}`"
        )
        msg = await m.reply(f"💬 جاري...", reply_markup=cancel_button())
        ok, fail, elapsed, cancelled = await am.mass_comment_single(uid, accs, chat_id, msg_id, word, interval, msg)
        await send_log(
            f"💬 **انتهى رشق التعليق الواحد**\n"
            f"👤 {name} | {username}\n"
            f"🔗 {link}\n"
            f"✅ {ok} | ❌ {fail}\n"
            f"⏱ {int(elapsed)}ث"
        )
        await msg.edit_text(f"💬 **تم!**\n✅ {ok} | ❌ {fail}\n⏱ {int(elapsed)}ث", reply_markup=menu_roulette())
        states.pop(uid, None); tmp.pop(uid, None)
    elif s == "react_link":
        if "t.me/" not in t: return await m.reply("❌")
        tmp[uid]['react_link'] = t; states[uid] = "react_count"; await m.reply(f"🎭 كم حساب؟")
    elif s == "react_count":
        total = db.count(); cnt = total if t in ["الكل", "all"] else (int(t) if t.isdigit() and int(t) <= total else total)
        tmp[uid]['react_count'] = cnt; states[uid] = "react_emoji"; await m.reply("🎭 أرسل الرموز أو `عشوائي`:")
    elif s == "react_emoji":
        if t == "عشوائي" or t.lower() == "random": custom_emojis = None; random_emoji = True
        else:
            custom_emojis = [e.strip() for e in t.split() if e.strip()]; random_emoji = False
            if not custom_emojis: return await m.reply("❌")
        link = tmp[uid]['react_link']; cnt = tmp[uid]['react_count']; accs = db.all_acc()[:cnt]
        turbo = tmp[uid].get('turbo', False)
        name, username = await get_user_info(uid)
        await send_log(f"🎭 **بدأ تفاعل**\n👤 {name} | {username}\n📊 {cnt}\n🔗 {link}")
        msg = await m.reply(f"🎭 جاري...", reply_markup=cancel_button())
        if turbo:
            ok, fail, elapsed, _ = await am.mass_reactions_turbo(uid, accs, link, emoji_list=custom_emojis if not random_emoji else None, random_emoji=random_emoji, msg=msg)
        else:
            ok, fail, elapsed, _ = await am.mass_reactions(uid, accs, link, emoji=None, random_emoji=random_emoji, emoji_list=custom_emojis if not random_emoji else None, msg=msg, turbo=False)
        await send_log(f"🎭 **انتهى التفاعل**\n👤 {name} | {username}\n🔗 {link}\n✅ {ok} | ❌ {fail}")
        await msg.edit_text(f"🎭 **تم!**\n✅ {ok} | ❌ {fail}", reply_markup=menu_react()); states.pop(uid, None); tmp.pop(uid, None)
    elif s == "ref_link":
        if "t.me/" not in t: return await m.reply("❌")
        tmp[uid]['ref_link'] = t; states[uid] = "ref_channels"; await m.reply("📺 أرسل القنوات أو `تم`:")
    elif s == "ref_channels":
        if t in ["تم", "لا"]: tmp[uid]['ref_channels'] = []
        else: tmp[uid]['ref_channels'] = [l.strip() for l in t.split("\n") if l.strip()]
        states[uid] = "ref_count"; await m.reply(f"📊 كم حساب؟")
    elif s == "ref_count":
        total = db.count(); cnt = total if t in ["الكل", "all"] else (int(t) if t.isdigit() and int(t) <= total else total)
        link = tmp[uid]['ref_link']; chs = tmp[uid].get('ref_channels', []); accs = db.all_acc()[:cnt]
        mode = tmp[uid].get('mode', 'normal')
        name, username = await get_user_info(uid)
        await send_log(f"🚀 **بدأ رشق إحالات**\n👤 {name} | {username}\n📊 {cnt}\n🔗 {link}\n📋 قنوات: {len(chs)}")
        msg = await m.reply(f"🚀 جاري...", reply_markup=cancel_button())
        if mode == 'captcha':
            ok, fail, elapsed, _ = await am.mass_ref_with_captcha(uid, accs, link, chs, msg)
        else:
            ok, fail, elapsed, _ = await am.mass_ref(uid, accs, link, chs, msg)
        await send_log(f"🚀 **انتهى رشق الإحالات**\n👤 {name} | {username}\n🔗 {link}\n✅ {ok} | ❌ {fail}")
        await msg.edit_text(f"🚀 **تم!**\n✅ {ok} | ❌ {fail}", reply_markup=menu_ref())
        states.pop(uid, None); tmp.pop(uid, None)
    elif s == "vote_channel":
        tmp[uid]['vote_channel'] = t; states[uid] = "vote_link"; await m.reply("🗳 أرسل رابط التصويت:")
    elif s == "vote_link":
        if "t.me/" not in t: return await m.reply("❌")
        tmp[uid]['vote_link'] = t
        mode = tmp[uid].get('mode', 'normal')
        if mode == 'fast': states[uid] = "vote_fast_count"; await m.reply(f"🗳⚡ كم تصويت؟")
        elif mode == 'scheduled': states[uid] = "vote_scheduled_count"; await m.reply(f"🗳⏰ كم تصويت/دفعة؟")
        else: states[uid] = "vote_count"; await m.reply(f"🗳 كم حساب؟")
    elif s == "vote_count":
        total = db.count(); cnt = total if t in ["الكل", "all"] else (int(t) if t.isdigit() and int(t) <= total else total)
        channel = tmp[uid]['vote_channel']; link = tmp[uid]['vote_link']; accs = db.all_acc()[:cnt]
        name, username = await get_user_info(uid)
        await send_log(f"🗳 **تصويت**\n👤 {name} | {username}\n📊 {cnt}\n📍 {channel}\n🔗 {link}")
        msg = await m.reply(f"🗳 جاري...")
        ok = fail = 0
        for acc in accs:
            client = await am.get_client(acc['user_id'])
            if not client: fail += 1; continue
            accname = acc['first_name'] or str(acc['user_id'])
            success, _ = await am.vote_with_captcha_buttons(client, channel, link, accname)
            if success: ok += 1
            else: fail += 1
        await send_log(f"🗳 **انتهى**\n👤 {name} | {username}\n✅ {ok} | ❌ {fail}")
        await msg.edit_text(f"🗳 **تم!**\n✅ {ok} | ❌ {fail}", reply_markup=menu_vote()); states.pop(uid, None); tmp.pop(uid, None)
    elif s == "vote_fast_count":
        required = int(t) if t.isdigit() and int(t) > 0 else db.count()
        channel = tmp[uid]['vote_channel']; link = tmp[uid]['vote_link']; accs = db.all_acc()
        name, username = await get_user_info(uid)
        await send_log(f"🗳⚡ **تصويت فائق**\n👤 {name} | {username}\n🎯 {required}\n📍 {channel}\n🔗 {link}")
        msg = await m.reply(f"🗳⚡ جاري...", reply_markup=cancel_button())
        ok, fail, elapsed, cancelled = await am.mass_vote_captcha_turbo(uid, accs, channel, link, required, msg)
        await send_log(f"🗳⚡ **انتهى**\n👤 {name} | {username}\n✅ {ok}/{required} | ❌ {fail}")
        await msg.edit_text(f"🗳⚡ **تم!**\n✅ {ok}/{required}", reply_markup=menu_vote()); states.pop(uid, None); tmp.pop(uid, None)
    elif s == "vote_scheduled_count":
        votes_per_interval = int(t) if t.isdigit() and int(t) > 0 else 5
        tmp[uid]['votes_per_interval'] = votes_per_interval; states[uid] = "vote_scheduled_interval"
        await m.reply("⏰ كم ثانية بين الدفعات؟")
    elif s == "vote_scheduled_interval":
        interval = int(t) if t.isdigit() and int(t) >= 10 else 60
        channel = tmp[uid]['vote_channel']; link = tmp[uid]['vote_link']; vpi = tmp[uid]['votes_per_interval']
        accs = db.all_acc()
        name, username = await get_user_info(uid)
        await send_log(f"🗳⏰ **تصويت بمدة**\n👤 {name} | {username}\n📊 {vpi} كل {interval}ث\n📍 {channel}")
        msg = await m.reply(f"🗳⏰ جاري...", reply_markup=cancel_button())
        ok, fail, elapsed, cancelled = await am.mass_vote_scheduled(uid, accs, channel, link, vpi, interval, msg)
        await send_log(f"🗳⏰ **انتهى**\n👤 {name} | {username}\n✅ {ok} | ❌ {fail}")
        await msg.edit_text(f"🗳⏰ **تم!**\n✅ {ok}\n❌ {fail}", reply_markup=menu_vote()); states.pop(uid, None); tmp.pop(uid, None)
    elif s == "roulette_link":
        if "t.me/" not in t: return await m.reply("❌")
        tmp[uid]['roulette_link'] = t
        states[uid] = "roulette_count"
        await m.reply(f"🎰 الحسابات: {db.count()}\nكم؟")
    elif s == "roulette_count":
        total = db.count()
        cnt = total if t in ["الكل", "all", "كل"] else (int(t) if t.isdigit() and int(t) <= total else total)
        tmp[uid]['roulette_count'] = cnt
        states[uid] = "roulette_interval"
        await m.reply("⏱ ثواني (1-60):")
    elif s == "roulette_interval":
        interval = int(t) if t.isdigit() and 1 <= int(t) <= 60 else 6
        link = tmp[uid]['roulette_link']; cnt = tmp[uid]['roulette_count']
        accs = db.all_acc()[:cnt]
        name, username = await get_user_info(uid)
        await send_log(f"🎰 **روليت**\n👤 {name} | {username}\n📊 {cnt}\n🔗 {link}\n⏱ {interval}ث")
        msg = await m.reply(f"🎰 جاري...", reply_markup=cancel_button())
        ok, fail, elapsed, cancelled = await am.mass_roulette_scheduled(uid, accs, link, interval, msg)
        await send_log(f"🎰 **انتهى**\n👤 {name} | {username}\n🔗 {link}\n✅ {ok} | ❌ {fail}")
        await msg.edit_text(f"🎰 **تم!**\n✅ {ok} | ❌ {fail}", reply_markup=menu_roulette())
        states.pop(uid, None); tmp.pop(uid, None)

async def main():
    print("="*40)
    print(f"🤖 بوت رشق الإحالات | 👑 {OWNER_ID} | 📊 {db.count()}")
    print(f"🎨 ألوان الأزرار: {'✅' if _HAS_STYLE else '⚠️'}")
    loaded = await am.load_all()
    print(f"✅ {loaded} جلسة")
    app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

    @app.on_message(filters.command("setlog"))
    async def setlog_cmd(c, m):
        if m.from_user.id != OWNER_ID:
            return await m.reply("⛔ للمالك فقط")
        db.set_log_chat(m.chat.id)
        await m.reply(f"✅ **تم ربط القروب كـ Log**\n🆔 `{m.chat.id}`")

    @app.on_message(filters.command("unsetlog"))
    async def unsetlog_cmd(c, m):
        if m.from_user.id != OWNER_ID:
            return await m.reply("⛔")
        db.set_setting("log_chat_id", "")
        await m.reply("✅ تم إلغاء الربط")

    @app.on_message(filters.command("logtest"))
    async def logtest_cmd(c, m):
        if m.from_user.id != OWNER_ID:
            return await m.reply("⛔")
        name, username = await get_user_info(m.from_user.id)
        await send_log(f"🧪 **تجربة اللوق**\n👤 {name} | {username}\n⏰ `{datetime.now().strftime('%H:%M:%S')}`")
        await m.reply("✅")

    @app.on_message(filters.command("start"))
    async def h(c, m): await start_msg(c, m)
    @app.on_message(filters.command("l"))
    async def l(c, m): await l_command(c, m)
    @app.on_message(filters.command("spam"))
    async def sp(c, m): await spam_command(c, m)
    @app.on_message()
    async def hm(c, m): await msg_handler(c, m)
    @app.on_callback_query()
    async def cb(c, cb): await cb_handler(c, cb)

    await app.start()
    me = await app.get_me()
    send_log._client = app
    print(f"✅ @{me.username}\n")
    try:
        await send_log(f"🤖 **البوت اشتغل**\n👤 @{me.username}\n📊 {db.count()} حساب\n⏰ `{datetime.now().strftime('%H:%M:%S')}`")
    except: pass
    while True: await asyncio.sleep(1)

if __name__ == "__main__":
    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    try: loop.run_until_complete(main())
    except KeyboardInterrupt: print("\n👋")
    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback; traceback.print_exc()
    finally: loop.close()