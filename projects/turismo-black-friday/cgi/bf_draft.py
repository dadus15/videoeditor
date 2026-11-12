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

W, H, FPS, N = 1080, 1920, 30, 540
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
    save=("SAVE UP TO", "€700", "PER SET"),
    onall=("ON ALL", "FORGED SERIES WHEELS"),
    nov=("NOV 23", "THRU", "NOV 30"),
    copyright="© 2026 TURISMO WHEELS",
)

# ---- shot list (film frames at 30 fps; reference = Vossen Short, loop 18.0 s) ---------------------------
# (start, end, kind, args)
SHOTS = [
    (0, 23, "clip", dict(src="show", t=40.0, focus=(0.55, 0.5), push=(1.0, 1.06))),          # A dark wheel, title
    (23, 65, "clip", dict(src="porsche", t=19.1, focus=(0.5, 0.55), push=(1.0, 1.05))),      # B car in smoke, title
    (65, 89, "clip", dict(src="ferrari", t=16.5, focus=(0.5, 0.45), push=(1.05, 1.12))),     # C wheel macro, red line
    (89, 111, "stack", dict()),                                                              # D drop: wheel, red neon
    (111, 122, "split", dict(a=("ferrari", 5.0), b=("ferrari", 19.6))),                      # E two shots split
    (122, 123, "white", dict()),                                                             # F 1-frame white flash
    (123, 135, "spin", dict(img="TR09F", zoom=2.3, c=(0.62, 0.38), rot=(0, -9))),            # G silver closeup
    (135, 155, "clip", dict(src="ferrari", t=21.6, focus=(0.5, 0.45), push=(1.0, 1.04))),    # H car wheel closeup
    (155, 167, "mirror", dict(src="porsche", t=16.6, focus=(0.55, 0.5))),                    # I car, mirrored split
    (167, 178, "clip", dict(src="ferrari", t=25.0, focus=(0.5, 0.4), push=(1.0, 1.04))),     # J low angle, sky
    (178, 203, "collage", dict()),                                                           # K wheels on white
    (203, 213, "bmw", dict(c=(0.258, 0.66), zoom=(1.0, 1.03))),                              # L car side, red line
    (213, 225, "bmw", dict(c=(0.745, 0.64), zoom=(1.12, 1.2))),                              # M car, ON ALL in
    (225, 231, "clip", dict(src="show", t=36.6, focus=(0.5, 0.5), push=(1.0, 1.03))),        # N wheel display
    (231, 240, "sky", dict()),                                                               # O wheel, sky
    (240, 248, "clip", dict(src="show", t=40.8, focus=(0.5, 0.5), push=(1.1, 1.14))),        # P spoke macro
    (248, 257, "clip", dict(src="show", t=21.0, focus=(0.45, 0.5), push=(1.0, 1.03))),       # Q dark wheel
    (257, 270, "clip", dict(src="porsche", t=13.6, focus=(0.5, 0.5), push=(1.0, 1.04))),     # R embers, flames
    (270, 299, "clip", dict(src="porsche", t=8.2, focus=(0.5, 0.55), push=(1.0, 1.06))),     # S engine, machine
    (299, 312, "clip", dict(src="porsche", t=14.1, focus=(0.5, 0.5), push=(1.0, 1.04))),     # T dark motion
    (312, 329, "clip", dict(src="porsche", t=5.6, focus=(0.55, 0.45), push=(1.0, 1.03))),    # U car on airfield
    (329, 346, "row", dict()),                                                               # V three wheels, mirror
    (346, 375, "swap", dict()),                                                              # W product swaps, box
    (375, 389, "clip", dict(src="show", t=26.6, focus=(0.5, 0.5), push=(1.0, 1.05))),        # X dark car, NOV types
    (389, 395, "clip", dict(src="porsche", t=15.0, focus=(0.5, 0.5), push=(1.0, 1.1), whip=True)),  # Y whip
    (395, 425, "clip", dict(src="show", t=37.0, focus=(0.5, 0.5), push=(1.0, 1.05))),        # Z wheel display
    (425, 447, "clip", dict(src="ferrari", t=13.2, focus=(0.5, 0.45), push=(1.0, 1.04))),    # AA car, sunset
    (447, 540, "clip", dict(src="show", t=14.0, focus=(0.5, 0.5), push=(1.0, 1.04))),        # AB people, final card
]

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
        fr = clip_frames(a["src"], a["t"], n)[i]
        z = lerp(*a.get("push", (1, 1)), u)
        img = cover(fr, a["focus"], z, AREA[a["src"]]).astype(np.float32) / 255
        if a.get("whip"):
            k = 61
            ker = np.zeros((k, k), np.float32)
            ker[k // 2] = 1 / k
            img = cv2.filter2D(img, -1, ker)
        return img
    if kind == "split":
        top = cover(clip_frames(*a["a"], n)[i], (0.5, 0.45), 1.0, AREA["ferrari"])
        bot = cover(clip_frames(*a["b"], n)[i], (0.5, 0.45), 1.0, AREA["ferrari"])
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
            nz = cv2.resize(rng.random((24, 14)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
            nz = cv2.GaussianBlur(nz, (0, 0), 40)
            nz = np.clip((nz - 0.45) * 3, 0, 1)[..., None]
            sky = vgrad((0.20, 0.55, 0.60), (0.55, 0.78, 0.80))
            _rend["sky"] = sky * (1 - nz) + nz * 0.97
        bg = _rend["sky"].copy()
        bg[1150:, 515:565] = (0.25, 0.25, 0.27)
        return paste(bg, rend("TR02A", int(lerp(900, 940, u))), 540, 820)
    if kind == "row":                                     # three wheels on a black mirror floor
        bg = vgrad((0.02, 0.02, 0.02), (0.06, 0.06, 0.07))
        pan = lerp(30, -30, u)
        for k, s, cx, cy in [("TR02A", 420, 230, 900), ("TR02A", 560, 520, 940), ("TR02A", 760, 860, 1000)]:
            r = rend(k, s)
            paste(bg, r, cx + pan, cy)
            ref = r[::-1].copy()
            ref[..., 3] *= np.linspace(0.35, 0, ref.shape[0])[:, None]
            paste(bg, ref, cx + pan, cy + r.shape[0] * 0.98)
        return bg
    if kind == "swap":                                    # finishes swap every 3 frames on white
        bg = np.ones((H, W, 3), np.float32)
        seq = ["TR09F", "TR02F", "X03", "TR02A", "TR09F", "TR02F", "X03", "TR02S", "TR09F", "TR02F"]
        k = seq[min(i // 3, len(seq) - 1)]
        return paste(bg, rend(k, int(lerp(880, 940, u))), 540, 900)
    raise ValueError(kind)


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
    put(lay, s2, 245 + s2.shape[1] / 2, 1060, "cm")
    put(lay, s3, 245 + s2.shape[1] + 18, 1128, "lb")
    if f < 77:                                            # reveal from the line at y=960
        r = ease((f - 71) / 6) * 320
        rows = np.abs(np.arange(H) - 960) > r
        lay[rows, 3] = 0
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
    return put(bg, _logo, 540, 1760, "cm", alpha=0.9)


def red_lines(bg, f):
    if 64 <= f <= 71:                                     # diagonal sweep that settles horizontal (C)
        u = ease((f - 64) / 7)
        y_left = lerp(250, 960, u)
        y_right = lerp(1650, 960, u)
        bg = line(bg, (0, int(y_left)), (W, int(y_right)), RED, 6)
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


def frame(f):
    for s, e, kind, a in SHOTS:
        if s <= f < e:
            bg = shot_frame(kind, a, f - s, e - s)
            break
    bg = np.ascontiguousarray(bg, np.float32)
    if f < 65:
        bg = hud(bg, f)
    bg = red_lines(bg, f)
    if 71 <= f < 178:
        bg = save_block(bg, f)
    if 214 <= f < 325:
        bg = onall_block(bg, f)
    bg = nov_block(bg, f)
    if f >= 447:
        bg = logo_card(bg, f)
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
