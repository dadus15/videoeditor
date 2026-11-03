#!/usr/bin/env python3
"""Repaint a car's body colour in an AI clip without new generations (e.g. a white car -> a yellow "before" car).

Per frame:
  1. Car mask: CLIPSeg ("a car") unioned with rembg u2net, steadied by an EMA between frames. CLIPSeg keeps the
     body in extreme close-ups, where salient-object models only pick the wheel.
  2. Paint = bright, low-saturation pixels inside the mask. Tyres, carbon, glass (dark), gold and red parts
     (saturated) and hot speculars stay untouched.
  3. Wheel guard: CLIPSeg "a wheel rim", dilated by about 3 % of the frame, so chrome lips and barrels are never
     repainted (colour heuristics fail at sunset, when orange reflections on the paint look like gold).
     Use --guard 0 for shots with no visible custom wheels.
  4. The paint is retinted to --color with its shading and a little of the scene's reflected colour kept.

    python3 recolor_car.py in.mp4 check.jpg --stills 0,40,80            # before/after sheet
    python3 recolor_car.py in.mp4 out.mp4 [--to 95]                      # whole clip (fades back out after --to)

Install (Higgsfield sandbox: PYTHONPATH must be empty, HOME=/home/user):
    python3 -m venv --system-site-packages venv && venv/bin/pip install "rembg[cpu]" transformers
    venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
Speed: about 2 s per 720p frame. Do not set OMP_NUM_THREADS=1 (it stalled three parallel jobs), and kill stray
jobs with pgrep -f "recolor_c[a]r" in a call of its own (a pattern that also matches your shell kills it).
Settings that worked on the MSP02 reel (white -> yellow): FPV close-ups --guard 0 --sat-max 0.6 (sunset
reflections on the paint are warm); shots with gold wheels --sat-max 0.45; stop before the cap macro with --to.
"""
import argparse
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip().split(",")
    num, den = out[2].split("/")
    return int(out[0]), int(out[1]), float(num) / float(den)


def frames(path, w, h):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE)
    n = w * h * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield np.frombuffer(b, np.uint8).reshape(h, w, 3)
    p.stdout.close()


class Painter:
    def __init__(self, color, sat_max=0.38, guard=1.0, prompt="a car", use_u2net=True):
        import torch
        from transformers import CLIPSegForImageSegmentation, CLIPSegProcessor
        self.torch = torch
        self.proc = CLIPSegProcessor.from_pretrained("CIDAS/clipseg-rd64-refined")
        self.seg = CLIPSegForImageSegmentation.from_pretrained("CIDAS/clipseg-rd64-refined").eval()
        self.prompt = prompt
        self.u2 = None
        if use_u2net:
            from rembg import new_session, remove
            self.u2 = (new_session("u2net"), remove)
        self.color = np.array(color, np.float32)
        self.sat_max = sat_max
        self.guard = guard
        self.prev = None

    def car_mask(self, rgb):
        h, w = rgb.shape[:2]
        im = Image.fromarray(rgb)
        with self.torch.no_grad():
            inp = self.proc(text=[self.prompt, "a wheel rim"], images=[im, im], return_tensors="pt", padding=True)
            prob = self.torch.sigmoid(self.seg(**inp).logits).numpy()
        m = cv2.resize(prob[0], (w, h), interpolation=cv2.INTER_LINEAR)
        m = np.clip((m - 0.2) / 0.25, 0, 1)
        wheel = cv2.resize(prob[1], (w, h), interpolation=cv2.INTER_LINEAR)
        self.wheel = np.clip((wheel - 0.25) / 0.2, 0, 1)          # CLIPSeg "a wheel rim": the wheel guard
        if self.u2:
            sess, remove = self.u2
            u = remove(im.resize((w // 2, h // 2)), session=sess, only_mask=True)
            m = np.maximum(m, np.asarray(u.resize((w, h), Image.BILINEAR)).astype(np.float32) / 255)
        m = cv2.GaussianBlur(m, (0, 0), 3)
        if self.prev is not None:
            m = 0.6 * m + 0.4 * self.prev
        self.prev = m
        return m

    def paint(self, rgb, active=1.0):
        x = rgb.astype(np.float32) / 255
        mx, mn = x.max(2), x.min(2)
        sat = (mx - mn) / (mx + 1e-4)
        lum = x @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        w = self.car_mask(rgb)
        w *= np.clip((self.sat_max - sat) / 0.12, 0, 1)
        w *= np.clip((lum - 0.16) / 0.14, 0, 1)
        if self.guard:
            # keep chrome lips and barrels: dilate the wheel map by ~3 % of the frame
            k = max(3, int(min(rgb.shape[:2]) * 0.03) | 1)
            g = cv2.dilate(self.wheel, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
            w *= 1 - cv2.GaussianBlur(g, (0, 0), k / 4)
        spec = np.clip((lum - 0.9) / 0.08, 0, 1)
        tint = self.color[None, None, :] * (lum / 0.82)[..., None]
        warm = x / (lum[..., None] + 1e-4)
        new = tint * (0.75 + 0.25 * warm)
        new = new * (1 - spec[..., None]) + x * spec[..., None]
        out = x * (1 - w[..., None] * active) + np.clip(new, 0, 1) * (w[..., None] * active)
        return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--color", default="1.0,0.76,0.06")
    ap.add_argument("--sat-max", type=float, default=0.38)
    ap.add_argument("--guard", type=float, default=1, help="1 = protect wheels (CLIPSeg wheel map), 0 = off")
    ap.add_argument("--prompt", default="a car")
    ap.add_argument("--no-u2net", action="store_true")
    ap.add_argument("--stills", default="")
    ap.add_argument("--from", dest="f0", type=int, default=0)
    ap.add_argument("--to", dest="f1", type=int, default=10 ** 9, help="last repainted frame; fades out over 6")
    a = ap.parse_args()
    w, h, fps = probe(a.src)
    pt = Painter([float(v) for v in a.color.split(",")], a.sat_max, a.guard, a.prompt, not a.no_u2net)
    if a.stills:
        want = sorted(int(v) for v in a.stills.split(","))
        tiles = []
        for i, fr in enumerate(frames(a.src, w, h)):
            if i in want:
                pt.prev = None
                tiles.append(np.concatenate([fr, pt.paint(fr)], 1))
            if i >= want[-1]:
                break
        Image.fromarray(np.concatenate(tiles, 0)).resize((w // 2, h * len(tiles) // 4)).save(a.out, quality=80)
        print("wrote", a.out)
        return
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                            "-r", str(fps), "-i", "-", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", a.out],
                           stdin=subprocess.PIPE)
    for i, fr in enumerate(frames(a.src, w, h)):
        if i < a.f0 or i > a.f1 + 6:
            enc.stdin.write(fr.tobytes())
            continue
        active = 1.0 if i <= a.f1 else 1 - (i - a.f1) / 6
        enc.stdin.write(pt.paint(fr, active).tobytes())
        if i % 20 == 0:
            print(i, file=sys.stderr, flush=True)
    enc.stdin.close()
    enc.wait()
    print("wrote", a.out)


if __name__ == "__main__":
    main()
