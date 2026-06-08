"""Stage 3 of the pipeline: Script -> narrated MP4.

Builds dark-themed 1920x1080 slides (Pillow), narrates each with gTTS, and
assembles them into a single MP4 with MoviePy/ffmpeg. Each slide is shown for
exactly as long as its narration segment, so audio and visuals stay in sync.
"""
from __future__ import annotations

import os
import textwrap
from pathlib import Path
from typing import Callable, List, Tuple

from PIL import Image, ImageDraw, ImageFont

# Use the ffmpeg binary bundled with imageio-ffmpeg (no system install needed).
os.environ.setdefault("IMAGEIO_FFMPEG_EXE", "")
try:
    import imageio_ffmpeg
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:  # pragma: no cover
    pass

from gtts import gTTS  # noqa: E402
from moviepy.editor import (  # noqa: E402
    AudioFileClip,
    ImageClip,
    concatenate_videoclips,
)

from config import ScriptResult  # noqa: E402

W, H = 1920, 1080
BG = (15, 17, 21)
FG = (231, 235, 242)
MUTED = (154, 166, 184)
ACCENT = (79, 140, 255)

ProgressFn = Callable[[int, str], None]


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _wrap(draw, text, font, max_w) -> List[str]:
    lines: List[str] = []
    for para in text.split("\n"):
        words = para.split()
        if not words:
            lines.append("")
            continue
        cur = words[0]
        for w in words[1:]:
            if draw.textlength(cur + " " + w, font=font) <= max_w:
                cur += " " + w
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def _slide(path: Path, kicker: str, body: str, footer: str = "") -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    margin = 140

    if kicker:
        kf = _font(40)
        d.text((margin, 120), kicker.upper(), font=kf, fill=ACCENT)
        d.line((margin, 185, margin + 90, 185), fill=ACCENT, width=5)

    bf = _font(76)
    lines = _wrap(d, body, bf, W - 2 * margin)
    line_h = 96
    total_h = line_h * len(lines)
    y = max(260, (H - total_h) // 2)
    for ln in lines:
        d.text((margin, y), ln, font=bf, fill=FG)
        y += line_h

    if footer:
        ff = _font(34)
        for fl in _wrap(d, footer, ff, W - 2 * margin)[:3]:
            d.text((margin, H - 150), fl, font=ff, fill=MUTED)
            break
    img.save(path)


def _segments(s: ScriptResult) -> List[Tuple[str, str, str, str]]:
    """(kicker, on-screen body, footer, narration) per slide."""
    segs: List[Tuple[str, str, str, str]] = []
    segs.append(("", s.youtube_title, "", s.youtube_title))
    segs.append(("Cold open", s.cold_artifact, s.promise, f"{s.cold_artifact}. {s.promise}"))
    for i, st in enumerate(s.steps, 1):
        segs.append((f"How it works · step {i}", st.step, f"On screen: {st.doc}", st.step))
    if s.illustrative:
        segs.append(("The case", s.illustrative, "", s.illustrative))
    segs.append(("See it everywhere", s.pattern_general, s.other_places, s.pattern_general))
    segs.append(("", s.close, "", s.close))
    return segs


def build_video(s: ScriptResult, out_dir: Path, progress: ProgressFn | None = None) -> Path:
    def report(p: int, msg: str) -> None:
        if progress:
            progress(p, msg)

    work = out_dir / ("video_" + str(abs(hash(s.youtube_title)) % 10_000_000))
    work.mkdir(parents=True, exist_ok=True)

    segs = _segments(s)
    clips = []
    n = len(segs)
    for i, (kicker, body, footer, speak) in enumerate(segs):
        report(int(10 + 70 * i / n), f"Rendering slide {i + 1}/{n}")
        img_path = work / f"slide_{i:02d}.png"
        _slide(img_path, kicker, body, footer)

        audio_path = work / f"audio_{i:02d}.mp3"
        gTTS(text=speak or body, lang="en").save(str(audio_path))
        narration = AudioFileClip(str(audio_path))
        dur = narration.duration + 0.6  # small tail of silence

        clip = ImageClip(str(img_path)).set_duration(dur).set_audio(narration)
        clips.append(clip)

    report(85, "Stitching video")
    final = concatenate_videoclips(clips, method="compose")
    out_path = out_dir / (work.name + ".mp4")
    final.write_videofile(
        str(out_path),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        logger=None,
    )
    for c in clips:
        c.close()
    final.close()
    report(100, "Video ready")
    return out_path
