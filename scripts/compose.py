#!/usr/bin/env python3
"""Render a 9:16 edit from an EDL (edit/edl_*.json) and the low-res source.

The compositor works frame by frame with sub-pixel affine sampling (Lanczos):
each shot is shown inside a window (square or wide) over a dark, blurred
duplicate of itself. It handles wheel-anchored push-ins, the square->wide
"aperture" reveal, the closing wide->square loop move and the titles.

Usage:
  python3 scripts/compose.py edit/edl_hero.json renders/out.mp4 [--bpm 120] [--audio mix.wav]
         [--preview-every N --preview-dir work/preview]
"""
import argparse, json, math, subprocess, sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = {400: ROOT / "assets/fonts/DMSans-400.ttf", 500: ROOT / "assets/fonts/DMSans-500.ttf",
         700: ROOT / "assets/fonts/DMSans-700.ttf"}
SRC_W, SRC_H = 448, 368
# Rows that contain picture (everything else is player letterbox or player UI).
LETTERBOX_ROWS = (50, 318)
ZOOMED_RANGES = [((5.10, 6.30), (40, 336)), ((7.35, 9.50), (40, 336))]  # badge at y~20-35 excluded

EASE = {
    "linear": lambda t: t,
    "out_cubic": lambda t: 1 - (1 - t) ** 3,
    "in_cubic": lambda t: t ** 3,
    "out_expo": lambda t: 1.0 if t >= 1 else 1 - 2 ** (-10 * t),
    "in_out_sine": lambda t: -(math.cos(math.pi * t) - 1) / 2,
    "in_out_cubic": lambda t: 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2,
}


def clamp01(t):
    return max(0.0, min(1.0, t))


def lerp(a, b, t):
    return a + (b - a) * t


def pic_rows(t):
    for (a, b), rows in ZOOMED_RANGES:
        if a <= t <= b:
            return rows
    return LETTERBOX_ROWS


# ---------------------------------------------------------------- source

class Source:
    """Decodes the needed source ranges once and serves the frame nearest to a time."""

    def __init__(self, path, ranges):
        pts = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                              "frame=pts_time", "-of", "csv=p=0", str(path)],
                             capture_output=True, text=True, check=True).stdout.split()
        self.pts = np.array([float(p) for p in pts])
        need = np.zeros(len(self.pts), bool)
        for a, b in ranges:
            need |= (self.pts >= a - 0.1) & (self.pts <= b + 0.1)
        cmd = ["ffmpeg", "-v", "fatal", "-i", str(path), "-fps_mode", "passthrough", "-vf",
               "scale=in_color_matrix=bt709:in_range=tv,format=rgb24", "-f", "rawvideo", "-"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        self.frames = {}
        n = SRC_W * SRC_H * 3
        for i in range(len(self.pts)):
            buf = proc.stdout.read(n)
            if len(buf) < n:
                break
            if need[i]:
                self.frames[i] = np.frombuffer(buf, np.uint8).reshape(SRC_H, SRC_W, 3).astype(np.float32) / 255
        proc.wait()
        self.idx = np.array(sorted(self.frames))

        # The capture (~40 fps, irregular) holds every film frame 1-2 times. Keep only the
        # captures that show a new film frame so playback can be re-timed to an exact 25 fps.
        prev, self.new = None, []
        for i in self.idx:
            g = cv2.resize(self.frames[i][LETTERBOX_ROWS[0]:LETTERBOX_ROWS[1]].mean(axis=2), (224, 134))
            if prev is None or np.abs(g - prev).mean() * 255 > 0.9 or self.pts[i] - self.pts[self.new[-1]] > 0.07:
                self.new.append(i)
            prev = g
        self.new = np.array(self.new)

    def film_frame(self, src_in, k):
        """k-th film frame of a shot starting at src_in (exact 25 fps re-timing). Returns (image, pts)."""
        start = int(np.searchsorted(self.pts[self.new], src_in - 0.02))
        i = int(self.new[min(start + k, len(self.new) - 1)])
        return self.frames[i], float(self.pts[i])


# ---------------------------------------------------------------- picture

def grade(img, g):
    gamma, gain = g.get("gamma", 1.0), g.get("gain", 1.0)
    x = np.power(np.clip(img, 0, 1), 1 / gamma) * gain
    knee = 0.86  # soft shoulder protects headlights and paint reflections
    hi = x > knee
    x[hi] = knee + (1 - knee) * np.tanh((x[hi] - knee) / (1 - knee))
    return x


def sample(frame, crop, win_w, win_h):
    """Map the source rect crop=(x0,y0,w,h) onto a win_w x win_h image (uniform scale)."""
    x0, y0, w, h = crop
    s = win_w / w
    M = np.float32([[s, 0, -x0 * s], [0, s, -y0 * s]])
    out = cv2.warpAffine(frame, M, (int(round(win_w)), int(round(win_h))), flags=cv2.INTER_LANCZOS4,
                         borderMode=cv2.BORDER_REPLICATE)
    blur = cv2.GaussianBlur(out, (0, 0), 1.6)
    return np.clip(out + 0.28 * (out - blur), 0, 1)  # gentle detail recovery, no halos


def background(win_img, W, H):
    small = cv2.resize(win_img, (48, int(48 * win_img.shape[0] / win_img.shape[1]) or 1), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), 3)
    bg = cv2.resize(small, (W, H), interpolation=cv2.INTER_CUBIC)
    lum = bg.mean(axis=2, keepdims=True)
    bg = (0.55 * bg + 0.45 * lum) * 0.17
    yy = np.linspace(-1, 1, H)[:, None, None]
    return bg * (1 - 0.55 * yy ** 2) + 0.012


def vignette(h, w, strength=0.16):
    yy, xx = np.mgrid[-1:1:h * 1j, -1:1:w * 1j]
    return (1 - strength * np.clip((xx ** 2 + yy ** 2) / 2, 0, 1) ** 1.2)[..., None].astype(np.float32)


# ---------------------------------------------------------------- text

def render_text(text, weight, size, track, color=(255, 255, 255), stroke=0):
    font = ImageFont.truetype(str(FONTS[weight]), size)
    adv = [font.getlength(c) + track * size for c in text]
    width = int(math.ceil(sum(adv) - track * size)) + 8 + 2 * stroke
    asc, desc = font.getmetrics()
    img = Image.new("RGBA", (width, asc + desc + 8 + 2 * stroke), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 4 + stroke
    for c, a in zip(text, adv):
        d.text((x, 4 + stroke), c, font=font, fill=color + (255,), stroke_width=stroke, stroke_fill=color + (255,))
        x += a
    arr = np.asarray(img).astype(np.float32) / 255
    return arr  # RGBA, premultiplied later


def blit(canvas, rgba, x, y, alpha=1.0, clip=None):
    """Alpha-composite rgba onto canvas at top-left (x, y); clip=(x0,y0,x1,y1) in canvas coords."""
    h, w = rgba.shape[:2]
    x, y = int(round(x)), int(round(y))
    X0, Y0, X1, Y1 = 0, 0, canvas.shape[1], canvas.shape[0]
    if clip:
        X0, Y0, X1, Y1 = max(X0, clip[0]), max(Y0, clip[1]), min(X1, clip[2]), min(Y1, clip[3])
    cx0, cy0, cx1, cy1 = max(x, X0), max(y, Y0), min(x + w, X1), min(y + h, Y1)
    if cx0 >= cx1 or cy0 >= cy1 or alpha <= 0:
        return
    src = rgba[cy0 - y:cy1 - y, cx0 - x:cx1 - x]
    a = src[..., 3:4] * alpha
    canvas[cy0:cy1, cx0:cx1] = canvas[cy0:cy1, cx0:cx1] * (1 - a) + src[..., :3] * a


# ---------------------------------------------------------------- timeline

def build_timeline(edl, bpm):
    beat = 60.0 / bpm
    t = 0.0
    shots = []
    for s in edl["shots"]:
        d = s["beats"] * beat
        shots.append(dict(s, start=t, end=t + d, dur=d))
        t += d
    return shots, t, beat


def window_rect(layout, name):
    L = layout[name]
    return np.array([L["cx"] - L["w"] / 2, L["cy"] - L["h"] / 2, L["w"], L["h"]], float)


def frame_geometry(shot, T, layout, src_t):
    """Return (window rect [x,y,w,h] in canvas px, crop rect [x0,y0,w,h] in source px)."""
    u = clamp01((T - shot["start"]) / shot["dur"])
    r0, r1 = pic_rows(src_t)
    ph = r1 - r0
    c = shot["crop"]
    W = window_rect(layout, shot["frame"])
    cw, ch = c["w"], min(c["h"], ph)
    ccx, ccy = lerp(c["cx"][0], c["cx"][1], u), lerp(c["cy"][0], c["cy"][1], u)
    zoom, anchor = 1.0, (ccx, ccy)

    if "push" in shot:
        p = shot["push"]
        zoom = lerp(p["from"], p["to"], EASE[p["ease"]](u))
        anchor = (lerp(p["anchor"][0][0], p["anchor"][1][0], u), lerp(p["anchor"][0][1], p["anchor"][1][1], u))

    if "open_from_square" in shot:  # aperture reveal: square -> wide, always full picture height
        o = shot["open_from_square"]
        k = EASE[o["ease"]](clamp01((T - shot["start"]) / o["dur"]))
        Ws, Ww = window_rect(layout, "square"), window_rect(layout, shot["frame"])
        W = Ws + (Ww - Ws) * k
        cw = W[2] * ph / W[3]
        ccx = lerp(o["crop_cx"], ccx, k)

    if "close_to_square" in shot:  # loop move: wide -> square around the front wheel
        cl = shot["close_to_square"]
        k = EASE[cl["ease"]](clamp01((T - (shot["end"] - cl["dur"])) / cl["dur"]))
        if k > 0:
            Ww, Ws = window_rect(layout, shot["frame"]), window_rect(layout, "square")
            W = Ww + (Ws - Ww) * k
            cw = W[2] * ph / W[3]
            ccx = lerp(ccx, cl["crop_cx"], k)
            zoom = lerp(zoom, cl["zoom_to"], EASE["in_out_sine"](k))

    ch = cw * W[3] / W[2]
    x0 = min(max(ccx - cw / 2, 0), SRC_W - cw)
    y0 = min(max(ccy - ch / 2, r0), r1 - ch)
    # push-in: shrink the crop around the anchor so the anchor holds its screen position
    if zoom != 1.0:
        ax, ay = anchor
        nw, nh = cw / zoom, ch / zoom
        x0 = ax - (ax - x0) / zoom
        y0 = ay - (ay - y0) / zoom
        x0 = min(max(x0, 0), SRC_W - nw)
        y0 = min(max(y0, r0), r1 - nh)
        cw, ch = nw, nh
    return W, (x0, y0, cw, ch)


def text_events(edl, shots, beat):
    by_name = {s["name"]: s for s in shots}
    ev = []
    for t in edl["texts"]:
        e = dict(t)
        if "anchor_shot" in t:
            s = by_name[t["anchor_shot"]]
            e["in"] = s["start"] + t["in_beat"] * beat
            e["out"] = s["end"] - t["out_from_end"]
        if t.get("rule"):
            col = tuple(int(t["color"][i:i + 2], 16) / 255 for i in (1, 3, 5))
            e["img"] = np.concatenate([np.ones((t["h"], t["w"], 3), np.float32) * col,
                                       np.ones((t["h"], t["w"], 1), np.float32)], axis=2)
        else:
            e["img"] = render_text(t["text"], t["font"], t["size"], t["track"], stroke=t.get("stroke", 0))
            if "suffix_mask" in t:
                e["img2"] = render_text(t["suffix_mask"], 700, t["size"], t["track"])
        ev.append(e)
    return ev


def draw_texts(canvas, events, T, W):
    IN, OUT = 0.42, 0.35
    for e in events:
        if T < e["in"] or T > e["out"] + OUT:
            continue
        a_in = EASE["out_cubic"](clamp01((T - e["in"]) / IN))
        a_out = 1 - EASE["in_cubic"](clamp01((T - e["out"]) / OUT)) if T > e["out"] else 1
        alpha = a_in * a_out
        img = e["img"]
        if e.get("rule"):
            w = max(1, int(round(img.shape[1] * EASE["out_cubic"](clamp01((T - e["in"]) / 0.5)))))
            blit(canvas, img[:, :w], W / 2 - w / 2, e["y"], alpha * 0.9)
            continue
        dy = (1 - a_in) * 16
        if "img2" in e:
            img2 = e["img2"]
            total = img.shape[1] + img2.shape[1] - 8
            x = W / 2 - total / 2
            ytop = e["y"] - img.shape[0] / 2
            blit(canvas, img, x, ytop + dy, alpha * 0.86)
            t2 = clamp01((T - e["in"] - e["mask_delay"]) / 0.72)
            m = EASE["out_cubic"](t2)
            x2 = x + img.shape[1] - 8
            y2 = ytop + (1 - m) * img2.shape[0] * 0.95
            clip = (int(x2), int(ytop + 2), int(x2 + img2.shape[1]), int(ytop + img2.shape[0] - 2))
            blit(canvas, img2, x2, y2, a_out * (0.35 + 0.65 * m), clip=clip)
        else:
            blit(canvas, img, W / 2 - img.shape[1] / 2, e["y"] - img.shape[0] / 2 + dy, alpha)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edl")
    ap.add_argument("out")
    ap.add_argument("--bpm", type=float)
    ap.add_argument("--audio", help="final mix wav to mux")
    ap.add_argument("--preview-every", type=int, default=0)
    ap.add_argument("--preview-dir", default="work/preview")
    ap.add_argument("--grain", type=float, default=0.010)
    ap.add_argument("--crf", type=int, default=18, help="use ~6 for an intermediate that gets re-encoded")
    args = ap.parse_args()

    edl = json.loads(Path(args.edl).read_text())
    bpm = args.bpm or edl["bpm"]
    fps = edl["fps"]
    Wc, Hc = edl["size"]
    shots, total, beat = build_timeline(edl, bpm)
    src = Source(ROOT / edl["source"], [(s["src_in"], s["src_in"] + s["dur"]) for s in shots])
    events = text_events(edl, shots, beat)
    nframes = int(round(total * fps))
    print(f"bpm {bpm}  beat {beat:.3f}s  duration {total:.3f}s  frames {nframes}", file=sys.stderr)
    for s in shots:
        print(f"  {s['start']:6.3f}-{s['end']:6.3f}  {s['name']:22s} src {s['src_in']:.2f}-{s['src_in'] + s['dur']:.2f}",
              file=sys.stderr)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{Wc}x{Hc}",
           "-r", str(fps), "-i", "-"]
    if args.audio:
        cmd += ["-i", args.audio]
    cmd += ["-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
            "-c:v", "libx264", "-preset", "slow", "-crf", str(args.crf), "-profile:v", "high",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
            "-movflags", "+faststart"]
    if args.audio:
        cmd += ["-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest"]
    else:
        cmd += ["-an"]
    cmd += [str(out)]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    rng = np.random.default_rng(7)
    vig_cache = {}
    pdir = Path(args.preview_dir)
    if args.preview_every:
        pdir.mkdir(parents=True, exist_ok=True)

    si = 0
    for f in range(nframes):
        T = f / fps
        while si < len(shots) - 1 and f >= int(round(shots[si]["end"] * fps)):
            si += 1
        shot = shots[si]
        k = f - int(round(shot["start"] * fps))
        frame, src_t = src.film_frame(shot["src_in"], k)
        Wr, crop = frame_geometry(shot, T, edl["layout"], src_t)
        ww, wh = int(round(Wr[2])), int(round(Wr[3]))
        win = sample(frame, crop, ww, wh)
        win = grade(win, shot.get("grade", {}))
        key = (wh, ww)
        if key not in vig_cache:
            vig_cache[key] = vignette(wh, ww)
        win *= vig_cache[key]
        canvas = background(win, Wc, Hc)
        x0, y0 = int(round(Wr[0])), int(round(Wr[1]))
        canvas[y0:y0 + wh, x0:x0 + ww] = win
        draw_texts(canvas, events, T, Wc)
        g = rng.normal(0, 1, (Hc // 2, Wc // 2)).astype(np.float32)
        g = cv2.resize(g, (Wc, Hc), interpolation=cv2.INTER_LINEAR)[..., None]
        canvas = canvas + args.grain * g * (0.6 + 0.4 * (1 - canvas.mean(axis=2, keepdims=True)))
        rgb = (np.clip(canvas, 0, 1) * 255 + 0.5).astype(np.uint8)
        enc.stdin.write(rgb.tobytes())
        if args.preview_every and f % args.preview_every == 0:
            cv2.imwrite(str(pdir / f"f{f:04d}_{T:06.2f}.jpg"), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    enc.stdin.close()
    enc.wait()
    json.dump({"bpm": bpm, "duration": total, "fps": fps,
               "shots": [{k: s[k] for k in ("name", "start", "end", "src_in")} for s in shots],
               "cue_points": {"open_impact": 0.0, "riser_end_reveal": shots[4]["start"],
                              "signature": shots[-1]["start"], "end": total}},
              open(out.with_suffix(".timeline.json"), "w"), indent=2)
    print(f"wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
