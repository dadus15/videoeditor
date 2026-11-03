#!/usr/bin/env python3
"""2D pieces for the AI (Higgsfield) version of the promo, rendered in one file for upload:

    frames   0-63   title card   "TURISMO WHEELS · C19R" / UNLOCK YOUR STYLE        (film 0.00-2.56)
    frames  64-67   studio white bridge                                             (film 10.40-10.56)
    frames  68-72   studio white bridge                                             (film 24.40-24.60)
    frames  73-114  end card with a line drawing of the C19R                        (film 33.04-34.72)

    python3 cgi/bookends.py work/hf/bookends.mp4 --label "TURISMO WHEELS · C19R" \
        --product assets/product/c19r_silver.png

Copy (title words, end card words) lives in post.py COPY; the label and the product render for the end-card
line drawing are arguments. Bridges are plain studio white for the gaps between AI segments.
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import post as P  # noqa: E402

W, H = 1920, 1080


def product_line_art(w, h, product):
    """Faint blue line drawing of the product from a clean render on white (silver finishes give the best edges)."""
    src = cv2.imread(str(product), cv2.IMREAD_GRAYSCALE)
    g = cv2.GaussianBlur(src, (0, 0), 1.6)
    e = cv2.Canny(g, 22, 60).astype(np.float32) / 255
    e = cv2.dilate(e, np.ones((2, 2), np.uint8))
    e = cv2.GaussianBlur(e, (0, 0), 1.2)
    side = int(h * 1.55)
    big = cv2.resize(e, (side, side), interpolation=cv2.INTER_AREA)
    out = np.zeros((h, w), np.float32)
    ox, oy = int(w * 0.47 - side / 2), int(h * 0.22 - side / 2)
    xs0, ys0 = max(0, -ox), max(0, -oy)
    xd0, yd0 = max(0, ox), max(0, oy)
    cw, ch = min(w - xd0, side - xs0), min(h - yd0, side - ys0)
    out[yd0:yd0 + ch, xd0:xd0 + cw] = big[ys0:ys0 + ch, xs0:xs0 + cw]
    col = np.array([150, 172, 214], np.float32) / 255
    return np.dstack([np.broadcast_to(col, (h, w, 3)), np.clip(out * 1.3, 0, 1) * 0.30])


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--label", default=None, help="red label over the title bar")
    ap.add_argument("--product", required=True, help="product render on white for the end-card line drawing")
    args = ap.parse_args()
    if args.label:
        P.COPY["title_label"] = args.label
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    bg = P.studio_bg(W, H)
    title = P.TitleCard(W, H, P.COPY["title_label"], P.COPY["title_words"], H * 0.505, seed=7)
    endc = P.TitleCard(W, H, P.COPY["end_label"], P.COPY["end_words"], H * 0.585, seed=11)
    art = product_line_art(W, H, args.product)
    rng = np.random.default_rng(3)
    grain = [rng.normal(0, 1, (H, W)).astype(np.float32) for _ in range(4)]
    ff = subprocess.Popen([
        "ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "25",
        "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
        "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-tune", "film", "-color_primaries", "bt709",
        "-color_trc", "bt709", "-colorspace", "bt709", str(out)], stdin=subprocess.PIPE)
    for f in range(115):
        if f < 64:
            img = P.over(bg, title.draw(f / 25))
        elif f < 73:
            img = bg.copy()
        else:
            te = (f - 73) / 25
            img = P.over(bg, art, P.ramp(te, 0.0, 0.45))
            img = P.over(img, endc.draw(te + 0.10, settle=0.62))
            flash = 1 - P.ramp(te, 0.0, 0.20)
            img = img * (1 - 0.35 * flash) + 0.35 * flash
        img = np.clip(img, 0, 1)
        img = img + (img - img * img) * 0.06 + grain[f % 4][..., None] * 0.006
        ff.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    ff.stdin.close()
    ff.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()
