#!/usr/bin/env python3
"""Wrap a rendered film (from compose.py) with the Turismo brand bookends.

  intro : white card, Turismo logo eases in, "UNLOCK YOUR STYLE" masked reveal,
          then a push-slide to the left into the film (matches the opener's leftward camera move)
  outro : the film's closing push into the front wheel opens through a circular iris centred on that
          wheel into the end card (zooming through the card's hub, 2.2x -> 1x), one light sweep, hold

Usage:
  python3 scripts/bookends.py edit/edl_hero.json work/film_hero.mp4 renders/out.mp4 [--audio mix.wav]
"""
import argparse, json, math, subprocess, sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compose as C  # noqa: E402

ROOT = C.ROOT
NAVY = np.array([10, 27, 43], np.float32) / 255
RED = np.array([199, 34, 42], np.float32) / 255
W, H, FPS = 1080, 1920, 25

INTRO_HOLD = 1.90      # logo card before the slide starts
SLIDE = 0.56           # push-slide into the film
IRIS_LEAD = 0.45       # iris starts this long before the film's last frame
IRIS = 0.80
CARD_HOLD = 2.70       # end card after the iris completes

CARD = ROOT / "assets/brand/turismo_end_card_gemini.jpg"
CARD_WHEEL = (383.0, 633.5, 262.0)   # wheel centre x, y and rim radius in the 768x1376 card
LOGO_BOX = (190, 70, 600, 312)       # logo + wordmark region inside the card (sharper than the 280px logo file)
FILM_HUB = (200.0, 235.0)            # hero front-wheel hub (source px) at the film's last frame
FILM_RIM = 22.0                      # its rim radius in source px


def ease(name, t):
    return C.EASE[name](C.clamp01(t))


# ------------------------------------------------------------------ assets

def clean_logo(scale=2.6):
    """Logo from the card, upscaled and re-inked in the two brand colours on a transparent matte."""
    img = Image.open(CARD).convert("RGB").crop(LOGO_BOX)
    img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    a = np.asarray(img).astype(np.float32) / 255
    is_red = (a[..., 0] - a[..., 2]) > 0.25
    ink = np.where(is_red[..., None], RED, NAVY)
    dist = np.linalg.norm(1 - a, axis=2) / np.linalg.norm(1 - ink, axis=2)
    alpha = np.clip((dist - 0.22) / 0.5, 0, 1)
    alpha = alpha * alpha * (3 - 2 * alpha)          # crisp, anti-aliased edges; drops JPEG noise
    alpha = cv2.GaussianBlur(alpha, (0, 0), 0.6)
    return np.dstack([ink, alpha]).astype(np.float32)


def text_rgba(text, weight, size, track, color):
    arr = C.render_text(text, weight, size, track)
    arr[..., :3] = color
    return arr


def card_canvas():
    card = np.asarray(Image.open(CARD).convert("RGB")).astype(np.float32) / 255
    s = max(W / card.shape[1], H / card.shape[0])
    big = cv2.resize(card, (round(card.shape[1] * s), round(card.shape[0] * s)), interpolation=cv2.INTER_LANCZOS4)
    oy, ox = (big.shape[0] - H) // 2, (big.shape[1] - W) // 2
    cx, cy, r = CARD_WHEEL
    return np.clip(big[oy:oy + H, ox:ox + W], 0, 1), (cx * s - ox, cy * s - oy, r * s)


def warp_scale(img, s, center_src, center_dst, fill=1.0):
    M = np.float32([[s, 0, center_dst[0] - s * center_src[0]], [0, s, center_dst[1] - s * center_src[1]]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                          borderValue=(fill, fill, fill))


# ------------------------------------------------------------------ film geometry

def film_hub_on_screen(edl):
    """Where the hero front-wheel hub sits on screen in the film's last frame (and its rim radius)."""
    shots, total, _ = C.build_timeline(edl, edl["bpm"])
    last = shots[-1]
    T = (round(total * edl["fps"]) - 1) / edl["fps"]
    Wr, (x0, y0, cw, ch) = C.frame_geometry(last, T, edl["layout"], last["src_in"] + last["dur"])
    k = Wr[2] / cw
    return (Wr[0] + (FILM_HUB[0] - x0) * k, Wr[1] + (FILM_HUB[1] - y0) * k, FILM_RIM * k), total


def read_frames(path):
    cmd = ["ffmpeg", "-v", "error", "-i", str(path), "-vf",
           "scale=in_color_matrix=bt709:in_range=tv,format=rgb24", "-f", "rawvideo", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n = W * H * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.float32) / 255
    p.wait()


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edl")
    ap.add_argument("film")
    ap.add_argument("out")
    ap.add_argument("--audio")
    ap.add_argument("--bpm", type=float, help="must match the bpm the film was rendered at")
    ap.add_argument("--preview-every", type=int, default=0)
    ap.add_argument("--preview-dir", default="work/preview_bookends")
    args = ap.parse_args()

    edl = json.loads(Path(args.edl).read_text())
    if args.bpm:
        edl["bpm"] = args.bpm
    (hx, hy, hr), film_len = film_hub_on_screen(edl)
    film_n = round(film_len * FPS)
    film_start = INTRO_HOLD                                  # film frame 0 enters with the slide
    iris_start = film_start + film_len - IRIS_LEAD
    total = iris_start + IRIS + CARD_HOLD
    nframes = round(total * FPS)
    print(f"intro {INTRO_HOLD + SLIDE:.2f}s  film {film_start:.2f}-{film_start + film_len:.2f}  "
          f"iris {iris_start:.2f}  total {total:.2f}s  hub@({hx:.0f},{hy:.0f}) r{hr:.0f}", file=sys.stderr)

    logo = clean_logo()
    lw = 640
    logo = cv2.resize(logo, (lw, round(logo.shape[0] * lw / logo.shape[1])), interpolation=cv2.INTER_AREA)
    t_unlock = text_rgba("UNLOCK YOUR ", 700, 66, 0.16, NAVY)
    t_style = text_rgba("STYLE", 700, 66, 0.16, RED)
    card, (ccx, ccy, cr) = card_canvas()
    white = np.ones((H, W, 3), np.float32)

    def intro_frame(t):
        img = white.copy()
        # logo: fade + settle from 94 %, ease-out, already visible on frame 1
        k = ease("out_cubic", (t + 0.12) / 0.62)
        s = 0.94 + 0.06 * k
        lg = cv2.resize(logo, (round(logo.shape[1] * s), round(logo.shape[0] * s)), interpolation=cv2.INTER_AREA)
        C.blit(img, lg, W / 2 - lg.shape[1] / 2, 700 - lg.shape[0] / 2, k)
        # UNLOCK YOUR STYLE: one line rising out of a mask, STYLE lands a beat later
        y = 1080
        total_w = t_unlock.shape[1] + t_style.shape[1] - 8
        x = W / 2 - total_w / 2
        hh = t_unlock.shape[0]
        clip = (0, int(y - hh / 2 + 2), W, int(y + hh / 2 - 2))
        m1 = ease("out_cubic", (t - 0.45) / 0.6)
        m2 = ease("out_cubic", (t - 0.72) / 0.6)
        C.blit(img, t_unlock, x, y - hh / 2 + (1 - m1) * hh, m1, clip=clip)
        C.blit(img, t_style, x + t_unlock.shape[1] - 8, y - hh / 2 + (1 - m2) * hh, m2, clip=clip)
        # thin red rule draws in under the line
        rw = int(round(96 * ease("out_cubic", (t - 0.95) / 0.5)))
        if rw > 0:
            img[y + 62:y + 65, W // 2 - rw // 2:W // 2 - rw // 2 + rw] = RED
        return img

    film = read_frames(args.film)
    film_frame, film_i = None, -1

    def get_film(i):
        nonlocal film_frame, film_i
        i = min(i, film_n - 1)
        while film_i < i:
            nxt = next(film, None)
            if nxt is None:
                break
            film_frame, film_i = nxt, film_i + 1
        return film_frame

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-"]
    if args.audio:
        cmd += ["-i", args.audio]
    cmd += ["-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p", "-c:v", "libx264", "-preset", "slow",
            "-crf", "18", "-profile:v", "high", "-colorspace", "bt709", "-color_primaries", "bt709",
            "-color_trc", "bt709", "-color_range", "tv", "-movflags", "+faststart"]
    cmd += (["-c:a", "aac", "-b:a", "256k", "-shortest"] if args.audio else ["-an"]) + [str(out)]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    pdir = Path(args.preview_dir)
    if args.preview_every:
        pdir.mkdir(parents=True, exist_ok=True)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

    for f in range(nframes):
        t = f / FPS
        if t < film_start:                                   # logo card
            img = intro_frame(t)
        elif t < film_start + SLIDE:                         # push-slide left into the film
            k = ease("in_out_cubic", (t - film_start) / SLIDE)
            dx = int(round(k * W))
            card_img = intro_frame(t)
            fr = get_film(f - round(film_start * FPS))
            img = np.empty_like(card_img)
            img[:, :W - dx] = card_img[:, dx:]
            img[:, W - dx:] = fr[:, :dx]
        elif t < iris_start:
            img = get_film(f - round(film_start * FPS))
        else:                                                # iris from the car's wheel into the end card
            fr = get_film(f - round(film_start * FPS))
            u = (t - iris_start) / IRIS
            k = ease("in_out_cubic", u)
            sc = 2.2 ** (1 - ease("out_cubic", u))           # zoom through the hub: card settles from 2.2x to 1x
            cxy = (C.lerp(hx, ccx, k), C.lerp(hy, ccy, k))
            cimg = warp_scale(card, sc, (ccx, ccy), cxy) if abs(sc - 1) > 1e-3 else card
            r0, r1 = hr * 1.04, math.hypot(W, H)
            R = r0 * (r1 / r0) ** k
            d = np.sqrt((xx - cxy[0]) ** 2 + (yy - cxy[1]) ** 2)
            m = np.clip((R - d) / 6.0 + 0.5, 0, 1)[..., None]
            img = fr * (1 - m) + cimg * m
            if u >= 1:                                       # hold: slow push + one light sweep over the wheel
                h = t - iris_start - IRIS
                z = 1 + 0.025 * ease("in_out_sine", h / CARD_HOLD)
                img = warp_scale(card, z, (ccx, ccy), (ccx, ccy))
                p = ease("in_out_sine", (h - 0.25) / 1.1)
                if 0 < p < 1:
                    band = (xx + 0.55 * yy) - (-600 + p * (W + 0.55 * H + 1200))
                    glow = np.exp(-(band / 70) ** 2) * 0.55
                    glow *= np.exp(-((np.hypot(xx - ccx, yy - ccy) - cr * 0.6) / (cr * 0.55)) ** 2)
                    img = 1 - (1 - img) * (1 - glow[..., None])  # screen blend: lifts the dark spokes only
        rgb = (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
        enc.stdin.write(rgb.tobytes())
        if args.preview_every and f % args.preview_every == 0:
            cv2.imwrite(str(pdir / f"b{f:04d}_{t:06.2f}.jpg"), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    enc.stdin.close()
    enc.wait()

    tl = json.loads(Path(args.film).with_suffix(".timeline.json").read_text())
    off = film_start
    for s in tl["shots"]:
        s["start"] += off
        s["end"] += off
    tl["shots"].insert(0, {"name": "turismo_logo_unlock_your_style", "start": 0.0, "end": film_start + SLIDE, "src_in": None})
    tl["duration"] = total
    tl["cue_points"] = {"open_impact": 0.0, "style_word": 0.72, "slide_into_film": film_start,
                        "riser_end_reveal": off + tl["cue_points"]["riser_end_reveal"],
                        "signature": off + tl["cue_points"]["signature"],
                        "end_card_iris": iris_start, "end": total}
    tl["shimmer_at"] = tl["shots"][2]["start"]  # TURISMO lettering shot
    json.dump(tl, open(out.with_suffix(".timeline.json"), "w"), indent=2)
    print(f"wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
