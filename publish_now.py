import asyncio
import os
from pathlib import Path
from telegram import Bot
import bot
from video_maker import create_video, create_post_image

POSTS = [
"""🤖 NEOVO چیست؟

NEOVO ربات تلگرامی ما برای ساده‌تر کردن ارتباط با خدمات و ثبت درخواست‌هاست.

از طریق ربات می‌توانی:
• خدمات و گزینه‌های موجود را ببینی
• درخواست یا سفارش خودت را ثبت کنی
• اطلاعات لازم برای پیگیری را ارسال کنی

هدف ما این است که مسیر ثبت سفارش در تلگرام ساده‌تر و منظم‌تر باشد.

تو دوست داری چه قابلیتی به NEOVO اضافه شود؟""",
"""📝 آموزش ثبت سفارش در NEOVO

برای شروع کار با ربات:
۱) وارد ربات تلگرامی NEOVO شو.
۲) دستور شروع یا دکمه شروع را بزن.
۳) بخش خدمات موردنظرت را انتخاب کن.
۴) اطلاعات درخواستت را با دقت وارد و ارسال کن.

قبل از ارسال، متن سفارش را یک بار بررسی کن تا جزئیات درست ثبت شوند.

پیشنهادت برای ساده‌تر شدن این فرایند چیست؟""",
"""🛠️ پنل مدیریت NEOVO چه کاربردی دارد؟

پنل مدیریت برای مدیر ربات طراحی شده تا بتواند درخواست‌های ثبت‌شده را منظم‌تر بررسی و مدیریت کند.

یک پنل کاربردی باید:
• دسترسی مدیر را از کاربران عادی جدا کند
• درخواست‌ها را قابل پیگیری نمایش دهد
• مدیریت خدمات و پیام‌ها را ساده کند

امنیت دسترسی مدیریتی یکی از بخش‌های مهم هر ربات سفارش‌گیری است.""",
"""💡 چرا ثبت سفارش با ربات تلگرامی مفید است؟

وقتی مسیر ثبت درخواست مشخص باشد، کاربر لازم نیست برای هر مرحله منتظر پاسخ دستی بماند.

مزیت‌های یک ربات سفارش‌گیری منظم:
• دریافت درخواست‌ها در قالب مشخص
• کاهش پیام‌های پراکنده
• دسترسی آسان از داخل تلگرام
• نظم بهتر در پیگیری سفارش‌ها

NEOVO را با هدف ساده‌تر کردن همین مسیر توسعه می‌دهیم."""
]

async def main():
    if not bot.TOKEN or not bot.CHANNEL_ID:
        raise RuntimeError("TELEGRAM_TOKEN یا CHANNEL_ID تنظیم نشده است.")
    bot.init_database()
    slot_key = bot.current_slot_key()
    if bot.already_published(slot_key):
        print("SLOT_ALREADY_PUBLISHED", slot_key)
        return

    now = bot.datetime.now(bot.TIMEZONE)
    slot_number = now.hour * 12 + (now.minute // 5)
    force_video = os.getenv('FORCE_VIDEO', '').lower() == 'true'
    content = POSTS[-1] if (os.getenv('FORCE_NEW_POST', '').lower() == 'true' or os.getenv('FORCE_VIDEO', '').lower() == 'true') else POSTS[slot_number % len(POSTS)]
    async with Bot(bot.TOKEN) as client:
        if force_video or slot_number % 2 == 0:
            media = await asyncio.to_thread(create_video, content)
            try:
                with open(media, "rb") as f:
                    message = await client.send_video(
                        chat_id=bot.CHANNEL_ID, video=f, caption=content,
                        supports_streaming=True
                    )
                print(f"VIDEO_PUBLISHED message_id={message.message_id}")
            finally:
                Path(media).unlink(missing_ok=True)
        else:
            image = await asyncio.to_thread(create_post_image, content)
            try:
                with open(image, "rb") as f:
                    message = await client.send_photo(
                        chat_id=bot.CHANNEL_ID, photo=f, caption=content
                    )
                print(f"PHOTO_TEXT_PUBLISHED message_id={message.message_id}")
            finally:
                Path(image).unlink(missing_ok=True)

    bot.mark_published(slot_key, message.message_id)

if __name__ == "__main__":
    asyncio.run(main())
