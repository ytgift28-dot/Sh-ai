import logging
import os
import requests
import io
from telegram import Update, constants, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# --- কনফিগারেশন (রেলওয়ে ড্যাশবোর্ড থেকে এডিট করবেন) ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "আপনার_নতুন_জেমিনি_কি")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "আপনার_বট_টোকেন")
CHANNEL_USERNAME = "@SH_tricks"
OWNER_ID = 6941003064 # @userinfobot থেকে আপনার আইডি নিয়ে এখানে বসান
OWNER_HANDLE = "@Suptho1"

# Gemini AI কনফিগারেশন
genai.configure(api_key=GOOGLE_API_KEY)
chat_sessions = {}
user_list = set()

# বটের পার্সোনালিটি
SYSTEM_PROMPT = f"Your name is SH AI. Owner is {OWNER_HANDLE}. Be helpful and professional in Bengali or English."

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
        await update.message.reply_text("হ্যালো! আমি **SH AI**। আমাকে ব্যবহার করতে আগে আমাদের চ্যানেলে জয়েন করুন।", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    await update.message.reply_text(f"স্বাগতম! আমি **SH AI**।\nওনার: {OWNER_HANDLE}\n\nআমি ইমেজ তৈরি এবং যেকোনো প্রশ্নের উত্তর দিতে পারি।")

# মেইন মেসেজ হ্যান্ডলার
async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_subscribed(user_id, context): return

    user_text = update.message.text if update.message.text else ""
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)

    # ১. ইমেজ জেনারেশন (FIXED)
    img_keywords = ["image", "photo", "ছবি", "আঁকো", "draw"]
    if any(word in user_text.lower() for word in img_keywords):
        seed = user_text.replace(" ", "_")
        img_url = f"https://pollinations.ai/p/{seed}?width=1024&height=1024&nologo=true"
        try:
            response = requests.get(img_url)
            await update.message.reply_photo(photo=io.BytesIO(response.content), caption=f"এখানে আপনার ছবি: {user_text}\nBy SH AI")
            return
        except:
            await update.message.reply_text("দুঃখিত, ছবি তৈরি করা যাচ্ছে না।")
            return

    # ২. এআই চ্যাট (MEMORY & WEB SEARCH)
    if user_id not in chat_sessions:
        chat_sessions[user_id] = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=SYSTEM_PROMPT,
            tools=[{'google_search': {}}]
        ).start_chat(history=[], enable_automatic_function_calling=True)

    try:
        response = chat_sessions[user_id].send_message(user_text)
        await update.message.reply_text(response.text, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text("এখন কোনো উত্তর দিতে পারছি না। একটু পরে ট্রাই করুন।")

# ৩. অ্যাডমিন কমান্ড (ব্রডকাস্ট)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("আপনি এই কমান্ড ব্যবহার করতে পারবেন না!")
        return
    
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("ব্যবহার: `/broadcast হ্যালো সবাই`", parse_mode='Markdown')
        return

    count = 0
    for uid in user_list:
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 **অ্যাডমিন নোটিশ:**\n\n{msg}")
            count += 1
        except: continue
    await update.message.reply_text(f"সফলভাবে {count} জন ইউজারকে মেসেজ পাঠানো হয়েছে।")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all))
    print("SH AI is Running...")
    app.run_polling()

if __name__ == '__main__':
    main()
