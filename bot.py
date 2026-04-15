import asyncio
import pyotp
import requests
import re
import os
import json
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== CONFIG ====================
BOT_TOKEN = "8600715105:AAEf157zFN-0T4uCFTOZ_OXKVlejci4WLR4"

# ==================== MENU ====================
main_menu = ReplyKeyboardMarkup(
    [
        ["🔐 Generate 2FA", "🔗 FB Link → UID"],
        ["📊 My Stats", "ℹ️ About Bot"]
    ],
    resize_keyboard=True
)

# ==================== DATA STORAGE ====================
user_data = {}

def load_data():
    global user_data
    try:
        if os.path.exists("user_data.json"):
            with open("user_data.json", "r") as f:
                user_data = json.load(f)
            logger.info(f"Loaded data for {len(user_data)} users")
    except Exception as e:
        logger.error(f"Load error: {e}")
        user_data = {}

def save_data():
    try:
        with open("user_data.json", "w") as f:
            json.dump(user_data, f)
        logger.info("Data saved successfully")
    except Exception as e:
        logger.error(f"Save error: {e}")

# ==================== START COMMAND ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    
    if user_id not in user_data:
        user_data[user_id] = {
            "name": user.first_name,
            "joined": datetime.now().isoformat(),
            "total_2fa": 0,
            "total_uid": 0
        }
        save_data()
    
    welcome_text = f"""
✨ **Welcome {user.first_name}!** ✨

🤖 **Ultimate Telegram Bot**
━━━━━━━━━━━━━━━━━━━

🔧 **Features Available:**
• 🔐 Live 2FA Code Generator
• 🔗 Facebook UID Extractor  
• 📊 Personal Statistics
• ℹ️ Bot Information

📌 **How to Use:**
Simply tap any button below

⚡ **Fast & Free Forever!**
━━━━━━━━━━━━━━━━━━━
    """
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=main_menu)
    logger.info(f"User {user_id} started the bot")

# ==================== 2FA GENERATOR ====================
async def generate_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    
    # Update stats
    if user_id in user_data:
        user_data[user_id]["total_2fa"] += 1
        save_data()
    
    status_msg = await update.message.reply_text("🔄 **Starting 2FA Generator...**\n\n_This will run for 60 seconds_", parse_mode='Markdown')
    
    try:
        for i in range(60):
            current_code = totp.now()
            remaining = 30 - (i % 30)
            if remaining == 0:
                remaining = 30
            
            progress = "█" * (i // 6) + "░" * (10 - (i // 6))
            
            display_text = f"""
🔐 **LIVE 2FA GENERATOR**
━━━━━━━━━━━━━━━━━━━

📋 **Secret Key:**
`{secret}`

🔢 **Current Code:**
`{current_code}`

⏱️ **Expires In:** `{remaining}s`

📊 **Progress:** `{progress}`
⏰ **Time Left:** `{60 - i}s`
━━━━━━━━━━━━━━━━━━━
💡 _Save this secret key for future use_
"""
            
            try:
                await status_msg.edit_text(display_text, parse_mode='Markdown')
            except:
                pass
            
            await asyncio.sleep(1)
        
        # Completion message
        completion_text = f"""
✅ **2FA Generation Complete!**
━━━━━━━━━━━━━━━━━━━

🔑 **Your Secret Key:**
`{secret}`

⚠️ **Keep this key safe!**
You can use it anytime to generate codes.

📌 _Use /start to return to menu_
"""
        await status_msg.edit_text(completion_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"2FA error for {user_id}: {e}")
        await status_msg.edit_text("❌ **Error generating 2FA codes. Please try again.**", parse_mode='Markdown')

# ==================== FACEBOOK UID EXTRACTOR ====================
async def extract_facebook_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔗 **Send me your Facebook profile link:**\n\n_Example: https://facebook.com/username_", parse_mode='Markdown')
    context.user_data['waiting_for_uid'] = True

async def process_facebook_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    link = update.message.text.strip()
    
    processing_msg = await update.message.reply_text("🔄 **Processing your request...**\n\n_Extracting UID from Facebook_", parse_mode='Markdown')
    
    # Update stats
    if user_id in user_data:
        user_data[user_id]["total_uid"] += 1
        save_data()
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        response = requests.get(link, timeout=15, headers=headers)
        html_content = response.text
        
        uid = None
        
        # Pattern 1: userID
        match = re.search(r'"userID":"(\d+)"', html_content)
        if match:
            uid = match.group(1)
        
        # Pattern 2: entity_id
        if not uid:
            match = re.search(r'entity_id[=:]["\']?(\d+)', html_content)
            if match:
                uid = match.group(1)
        
        # Pattern 3: profile_id
        if not uid:
            match = re.search(r'profile_id[=:]["\']?(\d+)', html_content)
            if match:
                uid = match.group(1)
        
        # Pattern 4: Direct URL
        if not uid:
            match = re.search(r'facebook\.com/(\d+)', link)
            if match:
                uid = match.group(1)
        
        if uid:
            result_text = f"""
✅ **UID Extracted Successfully!**
━━━━━━━━━━━━━━━━━━━

🔗 **Original Link:**
`{link[:60]}...`

🆔 **Facebook UID:**
`{uid}`

🔗 **Profile URL:**
`https://facebook.com/{uid}`

📊 **Profile Type:** Facebook User
━━━━━━━━━━━━━━━━━━━
💡 _Use this UID for profile lookup_
"""
        else:
            result_text = f"""
❌ **UID Extraction Failed!**
━━━━━━━━━━━━━━━━━━━

🔗 **Link Provided:**
`{link[:60]}...`

⚠️ **Possible Reasons:**
• Profile might be private
• Invalid profile link
• Profile doesn't exist

💡 **Try these formats:**
• `https://facebook.com/username`
• `https://www.facebook.com/profile.php?id=12345`
"""
        
        await processing_msg.edit_text(result_text, parse_mode='Markdown')
        
    except requests.Timeout:
        await processing_msg.edit_text("❌ **Request Timeout!**\n\nPlease check your link and try again.", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"UID error for {user_id}: {e}")
        await processing_msg.edit_text("❌ **Error processing link. Please try again with a valid Facebook URL.**", parse_mode='Markdown')
    
    context.user_data['waiting_for_uid'] = False

# ==================== STATISTICS ====================
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    
    if user_id not in user_data:
        user_data[user_id] = {"total_2fa": 0, "total_uid": 0, "name": user.first_name, "joined": datetime.now().isoformat()}
    
    stats = user_data[user_id]
    
    stats_text = f"""
📊 **Your Personal Statistics**
━━━━━━━━━━━━━━━━━━━

👤 **User:** {stats.get('name', user.first_name)}
🆔 **ID:** `{user_id}`

📈 **Activity Summary:**
• 🔐 2FA Generated: `{stats.get('total_2fa', 0)}`
• 🔗 UID Extracted: `{stats.get('total_uid', 0)}`
• 📅 Total Actions: `{stats.get('total_2fa', 0) + stats.get('total_uid', 0)}`

📅 **Joined:** `{stats.get('joined', 'Unknown')[:10]}`

💎 **Status:** Active ✅
━━━━━━━━━━━━━━━━━━━
"""
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

# ==================== ABOUT ====================
async def about_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = """
ℹ️ **About This Bot**
━━━━━━━━━━━━━━━━━━━

🤖 **Name:** Ultimate Tool Bot
📌 **Version:** 2.0.0
⚡ **Status:** Online 24/7

🔧 **Features:**
• Live 2FA Code Generator
• Facebook UID Extractor  
• User Statistics Tracker
• Secure & Private

👨‍💻 **Developer:** @Shihab_920
🆓 **Price:** Free Forever

📈 **Uptime:** 99.9%
🌍 **Hosting:** Railway Cloud
━━━━━━━━━━━━━━━━━━━

✅ _Bot is fully operational_
"""
    
    await update.message.reply_text(about_text, parse_mode='Markdown')

# ==================== HEALTH CHECK ====================
async def health_check():
    """Keep bot alive with periodic logging"""
    while True:
        logger.info("Bot health check: OK")
        await asyncio.sleep(300)  # Every 5 minutes

# ==================== MESSAGE HANDLER ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔐 Generate 2FA":
        await generate_2fa(update, context)
    
    elif text == "🔗 FB Link → UID":
        await extract_facebook_uid(update, context)
    
    elif text == "📊 My Stats":
        await show_stats(update, context)
    
    elif text == "ℹ️ About Bot":
        await about_bot(update, context)
    
    elif context.user_data.get('waiting_for_uid'):
        await process_facebook_link(update, context)
    
    elif "facebook.com" in text or "fb.com" in text or "fb.me" in text:
        await process_facebook_link(update, context)
    
    else:
        await update.message.reply_text("❌ **Invalid option!**\n\nPlease use the menu buttons below.", parse_mode='Markdown', reply_markup=main_menu)

# ==================== ERROR HANDLER ====================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ **An error occurred. Please try again later.**", parse_mode='Markdown')

# ==================== MAIN FUNCTION ====================
def main():
    # Load existing data
    load_data()
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    
    # Start health check task
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(health_check())
    
    logger.info("=" * 50)
    logger.info("🤖 BOT STARTED SUCCESSFULLY!")
    logger.info("📌 Status: PRODUCTION MODE")
    logger.info("⚡ Running 24/7 on Railway")
    logger.info("=" * 50)
    
    # Start polling with retry logic
    while True:
        try:
            app.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                timeout=30,
                read_timeout=30,
                write_timeout=30,
                connect_timeout=30,
                pool_timeout=30
            )
        except Exception as e:
            logger.error(f"Polling error: {e}")
            logger.info("Restarting bot in 10 seconds...")
            time.sleep(10)
            continue
        break

if __name__ == "__main__":
    import time
    main()