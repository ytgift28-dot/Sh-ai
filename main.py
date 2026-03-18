import logging
import os
import requests
import io
from telegram import Update, constants, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# --- কনফিগারেশন ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_USERNAME = "@SH_tricks"
OWNER_ID = 6941003064 # আপনার সঠিক আইডি এখানে দিন
OWNER_HANDLE = "@Suptho1"

# Gemini AI সেটআপ
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
chat_sessions = {}
user_list = set()

logging.basicConfig(level=logging.INFO)

# চ্যানেল সাবস্ক্রিপশন চেক
async def is_subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in [constants.ChatMemberStatus.MEMBER, constants.ChatMemberStatus.ADMINISTRATOR, constants.ChatMemberStatus.OWNER]
    except:
        return False

# স্টার্ট কমান্ড
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_list.add(user_id)
    
    if not await is_subscribed(user_id, context):
        keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]]
        await update.message.reply_text("হ্যালো! আমি **SH AI**। আগে চ্যানেলে জয়েন করুন।", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    await update.message.reply_text(f"স্বাগতম! আমি **SH AI**।\nওনার: {OWNER_HANDLE}\n\nআমি এখন সচল আছি। যেকোনো প্রশ্ন করুন!")

# মেসেজ হ্যান্ডলার
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_subscribed(user_id, context): return

    user_text = update.message.text
    if not user_text: return

    # টাইপিং শুরু
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)

    # ১. ইমেজ জেনারেশন লজিক
    if any(word in user_text.lower() for word in ["image", "photo", "ছবি", "draw"]):
        seed = user_text.replace(" ", "_")
        img_url = f"https://pollinations.ai/p/{seed}?width=1024&height=1024&nologo=true"
        try:
            response = requests.get(img_url)
            await update.message.reply_photo(photo=io.BytesIO(response.content), caption=f"এখানে আপনার ছবি: {user_text}\nBy SH AI")
            return
        except: pass

    # ২. সাধারণ এআই চ্যাট (অ্যাপিআই কল)
    try:
        if user_id not in chat_sessions:
            chat_sessions[user_id] = model.start_chat(history=[])
        
        response = chat_sessions[user_id].send_message(user_text)
        await update.message.reply_text(response.text, parse_mode='Markdown')
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("দুঃখিত, আমি এখন উত্তর দিতে পারছি না। পরে চেষ্টা করুন।")

# ব্রডকাস্ট কমান্ড
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    msg = " ".join(context.args)
    if not msg: return
    for uid in list(user_list):
        try: await context.bot.send_message(chat_id=uid, text=f"📢 **নোটিশ:**\n\n{msg}")
        except: continue

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
