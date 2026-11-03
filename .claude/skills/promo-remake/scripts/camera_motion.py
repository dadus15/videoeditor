#!/usr/bin/env python3
"""Camera-motion fingerprint of a video: per-frame pan (dx, dy), zoom, roll and motion energy, from dense optical
flow fitted to a similarity model (translation + scale + rotation). Use it to compare a remake's camera moves with
the reference's, shot by shot.

    python3 camera_motion.py ref.mp4 out.csv [--fps 25] [--width 256]
    python3 camera_motion.py ref.mp4 out.csv --compare ours.csv        # prints per-window differences

CSV columns: t, dx, dy (px/frame at --width), zoom (% per frame, + = push in), roll (deg/frame), energy, luma
"""
import argparse
import csv
import subprocess
import sys

import numpy as np

try:
    import cv2
except ImportError:  # pragma: no cover
    sys.exit("needs opencv-python-headless")


def frames(path, fps, width):
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip().split(",")
    w0, h0 = int(probe[0]), int(probe[1])
    h = int(round(width * h0 / w0 / 2) * 2)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={fps},scale={width}:{h},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, width), width, h


def fit(flow, w, h):
    ys, xs = np.mgrid[0:h:4, 0:w:4]
    u = flow[0:h:4, 0:w:4, 0].ravel()
    v = flow[0:h:4, 0:w:4, 1].ravel()
    x = (xs.ravel() - w / 2)
    y = (ys.ravel() - h / 2)
    # u = tx + s*x - r*y ; v = ty + s*y + r*x   (least squares, robust-ish by trimming)
    A = np.zeros((2 * len(x), 4))
    A[0::2, 0] = 1; A[0::2, 2] = x; A[0::2, 3] = -y
    A[1::2, 1] = 1; A[1::2, 2] = y; A[1::2, 3] = x
    b = np.empty(2 * len(x)); b[0::2] = u; b[1::2] = v
    p, *_ = np.linalg.lstsq(A, b, rcond=None)
    res = np.abs(A @ p - b)
    keep = res < np.percentile(res, 80)
    p, *_ = np.linalg.lstsq(A[keep], b[keep], rcond=None)
    tx, ty, s, r = p
    return tx, ty, s * 100, np.degrees(r)


def analyse(path, fps=25, width=256):
    fr, w, h = frames(path, fps, width)
    rows = []
    for i in range(1, len(fr)):
        flow = cv2.calcOpticalFlowFarneback(fr[i - 1], fr[i], None, 0.5, 3, 21, 3, 5, 1.1, 0)
        tx, ty, z, r = fit(flow, w, h)
        energy = float(np.median(np.hypot(flow[..., 0], flow[..., 1])))
        rows.append((i / fps, tx, ty, z, r, energy, float(fr[i].mean())))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("csv")
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--width", type=int, default=256)
    ap.add_argument("--compare", default="")
    ap.add_argument("--window", type=float, default=0.5)
    a = ap.parse_args()
    rows = analyse(a.video, a.fps, a.width)
    with open(a.csv, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["t", "dx", "dy", "zoom", "roll", "energy", "luma"])
        for r in rows:
            wr.writerow([f"{v:.4f}" for v in r])
    print(f"{len(rows)} frames -> {a.csv}")
    R = np.array(rows)
    print(" window   dx    dy   zoom%  roll°  energy  luma")
    for t0 in np.arange(0, R[-1, 0], a.window):
        m = (R[:, 0] >= t0) & (R[:, 0] < t0 + a.window)
        if m.any():
            d = R[m].mean(0)
            print(f"{t0:5.1f}  {d[1]:5.1f} {d[2]:5.1f} {d[3]:6.2f} {d[4]:6.2f} {d[5]:6.2f} {d[6]:5.0f}")
    if a.compare:
        O = np.array([[float(x) for x in r] for r in list(csv.reader(open(a.compare)))[1:]])
        print("\n window | ref dx dy zoom roll energy | ours dx dy zoom roll energy")
        for t0 in np.arange(0, min(R[-1, 0], O[-1, 0]), a.window):
            mr = (R[:, 0] >= t0) & (R[:, 0] < t0 + a.window)
            mo = (O[:, 0] >= t0) & (O[:, 0] < t0 + a.window)
            if mr.any() and mo.any():
                r, o = R[mr].mean(0), O[mo].mean(0)
                print(f"{t0:5.1f} | {r[1]:5.1f} {r[2]:5.1f} {r[3]:5.2f} {r[4]:5.2f} {r[5]:5.2f} | "
                      f"{o[1]:5.1f} {o[2]:5.1f} {o[3]:5.2f} {o[4]:5.2f} {o[5]:5.2f}")


if __name__ == "__main__":
    main()
