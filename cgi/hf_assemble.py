#!/usr/bin/env python3
"""Assemble the AI (Higgsfield Seedance) version of the Turismo C19R promo. Runs in the Higgsfield sandbox.

Inputs (frame folders at 1920x1080, 25 fps, made by extract.sh in the sandbox):
  fr/book   bookends_c19r.mp4: title 0-63, white bridges 64-67 and 68-72, end card 73-114
  fr/seg1-4 the four video_edit segments, each re-timed to its source duration
  fr/p1-p4  patch shots generated from the C19R photos only (no CGI guide), for the frames where the
            video edit kept the old CGI wheel: line-up, flat wheel, ghost hub, cap close-ups, cap whip
Output: c19r_film.mp4 (868 frames, 34.72 s) muxed with score.mp3 (PCM WAV served under .mp3).
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

D = Path("/home/user/c19r")
FPS, N = 25, 868
cache = {}


def frame(src, i):
    files = cache.setdefault(src, sorted((D / "fr" / src).glob("*.jpg")))
    i = int(round(i))
    p = files[max(0, min(i, len(files) - 1))]
    return np.asarray(Image.open(p).convert("RGB")).astype(np.float32) / 255


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def ramp(t, a, b):
    return smooth((t - a) / (b - a))


WHITE = None


def white():
    global WHITE
    if WHITE is None:
        WHITE = frame("book", 65)
    return WHITE


def pick(f):
    """Return the output image for film frame f."""
    t = f / FPS
    # bookends and bridges
    if f < 64:
        return frame("book", f)
    if 260 <= f < 264:
        return frame("book", 64 + (f - 260))
    if 610 <= f < 615:
        return frame("book", 68 + (f - 610))
    if f >= 826:
        return frame("book", 73 + (f - 826))
    # patches (film frame ranges -> patch frame indices)
    if 64 <= f < 120:                                   # line-up, whips in, fades to white 4.0-4.6 s
        img = frame("p1", f - 64 + 6)
        a = 1 - ramp(t, 4.00, 4.60)
        return img * a + white() * (1 - a)
    if 189 <= f < 213:                                  # gloss flash + flat wheel with whip
        return frame("p3", 60 + (f - 189))
    if 370 <= f < 416:                                  # ghost hub fades in from white
        img = frame("p2", f - 370)
        a = 0.55 * ramp(t, 14.80, 16.64) ** 0.8
        img = img * a + white() * (1 - a)
        return img * 0.82 + np.array([0.165, 0.172, 0.19], np.float32)
    if 477 <= f < 483:                                  # centre-cap close-up in montage A
        return frame("p2", 50 + (f - 477))
    if 505 <= f < 515:                                  # hub flash before the dark hero
        return frame("p2", 75 + (f - 505))
    if 515 <= f < 610:                                  # dark hero: start where the AI clip is clean
        k = (f - 515) / 95
        return frame("seg3", 115 + k * 79)
    if 818 <= f < 826:                                  # whip into the cap
        return frame("p4", 92 + (f - 818))
    # the video-edit segments
    if 64 <= f < 260:
        return frame("seg1", f - 64)
    if 264 <= f < 416:
        return frame("seg2", f - 264)
    if 416 <= f < 610:
        return frame("seg3", f - 416)
    return frame("seg4", f - 615)


def main():
    out = D / "c19r_film.mp4"
    a, b = (int(x) for x in sys.argv[1].split(":")) if len(sys.argv) > 1 else (0, N)
    ff = subprocess.Popen([
        "ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080", "-r", str(FPS),
        "-i", "-", "-i", str(D / "score.mp3"), "-map", "0:v", "-map", "1:a",
        "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for f in range(a, b):
        img = np.clip(pick(f), 0, 1)
        ff.stdin.write((img * 255 + 0.5).astype(np.uint8).tobytes())
    ff.stdin.close()
    ff.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()
