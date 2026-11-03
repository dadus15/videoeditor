#!/usr/bin/env python3
"""Brand textures for the CGI wheel and the 2D cards.

Writes into work/tex/:
  logo_clean.png   Turismo mark + wordmark from the end card, re-inked navy/red on alpha (2.6x)
  mark_clean.png   the GT mark only
  cap.png          centre-cap face: dark satin cap, GT mark in silver with the red square, TURISMO under it
  lip_text.png     a 4096x128 strip that wraps around the outer lip: "TURISMO  ·  INVENTA" twice, engraved look
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "work" / "tex"
CARD = ROOT / "assets" / "brand" / "turismo_end_card_gemini.jpg"
FONT = ROOT / "assets" / "fonts"
NAVY = np.array([0x0A, 0x1B, 0x2B], np.float32) / 255
RED = np.array([0xC7, 0x22, 0x2A], np.float32) / 255


def clean(box, scale=2.6):
    img = Image.open(CARD).convert("RGB").crop(box)
    img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    a = np.asarray(img).astype(np.float32) / 255
    is_red = (a[..., 0] - a[..., 2]) > 0.25
    ink = np.where(is_red[..., None], RED, NAVY)
    dist = np.linalg.norm(1 - a, axis=2) / np.linalg.norm(1 - ink, axis=2)
    alpha = np.clip((dist - 0.22) / 0.5, 0, 1)
    alpha = alpha * alpha * (3 - 2 * alpha)
    alpha = cv2.GaussianBlur(alpha, (0, 0), 0.6)
    return np.dstack([ink, alpha]).astype(np.float32), is_red


def save(arr, name):
    Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), "RGBA").save(OUT / name)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    logo, _ = clean((190, 70, 600, 312))
    save(logo, "logo_clean.png")
    mark, red = clean((265, 75, 530, 215), 3.0)
    save(mark, "mark_clean.png")

    # centre cap, 1024 px square (the cap's top face maps to the inscribed circle)
    S = 1024
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    r = np.hypot(xx - S / 2, yy - S / 2) / (S / 2)
    base = np.full((S, S, 3), 0.035, np.float32)
    base += (0.03 * (1 - r))[..., None]                      # soft dome highlight baked very lightly
    ring = np.clip(1 - np.abs(r - 0.93) / 0.025, 0, 1)        # thin machined ring
    base += ring[..., None] * 0.35
    m = np.asarray(Image.fromarray((mark * 255).astype(np.uint8), "RGBA").resize((560, int(560 * mark.shape[0] / mark.shape[1])), Image.LANCZOS)).astype(np.float32) / 255
    mh, mw = m.shape[:2]
    y0, x0 = int(S * 0.40 - mh / 2), (S - mw) // 2
    red_m = (m[..., 0] - m[..., 2]) > 0.25
    silver = np.array([0.80, 0.81, 0.83], np.float32)
    col = np.where(red_m[..., None], RED, silver)
    a = m[..., 3:4]
    base[y0:y0 + mh, x0:x0 + mw] = base[y0:y0 + mh, x0:x0 + mw] * (1 - a) + col * a
    im = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(str(FONT / "Archivo-Exp-800.ttf"), 92)
    txt = "TURISMO"
    w = d.textlength(txt, font=f) + 14 * (len(txt) - 1)
    x = (S - w) / 2
    for ch in txt:
        d.text((x, S * 0.62), ch, font=f, fill=(205, 207, 212))
        x += d.textlength(ch, font=f) + 14
    im.save(OUT / "cap.png")

    # lip engraving strip: U = angle (0..1 around the wheel), V = radius across the lip face
    LW, LH = 4096, 128
    strip = Image.new("L", (LW, LH), 0)
    d = ImageDraw.Draw(strip)
    f = ImageFont.truetype(str(FONT / "Archivo-Exp-800.ttf"), 70)
    # U runs clockwise from 3 o'clock (U=0.5); top = 0.25, bottom = 0.75. Words in the lower half are
    # turned 180 degrees so they read upright from below, like the lettering on a real lip.
    for cu, txt, flip in [(0.25, "TURISMO", False), (0.5, "INVENTA", False), (0.75, "TURISMO", True)]:
        sp = 22
        w = int(d.textlength(txt, font=f) + sp * (len(txt) - 1)) + 8
        word = Image.new("L", (w, LH), 0)
        dw = ImageDraw.Draw(word)
        x = 4
        for ch in txt:
            dw.text((x, 24), ch, font=f, fill=255)
            x += dw.textlength(ch, font=f) + sp
        if flip:
            word = word.rotate(180)
        strip.paste(word, (int(LW * cu - w / 2), 0))
    strip.save(OUT / "lip_text.png")
    print("textures ->", OUT)


if __name__ == "__main__":
    sys.exit(main())
