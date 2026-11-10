#!/usr/bin/env python3
"""Wrap a rendered film (from compose.py) with brand bookends, configured by the EDL's "bookends" block.

  intro : white card, brand logo eases in, tagline (e.g. "UNLOCK YOUR STYLE") masked reveal,
          then a push-slide to the left into the film (matches the opener's leftward camera move)
  outro : the film's closing push into the front wheel opens through a circular iris centred on that
          wheel into the end card (zooming through the card's hub, 2.2x -> 1x), one light sweep, hold

Usage:
  python3 .claude/skills/youtube-edit/scripts/bookends.py edit/edl_hero.json work/film_hero.mp4 renders/out.mp4 [--audio mix.wav]
"""
import argparse, json, math, subprocess, sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compose as C  # noqa: E402

ROOT = C.ROOT
W, H, FPS = 1080, 1920, 25   # size and fps are replaced by the EDL's "size" and "fps" in main()

INTRO_HOLD = 1.90      # logo card before the slide starts
SLIDE = 0.56           # push-slide into the film
IRIS_LEAD = 0.45       # iris starts this long before the film's last frame
IRIS = 0.80
CARD_HOLD = 2.70       # end card after the iris completes

# Brand + geometry come from the EDL ("bookends" block, see templates/edl_automotive_example.json):
#   card        end-card image (also the logo source when it carries a sharper copy than the logo file)
#   logo_box    [x0, y0, x1, y1] of the logo + wordmark inside the card
#   card_wheel  [cx, cy, r] of the product wheel in the card (card pixels)
#   film_hub    [x, y] of the wheel hub in SOURCE pixels at the film's last frame (measure it on a render)
#   film_rim    rim radius in source pixels
#               (both unused when the film's timeline.json carries "end_hub", as compose_multi.py writes it)
#   intro       false = no logo card: the film opens on frame 1 (hook-first), the brand lands on the end card
#   outro       "iris" (default): iris from the film's wheel through the card's hub
#               "fade": a dip through white into the card (nothing is composited over the car's wheels)
#   ink         {"primary": "#0A1B2B", "accent": "#C7222A"}   sampled from the logo
#   tagline     [["UNLOCK YOUR ", "primary"], ["STYLE", "accent"]]
CFG = {}
NAVY = RED = None


def hex_rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255


def load_cfg(edl):
    global NAVY, RED
    b = edl["bookends"]
    CFG.update(card=ROOT / b["card"], logo_box=tuple(b["logo_box"]), card_wheel=tuple(b["card_wheel"]),
               film_hub=tuple(b.get("film_hub", (0, 0))), film_rim=float(b.get("film_rim", 0)),
               tagline=b.get("tagline", []), intro=b.get("intro", True), outro=b.get("outro", "iris"),
               card_box=b.get("card_box"))
    NAVY, RED = hex_rgb(b["ink"]["primary"]), hex_rgb(b["ink"]["accent"])


def ease(name, t):
    return C.EASE[name](C.clamp01(t))


# ------------------------------------------------------------------ assets

def clean_logo(scale=2.6):
    """Logo from the card, upscaled and re-inked in the two brand colours on a transparent matte."""
    img = Image.open(CFG["card"]).convert("RGB").crop(CFG["logo_box"])
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
    card = np.asarray(Image.open(CFG["card"]).convert("RGB")).astype(np.float32) / 255
    box = CFG.get("card_box")   # [x0, y0, x1, y1]: fit the card inside a safe zone (e.g. clear of TikTok's UI)
    if box or W > H:   # contain on white, sides feathered into the white
        bx0, by0, bx1, by1 = box if box else (0, 0, W, H)
        s = min((bx1 - bx0) / card.shape[1], (by1 - by0) / card.shape[0])
        sc = cv2.resize(card, (round(card.shape[1] * s), round(card.shape[0] * s)), interpolation=cv2.INTER_AREA)
        fw = max(1, int(sc.shape[1] * 0.10))
        ramp = np.ones(sc.shape[1], np.float32)
        ramp[:fw] = np.linspace(0, 1, fw) ** 1.5
        ramp[-fw:] = ramp[:fw][::-1]
        sc = 1 - (1 - sc) * ramp[None, :, None]
        fh = max(1, int(sc.shape[0] * 0.04))           # soft top/bottom edge as well
        vr = np.ones(sc.shape[0], np.float32)
        vr[:fh] = np.linspace(0, 1, fh) ** 1.5
        vr[-fh:] = vr[:fh][::-1]
        sc = 1 - (1 - sc) * vr[:, None, None]
        out = np.ones((H, W, 3), np.float32)
        ox = int(round((bx0 + bx1) / 2 - sc.shape[1] / 2))
        oy = int(round((by0 + by1) / 2 - sc.shape[0] / 2))
        out[oy:oy + sc.shape[0], ox:ox + sc.shape[1]] = sc
        cx, cy, r = CFG["card_wheel"]
        return np.clip(out, 0, 1), (cx * s + ox, cy * s + oy, r * s)
    s = max(W / card.shape[1], H / card.shape[0])
    big = cv2.resize(card, (round(card.shape[1] * s), round(card.shape[0] * s)), interpolation=cv2.INTER_LANCZOS4)
    oy, ox = (big.shape[0] - H) // 2, (big.shape[1] - W) // 2
    cx, cy, r = CFG["card_wheel"]
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
    hub, rim = CFG["film_hub"], CFG["film_rim"]
    return (Wr[0] + (hub[0] - x0) * k, Wr[1] + (hub[1] - y0) * k, rim * k), total


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
    ap.add_argument("--crf", type=int, default=18, help="x264 CRF of the output (12 = high-bitrate master)")
    ap.add_argument("--hq", action="store_true", help="slower preset, film tuning, gradient-friendly adaptive quant")
    ap.add_argument("--preview-every", type=int, default=0)
    ap.add_argument("--preview-dir", default="work/preview_bookends")
    args = ap.parse_args()

    global FPS, W, H
    edl = json.loads(Path(args.edl).read_text())
    FPS = edl.get("fps", FPS)
    W, H = edl.get("size", [W, H])
    if args.bpm:
        edl["bpm"] = args.bpm
    load_cfg(edl)
    tl_in = json.loads(Path(args.film).with_suffix(".timeline.json").read_text())
    if tl_in.get("end_hub"):                                 # measured by the compositor on the last frame
        hx, hy, hr = tl_in["end_hub"]
        film_len = tl_in["duration"]
    else:
        (hx, hy, hr), film_len = film_hub_on_screen(edl)
    film_n = round(film_len * FPS)
    film_start = INTRO_HOLD if CFG["intro"] else 0.0         # film frame 0 enters with the slide
    # fade: the dip to white finishes exactly on the film's last frame (no frozen frame under the fade)
    iris_start = film_start + film_len - (IRIS / 2 if CFG["outro"] == "fade" else IRIS_LEAD)
    total = iris_start + IRIS + CARD_HOLD
    nframes = round(total * FPS)
    print(f"intro {(INTRO_HOLD + SLIDE) if CFG['intro'] else 0:.2f}s  film {film_start:.2f}-{film_start + film_len:.2f}  "
          f"iris {iris_start:.2f}  total {total:.2f}s  hub@({hx:.0f},{hy:.0f}) r{hr:.0f}", file=sys.stderr)

    logo = clean_logo()
    land = W > H
    lw = 520 if land else 640
    logo = cv2.resize(logo, (lw, round(logo.shape[0] * lw / logo.shape[1])), interpolation=cv2.INTER_AREA)
    ink = {"primary": NAVY, "accent": RED}
    tag_parts = [text_rgba(txt, 700, 66, 0.16, ink[col]) for txt, col in CFG["tagline"]]
    card, (ccx, ccy, cr) = card_canvas()
    white = np.ones((H, W, 3), np.float32)

    def intro_frame(t):
        img = white.copy()
        # logo: fade + settle from 94 %, ease-out, already visible on frame 1
        k = ease("out_cubic", (t + 0.12) / 0.62)
        s = 0.94 + 0.06 * k
        lg = cv2.resize(logo, (round(logo.shape[1] * s), round(logo.shape[0] * s)), interpolation=cv2.INTER_AREA)
        C.blit(img, lg, W / 2 - lg.shape[1] / 2, (0.38 * H if land else 700) - lg.shape[0] / 2, k)
        # tagline: one line rising out of a mask, each part lands ~0.27 s after the previous one
        y = int(0.66 * H) if land else 1080
        if tag_parts:
            total_w = sum(p.shape[1] for p in tag_parts) - 8 * (len(tag_parts) - 1)
            x = W / 2 - total_w / 2
            hh = tag_parts[0].shape[0]
            clip = (0, int(y - hh / 2 + 2), W, int(y + hh / 2 - 2))
            for j, part in enumerate(tag_parts):
                m = ease("out_cubic", (t - 0.45 - 0.27 * j) / 0.6)
                C.blit(img, part, x, y - hh / 2 + (1 - m) * hh, m, clip=clip)
                x += part.shape[1] - 8
        # thin accent rule draws in under the line
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
            "-crf", str(args.crf), "-profile:v", "high"]
    if args.hq:   # film tuning + adaptive quantisation that protects smooth gradients (sky, paint)
        cmd += ["-preset", "slower", "-tune", "film", "-x264-params", "aq-mode=3:aq-strength=0.9"]
    cmd += [ "-colorspace", "bt709", "-color_primaries", "bt709",
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
        elif CFG["intro"] and t < film_start + SLIDE:        # push-slide left into the film
            k = ease("in_out_cubic", (t - film_start) / SLIDE)
            dx = int(round(k * W))
            card_img = intro_frame(t)
            fr = get_film(f - round(film_start * FPS))
            img = np.empty_like(card_img)
            img[:, :W - dx] = card_img[:, dx:]
            img[:, W - dx:] = fr[:, :dx]
        elif t < iris_start:
            img = get_film(f - round(film_start * FPS))
        elif CFG["outro"] == "fade":                         # cross-dissolve into the end card, then hold
            fr = get_film(f - round(film_start * FPS))
            u = (t - iris_start) / IRIS
            h = t - iris_start
            z = 1.02 - 0.02 * ease("out_cubic", h / (IRIS + CARD_HOLD))   # card settles gently
            cimg = warp_scale(card, z, (ccx, ccy), (ccx, ccy))
            if u < 0.5:                                      # dip through white: no double exposure of
                k = ease("in_out_sine", u / 0.5)             # the card's wheel over the car's wheels
                img = fr * (1 - k) + k
            elif u < 1:
                k = ease("in_out_sine", (u - 0.5) / 0.5)
                img = (1 - k) + cimg * k
            else:
                img = cimg
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
    if CFG["intro"]:
        tl["shots"].insert(0, {"name": "brand_logo_tagline", "start": 0.0, "end": film_start + SLIDE, "src_in": None})
    tl["duration"] = total
    tl["cue_points"] = {"open_impact": 0.0, "tagline_accent": 0.72 if CFG["intro"] else None,
                        "slide_into_film": film_start if CFG["intro"] else None,
                        "riser_end_reveal": (None if tl["cue_points"]["riser_end_reveal"] is None
                                             else off + tl["cue_points"]["riser_end_reveal"]),
                        "signature": off + tl["cue_points"]["signature"],
                        "end_card_iris": iris_start, "end": total}
    tl["shimmer_at"] = tl["shots"][min(2 if CFG["intro"] else 0, len(tl["shots"]) - 1)]["start"]  # a detail shot
    json.dump(tl, open(out.with_suffix(".timeline.json"), "w"), indent=2)
    print(f"wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
