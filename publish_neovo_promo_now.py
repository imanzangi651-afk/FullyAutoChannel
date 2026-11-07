import json
import os
import urllib.parse
import urllib.request

token = os.environ["TELEGRAM_TOKEN"]
channel = os.environ["CHANNEL_ID"]
bot_url = f"https://api.telegram.org/bot{token}/sendMessage"

text = """🌐 NEOVO | مدیریت هوشمند کانال تلگرام

کانالت را حرفه‌ای‌تر مدیریت کن؛ بدون دردسر انتشار دستی!

✨ خدمات NEOVO:
• برنامه‌ریزی و انتشار منظم محتوا
• تولید متن با کمک هوش مصنوعی
• انتشار پست‌های تصویری و ویدئویی
• برنامه‌ریزی تبلیغات و معرفی خدمات
• دریافت سفارش و پیگیری درخواست‌ها از طریق ربات

💼 پلن‌های مدیریت کانال از ماهانه ۲ میلیون تومان شروع می‌شوند.

📩 برای مشاهده پلن‌ها و ثبت سفارش، از ربات رسمی NEOVO استفاده کن."""

keyboard = {
    "inline_keyboard": [[
        {"text": "🤖 ورود به ربات و مشاهده پلن‌ها", "url": "https://t.me/Iman_Channel_Manager_Bot"}
    ], [
        {"text": "📩 ارتباط با ما", "url": "https://t.me/iman_1258"}
    ]]
}

payload = urllib.parse.urlencode({
    "chat_id": channel,
    "text": text,
    "reply_markup": json.dumps(keyboard, ensure_ascii=False)
}).encode()

request = urllib.request.Request(bot_url, data=payload)
with urllib.request.urlopen(request, timeout=30) as response:
    result = json.loads(response.read().decode("utf-8"))

if not result.get("ok"):
    raise RuntimeError("Telegram API did not confirm the message")

print("PROMO_SENT message_id=" + str(result["result"]["message_id"]))
