import logging
import os
import requests
import io
from telegram import Update, constants, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from pytube import YouTube

# --- কনফিগারেশন ---
# আপনার দেওয়া নতুন এপিআই কি এখানে বসানো হয়েছে
GOOGLE_API_KEY = "AIzaSyBHy9W8La_Rwrw1XyMF5rNbS_2zQRE5aQ0" 
TELEGRAM_BOT_TOKEN = "8475299865:AAE5rfJeAAEnvL3NWrkCF2XuEsXz7OV27vQ" 
CHANNEL_USERNAME = "@SH_tricks"
OWNER_ID = 6941003064 # আপনার সঠিক আইডি
OWNER_HANDLE = "@Suptho1"

# Gemini AI সেটআপ
genai.configure(api_key=GOOGLE_API_KEY)
chat_sessions = {}
user_list = set()

SYSTEM_PROMPT = f"Your name is SH AI. Owner is {OWNER_HANDLE}. You are a professional AI assistant. You can search the web, summarize YouTube videos, and generate images. Answer in Bengali or English as per user."

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
    await update.message.reply_text(f"স্বাগতম! আমি **SH AI**।\nওনার: {OWNER_HANDLE}\n\nআমি এখন পুরোপুরি সচল। যেকোনো প্রশ্ন করুন বা ছবি আঁকতে বলুন!")

# ইউটিউব ডাটা ফাংশন
def get_yt_info(url):
    try:
        yt = YouTube(url)
        return f"Title: {yt.title}\nDescription: {yt.description[:500]}"
    except: return None

# মেইন মেসেজ হ্যান্ডলার
async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_subscribed(user_id, context): return

    user_text = update.message.text if update.message.text else ""
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)

    # ১. ইমেজ জেনারেশন
    if any(word in user_text.lower() for word in ["image", "photo", "ছবি", "draw", "আঁকো"]):
        seed = user_text.replace(" ", "_")
        img_url = f"https://pollinations.ai/p/{seed}?width=1024&height=1024&nologo=true"
        try:
            response = requests.get(img_url)
            await update.message.reply_photo(photo=io.BytesIO(response.content), caption=f"এখানে আপনার ছবি: {user_text}\nBy SH AI")
            return
        except: pass

    # ২. ইউটিউব সামারি
    if "youtube.com" in user_text or "youtu.be" in user_text:
        yt_data = get_yt_info(user_text)
        if yt_data:
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(f"Summarize this YouTube video in Bengali: {yt_data}")
            await update.message.reply_text(f"🎬 **YT Summary:**\n\n{res.text}")
        else:
            await update.message.reply_text("ইউটিউব ভিডিওর তথ্য পাওয়া যায়নি।")
        return

    # ৩. এআই চ্যাট (Web Search & Memory সহ)
    if user_id not in chat_sessions:
        chat_sessions[user_id] = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=SYSTEM_PROMPT,
            tools=[{'google_search': {}}] 
        ).start_chat(history=[], enable_automatic_function_calling=True)

    try:
        # ভয়েস মেসেজ হ্যান্ডলিং
        if update.message.voice:
            v_file = await context.bot.get_file(update.message.voice.file_id)
            v_data = await v_file.download_as_bytearray()
            response = chat_sessions[user_id].send_message([{'mime_type': 'audio/ogg', 'data': bytes(v_data)}, "Reply to this voice."])
        else:
            response = chat_sessions[user_id].send_message(user_text)
        
        await update.message.reply_text(response.text, parse_mode='Markdown')
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("দুঃখিত, এপিআই কি-তে সমস্যা হচ্ছে অথবা লিমিট শেষ।")

# ব্রডকাস্ট কমান্ড
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    msg = " ".join(context.args)
    if not msg: return
    for uid in list(user_list):
        try: await context.bot.send_message(chat_id=uid, text=f"📢 **SH AI Update:**\n\n{msg}")
        except: continue

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT | filters.VOICE, handle_all))
    print("SH AI is live with New API Key...")
    app.run_polling()

if __name__ == '__main__':
    main()
