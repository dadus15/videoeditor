#!/usr/bin/env python3
"""Every CGI shot of the Turismo Inventa promo, matched to the Vossen HF reference cut.

Each shot is rendered on its own (transparent background, shadow catcher where the wheel stands) to
work/cgi/<res>/<shot>/f0001.png ... and composited over the studio white by cgi/post.py.

    python3 cgi/shots.py --res 720 --spp 16                 # all shots
    python3 cgi/shots.py --res 180 --spp 4 --only S02,S03   # quick previz

Camera positions are world metres. The wheel stands at the origin, face toward -Y, radius 0.262.
`spin` turns the wheel about its axle (degrees, clockwise as seen from the front when negative).
"""
import argparse
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
from mathutils import Quaternion, Vector  # noqa: E402

import scene as S  # noqa: E402

FPS = 25


def lerp(a, b, t):
    if isinstance(a, (tuple, list)):
        return tuple(x + (y - x) * t for x, y in zip(a, b))
    return a + (b - a) * t


def ease_io(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def ease_out(t, p=3):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** p


def ease_in(t, p=3):
    t = min(max(t, 0.0), 1.0)
    return t ** p


def move(a, b, curve=ease_io):
    """Camera keyframe helper: returns f(t) that blends two dicts with an easing curve."""
    def f(t):
        k = curve(t)
        return {key: lerp(a[key], b[key], k) for key in a}
    return f


# ------------------------------------------------------------------------------------------- shots
# frames: number of frames. finish: wheel finish. cam(t) -> dict(loc, tgt, roll, lens, spin[, fstop])
# blur: motion blur shutter (0 = off). floor: shadow catcher under a standing wheel.

def s02_cam(t):
    # line-up slides in from the right on a fast whip (first 5 frames), then drifts slowly
    k = ease_out(t * 52 / 6, 2.2)
    x = lerp(2.4, 0.16, k) - 0.16 * ease_io(t)
    return dict(loc=(x, -4.25, 0.06), tgt=(x, 0, 0.0), roll=0, lens=50, spin=0)


def s04_cam(t):
    # whip: the camera rolls hard and pushes toward the hub
    k = ease_in(t, 2.0)
    loc = lerp((0.02, -0.29, -0.27), (0.0, -0.26, -0.02), k)
    tgt = lerp((0.0, 0.0, -0.17), (0.0, 0.0, -0.02), k)
    return dict(loc=loc, tgt=tgt, roll=lerp(0, -150, k), lens=lerp(22, 28, k), spin=lerp(-15, -60, k), fstop=4.0)


def s07_cam(t):
    # wheel lying almost flat, seen low; last 5 frames whip (the wheel spins) into S08
    w = max(0.0, (t * 19 - 13) / 6)
    return dict(loc=(0.0, -1.12, 0.29), tgt=(0.0, 0.0, -0.03), roll=lerp(0, 25, ease_in(w)), lens=50,
                spin=lerp(0, -12, t) - 160 * ease_in(w, 2), fstop=5.6)


def s09_cam(t):
    # along the bottom of the lip: the camera orbits from 6 o'clock toward 4 o'clock and tilts onto the
    # lip edge, accelerating at the end (reference 12.8-14.0 s)
    k = 0.35 * t + 0.65 * ease_in(max(0.0, (t - 0.62) / 0.38), 2.2)
    ang = math.radians(lerp(-90, -35, k))
    r_tgt = 0.235
    tgt = (r_tgt * math.cos(ang), 0.005, r_tgt * math.sin(ang))
    d = lerp(0.27, 0.13, k)
    cdir = Vector((math.cos(ang) * 0.55, -1.0, math.sin(ang) * 0.55 + 0.55)).normalized()
    loc = tuple(Vector(tgt) + cdir * d)
    return dict(loc=loc, tgt=tgt, roll=lerp(0, 38, k), lens=28, spin=lerp(0, 6, t), fstop=2.8)


def s11_cam(t):
    return dict(loc=lerp((0.03, -0.40, -0.07), (0.0, -0.36, -0.06), ease_io(t)),
                tgt=(0.0, 0.0, -0.10), roll=0, lens=30, spin=lerp(0, -9, t), fstop=5.6,
                sweep=lerp(-3.0, 3.0, ease_io((t * 95 - 15) / 22)))


def s12_cam(t):
    return dict(loc=lerp((-0.36, -0.62, 0.05), (-0.17, -0.50, 0.03), ease_io(t)),
                tgt=lerp((0.03, 0.0, 0.0), (0.0, 0.0, 0.0), t), roll=0, lens=32,
                spin=lerp(0, -16, t), fstop=5.6)


def s13_cam(t):
    k = ease_in(t, 2.0)
    return dict(loc=lerp((-0.17, -0.50, 0.03), (0.0, -0.10, 0.0), k), tgt=(0.0, 0.0, -0.035),
                roll=lerp(0, -110, k), lens=32, spin=lerp(-16, -20, t), fstop=8.0)


SHOTS = {
    # name: frames, finish, cam, extras
    "S02": dict(frames=52, finish="lineup", blur=0.6, floor=True, cam=s02_cam),
    "S03": dict(frames=34, finish="satin_black", cam=move(
        dict(loc=(0.02, -0.30, -0.27), tgt=(0.0, 0.0, -0.17), roll=0, lens=22, spin=0, fstop=4.0),
        dict(loc=(0.02, -0.29, -0.27), tgt=(0.0, 0.0, -0.17), roll=0, lens=22, spin=-15, fstop=4.0), lambda t: t)),
    "S04": dict(frames=15, finish="satin_black", blur=1.0, cam=s04_cam),
    "S05": dict(frames=20, finish="hyper_silver", cam=move(
        dict(loc=(-0.44, -0.72, 0.06), tgt=(0.03, 0, 0), roll=0, lens=40, spin=0, fstop=5.6),
        dict(loc=(-0.42, -0.68, 0.055), tgt=(0.03, 0, 0), roll=0, lens=40, spin=-4, fstop=5.6), lambda t: t)),
    "S06": dict(frames=5, finish="gloss_black", cam=move(
        dict(loc=(0.56, -0.56, 0.10), tgt=(0.0, 0, 0), roll=0, lens=35, spin=0, fstop=5.6),
        dict(loc=(0.55, -0.55, 0.10), tgt=(0.0, 0, 0), roll=0, lens=35, spin=-1, fstop=5.6), lambda t: t)),
    "S07": dict(frames=19, finish="gunmetal", blur=0.8, wheel_rot=(8, 0, 0), cam=s07_cam),
    "S08": dict(frames=47, finish="brushed", floor=True, cam=move(
        dict(loc=(0.0, -1.95, 0.05), tgt=(0, 0, 0), roll=0, lens=50, spin=0, yaw=-55),
        dict(loc=(0.0, -1.88, 0.05), tgt=(0, 0, 0), roll=0, lens=50, spin=-10, yaw=-4), lambda t: ease_out(t * 1.35, 3))),
    "S09": dict(frames=93, finish="gunmetal", blur=0.5, cam=s09_cam),
    "S10": dict(frames=46, finish="hyper_silver", cam=move(
        dict(loc=(0.14, -0.36, 0.05), tgt=(0.05, 0, 0.0), roll=0, lens=35, spin=0, fstop=4.0),
        dict(loc=(-0.02, -0.34, 0.04), tgt=(0.0, 0, 0.0), roll=0, lens=35, spin=-3, fstop=4.0), lambda t: t)),
    # montage A / B (short, reused)
    "A1": dict(frames=4, finish="hyper_silver", cam=move(
        dict(loc=(-0.40, -0.46, 0.02), tgt=(0.07, 0, 0), roll=0, lens=32, spin=0, fstop=4.0),
        dict(loc=(-0.39, -0.45, 0.02), tgt=(0.07, 0, 0), roll=0, lens=32, spin=-1, fstop=4.0), lambda t: t)),
    "A2": dict(frames=2, finish="gloss_black", cam=move(
        dict(loc=(0.0, -0.30, 0.0), tgt=(0, 0, -0.02), roll=0, lens=35, spin=0, fstop=4.0),
        dict(loc=(0.0, -0.30, 0.0), tgt=(0, 0, -0.02), roll=0, lens=35, spin=-0.5, fstop=4.0), lambda t: t)),
    "A3": dict(frames=4, finish="gloss_black", cam=move(
        dict(loc=(0.16, -0.42, 0.21), tgt=(-0.05, 0, -0.11), roll=10, lens=30, spin=0, fstop=4.0),
        dict(loc=(0.16, -0.41, 0.21), tgt=(-0.05, 0, -0.11), roll=10, lens=30, spin=-1, fstop=4.0), lambda t: t)),
    "A4": dict(frames=12, finish="bronze", floor=True, cam=move(
        dict(loc=(0.08, -1.28, 0.10), tgt=(0, 0, 0), roll=0, lens=50, spin=0, yaw=-8),
        dict(loc=(0.08, -1.24, 0.10), tgt=(0, 0, 0), roll=0, lens=50, spin=-3, yaw=-8), lambda t: t)),
    "A5": dict(frames=15, finish="gunmetal", cam=move(
        dict(loc=(0.43, -0.50, 0.08), tgt=(-0.06, 0, 0), roll=0, lens=35, spin=0, fstop=4.0),
        dict(loc=(0.41, -0.48, 0.08), tgt=(-0.06, 0, 0), roll=0, lens=35, spin=-3, fstop=4.0), lambda t: t)),
    "A6": dict(frames=18, finish="hyper_silver", cam=move(
        dict(loc=(0.05, -0.44, 0.06), tgt=(0, 0, -0.01), roll=0, lens=40, spin=0, fstop=4.0),
        dict(loc=(0.04, -0.37, 0.05), tgt=(0, 0, -0.01), roll=0, lens=40, spin=-3, fstop=4.0), lambda t: t)),
    "A7": dict(frames=7, finish="bronze", cam=move(
        dict(loc=(0.0, -0.25, 0.0), tgt=(0, 0, -0.03), roll=0, lens=35, spin=0, fstop=4.0),
        dict(loc=(0.0, -0.245, 0.0), tgt=(0, 0, -0.03), roll=0, lens=35, spin=-1.5, fstop=4.0), lambda t: t)),
    "A8": dict(frames=6, finish="hyper_silver", cam=move(
        dict(loc=(-0.21, -0.30, 0.19), tgt=(0.0, 0, 0.06), roll=-8, lens=28, spin=0, fstop=4.0),
        dict(loc=(-0.20, -0.30, 0.19), tgt=(0.0, 0, 0.06), roll=-8, lens=28, spin=-1.5, fstop=4.0), lambda t: t)),
    "A9": dict(frames=7, finish="hyper_silver", cam=move(
        dict(loc=(0.0, -0.17, 0.0), tgt=(0, 0, -0.04), roll=0, lens=50, spin=0, fstop=5.6),
        dict(loc=(0.0, -0.16, 0.0), tgt=(0, 0, -0.04), roll=0, lens=50, spin=0, fstop=5.6), lambda t: t)),
    "A10": dict(frames=7, finish="satin_black", cam=move(
        dict(loc=(0.31, -0.36, -0.15), tgt=(-0.05, 0, 0.05), roll=0, lens=28, spin=0, fstop=4.0),
        dict(loc=(0.30, -0.35, -0.15), tgt=(-0.05, 0, 0.05), roll=0, lens=28, spin=-1.5, fstop=4.0), lambda t: t)),
    "A11": dict(frames=12, finish="satin_black", floor=True, cam=move(
        dict(loc=(-0.22, -1.26, 0.05), tgt=(0, 0, 0), roll=0, lens=50, spin=0, yaw=6),
        dict(loc=(-0.22, -1.22, 0.05), tgt=(0, 0, 0), roll=0, lens=50, spin=-3, yaw=6), lambda t: t)),
    "A12": dict(frames=2, finish="hyper_silver", cam=move(
        dict(loc=(0.0, -0.50, -0.05), tgt=(0, 0, -0.20), roll=0, lens=28, spin=0, fstop=4.0),
        dict(loc=(0.0, -0.50, -0.05), tgt=(0, 0, -0.20), roll=0, lens=28, spin=-1, fstop=4.0), lambda t: t)),
    "S11": dict(frames=95, finish="gunmetal", cam=s11_cam),
    "B5": dict(frames=13, finish="hyper_silver", floor=True, cam=move(
        dict(loc=(0.25, -2.30, 0.06), tgt=(0, 0, 0), roll=0, lens=50, spin=0, yaw=-6),
        dict(loc=(0.25, -2.26, 0.06), tgt=(0, 0, 0), roll=0, lens=50, spin=-3, yaw=-6), lambda t: t)),
    "B7": dict(frames=18, finish="gunmetal", cam=move(
        dict(loc=(0.0, -0.40, 0.17), tgt=(0, 0, 0.11), roll=0, lens=28, spin=0, fstop=4.0),
        dict(loc=(0.0, -0.36, 0.16), tgt=(0, 0, 0.11), roll=0, lens=28, spin=-4, fstop=4.0), lambda t: t)),
    "B12": dict(frames=13, finish="gloss_black", floor=True, cam=move(
        dict(loc=(0.0, -1.32, 0.03), tgt=(0, 0, 0), roll=0, lens=50, spin=0, yaw=-4),
        dict(loc=(0.0, -1.28, 0.03), tgt=(0, 0, 0), roll=0, lens=50, spin=-3, yaw=-4), lambda t: t)),
    "S12": dict(frames=104, finish="bronze", cam=s12_cam),
    "S13": dict(frames=8, finish="bronze", blur=1.0, cam=s13_cam),
    # end-card line art source (one still)
    "LINE": dict(frames=1, finish="brushed", cam=move(
        dict(loc=(-0.55, -1.05, 0.30), tgt=(0.05, 0, 0.02), roll=0, lens=40, spin=0, yaw=-10),
        dict(loc=(-0.55, -1.05, 0.30), tgt=(0.05, 0, 0.02), roll=0, lens=40, spin=0, yaw=-10), lambda t: t)),
}

LINEUP = ["gloss_black", "satin_black", "hyper_silver", "brushed", "gunmetal", "bronze", "gloss_black"]


def build(name, spec, w, h, spp):
    S.reset()
    blur = spec.get("blur", 0.0)
    S.render_setup(w, h, samples=spp, fps=FPS, motion_blur=blur > 0, shutter=blur or 0.5)
    S.studio()
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
    wheels = []
    if spec["finish"] == "lineup":
        for i, f in enumerate(LINEUP):
            r = S.WheelRig(f, name=f"w{i}")
            r.place(((i - 3) * 0.60, 0, 0), (90, 0, -12))
            wheels.append(r)
    else:
        r = S.WheelRig(spec["finish"])
        r.place((0, 0, 0), (*spec.get("wheel_rot", (90, 0, 0)),))
        wheels.append(r)
    if spec.get("floor"):
        S.floor(-S.R_LIP)
    cam = S.camera()
    cam.rotation_mode = "QUATERNION"
    strip = bpy.data.objects.get("strip")
    sc = bpy.context.scene
    n = spec["frames"]
    sc.frame_start, sc.frame_end = 1, n
    prev_q = None
    base_rot = [tuple(r.root.rotation_euler) for r in wheels]
    # keys at every frame plus one extra beyond each end so motion blur has data
    for f in range(0, n + 2):
        t = (f - 1) / max(n - 1, 1)
        p = spec["cam"](t)
        cam.location = p["loc"]
        d = Vector(p["tgt"]) - Vector(p["loc"])
        q = d.to_track_quat("-Z", "Y")
        q = q @ Quaternion((0, 0, 1), math.radians(p.get("roll", 0)))
        if prev_q is not None and prev_q.dot(q) < 0:
            q.negate()
        prev_q = q.copy()
        cam.rotation_quaternion = q
        cam.data.lens = p["lens"]
        cam.data.dof.use_dof = "fstop" in p
        if "fstop" in p:
            cam.data.dof.aperture_fstop = p["fstop"]
            cam.data.dof.focus_distance = d.length
            cam.data.dof.keyframe_insert("focus_distance", frame=f)
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_quaternion", frame=f)
        cam.data.keyframe_insert("lens", frame=f)
        for r, br in zip(wheels, base_rot):
            r.spin.rotation_euler.z = math.radians(p.get("spin", 0))
            r.spin.keyframe_insert("rotation_euler", index=2, frame=f)
            if "yaw" in p:
                r.root.rotation_euler = (br[0], br[1], math.radians(p["yaw"]))
                r.root.keyframe_insert("rotation_euler", frame=f)
        if strip is not None and "sweep" in p:
            strip.location.x = p["sweep"]
            strip.keyframe_insert("location", index=0, frame=f)
    return sc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", type=int, default=720, help="output height; width is 16:9")
    ap.add_argument("--spp", type=int, default=16)
    ap.add_argument("--only", default="")
    ap.add_argument("--skip-existing", action="store_true")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    h = args.res
    w = h * 16 // 9
    names = [s for s in args.only.split(",") if s] or list(SHOTS)
    root = S.ROOT / "work" / "cgi" / str(h)
    for name in names:
        spec = SHOTS[name]
        out = root / name
        if args.skip_existing and out.exists() and len(list(out.glob("f*.png"))) >= spec["frames"]:
            print(f"[{name}] exists, skipped", flush=True)
            continue
        out.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        sc = build(name, spec, w, h, args.spp)
        sc.render.filepath = str(out / "f")
        bpy.ops.render.render(animation=True)
        dt = time.time() - t0
        print(f"[{name}] {spec['frames']} frames in {dt:.0f}s ({dt / spec['frames']:.1f}s/frame)", flush=True)


if __name__ == "__main__":
    main()
