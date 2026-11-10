#!/usr/bin/env python3
"""Multi-source 9:16 compositor for short product films cut from phone screen-recordings (Reels/TikTok).

compose.py handles one letterboxed source. This one takes several sources (EDL "sources" block), each
with its own clean picture rect, and adds:
  - per-source cleanup in source pixels before any scaling: inpaint boxes for licence plates and
    burned-in text (static, or linearly tracked between two boxes)
  - timestamp re-timing at any output fps, with "speed" < 1 for real slow motion on high-fps sources
  - one shared "look" over every shot (so separate shoots read as one film) plus per-shot trims
  - hub-anchored moves: push, zoom_in (land), zoom_out (crash zoom) with radial motion blur
  - iris_in: a circular wipe from the previous shot's wheel hub into this shot's hub (zoom through the hub)
  - glint: a light streak across the wheel metal
  - titles (same engine as compose.py)
It writes <out>.timeline.json with cue points and the final hub position on screen (used by bookends.py).

Run from the project root:
  python3 .claude/skills/youtube-edit/scripts/compose_multi.py edit/edl_x.json work/film_x.mp4 [--crf 6]
        [--bpm 120] [--preview-every N --preview-dir work/preview] [--only a,b]
"""
import argparse, json, math, subprocess, sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compose as C  # noqa: E402  (text engine, easing, background, vignette)

ROOT = Path.cwd()
EASE = C.EASE
clamp01, lerp = C.clamp01, C.lerp


# ---------------------------------------------------------------- sources

class Source:
    """Decodes the needed ranges of one capture, cleans frames on demand and serves them by timestamp."""

    def __init__(self, name, cfg, ranges):
        self.name, self.cfg = name, cfg
        path = ROOT / cfg["path"]
        probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                                "stream=width,height", "-of", "csv=p=0", str(path)],
                               capture_output=True, text=True, check=True).stdout.split(",")
        self.w, self.h = int(probe[0]), int(probe[1])
        pts = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                              "frame=pts_time", "-of", "csv=p=0", str(path)],
                             capture_output=True, text=True, check=True).stdout.split()
        self.pts = np.array([float(p) for p in pts])
        need = np.zeros(len(self.pts), bool)
        for a, b in ranges:
            need |= (self.pts >= a - 0.25) & (self.pts <= b + 0.25)
        cmd = ["ffmpeg", "-v", "fatal", "-i", str(path), "-fps_mode", "passthrough", "-vf",
               "scale=in_color_matrix=bt709:in_range=tv,format=rgb24", "-f", "rawvideo", "-"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        n = self.w * self.h * 3
        self.raw = {}
        for i in range(len(self.pts)):
            buf = proc.stdout.read(n)
            if len(buf) < n:
                break
            if need[i]:
                self.raw[i] = np.frombuffer(buf, np.uint8).reshape(self.h, self.w, 3)
        proc.wait()
        self.idx = np.array(sorted(self.raw))
        # Screen captures repeat frames irregularly. Keep only captures that show a new picture,
        # then serve the new frame nearest to the requested time.
        x0, y0, x1, y1 = regions_of(cfg["clean"])[0]
        prev, new = None, []
        for i in self.idx:
            g = self.raw[i][y0:y1, x0:x1].mean(axis=2)
            if prev is None or np.abs(g - prev).mean() > cfg.get("dup_threshold", 0.45) \
                    or self.pts[i] - self.pts[new[-1]] > 0.05:
                new.append(i)
            prev = g
        self.new = np.array(new)
        self.new_pts = self.pts[self.new]
        self.cache = {}

    def index_at(self, t):
        return int(self.new[int(np.argmin(np.abs(self.new_pts - t)))])

    def hires(self, i, up):
        """(ai, faithful) 4x images of the picture rect 'sr_rect' for capture i, AI result cached on disk.

        ai       Real-ESRGAN general-x4v3 (sharp edges, clean surfaces; invents texture in fine meshes)
        faithful Lanczos 4x + gentle unsharp (no invented detail): used inside the wheel masks
        """
        import hashlib
        x0, y0, x1, y1 = self.cfg["sr_rect"]
        clean = self.frame_at(self.pts[i])[0][y0:y1, x0:x1]
        key = hashlib.md5(json.dumps([self.cfg.get("cleanup", []), self.cfg["sr_rect"], up.get("denoise", 0.5)],
                                     sort_keys=True).encode()).hexdigest()[:8]
        cdir = ROOT / up.get("cache", "work/sr_cache") / self.name
        cdir.mkdir(parents=True, exist_ok=True)
        f = cdir / f"{i:05d}_{key}.png"
        if f.exists():
            ai = cv2.cvtColor(cv2.imread(str(f)), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
        else:
            ai = UPSCALER(up)(clean)
            cv2.imwrite(str(f), cv2.cvtColor((ai * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGB2BGR),
                        [cv2.IMWRITE_PNG_COMPRESSION, 1])
        H, W = ai.shape[:2]
        fa = cv2.resize(clean, (W, H), interpolation=cv2.INTER_LANCZOS4)
        sh = up.get("faithful_sharpen", 0.6)
        fa = np.clip(fa + sh * (fa - cv2.GaussianBlur(fa, (0, 0), 2.2)), 0, 1)
        return ai, fa

    def frame_at(self, t):
        j = int(np.argmin(np.abs(self.new_pts - t)))
        i = int(self.new[j])
        if i not in self.cache:
            if len(self.cache) > 400:
                self.cache.clear()
            self.cache[i] = self.clean(self.raw[i], self.pts[i])
        return self.cache[i], float(self.pts[i])

    def clean(self, rgb, t):
        """Inpaint plates and burned-in text (source pixels), feathered so nothing has a hard edge."""
        boxes = []
        for c in self.cfg.get("cleanup", []):
            a, b = c["t"]
            if not (a - 0.02 <= t <= b + 0.02):
                continue
            b0 = np.array(c["box"], float)
            b1 = np.array(c.get("box_end", c["box"]), float)
            u = clamp01((t - a) / max(b - a, 1e-6))
            boxes.append((b0 + (b1 - b0) * u, c.get("pad", 1.5), c.get("soften", 1.0), c.get("fill_gain", 1.0)))
        img = rgb.astype(np.float32) / 255
        if not boxes:
            return img
        mask = np.zeros((self.h, self.w), np.float32)
        soft = np.zeros((self.h, self.w), np.float32)
        gain = np.ones((self.h, self.w), np.float32)
        for (x0, y0, x1, y1), pad, sf, fg in boxes:
            m = np.zeros_like(mask)
            # sub-pixel box via supersampled rasterisation
            ss = 4
            big = np.zeros((self.h * ss, self.w * ss), np.uint8)
            cv2.rectangle(big, (int((x0 - pad) * ss), int((y0 - pad) * ss)),
                          (int((x1 + pad) * ss), int((y1 + pad) * ss)), 255, -1)
            m = cv2.resize(big, (self.w, self.h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
            mask = np.maximum(mask, m)
            soft = np.maximum(soft, m * sf)
            gain = gain * (1 - m * (1 - fg))
        hard = (mask > 0.02).astype(np.uint8) * 255
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        fill = cv2.inpaint(bgr, hard, 4, cv2.INPAINT_TELEA)
        fill = cv2.cvtColor(fill, cv2.COLOR_BGR2RGB).astype(np.float32) / 255
        # smooth the fill a touch so inpaint streaks don't show at 5x
        sm = cv2.GaussianBlur(fill, (0, 0), 1.1)
        fill = fill * (1 - soft[..., None] * 0.7) + sm * (soft[..., None] * 0.7)
        fill = fill * cv2.GaussianBlur(gain, (0, 0), 0.8)[..., None]
        a = cv2.GaussianBlur(mask, (0, 0), 0.8)[..., None]
        a = np.clip(a * 1.6, 0, 1)
        return img * (1 - a) + fill * a


_UP = {}


def UPSCALER(up):
    k = up.get("denoise", 0.5)
    if k not in _UP:
        import upscale
        _UP[k] = upscale.Upscaler(ROOT / up.get("models", "work/models"), denoise=k)
    return _UP[k]


def track_wheels(shot, src, indices):
    """Per output frame, (x, y, r) of every wheel in the shot, in source px.

    A wheel is {"c": [x, y] or [[x0, y0], [x1, y1]], "r": r or [r0, r1], "ry": vertical/horizontal ratio,
    "track": true}. Tracked wheels follow the picture by template matching (sub-pixel) from the given start
    position; untracked ones interpolate linearly between start and end."""
    n = len(indices)
    out = []
    for wdef in shot.get("wheels", []):
        c0, c1 = (wdef["c"] if isinstance(wdef["c"][0], (list, tuple)) else (wdef["c"], wdef["c"]))
        r0, r1 = (wdef["r"] if isinstance(wdef["r"], (list, tuple)) else (wdef["r"], wdef["r"]))
        pos = [(lerp(c0[0], c1[0], k / max(n - 1, 1)), lerp(c0[1], c1[1], k / max(n - 1, 1))) for k in range(n)]
        if wdef.get("track"):
            h = int(max(r0, r1) * 1.15) + 3
            gray = lambda i: src.raw[i].astype(np.float32).mean(axis=2)
            g = gray(indices[0])
            x, y = c0
            tmpl = g[int(y) - h:int(y) + h + 1, int(x) - h:int(x) + h + 1].copy()
            pos, vx, vy, last = [(x, y)], 0.0, 0.0, indices[0]
            for i in indices[1:]:
                if i == last:
                    pos.append(pos[-1])
                    continue
                g = gray(i)
                sr_ = 10
                px, py = x + vx, y + vy
                X0, Y0 = int(px) - h - sr_, int(py) - h - sr_
                win = g[max(Y0, 0):Y0 + 2 * (h + sr_) + 1, max(X0, 0):X0 + 2 * (h + sr_) + 1]
                res = cv2.matchTemplate(win, tmpl, cv2.TM_CCOEFF_NORMED)
                _, _, _, (mx, my) = cv2.minMaxLoc(res)
                dx = dy = 0.0                                    # parabolic sub-pixel refinement
                if 0 < mx < res.shape[1] - 1:
                    a, b, c = res[my, mx - 1], res[my, mx], res[my, mx + 1]
                    dx = 0.5 * (a - c) / (a - 2 * b + c + 1e-9)
                if 0 < my < res.shape[0] - 1:
                    a, b, c = res[my - 1, mx], res[my, mx], res[my + 1, mx]
                    dy = 0.5 * (a - c) / (a - 2 * b + c + 1e-9)
                nx, ny = max(X0, 0) + mx + dx + h, max(Y0, 0) + my + dy + h
                vx, vy = 0.6 * vx + 0.4 * (nx - x), 0.6 * vy + 0.4 * (ny - y)
                x, y, last = nx, ny, i
                new = g[int(y) - h:int(y) + h + 1, int(x) - h:int(x) + h + 1]
                if new.shape == tmpl.shape:
                    tmpl = 0.85 * tmpl + 0.15 * new
                pos.append((x, y))
        out.append([(p[0], p[1], lerp(r0, r1, k / max(n - 1, 1)), wdef.get("ry", 1.0), wdef.get("core", 1.0))
                    for k, p in enumerate(pos)])
    return [list(z) for z in zip(*out)] if out else [[] for _ in range(n)]


def wheel_mask(shape, wheels, sr_rect, scale=4):
    """Soft elliptical mask (1 = faithful) over every wheel, in hi-res pixels."""
    H, W = shape
    m = np.zeros((H, W), np.float32)
    for x, y, r, ry, core in wheels:
        cx, cy = (x - sr_rect[0]) * scale, (y - sr_rect[1]) * scale
        R = r * scale * core
        x0, x1 = int(max(cx - R * 1.4, 0)), int(min(cx + R * 1.4, W))
        y0, y1 = int(max(cy - R * ry * 1.4, 0)), int(min(cy + R * ry * 1.4, H))
        if x0 >= x1 or y0 >= y1:
            continue
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        d = np.sqrt(((xx - cx) / R) ** 2 + ((yy - cy) / (R * ry)) ** 2)
        a = np.clip((1.12 - d) / 0.24, 0, 1)
        m[y0:y1, x0:x1] = np.maximum(m[y0:y1, x0:x1], a * a * (3 - 2 * a))
    return m


# ---------------------------------------------------------------- look

def apply_look(img, look, trim):
    """Shared film look + per-shot trims. img float RGB 0..1."""
    x = img
    wb = np.array(trim.get("wb", [1, 1, 1]), np.float32) * np.array(look.get("wb", [1, 1, 1]), np.float32)
    x = x * wb * trim.get("exposure", 1.0)
    g = trim.get("gamma", 1.0)
    if g != 1.0:
        x = np.power(np.clip(x, 0, None), 1 / g)
    sat = trim.get("sat", 1.0) * look.get("sat", 1.0)
    lum = (x * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(axis=2, keepdims=True)
    x = lum + (x - lum) * sat
    gsat = trim.get("green_sat", look.get("green_sat", 1.0))
    if gsat != 1.0:  # tame lawns/trees only (pixels where green dominates)
        gdom = np.clip((x[..., 1:2] - np.maximum(x[..., 0:1], x[..., 2:3])) * 6, 0, 1)
        x = lum + (x - lum) * (1 - gdom * (1 - gsat))
    c = look.get("contrast", 1.0) * trim.get("contrast", 1.0)
    pivot = look.get("pivot", 0.42)
    x = pivot + (x - pivot) * c
    # split tone: cool shadows, warm highlights (very light; the same on every shot = one film)
    st = look.get("split", 0.0)
    if st:
        lum = np.clip((x * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(axis=2, keepdims=True), 0, 1)
        x = x + st * ((1 - lum) * np.array([-0.6, 0.1, 0.5], np.float32) + lum * np.array([0.5, 0.1, -0.6], np.float32))
    x = np.clip(x + look.get("lift", 0.0) * (1 - x), 0, None)
    knee = 0.86
    hi = x > knee
    x[hi] = knee + (1 - knee) * np.tanh((x[hi] - knee) / (1 - knee))
    return np.clip(x, 0, 1)


# ---------------------------------------------------------------- geometry

def window_rect(layout, name):
    L = layout[name]
    return np.array([L["cx"] - L["w"] / 2, L["cy"] - L["h"] / 2, L["w"], L["h"]], float)


def pt_lerp(p, u):
    """p is [x, y] or [[x, y], [x, y]] (start -> end of the shot)."""
    if isinstance(p[0], (list, tuple)):
        return (lerp(p[0][0], p[1][0], u), lerp(p[0][1], p[1][1], u))
    return tuple(p)


def zoom_at(shot, T):
    u = clamp01((T - shot["start"]) / shot["dur"])
    z = 1.0
    if "push" in shot:
        p = shot["push"]
        z = lerp(p["from"], p["to"], EASE[p.get("ease", "in_out_sine")](u))
    if "zoom_in" in shot:
        zi = shot["zoom_in"]
        k = EASE[zi.get("ease", "out_cubic")](clamp01((T - shot["start"]) / zi["dur"]))
        z *= lerp(zi["from"], 1.0, k)
    if "zoom_out" in shot:
        zo = shot["zoom_out"]
        k = EASE[zo.get("ease", "in_cubic")](clamp01((T - (shot["end"] - zo["dur"])) / zo["dur"]))
        z *= lerp(1.0, zo["to"], k)
    return z


def regions_of(clean):
    """'clean' is one rect [x0, y0, x1, y1] or a list of rects (an L-shaped overlay-free area)."""
    return [clean] if isinstance(clean[0], (int, float)) else clean


def fit(x0, y0, w, h, regions):
    """Move the crop the least distance needed to sit fully inside one of the clean rects."""
    best = None
    for bx0, by0, bx1, by1 in regions:
        if w > bx1 - bx0 + 1e-6 or h > by1 - by0 + 1e-6:
            continue
        nx, ny = min(max(x0, bx0), bx1 - w), min(max(y0, by0), by1 - h)
        d = math.hypot(nx - x0, ny - y0)
        if best is None or d < best[0]:
            best = (d, nx, ny)
    if best is None:  # larger than every rect: use the first one
        bx0, by0, bx1, by1 = regions[0]
        return min(max(x0, bx0), bx1 - w), min(max(y0, by0), by1 - h)
    return best[1], best[2]


def geometry(shot, T, layout, clean):
    """(window rect, crop rect (x0, y0, w, h) in source px, hub in source px)."""
    u = clamp01((T - shot["start"]) / shot["dur"])
    W = window_rect(layout, shot["frame"])
    regions = regions_of(clean)
    bx0, by0, bx1, by1 = regions[0]
    c = shot["crop"]
    cw = min(c.get("w", bx1 - bx0), bx1 - bx0)
    ch = cw * W[3] / W[2]
    if ch > by1 - by0:
        ch = by1 - by0
        cw = ch * W[2] / W[3]
    ccx, ccy = pt_lerp(c["c"], u) if "c" in c else ((bx0 + bx1) / 2, by1 - ch / 2)
    x0, y0 = fit(ccx - cw / 2, ccy - ch / 2, cw, ch, regions[:1])
    hub = pt_lerp(shot["hub"], u) if "hub" in shot else (x0 + cw / 2, y0 + ch / 2)
    z = zoom_at(shot, T)
    if z != 1.0:
        # s = 1 keeps the hub where it is on screen; s > 1 also brings it towards the centre as we zoom
        s = shot.get("centre", 1.0) if z > 1 else 1.0
        ax, ay = hub
        mx, my = x0 + cw / 2, y0 + ch / 2
        nw, nh = cw / z, ch / z
        ncx = ax + (mx - ax) / z ** s
        ncy = ay + (my - ay) / z ** s
        x0, y0 = fit(ncx - nw / 2, ncy - nh / 2, nw, nh, regions)
        cw, ch = nw, nh
    return W, (x0, y0, cw, ch), hub


def to_screen(W, crop, p):
    k = W[2] / crop[2]
    return (W[0] + (p[0] - crop[0]) * k, W[1] + (p[1] - crop[1]) * k), k


# ---------------------------------------------------------------- effects

def radial_blur(img, center, amount, n=9):
    """Zoom blur about center: average of copies scaled 1..1+amount (motion blur of a fast push)."""
    if amount < 0.003:
        return img
    h, w = img.shape[:2]
    acc = np.zeros_like(img)
    for i in range(n):
        s = 1 + amount * (i / (n - 1) - 0.5)
        M = np.float32([[s, 0, center[0] * (1 - s)], [0, s, center[1] * (1 - s)]])
        acc += cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return acc / n


def glint(win, center, radius, p, angle=-0.55, width=0.16, gain=0.55):
    """A light streak crossing the wheel. p: 0..1 progress. Added mostly on bright metal."""
    h, w = win.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ca, sa = math.cos(angle), math.sin(angle)
    proj = ((xx - center[0]) * ca + (yy - center[1]) * sa) / radius      # -1..1 across the wheel
    pos = lerp(-1.6, 1.6, p)
    band = 0.55 * np.exp(-((proj - pos) / width) ** 2) + 0.9 * np.exp(-((proj - pos) / (width * 0.22)) ** 2)
    disk = np.clip((radius * 1.02 - np.hypot(xx - center[0], yy - center[1])) / (radius * 0.08), 0, 1)
    lum = win.mean(axis=2)
    metal = np.clip((lum - 0.25) / 0.45, 0, 1) ** 1.2
    g = (band * disk * (0.25 + 0.75 * metal) * gain)[..., None]
    warm = np.array([1.0, 0.96, 0.88], np.float32)
    return 1 - (1 - win) * (1 - g * warm)


def iris(prev_img, prev_hub, prev_r, cur_img, cur_hub, k_mov, k_rad, zoom_from):
    """Circular wipe from the previous hub; the new shot zooms through its own hub (zoom_from -> 1)."""
    h, w = cur_img.shape[:2]
    cx, cy = lerp(prev_hub[0], cur_hub[0], k_mov), lerp(prev_hub[1], cur_hub[1], k_mov)
    s = zoom_from ** (1 - k_rad)
    M = np.float32([[s, 0, cx - s * cur_hub[0]], [0, s, cy - s * cur_hub[1]]])
    cimg = cv2.warpAffine(cur_img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    r0, r1 = prev_r * 1.02, math.hypot(w, h)
    R = r0 * (r1 / r0) ** k_rad
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.hypot(xx - cx, yy - cy)
    m = np.clip((R - d) / 5.0 + 0.5, 0, 1)[..., None]
    # thin bright rim on the iris edge while it opens (reads as light catching the lip of the wheel)
    rim = np.exp(-((d - R) / 2.2) ** 2)[..., None] * 0.35 * math.sin(math.pi * min(1.0, k_rad * 1.15))
    out = prev_img * (1 - m) + cimg * m
    return np.clip(out + rim, 0, 1)


# ---------------------------------------------------------------- render

def build_timeline(edl, bpm):
    beat = 60.0 / bpm
    t, shots = 0.0, []
    for s in edl["shots"]:
        d = s["beats"] * beat
        shots.append(dict(s, start=t, end=t + d, dur=d))
        t += d
    return shots, t, beat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edl")
    ap.add_argument("out")
    ap.add_argument("--bpm", type=float)
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--grain", type=float, default=0.011)
    ap.add_argument("--preview-every", type=int, default=0)
    ap.add_argument("--preview-dir", default="work/preview")
    ap.add_argument("--frames", help="render only these output frames to the preview dir, e.g. 0,45,120")
    ap.add_argument("--show-masks", action="store_true", help="outline the wheel masks (QC only)")
    args = ap.parse_args()

    edl = json.loads(Path(args.edl).read_text())
    bpm = args.bpm or edl["bpm"]
    fps = edl["fps"]
    Wc, Hc = edl["size"]
    shots, total, beat = build_timeline(edl, bpm)
    look = edl.get("look", {})
    ranges = {}
    for i, s in enumerate(shots):
        sp = s.get("speed", 1.0)
        extra = shots[i + 1].get("iris_in", {}).get("dur", 0) if i + 1 < len(shots) else 0.5
        ranges.setdefault(s["src"], []).append((s["src_in"], s["src_in"] + (s["dur"] + extra) * sp))
    S = {k: Source(k, edl["sources"][k], ranges.get(k, [])) for k in edl["sources"] if k in ranges}
    events = C.text_events(edl, shots, beat)
    nframes = int(round(total * fps))
    print(f"bpm {bpm}  beat {beat:.3f}s  duration {total:.3f}s  frames {nframes} @ {fps}", file=sys.stderr)
    for s in shots:
        sp = s.get("speed", 1.0)
        print(f"  {s['start']:6.3f}-{s['end']:6.3f}  {s['name']:24s} {s['src']:7s} "
              f"src {s['src_in']:.2f}-{s['src_in'] + s['dur'] * sp:.2f}  x{sp}", file=sys.stderr)

    up = edl.get("upscale")
    grain = edl.get("grain", args.grain)

    def src_index(si, k):
        shot = shots[si]
        ts = shot["src_in"] + k / fps * shot.get("speed", 1.0)
        ts = min(ts, shot.get("src_max", 1e9))   # outgoing shots under a transition must not run into the next cut
        return S[shot["src"]].index_at(ts)

    # wheel positions per output frame (tracked on the source frames the shot actually shows)
    tracks = {}
    if up:
        for si, shot in enumerate(shots):
            nk = int(round(shot["end"] * fps)) - int(round(shot["start"] * fps))
            tracks[si] = track_wheels(shot, S[shot["src"]], [src_index(si, k) for k in range(nk)])

    def view(si, T, f):
        """Render shot si at canvas time T / frame f -> (W, window image, hub screen pos, hub radius px, crop)."""
        shot = shots[si]
        src = S[shot["src"]]
        k = f - int(round(shot["start"] * fps))
        i = src_index(si, k)
        Wr, crop, hub = geometry(shot, T, edl["layout"], edl["sources"][shot["src"]]["clean"])
        ww, wh = int(round(Wr[2])), int(round(Wr[3]))
        if up:
            ai, fa = src.hires(i, up)
            rx0, ry0 = edl["sources"][shot["src"]]["sr_rect"][:2]
            wl = tracks[si][min(k, len(tracks[si]) - 1)] if tracks[si] else []
            if shot.get("wheel_ai") or not wl:
                hi = ai
            else:
                m = wheel_mask(ai.shape[:2], wl, (rx0, ry0))[..., None]
                hi = ai * (1 - m) + fa * m
            if args.show_masks and wl:
                hi = hi.copy()
                for x, y, r, ry, core in wl:
                    cv2.ellipse(hi, (int((x - rx0) * 4), int((y - ry0) * 4)),
                                (int(r * 4 * core), int(r * 4 * core * ry)), 0, 0, 360, (0, 1, 1), 2)
            x0, y0, cw, ch = crop
            s4 = ww / (cw * 4)
            M = np.float32([[s4, 0, -(x0 - rx0) * 4 * s4], [0, s4, -(y0 - ry0) * 4 * s4]])
            win = cv2.warpAffine(hi, M, (ww, wh), flags=cv2.INTER_LANCZOS4 if s4 >= 1 else cv2.INTER_AREA,
                                 borderMode=cv2.BORDER_REPLICATE)
            win = np.clip(win, 0, 1)
        else:
            frame, _ = src.frame_at(src.pts[i])
            win = C.sample(frame, crop, ww, wh)
        win = apply_look(win, look, shot.get("grade", {}))
        (hx, hy), kk = to_screen(Wr, crop, hub)
        hx -= Wr[0]
        hy -= Wr[1]
        # motion blur on fast zooms (shutter ~180 deg)
        z0, z1 = zoom_at(shot, T - 0.5 / fps), zoom_at(shot, T + 0.5 / fps)
        amt = abs(z1 / z0 - 1) * shot.get("blur", 1.2)
        win = radial_blur(win, (hx, hy), amt)
        if "glint" in shot:
            gl = shot["glint"]
            p = (T - shot["start"] - gl["at"]) / gl["dur"]
            if 0 < p < 1:
                win = glint(win, (hx + gl.get("dx", 0) * kk, hy + gl.get("dy", 0) * kk), gl["r"] * kk,
                            EASE["in_out_sine"](p), gl.get("angle", -0.55), gl.get("width", 0.16), gl.get("gain", 0.55))
        rim = shot.get("rim", 20) * kk
        return Wr, win, (hx, hy), rim, crop

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    only = set(int(x) for x in args.frames.split(",")) if args.frames else None
    enc = None
    if only is None:
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{Wc}x{Hc}",
               "-r", str(fps), "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
               "-c:v", "libx264", "-preset", "slow", "-crf", str(args.crf), "-profile:v", "high",
               "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
               "-movflags", "+faststart", "-an", str(out)]
        enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    rng = np.random.default_rng(7)
    vig = {}
    pdir = Path(args.preview_dir)
    if args.preview_every or only:
        pdir.mkdir(parents=True, exist_ok=True)

    end_hub = None
    si = 0
    for f in range(nframes):
        T = f / fps
        while si < len(shots) - 1 and f >= int(round(shots[si]["end"] * fps)):
            si += 1
        if only is not None and f not in only:
            continue
        shot = shots[si]
        Wr, win, hub, rim, crop = view(si, T, f)
        ir = shot.get("iris_in")
        if ir and si > 0 and T < shot["start"] + ir["dur"]:
            Wp, pwin, phub, prim, _ = view(si - 1, T, f)
            u = clamp01((T - shot["start"]) / ir["dur"])
            win = iris(pwin, phub, prim, win, hub, EASE["in_out_cubic"](u), EASE[ir.get("ease", "in_out_cubic")](u),
                       ir.get("zoom_from", 1.6))
        wh, ww = win.shape[:2]
        if (wh, ww) not in vig:
            vig[(wh, ww)] = C.vignette(wh, ww)
        win = win * vig[(wh, ww)]
        canvas = C.background(win, Wc, Hc)
        x0, y0 = int(round(Wr[0])), int(round(Wr[1]))
        canvas[y0:y0 + wh, x0:x0 + ww] = win
        C.draw_texts(canvas, events, T, Wc)
        g = rng.normal(0, 1, (Hc // 2, Wc // 2)).astype(np.float32)
        g = cv2.resize(g, (Wc, Hc), interpolation=cv2.INTER_LINEAR)[..., None]
        canvas = canvas + grain * g * (0.6 + 0.4 * (1 - canvas.mean(axis=2, keepdims=True)))
        rgb = (np.clip(canvas, 0, 1) * 255 + 0.5).astype(np.uint8)
        if enc:
            enc.stdin.write(rgb.tobytes())
        if (args.preview_every and f % args.preview_every == 0) or only:
            cv2.imwrite(str(pdir / f"f{f:04d}_{T:06.2f}.jpg"), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR),
                        [cv2.IMWRITE_JPEG_QUALITY, 92])
        if f == nframes - 1:
            end_hub = [x0 + hub[0], y0 + hub[1], rim]
    if enc:
        enc.stdin.close()
        enc.wait()
        json.dump({"bpm": bpm, "duration": total, "fps": fps,
                   "shots": [{k: s[k] for k in ("name", "start", "end", "src_in")} for s in shots],
                   "cue_points": {"open_impact": 0.0,
                                  "riser_end_reveal": next((s["start"] for s in shots if s.get("cue") == "reveal"), None),
                                  "signature": shots[-1]["start"], "end": total},
                   "end_hub": end_hub},
                  open(out.with_suffix(".timeline.json"), "w"), indent=2)
        print(f"wrote {out}  end hub {end_hub}", file=sys.stderr)


if __name__ == "__main__":
    main()
