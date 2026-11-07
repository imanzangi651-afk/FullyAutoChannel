import asyncio
import shutil, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts

W, H = 720, 1280
BG, CYAN, GOLD, WHITE = (5, 12, 27), (0, 220, 255), (255, 190, 55), (242, 248, 255)

def font(size, bold=False):
    paths = [
        Path("/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    ]
    for path in paths:
        if path.exists():
            try: return ImageFont.truetype(str(path), size)
            except Exception: pass
    return ImageFont.load_default()

def center(draw, y, text, fnt, color):
    draw.multiline_text((W//2, y), text, font=fnt, fill=color, anchor="mm",
                        align="center", direction="rtl", spacing=20)

def make_slide(path, title, body, number):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((22,22,W-22,H-22), radius=34, outline=CYAN, width=3)
    d.ellipse((W-190,65,W+60,315), outline=(0,75,110), width=5)
    d.ellipse((-130,H-300,155,H-15), outline=(0,75,110), width=5)
    d.rounded_rectangle((52,65,W-52,145), radius=20, fill=(10,29,52), outline=(0,115,150), width=2)
    center(d,105,"NEOVO | ربات تلگرامی ما",font(27,True),CYAN)
    center(d,300,title,font(48,True),GOLD)
    d.rounded_rectangle((60,465,W-60,1010),radius=28,fill=(9,24,44),outline=(0,105,140),width=2)
    center(d,735,body,font(36),WHITE)
    d.line((105,1090,W-105,1090),fill=CYAN,width=3)
    center(d,1150,"ثبت سفارش ساده‌تر در تلگرام",font(27,True),CYAN)
    center(d,1210,f"{number:02d} / 03",font(24,True),GOLD)
    im.save(path,"PNG")

def _make_audio(path):
    narration = (
      "با NEOVO، ربات تلگرامی سفارش‌گیری ما آشنا شو. "
      "هدف این ربات ساده‌تر کردن ارتباط کاربران با خدمات و ثبت درخواست‌ها در تلگرام است. "
      "کاربر می‌تواند وارد ربات شود، بخش موردنظر را انتخاب کند و اطلاعات سفارش خود را ارسال کند. "
      "در سمت مدیریت هم درخواست‌ها باید به شکل منظم بررسی و پیگیری شوند. "
      "ما در حال توسعه تجربه‌ای ساده‌تر و کاربردی‌تر برای ثبت سفارش هستیم. "
      "برای پیشنهاد قابلیت‌های بعدی، نظرت را با ما در میان بگذار."
    )
    async def run():
        await edge_tts.Communicate(narration,"fa-IR-DilaraNeural",rate="+0%").save(str(path))
    asyncio.run(run())

def create_video(post_text=None):
    ffmpeg=shutil.which("ffmpeg")
    if not ffmpeg: raise RuntimeError("FFmpeg is not installed or not on PATH.")
    scenes=[
      ("معرفی NEOVO","ربات تلگرامی\nثبت و پیگیری درخواست",1),
      ("برای کاربران","انتخاب خدمات\nارسال جزئیات سفارش",2),
      ("برای مدیریت","بررسی درخواست‌ها\nنظم بیشتر در پیگیری",3)
    ]
    with tempfile.TemporaryDirectory(prefix="neovo_video_") as td:
        folder=Path(td); entries=[]
        for i,(title,body,num) in enumerate(scenes,1):
            slide=folder/f"slide_{i}.png"; make_slide(slide,title,body,num)
            entries.extend([f"file '{slide.as_posix()}'","duration 6"])
        entries.append(f"file '{(folder/'slide_3.png').as_posix()}'")
        concat=folder/"slides.txt"; concat.write_text("\n".join(entries)+"\n",encoding="utf-8")
        audio=folder/"narration.mp3"; _make_audio(audio)
        output=Path.cwd()/"NEOVO_Telegram_Bot_Intro.mp4"
        cmd=[ffmpeg,"-y","-f","concat","-safe","0","-i",str(concat),"-i",str(audio),
             "-vf","scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
             "-r","24","-c:v","libx264","-preset","ultrafast","-c:a","aac","-b:a","128k",
             "-shortest","-movflags","+faststart",str(output)]
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
        if result.returncode: raise RuntimeError(result.stderr[-2000:])
        return output

def create_post_image(post_text):
    output=Path.cwd()/"NEOVO_post_image.png"
    make_slide(output,"امکانات NEOVO","ثبت درخواست\nاز داخل تلگرام",1)
    return output
