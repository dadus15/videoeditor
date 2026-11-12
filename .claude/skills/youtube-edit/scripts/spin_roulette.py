#!/usr/bin/env python3
""""Wheel roulette" 9:16 short from wheel STILLS: spin -> stop on the beat -> swap design inside the blur.

Built for product renders of wheels in a 3/4 view (Turismo BF campaign), no 3D needed:
  * spin       the wheel face (an ellipse in the still) rotates about the hub in perspective: pixels are mapped
               through S R(phi) S^-1 (S = ellipse axes), with rotational motion blur (many sub-frame samples).
               Every stop lands on a whole number of turns, so the resting frame is the untouched still.
               The outer lip stays static (it is rotationally uniform), so no seam shows.
  * swap       designs change at peak blur (the cut is invisible), speed is continuous across the cut.
  * vortex     procedural red/blue light-painting swirl (matches the stills' own lighting) around the wheel;
               its speed is coupled to the wheel's speed and it swells on every stop.
  * behind     one huge word per design rises out from BEHIND the wheel (occluded by the wheel silhouette:
               hull of the face ellipse and the rear lip ellipse) and sinks back before the next spin.
  * grid       finale: all designs in a 2x2 grid spin down together and stop on the beat; numbers + question
               (comment prompt); the grid spins up again at the end, which loops into frame 1 (also spinning).

Run from the project root:
  python3 .claude/skills/youtube-edit/scripts/spin_roulette.py edit/spin_x.json renders/x.mp4 [--bpm 120]
          [--crf 18] [--frames 0,12,40 --preview-dir work/pv]
Writes <out>.timeline.json (cue points: every stop and every swap) for mix_audio.py.
"""
import argparse, json, math, subprocess, sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compose as C  # noqa: E402

ROOT = Path.cwd()
E = C.EASE
TAU = 2 * math.pi


def load_rgb(p):
    return np.asarray(Image.open(ROOT / p).convert("RGB")).astype(np.float32) / 255


def smooth(m, s):
    return cv2.GaussianBlur(m, (0, 0), s) if s > 0 else m


class Wheel:
    """One still: rotation of the face about the hub + silhouette mask, in source pixels."""

    def __init__(self, d):
        self.d = d
        self.img = load_rgb(d["image"])
        self.half = cv2.resize(self.img, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        H, W = self.img.shape[:2]
        self.hub = np.array(d["hub"], np.float32)
        fx, fy, a, b = d["face"]
        self.a, self.b = a, b
        k = d.get("spin_inset", 0.965)                  # rotate inside the lip; the lip itself stays put
        m = np.zeros((H, W), np.float32)
        cv2.ellipse(m, (int(round(self.hub[0])), int(round(self.hub[1]))), (int(a * k), int(b * k)), 0, 0, 360, 1, -1,
                    cv2.LINE_AA)
        self.spin_mask = smooth(m, 2.0)[..., None]
        # silhouette: hull of the front face ellipse and the rear lip ellipse (the barrel)
        pts = cv2.ellipse2Poly((int(fx), int(fy)), (int(a), int(b)), 0, 0, 360, 4)
        rx, ry, ra, rb = d["rear"]
        pts = np.vstack([pts, cv2.ellipse2Poly((int(rx), int(ry)), (int(ra), int(rb)), 0, 0, 360, 4)])
        sil = np.zeros((H, W), np.float32)
        cv2.fillConvexPoly(sil, cv2.convexHull(pts), 1, cv2.LINE_AA)
        self.sil = smooth(sil, 1.5)

    def rot_matrix(self, phi, scale=1.0):
        """Forward affine (source -> source) rotating the face ellipse by phi about the hub."""
        S = np.diag([self.a, self.b])
        R = np.array([[math.cos(phi), -math.sin(phi)], [math.sin(phi), math.cos(phi)]])
        A = S @ R @ np.linalg.inv(S)
        h = self.hub * scale
        t = h - A @ h
        return np.hstack([A, t[:, None]]).astype(np.float32)

    def frame(self, phi, dphi):
        """Still with the face at angle phi, motion-blurred over the arc dphi (radians, this frame's shutter)."""
        arc = abs(dphi) * max(self.a, self.b)
        if arc < 0.6:
            if abs(phi % TAU) < 1e-6 or abs(phi % TAU - TAU) < 1e-6:
                return self.img
            M = self.rot_matrix(phi)
            r = cv2.warpAffine(self.img, M, self.img.shape[1::-1], flags=cv2.INTER_LANCZOS4,
                               borderMode=cv2.BORDER_REFLECT)
            return self.img * (1 - self.spin_mask) + np.clip(r, 0, 1) * self.spin_mask
        n = int(min(56, max(3, math.ceil(arc / 7))))
        lo = arc > 40                                     # heavy blur: sample at half resolution
        src = self.half if lo else self.img
        sc = 0.5 if lo else 1.0
        acc = np.zeros_like(src)
        for i in range(n):
            p = phi - dphi * (i + 0.5) / n               # shutter trails behind the current angle
            acc += cv2.warpAffine(src, self.rot_matrix(p, sc), src.shape[1::-1], flags=cv2.INTER_LINEAR,
                                  borderMode=cv2.BORDER_REFLECT)
        acc /= n
        if lo:
            acc = cv2.resize(acc, self.img.shape[1::-1], interpolation=cv2.INTER_LINEAR)
        return self.img * (1 - self.spin_mask) + acc * self.spin_mask


def place(src, hub, z, hub_xy, W, H, flags=cv2.INTER_LANCZOS4, border=0.0):
    """Warp a source-space image so the hub lands on hub_xy at zoom z."""
    M = np.float32([[z, 0, hub_xy[0] - z * hub[0]], [0, z, hub_xy[1] - z * hub[1]]])
    bv = (border,) * (src.shape[2] if src.ndim == 3 else 1)
    return cv2.warpAffine(src, M, (W, H), flags=flags, borderMode=cv2.BORDER_CONSTANT, borderValue=bv)


def window_alpha(w, valid, hub, z, hub_xy, W, H, feather, side=50):
    """Soft window over the valid source rect. The rect is shrunk first so the soft edge stays INSIDE it
    (otherwise the blur drags in what was cropped off: baked logos, counters, borders)."""
    x0, y0, x1, y1 = valid
    f = feather / z
    m = np.zeros(w.img.shape[:2], np.float32)
    m[int(y0 + f):int(y1 - f), int(x0 + side / z):int(x1 - side / z)] = 1
    out = place(m, hub, z, hub_xy, W, H, cv2.INTER_LINEAR)
    small = cv2.resize(out, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), feather / 2.2 / 4)
    return np.clip(cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR), 0, 1)


# ------------------------------------------------------------------ vortex

class Vortex:
    def __init__(self, W, H, cfg, s=2):
        self.W, self.H, self.s = W, H, s
        self.cfg = cfg
        yy, xx = np.mgrid[0:H // s, 0:W // s].astype(np.float32)
        self.xx, self.yy = xx * s, yy * s
        self.red = np.array(cfg.get("red", [1.0, 0.04, 0.16]), np.float32)
        self.blue = np.array(cfg.get("blue", [0.10, 0.22, 1.0]), np.float32)
        self.mag = np.array(cfg.get("mid", [0.55, 0.05, 0.75]), np.float32)

    def render(self, center, phase, gain, r_peak, r_width):
        dx = (self.xx - center[0]) / 1.0
        dy = (self.yy - center[1]) / 1.08
        r = np.sqrt(dx * dx + dy * dy) + 1e-3
        th = np.arctan2(dy, dx)
        lr = np.log(r / r_peak)
        env = np.exp(-(lr / r_width) ** 2)
        wob = 0.35 * np.sin(2 * th + 0.6 * phase) + 0.2 * np.sin(3 * th - 0.37 * phase)
        a1 = (0.5 + 0.5 * np.cos(3 * (th - phase) + 5.5 * lr + wob)) ** 10        # three main ribbons
        a2 = (0.5 + 0.5 * np.cos(5 * (th + 0.62 * phase) - 7.5 * lr + 1.3 * wob)) ** 18  # counter-swirl, thinner
        a3 = (0.5 + 0.5 * np.cos(2 * (th - 1.4 * phase) + 3.0 * lr)) ** 4 * 0.25   # soft haze
        inten = (a1 * 0.95 + a2 * 0.55 + a3) * env * gain
        side = np.clip(0.5 - 0.5 * np.cos(th), 0, 1)                                # 0 = right (blue), 1 = left (red)
        top = np.abs(np.sin(th)) ** 3
        col = (self.red * side[..., None] + self.blue * (1 - side[..., None])) * (1 - 0.45 * top[..., None]) \
            + self.mag * (0.45 * top[..., None])
        img = col * inten[..., None]
        img = cv2.GaussianBlur(img, (0, 0), 1.6)
        return cv2.resize(img, (self.W, self.H), interpolation=cv2.INTER_LINEAR)


def screen(a, b):
    return 1 - (1 - a) * (1 - np.clip(b, 0, 1))


# ------------------------------------------------------------------ text

def big_word(text, max_w, max_size, weight=700, track=-0.01):
    probe = C.render_text(text, weight, 100, track)
    size = int(min(max_size, 100 * max_w / probe.shape[1]))
    return C.render_text(text, weight, size, track), size


# ------------------------------------------------------------------ timeline

def spin_angle(t, dec, acc, seg, theta):
    """Angle (rad) of a segment's wheel: decelerates from -theta to 0 over dec, rests, then accelerates to
    +theta over the last acc seconds. Speed at both ends: 3*theta/dec == 3*theta/acc (continuous across cuts)."""
    if t < dec:
        return -theta * (1 - t / dec) ** 3
    if t > seg - acc:
        return theta * ((t - (seg - acc)) / acc) ** 3
    return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edl")
    ap.add_argument("out")
    ap.add_argument("--bpm", type=float)
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--audio")
    ap.add_argument("--grain", type=float, default=0.008)
    ap.add_argument("--frames")
    ap.add_argument("--preview-dir", default="work/preview_spin")
    args = ap.parse_args()

    edl = json.loads(Path(args.edl).read_text())
    bpm = args.bpm or edl["bpm"]
    beat = 60 / bpm
    fps = edl["fps"]
    W, H = edl["size"]
    sp = edl["spin"]
    DEC, ACC = sp["dec_beats"] * beat, sp["acc_beats"] * beat
    # keep the peak speed constant when re-timed: theta = w_max * dec / 3
    THETA = math.radians(sp["peak_deg_per_s"]) * DEC / 3
    SHUT = sp.get("shutter", 0.75)
    hub_xy = tuple(edl["hub_xy"])
    wheels = [Wheel(d) for d in edl["designs"]]
    seg_len = edl["segment_beats"] * beat
    grid = edl["grid"]
    grid_len = grid["beats"] * beat
    n_designs = len(wheels)
    total = n_designs * seg_len + grid_len
    nframes = int(round(total * fps))
    vort = Vortex(W, H, edl.get("vortex", {}))
    logo = None
    if "logo" in edl:
        from compose_stills import light_logo
        logo = light_logo(edl["logo"])

    # precompute: per design window alpha + silhouette in screen space at the base zoom is NOT valid when zoom
    # changes, so they are warped per frame (cheap, single channel).
    words = [big_word(d["word"], edl["word"]["max_w"], edl["word"]["max_size"]) for d in edl["designs"]]
    small = {k: C.render_text(v["text"], v.get("font", 500), v["size"], v.get("track", 0.2))
             for k, v in edl.get("labels", {}).items()}
    counters = [C.render_text(f"{i + 1:02d}", 700, 44, 0.04) for i in range(n_designs)]
    counter_tail = C.render_text(f" / {n_designs:02d}", 500, 44, 0.04)
    tile_nums = [C.render_text(f"{i + 1}", 700, 64, 0.0) for i in range(n_designs)]
    gtexts = {k: C.render_text(v["text"], v.get("font", 700), v["size"], v.get("track", 0.02),
                               stroke=v.get("stroke", 0)) for k, v in grid["texts"].items()}

    # wheel angular speed -> vortex phase (integrated so speed changes never jump)
    def wheel_speed(T):
        if T >= n_designs * seg_len:
            t = T - n_designs * seg_len
            ln = grid_len
        else:
            t = T % seg_len
            ln = seg_len
        e = 1e-3
        return abs(spin_angle(min(t + e, ln), DEC, ACC, ln, THETA) - spin_angle(max(t - e, 0), DEC, ACC, ln, THETA)) / (2 * e)

    vcfg = edl.get("vortex", {})
    phase_at = np.zeros(nframes + 1)
    ph = 0.0
    for f in range(nframes + 1):
        phase_at[f] = ph
        T = f / fps
        ph += (vcfg.get("base_speed", 0.55) + vcfg.get("coupling", 0.11) * wheel_speed(T)) / fps
    stops = [i * seg_len + DEC for i in range(n_designs)] + [n_designs * seg_len + DEC]
    swaps = [i * seg_len for i in range(1, n_designs + 1)]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    only = [int(x) for x in args.frames.split(",")] if args.frames else None
    pdir = Path(args.preview_dir)
    enc = None
    if only is None:
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
               "-i", "-"]
        if args.audio:
            cmd += ["-i", args.audio]
        cmd += ["-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p", "-c:v", "libx264", "-preset", "slow",
                "-crf", str(args.crf), "-profile:v", "high", "-colorspace", "bt709", "-color_primaries", "bt709",
                "-color_trc", "bt709", "-color_range", "tv", "-movflags", "+faststart"]
        cmd += (["-c:a", "aac", "-b:a", "256k", "-shortest"] if args.audio else ["-an"]) + [str(out)]
        enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    else:
        pdir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(3)
    base = np.full((H, W, 3), 0.010, np.float32)
    print(f"bpm {bpm} total {total:.2f}s frames {nframes} theta {math.degrees(THETA):.0f} deg  stops {stops}",
          file=sys.stderr)

    def swell(T):
        g = 0.0
        for s in stops:
            if 0 <= T - s < 0.9:
                g = max(g, math.exp(-(T - s) / 0.28))
        return g

    for f in (only if only is not None else range(nframes)):
        T = f / fps
        dt = 1 / fps
        canvas = base.copy()
        sw = swell(T)
        in_grid = T >= n_designs * seg_len
        if not in_grid:
            i = int(T // seg_len)
            t = T - i * seg_len
            w = wheels[i]
            d = edl["designs"][i]
            phi = spin_angle(t, DEC, ACC, seg_len, THETA)
            phi_prev = spin_angle(max(t - dt * SHUT, 0), DEC, ACC, seg_len, THETA) if t > 0 else \
                -THETA * (1 + 3 * dt * SHUT / DEC)       # frame 0 of a segment: carry the speed from before the cut
            dphi = phi - phi_prev
            # camera: settles on the stop, slow push while resting, rushes in on the spin-up
            z0 = d["z"]
            if t < DEC:
                z = z0 * (1.10 - 0.10 * E["out_cubic"](t / DEC))
            elif t > seg_len - ACC:
                u = (t - (seg_len - ACC)) / ACC
                z = z0 * (1.035 + 0.115 * E["in_cubic"](u))
            else:
                z = z0 * (1 + 0.035 * E["in_out_sine"]((t - DEC) / (seg_len - DEC - ACC)))
            still = w.frame(phi, dphi)
            hub = w.hub
            photo = place(still, hub, z, hub_xy, W, H)
            sil = place(w.sil, hub, z, hub_xy, W, H, cv2.INTER_LINEAR)
            wa = window_alpha(w, d["valid"], hub, z, hub_xy, W, H, edl.get("feather", 150))[..., None]
            dark = edl.get("bg_darken", 0.5)
            photo = photo * (1 - dark * (1 - sil[..., None]))
            canvas = canvas * (1 - wa) + photo * wa
            v = vort.render(hub_xy, phase_at[f], vcfg.get("gain", 1.0) * (1 + 0.6 * sw), vcfg.get("r_peak", 520),
                            vcfg.get("r_width", 0.55))
            canvas = screen(canvas, v * (1 - 0.93 * sil[..., None]))
            # the word behind the wheel: rises out from behind the rim, sinks back before the swap
            img, size = words[i]
            wheel_top = hub_xy[1] - w.b * z
            y_rest = wheel_top + edl["word"].get("tuck", 110) - size - 4      # baseline sits `tuck` px behind the rim
            if i == 0 and t < DEC:
                k = 1.0                                   # hook: the first word is already up on frame 1
            else:
                k = E["out_cubic"](C.clamp01((t - DEC + 0.12) / 0.5))
            k *= 1 - E["in_cubic"](C.clamp01((t - (seg_len - ACC - 0.05)) / 0.4))
            if k > 0:
                y = y_rest + (1 - k) * size * 1.1
                al = np.zeros((H, W), np.float32)
                x0, y0 = int(round(W / 2 - img.shape[1] / 2)), int(round(y))
                ys, xs = max(0, y0), max(0, x0)
                ye, xe = min(H, y0 + img.shape[0]), min(W, x0 + img.shape[1])
                if ye > ys and xe > xs:
                    al[ys:ye, xs:xe] = img[ys - y0:ye - y0, xs - x0:xe - x0, 3]
                a = (al * (1 - sil) * edl["word"].get("opacity", 0.96))[..., None]
                canvas = canvas * (1 - a) + a * 1.0
            # counter top-left (carousel echo)
            ca = E["out_cubic"](C.clamp01((t - DEC + 0.05) / 0.35)) if not (i == 0 and t < DEC) else 1.0
            ca *= 1 - E["in_cubic"](C.clamp01((t - (seg_len - ACC)) / 0.3))
            cnum = counters[i].copy()
            cnum[..., :3] = np.array([0.04, 0.94, 0.94], np.float32)
            C.blit(canvas, cnum, 56, 92, ca)
            C.blit(canvas, counter_tail, 56 + cnum.shape[1] - 6, 92, ca * 0.8)
        else:
            t = T - n_designs * seg_len
            phi = spin_angle(t, DEC, ACC, grid_len, THETA)
            phi_prev = spin_angle(max(t - dt * SHUT, 0), DEC, ACC, grid_len, THETA) if t > 0 else \
                -THETA * (1 + 3 * dt * SHUT / DEC)
            dphi = phi - phi_prev
            c = grid["center"]
            v = vort.render(c, phase_at[f], vcfg.get("gain", 1.0) * (0.85 + 0.6 * sw), grid.get("r_peak", 640),
                            vcfg.get("r_width", 0.55))
            canvas = screen(canvas, v)
            ts = grid["tile"]
            sc_in = 1.0 + 0.12 * (1 - E["out_cubic"](C.clamp01(t / DEC)))
            sc_out = 1.0 + 0.10 * E["in_cubic"](C.clamp01((t - (grid_len - ACC)) / ACC))
            for j, (w, pos) in enumerate(zip(wheels, grid["pos"])):
                still = w.frame(phi, dphi)
                z = ts * grid.get("fill", 0.42) / w.b * sc_in * sc_out
                tile_c = (ts / 2, ts / 2)
                tile = place(still, w.hub, z, tile_c, ts, ts)
                vx0, vy0, vx1, vy1 = edl["designs"][j]["valid"]
                vm = np.zeros(w.img.shape[:2], np.float32)
                vm[vy0 + 40:vy1 - 40, vx0 + 40:vx1 - 40] = 1
                m = smooth(place(vm, w.hub, z, tile_c, ts, ts, cv2.INTER_LINEAR), 14)
                tsil = place(w.sil, w.hub, z, tile_c, ts, ts, cv2.INTER_LINEAR)
                # soft tile; around the wheel the swirl shows through, so the wheels float on it
                rr = np.zeros((ts, ts), np.float32)
                cv2.rectangle(rr, (24, 24), (ts - 25, ts - 25), 1, -1)
                rr = smooth(rr, 16) * m * (grid.get("tile_bg", 0.35) + (1 - grid.get("tile_bg", 0.35)) * tsil)
                x0, y0 = int(pos[0] - ts / 2), int(pos[1] - ts / 2)
                reg = canvas[y0:y0 + ts, x0:x0 + ts]
                canvas[y0:y0 + ts, x0:x0 + ts] = reg * (1 - rr[..., None]) + tile * rr[..., None]
                na = E["out_cubic"](C.clamp01((t - DEC - 0.08 * j) / 0.35))
                na *= 1 - E["in_cubic"](C.clamp01((t - (grid_len - ACC)) / 0.3))
                num = tile_nums[j].copy()
                num[..., :3] = np.array([0.04, 0.94, 0.94], np.float32)
                C.blit(canvas, num, x0 + 30, y0 + ts - 30 - num.shape[0] + (1 - na) * 20, na)
            for k_, gt in grid["texts"].items():
                img = gtexts[k_]
                a = E["out_cubic"](C.clamp01((t - gt["in"]) / 0.42))
                a *= 1 - E["in_cubic"](C.clamp01((t - (grid_len - ACC)) / 0.3))
                if a <= 0:
                    continue
                if gt.get("anim") == "mask":
                    yy0 = gt["y"] - img.shape[0] / 2
                    clip = (0, int(yy0 + 2), W, int(yy0 + img.shape[0] - 2))
                    C.blit(canvas, img, W / 2 - img.shape[1] / 2, yy0 + (1 - a) * img.shape[0] * 0.95, a, clip=clip)
                else:
                    C.blit(canvas, img, W / 2 - img.shape[1] / 2, gt["y"] - img.shape[0] / 2 + (1 - a) * 16, a)
        # constant top band: logo + campaign line
        if logo is not None:
            C.blit(canvas, logo, W / 2 - logo.shape[1] / 2, edl["logo"].get("y", 110) - logo.shape[0] / 2, 1.0)
        for k_, lab in edl.get("labels", {}).items():
            if in_grid and lab.get("hide_in_grid"):
                continue
            img = small[k_]
            C.blit(canvas, img, W / 2 - img.shape[1] / 2, lab["y"] - img.shape[0] / 2, lab.get("alpha", 0.85))
        g = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
        g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
        canvas = canvas + args.grain * g * (0.6 + 0.4 * (1 - canvas.mean(axis=2, keepdims=True)))
        rgb = (np.clip(canvas, 0, 1) * 255 + 0.5).astype(np.uint8)
        if enc:
            enc.stdin.write(rgb.tobytes())
        else:
            cv2.imwrite(str(pdir / f"s{f:04d}_{T:06.2f}.png"), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    if enc:
        enc.stdin.close()
        enc.wait()
        fr = lambda x: math.ceil(x * fps - 1e-6) / fps  # noqa: E731
        shots = [{"name": f"design_{i + 1}", "start": fr(i * seg_len), "end": fr((i + 1) * seg_len), "src_in": None}
                 for i in range(n_designs)]
        shots.append({"name": "grid_pick_one", "start": fr(n_designs * seg_len), "end": nframes / fps, "src_in": None})
        tl = {"bpm": bpm, "duration": nframes / fps, "fps": fps, "shots": shots,
              "cue_points": {"open_impact": 0.0, "riser_end_reveal": fr(stops[0]), "signature": fr(stops[-1]),
                             "end": nframes / fps},
              "stops": [fr(s) for s in stops], "swaps": [fr(s) for s in swaps],
              "shimmer_at": fr(stops[1])}
        json.dump(tl, open(out.with_suffix(".timeline.json"), "w"), indent=2)
        print(f"wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
