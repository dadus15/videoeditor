#!/usr/bin/env python3
"""Composite the Turismo Inventa promo: studio white, CGI shots, title and end cards, fades.

The cut is a frame-for-frame re-build of the Vossen "Hybrid Forged Series" reference (34.72 s at 25 fps):
title card -> line-up whip -> detail act -> barrel macro -> ghost hub -> finish montage A -> dark hero
-> montage B -> bronze hero -> whip into the cap -> "AVAILABLE IN / 6 EXCLUSIVE FINISHES".

    python3 cgi/post.py --res 720 --out work/film_720.mp4
    python3 cgi/post.py --res 216 --out work/previz.mp4 --size 960x540      # quick previz

Writes <out> (no audio) and <out>.timeline.json with the cut points for the sound design.
"""
import argparse
import json
import math
import random
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "assets" / "fonts"
TEX = ROOT / "work" / "tex"
FPS = 25
N_FRAMES = 868                     # 34.72 s, the length of the reference

NAVY = (10, 27, 43)                # Turismo primary ink, used for the title bars
RED = (199, 34, 42)                # Turismo accent, used for the labels
INK = (40, 42, 46)                 # brackets and the small mark

COPY = {
    "title_label": "TURISMO FORGED · C19R",
    "title_words": [("UNLOCK", "solid"), ("YOUR", "outline"), ("STYLE", "solid")],
    "end_label": "AVAILABLE IN",
    "end_words": [("6 EXCLUSIVE ", "solid"), ("FINISHES", "outline")],
}

# (start frame, end frame exclusive, source, source frame offset)
TIMELINE = [
    (0, 64, "TITLE", 0),
    (64, 120, "S02", 0), (120, 154, "S03", 0), (154, 169, "S04", 0), (169, 189, "S05", 0),
    (189, 194, "S06", 0), (194, 213, "S07", 0), (213, 264, "S08", 0), (264, 370, "S09", 0),
    (370, 416, "S10", 0),
    # montage A
    (416, 420, "A1", 0), (420, 422, "A2", 0), (422, 426, "A3", 0), (426, 438, "A4", 0), (438, 446, "A5", 0),
    (446, 464, "A6", 0), (464, 471, "A7", 0), (471, 477, "A8", 0), (477, 483, "A9", 0), (483, 490, "A10", 0),
    (490, 502, "A11", 0), (502, 505, "A1", 0), (505, 507, "A2", 0), (507, 510, "A3", 0), (510, 512, "A12", 0),
    (512, 515, "A8", 3),
    (515, 615, "S11", 0),
    # montage B
    (615, 618, "A1", 0), (618, 620, "A2", 0), (620, 623, "A3", 0), (623, 625, "A12", 0), (625, 638, "B5", 0),
    (638, 645, "A5", 8), (645, 663, "B7", 0), (663, 670, "A7", 0), (670, 675, "A8", 0), (675, 682, "A9", 0),
    (682, 689, "A10", 0), (689, 702, "B12", 0),
    (702, 705, "A1", 0), (705, 707, "A2", 0), (707, 710, "A3", 0), (710, 712, "A12", 0), (712, 714, "A8", 0),
    (714, 818, "S12", 0), (818, 826, "S13", 0),
    (826, N_FRAMES, "END", 0),
]

# cut points that carry a hit in the sound design (seconds) and the whooshes/risers
SFX_CUES = {
    "impact": [2.56, 10.56, 16.64, 24.60, 28.56, 33.04],
    "whoosh": [2.50, 6.12, 8.28, 13.70, 32.70],
    "tick": [],          # filled with every montage cut
    "swell": [(4.80, 5.50), (14.80, 16.64), (22.80, 24.40)],
}


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def ease_out(t, p=3):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** p


def ramp(t, a, b):
    return smooth((t - a) / (b - a))


def opacity(src, t):
    """Wheel-layer opacity over the studio white (1 = fully visible). t in seconds."""
    if src == "S02":
        return 1 - ramp(t, 4.00, 4.60)
    if src == "S03":
        return ramp(t, 4.80, 5.50)
    if src == "S08":
        return 1 - ramp(t, 9.40, 10.40)
    if src == "S09":
        return 1 - ramp(t, 13.98, 14.30)
    if src == "S10":
        return 0.55 * ramp(t, 14.80, 16.64) ** 0.8
    if src == "S11":
        return 1 - ramp(t, 22.80, 24.40)
    if src == "A12":
        return 0.38
    return 1.0


class Frames:
    def __init__(self, res, size):
        self.dir = ROOT / "work" / "cgi" / str(res)
        self.size = size
        self.cache = {}

    def get(self, shot, i):
        key = (shot, i)
        if key not in self.cache:
            files = sorted((self.dir / shot).glob("f*.png"))
            if not files:
                raise SystemExit(f"missing renders for {shot} in {self.dir}")
            p = files[min(i, len(files) - 1)]
            im = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
            im = cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA).astype(np.float32) / 255
            if im.shape[1] != self.size[0]:
                im = cv2.resize(im, self.size, interpolation=cv2.INTER_LANCZOS4)
                im = np.clip(im, 0, 1)
            if len(self.cache) > 40:
                self.cache.pop(next(iter(self.cache)))
            self.cache[key] = im
        return self.cache[key]


# ------------------------------------------------------------------------------------- studio white

def studio_bg(w, h):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx, ny = (xx - w * 0.5) / (w * 0.5), (yy - h * 0.46) / (h * 0.5)
    r = np.sqrt(nx ** 2 * 0.75 + ny ** 2)
    centre = np.array([238, 238, 236], np.float32) / 255
    edge = np.array([205, 206, 205], np.float32) / 255
    k = np.clip(r / 1.35, 0, 1) ** 1.7
    return centre * (1 - k[..., None]) + edge * k[..., None]


# ------------------------------------------------------------------------------------------ titles

# Orbitron (OFL): the closest open match to the wide, rounded-rectangle TURISMO wordmark
FONT_MAP = {900: "Orbitron-900.ttf", 800: "Orbitron-700.ttf", 600: "Orbitron-500.ttf"}


def font(weight, size):
    return ImageFont.truetype(str(FONTS / FONT_MAP[weight]), size)


class TitleCard:
    """Red label over a navy bar of words (solid / outline), corner brackets, a small mark under the bar.
    Animated like the reference: the bar wipes open from the centre, characters type on behind a block
    cursor, a few dark glitch blocks flicker, then everything holds."""

    def __init__(self, w, h, label, words, cy, seed):
        self.w, self.h = w, h
        s = h / 1080
        self.s = s
        self.f_big = font(900, int(78 * s))
        self.f_lab = font(800, int(25 * s))
        self.f_small = font(600, int(13 * s))
        self.track_big = int(1 * s)
        self.track_lab = int(9 * s)
        self.label, self.words = label, words
        self.mark = Image.open(TEX / "logo_clean.png").convert("RGBA")
        self.rng = random.Random(seed)
        # measure the bar
        pad = int(16 * s)
        self.chars = []                      # (char, style, x)
        x = 0
        d = ImageDraw.Draw(Image.new("L", (10, 10)))
        for word, style in words:
            for ch in word:
                self.chars.append((ch, style, x))
                x += d.textlength(ch, font=self.f_big) + self.track_big
        self.text_w = x - self.track_big
        self.bar_h = int(86 * s)
        self.bar_w = int(self.text_w + 2 * pad)
        self.bx0 = (w - self.bar_w) // 2
        self.by0 = int(cy - self.bar_h / 2)
        self.pad = pad
        lab_w = sum((13 * s if c == "\u00b7" else d.textlength(c, font=self.f_lab)) + self.track_lab
                    for c in label) - self.track_lab
        self.lab_w = int(lab_w + 2 * 14 * s)
        self.lab_h = int(36 * s)
        self.lx0 = (w - self.lab_w) // 2
        self.ly0 = self.by0 - self.lab_h - int(6 * s)
        asc, desc = self.f_big.getmetrics()
        bb = self.f_big.getbbox("H")
        self.ty = self.by0 + (self.bar_h - (bb[3] - bb[1])) // 2 - bb[1]
        lb = self.f_lab.getbbox("H")
        self.lty = self.ly0 + (self.lab_h - (lb[3] - lb[1])) // 2 - lb[1]
        # glitch blocks: (t0, t1, x, y, w, h)
        self.glitch = []
        for _ in range(7):
            t0 = self.rng.uniform(0.05, 0.95)
            gw, gh = self.rng.randint(30, 90) * s, self.rng.randint(14, 30) * s
            gx = self.rng.uniform(self.bx0 + self.bar_w * 0.15, self.bx0 + self.bar_w * 0.9)
            gy = self.rng.choice([self.by0 + self.bar_h + 2 * s, self.by0 - gh - 2 * s, self.by0 + self.bar_h * 0.55])
            self.glitch.append((t0, t0 + self.rng.choice([0.08, 0.12, 0.16]), gx, gy, gw, gh))

    def draw(self, t, img=None, settle=1.25):
        """t: seconds since the card started. Returns RGBA float array."""
        s = self.s
        im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        # bar wipes open from the centre
        k = ease_out(t / 0.32, 3)
        if k > 0:
            half = self.bar_w * k / 2
            cx = self.bx0 + self.bar_w / 2
            d.rectangle([cx - half, self.by0, cx + half, self.by0 + self.bar_h], fill=NAVY + (255,))
        # characters type on
        n = len(self.chars)
        t_chars = (t - 0.30) / (settle - 0.30 - 0.10)
        shown = int(np.clip(t_chars, 0, 1) * n + 0.0001)
        for i, (ch, style, x) in enumerate(self.chars):
            px = self.bx0 + self.pad + x
            if i < shown:
                if style == "solid":
                    d.text((px, self.ty), ch, font=self.f_big, fill=(244, 244, 242, 255))
                else:
                    d.text((px, self.ty), ch, font=self.f_big, fill=NAVY + (255,),
                           stroke_width=max(1, round(2.2 * s)), stroke_fill=(232, 238, 248, 255))
            elif i == shown and t_chars < 1 and k >= 1:
                cw = self.f_big.getlength(ch)
                d.rectangle([px, self.ty + self.f_big.getbbox("H")[1] - 2 * s, px + cw,
                             self.ty + self.f_big.getbbox("H")[3] + 2 * s], fill=(244, 244, 242, 255))
        # label: red box grows from the left, letters follow
        kl = ease_out((t - 0.18) / 0.30, 3)
        if kl > 0:
            d.rectangle([self.lx0, self.ly0, self.lx0 + self.lab_w * kl, self.ly0 + self.lab_h], fill=RED + (255,))
            nl = int(np.clip((t - 0.30) / 0.55, 0, 1) * len(self.label))
            x = self.lx0 + 14 * s
            for i, c in enumerate(self.label):
                if c == "\u00b7":                     # Orbitron has no middle dot: draw a small square
                    sq = 5 * s
                    cy = self.ly0 + self.lab_h / 2
                    if i < nl:
                        d.rectangle([x + 4 * s, cy - sq / 2, x + 4 * s + sq, cy + sq / 2], fill=(255, 255, 255, 255))
                    x += 13 * s + self.track_lab
                    continue
                if i < nl:
                    d.text((x, self.lty), c, font=self.f_lab, fill=(255, 255, 255, 255))
                x += d.textlength(c, font=self.f_lab) + self.track_lab
        # corner brackets
        kb = ease_out((t - 0.25) / 0.3)
        if kb > 0:
            g, L, lw = 12 * s, 26 * s * kb, max(1, int(2 * s))
            xr, yt = self.bx0 + self.bar_w + g, self.by0 - g
            d.line([xr - L, yt, xr, yt], fill=INK + (255,), width=lw)
            d.line([xr, yt, xr, yt + L], fill=INK + (255,), width=lw)
            xl, yb = self.bx0 - g, self.by0 + self.bar_h + g
            d.line([xl, yb, xl + L, yb], fill=INK + (255,), width=lw)
            d.line([xl, yb, xl, yb - L], fill=INK + (255,), width=lw)
            # small Turismo mark + wordmark under the bar's right end (from the logo artwork)
            mw = int(84 * s)
            mk = self.mark.resize((mw, int(mw * self.mark.height / self.mark.width)), Image.LANCZOS)
            if kb < 1:
                mk.putalpha(mk.getchannel("A").point(lambda v: int(v * kb)))
            im.alpha_composite(mk, (int(self.bx0 + self.bar_w - mw), int(self.by0 + self.bar_h + 5 * s)))
        # glitch blocks
        for t0, t1, gx, gy, gw, gh in self.glitch:
            if t0 <= t < t1 and t < settle:
                d.rectangle([gx, gy, gx + gw, gy + gh], fill=(16, 16, 18, 255))
        return np.asarray(im).astype(np.float32) / 255


def over(base, layer, alpha_mul=1.0):
    a = layer[..., 3:4] * alpha_mul
    return base * (1 - a) + layer[..., :3] * a


# --------------------------------------------------------------------------------------- end card

def line_art(frames, w, h):
    """Faint blue line drawing of the wheel for the end card (edges of the LINE render)."""
    src = frames.get("LINE", 0)
    rgb = src[..., :3] * src[..., 3:4] + (1 - src[..., 3:4])
    g = (cv2.cvtColor((rgb * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY))
    g = cv2.GaussianBlur(g, (0, 0), 1.0 * h / 1080)
    e = cv2.Canny(g, 18, 48).astype(np.float32) / 255
    e = cv2.dilate(e, np.ones((2, 2), np.uint8))
    e = cv2.GaussianBlur(e, (0, 0), 1.1 * h / 1080)
    e = np.clip(e * 1.6, 0, 1)
    # scale up and park it high, cropped by the top edge, like the reference
    sc = 1.55
    big = cv2.resize(e, (int(w * sc), int(h * sc)), interpolation=cv2.INTER_CUBIC)
    out = np.zeros((h, w), np.float32)
    ox, oy = int(w * 0.47 - big.shape[1] * 0.5), int(h * 0.20 - big.shape[0] * 0.5)
    xs0, ys0 = max(0, -ox), max(0, -oy)
    xd0, yd0 = max(0, ox), max(0, oy)
    cw, ch = min(w - xd0, big.shape[1] - xs0), min(h - yd0, big.shape[0] - ys0)
    out[yd0:yd0 + ch, xd0:xd0 + cw] = big[ys0:ys0 + ch, xs0:xs0 + cw]
    col = np.array([150, 172, 214], np.float32) / 255
    return np.dstack([np.broadcast_to(col, (h, w, 3)), out * 0.30])


# ------------------------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", type=int, default=720, help="which CGI render set to use (work/cgi/<res>)")
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--out", default="work/film.mp4")
    ap.add_argument("--crf", type=int, default=14)
    ap.add_argument("--frames", default="", help="a:b frame range for tests")
    ap.add_argument("--timeline-only", action="store_true")
    args = ap.parse_args()
    if args.timeline_only:
        write_timeline(ROOT / args.out)
        return
    w, h = map(int, args.size.split("x"))
    fr = Frames(args.res, (w, h))
    bg = studio_bg(w, h)
    title = TitleCard(w, h, COPY["title_label"], COPY["title_words"], h * 0.505, seed=7)
    endc = TitleCard(w, h, COPY["end_label"], COPY["end_words"], h * 0.585, seed=11)
    try:
        art = line_art(fr, w, h)
    except SystemExit:
        art = np.zeros((h, w, 4), np.float32)
    rng = np.random.default_rng(3)
    grain = [rng.normal(0, 1, (h, w)).astype(np.float32) for _ in range(4)]

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    a, b = (map(int, args.frames.split(":")) if args.frames else (0, N_FRAMES))
    ff = subprocess.Popen([
        "ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(FPS),
        "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
        "-c:v", "libx264", "-preset", "slow", "-crf", str(args.crf), "-tune", "film",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart",
        str(out)], stdin=subprocess.PIPE)

    seg_of = {}
    for s0, s1, src, off in TIMELINE:
        for f in range(s0, s1):
            seg_of[f] = (s0, src, off)

    for f in range(a, b):
        t = f / FPS
        s0, src, off = seg_of[f]
        if src == "TITLE":
            img = over(bg, title.draw(t))
        elif src == "END":
            te = t - s0 / FPS
            img = over(bg, art, ramp(te, 0.0, 0.45))
            img = over(img, endc.draw(te + 0.10, settle=0.62))
            flash = 1 - ramp(te, 0.0, 0.20)           # the whip lands on a bright frame
            img = img * (1 - 0.35 * flash) + 0.35 * flash
        else:
            fg = fr.get(src, f - s0 + off)
            al = fg[..., 3:4] * opacity(src, t)
            img = fg[..., :3] * al + bg * (1 - al)
            if src in ("S10", "A12"):
                img = img * 0.82 + np.array([0.165, 0.172, 0.19], np.float32)   # cool high-key ghost
            if src == "A9" and f - s0 < 2 and f > 600:  # the one dissolve in montage B (27.0 s)
                prev = fr.get("A8", 5)
                pa = prev[..., 3:4]
                pimg = prev[..., :3] * pa + bg * (1 - pa)
                k = (f - s0 + 1) / 3
                img = img * k + pimg * (1 - k)
        # gentle finishing: soft contrast, fine grain
        img = np.clip(img, 0, 1)
        img = img + (img - img * img) * 0.06
        img = img + grain[f % 4][..., None] * 0.006
        ff.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    ff.stdin.close()
    ff.wait()

    write_timeline(out)
    print("wrote", out)


def write_timeline(out):
    cuts = [dict(t=round(s0 / FPS, 3), shot=src) for s0, s1, src, off in TIMELINE]
    montage = [s0 / FPS for s0, s1, src, off in TIMELINE if src[0] in "AB" and 16.6 < s0 / FPS < 28.6]
    cues = dict(SFX_CUES)
    cues["tick"] = [round(x, 3) for x in montage]
    out.with_suffix(".timeline.json").write_text(json.dumps(dict(fps=FPS, frames=N_FRAMES, cuts=cuts, sfx=cues), indent=1))


if __name__ == "__main__":
    main()
