import asyncio
import os
from pathlib import Path
from telegram import Bot
import bot
from video_maker import create_video, create_post_image

POSTS = [
"""🔐 امنیت کانال را جدی بگیر

برای محافظت بهتر از کانال:
• تأیید دومرحله‌ای را فعال کن.
• دسترسی مدیران را فقط به افراد لازم بده.
• لینک‌ها و فایل‌های ناشناس را باز نکن.

امنیت خوب از عادت‌های کوچک شروع می‌شود.""",
"""📌 نظم در انتشار محتوا

برای داشتن یک کانال حرفه‌ای:
• تقویم محتوایی هفتگی داشته باش.
• موضوع پست‌ها را متنوع انتخاب کن.
• زمان انتشار را ثابت نگه دار.
• کیفیت را فدای تعداد نکن.

مخاطب به محتوای مفید و منظم برمی‌گردد.""",
"""💡 یک نکته برای مدیران کانال

قبل از انتشار هر پست، این سه مورد را بررسی کن:
۱. عنوان روشن و جذاب باشد.
۲. متن کوتاه و قابل‌فهم باشد.
۳. تصویر با موضوع هماهنگ باشد.

جزئیات کوچک، تجربه مخاطب را بهتر می‌کنند.""",
"""🚀 رشد اصولی کانال

برای رشد پایدار:
• مخاطب هدف خودت را بشناس.
• محتوای کاربردی منتشر کن.
• به بازخوردها توجه کن.
• آمار بازدید و تعامل را بررسی کن.

رشد واقعی با اعتماد ساخته می‌شود."""
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
    slot_number = now.hour * 6 + (now.minute // 10)
    force_video = os.getenv('FORCE_VIDEO', '').lower() == 'true'
    content = POSTS[slot_number % len(POSTS)]
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
