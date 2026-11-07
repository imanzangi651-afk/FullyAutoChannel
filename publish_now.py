import asyncio
import bot
from telegram import Bot

async def main():
    bot.validate()
    bot.init_database()
    slot_key = bot.current_slot_key()

    if bot.already_published(slot_key):
        print("This three-hour slot has already been published.")
        return

    content = await asyncio.to_thread(bot.generate_post)
    async with Bot(bot.TOKEN) as client:
        message = await client.send_message(chat_id=bot.CHANNEL_ID, text=content)
    bot.mark_published(slot_key, message.message_id)
    print(f"Published successfully. Telegram message ID: {message.message_id}")

if __name__ == "__main__":
    asyncio.run(main())
