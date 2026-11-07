#!/usr/bin/env python3
"""Wrap a rendered film (from compose.py) with brand bookends, configured by the EDL's "bookends" block.

  intro : white card, brand logo eases in, tagline (e.g. "UNLOCK YOUR STYLE") masked reveal,
          then a push-slide to the left into the film (matches the opener's leftward camera move)
  outro : the film's closing push into the front wheel opens through a circular iris centred on that
          wheel into the end card (zooming through the card's hub, 2.2x -> 1x), one light sweep, hold

  Options in the "bookends" block (all optional, defaults = the original approved white version):
    theme   "light" (white card, navy/red logo) | "dark" (black card, white/red logo, one light sweep
            across the logo like a spotlight on a polished lip)
    slide   "left" | "right" | "down" | "up": direction the film pushes in; match the opener's motion
    outro   false = intro only. The film can then be any finished file (no compose.py EDL needed);
            film_hub, film_rim and card_wheel are not required.
  The EDL's "fps" sets the output rate (default 25); keep it equal to the film's native rate.

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
W, H, FPS = 1080, 1920, 25

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
#   ink         {"primary": "#0A1B2B", "accent": "#C7222A"}   sampled from the logo
#   tagline     [["UNLOCK YOUR ", "primary"], ["STYLE", "accent"]]
CFG = {}
NAVY = RED = None


def hex_rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255


def load_cfg(edl):
    global NAVY, RED
    b = edl["bookends"]
    CFG.update(card=ROOT / b["card"], logo_box=tuple(b["logo_box"]), tagline=b.get("tagline", []),
               theme=b.get("theme", "light"), slide=b.get("slide", "left"), outro=b.get("outro", True))
    if CFG["outro"]:
        CFG.update(card_wheel=tuple(b["card_wheel"]), film_hub=tuple(b["film_hub"]), film_rim=float(b["film_rim"]))
    NAVY, RED = hex_rgb(b["ink"]["primary"]), hex_rgb(b["ink"]["accent"])


def ease(name, t):
    return C.EASE[name](C.clamp01(t))


# ------------------------------------------------------------------ assets

def clean_logo(scale=2.6, primary=None):
    """Logo from the card, upscaled and re-inked in the two brand colours on a transparent matte.

    primary: colour for the logo body instead of the sampled ink (e.g. white on a dark card).
    """
    img = Image.open(CFG["card"]).convert("RGB").crop(CFG["logo_box"])
    img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    a = np.asarray(img).astype(np.float32) / 255
    is_red = (a[..., 0] - a[..., 2]) > 0.25
    ink = np.where(is_red[..., None], RED, NAVY)
    dist = np.linalg.norm(1 - a, axis=2) / np.linalg.norm(1 - ink, axis=2)
    alpha = np.clip((dist - 0.22) / 0.5, 0, 1)
    alpha = alpha * alpha * (3 - 2 * alpha)          # crisp, anti-aliased edges; drops JPEG noise
    alpha = cv2.GaussianBlur(alpha, (0, 0), 0.6)
    if primary is not None:
        ink = np.where(is_red[..., None], RED, primary)
    return np.dstack([ink, alpha]).astype(np.float32)


def text_rgba(text, weight, size, track, color):
    arr = C.render_text(text, weight, size, track)
    arr[..., :3] = color
    return arr


def card_canvas():
    card = np.asarray(Image.open(CFG["card"]).convert("RGB")).astype(np.float32) / 255
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


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=nb_frames,r_frame_rate", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip().split(",")
    num, den = out[0].split("/")
    return int(out[1]) * int(den) / int(num)


def push_slide(card_img, fr, k, direction):
    """Card leaves and the film enters, both moving in `direction` (k = 0..1)."""
    img = np.empty_like(card_img)
    if direction in ("left", "right"):
        d = int(round(k * W))
        if direction == "left":
            img[:, :W - d], img[:, W - d:] = card_img[:, d:], fr[:, :d]
        else:
            img[:, d:], img[:, :d] = card_img[:, :W - d], fr[:, W - d:]
    else:
        d = int(round(k * H))
        if direction == "down":
            img[d:], img[:d] = card_img[:H - d], fr[H - d:]
        else:
            img[:H - d], img[H - d:] = card_img[d:], fr[:d]
    return img


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

    global FPS
    edl = json.loads(Path(args.edl).read_text())
    if args.bpm:
        edl["bpm"] = args.bpm
    FPS = edl.get("fps", FPS)
    load_cfg(edl)
    dark = CFG["theme"] == "dark"
    if CFG["outro"]:
        (hx, hy, hr), film_len = film_hub_on_screen(edl)
    else:
        hx = hy = hr = 0.0
        film_len = probe_duration(args.film)
    film_n = round(film_len * FPS)
    film_start = INTRO_HOLD                                  # film frame 0 enters with the slide
    iris_start = film_start + film_len - IRIS_LEAD
    total = iris_start + IRIS + CARD_HOLD if CFG["outro"] else film_start + film_len
    nframes = round(total * FPS)
    print(f"intro {INTRO_HOLD + SLIDE:.2f}s  film {film_start:.2f}-{film_start + film_len:.2f}  "
          f"iris {iris_start:.2f}  total {total:.2f}s  hub@({hx:.0f},{hy:.0f}) r{hr:.0f}", file=sys.stderr)

    logo = clean_logo(primary=hex_rgb("#A9B1BA") if dark else None)  # brushed-steel grey: the sweep reads on it
    lw = 640
    logo = cv2.resize(logo, (lw, round(logo.shape[0] * lw / logo.shape[1])), interpolation=cv2.INTER_AREA)
    ink = {"primary": NAVY, "accent": RED}
    tag_parts = [text_rgba(txt, 700, 66, 0.16, ink[col]) for txt, col in CFG["tagline"]]
    if CFG["outro"]:
        card, (ccx, ccy, cr) = card_canvas()
    base = np.full((H, W, 3), 0.012, np.float32) if dark else np.ones((H, W, 3), np.float32)
    if dark:                                                 # faint cold vignette so the black has depth
        gy, gx = np.mgrid[0:H, 0:W].astype(np.float32)
        v = np.exp(-(((gx - W / 2) / (W * 0.62)) ** 2 + ((gy - 700) / (H * 0.42)) ** 2))
        base += v[..., None] * np.array([0.020, 0.026, 0.034], np.float32)
        lg_mask = np.zeros((H, W, 3), np.float32)            # where the settled logo sits
        C.blit(lg_mask, np.dstack([np.ones_like(logo[..., :3]), logo[..., 3:4]]),
               W / 2 - logo.shape[1] / 2, 700 - logo.shape[0] / 2)
        lg_mask = cv2.GaussianBlur(lg_mask[..., 0], (0, 0), 1.5)

    def intro_frame(t):
        img = base.copy()
        # logo: fade + settle from 94 %, ease-out, already visible on frame 1
        k = ease("out_cubic", (t + 0.12) / 0.62)
        s = 0.94 + 0.06 * k
        lg = cv2.resize(logo, (round(logo.shape[1] * s), round(logo.shape[0] * s)), interpolation=cv2.INTER_AREA)
        C.blit(img, lg, W / 2 - lg.shape[1] / 2, 700 - lg.shape[0] / 2, k)
        # tagline: one line rising out of a mask, each part lands ~0.27 s after the previous one
        y = 1080
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
        ry = y + 62 if tag_parts else int(700 + logo.shape[0] / 2 + 48)   # no tagline: rule sits under the logo
        if rw > 0:
            img[ry:ry + 3, W // 2 - rw // 2:W // 2 - rw // 2 + rw] = RED
        if dark:                                             # one spotlight sweep across the logo
            p = ease("in_out_sine", (t - 0.50) / 1.05)
            if 0 < p < 1:                                    # travels just across the logo, slow enough to read
                x0 = W / 2 - logo.shape[1] / 2 - 160 + 0.45 * 700
                x1 = W / 2 + logo.shape[1] / 2 + 160 + 0.45 * 700
                band = (xx + 0.45 * yy) - (x0 + p * (x1 - x0))
                glow = np.exp(-(band / 85) ** 2) * 0.95 * lg_mask
                img = 1 - (1 - img) * (1 - glow[..., None])  # screen blend over the logo only
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
            img = push_slide(intro_frame(t), get_film(f - round(film_start * FPS)), k, CFG["slide"])
        elif t < iris_start or not CFG["outro"]:
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
    if not CFG["outro"]:                                     # intro only: shift the film's cut list
        for c in tl.get("cuts", []):
            c["start"] += off
            c["end"] += off
        tl.setdefault("cuts", []).insert(0, {"name": "brand_logo", "start": 0.0, "end": film_start + SLIDE})
        tl["duration"] = total
        tl["intro"] = {"slide_into_film": film_start, "slide": CFG["slide"], "theme": CFG["theme"]}
        json.dump(tl, open(out.with_suffix(".timeline.json"), "w"), indent=2, ensure_ascii=False)
        print(f"wrote {out}", file=sys.stderr)
        return
    for s in tl["shots"]:
        s["start"] += off
        s["end"] += off
    tl["shots"].insert(0, {"name": "brand_logo_tagline", "start": 0.0, "end": film_start + SLIDE, "src_in": None})
    tl["duration"] = total
    tl["cue_points"] = {"open_impact": 0.0, "tagline_accent": 0.72, "slide_into_film": film_start,
                        "riser_end_reveal": (None if tl["cue_points"]["riser_end_reveal"] is None
                                             else off + tl["cue_points"]["riser_end_reveal"]),
                        "signature": off + tl["cue_points"]["signature"],
                        "end_card_iris": iris_start, "end": total}
    tl["shimmer_at"] = tl["shots"][min(2, len(tl["shots"]) - 1)]["start"]  # second film shot (detail texture)
    json.dump(tl, open(out.with_suffix(".timeline.json"), "w"), indent=2)
    print(f"wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
