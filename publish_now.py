import asyncio
import bot
from pathlib import Path
from telegram import Bot
from video_maker import create_video, create_post_image


async def main():
    bot.validate()
    bot.init_database()
    slot_key = bot.current_slot_key()

    if bot.already_published(slot_key):
        print("This three-hour slot has already been published.")
        return

    now = bot.datetime.now(bot.TIMEZONE)
    is_daily_promo = now.hour == 12
    content = await asyncio.to_thread(bot.generate_post)
    video_path = None
    async with Bot(bot.TOKEN) as client:
        if now.hour % 2 == 0:
            try:
                video_path = await asyncio.to_thread(create_video, content)
                caption = content if len(content) <= 1024 else content[:1000].rsplit(" ", 1)[0] + "…"
                with open(video_path, "rb") as video_file:
                    message = await client.send_video(chat_id=bot.CHANNEL_ID, video=video_file, caption=caption, supports_streaming=True)
                print(f"Video published. Telegram message ID: {message.message_id}")
            except Exception as exc:
                print(f"Video failed; sending text instead: {exc}")
                message = await client.send_message(chat_id=bot.CHANNEL_ID, text=content)
            finally:
                if video_path:
                    Path(video_path).unlink(missing_ok=True)
        else:
            image_path = await asyncio.to_thread(create_post_image, content)
            try:
                with open(image_path, "rb") as image_file:
                    message = await client.send_photo(chat_id=bot.CHANNEL_ID, photo=image_file, caption=content[:1024])
                print(f"Text and image published. Telegram message ID: {message.message_id}")
            finally:
                Path(image_path).unlink(missing_ok=True)

        if is_daily_promo:
            promo = (
                "🌐 طراحی سایت حرفه‌ای برای کسب‌وکار شما\n\n"
                "می‌خواهید کسب‌وکارتان در اینترنت حضور حرفه‌ای‌تری داشته باشد؟\n"
                "برای معرفی خدمات، نمایش نمونه‌کارها و ارتباط آسان با مشتریان، وب‌سایت اختصاصی داشته باشید.\n\n"
                "📩 سفارش و مشاوره:\n"
                "تلگرام: @iman_1258\n"
                "تلفن: 09999571259\n\n"
                "برای شروع، پیام بدهید تا درباره نیازهای وب‌سایتتان صحبت کنیم.\n"
                "#طراحی_سایت #کسب_و_کار_آنلاین #وبسایت"
            )
            promo_image = await asyncio.to_thread(create_post_image, promo)
            try:
                with open(promo_image, "rb") as image_file:
                    promo_message = await client.send_photo(
                        chat_id=bot.CHANNEL_ID,
                        photo=image_file,
                        caption=promo[:1024],
                        reply_markup={
                            "inline_keyboard": [[
                                {"text": "📝 ثبت سفارش طراحی سایت", "url": "https://t.me/Iman_Channel_Manager_Bot"}
                            ]]
                        },
                    )
                print(f"Daily website-design promotion with image published. Telegram message ID: {promo_message.message_id}")
            finally:
                Path(promo_image).unlink(missing_ok=True)

    bot.mark_published(slot_key, message.message_id)


if __name__ == "__main__":
    asyncio.run(main())
