import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 720, 1280
BG = (5, 12, 27)
CYAN = (0, 220, 255)
GOLD = (255, 190, 55)
WHITE = (242, 248, 255)


def _font(size):
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _wrap(draw, text, font, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if current and draw.textlength(trial, font=font, direction="rtl", language="fa") > max_width:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return "\n".join(lines)


def _sentences(text):
    cleaned = re.sub(r"https?://\\S+", "", text)
    parts = [p.strip(" \n•-*") for p in re.split(r"(?<=[.!؟?])\\s+|\\n+", cleaned) if p.strip()]
    return parts or [cleaned[:180]]


def _draw_scene(path, heading, body, index, total):
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    # Subtle neon frame and decorative circuitry.
    draw.rounded_rectangle((24, 24, WIDTH - 24, HEIGHT - 24), radius=34, outline=CYAN, width=3)
    draw.ellipse((WIDTH - 180, 70, WIDTH + 70, 320), outline=(0, 80, 115), width=4)
    draw.ellipse((-120, HEIGHT - 300, 150, HEIGHT - 30), outline=(0, 80, 115), width=4)
    draw.rounded_rectangle((54, 72, WIDTH - 54, 142), radius=22, fill=(10, 29, 52), outline=(0, 115, 150), width=2)

    brand_font = _font(30)
    heading_font = _font(54)
    body_font = _font(39)
    small_font = _font(25)

    draw.text((WIDTH // 2, 107), "NEOVO  |  دنیای هوشمند", font=brand_font, fill=CYAN,
              anchor="mm", direction="rtl", language="fa")

    title = _wrap(draw, heading, heading_font, WIDTH - 130)
    draw.multiline_text((WIDTH // 2, 310), title, font=heading_font, fill=GOLD,
                        anchor="mm", align="center", spacing=18, direction="rtl", language="fa")

    body_wrapped = _wrap(draw, body, body_font, WIDTH - 140)
    draw.rounded_rectangle((65, 485, WIDTH - 65, 1010), radius=30,
                           fill=(9, 24, 44), outline=(0, 105, 140), width=2)
    draw.multiline_text((WIDTH // 2, 745), body_wrapped, font=body_font, fill=WHITE,
                        anchor="mm", align="center", spacing=22, direction="rtl", language="fa")

    draw.line((110, 1090, WIDTH - 110, 1090), fill=CYAN, width=3)
    draw.text((WIDTH // 2, 1150), "یاد بگیر • کشف کن • پیشرفت کن",
              font=small_font, fill=CYAN, anchor="mm", direction="rtl", language="fa")
    draw.text((WIDTH // 2, 1210), f"{index:02d} / {total:02d}",
              font=small_font, fill=GOLD, anchor="mm")
    image.save(path, "PNG")


def create_video(post_text):
    """Create a short silent vertical slideshow video from the generated Persian post."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is not installed")

    parts = _sentences(post_text)
    heading = parts[0][:100] if parts else "دانستنی امروز"
    body_parts = parts[1:] or parts
    # Split into up to three readable scenes.
    scenes = []
    chunks = 3
    for i in range(chunks):
        start = round(i * len(body_parts) / chunks)
        end = round((i + 1) * len(body_parts) / chunks)
        segment = " ".join(body_parts[start:end]).strip()
        if segment:
            scenes.append(segment[:420])
    if not scenes:
        scenes = [post_text[:420]]
    scenes = scenes[:3]

    with tempfile.TemporaryDirectory(prefix="neovo_video_") as workdir:
        work = Path(workdir)
        slides = []
        for i, body in enumerate(scenes, start=1):
            slide = work / f"slide_{i:02d}.png"
            _draw_scene(slide, heading if i == 1 else f"نکته {i}", body, i, len(scenes))
            slides.append(slide)

        concat_file = work / "slides.txt"
        lines = []
        for slide in slides:
            lines.append(f"file '{slide.as_posix()}'")
            lines.append("duration 7")
        lines.append(f"file '{slides[-1].as_posix()}'")
        concat_file.write_text("\\n".join(lines) + "\\n", encoding="utf-8")

        fd, output_name = tempfile.mkstemp(prefix="neovo_", suffix=".mp4")
        os.close(fd)
        output = Path(output_name)
        command = [
            ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-vf", "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
            "-r", "24", "-c:v", "libx264", "-preset", "ultrafast",
            "-movflags", "+faststart", "-an", str(output),
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            output.unlink(missing_ok=True)
            raise RuntimeError("ساخت ویدیو ناموفق بود: " + result.stderr[-1200:])
        return output
