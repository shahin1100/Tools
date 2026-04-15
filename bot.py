import asyncio
import pyotp
import requests
import re
import os
import json
import time
import random
import string
import hashlib
import base64
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ==================== CONFIG ====================
BOT_TOKEN = "8600715105:AAEf157zFN-0T4uCFTOZ_OXKVlejci4WLR4"
ADMIN_ID = 8600715105  # Your Telegram ID
VERSION = "2.0.0"

# ==================== MAIN MENU ====================
main_menu = ReplyKeyboardMarkup(
    [
        ["🔐 Generate 2FA", "🔗 FB Link → UID"],
        ["📊 User Info", "ℹ️ About Bot"],
        ["⚙️ Tools", "👤 Profile"]
    ],
    resize_keyboard=True
)

tools_menu = ReplyKeyboardMarkup(
    [
        ["📝 Base64 Encode", "📝 Base64 Decode"],
        ["🔑 Generate Password", "📱 Generate Phone"],
        ["🔙 Back to Main"]
    ],
    resize_keyboard=True
)

# ==================== USER DATA ====================
user_data = {}

class UserSession:
    def __init__(self, user_id):
        self.user_id = user_id
        self.created_at = datetime.now()
        self.total_2fa = 0
        self.total_uid = 0
        
# ==================== UTILITY FUNCTIONS ====================
def save_user_data():
    try:
        with open("users.json", "w") as f:
            json.dump(user_data, f, default=str)
    except:
        pass

def load_user_data():
    global user_data
    try:
        with open("users.json", "r") as f:
            user_data = json.load(f)
    except:
        user_data = {}

def generate_secure_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))

def generate_bangladesh_phone():
    operators = ['017', '018', '019', '013', '014', '015', '016']
    operator = random.choice(operators)
    number = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    return f"{operator}{number}"

def get_facebook_uid_method1(link):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        response = requests.get(link, timeout=15, headers=headers)
        text = response.text
        
        patterns = [
            r'"userID":"(\d+)"',
            r'"uid":"(\d+)"',
            r'profile_id=(\d+)',
            r'entity_id=(\d+)',
            r'pages\["(\d+)"\]',
            r'"profile_id":"(\d+)"',
            r'id="u_0_[^"]+"[^>]+data-userid="(\d+)"',
            r'data-profileid="(\d+)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        # Try from URL
        url_match = re.search(r'facebook\.com/(\d+)(?:\?|$)', link)
        if url_match:
            return url_match.group(1)
            
        url_match2 = re.search(r'fb\.com/(\d+)(?:\?|$)', link)
        if url_match2:
            return url_match2.group(1)
            
        return None
    except:
        return None

def get_facebook_uid_method2(link):
    try:
        # Graph API approach
        if "facebook.com" in link:
            parts = link.rstrip('/').split('/')
            for part in parts:
                if part.isdigit() and len(part) > 5:
                    return part
        return None
    except:
        return None

def get_facebook_uid_final(link):
    uid = get_facebook_uid_method1(link)
    if uid:
        return uid
    uid = get_facebook_uid_method2(link)
    if uid:
        return uid
    return "UID not found. Try another link format."

# ==================== 2FA GENERATOR ====================
async def generate_2fa_live(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    
    msg = await update.message.reply_text("🔄 **Generating 2FA Codes...**\n\n_This will run for 60 seconds_", parse_mode='Markdown')
    
    if str(user_id) not in user_data:
        user_data[str(user_id)] = {"total_2fa": 0, "total_uid": 0}
    user_data[str(user_id)]["total_2fa"] += 1
    save_user_data()
    
    start_time = time.time()
    
    for i in range(60):
        current_code = totp.now()
        elapsed = int(time.time() - start_time)
        remaining = 30 - (elapsed % 30)
        if remaining <= 0:
            remaining = 30
            
        progress_bar = "█" * (i // 6) + "░" * (10 - (i // 6))
        
        text = f"""
╔══════════════════════════╗
║     🔐 LIVE 2FA GENERATOR    ║
╚══════════════════════════╝

📋 **SECRET KEY:**
`{secret}`

🔢 **CURRENT CODE:**
`{current_code}`

⏱️ **EXPIRES IN:** `{remaining} seconds`

📊 **PROGRESS:** `{progress_bar}`
⏰ **TIME LEFT:** `{60 - i} seconds`

💡 Save this secret key for future use!
        """
        
        try:
            await msg.edit_text(text, parse_mode='Markdown')
        except:
            pass
        
        await asyncio.sleep(1)
    
    await msg.edit_text(f"""
╔══════════════════════════╗
║     ✅ 2FA GENERATION COMPLETE    ║
╚══════════════════════════╝

🔑 **Your Secret Key:** `{secret}`

⚠️ Keep this secret key safe!
You can use it anytime to generate codes.
    """, parse_mode='Markdown')

# ==================== FACEBOOK UID ====================
async def get_fb_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
╔══════════════════════════╗
║     🔗 FACEBOOK UID EXTRACTOR    ║
╚══════════════════════════╝

📝 **Send me a Facebook profile link:**

Examples:
• https://facebook.com/username
• https://www.facebook.com/123456789
• https://fb.com/profile.php?id=123456789

⚡ Fast & Accurate extraction!
    """)

async def extract_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text
    user_id = update.effective_user.id
    
    msg = await update.message.reply_text("🔄 **Processing your request...**\n\n⏳ Fetching UID from Facebook", parse_mode='Markdown')
    
    if str(user_id) not in user_data:
        user_data[str(user_id)] = {"total_2fa": 0, "total_uid": 0}
    user_data[str(user_id)]["total_uid"] += 1
    save_user_data()
    
    uid = get_facebook_uid_final(link)
    
    await asyncio.sleep(1)
    
    if uid and uid != "UID not found. Try another link format.":
        text = f"""
╔══════════════════════════╗
║     ✅ UID EXTRACTED SUCCESSFULLY    ║
╚══════════════════════════╝

🔗 **Original Link:** `{link[:50]}...`

🆔 **Facebook UID:** `{uid}`

📊 **Profile URL:** `https://facebook.com/{uid}`

💡 Use this UID for:
• Profile lookup
• API requests
• Data extraction
        """
    else:
        text = f"""
╔══════════════════════════╗
║     ❌ EXTRACTION FAILED    ║
╚══════════════════════════╝

🔗 **Link:** `{link[:50]}...`

⚠️ **Error:** {uid if uid else "Could not extract UID"}

💡 **Troubleshooting:**
• Make sure the profile is public
• Try a different link format
• Check if the profile exists
        """
    
    await msg.edit_text(text, parse_mode='Markdown')

# ==================== USER INFO ====================
async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    
    if user_id not in user_data:
        user_data[user_id] = {"total_2fa": 0, "total_uid": 0}
        save_user_data()
    
    stats = user_data[user_id]
    
    text = f"""
╔══════════════════════════╗
║     👤 USER INFORMATION    ║
╚══════════════════════════╝

📱 **Name:** {user.first_name}
🆔 **User ID:** `{user.id}`
👤 **Username:** @{user.username if user.username else 'None'}
🤖 **Bot Version:** {VERSION}

📊 **Your Statistics:**
• 🔐 2FA Generated: `{stats.get("total_2fa", 0)}`
• 🔗 UID Extracted: `{stats.get("total_uid", 0)}`
• 📅 Joined: `{datetime.now().strftime('%Y-%m-%d')}`

💎 **Status:** Active ✅
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ==================== ABOUT ====================
async def about_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""
╔══════════════════════════╗
║     ℹ️ ABOUT THIS BOT    ║
╚══════════════════════════╝

🤖 **Bot Name:** Ultimate Tool Bot
📌 **Version:** {VERSION}
👨‍💻 **Developer:** @Shihab_920
⚡ **Language:** Python + Telegram API

🔧 **Features:**
• 🔐 Live 2FA Code Generator
• 🔗 Facebook UID Extractor
• 📊 User Statistics
• 🔑 Password Generator
• 📱 Phone Number Generator
• 📝 Base64 Encoder/Decoder

📈 **Status:** Online ✅
🆓 **Cost:** Free Forever

💡 **Commands:**
/start - Show Main Menu
/help - Get Help
/stats - Your Statistics
/about - About Bot
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ==================== TOOLS ====================
async def show_tools(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛠️ **Tools Menu**\n\nChoose an option below:", parse_mode='Markdown', reply_markup=tools_menu)

async def base64_encode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 **Send me text to encode in Base64:**", parse_mode='Markdown')
    context.user_data['waiting_for'] = 'base64_encode'

async def base64_decode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 **Send me Base64 text to decode:**", parse_mode='Markdown')
    context.user_data['waiting_for'] = 'base64_decode'

async def generate_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("8 chars", callback_data="pwd_8"),
         InlineKeyboardButton("12 chars", callback_data="pwd_12"),
         InlineKeyboardButton("16 chars", callback_data="pwd_16")],
        [InlineKeyboardButton("20 chars", callback_data="pwd_20"),
         InlineKeyboardButton("24 chars", callback_data="pwd_24")]
    ])
    await update.message.reply_text("🔑 **Choose password length:**", parse_mode='Markdown', reply_markup=keyboard)

async def generate_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phones = []
    for _ in range(5):
        phones.append(generate_bangladesh_phone())
    
    text = "📱 **Generated Bangladesh Phone Numbers:**\n\n"
    for i, phone in enumerate(phones, 1):
        text += f"{i}. `{phone}`\n"
    text += "\n⚡ Valid Bangladesh mobile numbers"
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ==================== HANDLE TEXT ====================
async def handle_tools_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if context.user_data.get('waiting_for') == 'base64_encode':
        encoded = base64.b64encode(text.encode()).decode()
        await update.message.reply_text(f"✅ **Encoded:**\n`{encoded}`", parse_mode='Markdown')
        context.user_data['waiting_for'] = None
    
    elif context.user_data.get('waiting_for') == 'base64_decode':
        try:
            decoded = base64.b64decode(text).decode()
            await update.message.reply_text(f"✅ **Decoded:**\n`{decoded}`", parse_mode='Markdown')
        except:
            await update.message.reply_text("❌ Invalid Base64 string!", parse_mode='Markdown')
        context.user_data['waiting_for'] = None
    
    elif text == "🔙 Back to Main":
        await update.message.reply_text("🏠 **Main Menu**", parse_mode='Markdown', reply_markup=main_menu)

# ==================== CALLBACK HANDLER ====================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("pwd_"):
        length = int(query.data.split("_")[1])
        password = generate_secure_password(length)
        
        text = f"""
╔══════════════════════════╗
║     🔑 GENERATED PASSWORD    ║
╚══════════════════════════╝

📏 **Length:** {length} characters
🔐 **Password:** `{password}`

⚡ Strength: {'Weak' if length < 8 else 'Medium' if length < 12 else 'Strong'}

💡 Copy and save this password!
        """
        await query.edit_message_text(text, parse_mode='Markdown')

# ==================== STATS ====================
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id not in user_data:
        user_data[user_id] = {"total_2fa": 0, "total_uid": 0}
    
    stats = user_data[user_id]
    
    text = f"""
📊 **YOUR STATISTICS**

🔐 2FA Generated: `{stats.get('total_2fa', 0)}`
🔗 UID Extracted: `{stats.get('total_uid', 0)}`
📅 Total Actions: `{stats.get('total_2fa', 0) + stats.get('total_uid', 0)}`

💎 Keep using for more features!
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    total_users = len(user_data)
    total_2fa = sum(u.get('total_2fa', 0) for u in user_data.values())
    total_uid = sum(u.get('total_uid', 0) for u in user_data.values())
    
    text = f"""
👑 **ADMIN STATISTICS**

👥 Total Users: `{total_users}`
🔐 Total 2FA: `{total_2fa}`
🔗 Total UID: `{total_uid}`
📊 Total Actions: `{total_2fa + total_uid}`

🤖 Bot Status: Online ✅
📅 Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ==================== HELP ====================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
📚 **BOT HELP & COMMANDS**

🔹 **Main Features:**

1️⃣ **🔐 Generate 2FA**
   - Live 60-second 2FA codes
   - Save secret key for later use

2️⃣ **🔗 FB Link → UID**
   - Extract UID from any Facebook profile
   - Works with username and ID links

3️⃣ **📊 User Info**
   - View your profile and statistics

4️⃣ **⚙️ Tools**
   - Base64 Encode/Decode
   - Secure Password Generator
   - Phone Number Generator

📝 **Commands:**
/start - Show main menu
/help - Show this help
/stats - Your statistics
/about - Bot information

💡 **Tips:**
• All features are free
• No daily limits
• 24/7 available
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ==================== MAIN HANDLER ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔐 Generate 2FA":
        await generate_2fa_live(update, context)
    
    elif text == "🔗 FB Link → UID":
        await get_fb_uid(update, context)
    
    elif text == "📊 User Info":
        await user_info(update, context)
    
    elif text == "ℹ️ About Bot":
        await about_bot(update, context)
    
    elif text == "⚙️ Tools":
        await show_tools(update, context)
    
    elif text == "👤 Profile":
        await user_info(update, context)
    
    elif text == "📝 Base64 Encode":
        await base64_encode(update, context)
    
    elif text == "📝 Base64 Decode":
        await base64_decode(update, context)
    
    elif text == "🔑 Generate Password":
        await generate_password(update, context)
    
    elif text == "📱 Generate Phone":
        await generate_phone(update, context)
    
    elif text == "🔙 Back to Main":
        await update.message.reply_text("🏠 **Main Menu**", parse_mode='Markdown', reply_markup=main_menu)
    
    elif "facebook.com" in text or "fb.com" in text or "fb.me" in text:
        await extract_uid(update, context)
    
    elif context.user_data.get('waiting_for'):
        await handle_tools_input(update, context)
    
    else:
        await update.message.reply_text("❌ **Invalid option!**\n\nPlease use the menu buttons below.", parse_mode='Markdown', reply_markup=main_menu)

# ==================== MAIN ====================
def main():
    load_user_data()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CommandHandler("about", about_bot))
    app.add_handler(CommandHandler("admin", admin_stats))
    
    # Callback handler
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    # Message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("=" * 50)
    print("🤖 BOT STARTED SUCCESSFULLY!")
    print(f"📌 VERSION: {VERSION}")
    print(f"👑 ADMIN ID: {ADMIN_ID}")
    print("=" * 50)
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"""
╔══════════════════════════╗
║     🎉 WELCOME {user.first_name}!    ║
╚══════════════════════════╝

🤖 **Ultimate Tool Bot v{VERSION}**

🔧 **Features Available:**
• 🔐 Live 2FA Code Generator
• 🔗 Facebook UID Extractor
• 🔑 Secure Password Generator
• 📱 Phone Number Generator
• 📝 Base64 Encoder/Decoder
• 📊 User Statistics

💡 **How to use:**
Simply tap any button from the menu below!

📞 **Support:** @Shihab_920

⬇️ **Choose an option:**
    """
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=main_menu)

if __name__ == "__main__":
    main()