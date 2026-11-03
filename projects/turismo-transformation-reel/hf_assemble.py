#!/usr/bin/env python3
"""Plan-driven assembly of an AI promo: AI segments + patch shots + 2D bookends + score -> one master.

Runs anywhere with ffmpeg, numpy and Pillow, in practice the Higgsfield sandbox (sandbox_exec), because that is
where the generated clips can be downloaded when this cloud session's network blocks the Higgsfield CDN.

    python3 hf_assemble.py plan.json --extract        # decode every source to 25 fps frames at the output size
    python3 hf_assemble.py plan.json --stills 70,400,810 --sheet check.jpg   # look at chosen output frames
    python3 hf_assemble.py plan.json --out master.mp4  # encode the whole film and mux the audio

Plan (see templates/hf_plan_turismo_c19r.json):
  fps, frames, size [w, h], workdir, audio (file in workdir)
  sources: name -> {file, retime_to?}   retime_to = source length in seconds the clip must be stretched to
                                        (Seedance returns 24 fps and a slightly shorter clip than its guide)
  white: [source, frame]                frame used as studio white for fades and ghosts
  timeline: ordered entries; a LATER entry overrides an earlier one on the frames it covers, so list the
            base segments first and the patches after them.
     {from, to, src, in}                output frames [from, to) <- source frames in, in+1, ...
     speed: k                           take every k-th source frame (whips)
     span: n                            spread n source frames across the entry (slow a clip down)
     fade_out: [t0, t1]                 dissolve to white between t0 and t1 seconds (film time)
     fade_in: [t0, t1]                  rise from white
     ghost: [t0, t1, peak]              high-key ghost: opacity rises to peak over t0..t1, then cool lift
  overlays (optional): [{file, from, to, cx, cy, width, fade_in: [t0, t1]}]   RGBA image (e.g. the logo)
            composited on output frames [from, to); cx/cy/width as fractions of the frame; fade in film seconds
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def ramp(t, a, b):
    return smooth((t - a) / (b - a))


class Film:
    def __init__(self, plan):
        self.p = plan
        self.fps = plan.get("fps", 25)
        self.w, self.h = plan.get("size", [1920, 1080])
        self.dir = Path(plan.get("workdir", "."))
        self.cache = {}
        self._white = None
        self.overlays = []
        for o in plan.get("overlays", []):
            im = Image.open(self.dir / o["file"]).convert("RGBA")
            w = int(o["width"] * self.w)
            im = im.resize((w, int(w * im.height / im.width)), Image.LANCZOS)
            arr = np.asarray(im).astype(np.float32) / 255
            x0 = int(o["cx"] * self.w - arr.shape[1] / 2)
            y0 = int(o["cy"] * self.h - arr.shape[0] / 2)
            self.overlays.append((o, arr, x0, y0))
        # resolve the entry that owns each frame (later entries win)
        self.owner = [None] * plan["frames"]
        for e in plan["timeline"]:
            for f in range(e["from"], min(e["to"], plan["frames"])):
                self.owner[f] = e
        gaps = [f for f, e in enumerate(self.owner) if e is None]
        if gaps:
            sys.exit(f"timeline leaves frames uncovered: {gaps[:10]}{'...' if len(gaps) > 10 else ''}")

    def extract(self):
        for name, s in self.p["sources"].items():
            out = self.dir / "fr" / name
            out.mkdir(parents=True, exist_ok=True)
            for old in out.glob("*.jpg"):
                old.unlink()
            vf = []
            if s.get("retime_to"):
                dur = float(subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                     str(self.dir / s["file"])], capture_output=True, text=True).stdout)
                vf.append(f"setpts=PTS*{s['retime_to']}/{dur}")
            vf += [f"fps={self.fps}", f"scale={self.w}:{self.h}:flags=lanczos"]
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(self.dir / s["file"]), "-vf", ",".join(vf),
                            "-q:v", "2", str(out / "%04d.jpg")], check=True)
            print(f"{name}: {len(list(out.glob('*.jpg')))} frames")

    def frame(self, src, i):
        files = self.cache.setdefault(src, sorted((self.dir / "fr" / src).glob("*.jpg")))
        if not files:
            sys.exit(f"no frames for source {src}: run --extract first")
        i = max(0, min(int(round(i)), len(files) - 1))
        return np.asarray(Image.open(files[i]).convert("RGB")).astype(np.float32) / 255

    def white(self):
        if self._white is None:
            self._white = self.frame(*self.p["white"])
        return self._white

    def pick(self, f):
        e = self.owner[f]
        t = f / self.fps
        k = f - e["from"]
        if "span" in e:
            idx = e["in"] + k / max(e["to"] - e["from"], 1) * e["span"]
        else:
            idx = e["in"] + k * e.get("speed", 1)
        img = self.frame(e["src"], idx)
        if "fade_out" in e:
            a = 1 - ramp(t, *e["fade_out"])
            img = img * a + self.white() * (1 - a)
        if "fade_in" in e:
            a = ramp(t, *e["fade_in"])
            img = img * a + self.white() * (1 - a)
        if "ghost" in e:
            t0, t1, peak = e["ghost"]
            a = peak * ramp(t, t0, t1) ** 0.8
            img = img * a + self.white() * (1 - a)
            img = img * 0.82 + np.array([0.165, 0.172, 0.19], np.float32)
        for o, arr, x0, y0 in self.overlays:
            if o["from"] <= f < o["to"]:
                k = ramp(t, *o["fade_in"]) if "fade_in" in o else 1.0
                h, w = arr.shape[:2]
                a = arr[..., 3:4] * k
                img = img.copy()
                img[y0:y0 + h, x0:x0 + w] = img[y0:y0 + h, x0:x0 + w] * (1 - a) + arr[..., :3] * a
        return np.clip(img, 0, 1)

    def encode(self, out, crf=17):
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{self.w}x{self.h}",
               "-r", str(self.fps), "-i", "-"]
        audio = self.p.get("audio")
        if audio:
            cmd += ["-i", str(self.dir / audio), "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "256k",
                    "-ar", "48000", "-shortest"]
        cmd += ["-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
                "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                "-movflags", "+faststart", str(out)]
        ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for f in range(self.p["frames"]):
            ff.stdin.write((self.pick(f) * 255 + 0.5).astype(np.uint8).tobytes())
        ff.stdin.close()
        ff.wait()
        print("wrote", out)

    def stills(self, frames, sheet, tile=None):
        tile = tile or ((384, 216) if self.w >= self.h else (216, 384))
        ims = [Image.fromarray((self.pick(f) * 255).astype(np.uint8)).resize(tile) for f in frames]
        cols = min(4 if self.w >= self.h else 6, len(ims))
        rows = (len(ims) + cols - 1) // cols
        g = Image.new("RGB", (tile[0] * cols, tile[1] * rows))
        for i, im in enumerate(ims):
            g.paste(im, ((i % cols) * tile[0], (i // cols) * tile[1]))
        g.save(sheet, quality=80)          # keep under ~500 KiB for sandbox image inspection
        print("wrote", sheet)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--extract", action="store_true")
    ap.add_argument("--stills", default="")
    ap.add_argument("--sheet", default="check.jpg")
    ap.add_argument("--out", default="")
    ap.add_argument("--crf", type=int, default=17)
    args = ap.parse_args()
    film = Film(json.loads(Path(args.plan).read_text()))
    if args.extract:
        film.extract()
    if args.stills:
        film.stills([int(x) for x in args.stills.split(",")], film.dir / args.sheet)
    if args.out:
        film.encode(film.dir / args.out, args.crf)


if __name__ == "__main__":
    main()
