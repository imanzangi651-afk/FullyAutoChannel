import shutil, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 720, 1280
BG, CYAN, GOLD, WHITE = (5,12,27), (0,220,255), (255,190,55), (242,248,255)

def font(size, bold=False):
    names = ["arialbd.ttf" if bold else "arial.ttf", "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    candidates = [Path(r"C:\Windows\Fonts") / names[0],
                  Path("/usr/share/fonts/truetype/dejavu") / names[1],
                  Path("/usr/share/fonts/truetype/noto") / ("NotoSans-Bold.ttf" if bold else "NotoSans-Regular.ttf")]
    for p in candidates:
        try:
            if p.exists(): return ImageFont.truetype(str(p), size)
        except Exception: pass
    return ImageFont.load_default()

def center(draw, y, text, fnt, color, spacing=18):
    draw.multiline_text((W//2,y), text, font=fnt, fill=color, anchor="mm", align="center", spacing=spacing)

def make_slide(path, title, body, number):
    im = Image.new("RGB", (W,H), BG); d = ImageDraw.Draw(im)
    d.rounded_rectangle((22,22,W-22,H-22), radius=34, outline=CYAN, width=3)
    d.ellipse((W-190,65,W+60,315), outline=(0,75,110), width=5)
    d.ellipse((-130,H-300,155,H-15), outline=(0,75,110), width=5)
    d.rounded_rectangle((52,65,W-52,145), radius=20, fill=(10,29,52), outline=(0,115,150), width=2)
    center(d,105,"NEOVO  |  SMART CHANNEL MANAGEMENT",font(25,True),CYAN)
    center(d,300,title,font(47,True),GOLD,22)
    d.rounded_rectangle((60,465,W-60,1010),radius=28,fill=(9,24,44),outline=(0,105,140),width=2)
    center(d,735,body,font(36),WHITE,26)
    d.line((105,1090,W-105,1090),fill=CYAN,width=3)
    center(d,1150,"PLAN  •  PUBLISH  •  GROW",font(26,True),CYAN)
    center(d,1210,f"{number:02d} / 03",font(24,True),GOLD)
    im.save(path,"PNG")

def _ffmpeg_path():
    found=shutil.which("ffmpeg")
    if found: return found
    candidates=[
      Path(__file__).resolve().parent/"node_modules"/"@ffmpeg-installer"/"win32-x64"/"ffmpeg.exe",
      Path.home()/"node_modules"/"@ffmpeg-installer"/"win32-x64"/"ffmpeg.exe"
    ]
    for candidate in candidates:
        if candidate.exists(): return str(candidate)
    raise RuntimeError("FFmpeg is not installed or not on PATH.")

def create_video(post_text=None):
    ffmpeg=_ffmpeg_path()
    scenes=[
      ("PROTECT YOUR CHANNEL","Use strong passwords\nEnable two-step verification\nReview admin access regularly"),
      ("PUBLISH WITH A PLAN","Prepare content in advance\nKeep text and visuals consistent\nFocus on quality and clarity"),
      ("MEET NEOVO","Scheduled channel publishing\nText, image and video management\nSimple order and support bot")
    ]
    with tempfile.TemporaryDirectory(prefix="neovo_video_") as td:
      folder=Path(td); entries=[]
      for i,(title,body) in enumerate(scenes,1):
        p=folder/f"slide_{i}.png"; make_slide(p,title,body,i)
        entries += [f"file '{p.as_posix()}'","duration 7"]
      entries.append(f"file '{(folder/'slide_3.png').as_posix()}'")
      concat=folder/"slides.txt"; concat.write_text("\n".join(entries)+"\n",encoding="utf-8")
      out=Path.cwd()/"NEOVO_video_now.mp4"
      cmd=[ffmpeg,"-y","-f","concat","-safe","0","-i",str(concat),"-vf","scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,format=yuv420p","-r","24","-c:v","libx264","-preset","ultrafast","-movflags","+faststart","-an",str(out)]
      result=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
      if result.returncode: raise RuntimeError(result.stderr[-1500:])
      return out

def create_post_image(post_text):
    path=Path.cwd()/"NEOVO_post_image.png"
    make_slide(path,"CHANNEL MANAGEMENT","Plan your posts\nKeep your audience informed\nBuild trust with consistency",1)
    return path
