#!/usr/bin/env python3
"""Put the exact Turismo mark on the centre cap of a still keyframe (before it is animated).

Replacing the cap in finished video looks pasted on ("floating cap"). Instead the start frame is
fixed: the generated logo is removed from the cap (inpainting) and the brand mark is drawn in as a
raised silver emblem lit like the rest of the wheel. The video model then animates the wheel with
the correct emblem as part of it.

Usage (from the project root):
    python3 edit/c01_cnc/cap_still.py <in.png> <out.png> --cx X --cy Y --r R [--size 0.62] [--sy 1.0] [--level 0.75]
    (cx, cy, r: approximate cap centre and radius in the image; refined automatically)
"""
import argparse

import cv2
import numpy as np

from cap_overlay import mark_rgba, refine_circle, RED


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp")
    ap.add_argument("out")
    ap.add_argument("--cx", type=float, required=True)
    ap.add_argument("--cy", type=float, required=True)
    ap.add_argument("--r", type=float, required=True)
    ap.add_argument("--size", type=float, default=0.62, help="mark width as a share of the cap diameter")
    ap.add_argument("--sy", type=float, default=1.0, help="vertical squash for a cap seen at an angle")
    ap.add_argument("--level", type=float, default=0.75, help="brightness of the silver emblem")
    ap.add_argument("--debug")
    a = ap.parse_args()

    img = cv2.imread(a.inp)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    snap = refine_circle(gray, a.cx, a.cy, a.r)
    cx, cy, r = (a.cx, a.cy, a.r) if snap is None else snap
    print(f"cap at ({cx:.1f},{cy:.1f}) r={r:.1f}")

    # 1) remove the generated emblem: bright pixels inside the cap face, inpainted from the cap around them
    yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    face = np.hypot(xx - cx, (yy - cy) / a.sy) < r * 0.80
    base = np.median(gray[face])
    old = (face & (gray > base + 18)).astype(np.uint8) * 255
    old = cv2.dilate(old, np.ones((5, 5), np.uint8), iterations=2)
    # rebuild the cap face as a smooth satin surface: a fitted brightness gradient (per channel)
    # from the face pixels that are not emblem, plus the fine grain of the original surface
    keep = face & (old == 0)
    X = np.stack([xx[keep] - cx, yy[keep] - cy, np.ones(keep.sum())], 1).astype(np.float64)
    F = np.stack([xx - cx, yy - cy, np.ones_like(xx)], -1).astype(np.float64)
    fit = np.zeros(img.shape, np.float64)
    for ch in range(3):
        coef, *_ = np.linalg.lstsq(X, img[..., ch][keep].astype(np.float64), rcond=None)
        fit[..., ch] = F @ coef
    rng = np.random.default_rng(1)
    noise = cv2.GaussianBlur(rng.normal(0, 1, img.shape[:2]).astype(np.float32), (0, 0), 0.7)
    noise = noise / noise.std() * 1.6                    # fine satin grain, a couple of levels
    fit += noise[..., None]
    m = np.clip((r * 0.84 - np.hypot(xx - cx, (yy - cy) / a.sy)) / (r * 0.06), 0, 1)[..., None]
    clean = np.clip(img * (1 - m) + fit * m, 0, 255).astype(np.uint8)

    # 2) the brand mark as a raised emblem: silver body (lit from the top left), red square, soft drop shadow
    col, alpha = mark_rgba()
    w = int(round(2 * r * a.size))
    h = int(round(alpha.shape[0] * w / alpha.shape[1] * a.sy))
    col = cv2.resize(col, (w, h), interpolation=cv2.INTER_AREA)
    alpha = cv2.resize(alpha, (w, h), interpolation=cv2.INTER_AREA)
    is_red = np.all(np.abs(col - RED) < 0.05, axis=2)
    gy = np.linspace(1.08, 0.88, h)[:, None]
    gx = np.linspace(1.02, 0.96, w)[None, :]
    silver = np.clip(a.level * gy * gx, 0, 1)
    body = np.dstack([silver * 0.97, silver * 0.99, silver * 1.03])
    body[is_red] = RED * 0.85
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    out = clean.astype(np.float32)[..., ::-1] / 255
    roi = out[y0:y0 + h, x0:x0 + w]
    sh = cv2.GaussianBlur(alpha, (0, 0), max(1.0, r * 0.03))
    shift = max(1, int(round(r * 0.03)))
    sh = np.pad(sh, ((shift, 0), (shift, 0)))[:h, :w]      # drop shadow down-right (no wrap-around)
    roi[:] = roi * (1 - 0.55 * sh[..., None])
    edge = cv2.GaussianBlur(alpha, (0, 0), 0.6)
    roi[:] = roi * (1 - edge[..., None]) + body * edge[..., None]
    res = (np.clip(out, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8)
    cv2.imwrite(a.out, res)
    if a.debug:
        p = int(r * 2.2)
        cv2.imwrite(a.debug, cv2.resize(np.hstack([img[int(cy) - p:int(cy) + p, int(cx) - p:int(cx) + p],
                                                   res[int(cy) - p:int(cy) + p, int(cx) - p:int(cx) + p]]), (840, 420)))


if __name__ == "__main__":
    main()
