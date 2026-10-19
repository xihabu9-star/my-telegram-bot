import os
import re
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
import edge_tts
import yt_dlp

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = "8788245732:AAGCJXld9R6PDiiu_Xogim0RfLUw51-Af2M"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "👋 **স্বাগতম Multi-Functional Bot-এ!**\n\n"
        "আমি আপনাকে ২টি প্রধান কাজে সাহায্য করতে পারি:\n\n"
        "🎙️ **Voice Generator:**\n"
        "যেকোনো সাধারণ বাংলা বা ইংরেজি টেক্সট মেসেজ পাঠান, আমি সেটাকে সুন্দর ভয়েস নোটে রূপান্তর করে দেব।\n\n"
        "📥 **Video Downloader:**\n"
        "যেকোনো **TikTok, Instagram, অথবা YouTube** ভিডিওর লিংক পাঠান, আমি সরাসরি ভিডিও ডাউনলোড করে পাঠিয়ে দেব।"
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")

async def generate_voice(text: str, output_file: str):
    if any('\u0980' <= char <= '\u09ff' for char in text):
        voice = "bn-BD-NabanitaNeural"
    else:
        voice = "en-US-AriaNeural"
        
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def download_video_file(url: str, output_path: str):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': 50 * 1024 * 1024,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    url_pattern = re.compile(r'https?://[^\s]+')
    
    if url_pattern.search(text):
        url = url_pattern.search(text).group(0)
        if any(domain in url.lower() for domain in ['tiktok.com', 'instagram.com', 'youtube.com', 'youtu.be']):
            status_msg = await update.message.reply_text("⏳ ভিডিও প্রসেস হচ্ছে, অনুগ্রহ করে অপেক্ষা করুন...")
            file_name = f"video_{update.message.message_id}.mp4"
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, download_video_file, url, file_name)
                if os.path.exists(file_name):
                    await status_msg.edit_text("📤 ভিডিও আপলোড হচ্ছে...")
                    with open(file_name, 'rb') as video:
                        await update.message.reply_video(video=video, caption="🎬 আপনার ডাউনলোডকৃত ভিডিও")
                    await status_msg.delete()
                else:
                    await status_msg.edit_text("❌ ভিডিওটি ডাউনলোড করা সম্ভব হয়নি। ফাইল সাইজ ৫০MB-এর বেশি হতে পারে।")
            except Exception as e:
                logging.error(f"Error downloading video: {e}")
                await status_msg.edit_text("❌ ভিডিও ডাউনলোড করতে সমস্যা হয়েছে। লিংকটি সঠিক কিনা পরীক্ষা করুন।")
            finally:
                if os.path.exists(file_name):
                    os.remove(file_name)
        else:
            await update.message.reply_text("⚠️ শুধু TikTok, Instagram, এবং YouTube-এর video লিংক সাপোর্ট করবে।")
    else:
        status_msg = await update.message.reply_text("🎙️ ভয়েস তৈরি হচ্ছে...")
        voice_file = f"voice_{update.message.message_id}.mp3"
        try:
            await generate_voice(text, voice_file)
            if os.path.exists(voice_file):
                with open(voice_file, 'rb') as voice:
                    await update.message.reply_voice(voice=voice, caption="🔊 আপনার তৈরি ভয়েস")
                await status_msg.delete()
            else:
                await status_msg.edit_text("❌ ভয়েস ফাইল তৈরি করা যায়নি।")
        except Exception as e:
            logging.error(f"Error generating voice: {e}")
            await status_msg.edit_text("❌ ভয়েস জেনারেট করতে সমস্যা হয়েছে।")
        finally:
            if os.path.exists(voice_file):
                os.remove(voice_file)

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 All-in-One Telegram Bot চালু হয়েছে...")
    app.run_polling()
