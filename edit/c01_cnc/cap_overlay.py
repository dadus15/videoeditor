#!/usr/bin/env python3
"""Put one identical Turismo centre cap on a wheel in a generated clip.

AI video re-draws the cap logo differently in every shot. This replaces it with a clean cap
rendered from the brand logo, tracked to the wheel hub:
  1. the hub is marked by hand once (centre and cap radius, at the clip's first used frame),
  2. it is followed frame to frame with optical flow on the spokes and lug nuts around it
     (similarity transform: move + scale + roll), refined by a circle fit on the cap edge,
  3. the cap is drawn, lit to the shot (gain), softened to the footage and composited.

Usage (from the project root):
    python3 edit/c01_cnc/cap_overlay.py <in.mp4> <out.mp4> --start S --cx X --cy Y --r R [--gain G] [--sy SY]
"""
import argparse
import subprocess

import cv2
import numpy as np
from PIL import Image

CARD = "assets/brand/turismo_end_card_gemini.jpg"
MARK_BOX = (190, 83, 600, 214)        # the "T" mark (no wordmark) inside the end card's logo
SILVER = np.array([0.80, 0.82, 0.85], np.float32)
RED = np.array([0.78, 0.13, 0.16], np.float32)
TEX = 512
ROLL = False   # parked car: the wheel never turns, so the cap keeps the logo upright (set by --roll)


def mark_rgba():
    """The Turismo T mark cut from the card, re-inked: body silver, the small square red."""
    a = np.asarray(Image.open(CARD).convert("RGB").crop(MARK_BOX)).astype(np.float32) / 255
    ink = 1 - a.min(axis=2)
    alpha = np.clip((ink - 0.25) / 0.45, 0, 1)
    alpha = cv2.GaussianBlur(alpha * alpha * (3 - 2 * alpha), (0, 0), 0.6)
    is_red = (a[..., 0] - a[..., 2]) > 0.25
    col = np.where(is_red[..., None], RED, SILVER)
    ys, xs = np.where(alpha > 0.05)
    alpha, col = alpha[ys.min():ys.max() + 1, xs.min():xs.max() + 1], col[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return col, alpha


def cap_texture():
    """Black satin cap with lathe rings, a thin polished rim and the logo; RGBA float, TEX x TEX."""
    yy, xx = np.mgrid[0:TEX, 0:TEX].astype(np.float32)
    c = (TEX - 1) / 2
    d = np.hypot(xx - c, yy - c) / c                     # 0 centre .. 1 edge
    ang = np.arctan2(yy - c, xx - c)
    base = 0.05 + 0.10 * np.exp(-((xx - c * 0.62) ** 2 + (yy - c * 0.50) ** 2) / (2 * (c * 0.38) ** 2))  # dome sheen
    base = base * (1 - 0.35 * d ** 3)                    # falls off toward the edge like a domed cap
    base = base + 0.006 * np.sin(d * 140)                # fine concentric machining
    rgb = np.repeat(base[..., None], 3, 2) * np.array([0.95, 1.0, 1.08], np.float32)
    rim = (d > 0.93) & (d <= 1.0)
    rim_light = 0.20 + 0.36 * np.clip(-np.sin(ang + 0.6), 0, 1) ** 2   # brighter on the upper left
    rgb[rim] = (rim_light[rim, None] * np.array([0.92, 0.95, 1.0], np.float32))
    rgb[(d > 0.915) & (d <= 0.93)] *= 0.3                 # shadow line inside the rim
    col, alpha = mark_rgba()
    w = int(TEX * 0.62)
    h = int(round(alpha.shape[0] * w / alpha.shape[1]))
    col = cv2.resize(col, (w, h), interpolation=cv2.INTER_AREA)
    alpha = cv2.resize(alpha, (w, h), interpolation=cv2.INTER_AREA)
    x0, y0 = int(c - w / 2), int(c - h / 2)
    region = rgb[y0:y0 + h, x0:x0 + w]
    lit = 0.85 + 0.25 * np.clip(1 - np.hypot(xx[y0:y0 + h, x0:x0 + w] - c * 0.7, yy[y0:y0 + h, x0:x0 + w] - c * 0.6) / c, 0, 1)
    rgb[y0:y0 + h, x0:x0 + w] = region * (1 - alpha[..., None]) + col * lit[..., None] * alpha[..., None]
    a = np.clip((1.0 - d) * c / 1.5, 0, 1)               # anti-aliased disc edge
    return np.dstack([rgb, a]).astype(np.float32)


def read_video(path, start):
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_POS_MSEC, 0)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    return frames, fps, int(round(start * fps))


def refine_circle(gray, cx, cy, r):
    """Snap to the cap edge if a circle of about the right size is found close by."""
    pad = int(r * 1.6)
    x0, y0 = int(max(cx - pad, 0)), int(max(cy - pad, 0))
    roi = cv2.GaussianBlur(gray[y0:int(cy + pad), x0:int(cx + pad)], (5, 5), 1.2)
    cs = cv2.HoughCircles(roi, cv2.HOUGH_GRADIENT, dp=1, minDist=r, param1=80, param2=18,
                          minRadius=int(r * 0.85), maxRadius=int(r * 1.15))
    if cs is None:
        return None
    best = min(cs[0], key=lambda c: np.hypot(c[0] + x0 - cx, c[1] + y0 - cy))
    bx, by, br = best[0] + x0, best[1] + y0, best[2]
    if np.hypot(bx - cx, by - cy) > r * 0.25:
        return None
    return bx, by, br


def track(frames, i0, cx, cy, r):
    """Hub centre, radius and roll for every frame, forwards and backwards from frame i0."""
    n = len(frames)
    out = [None] * n
    out[i0] = (cx, cy, r, 0.0)
    grays = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
    for direction in (1, -1):
        x, y, rr, rot = cx, cy, r, 0.0
        i = i0
        while 0 <= i + direction < n:
            j = i + direction
            mask = np.zeros_like(grays[i])
            cv2.circle(mask, (int(x), int(y)), int(rr * 4.0), 255, -1)
            cv2.circle(mask, (int(x), int(y)), int(rr * 1.15), 0, -1)   # ignore the old cap itself
            p0 = cv2.goodFeaturesToTrack(grays[i], 200, 0.01, 6, mask=mask)
            if p0 is not None and len(p0) >= 6:
                p1, st, _ = cv2.calcOpticalFlowPyrLK(grays[i], grays[j], p0, None, winSize=(21, 21), maxLevel=3)
                good0, good1 = p0[st == 1], p1[st == 1]
                if len(good0) >= 6:
                    M, _ = cv2.estimateAffinePartial2D(good0, good1, method=cv2.RANSAC, ransacReprojThreshold=2.0)
                    if M is not None:
                        s = float(np.hypot(M[0, 0], M[1, 0]))
                        x, y = M @ np.array([x, y, 1.0])
                        rr *= s
                        if ROLL:
                            rot += float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
            snap = refine_circle(grays[j], x, y, rr)
            if snap is not None:                          # gentle pull toward the detected edge
                x, y, rr = 0.6 * x + 0.4 * snap[0], 0.6 * y + 0.4 * snap[1], 0.8 * rr + 0.2 * snap[2]
            out[j] = (x, y, rr, rot)
            i = j
    # light temporal smoothing (removes tracker jitter, keeps real motion)
    arr = np.array(out, np.float64)
    k = np.array([1, 2, 3, 2, 1], np.float64)
    k /= k.sum()
    sm = arr.copy()
    for c in range(4):
        sm[:, c] = np.convolve(np.pad(arr[:, c], 2, mode="edge"), k, mode="valid")
    return sm


def composite(frame, tex, cx, cy, r, rot, sy, gain):
    h, w = frame.shape[:2]
    s = (r * 2) / TEX
    th = np.radians(rot)
    R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
    A = R @ np.diag([s, s * sy])
    c = (TEX - 1) / 2
    t = np.array([cx, cy]) - A @ np.array([c, c])
    M = np.hstack([A, t[:, None]]).astype(np.float32)
    warped = cv2.warpAffine(tex, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    rgb, a = warped[..., :3] * gain, warped[..., 3:4]
    soft = cv2.GaussianBlur(rgb, (0, 0), 0.7)
    img = frame.astype(np.float32) / 255
    img_rgb = img[..., ::-1]
    out = img_rgb * (1 - a) + soft * a
    noise = np.random.default_rng().normal(0, 0.005, out.shape[:2])[..., None] * a
    return (np.clip(out + noise, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp")
    ap.add_argument("out")
    ap.add_argument("--start", type=float, required=True, help="time (s) where cx/cy/r were measured")
    ap.add_argument("--cx", type=float, required=True)
    ap.add_argument("--cy", type=float, required=True)
    ap.add_argument("--r", type=float, required=True, help="cap radius incl. its rim, px")
    ap.add_argument("--sy", type=float, default=1.0, help="vertical squash for a wheel seen at an angle")
    ap.add_argument("--gain", type=float, default=1.0, help="cap brightness to match the shot")
    ap.add_argument("--roll", action="store_true", help="follow the wheel's rotation (only for a turning wheel)")
    ap.add_argument("--preview")
    args = ap.parse_args()
    global ROLL
    ROLL = args.roll

    frames, fps, i0 = read_video(args.inp, args.start)
    snap = refine_circle(cv2.cvtColor(frames[i0], cv2.COLOR_BGR2GRAY), args.cx, args.cy, args.r)
    cx, cy, r = (args.cx, args.cy, args.r) if snap is None else snap
    print(f"start frame {i0}: hand ({args.cx:.0f},{args.cy:.0f},{args.r:.0f}) -> used ({cx:.1f},{cy:.1f},{r:.1f})")
    path = track(frames, i0, cx, cy, r * 1.04)
    tex = cap_texture()
    h, w = frames[0].shape[:2]
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}",
                            "-r", str(fps), "-i", "-", "-i", args.inp, "-map", "0:v", "-map", "1:a?",
                            "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p",
                            "-c:a", "copy", args.out], stdin=subprocess.PIPE)
    for i, f in enumerate(frames):
        x, y, rr, rot = path[i]
        g = composite(f, tex, x, y, rr, rot, args.sy, args.gain)
        enc.stdin.write(g.tobytes())
        if args.preview and i in (0, i0, len(frames) // 2, len(frames) - 1):
            pad = int(rr * 3)
            crop = g[max(int(y) - pad, 0):int(y) + pad, max(int(x) - pad, 0):int(x) + pad]
            cv2.imwrite(f"{args.preview}_{i:03d}.png", cv2.resize(crop, (360, 360)))
    enc.stdin.close()
    enc.wait()
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
