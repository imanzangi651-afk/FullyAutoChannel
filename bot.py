import asyncio
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from openai import OpenAI
from telegram import Bot

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
CHANNEL_ID = os.getenv("CHANNEL_ID", "").strip()
API_KEY = (os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
BASE_URL = (os.getenv("GROQ_BASE_URL") or "https://api.groq.com/openai/v1").strip()
MODEL = os.getenv("MODEL_NAME", "openai/gpt-oss-20b").strip()
TIMEZONE_NAME = os.getenv("TIMEZONE", "Asia/Tehran").strip()
TIMEZONE = ZoneInfo(TIMEZONE_NAME)
DB_PATH = ROOT / "data" / "published.sqlite3"

PROMPT = """تو سردبیر حرفه‌ای کانال تلگرامی NEOVO | دنیای هوشمند هستی.
برای مخاطب فارسی‌زبان، محتوای اصیل و قابل‌اشتراک فقط درباره هوش مصنوعی و فناوری تولید کن؛
از مدل‌های زبانی، ابزارهای AI، رباتیک، تراشه‌ها، گجت‌ها، برنامه‌نویسی،
فناوری‌های نوظهور و دستاوردهای علمی مرتبط موضوع انتخاب کن.

قواعد:
- هر بار موضوعی مشخص، تازه و متفاوت از هوش مصنوعی یا تکنولوژی انتخاب کن؛ از موضوعات عمومی رشد کانال و تبلیغات دوری کن.
- خط اول قلابی کوتاه و کنجکاوی‌برانگیز باشد، اما گمراه‌کننده و اغراق‌آمیز نباشد.
- متن حدود ۱۰۰ تا ۱۶۰ کلمه، ساده، دقیق و کاربردی باشد.
- یک نکته جالبِ درست، مثال ملموس یا راهکار امن و قابل‌اجرا اضافه کن.
- آمار، خبر، نقل‌قول یا ادعای علمی ساختگی نساز؛ در صورت تردید ادعا را قطعی بیان نکن.
- آموزش نفوذ غیرمجاز یا کار خطرناک نده؛ نکته‌های امنیتی باید دفاعی و ایمن باشند.
- حداکثر ۳ ایموجی و ۲ تا ۴ هشتگ واقعاً مرتبط استفاده کن.
- پایان پست یک پرسش مشخص برای گفت‌وگو و دعوت کوتاهی برای فرستادن آن به دوستی که از آن استفاده می‌کند داشته باشد.
- تبلیغ دروغین، وعده درآمد، درخواست اسپم یا عضویت اجباری ننویس.
- نام NEOVO را فقط وقتی طبیعی است بیاور.
فقط متن نهایی پست را برگردان."""

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(ROOT / "auto_channel.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("channel-bot")


def validate():
    missing = []
    if not TOKEN:
        missing.append("TELEGRAM_TOKEN")
    if not CHANNEL_ID:
        missing.append("CHANNEL_ID")
    if not API_KEY:
        missing.append("GROQ_API_KEY یا OPENAI_API_KEY")
    if missing:
        raise RuntimeError("این مقادیر در فایل .env خالی هستند: " + ", ".join(missing))
    if not CHANNEL_ID.startswith("@") and not CHANNEL_ID.lstrip("-").isdigit():
        raise RuntimeError("CHANNEL_ID باید مانند @channelname یا شناسه عددی باشد.")


def init_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS published_slots (
                slot_key TEXT PRIMARY KEY,
                telegram_message_id INTEGER NOT NULL,
                published_at TEXT NOT NULL
            )
        """)
        conn.commit()


def current_slot_key():
    now = datetime.now(TIMEZONE)
    minute_slot = (now.minute // 5) * 5
    return now.strftime("%Y-%m-%d-%H-") + f"{minute_slot:02d}"


def already_published(slot_key):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT 1 FROM published_slots WHERE slot_key = ?",
            (slot_key,),
        ).fetchone()
    return row is not None


def mark_published(slot_key, message_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO published_slots "
            "(slot_key, telegram_message_id, published_at) VALUES (?, ?, ?)",
            (slot_key, message_id, datetime.now(TIMEZONE).isoformat()),
        )
        conn.commit()


def generate_post():
    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        timeout=90.0,
        max_retries=2,
    )
    now_text = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M")
    result = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": f"برای زمان {now_text} یک موضوع تازه انتخاب کن."},
        ],
        temperature=0.7,
        max_tokens=700,
    )
    content = (result.choices[0].message.content or "").strip()
    if not content:
        raise RuntimeError("مدل هوش مصنوعی متن خالی برگرداند.")
    if len(content) > 4000:
        content = content[:3990].rsplit(" ", 1)[0] + "…"
    return content


async def scheduled_job(bot):
    slot_key = current_slot_key()
    if already_published(slot_key):
        log.info("این بازه ۵ دقیقه‌ای قبلاً پست داشته؛ از انتشار تکراری جلوگیری شد.")
        return
    log.info("شروع تولید پست برای بازه %s با مدل %s", slot_key, MODEL)
    try:
        content = await asyncio.to_thread(generate_post)
        now = datetime.now(TIMEZONE)
        slot_number = now.hour * 12 + (now.minute // 5)
        publish_video = (slot_number % 2 == 0)

        if publish_video:
            media_path = None
            try:
                from video_maker import create_video
                media_path = await asyncio.to_thread(create_video, content)
                with open(media_path, "rb") as media_file:
                    message = await bot.send_video(
                        chat_id=CHANNEL_ID,
                        video=media_file,
                        caption=content[:1000],
                        supports_streaming=True,
                    )
                log.info("ویدیو با موفقیت منتشر شد. message_id=%s", message.message_id)
            except Exception:
                log.exception("ساخت یا ارسال ویدیو ناموفق بود؛ ارسال متن انجام می‌شود.")
                message = await bot.send_message(chat_id=CHANNEL_ID, text=content)
            finally:
                if media_path:
                    Path(media_path).unlink(missing_ok=True)
        else:
            media_path = None
            try:
                from video_maker import create_post_image
                media_path = await asyncio.to_thread(create_post_image, content)
                with open(media_path, "rb") as media_file:
                    message = await bot.send_photo(
                        chat_id=CHANNEL_ID,
                        photo=media_file,
                        caption=content[:1000],
                    )
                log.info("متن همراه عکس با موفقیت منتشر شد. message_id=%s", message.message_id)
            except Exception:
                log.exception("ساخت یا ارسال عکس ناموفق بود؛ ارسال متن انجام می‌شود.")
                message = await bot.send_message(chat_id=CHANNEL_ID, text=content)
            finally:
                if media_path:
                    Path(media_path).unlink(missing_ok=True)

        mark_published(slot_key, message.message_id)
    except Exception:
        log.exception("تولید یا انتشار پست ناموفق بود.")


async def main():
    validate()
    init_database()
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    async with Bot(TOKEN) as bot:
        me = await bot.get_me()
        log.info("اتصال تلگرام برقرار شد؛ ربات: @%s", me.username or "unknown")
        scheduler.add_job(
            scheduled_job,
            trigger="cron",
            minute="*/5",
            timezone=TIMEZONE,
            args=[bot],
            id="five_minute_channel_post",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600,
        )
        scheduler.start()
        log.info("ربات فعال است؛ هر ۵ دقیقه به وقت %s پست می‌گذارد.", TIMEZONE_NAME)
        try:
            while True:
                await asyncio.sleep(60)
        finally:
            scheduler.shutdown(wait=False)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("ربات با درخواست کاربر متوقف شد.")
