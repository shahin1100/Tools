import asyncio
import pyotp
import requests
import re
import os
import json
import random
import string
import base64
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==================== CONFIG ====================
BOT_TOKEN = "8600715105:AAEf157zFN-0T4uCFTOZ_OXKVlejci4WLR4"

# ==================== MENU ====================
menu = ReplyKeyboardMarkup(
    [
        ["🔐 Generate 2FA", "🔗 FB Link → UID"],
        ["📊 My Stats", "ℹ️ About"]
    ],
    resize_keyboard=True
)

# ==================== USER DATA ====================
user_stats = {}

def save_stats():
    try:
        with open("stats.json", "w") as f:
            json.dump(user_stats, f)
    except:
        pass

def load_stats():
    global user_stats
    try:
        with open("stats.json", "r") as f:
            user_stats = json.load(f)
    except:
        user_stats = {}

# ==================== 2FA GENERATOR ====================
async def generate_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    
    msg = await update.message.reply_text("⏳ **Generating 2FA Codes...**", parse_mode='Markdown')
    
    # Update stats
    if user_id not in user_stats:
        user_stats[user_id] = {"2fa": 0, "uid": 0}
    user_stats[user_id]["2fa"] += 1
    save_stats()
    
    for i in range(60):
        code = totp.now()
        remaining = 30 - (i % 30)
        if remaining == 0:
            remaining = 30
        
        text = f"""
🔐 **LIVE 2FA GENERATOR**

📋 **Secret:** `{secret}`
🔢 **Code:** `{code}`
⏱️ **Expires:** {remaining}s

⚡ Auto-updating every second
        """
        
        try:
            await msg.edit_text(text, parse_mode='Markdown')
        except:
            pass
        
        await asyncio.sleep(1)
    
    await msg.edit_text(f"✅ **2FA Generation Complete!**\n\n🔑 Your secret key: `{secret}`\n\n💡 Save this key for future use.", parse_mode='Markdown')

# ==================== FB UID EXTRACTOR ====================
def extract_uid(link):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(link, timeout=10, headers=headers)
        text = response.text
        
        # Multiple patterns
        patterns = [
            r'"userID":"(\d+)"',
            r'"uid":"(\d+)"',
            r'profile_id=(\d+)',
            r'entity_id=(\d+)',
            r'facebook\.com/(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        # URL direct extract
        url_match = re.search(r'facebook\.com/(\d+)', link)
        if url_match:
            return url_match.group(1)
        
        return "❌ UID not found"
    except Exception as e:
        return f"❌ Error: {str(e)[:30]}"

async def get_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔗 **Send me your Facebook profile link:**", parse_mode='Markdown')

async def process_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    link = update.message.text
    
    msg = await update.message.reply_text("⏳ **Extracting UID...**", parse_mode='Markdown')
    
    # Update stats
    if user_id not in user_stats:
        user_stats[user_id] = {"2fa": 0, "uid": 0}
    user_stats[user_id]["uid"] += 1
    save_stats()
    
    uid = extract_uid(link)
    
    text = f"""
🔗 **Facebook UID Extractor**

📎 **Link:** {link[:40]}...
🆔 **UID:** `{uid}`

🔗 **Profile:** https://facebook.com/{uid if "❌" not in uid else ""}
    """
    
    await msg.edit_text(text, parse_mode='Markdown')

# ==================== STATS ====================
async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = update.effective_user
    
    if user_id not in user_stats:
        user_stats[user_id] = {"2fa": 0, "uid": 0}
    
    stats = user_stats[user_id]
    
    text = f"""
📊 **Your Statistics**

👤 **Name:** {user.first_name}
🆔 **ID:** `{user_id}`

🔐 **2FA Generated:** {stats.get('2fa', 0)}
🔗 **UID Extracted:** {stats.get('uid', 0)}
📅 **Total:** {stats.get('2fa', 0) + stats.get('uid', 0)}

💎 Keep using the bot!
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ==================== ABOUT ====================
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
🤖 **Ultimate Bot v1.0**

🔧 **Features:**
• 🔐 Live 2FA Code Generator
• 🔗 Facebook UID Extractor
• 📊 User Statistics

⚡ **Commands:**
/start - Show menu
/stats - Your stats

👨‍💻 **Developer:** @Shihab_920

✅ Bot is online and free!
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ==================== START ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = f"""
👋 **Welcome {user.first_name}!**

🤖 **Ultimate Tool Bot**

🔧 **Available Features:**
✅ Live 2FA Code Generator
✅ Facebook UID Extractor
✅ User Statistics

📌 **How to use:**
Simply tap the buttons below!

⬇️ **Choose an option:**
    """
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=menu)

# ==================== HANDLER ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔐 Generate 2FA":
        await generate_2fa(update, context)
    
    elif text == "🔗 FB Link → UID":
        await get_uid(update, context)
    
    elif text == "📊 My Stats":
        await my_stats(update, context)
    
    elif text == "ℹ️ About":
        await about(update, context)
    
    elif "facebook.com" in text or "fb.com" in text or "fb.me" in text:
        await process_uid(update, context)
    
    else:
        await update.message.reply_text("❌ Please use the menu buttons!", reply_markup=menu)

# ==================== MAIN ====================
def main():
    load_stats()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", my_stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("=" * 40)
    print("✅ BOT IS RUNNING!")
    print("=" * 40)
    
    app.run_polling()

if __name__ == "__main__":
    main()