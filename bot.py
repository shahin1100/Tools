import asyncio
import pyotp
import requests
import re
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ====== TOKEN (Railway ENV) ======
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ====== MENU ======
menu = ReplyKeyboardMarkup(
    [
        ["🔐 Generate 2FA"],
        ["🔗 FB Link → UID"]
    ],
    resize_keyboard=True
)

# ====== START ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n\nChoose option:",
        reply_markup=menu
    )

# ====== 2FA LIVE ======
async def generate_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    
    message = await update.message.reply_text("⏳ Generating 2FA...")
    
    for i in range(60):
        code = totp.now()
        remaining = 30 - (i % 30)
        
        if remaining == 0:
            remaining = 30
        
        text = (
            f"🔐 2FA LIVE\n\n"
            f"SECRET: `{secret}`\n"
            f"CODE: `{code}`\n"
            f"⏱️ Expires in: {remaining}s"
        )
        
        try:
            await message.edit_text(text, parse_mode='Markdown')
        except:
            pass
        
        await asyncio.sleep(1)

# ====== FB UID ======
def get_uid_from_link(link):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        res = requests.get(link, timeout=10, headers=headers)
        text = res.text
        
        # Method 1
        uid = re.search(r'"userID":"(\d+)"', text)
        if uid:
            return uid.group(1)
        
        # Method 2  
        uid2 = re.search(r'entity_id[=:]["\']?(\d+)', text)
        if uid2:
            return uid2.group(1)
            
        # Method 3 - from URL
        uid3 = re.search(r'facebook\.com/(\d+)', link)
        if uid3:
            return uid3.group(1)
        
        return "UID not found"
    except Exception as e:
        return f"Error: {str(e)[:50]}"

# ====== HANDLE ======
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔐 Generate 2FA":
        await generate_2fa(update, context)
    
    elif text == "🔗 FB Link → UID":
        await update.message.reply_text("🔗 Please send your Facebook profile link:")
    
    elif "facebook.com" in text or "fb.com" in text:
        await update.message.reply_text("⏳ Fetching UID...")
        uid = get_uid_from_link(text)
        await update.message.reply_text(f"🆔 **UID:** `{uid}`", parse_mode='Markdown')
    
    else:
        await update.message.reply_text("❌ Please use the menu buttons.", reply_markup=menu)

# ====== MAIN ======
def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not found!")
        return
    
    # Fixed: Using Application instead of Updater
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    
    print("✅ Bot is running on Railway...")
    
    # Start polling
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()