import asyncio
import pyotp
import requests
import re
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8600715105:AAEf157zFN-0T4uCFTOZ_OXKVlejci4WLR4"

menu = ReplyKeyboardMarkup(
    [["🔐 Generate 2FA", "🔗 FB Link → UID"]],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome!\n\nChoose option:", reply_markup=menu)

async def generate_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    msg = await update.message.reply_text("⏳ Generating 2FA...")
    for i in range(60):
        code = totp.now()
        remain = 30 - (i % 30)
        if remain == 0: remain = 30
        try:
            await msg.edit_text(f"🔐 2FA LIVE\n\nSECRET: `{secret}`\nCODE: `{code}`\n⏱️ Expires: {remain}s", parse_mode='Markdown')
        except: pass
        await asyncio.sleep(1)

def get_uid(link):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(link, timeout=10, headers=headers)
        text = r.text
        uid = re.search(r'"userID":"(\d+)"', text)
        if uid: return uid.group(1)
        uid = re.search(r'entity_id[=:]["\']?(\d+)', text)
        if uid: return uid.group(1)
        uid = re.search(r'facebook\.com/(\d+)', link)
        if uid: return uid.group(1)
        return "UID not found"
    except:
        return "Error"

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔐 Generate 2FA":
        await generate_2fa(update, context)
    elif text == "🔗 FB Link → UID":
        await update.message.reply_text("🔗 Send Facebook link:")
    elif "facebook.com" in text or "fb.com" in text:
        await update.message.reply_text("⏳ Fetching...")
        uid = get_uid(text)
        await update.message.reply_text(f"🆔 UID: {uid}")
    else:
        await update.message.reply_text("❌ Use menu buttons", reply_markup=menu)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("✅ Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()