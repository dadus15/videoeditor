"""Find where a clip's frames sit in a master video (normalised grey correlation, 96x54).

    python3 frame_match.py <clip.mp4> <master.mp4> <master_fps_to_scan> <clip_t> [<clip_t> ...]

Prints "src t -> ref t  score s" for each clip time. A score of 0.89+ is a sure match; scan the master at its
own frame rate (25 or 50) for frame accuracy. Use it to replace a low-res screen recording with the same moment
from a 4K/1080p master.
"""
import subprocess
import sys

import numpy as np


def frames(path, fps, w=96, h=54, ss=None, t=None, crop=None):
    vf = (f"crop={crop}," if crop else "") + f"fps={fps},scale={w}:{h},format=gray"
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", str(ss)] if ss is not None else []) + ["-i", path] \
        + (["-t", str(t)] if t else []) + ["-vf", vf, "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)


def norm(a):
    a = a - a.mean(axis=(-1, -2), keepdims=True)
    return a / (np.linalg.norm(a.reshape(len(a), -1), axis=1)[:, None, None] + 1e-6)


src, ref, fps = sys.argv[1], sys.argv[2], float(sys.argv[3])
R = norm(frames(ref, fps))
for t in [float(x) for x in sys.argv[4:]]:
    q = norm(frames(src, 30, ss=t, t=0.04))[0]
    sc = (R * q).sum(axis=(1, 2))
    i = sc.argmax()
    print(f"src {t:.2f} -> ref {i / fps:.2f}  score {sc[i]:.3f}")
