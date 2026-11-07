import asyncio
import shutil, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts

W, H = 720, 1280
BG, CYAN, GOLD, WHITE = (5,12,27), (0,220,255), (255,190,55), (242,248,255)

def font(size, bold=False):
    candidates = [
        Path("/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    ]
    for p in candidates:
        if p.exists():
            try: return ImageFont.truetype(str(p), size)
            except Exception: pass
    return ImageFont.load_default()

def center(draw, y, text, fnt, color):
    draw.multiline_text((W//2,y), text, font=fnt, fill=color, anchor="mm", align="center", direction="rtl", spacing=20)

def make_slide(path, title, body, number):
    im = Image.new("RGB", (W,H), BG); d = ImageDraw.Draw(im)
    d.rounded_rectangle((22,22,W-22,H-22), radius=34, outline=CYAN, width=3)
    d.ellipse((W-190,65,W+60,315), outline=(0,75,110), width=5)
    d.ellipse((-130,H-300,155,H-15), outline=(0,75,110), width=5)
    d.rounded_rectangle((52,65,W-52,145), radius=20, fill=(10,29,52), outline=(0,115,150), width=2)
    center(d,105,"فناوری و هوش مصنوعی",font(28,True),CYAN)
    center(d,300,title,font(47,True),GOLD)
    d.rounded_rectangle((60,465,W-60,1010),radius=28,fill=(9,24,44),outline=(0,105,140),width=2)
    center(d,735,body,font(36),WHITE)
    d.line((105,1090,W-105,1090),fill=CYAN,width=3)
    center(d,1150,"دانش فناوری | آینده هوشمند",font(27,True),CYAN)
    center(d,1210,f"{number:02d} / 03",font(24,True),GOLD)
    im.save(path,"PNG")

def _ffmpeg_path():
    found=shutil.which("ffmpeg")
    if found: return found
    raise RuntimeError("FFmpeg is not installed or not on PATH.")

def _make_audio(path):
    narration = ("سلام! امروز می‌خواهیم با یک فناوری مهم آشنا شویم: هوش مصنوعی لبه‌ای. "
      "در این روش، بخشی از پردازش هوش مصنوعی به‌جای سرورهای دوردست، روی خود دستگاه انجام می‌شود؛ "
      "مثلاً روی گوشی، دوربین هوشمند یا خودرو. "
      "نتیجه می‌تواند پاسخ‌گویی سریع‌تر، کاهش نیاز به اینترنت و کنترل بهتر داده‌ها باشد. "
      "البته دستگاه‌های کوچک محدودیت حافظه و قدرت پردازش دارند. "
      "هوش مصنوعی لبه‌ای یکی از فناوری‌هایی است که آینده ابزارهای هوشمند را شکل می‌دهد.")
    async def run():
        communicate = edge_tts.Communicate(narration, "fa-IR-DilaraNeural", rate="+0%")
        await communicate.save(str(path))
    asyncio.run(run())

def create_video(post_text=None):
    ffmpeg=_ffmpeg_path()
    scenes=[
      ("هوش مصنوعی لبه‌ای","پردازش هوشمند
نزدیک به محل تولید داده",1),
      ("کجا استفاده می‌شود؟","گوشی هوشمند
دوربین و خودرو",2),
      ("چرا اهمیت دارد؟","پاسخ سریع‌تر
نیاز کمتر به اینترنت",3)
    ]
    with tempfile.TemporaryDirectory(prefix="tech_video_") as td:
      folder=Path(td); entries=[]
      for i,(title,body,num) in enumerate(scenes,1):
        p=folder/f"slide_{i}.png"; make_slide(p,title,body,num)
        entries += [f"file '{p.as_posix()}'", "duration 6"]
      entries.append(f"file '{(folder/'slide_3.png').as_posix()}'")
      concat=folder/"slides.txt"; concat.write_text("\n".join(entries)+"\n",encoding="utf-8")
      audio=folder/"narration.mp3"; _make_audio(audio)
      out=Path.cwd()/"Persian_Technology_Video.mp4"
      cmd=[ffmpeg,"-y","-f","concat","-safe","0","-i",str(concat),"-i",str(audio),
           "-vf","scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
           "-r","24","-c:v","libx264","-preset","ultrafast","-c:a","aac","-b:a","128k",
           "-shortest","-movflags","+faststart",str(out)]
      result=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
      if result.returncode: raise RuntimeError(result.stderr[-2000:])
      return out

def create_post_image(post_text):
    path=Path.cwd()/"NEOVO_post_image.png"
    make_slide(path,"فناوری هوشمند","دانش فناوری
برای آینده‌ای بهتر",1)
    return path
