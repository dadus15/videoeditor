#!/usr/bin/env python3
"""Assemble the Turismo Forged C01 "CNC" short (9:16, 30 s, no music).

Usage (from the project root):
    python3 edit/c01_cnc/assemble.py <clips_dir> <out.mp4>

<clips_dir> holds the generated clips s1.mp4, s2.mp4, s3.mp4, s45.mp4, s6.mp4.
Cut list, titles and audio levels live in CUTS / TITLES / AUDIO below.
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 24
FONTS = Path(".claude/skills/youtube-edit/assets/fonts")

# (clip, source in, source out). Timeline position follows from the order.
# None = black slate with silence (the hard cut before the finished wheel).
CUTS = [
    ("s1.mp4", 0.0, 5.0),    # 0.0-5.0   billet drops into the chuck
    ("s2.mp4", 0.0, 9.0),    # 5.0-14.0  milling, tracking along spokes
    ("s3.mp4", 0.5, 4.5),    # 14.0-18.0 pull back, machine reveal
    (None, 0.0, 0.5),        # 18.0-18.5 hard cut: black + silence
    ("s45.mp4", 0.0, 7.5),   # 18.5-26.0 finished wheel, slow orbit (shots 4+5)
    ("s6.mp4", 0.5, 4.5),    # 26.0-30.0 CLS 63, engine idle
]

# Which cuts keep their own sound, and at what loudness (LUFS) each is set.
# Shots 4-5 are silent by brief.
AUDIO = {0: -13.0, 1: -13.0, 2: -14.0, 5: -21.0}

# Titles: text lines, start, end, y of the first baseline block, style.
TITLES = [
    {
        "lines": [("Jeden kęs aluminium 6061", 500, 46, 0.04)],
        "t0": 7.0, "t1": 10.6, "y": 1290,
    },
    {
        "lines": [
            ("TURISMO WHEELS", 700, 64, 0.16),
            ("Wykute. Nie produkowane.", 400, 44, 0.02),
        ],
        "t0": 26.9, "t1": 30.5, "y": 400, "rule": True,
    },
]
FADE_IN, FADE_OUT = 0.6, 0.35


def run(cmd):
    print(" ".join(str(c) for c in cmd), file=sys.stderr)
    subprocess.run(cmd, check=True)


def measure_lufs(src, start, dur):
    """Integrated loudness (LUFS) of a clip section."""
    res = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{start}", "-t", f"{dur}", "-i", str(src),
                          "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
    lines = [l for l in res.stderr.splitlines() if l.strip().startswith("I:")]
    return float(lines[-1].split()[1])


def text_png(title, path):
    """Render one title card as a transparent 1080x1920 PNG.

    White DM Sans over a soft, blurred dark halo so it stays legible on bright metal.
    """
    glyphs = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(glyphs)
    y = title["y"]
    first = True
    for text, weight, size, track in title["lines"]:
        font = ImageFont.truetype(str(FONTS / f"DMSans-{weight}.ttf"), size)
        spacing = size * track
        glyph_w = [d.textlength(ch, font=font) for ch in text]
        total = sum(glyph_w) + spacing * (len(text) - 1)
        x = (W - total) / 2
        for ch, gw in zip(text, glyph_w):
            d.text((x, y), ch, font=font, fill=(255, 255, 255, 255))
            x += gw + spacing
        y += int(size * 1.45)
        if title.get("rule") and first:
            # thin hairline between brand name and claim
            d.line([(W / 2 - 60, y - 6), (W / 2 + 60, y - 6)], fill=(255, 255, 255, 170), width=2)
            y += 18
        first = False
    alpha = glyphs.split()[3]
    halo = alpha.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(14))
    halo = halo.point(lambda v: int(v * 0.55))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    img.putalpha(halo)
    img.alpha_composite(glyphs)
    img.save(path)


def main(clips, out):
    clips = Path(clips)
    out = Path(out)
    work = out.parent / (out.stem + "_work")
    work.mkdir(parents=True, exist_ok=True)

    # 1) Normalise every cut to 1080x1920 @ 30 fps with a stereo track.
    seg_files = []
    t = 0.0
    timeline = []
    for i, (clip, a, b) in enumerate(CUTS):
        dur = b - a
        seg = work / f"seg{i}.mp4"
        if clip is None:
            run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                 "-f", "lavfi", "-i", f"color=black:s={W}x{H}:r={FPS}:d={dur}",
                 "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                 "-t", f"{dur}", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p",
                 "-c:a", "pcm_s16le", str(seg.with_suffix(".mov"))])
        else:
            src = clips / clip
            has_audio = i in AUDIO
            vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
                  f"crop={W}:{H},fps={FPS},setsar=1")
            cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                   "-ss", f"{a}", "-t", f"{dur}", "-i", str(src)]
            if has_audio:
                # Static gain to the target loudness (no dynamic loudnorm: it would pump the impact).
                gain = AUDIO[i] - measure_lufs(src, a, dur)
                af = (f"aresample=48000,aformat=channel_layouts=stereo,"
                      f"volume={gain:.2f}dB,"
                      f"apad,atrim=0:{dur},afade=t=in:d=0.01,afade=t=out:st={dur-0.02}:d=0.02")
                cmd += ["-vf", vf, "-af", af]
            else:
                cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                        "-map", "0:v", "-map", "1:a", "-vf", vf]
            cmd += ["-t", f"{dur}", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p",
                    "-c:a", "pcm_s16le", str(seg.with_suffix(".mov"))]
            run(cmd)
        seg_files.append(seg.with_suffix(".mov"))
        timeline.append({"cut": i, "clip": clip, "in": a, "out": b, "start": round(t, 3), "end": round(t + dur, 3)})
        t += dur
    total = t

    # 2) Concatenate the cuts (hard cuts only).
    lst = work / "concat.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in seg_files))
    joined = work / "joined.mov"
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", str(lst), "-c", "copy", str(joined)])

    # 3) Titles, one shared cold-steel grade and fine grain, final audio limiter.
    inputs = ["-i", str(joined)]
    for k, title in enumerate(TITLES):
        png = work / f"title{k}.png"
        text_png(title, png)
        inputs += ["-loop", "1", "-t", f"{total}", "-i", str(png)]
    grade = ("colorbalance=rs=-0.03:bs=0.04:rm=-0.02:bm=0.03:rh=-0.01:bh=0.02,"
             "eq=saturation=0.82:contrast=1.04,"
             "noise=alls=3:allf=t")
    fc = [f"[0:v]{grade}[g0]"]
    last = "g0"
    for k, title in enumerate(TITLES):
        t0, t1 = title["t0"], min(title["t1"], total)
        fo = t1 - FADE_OUT
        fade = f"fade=t=in:st={t0}:d={FADE_IN}:alpha=1"
        if title["t1"] < total:
            fade += f",fade=t=out:st={fo}:d={FADE_OUT}:alpha=1"
        fc.append(f"[{k+1}:v]format=rgba,{fade}[t{k}]")
        fc.append(f"[{last}][t{k}]overlay=0:0:enable='between(t,{t0},{t1})'[o{k}]")
        last = f"o{k}"
    fc.append(f"[{last}]format=yuv420p[v]")
    fc.append("[0:a]highpass=f=24,alimiter=limit=0.74:level=false,"
              f"apad,atrim=0:{total + 0.12}[a]")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
         "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
         "-t", f"{total}", "-r", str(FPS),
         "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-tune", "grain", "-profile:v", "high", "-maxrate", "14M", "-bufsize", "28M",
         "-movflags", "+faststart", "-c:a", "aac", "-b:a", "256k", str(out)])

    meta = {"duration": total, "fps": FPS, "size": [W, H], "cuts": timeline, "titles": TITLES}
    out.with_suffix(".timeline.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"wrote {out} ({total:.2f} s)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
