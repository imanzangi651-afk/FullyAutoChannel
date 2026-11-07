import asyncio
import bot
from pathlib import Path
from telegram import Bot
from video_maker import create_video


async def main():
    bot.validate()
    bot.init_database()
    slot_key = bot.current_slot_key()

    if bot.already_published(slot_key):
        print("This three-hour slot has already been published.")
        return

    content = await asyncio.to_thread(bot.generate_post)
    video_path = None
    async with Bot(bot.TOKEN) as client:
        try:
            video_path = await asyncio.to_thread(create_video, content)
            caption = content if len(content) <= 1024 else content[:1000].rsplit(" ", 1)[0] + "…"
            with open(video_path, "rb") as video_file:
                message = await client.send_video(
                    chat_id=bot.CHANNEL_ID,
                    video=video_file,
                    caption=caption,
                    supports_streaming=True,
                )
            print(f"Video published successfully. Telegram message ID: {message.message_id}")
        except Exception as exc:
            print(f"Video creation or upload failed; sending text instead: {exc}")
            message = await client.send_message(chat_id=bot.CHANNEL_ID, text=content)
            print(f"Text fallback published. Telegram message ID: {message.message_id}")
        finally:
            if video_path:
                Path(video_path).unlink(missing_ok=True)

    bot.mark_published(slot_key, message.message_id)


if __name__ == "__main__":
    asyncio.run(main())
