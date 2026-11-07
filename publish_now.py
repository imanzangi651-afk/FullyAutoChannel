import asyncio
import os
from pathlib import Path
from telegram import Bot
import bot
from video_maker import create_video, create_post_image

POSTS = [
"""🤖 هوش مصنوعی چطور پاسخ می‌سازد؟

مدل‌های زبانی با بررسی الگوهایی که در داده‌های آموزشی یاد گرفته‌اند، پاسخ‌هایی متناسب با درخواست ما تولید می‌کنند.

اما یک نکته مهم: پاسخ روان همیشه به معنی پاسخ درست نیست.

برای استفاده بهتر:
• اطلاعات مهم را با منبع معتبر بررسی کن.
• سؤال را دقیق و همراه با زمینه مطرح کن.
• از ابزار هوش مصنوعی بخواه مراحل پاسخ را روشن کند.
• اطلاعات خصوصی را در ابزارهای ناشناس وارد نکن.

تو بیشتر از هوش مصنوعی برای یادگیری استفاده می‌کنی یا ساختن چیزهای جدید؟""",
"""💻 چرا تراشه‌های هوش مصنوعی اهمیت دارند؟

آموزش و اجرای مدل‌های هوش مصنوعی به محاسبات زیادی نیاز دارد. به همین دلیل پردازنده‌های گرافیکی و شتاب‌دهنده‌های مخصوص هوش مصنوعی نقش مهمی در این حوزه پیدا کرده‌اند.

این تراشه‌ها می‌توانند بسیاری از محاسبات موازی را سریع‌تر انجام دهند.

نکته جالب اینکه همه پردازش‌ها الزاماً در فضای ابری انجام نمی‌شوند؛ بعضی قابلیت‌های هوش مصنوعی مستقیماً روی گوشی و لپ‌تاپ اجرا می‌شوند.

به نظرت اجرای هوش مصنوعی روی دستگاه شخصی مهم‌تر است یا سرویس‌های آنلاین؟""",
"""📱 هوش مصنوعی روی گوشی؛ بدون وابستگی دائمی به اینترنت؟

بعضی مدل‌های هوش مصنوعی کوچک می‌توانند مستقیماً روی گوشی یا لپ‌تاپ اجرا شوند.

مزیت‌های این روش:
• امکان استفاده آفلاین در برخی قابلیت‌ها
• کاهش نیاز به ارسال داده به سرور
• پاسخ‌گویی سریع‌تر در بعضی کارها

البته مدل‌های کوچک معمولاً محدودیت‌هایی در سرعت، حافظه و توانایی دارند و همه کارها را مثل مدل‌های بزرگ انجام نمی‌دهند.

فناوری هوش مصنوعی آفلاین را برای چه کاری مفیدتر می‌دانی؟""",
"""🧠 واقعیت مجازی و واقعیت افزوده چه تفاوتی دارند؟

واقعیت مجازی (VR) محیطی دیجیتال می‌سازد که کاربر در آن غوطه‌ور می‌شود.

واقعیت افزوده (AR) اطلاعات یا عناصر دیجیتال را روی تصویر دنیای واقعی قرار می‌دهد.

برای نمونه، در VR ممکن است وارد یک محیط آموزشی شبیه‌سازی‌شده شوی؛ اما در AR می‌توانی مدل سه‌بعدی یک وسیله را روی میز واقعی ببینی.

این فناوری‌ها در آموزش، طراحی، پزشکی و سرگرمی کاربرد دارند.

تو کدام تجربه را جذاب‌تر می‌دانی؟"""
,
"""⚡ هوش مصنوعی لبه‌ای چیست و چرا مهم شده؟

هوش مصنوعی لبه‌ای (Edge AI) یعنی بخشی از پردازش هوشمند به‌جای ارسال همه داده‌ها به سرورهای دوردست، نزدیک به محل تولید داده انجام شود؛ مثلاً روی گوشی، دوربین هوشمند یا دستگاه‌های اینترنت اشیا.

چرا اهمیت دارد؟
• کاهش تأخیر در بعضی کاربردها
• امکان کارکرد برخی قابلیت‌ها بدون اینترنت
• کنترل بهتر بر محل پردازش داده‌ها

البته دستگاه‌های کوچک محدودیت توان پردازشی و حافظه دارند و همه مدل‌ها روی آن‌ها اجرا نمی‌شوند.

به نظرت کدام وسیله در آینده بیشتر از هوش مصنوعی لبه‌ای استفاده می‌کند؟"""
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
    content = POSTS[-1] if os.getenv('FORCE_NEW_POST', '').lower() == 'true' else POSTS[slot_number % len(POSTS)]
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
