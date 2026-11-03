#!/usr/bin/env python3
"""Pro finishing for AI-generated shots: smooth speed ramps, speed-dependent motion blur, real whip / zoom / spin
transitions on the beat, drone micro-shake, one filmic grade (tone curve, desaturated hot hues, halation, grain,
vignette, slight lens CA) and logo overlays. Turns obviously-AI clips into an edited commercial.

Why: assembling AI clips by dropping or duplicating frames (24 -> 25 fps, 1.5x / 2x) makes motion judder. Plain
cuts and white flashes look cheap, and every clip carries its own over-saturated "AI" colour. This fixes all three.

Input: each clip pre-interpolated to a high frame rate (e.g. 96 fps JPEG folders via ffmpeg minterpolate), so any
speed ramp samples real in-between frames:
    ffmpeg -i v3.mp4 -vf "minterpolate=fps=96:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,scale=1080:1920" hf/v3/%04d.jpg

Plan JSON (see templates/reel_finish_turismo_msp02.json):
  fps (output, e.g. 30), duration (s), size [w, h], src_fps (96), workdir, audio, frames_dir ("hf")
  shots: [{src, t, dur, src_in, src_out, ease, shake, blur, cam}]   t/dur = place in the film (s);
         src_in/src_out = source seconds consumed (src_out < src_in plays backwards, equal values hold a frame);
         ease = linear|in|out|inout|ramp (fast-slow-fast)
         shake = drone micro-shake in px; blur = shutter (0.5 = 180 degrees, scaled by speed)
         cam = digital camera move over the shot: {zoom: [a, b], pan: [[x0, y0], [x1, y1]] (fractions of the frame),
               roll: [a, b] (deg), ease}  e.g. a slow pan right on a still close-up to match the reference
  transitions: [{t, type: whip_h|whip_v|zoom|spin|impact, frames, strength}]   centred on the cut at t
  grade: {sat, hot_sat, contrast, lift, warmth, halation, grain, vignette, ca}
  overlays: [{file, t0, t1, fade, cx, cy, width}]
Usage:  python3 reel_finish.py plan.json --stills 1.5,5,9 --sheet s.jpg      python3 reel_finish.py plan.json --out x.mp4
"""
import argparse
import json
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

EASE = {
    "linear": lambda u: u,
    "in": lambda u: u ** 1.8,
    "out": lambda u: 1 - (1 - u) ** 1.8,
    "inout": lambda u: u * u * (3 - 2 * u),
    "ramp": lambda u: 0.5 + 0.5 * math.copysign(abs(2 * u - 1) ** 0.55, 2 * u - 1),   # fast-slow-fast
}


class Finisher:
    def __init__(self, plan):
        self.p = plan
        self.fps = plan.get("fps", 30)
        self.w, self.h = plan["size"]
        self.dir = Path(plan["workdir"])
        self.sfps = plan.get("src_fps", 96)
        self.fdir = self.dir / plan.get("frames_dir", "hf")
        self.files = {}
        self.cache = {}
        self.n = int(round(plan["duration"] * self.fps))
        g = plan.get("grade", {})
        self.g = dict(sat=0.9, hot_sat=0.78, contrast=0.12, lift=0.02, warmth=0.0, halation=0.10,
                      grain=0.018, vignette=0.22, ca=1.0)
        self.g.update(g)
        yy, xx = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        r = np.hypot((xx - self.w / 2) / (self.w / 2), (yy - self.h / 2) / (self.h / 2)) / math.sqrt(2)
        self.vig = (1 - self.g["vignette"] * np.clip(r, 0, 1) ** 2)[..., None]
        rng = np.random.default_rng(5)
        self.grain = [rng.normal(0, 1, (self.h // 2, self.w // 2)).astype(np.float32) for _ in range(6)]
        self.overlays = []
        for o in plan.get("overlays", []):
            im = Image.open(self.dir / o["file"]).convert("RGBA")
            ww = int(o["width"] * self.w)
            im = im.resize((ww, int(ww * im.height / im.width)), Image.LANCZOS)
            arr = np.asarray(im).astype(np.float32) / 255
            self.overlays.append((o, arr, int(o["cx"] * self.w - arr.shape[1] / 2), int(o["cy"] * self.h - arr.shape[0] / 2)))

    # ---------------------------------------------------------------- sources
    def src(self, name, t):
        files = self.files.setdefault(name, sorted((self.fdir / name).glob("*.jpg")))
        i = max(0, min(int(round(t * self.sfps)), len(files) - 1))
        key = (name, i)
        if key not in self.cache:
            if len(self.cache) > 48:
                self.cache.pop(next(iter(self.cache)))
            im = Image.open(files[i]).convert("RGB")
            if im.size != (self.w, self.h):
                im = im.resize((self.w, self.h), Image.LANCZOS)
            self.cache[key] = np.asarray(im).astype(np.float32) / 255
        return self.cache[key]

    def shot_at(self, t):
        cur = None
        for s in self.p["shots"]:
            if s["t"] <= t + 1e-6:
                cur = s
        return cur

    def src_time(self, s, t):
        u = min(max((t - s["t"]) / s["dur"], 0.0), 1.0)
        return s["src_in"] + (s["src_out"] - s["src_in"]) * EASE[s.get("ease", "linear")](u)

    def render_shot(self, s, t):
        """Source frame(s) for film time t with speed-dependent motion blur."""
        ts = self.src_time(s, t)
        dt = 1.0 / self.fps
        speed = abs(self.src_time(s, min(t + dt / 2, s["t"] + s["dur"])) - self.src_time(s, max(t - dt / 2, s["t"]))) / dt
        shutter = s.get("blur", 0.5) * speed / self.fps          # source seconds the shutter stays open
        k = int(min(12, max(1, round(shutter * self.sfps))))
        if k <= 1:
            img = self.src(s["src"], ts)
        else:
            img = sum(self.src(s["src"], ts + (j / (k - 1) - 0.5) * shutter) for j in range(k)) / k
        if s.get("cam"):
            c = s["cam"]
            u = EASE[c.get("ease", "inout")](min(max((t - s["t"]) / s["dur"], 0.0), 1.0))
            z0, z1 = c.get("zoom", [1.0, 1.0])
            (px0, py0), (px1, py1) = c.get("pan", [[0, 0], [0, 0]])
            r0, r1 = c.get("roll", [0.0, 0.0])
            img = self.affine(img, z0 + (z1 - z0) * u, r0 + (r1 - r0) * u,
                              (px0 + (px1 - px0) * u) * self.w, (py0 + (py1 - py0) * u) * self.h)
        if s.get("shake"):
            img = self.shake(img, t, s["shake"])
        return img

    def shake(self, img, t, amp):
        dx = amp * (math.sin(t * 7.1) * 0.6 + math.sin(t * 13.7 + 1.3) * 0.4)
        dy = amp * (math.sin(t * 5.3 + 0.7) * 0.6 + math.sin(t * 11.9 + 2.1) * 0.4)
        rot = amp * 0.04 * math.sin(t * 6.1 + 0.4)
        return self.affine(img, 1.0 + amp * 0.004, rot, dx, dy)

    def affine(self, img, scale, rot_deg, dx, dy):
        im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
        c, sn = math.cos(math.radians(rot_deg)) / scale, math.sin(math.radians(rot_deg)) / scale
        cx, cy = self.w / 2, self.h / 2
        a, b = c, sn
        d, e = -sn, c
        tx = cx - a * (cx + dx) - b * (cy + dy)
        ty = cy - d * (cx + dx) - e * (cy + dy)
        out = im.transform((self.w, self.h), Image.AFFINE, (a, b, tx, d, e, ty), resample=Image.BICUBIC)
        return np.asarray(out).astype(np.float32) / 255

    # ------------------------------------------------------------ transitions
    def transition(self, img, t):
        for tr in self.p.get("transitions", []):
            half = tr.get("frames", 6) / 2 / self.fps
            x = (t - tr["t"]) / half
            if abs(x) >= 1:
                continue
            w = (1 - abs(x)) ** 1.5 * tr.get("strength", 1.0)
            typ = tr["type"]
            if typ in ("whip_h", "whip_v"):
                img = self.dir_blur(img, int(160 * w), horizontal=(typ == "whip_h"))
            elif typ == "zoom":
                img = self.zoom_blur(img, 0.18 * w)
                img = img * (1 + 0.25 * w)
            elif typ == "spin":
                img = self.spin_blur(img, 14 * w)
                img = self.zoom_blur(img, 0.12 * w)
                img = img * (1 + 0.35 * w)
            elif typ == "impact" and x >= 0:
                img = self.affine(img, 1 + 0.05 * w, 0, 0, 0)
        return img

    def dir_blur(self, img, px, horizontal=True):
        if px < 2:
            return img
        im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
        small = im.resize((self.w // 4, self.h // 4), Image.BILINEAR)
        arr = np.asarray(small).astype(np.float32)
        k = max(1, px // 4)
        acc = np.zeros_like(arr)
        for o in range(-k, k + 1):
            acc += np.roll(arr, o, axis=1 if horizontal else 0)
        acc /= (2 * k + 1)
        out = Image.fromarray(np.clip(acc, 0, 255).astype(np.uint8)).resize((self.w, self.h), Image.BICUBIC)
        return np.asarray(out).astype(np.float32) / 255

    def zoom_blur(self, img, amount, steps=7):
        if amount < 0.005:
            return img
        acc = np.zeros_like(img)
        for j in range(steps):
            acc += self.affine(img, 1 + amount * j / (steps - 1), 0, 0, 0)
        return acc / steps

    def spin_blur(self, img, deg, steps=7):
        if deg < 0.5:
            return img
        acc = np.zeros_like(img)
        for j in range(steps):
            acc += self.affine(img, 1.02, deg * (j / (steps - 1) - 0.5), 0, 0)
        return acc / steps

    # ------------------------------------------------------------------ grade
    def grade(self, img, f):
        g = self.g
        lum = img @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        # pull back the AI over-saturation, more on hot oranges/yellows
        mx, mn = img.max(2), img.min(2)
        sat = (mx - mn)
        hot = np.clip((img[..., 0] - img[..., 2]) * 2, 0, 1) * np.clip(sat * 2, 0, 1)
        s = g["sat"] * (1 - hot * (1 - g["hot_sat"] / max(g["sat"], 1e-6)))
        img = lum[..., None] + (img - lum[..., None]) * s[..., None]
        # filmic S-curve with lifted blacks
        c = g["contrast"]
        img = img + c * (img - 0.5) * (1 - np.abs(2 * img - 1))
        img = g["lift"] + img * (1 - g["lift"])
        if g["warmth"]:
            img = img * np.array([1 + g["warmth"], 1, 1 - g["warmth"]], np.float32)
        # halation: warm glow around highlights
        if g["halation"]:
            hi = np.clip((lum - 0.72) / 0.28, 0, 1)
            small = Image.fromarray((hi * 255).astype(np.uint8)).resize((self.w // 8, self.h // 8), Image.BILINEAR)
            glow = small.filter(ImageFilter.GaussianBlur(6)).resize((self.w, self.h), Image.BICUBIC)
            glow = np.asarray(glow).astype(np.float32)[..., None] / 255
            img = img + glow * g["halation"] * np.array([1.0, 0.75, 0.55], np.float32)
        # lens: slight lateral CA toward the edges
        if g["ca"]:
            sh = int(round(g["ca"]))
            img[..., 0] = np.roll(img[..., 0], sh, axis=1)
            img[..., 2] = np.roll(img[..., 2], -sh, axis=1)
        img = img * self.vig
        gr = self.grain[f % len(self.grain)]
        gr = np.asarray(Image.fromarray(gr).resize((self.w, self.h), Image.BILINEAR))
        img = img + gr[..., None] * g["grain"] * (0.6 + 0.4 * (1 - lum[..., None]))
        return np.clip(img, 0, 1)

    def frame(self, f):
        t = f / self.fps
        s = self.shot_at(t)
        img = self.render_shot(s, t)
        img = self.transition(img, t)
        img = self.grade(np.clip(img, 0, 1), f)
        for o, arr, x0, y0 in self.overlays:
            if o["t0"] <= t < o["t1"]:
                a0, a1 = o.get("fade", [o["t0"], o["t0"]])
                k = 1.0 if a1 <= a0 else min(max((t - a0) / (a1 - a0), 0), 1)
                k = k * k * (3 - 2 * k)
                hh, ww = arr.shape[:2]
                a = arr[..., 3:4] * k
                img[y0:y0 + hh, x0:x0 + ww] = img[y0:y0 + hh, x0:x0 + ww] * (1 - a) + arr[..., :3] * a
        return img

    def encode(self, out, crf=16):
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{self.w}x{self.h}",
               "-r", str(self.fps), "-i", "-"]
        if self.p.get("audio"):
            cmd += ["-i", str(self.dir / self.p["audio"]), "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "256k",
                    "-ar", "48000", "-shortest"]
        cmd += ["-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-tune", "grain",
                "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart", str(out)]
        ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for f in range(self.n):
            ff.stdin.write((self.frame(f) * 255 + 0.5).astype(np.uint8).tobytes())
        ff.stdin.close()
        ff.wait()
        print("wrote", out)

    def stills(self, times, sheet):
        tile = (216, 384) if self.h > self.w else (384, 216)
        ims = [Image.fromarray((self.frame(int(round(t * self.fps))) * 255).astype(np.uint8)).resize(tile) for t in times]
        cols = min(6, len(ims))
        g = Image.new("RGB", (tile[0] * cols, tile[1] * ((len(ims) + cols - 1) // cols)))
        for i, im in enumerate(ims):
            g.paste(im, ((i % cols) * tile[0], (i // cols) * tile[1]))
        g.save(self.dir / sheet, quality=80)
        print("wrote", sheet)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--stills", default="")
    ap.add_argument("--sheet", default="finish_check.jpg")
    ap.add_argument("--out", default="")
    ap.add_argument("--crf", type=int, default=16)
    a = ap.parse_args()
    fin = Finisher(json.loads(Path(a.plan).read_text()))
    if a.stills:
        fin.stills([float(x) for x in a.stills.split(",")], a.sheet)
    if a.out:
        fin.encode(fin.dir / a.out, a.crf)


if __name__ == "__main__":
    main()
