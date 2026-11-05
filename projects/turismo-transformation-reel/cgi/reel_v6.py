"""v6 compositor (runs in the Higgsfield sandbox): 96 fps sources -> 30 fps 1080x1920 film with real slow motion,
speed ramps (PCHIP time keys), digital zoom ramps (exponential in / explosive out) with zoom motion blur, a flat
white-paint hold (push-through transition), measured high-key grade, grain and the end logo.
Sources: /home/user/v6/hf/<name>/%05d.jpg (minterpolate to 96 fps, 720x1280). Run: python3 reel_v6.py full out.mp4
"""
import glob, math, subprocess, sys
import numpy as np
from PIL import Image, ImageFilter

W, H, FPS, DUR, SFPS = 720, 1280, 30, 18.0, 96
HF = "/home/user/v6/hf"


def pchip(keys, x):
    xs = [k[0] for k in keys]; ys = [k[1] for k in keys]; n = len(xs)
    x = min(max(x, xs[0]), xs[-1])
    if n == 2:
        return ys[0] + (ys[1] - ys[0]) * (x - xs[0]) / (xs[1] - xs[0])
    d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(n - 1)]
    m = [d[0]] + [0.0 if d[i - 1] * d[i] <= 0 else 2 / (1 / d[i - 1] + 1 / d[i]) for i in range(1, n - 1)] + [d[-1]]
    i = max(0, min(n - 2, sum(1 for v in xs if v <= x) - 1))
    h = xs[i + 1] - xs[i]; u = (x - xs[i]) / h
    return (2*u**3-3*u**2+1)*ys[i] + (u**3-2*u**2+u)*h*m[i] + (-2*u**3+3*u**2)*ys[i+1] + (u**3-u**2)*h*m[i+1]


GR = {
    "none": dict(gain=1.0, gamma=1.0, sat=1.0, warm=0.0, soft=0.0),
    "w1fix": dict(gain=1.08, gamma=1.30, sat=0.85, warm=-0.02, soft=0.25, sky=True),   # sunset FPV pulled to overcast high-key
    "w1": dict(gain=1.04, gamma=1.08, sat=0.92, warm=-0.01, soft=0.15),
    "w2": dict(gain=1.08, gamma=1.30, sat=0.95, warm=-0.03, soft=0.25),
}

SHOTS = [
    dict(src="vA", t0=0.00, t1=1.04, keys=[[0, 1.6], [1.04, 3.1]], ty=0.12, gr="none"),
    dict(src="vFy", t0=1.04, t1=3.00, keys=[[1.04, 0], [1.75, 2.0], [2.25, 3.0], [2.6, 3.5], [3.0, 4.0]], gr="w1fix", blur=True),
    dict(src="meta", t0=3.00, t1=6.90, keys=[[3.0, 0.15], [6.9, 4.3]], zoom=(1.0, 1.06, 1.0), zc=(0.5, 0.55), gr="w1", blur=True),
    dict(src="meta", t0=6.90, t1=8.45, keys=[[6.9, 4.3], [8.45, 5.0]], zoom=(1.06, 5.5, 2.6), zc=(0.5, 0.60), gr="w1", blur=True, white_out=(8.30, 8.45)),
    dict(src=None, t0=8.45, t1=8.95, color=(0.925, 0.935, 0.95)),
    dict(src="vE", t0=8.95, t1=10.60, keys=[[8.95, 0], [10.6, 2.6]], zoom=(3.2, 1.0, -2.6), zc=(0.5, 0.5), gr="w2", blur=True, white_in=(8.95, 9.08)),
    dict(src="vE", t0=10.60, t1=13.30, keys=[[10.6, 2.6], [13.3, 5.0]], gr="w2", blur=True),
    dict(src="v7", t0=13.30, t1=15.30, keys=[[13.3, 2.3], [15.3, 1.2]], gr="w2"),
    dict(src="v8", t0=15.30, t1=16.22, keys=[[15.3, 1.2], [16.22, 1.66]], zoom=(1.0, 1.05, 1.0), zc=(0.5, 0.5), gr="w2"),
    dict(src="v9", t0=16.22, t1=17.07, keys=[[16.22, 1.4], [17.07, 1.825]], roll=(0, 0.8), gr="w2"),
    dict(src="vA", t0=17.07, t1=18.00, keys=[[17.07, 0.3], [18.0, 1.6]], ty=0.12, gr="none", logo=(17.2, 17.55)),
]

cache = {}


def frame(src, i):
    files = cache.get(src)
    if files is None:
        files = cache[src] = sorted(glob.glob(f"{HF}/{src}/*.jpg"))
    i = max(0, min(int(round(i)), len(files) - 1))
    return Image.open(files[i]).convert("RGB")


def zoom_at(s, t):
    if "zoom" not in s:
        return 1.0
    z0, z1, k = s["zoom"]
    u = min(max((t - s["t0"]) / (s["t1"] - s["t0"]), 0), 1)
    if k > 0:
        f = u ** k                      # exponential ramp-in
    elif k < 0:
        f = 1 - (1 - u) ** (-k)         # explosive ramp-out
    else:
        f = u * u * (3 - 2 * u)
    return math.exp(math.log(z0) + (math.log(z1) - math.log(z0)) * f)


def xform(im, z, cx, cy, roll, ty):
    if abs(z - 1) < 1e-4 and abs(roll) < 1e-4 and abs(ty) < 1e-6:
        return im
    px, py = cx * W, cy * H
    c, s_ = math.cos(math.radians(roll)) / z, math.sin(math.radians(roll)) / z
    a, b, d, e = c, s_, -s_, c
    ox, oy = px, py + ty * H
    tx = px - a * ox - b * oy
    tyy = py - d * ox - e * oy
    return im.transform((W, H), Image.AFFINE, (a, b, tx, d, e, tyy), resample=Image.BICUBIC, fillcolor=(0, 0, 0))


def sample(s, t):
    st = pchip(s["keys"], t)
    z = zoom_at(s, t)
    roll = 0.0
    if "roll" in s:
        u = min(max((t - s["t0"]) / (s["t1"] - s["t0"]), 0), 1)
        roll = s["roll"][0] + (s["roll"][1] - s["roll"][0]) * u
    cx, cy = s.get("zc", (0.5, 0.5))
    im = frame(s["src"], st * SFPS)
    return np.asarray(xform(im, z, cx, cy, roll, s.get("ty", 0.0)), np.float32) / 255, st, z


def grade(x, g):
    p = GR[g]
    if p.get("sky"):
        # pull the sunset oranges (hue 8-42 deg) to a neutral overcast; keep the racing-yellow paint (hue 45-60)
        mx, mn = x.max(2), x.min(2)
        hue = np.degrees(np.arctan2(np.sqrt(3) * (x[..., 1] - x[..., 2]), 2 * x[..., 0] - x[..., 1] - x[..., 2])) % 360
        w = np.clip(1 - np.abs(hue - 25) / 17, 0, 1) * np.clip((mx - mn) / (mx + 1e-4) / 0.25, 0, 1)
        lum = x @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        neutral = np.stack([lum * 0.98, lum, lum * 1.03], -1) * 1.08
        x = x * (1 - w[..., None] * 0.85) + neutral * (w[..., None] * 0.85)
    x = np.clip(x * p["gain"], 0, 1) ** (1 / p["gamma"])
    lum = x @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    x = lum[..., None] + (x - lum[..., None]) * p["sat"]
    x = x * np.array([1 + p["warm"], 1, 1 - p["warm"]], np.float32)
    x = np.clip(x, 0, 1)
    x = 1 - (1 - x) * (1 - 0.04 * np.clip((x - 0.85) / 0.15, 0, 1))    # soft highlight roll-off
    if p["soft"]:
        b = np.asarray(Image.fromarray((x * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
        x = x * (1 - p["soft"]) + b * p["soft"]
    return x


logo = Image.open("/home/user/anim/logo.png").convert("RGBA")
lw = int(0.46 * W); logo = logo.resize((lw, int(lw * logo.height / logo.width)), Image.LANCZOS)
LA = np.asarray(logo, np.float32) / 255
lx, ly = (W - LA.shape[1]) // 2, int(0.2 * H - LA.shape[0] / 2)
rng = np.random.default_rng(3)
GRAIN = [rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(8)]


def render(f):
    t = f / FPS
    s = [x for x in SHOTS if x["t0"] <= t + 1e-6][-1]
    if s["src"] is None:
        yy = (np.linspace(-1, 1, H)[:, None] ** 2 + np.linspace(-1, 1, W)[None, :] ** 2)
        img = np.ones((H, W, 3), np.float32) * np.array(s["color"], np.float32) * (1 - 0.05 * yy[..., None])
    else:
        shutter = 0.75 / FPS
        img, st, z = sample(s, t)
        if s.get("blur"):
            st1 = pchip(s["keys"], t + shutter / 2); st0 = pchip(s["keys"], t - shutter / 2)
            z1, z0 = zoom_at(s, t + shutter / 2), zoom_at(s, t - shutter / 2)
            motion = abs(st1 - st0) * SFPS + abs(math.log(z1 / z0)) * 120
            n = int(min(9, max(1, round(motion))))
            if n > 1:
                acc = np.zeros_like(img)
                for k in range(n):
                    acc += sample(s, t - shutter / 2 + shutter * k / (n - 1))[0]
                img = acc / n
        img = grade(img, s.get("gr", "none"))
        if "white_out" in s:
            a = min(max((t - s["white_out"][0]) / (s["white_out"][1] - s["white_out"][0]), 0), 1)
            img = img * (1 - a) + np.array([0.925, 0.935, 0.95], np.float32) * a
        if "white_in" in s:
            a = 1 - min(max((t - s["white_in"][0]) / (s["white_in"][1] - s["white_in"][0]), 0), 1)
            img = img * (1 - a) + np.array([0.925, 0.935, 0.95], np.float32) * a
        if "logo" in s:
            a0, a1 = s["logo"]; k = min(max((t - a0) / (a1 - a0), 0), 1)
            k = k * k * (3 - 2 * k)
            al = LA[..., 3:4] * k
            hh, ww = LA.shape[:2]
            img[ly:ly + hh, lx:lx + ww] = img[ly:ly + hh, lx:lx + ww] * (1 - al) + LA[..., :3] * al
    g = np.asarray(Image.fromarray(GRAIN[f % 8]).resize((W, H), Image.BILINEAR), np.float32)
    img = img + g[..., None] * 0.006
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "stills":
        ts = [float(x) for x in sys.argv[2].split(",")]
        ims = [Image.fromarray(render(int(round(t * FPS)))).resize((180, 320)) for t in ts]
        g = Image.new("RGB", (180 * len(ims), 320)); [g.paste(im, (i * 180, 0)) for i, im in enumerate(ims)]
        g.save(sys.argv[3], quality=85)
    else:
        out = sys.argv[2]
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-i", "/home/user/anim/score.mp3", "-map", "0:v", "-map", "1:a", "-vf", "scale=1080:1920:flags=lanczos,format=yuv420p",
                              "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-c:a", "aac", "-b:a", "256k", "-t", str(DUR),
                              "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        for f in range(int(DUR * FPS)):
            p.stdin.write(render(f).tobytes())
        p.stdin.close(); p.wait(); print("wrote", out)
