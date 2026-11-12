"""Turismo Black Friday 2026: draft (animatic) of the Vossen Black Friday Short, rebuilt 1:1 in timing and layout.

Runs in the Higgsfield sandbox in /home/user/bf (see README.md for the shot map).
Sources: clips/{ferrari,porsche,show}.mp4 (cropped from the client's screen recordings, 30 fps),
src/*.png|webp (client renders), brand/gt_white.png (GT mark), fonts/.

    python3 cgi/bf_draft.py out/frames            # writes 540 PNG frames, 1080x1920, 30 fps
    python3 cgi/bf_draft.py out/frames --only 60-80 --step 1
"""
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, N = 1080, 1920, 30, 563   # v4: the client-trimmed reference is 18.77 s (563 frames)
ROOT = "/home/user/bf"
RED = (199, 34, 42)          # Turismo red, sampled from the logo
WHITE = (255, 255, 255)
F_TITLE = f"{ROOT}/fonts/Orbitron-500.ttf"
F_TITLE_B = f"{ROOT}/fonts/Orbitron-700.ttf"
F_COND = f"{ROOT}/fonts/Anton.ttf"

# ---- copy (placeholders until the client confirms the offer) -------------------------------------------
COPY = dict(
    label="TURISMO",
    title=("BLACK", "FRIDAY"),
    date_small="NOV.23-NOV.30",
    sale="WORLDWIDE SALE",
    side="TURISMO WHEELS",
    save=("SAVE UP TO", "€7", "PER SET"),          # + two spinning-wheel zeros
    onall=("ON ALL", "FORGED SERIES WHEELS"),
    nov=("NOV 23", "THRU", "NOV 30"),
    copyright="© 2026 TURISMO WHEELS",
)

# ---- shot list (film frames at 30 fps; reference = Vossen Short, loop 18.0 s) ---------------------------
# (start, end, kind, args)
SHOTS = [
    (0, 23, "clip", dict(src="show", t=40.0, focus=(0.55, 0.5), push=(1.0, 1.06))),          # A dark wheel, title
    (23, 65, "clip", dict(src="porsche", t=19.3, focus=(0.5, 0.55), push=(1.0, 1.05))),      # B car in smoke, title
    (65, 89, "still", dict(img="g1", zoom=(1.0, 1.08), pan=((0, 0), (0, -30)))),          # C TR02 lying flat, top light (generated)
    (89, 111, "still", dict(img="g2", zoom=(1.04, 1.1), pan=((0, 0), (0, 20)))),         # D drop: X03 stack, red neon (generated)
    (111, 122, "split", dict(a=("show", 8.0), b=("show", 12.6))),                             # E Lamborghini / R34 split
    (122, 123, "white", dict()),                                                             # F 1-frame white flash
    (123, 135, "spin", dict(img="TR09F", zoom=2.3, c=(0.62, 0.38), rot=(0, -9))),            # G silver closeup
    (135, 155, "clip", dict(src="show", t=11.1, focus=(0.45, 0.5), push=(1.0, 1.05))),       # H R34 wheel closeup
    (155, 167, "mirror", dict(src="show", t=8.6, focus=(0.5, 0.5))),                        # I Lamborghini, mirrored
    (167, 178, "clip", dict(src="show", t=10.72, focus=(0.45, 0.5), push=(1.0, 1.06))),     # J R34 headlight
    (178, 203, "collage", dict()),                                                           # K wheels on white
    (203, 213, "bmw", dict(c=(0.258, 0.66), zoom=(1.0, 1.03))),                              # L car side, red line
    (213, 225, "bmw", dict(c=(0.745, 0.64), zoom=(1.12, 1.2))),                              # M car, ON ALL in
    (225, 231, "myst", dict(wheels=[("TR09F", 1150, 520, 980, 1.2, 1.0)], side=(0.15, 0.9, 0.45), rim=(0.3, 1.0, 0.5), haze=(0.05, 0.25, 0.1), embers=False, push=(1.0, 1.04))),  # N wheel in green side light
    (231, 240, "still", dict(img="g8", zoom=(1.0, 1.05), pan=((0, 0), (0, 0)))),           # O TR09 on a pedestal, sky (generated)
    (240, 248, "clip", dict(src="show", t=28.3, focus=(0.5, 0.45), push=(1.0, 1.04))),       # P Turismo sign
    (248, 257, "still", dict(img="g7", zoom=(1.0, 1.06), pan=((0, 0), (0, 0)))),           # Q X03 on a machine, dark workshop (generated)
    (257, 270, "still", dict(img="g3", zoom=(1.0, 1.08), pan=((0, 0), (0, 0)), embers=True)),  # R exploded wheel, embers (generated)
    (270, 299, "still", dict(img="g6", zoom=(1.0, 1.1), pan=((0, 0), (0, -40)))),         # S TR09 in a CNC (generated)
    (299, 312, "clip", dict(src="porsche", t=14.1, focus=(0.5, 0.5), push=(1.0, 1.04))),     # T dark motion
    (312, 329, "clip", dict(src="show", t=9.2, focus=(0.5, 0.5), push=(1.0, 1.04))),         # U Lamborghini side
    (329, 346, "still", dict(img="g5", zoom=(1.0, 1.05), pan=((30, 0), (-30, 0)))),        # V three TR02 on a wet floor (generated)
    (346, 375, "swap", dict()),                                                              # W product swaps, box
    (375, 389, "clip", dict(src="show", t=26.6, focus=(0.5, 0.5), push=(1.0, 1.05))),        # X dark car, NOV types
    (389, 395, "clip", dict(src="porsche", t=15.0, focus=(0.5, 0.5), push=(1.0, 1.1), whip=True)),  # Y whip
    (395, 425, "still", dict(img="g4", zoom=(1.0, 1.08), pan=((0, 0), (0, 30)))),         # Z TR02 stack, red and green light (generated)
    (425, 447, "clip", dict(src="show", t=13.0, focus=(0.5, 0.5), push=(1.0, 1.05))),        # AA R34 rear, crowd
    (447, 540, "gen", dict(src="final_audi.mp4", t=0.55)),                                  # AB Audi R8 + walker, final card (generated)
]

REC_ONSETS = [3.03, 3.21, 4.04, 4.26, 4.53, 4.71, 4.90, 5.46, 5.66, 6.05, 6.21, 6.44, 6.59, 7.14, 7.35, 7.53,
              7.71, 8.09, 8.28, 8.46, 8.65, 8.80, 9.00, 9.19, 9.63, 10.14, 10.35, 10.55, 10.71, 11.09, 11.28,
              11.46, 11.66, 12.05, 12.21, 12.59, 12.78, 13.05, 13.31, 13.53, 13.71, 14.09, 14.28, 14.46, 14.74]
KICK_F = [round((t - 0.13) * FPS) for t in REC_ONSETS]
ACCENT_F = [k for j, k in enumerate(KICK_F) if j == 0 or k - KICK_F[j - 1] > 9]   # first hit of each group
LIGHTS_F = [28, 36, 44, 52, 60]                         # F1 start lights on (film frames 4-36); all out at 65 (film 41)


def since_kick(f, kicks):
    d = [f - k for k in kicks if 0 <= f - k < 8]
    return min(d) if d else None


# usable source areas (x0, y0, x1, y1): the Instagram UI covers the bottom of the Ferrari reel
AREA = {"ferrari": (0, 0, 232, 318), "porsche": (0, 0, 368, 206), "show": (0, 0, 368, 206)}
_cache = {}


def clip_frames(src, t, n):
    key = (src, t, n)
    if key not in _cache:
        w, h = {"ferrari": (232, 410)}.get(src, (368, 206))
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", f"{ROOT}/clips/{src}.mp4",
                              "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, check=True).stdout
        a = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
        if len(a) < n:
            a = np.concatenate([a, np.repeat(a[-1:], n - len(a), 0)])
        _cache[key] = a
    return _cache[key]


def cover(img, focus=(0.5, 0.5), zoom=1.0, area=None):
    """Crop a 9:16 window around focus (fractions of the usable area), scale to W x H."""
    if area:
        x0, y0, x1, y1 = area
        img = img[y0:y1, x0:x1]
    h, w = img.shape[:2]
    if w / h > W / H:
        ch = h / zoom
        cw = ch * W / H
    else:
        cw = w / zoom
        ch = cw * H / W
    cx = np.clip(focus[0] * w, cw / 2, w - cw / 2)
    cy = np.clip(focus[1] * h, ch / 2, h - ch / 2)
    M = np.float32([[W / cw, 0, -(cx - cw / 2) * W / cw], [0, H / ch, -(cy - ch / 2) * H / ch]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def lerp(a, b, u):
    return a + (b - a) * u


# ---- renders --------------------------------------------------------------------------------------------
REND = {
    "TR02A": "TURISMO_FORGED_NTR_TR02_SATIN-BLACK_ANGLE_.png",
    "TR02F": "TURISMO_FORGED_NTR_TR02_SATIN-BLACK_FRONT_.png",
    "TR02S": "TURISMO_FORGED_NTR_TR02_SATIN-BLACK_SIDE_.png",
    "TR09F": "TURISMO_FORGED_RST-IS_TR09_GLOSS-SILVER_FRONT_.png",
    "X03": "TURISMO_FORGED_X03_ROTOR_S-BK_002-scaled.png",
}
_rend = {}


def rend(k, size=None):
    key = (k, size)
    if key not in _rend:
        im = Image.open(f"{ROOT}/src/{REND[k]}").convert("RGBA")
        im = im.crop(im.getbbox())
        if size:
            s = size / max(im.size)
            im = im.resize((round(im.size[0] * s), round(im.size[1] * s)), Image.LANCZOS)
        _rend[key] = np.asarray(im).astype(np.float32) / 255
    return _rend[key]


def paste(bg, rgba, cx, cy, alpha=1.0):
    """Alpha-composite rgba (float 0-1, HxWx4) centred at (cx, cy) onto bg (float 0-1)."""
    h, w = rgba.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + w, bg.shape[1]), min(y0 + h, bg.shape[0])
    if xa >= xb or ya >= yb:
        return bg
    s = rgba[ya - y0:yb - y0, xa - x0:xb - x0]
    a = s[..., 3:4] * alpha
    d = bg[ya:yb, xa:xb]
    if bg.shape[2] == 4:                                  # "over" onto a transparent layer
        da = d[..., 3:4]
        oa = a + da * (1 - a)
        rgb = (s[..., :3] * a + d[..., :3] * da * (1 - a)) / np.maximum(oa, 1e-6)
        bg[ya:yb, xa:xb] = np.concatenate([rgb, oa], -1)
    else:
        bg[ya:yb, xa:xb] = d * (1 - a) + s[..., :3] * a
    return bg


def rot_scale(rgba, ang, scale):
    h, w = rgba.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, scale)
    nw, nh = int(w * scale) + 2, int(h * scale) + 2
    M[0, 2] += nw / 2 - w / 2
    M[1, 2] += nh / 2 - h / 2
    return cv2.warpAffine(rgba, M, (nw, nh), flags=cv2.INTER_LINEAR)


def vgrad(top, bot):
    t = np.linspace(0, 1, H)[:, None, None]
    return np.broadcast_to(np.array(top)[None, None] * (1 - t) + np.array(bot)[None, None] * t, (H, W, 3)).copy()


_bmw = None


def bmw():
    global _bmw
    if _bmw is None:
        _bmw = np.asarray(Image.open(f"{ROOT}/src/BMW-M8-G16-V16-G-BK_002.webp").convert("RGB"))
    return _bmw


# ---- shot renderers (return float RGB 0-1) ---------------------------------------------------------------
def shot_frame(kind, a, i, n):
    u = i / max(n - 1, 1)
    if kind == "clip":
        sp = a.get("speed", 1.0)
        fr = clip_frames(a["src"], a["t"], int(n * sp) + 1)[int(i * sp)]
        z = lerp(*a.get("push", (1, 1)), u)
        img = cover(fr, a["focus"], z, AREA[a["src"]]).astype(np.float32) / 255
        if a.get("whip"):
            k = 61
            ker = np.zeros((k, k), np.float32)
            ker[k // 2] = 1 / k
            img = cv2.filter2D(img, -1, ker)
        return img
    if kind == "split":
        top = cover(clip_frames(*a["a"], n)[i], (0.5, 0.5), 1.0, AREA[a["a"][0]])
        bot = cover(clip_frames(*a["b"], n)[i], (0.5, 0.5), 1.0, AREA[a["b"][0]])
        out = np.concatenate([cv2.resize(top[H // 4:H // 4 * 3], (W, H // 2)),
                              cv2.resize(bot[H // 4:H // 4 * 3], (W, H // 2))])
        return out.astype(np.float32) / 255
    if kind == "mirror":
        fr = clip_frames(a["src"], a["t"], n)[i]
        img = cover(fr, a["focus"], 1.0, AREA[a["src"]])
        half = img[H // 4:H // 4 * 3]
        out = np.concatenate([half, half[::-1] * np.linspace(0.85, 0.5, H // 2)[:, None, None]])
        return out.astype(np.float32) / 255
    if kind == "white":
        return np.ones((H, W, 3), np.float32)
    if kind == "stack":                                   # dark studio, X03 with a red neon bar
        bg = vgrad((0.05, 0.05, 0.06), (0.02, 0.02, 0.02))
        x = np.arange(W)[None, :]
        glow = np.exp(-((x - 400) / 40.0) ** 2) * np.exp(-((np.arange(H)[:, None] - 520) / 330.0) ** 2)
        bg[..., 0] += glow * 0.9
        bg[..., 1] += glow * 0.05
        bg[..., 2] += glow * 0.07
        bar = (np.abs(x - 400) < 9) & (np.abs(np.arange(H)[:, None] - 520) < 300)
        bg[bar] = (1.0, 0.25, 0.25)
        w = rot_scale(rend("X03", 1300), lerp(0, -6, u), lerp(1.0, 1.05, u))
        w = w.copy()
        w[..., :3] *= 0.8
        return np.clip(paste(bg, w, 560, 1180), 0, 1)
    if kind == "spin":
        bg = vgrad((0.75, 0.75, 0.77), (0.35, 0.35, 0.37))
        r = rend(a["img"], 1500)
        w = rot_scale(r, lerp(*a["rot"], u), a["zoom"] * lerp(1, 1.04, u))
        return paste(bg, w, W / 2 - (a["c"][0] - 0.5) * w.shape[1], H / 2 - (a["c"][1] - 0.5) * w.shape[0])
    if kind == "collage":                                 # renders on white, red line, whip at frame 8
        bg = np.ones((H, W, 3), np.float32)
        lay1 = [("TR02A", 620, 250, 330), ("TR09F", 700, 860, 620), ("X03", 560, 180, 1080),
                ("TR02F", 760, 820, 1500), ("TR02S", 520, 120, 1700)]
        lay2 = [("TR09F", 820, 330, 520), ("TR02F", 640, 900, 360), ("X03", 700, 880, 1180),
                ("TR02A", 760, 260, 1420), ("TR09F", 560, 920, 1820)]
        lay = lay1 if i < 9 else lay2
        z = lerp(1.0, 1.06, (i if i < 9 else i - 9) / 12)
        for k, s, cx, cy in lay:
            paste(bg, rend(k, int(s * z)), W / 2 + (cx - W / 2) * z, H / 2 + (cy - H / 2) * z)
        if 7 <= i <= 10:                                  # whip between the two layouts
            k = 81
            ker = np.zeros((k, k), np.float32)
            np.fill_diagonal(ker, 1 / k)
            bg = cv2.filter2D(bg, -1, ker)
        return bg
    if kind == "bmw":
        img = bmw()
        z = lerp(*a["zoom"], u)
        h0, w0 = img.shape[:2]
        ch = h0 * 0.5 / z
        cw = ch * W / H
        cx, cy = a["c"][0] * w0, a["c"][1] * h0
        cy = np.clip(cy, ch / 2, h0 - ch / 2)
        M = np.float32([[W / cw, 0, -(cx - cw / 2) * W / cw], [0, H / ch, -(cy - ch / 2) * H / ch]])
        return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_AREA,
                              borderMode=cv2.BORDER_REPLICATE).astype(np.float32) / 255
    if kind == "sky":                                     # wheel on a pole against a teal sky
        rng = np.random.default_rng(3)
        if "sky" not in _rend:
            nz = cv2.resize(rng.random((7, 4)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
            nz = cv2.GaussianBlur(nz, (0, 0), 90)
            nz = np.clip((nz - 0.5) * 1.6 + 0.35, 0, 0.9)[..., None]
            sky = vgrad((0.20, 0.55, 0.60), (0.55, 0.78, 0.80))
            _rend["sky"] = sky * (1 - nz) + nz * 0.97
        bg = _rend["sky"].copy()
        bg[1150:, 515:565] = (0.25, 0.25, 0.27)
        return paste(bg, rend("TR02A", int(lerp(900, 940, u))), 540, 820)
    if kind == "myst":
        return mystery(a, i, n)
    if kind == "still":
        return still(a, i, n)
    if kind == "gen":
        return gen_clip(a, i, n)
    if kind == "row":                                     # three wheels on a black mirror floor
        bg = vgrad((0.10, 0.10, 0.11), (0.03, 0.03, 0.03))
        x = np.arange(W)[None, :]
        yy = np.arange(H)[:, None]
        for cx in (230, 520, 860):                        # a spotlight over each wheel
            cone = np.exp(-((x - cx) / (60 + yy * 0.12)) ** 2) * np.clip(1 - yy / 1500, 0, 1)
            bg += cone[..., None] * 0.22
        pan = lerp(30, -30, u)
        for k, s, cx, cy in [("TR02A", 420, 230, 900), ("TR02A", 560, 520, 940), ("TR02A", 760, 860, 1000)]:
            r = rend(k, s).copy()
            r[..., :3] = np.clip(r[..., :3] * 1.6 + 0.04, 0, 1)
            paste(bg, r, cx + pan, cy)
            ref = r[::-1].copy()
            ref[..., 3] *= np.linspace(0.35, 0, ref.shape[0])[:, None]
            paste(bg, ref, cx + pan, cy + r.shape[0] * 0.98)
        return bg
    if kind == "swap":                                    # finishes swap every 3 frames on white
        bg = np.ones((H, W, 3), np.float32)
        seq = ["TR09F", "TR02F", "X03", "TR02A", "TR09F", "TR02F", "X03", "TR02S", "TR09F", "TR02F"]
        k = seq[min(i // 3, len(seq) - 1)]
        return paste(bg, rend(k, int(lerp(1000, 1040, u))), 540, 900)
    raise ValueError(kind)


_haze = None
_stills = {}


def still(a, i, n):
    """A generated keyframe (gen/<img>.png, 9:16) with a slow push/pan; optional rising embers."""
    k = a["img"]
    if k not in _stills:
        im = cv2.cvtColor(cv2.imread(f"{ROOT}/gen/{k}.png"), cv2.COLOR_BGR2RGB)
        _stills[k] = cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    u = i / max(n - 1, 1)
    e = u * u * (3 - 2 * u)
    z = lerp(*a.get("zoom", (1, 1)), e)
    (x0, y0), (x1, y1) = a.get("pan", ((0, 0), (0, 0)))
    M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z)
    M[0, 2] += lerp(x0, x1, e)
    M[1, 2] += lerp(y0, y1, e)
    bg = cv2.warpAffine(_stills[k], M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    if a.get("embers"):
        img = (np.clip(bg, 0, 1) * 255).astype(np.uint8)
        rng = np.random.default_rng(5)
        for _ in range(60):
            x0_, y0_, sp, ph = rng.uniform(0, W), rng.uniform(300, H), rng.uniform(6, 18), rng.uniform(0, 6.28)
            x = x0_ + np.sin(ph + i * 0.2) * 20
            y = (y0_ - sp * i) % H
            fl = 0.6 + 0.4 * np.sin(ph + i * 0.9)
            cv2.circle(img, (int(x), int(y)), int(rng.integers(2, 4)), (255, int(150 * fl), int(40 * fl)), -1, cv2.LINE_AA)
        bg = img.astype(np.float32) / 255
    return np.clip(bg, 0, 1)


_gen = {}


def gen_clip(a, i, n):
    """A generated video (gen/<src>) conformed to 30 fps, cover-fit to 9:16."""
    key = a["src"]
    if key not in _gen:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a.get("t", 0)), "-i", f"{ROOT}/gen/{key}",
                              "-vf", f"fps=30,scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}",
                              "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, check=True).stdout
        v = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
        if len(v) < n:
            v = np.concatenate([v, np.repeat(v[-1:], n - len(v), 0)])
        _gen[key] = v
        # locked-off shot: the empty plate is the temporal median; the walker is what differs from it
        plate = np.median(v[::2].astype(np.float32), axis=0)
        ms = []
        for fr in v:
            d = np.abs(fr.astype(np.float32) - plate).max(-1)
            m = (cv2.GaussianBlur(d, (0, 0), 3) > 28).astype(np.uint8)
            m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
            m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
            ms.append(cv2.GaussianBlur(m.astype(np.float32), (0, 0), 2.5))
        _gen[key + ":matte"] = ms
    return _gen[key][min(i, len(_gen[key]) - 1)].astype(np.float32) / 255


def mystery(a, i, n):
    """Dark 'mysterious' studio: spotlight beams through haze, neon bars, rim-lit wheel renders, embers."""
    global _haze
    u = i / max(n - 1, 1)
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    bg = np.zeros((H, W, 3), np.float32) + 0.012
    if _haze is None:
        rng = np.random.default_rng(11)
        hz = cv2.resize(rng.random((30, 18)).astype(np.float32), (W + 400, H + 400), interpolation=cv2.INTER_CUBIC)
        _haze = cv2.GaussianBlur(hz, (0, 0), 60)
        _haze = (_haze - _haze.min()) / (_haze.max() - _haze.min())
    hz = _haze[200 - int(i * 3):200 - int(i * 3) + H, 200 + int(i * 2):200 + int(i * 2) + W][..., None]
    hcol = np.array(a.get("haze", (0.06, 0.06, 0.07)), np.float32)
    bg += hz * hcol * 0.6
    for bx, col, wd in a.get("beams", []):                # volumetric cone from the top
        cone = np.exp(-((xx - bx) / (wd * 0.35 + yy * 0.22)) ** 2) * np.clip(1.1 - yy / 1900, 0, 1)
        bg += cone[..., None] * (0.3 + 0.6 * hz) * np.array(col, np.float32) * 1.0
        bg += np.exp(-((xx - bx) ** 2 + (yy - 40) ** 2) / 900.0)[..., None] * np.array(col) * 0.9
    if "side" in a:                                       # coloured light from the right
        g = np.exp(-((xx - W) / 380.0) ** 2) * np.exp(-((yy - 900) / 700.0) ** 2)
        bg += g[..., None] * np.array(a["side"], np.float32) * (0.35 + 0.4 * hz)
    for nx, y0, y1, col in a.get("neons", []):            # neon tubes with glow
        g = np.exp(-((xx - nx) / 55.0) ** 2) * np.exp(-(np.maximum(0, np.maximum(y0 - yy, yy - y1)) / 120.0) ** 2)
        bg += g[..., None] * np.array(col, np.float32) * 0.8
        bg[max(y0, 0):y1, nx - 8:nx + 8] = np.array(col) * 0.4 + 0.6
    if a.get("bars"):                                     # machine frame in silhouette
        for bxx in (150, 420, 700, 950):
            bg[:, bxx - 22:bxx + 22] *= 0.15
        bg[300:330] *= 0.15
        bg[1500:1540] *= 0.15
    rim = np.array(a.get("rim", (1, 1, 1)), np.float32)
    for k, size, cx, cy, spin, squash in a["wheels"]:
        r = rot_scale(rend(k, size), -i * spin, 1.0)
        if squash != 1.0:
            r = cv2.resize(r, (r.shape[1], max(2, int(r.shape[0] * squash))), interpolation=cv2.INTER_AREA)
        r = r.copy()
        hh = r.shape[0]
        light = np.clip(1.25 - np.linspace(0, 1, hh)[:, None] * 0.9, 0.25, 1.25)   # lit from the top
        r[..., :3] = r[..., :3] * 0.55 * light[..., None]
        al = (r[..., 3] * 255).astype(np.uint8)
        edge = cv2.GaussianBlur(cv2.subtract(al, cv2.erode(al, np.ones((7, 7), np.uint8))), (0, 0), 3)
        e = (edge.astype(np.float32) / 255)[..., None] * light[..., None]
        r[..., :3] = np.clip(r[..., :3] + e * rim * 0.9, 0, 1)
        glow = np.zeros_like(r)
        glow[..., :3] = rim
        glow[..., 3] = cv2.GaussianBlur(edge.astype(np.float32) / 255, (0, 0), 18) * 0.8
        paste(bg, glow, cx, cy)
        paste(bg, r, cx, cy)
    if a.get("embers"):                                   # embers drifting up
        img = (np.clip(bg, 0, 1) * 255).astype(np.uint8)
        rng = np.random.default_rng(5)
        for _ in range(70):
            x0, y0, sp, ph = rng.uniform(0, W), rng.uniform(300, H), rng.uniform(6, 18), rng.uniform(0, 6.28)
            x = x0 + np.sin(ph + i * 0.2) * 20
            y = (y0 - sp * i) % H
            rad = int(rng.integers(2, 5))
            fl = 0.6 + 0.4 * np.sin(ph + i * 0.9)
            cv2.circle(img, (int(x), int(y)), rad, (255, int(150 * fl), int(40 * fl)), -1, cv2.LINE_AA)
        bg = img.astype(np.float32) / 255
        bg += cv2.GaussianBlur(np.clip(bg - 0.6, 0, 1), (0, 0), 6) * 0.8
    else:                                                 # dust motes in the light
        img = (np.clip(bg, 0, 1) * 255).astype(np.uint8)
        rng = np.random.default_rng(9)
        for _ in range(60):
            x0, y0 = rng.uniform(0, W), rng.uniform(0, H)
            x, y = x0 + np.sin(i * 0.05 + x0) * 15, (y0 + i * 1.5) % H
            v = int(90 + 120 * hz[int(y) % H, int(x) % W, 0])
            cv2.circle(img, (int(x), int(y)), 2, (v, v, v), -1, cv2.LINE_AA)
        bg = img.astype(np.float32) / 255
    vig = np.exp(-(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2))[..., None]
    bg *= 0.35 + 0.65 * vig
    z = lerp(*a.get("push", (1, 1)), u)
    if z != 1:
        M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z)
        bg = cv2.warpAffine(bg, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return np.clip(bg, 0, 1)


# ---- typography -----------------------------------------------------------------------------------------
def font(path, size):
    return ImageFont.truetype(path, size)


def text_img(txt, path, size, fill=WHITE, stroke=0, outline=False, sx=1.0, skew=0.0, track=0):
    f = font(path, size)
    pad = size
    tmp = Image.new("RGBA", (int(size * len(txt) * 1.2 + 2 * pad), int(size * 1.6 + 2 * pad)), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    x = pad
    for ch in txt:
        if outline:
            d.text((x, pad), ch, font=f, fill=(0, 0, 0, 0), stroke_width=stroke, stroke_fill=fill + (255,))
        else:
            d.text((x, pad), ch, font=f, fill=fill + (255,))
        x += d.textlength(ch, font=f) + track
    tmp = tmp.crop(tmp.getbbox())
    if sx != 1.0:
        tmp = tmp.resize((max(1, int(tmp.size[0] * sx)), tmp.size[1]), Image.LANCZOS)
    if skew:
        w, h = tmp.size
        tmp = tmp.transform((w + int(h * skew), h), Image.AFFINE, (1, skew, -h * skew, 0, 1, 0), Image.BICUBIC)
    return np.asarray(tmp).astype(np.float32) / 255


def put(bg, rgba, x, y, anchor="lt", alpha=1.0, clipx=None):
    """Composite rgba with its anchor at (x, y). anchor: l/c/r + t/m/b. clipx = (x0, x1) visible span."""
    h, w = rgba.shape[:2]
    x0 = x - {"l": 0, "c": w / 2, "r": w}[anchor[0]]
    y0 = y - {"t": 0, "m": h / 2, "b": h}[anchor[1]]
    if clipx:
        r = rgba.copy()
        cols = np.arange(w) + x0
        r[:, (cols < clipx[0]) | (cols > clipx[1]), 3] = 0
        rgba = r
    return paste(bg, rgba, x0 + w / 2, y0 + h / 2, alpha)


_T = {}


def T(key, *args, **kw):
    if key not in _T:
        _T[key] = text_img(*args, **kw)
    return _T[key]


def line(bg, p0, p1, col=RED, w=5):
    img = (bg * 255).astype(np.uint8)
    cv2.line(img, tuple(int(v) for v in p0), tuple(int(v) for v in p1), col, w, cv2.LINE_AA)
    return img.astype(np.float32) / 255


def hud(bg, f):
    """The BLACK FRIDAY title card, frames 0-64, with the red strike glitch at 56-64."""
    a = 0.85
    col = (np.array(WHITE) / 255).astype(np.float32)

    def L(p0, p1, w=2):
        nonlocal bg
        img = (bg * 255).astype(np.uint8)
        cv2.line(img, p0, p1, (235, 235, 235), w, cv2.LINE_AA)
        bg = img.astype(np.float32) / 255
    put(bg, T("ws_s", COPY["sale"], F_TITLE, 20, track=2), 78, 64, alpha=a)
    L((330, 76), (1000, 76))
    L((1000, 76), (1000, 170))
    circ(bg, (1000, 182), 11)
    side = np.rot90(T("side", COPY["side"], F_TITLE, 20, track=3))
    put(bg, side, 82, 120, alpha=a)
    # centre frame
    x0, x1, y0, y1 = 210, 880, 830, 1196
    L((x0, y0), (x1, y0))
    L((x0, y0), (x0, 990))
    L((x0, 1034), (x0, y1))
    L((x1, y0), (x1, 990))
    L((x1, 1034), (x1, y1))
    L((x0, y1), (395, y1))
    L((686, y1), (x1, y1))
    for p in [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]:
        L((p[0] - 12, p[1]), (p[0] + 12, p[1]))
        L((p[0], p[1] - 12), (p[0], p[1] + 12))
    circ(bg, (x0, 1012), 12)
    circ(bg, (x1, 1012), 12)
    # red label with the wordmark
    lab = T("lab", COPY["label"], F_TITLE_B, 30, track=6)
    lw, lh = lab.shape[1] + 56, 56
    bg[800 - lh // 2:800 + lh // 2, 540 - lw // 2:540 + lw // 2] = np.array(RED) / 255
    put(bg, lab, 540, 800, "cm")
    gl = 56 <= f <= 64
    t1, t2 = T("bl", COPY["title"][0], F_TITLE, 118, track=10), T("fr", COPY["title"][1], F_TITLE, 118, track=10)
    off = (np.sin(f * 7.1) * 14) if gl else 0
    put(bg, t1, 545 + off, 922, "cm")
    put(bg, t2, 545 - off, 1080, "cm")
    put(bg, T("ds", COPY["date_small"], F_TITLE, 26, track=5), 540, y1, "cm")
    put(bg, T("ws", COPY["sale"], F_TITLE, 34, track=9), 540, 1392, "cm")
    if gl:
        y = 1000 + (f - 56) * 3
        bg = line(bg, (int(lerp(W, 120, (f - 56) / 4)), y - 40), (W, y), RED, 6)
    return bg


def circ(bg, c, r):
    img = (bg * 255).astype(np.uint8)
    cv2.circle(img, c, r, (235, 235, 235), 2, cv2.LINE_AA)
    cv2.line(img, (c[0] - r // 2, c[1] - r // 2), (c[0] + r // 2, c[1] + r // 2), (235, 235, 235), 2, cv2.LINE_AA)
    cv2.line(img, (c[0] - r // 2, c[1] + r // 2), (c[0] + r // 2, c[1] - r // 2), (235, 235, 235), 2, cv2.LINE_AA)
    bg[:] = img.astype(np.float32) / 255


def save_block(bg, f):
    """SAVE UP TO / €700 / PER SET, revealed out of a red line at frames 71-77."""
    s1 = T("s1", COPY["save"][0], F_COND, 150, fill=RED, sx=0.9, skew=0.2)
    s2 = T("s2", COPY["save"][1], F_COND, 236, sx=0.9, skew=0.2)
    s3 = T("s3", COPY["save"][2], F_COND, 92, sx=0.9, skew=0.2)
    if f == 122:                                          # the white flash frame: red line only
        return put(bg, s1, 548, 872, "cm")
    lay = np.zeros((H, W, 4), np.float32)
    put(lay, s1, 548, 872, "cm")
    d = int(s2.shape[0] * 1.02)                           # the two zeros: spinning Turismo wheels
    x = 548 - (s2.shape[1] - 6 + 2 * (d + 4) + 22 + s3.shape[1]) / 2
    put(lay, s2, x + s2.shape[1] / 2, 1060, "cm")
    x += s2.shape[1] - 6
    k = since_kick(f, KICK_F)
    ang = -f * 14 - (0 if k is None else (8 - k) * 6)
    for j in range(2):
        wz = rot_scale(rend("TR09F", d), ang + j * 23, 1.0).copy()
        hh, ww = wz.shape[:2]
        ring = np.zeros((hh, ww), np.uint8)
        cv2.circle(ring, (ww // 2, hh // 2), int(d * 0.49), 255, 7, cv2.LINE_AA)
        rg = ring.astype(np.float32)[..., None] / 255
        wz[..., :3] = wz[..., :3] * (1 - rg) + rg
        wz[..., 3:4] = np.maximum(wz[..., 3:4], rg)
        paste(lay, wz, x + d / 2 + 4, 1060 + 6)
        x += d + 4
    put(lay, s3, x + 22, 1128, "lb")
    if f < 78:                                            # revealed behind the rolling wheel blade
        lay[:, max(0, int(blade_x(f)) - 40):, 3] = 0
    if 168 <= f <= 172:                                   # small glitch on shot J
        sl = slice(1000, 1080)
        lay[sl] = np.roll(lay[sl], 24 * (1 if f % 2 else -1), axis=1)
    a = lay[..., 3:4]
    return bg * (1 - a) + lay[..., :3] * a


def onall_block(bg, f):
    o1 = T("o1", COPY["onall"][0], F_COND, 128, fill=RED, sx=0.9, skew=0.2)
    o2 = T("o2", COPY["onall"][1], F_COND, 112, sx=0.86, skew=0.2)
    lay = np.zeros((H, W, 4), np.float32)
    put(lay, o1, 548, 890, "cm")
    put(lay, o2, 548, 1018, "cm")
    if f < 222:                                           # wipe in from the left behind the red line
        x = lerp(0, W, ease((f - 214) / 8))
        lay[:, int(x):, 3] = 0
    if f > 318:                                           # wipe out to the right
        x = lerp(0, W, ease((f - 318) / 6))
        lay[:, :int(x), 3] = 0
    a = lay[..., 3:4]
    return bg * (1 - a) + lay[..., :3] * a


def nov_block(bg, f):
    """Red box + NOV 23 / THRU / NOV 30 typing in (375-419) and out (512-539)."""
    cx, cy, half = 544, 964, 255
    if f < 366:
        return bg
    s = half if f >= 375 else half * ease((f - 366) / 9)
    if f >= 375 or s > 2:
        y0, y1, x0, x1 = int(cy - s), int(cy + s), int(cx - s), int(cx + s)
        bg[max(y0, 0):y1, max(x0, 0):x1] = np.array(RED) / 255
    if f < 378:
        return bg
    a, b, c = COPY["nov"]

    def typed(txt, start, step, end_start=None):
        k = int((f - start) / step) + 1
        if end_start is not None and f >= end_start:
            k = len(txt) - int((f - end_start) / 2) - 1
        return txt[:max(0, min(k, len(txt)))]
    t1 = typed(a, 378, 2, 528)
    t2 = b if 392 <= f < 522 else ""
    t3 = typed(c, 404, 3, 512)
    for txt, y, sz, outl, key in [(t1, 812, 160, False, "n1"), (t2, 964, 118, True, "n2"), (t3, 1110, 160, False, "n3")]:
        if txt.strip():
            im = T(key + txt, txt, F_COND, sz, sx=0.9, skew=0.2, outline=outl, stroke=3 if outl else 0)
            put(bg, im, cx + (8 if not outl else 0), y, "cm")
    return bg


def footer(bg, f):
    if f == 122:
        return bg
    return put(bg, T("cp", COPY["copyright"], F_TITLE, 15, track=1), 540, 1858, "cm", alpha=0.7)


_logo = None


def logo_card(bg, f):
    """TURISMO logo watermark on the final shot (like the VOSSEN mark), from frame 447."""
    global _logo
    if _logo is None:
        g = Image.open(f"{ROOT}/brand/gt_white.png").convert("RGBA")
        g = g.crop(g.getbbox())
        g = g.resize((150, round(g.size[1] * 150 / g.size[0])), Image.LANCZOS)
        g = np.asarray(g).astype(np.float32) / 255
        wm = T("wm", "TURISMO", F_TITLE_B, 44, track=14)
        h = max(g.shape[0], wm.shape[0])
        lay = np.zeros((h, g.shape[1] + 30 + wm.shape[1], 4), np.float32)
        paste(lay, g, g.shape[1] / 2, h / 2)
        paste(lay, wm, g.shape[1] + 30 + wm.shape[1] / 2, h / 2)
        _logo = lay
    return put(bg, _logo, 540, 1420, "cm", alpha=0.9)


def blade_x(f):
    u = min(max((f - 65) / 13, 0), 1)
    return lerp(-260, W + 260, u * u * (3 - 2 * u))


def blade(bg, f):
    """A Turismo wheel rolls across like a saw blade along the red line, throwing sparks (frames 65-78)."""
    if not 65 <= f <= 78:
        return bg
    x, y, d = blade_x(f), 960, 420
    bg = line(bg, (0, y), (int(x), y), RED, 7)
    for j, a in enumerate((14, 7, 0)):                    # cheap rotational blur, sharp copy on top
        w = rot_scale(rend("TR09F", d), -f * 47 - a, 1.0)
        paste(bg, w, x, y, alpha=1.0 if a == 0 else 0.35)
    img = (bg * 255).astype(np.uint8)
    rng = np.random.default_rng(f)
    for b in range(65, f + 1):                            # sparks born at the cutting edge
        bx = blade_x(b) - d * 0.42
        rb = np.random.default_rng(b)
        for _ in range(48):
            ang = rb.uniform(np.pi * 0.85, np.pi * 1.25)
            sp = rb.uniform(30, 95)
            age = f - b
            if age > 5:
                continue
            px = bx + np.cos(ang) * sp * age
            py = y + np.sin(ang) * sp * age + 9 * age * age
            tail = (px - np.cos(ang) * sp * 0.9, py - np.sin(ang) * sp * 0.9)
            c = (255, int(230 - age * 28), int(140 - age * 22))
            cv2.line(img, (int(tail[0]), int(tail[1])), (int(px), int(py)), c, 4 if age < 2 else 2, cv2.LINE_AA)
    base = bg * 255
    glow = cv2.GaussianBlur(np.clip(img.astype(np.float32) - base, 0, 255), (0, 0), 9)
    return np.clip(img.astype(np.float32) + glow * 1.5, 0, 255) / 255


def lights(bg, f):
    """F1 start lights above the BLACK FRIDAY title: on one by one, all out at 65 (lights out)."""
    if f >= 65:
        return bg
    img = (bg * 255).astype(np.uint8)
    over = img.copy()
    cv2.rectangle(over, (262, 600), (818, 708), (12, 12, 14), -1)
    img = cv2.addWeighted(over, 0.85, img, 0.15, 0)
    glow = np.zeros_like(img)
    for j in range(5):
        cx = 318 + j * 111
        on = f >= LIGHTS_F[j]
        cv2.circle(img, (cx, 654), 38, (225, 18, 28) if on else (45, 12, 14), -1, cv2.LINE_AA)
        if on:
            cv2.circle(glow, (cx, 654), 52, (255, 40, 40), -1, cv2.LINE_AA)
            cv2.circle(img, (cx - 10, 642), 10, (255, 150, 150), -1, cv2.LINE_AA)
    glow = cv2.GaussianBlur(glow, (0, 0), 22)
    out = np.clip(img.astype(np.float32) + glow.astype(np.float32) * 0.9, 0, 255)
    return out / 255


def punch(bg, f):
    """Beat energy between the drop and the stop: a quick zoom punch on each kick, RGB split on accents."""
    k = since_kick(f, KICK_F)
    if k is None or not 87 <= f < 447:
        return bg
    z = 1 + 0.05 * np.exp(-k / 1.6)
    if z > 1.002:
        M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z)
        bg = cv2.warpAffine(bg, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    a = since_kick(f, ACCENT_F)
    if a is not None and a < 3:
        s = int(10 * (1 - a / 3))
        bg = bg.copy()
        bg[..., 0] = np.roll(bg[..., 0], s, axis=1)
        bg[..., 2] = np.roll(bg[..., 2], -s, axis=1)
    if 87 <= f < 93:                                      # shake on the drop
        dx, dy = np.random.default_rng(f).integers(-14, 15, 2)
        bg = np.roll(bg, (int(dy), int(dx)), axis=(0, 1))
    return bg


def red_lines(bg, f):
    if 179 <= f <= 186:                                   # collage: line drawing between wheels
        u = ease((f - 179) / 7)
        bg = line(bg, (250, 330), (int(lerp(250, 860, u)), int(lerp(330, 620, u))), RED, 5)
    if 190 <= f <= 202:
        u = ease((f - 190) / 10)
        bg = line(bg, (330, 520), (int(lerp(330, 880, u)), int(lerp(520, 1180, u))), RED, 5)
    if 203 <= f <= 216:                                   # horizontal line across the car (L-M)
        u = ease((f - 203) / 5)
        y = 980
        bg = line(bg, (0, y), (int(lerp(0, W, u)), y), RED, 6)
    return bg


OUTRO_A = dict(img="g9", zoom=(1.0, 1.05), pan=((0, 0), (0, 0)))


def frame(f):
    """Film frame f (0-562). Frames 0-515 follow the v3 timeline offset by 24 (g = f + 24);
    516-537 is the outro card over a dark wheel; 538-562 the card over the car again (loop)."""
    if f <= 515:
        return frame_g(f + 24)
    if f <= 537:
        bg = still(OUTRO_A, f - 516, 22)
    else:
        fr = clip_frames("porsche", 19.5, 25)[f - 538]
        bg = cover(fr, (0.5, 0.55), 1.0, AREA["porsche"]).astype(np.float32) / 255
    bg = np.ascontiguousarray(bg, np.float32)
    bg = hud(bg, 0)
    bg = footer(bg, 0)
    return (np.clip(bg, 0, 1) * 255).astype(np.uint8)


def frame_g(f):
    for s, e, kind, a in SHOTS:
        if s <= f < e:
            bg = shot_frame(kind, a, f - s, e - s)
            break
    bg = np.ascontiguousarray(bg, np.float32)
    bg = punch(bg, f)
    if f < 65:
        bg = hud(bg, f)
        bg = lights(bg, f)
    bg = red_lines(bg, f)
    bg = blade(bg, f)
    if 71 <= f < 178:
        bg = save_block(bg, f)
    if 214 <= f < 325:
        bg = onall_block(bg, f)
    bg = nov_block(bg, f)
    if f >= 447 and "final_audi.mp4:matte" in _gen:      # the walker passes in front of the date card
        k = min(f - 447, len(_gen["final_audi.mp4"]) - 1)
        m = _gen["final_audi.mp4:matte"][k][..., None]
        orig = _gen["final_audi.mp4"][k].astype(np.float32) / 255
        ys, xs = slice(690, 1240), slice(270, 820)
        bg[ys, xs] = bg[ys, xs] * (1 - m[ys, xs]) + orig[ys, xs] * m[ys, xs]
    if f >= 447:
        bg = logo_card(bg, f)
    if f >= 470:
        bg = put(bg, T("bio", "LINK IN BIO", F_TITLE, 26, track=6), 540, 1505, "cm", alpha=min(1, (f - 470) / 8))
    bg = footer(bg, f)
    return (np.clip(bg, 0, 1) * 255).astype(np.uint8)


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    rng = range(N)
    if "--only" in sys.argv:
        a, b = sys.argv[sys.argv.index("--only") + 1].split("-")
        rng = range(int(a), int(b) + 1)
    if "--frames" in sys.argv:
        rng = [int(v) for v in sys.argv[sys.argv.index("--frames") + 1].split(",")]
    for f in rng:
        p = f"{out}/f{f:04d}.png"
        if os.path.exists(p) and "--force" not in sys.argv:
            continue
        cv2.imwrite(p, cv2.cvtColor(frame(f), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_PNG_COMPRESSION, 1])
        if f % 30 == 0:
            print("frame", f, flush=True)
