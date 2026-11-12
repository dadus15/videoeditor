#!/usr/bin/env python3
"""Render a 9:16 short from STILL images (product renders, campaign stills), configured by an EDL.

Same house style as compose.py (window over a dark blurred duplicate, DM Sans titles, film grain),
but each shot is a still that is given life by a sub-pixel virtual camera:

  keys   camera keyframes per shot: [{"t": 0, "c": [x, y], "z": 1.7}, {"t": 0.8, ..., "ease": "out_expo"},
         {"t": "end", ...}] -- c is the source point at the window centre, z = output px per source px.
         Zoom is interpolated geometrically, so pushes feel even. A big z -> small z key on the drop is
         the stills version of the aperture reveal (detail -> whole product).
  valid  [x0, y0, x1, y1] usable source rect (crops off baked logos, screenshot borders, page counters).

Optional pieces (EDL keys):
  logo     {"image", "box": [x0,y0,x1,y1], "y": centre_y, "scale"} -- light-on-dark logo cut from a still,
           matted by its own brightness and shown static at the top; fades out with the iris.
  outro    {"card", "card_wheel": [cx,cy,r], "card_cap": r, "hub_cap": r_src, "hub": [x,y],
            "lead", "iris", "hold"} -- iris opening from the last shot's centre cap into the end card
           (card zooms through its own hub 2.2x -> 1x), one light sweep, hold.

Run from the project root:
  python3 .claude/skills/youtube-edit/scripts/compose_stills.py edit/edl_x.json renders/x.mp4 [--bpm 120]
          [--crf 18] [--audio mix.wav] [--preview-every N --preview-dir work/preview]
Writes <out>.timeline.json with cue points for mix_audio.py.
"""
import argparse, json, math, subprocess, sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compose as C  # noqa: E402

ROOT = Path.cwd()


def load_rgb(path):
    return np.asarray(Image.open(ROOT / path).convert("RGB")).astype(np.float32) / 255


def interp_keys(keys, t, dur):
    """Camera (cx, cy, z) at shot-relative time t."""
    ks = [dict(k, t=(dur if k["t"] == "end" else float(k["t"]))) for k in keys]
    if t <= ks[0]["t"]:
        k = ks[0]
        return k["c"][0], k["c"][1], k["z"]
    for a, b in zip(ks, ks[1:]):
        if t <= b["t"]:
            u = C.EASE[b.get("ease", "in_out_sine")](C.clamp01((t - a["t"]) / max(1e-6, b["t"] - a["t"])))
            z = math.exp(C.lerp(math.log(a["z"]), math.log(b["z"]), u))
            return C.lerp(a["c"][0], b["c"][0], u), C.lerp(a["c"][1], b["c"][1], u), z
    k = ks[-1]
    return k["c"][0], k["c"][1], k["z"]


def crop_rect(shot, cx, cy, z, win_w, win_h):
    """Source rect shown in the window, kept inside the valid area (z raised if needed)."""
    x0, y0, x1, y1 = shot["valid"]
    z = max(z, win_w / (x1 - x0), win_h / (y1 - y0))
    cw, ch = win_w / z, win_h / z
    cx = min(max(cx, x0 + cw / 2), x1 - cw / 2)
    cy = min(max(cy, y0 + ch / 2), y1 - ch / 2)
    return cx - cw / 2, cy - ch / 2, z


def sample(img, x0, y0, z, w, h, sharpen):
    M = np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]])
    out = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
    if sharpen > 0:
        blur = cv2.GaussianBlur(out, (0, 0), 1.6)
        out = out + sharpen * (out - blur)
    return np.clip(out, 0, 1)


def feather_mask(h, w, top, bottom, side):
    yy = np.arange(h, dtype=np.float32)[:, None]
    xx = np.arange(w, dtype=np.float32)[None, :]
    m = np.ones((h, w), np.float32)
    if top:
        m *= np.clip(yy / top, 0, 1)
    if bottom:
        m *= np.clip((h - 1 - yy) / bottom, 0, 1)
    if side:
        m *= np.clip(xx / side, 0, 1) * np.clip((w - 1 - xx) / side, 0, 1)
    m = m * m * (3 - 2 * m)
    return m[..., None]


def light_logo(cfg):
    """White/red logo on black -> RGBA matted by brightness (keeps the artwork's own colours)."""
    img = load_rgb(cfg["image"])
    x0, y0, x1, y1 = cfg["box"]
    a = img[y0:y1, x0:x1]
    alpha = np.clip((a.max(axis=2) - 0.08) / 0.55, 0, 1)
    alpha = alpha * alpha * (3 - 2 * alpha)
    rgb = np.clip(a / np.maximum(a.max(axis=2, keepdims=True), 1e-3), 0, 1)
    rgba = np.dstack([rgb, alpha]).astype(np.float32)
    s = cfg.get("scale", 1.0)
    if s != 1.0:
        rgba = cv2.resize(rgba, (round(rgba.shape[1] * s), round(rgba.shape[0] * s)), interpolation=cv2.INTER_LANCZOS4)
        rgba = np.clip(rgba, 0, 1)
    return rgba


def card_canvas(path, wheel, W, H):
    card = load_rgb(path)
    s = max(W / card.shape[1], H / card.shape[0])
    big = cv2.resize(card, (round(card.shape[1] * s), round(card.shape[0] * s)), interpolation=cv2.INTER_LANCZOS4)
    oy, ox = (big.shape[0] - H) // 2, (big.shape[1] - W) // 2
    cx, cy, r = wheel
    return np.clip(big[oy:oy + H, ox:ox + W], 0, 1), (cx * s - ox, cy * s - oy, r * s), s


def warp_scale(img, s, c_src, c_dst, W, H, fill=1.0):
    M = np.float32([[s, 0, c_dst[0] - s * c_src[0]], [0, s, c_dst[1] - s * c_src[1]]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                          borderValue=(fill, fill, fill))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edl")
    ap.add_argument("out")
    ap.add_argument("--bpm", type=float)
    ap.add_argument("--audio")
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--grain", type=float, default=0.010)
    ap.add_argument("--preview-every", type=int, default=0)
    ap.add_argument("--preview-dir", default="work/preview")
    ap.add_argument("--frames", help="only render these comma-separated frame numbers as PNG stills to --preview-dir")
    args = ap.parse_args()

    edl = json.loads(Path(args.edl).read_text())
    bpm = args.bpm or edl["bpm"]
    fps = edl["fps"]
    Wc, Hc = edl["size"]
    shots, film_len, beat = C.build_timeline(edl, bpm)
    imgs = {s["image"]: load_rgb(s["image"]) for s in shots}
    events = C.text_events(edl, shots, beat)
    L = edl["window"]
    ww, wh = L["w"], L["h"]
    wx0, wy0 = int(round(L["cx"] - ww / 2)), int(round(L["cy"] - wh / 2))
    fmask = feather_mask(wh, ww, L.get("feather_top", 0), L.get("feather_bottom", 0), L.get("feather_side", 0))
    vig = C.vignette(wh, ww, 0.12)

    logo = light_logo(edl["logo"]) if "logo" in edl else None
    o = edl.get("outro")
    if o:
        card, (ccx, ccy, cr), card_s = card_canvas(o["card"], o["card_wheel"], Wc, Hc)
        card_cap = o["card_cap"] * card_s
        iris_start = film_len - o.get("lead", 0.45)
        IRIS, HOLD = o.get("iris", 0.8), o.get("hold", 2.7)
        total = iris_start + IRIS + HOLD
    else:
        total = film_len
        iris_start = None
    nframes = int(round(total * fps))
    print(f"bpm {bpm}  beat {beat:.3f}s  film {film_len:.3f}s  total {total:.3f}s  frames {nframes}", file=sys.stderr)
    for s in shots:
        print(f"  {s['start']:6.3f}-{s['end']:6.3f}  {s['name']:24s} {Path(s['image']).name}", file=sys.stderr)

    def film_frame(T):
        """Composited film frame at time T (clamped to the last shot) + hub screen position of that shot."""
        si = 0
        while si < len(shots) - 1 and T >= shots[si]["end"] - 1e-9:
            si += 1
        shot = shots[si]
        t = min(T - shot["start"], shot["dur"])
        cx, cy, z = interp_keys(shot["keys"], t, shot["dur"])
        x0, y0, z = crop_rect(shot, cx, cy, z, ww, wh)
        sharp = 0.10 + 0.14 * C.clamp01((z - 1.0) / 0.8)
        win = sample(imgs[shot["image"]], x0, y0, z, ww, wh, sharp)
        win = C.grade(win, shot.get("grade", {})) * vig
        canvas = C.background(win, Wc, Hc)
        reg = canvas[wy0:wy0 + wh, wx0:wx0 + ww]
        canvas[wy0:wy0 + wh, wx0:wx0 + ww] = reg * (1 - fmask) + win * fmask
        hub = None
        if "hub" in shot:
            hub = (wx0 + (shot["hub"][0] - x0) * z, wy0 + (shot["hub"][1] - y0) * z, z)
        return canvas, hub

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    pdir = Path(args.preview_dir)
    if args.preview_every or args.frames:
        pdir.mkdir(parents=True, exist_ok=True)
    only = [int(x) for x in args.frames.split(",")] if args.frames else None
    enc = None
    if only is None:
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{Wc}x{Hc}",
               "-r", str(fps), "-i", "-"]
        if args.audio:
            cmd += ["-i", args.audio]
        cmd += ["-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
                "-c:v", "libx264", "-preset", "slow", "-crf", str(args.crf), "-profile:v", "high",
                "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
                "-movflags", "+faststart"]
        cmd += (["-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest"] if args.audio else ["-an"]) + [str(out)]
        enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    rng = np.random.default_rng(7)
    yy, xx = np.mgrid[0:Hc, 0:Wc].astype(np.float32)
    LOGO_Y = edl["logo"].get("y", 120) if logo is not None else 0

    for f in (only if only is not None else range(nframes)):
        T = f / fps
        if o and T >= iris_start + IRIS:                         # end card hold: slow push + one light sweep
            h = T - iris_start - IRIS
            zz = 1 + 0.025 * C.EASE["in_out_sine"](C.clamp01(h / HOLD))
            canvas = warp_scale(card, zz, (ccx, ccy), (ccx, ccy), Wc, Hc)
            p = C.EASE["in_out_sine"](C.clamp01((h - 0.25) / 1.1))
            if 0 < p < 1:
                band = (xx + 0.55 * yy) - (-600 + p * (Wc + 0.55 * Hc + 1200))
                glow = np.exp(-(band / 70) ** 2) * 0.55
                glow *= np.exp(-((np.hypot(xx - ccx, yy - ccy) - cr * 0.6) / (cr * 0.55)) ** 2)
                canvas = 1 - (1 - canvas) * (1 - glow[..., None])
            grain = False
        else:
            canvas, hub = film_frame(T)
            C.draw_texts(canvas, events, T, Wc)
            if logo is not None:
                la = 1.0
                if o and T > iris_start:
                    la = 1 - C.EASE["out_cubic"](C.clamp01((T - iris_start) / 0.35))
                C.blit(canvas, logo, Wc / 2 - logo.shape[1] / 2, LOGO_Y - logo.shape[0] / 2, la)
            grain = True
            if o and T >= iris_start:                             # iris from the centre cap into the card
                u = (T - iris_start) / IRIS
                k = C.EASE["in_out_cubic"](u)
                hx, hy, hz = hub
                sc0 = max(2.2, o["hub_cap"] * hz / card_cap)      # card cap starts at least as big as the film's
                sc = sc0 ** (1 - C.EASE["out_cubic"](u))
                cxy = (C.lerp(hx, ccx, k), C.lerp(hy, ccy, k))
                cimg = warp_scale(card, sc, (ccx, ccy), cxy, Wc, Hc)
                r0, r1 = o["hub_cap"] * hz * 1.04, math.hypot(Wc, Hc)
                R = r0 * (r1 / r0) ** k
                d = np.sqrt((xx - cxy[0]) ** 2 + (yy - cxy[1]) ** 2)
                m = np.clip((R - d) / 6.0 + 0.5, 0, 1)[..., None]
                canvas = canvas * (1 - m) + cimg * m
        if grain:
            g = rng.normal(0, 1, (Hc // 2, Wc // 2)).astype(np.float32)
            g = cv2.resize(g, (Wc, Hc), interpolation=cv2.INTER_LINEAR)[..., None]
            canvas = canvas + args.grain * g * (0.6 + 0.4 * (1 - canvas.mean(axis=2, keepdims=True)))
        rgb = (np.clip(canvas, 0, 1) * 255 + 0.5).astype(np.uint8)
        if enc:
            enc.stdin.write(rgb.tobytes())
        if only is not None:
            cv2.imwrite(str(pdir / f"f{f:04d}_{T:06.2f}.png"), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        elif args.preview_every and f % args.preview_every == 0:
            cv2.imwrite(str(pdir / f"f{f:04d}_{T:06.2f}.jpg"), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    if enc:
        enc.stdin.close()
        enc.wait()
        def fr(t):  # a shot starts on the first output frame at or after its beat time
            return math.ceil(t * fps - 1e-6) / fps
        for s in shots:
            s["start"], s["end"] = fr(s["start"]), fr(s["end"])
        reveal = next((s["start"] for s in shots if s.get("cue") == "reveal"), None)
        sig = next((s["start"] for s in shots if s.get("cue") == "signature"), shots[-1]["start"])
        tl = {"bpm": bpm, "duration": nframes / fps, "fps": fps,
              "shots": [{"name": s["name"], "start": s["start"], "end": s["end"], "src_in": None} for s in shots],
              "cue_points": {"open_impact": 0.0, "riser_end_reveal": reveal, "signature": sig,
                             "end": nframes / fps},
              "shimmer_at": shots[1]["start"] if len(shots) > 1 else 0.0}
        if o:
            tl["shots"].append({"name": "end_card", "start": iris_start, "end": nframes / fps, "src_in": None})
            tl["cue_points"]["end_card_iris"] = iris_start
        json.dump(tl, open(out.with_suffix(".timeline.json"), "w"), indent=2)
        print(f"wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
