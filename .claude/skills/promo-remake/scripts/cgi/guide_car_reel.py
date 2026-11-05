"""Motion guide (grey-box playblast) for the VANTA-style reel, 1:1 with the reference choreography.

Blender 4.5 headless, BLENDER_WORKBENCH (about 1-3 s a frame on one CPU, 30x faster than Cycles).
The car is a Hunyuan3D mesh made from the client's three studio photos of the GT3 RS (MSP02).
Its parts are split by geometry: the bonnet (pops off, then the new bonnet lands), the rear wing (rises) and
the four wheels (spin).

    blender -b -P guide.py -- --seg A --f0 0 --f1 230 --out /home/user/guide/A --res 720
    blender -b -P guide.py -- --seg A --stills 1.04,2.3,3.5,5,7,8.3 --out /home/user/guide/checkA

Segment A = film 1.04-8.75 s: coastal road, yellow car on stock wheels. FPV roll 90 deg -> 45 deg -> level,
            the old bonnet bursts off (2.2-2.6), the new bonnet descends and floats (3.1-6.0), then lands
            (6.0-6.9); push in along the bonnet and dive into the vent until the frame is flat paint (8.6).
Segment B = film 8.75-13.30 s: snowy mountain road, white GT3 RS on MSP02. Out of the side-window glass,
            pull back along the left flank to the rear 3/4, the wing rises (10.45-10.85), then the chase
            slows and the car pulls away.
Car frame: the car sits at the origin and faces +X, left side = +Y, metres. The scenery scrolls -X at road
speed, so only relative motion matters.
"""
import argparse
import math
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Quaternion, Vector

FPS = 24
CAR_GLB = "/home/user/guide/car.glb"
SCALE = 4.24                       # mesh length 1.078 -> 4.57 m (911 GT3 RS); wheelbase comes out 2.46 m

SEG = {"A": (1.04, 8.75), "B": (8.75, 13.30)}

# camera keys: (film t, target xyz, azimuth deg [0 = ahead of the car, 90 = left side], elevation deg,
#               distance m, roll deg, lens mm). Measured against the reference sheets.
KEYS = {        # (film t, camera xyz, target xyz, roll deg, lens mm on a 24 mm vertical sensor)
    "A": [
        (1.04, (2.35, 1.40, 0.50), (0.40, 0.95, 0.40), -90, 14),
        (1.40, (2.30, 1.25, 0.95), (1.20, 0.80, 0.45), -84, 14),
        (1.75, (2.70, 1.10, 1.05), (1.60, 0.55, 0.50), -65, 15),
        (2.05, (3.60, 1.60, 0.60), (1.60, 0.45, 0.55), -45, 16),
        (2.30, (4.20, 2.20, 0.45), (1.60, 0.40, 0.60), -28, 17),
        (2.60, (4.60, 1.60, 0.45), (1.50, 0.20, 0.65), -10, 19),
        (3.00, (5.60, 0.35, 0.75), (1.40, 0.00, 0.80), 0, 22),
        (4.50, (6.00, 0.20, 0.95), (1.40, 0.00, 1.10), 0, 22),
        (6.00, (5.60, 0.80, 0.90), (1.40, 0.10, 0.85), 0, 22),
        (6.90, (4.80, 1.90, 0.95), (1.50, 0.15, 0.80), 0, 22),
        (7.50, (3.70, 2.10, 1.10), (1.70, 0.20, 0.85), 3, 20),
        (8.10, (2.60, 1.00, 1.30), (1.75, 0.22, 0.90), 12, 20),
        (8.50, (2.05, 0.35, 1.15), (1.80, 0.22, 0.92), 18, 20),
        (8.75, (1.88, 0.25, 1.02), (1.80, 0.22, 0.92), 20, 20),
    ],
    "B": [
        (8.75, (-0.20, 1.12, 1.05), (-0.20, 0.80, 1.00), 34, 20),
        (9.30, (-0.10, 2.00, 1.15), (-0.20, 0.90, 0.95), 30, 20),
        (9.80, (0.30, 3.60, 1.20), (-0.10, 0.70, 0.80), 15, 22),
        (10.25, (-2.60, 4.20, 1.10), (-0.40, 0.30, 0.75), 5, 24),
        (10.75, (-6.20, 2.60, 1.10), (-0.60, 0.00, 0.75), 0, 26),
        (11.50, (-10.5, 1.20, 1.20), (-0.40, 0.00, 0.70), 0, 28),
        (13.30, (-20.0, 0.60, 1.40), (-0.40, 0.00, 0.70), 0, 30),
    ],
}
ROAD_SPEED = {"A": 22.0, "B": 25.0}      # m/s; scenery scrolls -X


def smoothstep(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def hermite(keys, t, idx):
    """Monotone-ish cubic through keys[i][idx] (scalars or tuples), Catmull-Rom tangents."""
    ts = [k[0] for k in keys]
    if t <= ts[0]:
        return keys[0][idx]
    if t >= ts[-1]:
        return keys[-1][idx]
    i = max(j for j in range(len(ts) - 1) if ts[j] <= t)
    t0, t1 = ts[i], ts[i + 1]
    u = (t - t0) / (t1 - t0)
    def val(j):
        return np.array(keys[min(max(j, 0), len(keys) - 1)][idx], float)
    p0, p1 = val(i), val(i + 1)
    m0 = (val(i + 1) - val(i - 1)) / (ts[min(i + 1, len(ts) - 1)] - ts[max(i - 1, 0)]) * (t1 - t0)
    m1 = (val(i + 2) - val(i)) / (ts[min(i + 2, len(ts) - 1)] - ts[i]) * (t1 - t0)
    h00, h10, h01, h11 = 2*u**3 - 3*u**2 + 1, u**3 - 2*u**2 + u, -2*u**3 + 3*u**2, u**3 - u**2
    r = h00 * p0 + h10 * m0 + h01 * p1 + h11 * m1
    return r if r.shape else float(r)


# ----------------------------------------------------------------------------------------------- car
def mat(name, rgb):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    return m


def build_car(seg):
    bpy.ops.import_scene.gltf(filepath=CAR_GLB)
    src = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
    me = src.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    groups = {"hood": [], "wing": [], "wFL": [], "wFR": [], "wRL": [], "wRR": [], "body": []}
    wheels = {"wFL": (-0.355, 1), "wFR": (-0.355, -1), "wRL": (0.225, 1), "wRR": (0.225, -1)}
    for f in bm.faces:
        c = f.calc_center_median()
        n = f.normal
        x, y, z = c.x, c.y, c.z
        g = "body"
        for k, (wx, side) in wheels.items():
            if math.hypot(x - wx, z - 0.083) < 0.088 and y * side > 0.13:
                g = k
        if g == "body":
            if -0.555 < x < -0.29 and abs(y) < 0.16 and z > 0.122 + (x + 0.591) * 0.30 - 0.012 and n.z > 0.45:
                g = "hood"
            elif x > 0.345 and z > 0.252:
                g = "wing"
        groups[g].append(f.index)
    bm.free()
    paint = (1.0, 0.78, 0.05) if seg == "A" else (0.93, 0.93, 0.95)
    rim = (0.08, 0.08, 0.09) if seg == "A" else (0.78, 0.62, 0.36)
    cols = {"body": paint, "hood": paint, "wing": (0.12, 0.12, 0.13), "wFL": rim, "wFR": rim, "wRL": rim, "wRR": rim}
    objs = {}
    S = Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Scale(SCALE, 4)
    for g, faces in groups.items():
        if not faces:
            continue
        bm = bmesh.new()
        bm.from_mesh(me)
        keep = set(faces)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context="FACES")
        nm = bpy.data.meshes.new(g)
        bm.to_mesh(nm)
        bm.free()
        nm.transform(S)
        ob = bpy.data.objects.new("CAR_" + g, nm)
        bpy.context.scene.collection.objects.link(ob)
        ob.color = (*cols[g], 1)
        for p in nm.polygons:
            p.use_smooth = True
        # pivot at the part's centre so it can fly / spin about itself
        cen = sum((v.co for v in nm.vertices), Vector()) / max(len(nm.vertices), 1)
        if g.startswith("w"):
            cen = Vector((cen.x, cen.y, 0.35))
        nm.transform(Matrix.Translation(-cen))
        ob.location = cen
        objs[g] = ob
    bpy.data.objects.remove(src)
    if seg == "A":      # the new bonnet: a light copy of the stock one that will descend and land
        nb = objs["hood"].copy()
        nb.data = objs["hood"].data.copy()
        nb.name = "CAR_newhood"
        nb.color = (0.80, 0.90, 0.97, 1)
        bpy.context.scene.collection.objects.link(nb)
        objs["newhood"] = nb
    print("PARTS", {k: len(v) for k, v in groups.items()})
    return objs


# ---------------------------------------------------------------------------------------- scenery
def box(name, loc, size, rgb, parent=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    o.color = (*rgb, 1)
    if parent:
        o.parent = parent
    return o


def palm(env, x, y, h, lean, rng):
    bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=0.28, radius2=0.16, depth=h, location=(x, y, h / 2),
                                    rotation=(lean, 0, 0))
    t = bpy.context.object
    t.color = (0.42, 0.34, 0.25, 1)
    t.parent = env
    top = Vector((x, y - math.sin(lean) * h, math.cos(lean) * h))
    for k in range(9):
        a = k / 9 * 2 * math.pi + rng.uniform(0, 0.4)
        bpy.ops.mesh.primitive_plane_add(size=1, location=top + Vector((math.cos(a) * 1.4, math.sin(a) * 1.4, -0.35)))
        lf = bpy.context.object
        lf.scale = (2.8, 0.55, 1)
        lf.rotation_euler = (rng.uniform(-0.2, 0.2), 0.45, a)
        lf.color = (0.20, 0.33, 0.17, 1)
        lf.parent = env


def bare_tree(env, x, y, h, rng):
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.22, radius2=0.04, depth=h, location=(x, y, h / 2))
    t = bpy.context.object
    t.color = (0.18, 0.17, 0.16, 1)
    t.parent = env
    for k in range(7):
        z = h * rng.uniform(0.35, 0.85)
        a = rng.uniform(0, 2 * math.pi)
        L = h * rng.uniform(0.18, 0.32)
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.04, depth=L,
                                            location=(x + math.cos(a) * L * 0.35, y + math.sin(a) * L * 0.35, z + L * 0.3),
                                            rotation=(0.9 * math.sin(a), -0.9 * math.cos(a), 0))
        b = bpy.context.object
        b.color = (0.18, 0.17, 0.16, 1)
        b.parent = env


def build_env(seg):
    rng = np.random.default_rng(7)
    env = bpy.data.objects.new("ENV", None)
    bpy.context.scene.collection.objects.link(env)
    L = 900
    if seg == "A":
        box("ENV_road", (0, 0, -0.02), (L, 14, 0.04), (0.46, 0.46, 0.47), env)
        for x in np.arange(-L / 2, L / 2, 9):
            box("ENV_dash", (x, 2.1, 0.005), (3.0, 0.14, 0.01), (0.85, 0.85, 0.82), env)
            box("ENV_dash", (x + 4.5, -5.3, 0.005), (3.0, 0.14, 0.01), (0.85, 0.85, 0.82), env)
        box("ENV_kerbL", (0, 7.6, 0.1), (L, 1.2, 0.2), (0.70, 0.69, 0.66), env)
        box("ENV_kerbR", (0, -7.6, 0.1), (L, 1.2, 0.2), (0.70, 0.69, 0.66), env)
        for x in np.arange(-L / 2, L / 2, 3.2):                       # rock revetment on the sea side
            s = rng.uniform(0.8, 1.6)
            box("ENV_rock", (x, 9.3 + rng.uniform(-0.4, 0.4), 0.3), (s, s * 0.9, s * 0.7), (0.45, 0.42, 0.38), env,
                rot=(rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(0, 3)))
        box("ENV_sea", (0, 160, -0.3), (L * 2, 300, 0.1), (0.62, 0.68, 0.72), env)
        box("ENV_verge", (0, -60, -0.03), (L * 2, 100, 0.05), (0.58, 0.55, 0.48), env)
        for x in np.arange(-L / 2, L / 2, 16):
            palm(env, x + rng.uniform(-2, 2), -9.5, rng.uniform(9, 13), rng.uniform(-0.12, 0.05), rng)
            if rng.random() < 0.5:
                palm(env, x + 8, 8.6, rng.uniform(8, 12), rng.uniform(-0.05, 0.12), rng)
        sky = (0.90, 0.90, 0.91)
    else:
        box("ENV_road", (0, 0, -0.02), (L, 10, 0.04), (0.20, 0.21, 0.23), env)
        for x in np.arange(-L / 2, L / 2, 9):
            box("ENV_dash", (x, 0.0 - 1.9, 0.005), (3.0, 0.13, 0.01), (0.86, 0.87, 0.88), env)
        box("ENV_edgeL", (0, 4.6, 0.005), (L, 0.12, 0.01), (0.86, 0.87, 0.88), env)
        box("ENV_snowL", (0, 40, 0.15), (L, 70, 0.3), (0.90, 0.91, 0.93), env)
        box("ENV_snowR", (0, -40, 0.15), (L, 70, 0.3), (0.90, 0.91, 0.93), env)
        for x in np.arange(-L / 2, L / 2, 11):
            bare_tree(env, x + rng.uniform(-3, 3), 8 + rng.uniform(0, 6), rng.uniform(7, 12), rng)
            bare_tree(env, x + rng.uniform(-3, 3), -8 - rng.uniform(0, 6), rng.uniform(7, 12), rng)
        # mountains: far, static in the car frame (parallax negligible)
        for k in range(28):
            a = k / 28 * 2 * math.pi
            r = rng.uniform(900, 1300)
            h = rng.uniform(140, 260)
            bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=h * 1.3, depth=h,
                                            location=(math.cos(a) * r, math.sin(a) * r, h / 2 - 10))
            m = bpy.context.object
            m.color = (0.90, 0.91, 0.94, 1)
        sky = (0.86, 0.87, 0.89)
    return env, sky


# --------------------------------------------------------------------------------------- animation
def cam_at(seg, t):
    K = KEYS[seg]
    loc = Vector(hermite(K, t, 1))
    tgt = Vector(hermite(K, t, 2))
    roll, lens = hermite(K, t, 3), hermite(K, t, 4)
    q = (tgt - loc).to_track_quat("-Z", "Y")
    q = q @ Quaternion((0, 0, 1), math.radians(roll))
    return loc, q, lens


def pose(seg, objs, env, t):
    t0 = SEG[seg][0]
    env.location.x = -ROAD_SPEED[seg] * (t - t0)
    spin = ROAD_SPEED[seg] * (t - t0) / 0.35          # wheel angle (rad)
    for k in ("wFL", "wFR", "wRL", "wRR"):
        if k in objs:
            objs[k].rotation_euler = (0, -spin, 0)
    if seg == "A":
        h = objs["hood"]
        h0 = h.get("rest") or tuple(h.location)
        h["rest"] = h0
        u = smoothstep((t - 2.20) / 0.45)            # stock bonnet bursts off up and back
        h.location = Vector(h0) + Vector((-2.5 * u, 0.6 * u, 6.0 * u ** 1.6))
        h.rotation_euler = (0.4 * u, -1.1 * u, 0.3 * u)
        h.hide_render = t > 2.75
        n = objs["newhood"]
        n.hide_render = t < 3.02
        if t < 3.6:          # drops in from above the frame, fast, decelerating
            v = smoothstep((t - 3.02) / 0.58)
            off = Vector((0.9, 0, 9.0 * (1 - v) + 0.95 * v))
            rot = (0.25 * (1 - v), 0.55, 0.15 * (1 - v))
        elif t < 6.0:        # floats: slow descent with a gentle sway
            v = (t - 3.6) / 2.4
            off = Vector((0.9 * (1 - v) + 0.45 * v, 0.06 * math.sin(t * 1.7), 0.95 * (1 - v) + 0.45 * v))
            rot = (0.06 * math.sin(t * 1.3), 0.55 * (1 - v) + 0.20 * v, 0.07 * math.sin(t * 1.1))
        else:                # lands and seats
            v = smoothstep((t - 6.0) / 0.9)
            off = Vector((0.45 * (1 - v), 0, 0.45 * (1 - v)))
            rot = (0, 0.20 * (1 - v), 0)
        n.location = Vector(h0) + off
        n.rotation_euler = rot
    else:
        w = objs["wing"]
        w0 = w.get("rest") or tuple(w.location)
        w["rest"] = w0
        u = smoothstep((t - 10.45) / 0.40)
        w.location = Vector(w0) + Vector((0.12 * (1 - u), 0, -0.30 * (1 - u)))
        w.rotation_euler = (0, 0.25 * (1 - u), 0)


def setup(seg, res):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    objs = build_car(seg)
    env, sky = build_env(seg)
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "OBJECT"
    sh.show_shadows = True
    sh.shadow_intensity = 0.55
    sh.show_cavity = False
    sh.cavity_type = "BOTH"
    sh.show_specular_highlight = True
    sc.world = bpy.data.worlds.new("SKY")
    sc.world.color = sky
    sc.display.light_direction = (0.35, -0.25, 0.9) if seg == "A" else (-0.2, 0.3, 0.92)
    sc.display.render_aa = "5"
    sc.render.resolution_x = res * 9 // 16 // 2 * 2
    sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    cam = bpy.data.objects.new("CAM", bpy.data.cameras.new("CAM"))
    sc.collection.objects.link(cam)
    cam.data.sensor_fit = "VERTICAL"
    cam.data.sensor_height = 24
    cam.data.clip_start = 0.02
    cam.data.clip_end = 5000
    sc.camera = cam
    return sc, cam, objs, env


def render(seg, times, outdir, res):
    sc, cam, objs, env = setup(seg, res)
    for name, t in times:
        loc, q, lens = cam_at(seg, t)
        cam.location = loc
        cam.rotation_mode = "QUATERNION"
        cam.rotation_quaternion = q
        cam.data.lens = lens                        # on a 24 mm vertical sensor (9:16 frame)
        pose(seg, objs, env, t)
        sc.render.filepath = f"{outdir}/{name}.png"
        bpy.ops.render.render(write_still=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--seg", default="A")
    ap.add_argument("--f0", type=int, default=0)
    ap.add_argument("--f1", type=int, default=-1)
    ap.add_argument("--stills", default="")
    ap.add_argument("--out", default="/home/user/guide/out")
    ap.add_argument("--res", type=int, default=720)
    a = ap.parse_args(argv)
    t0, t1 = SEG[a.seg]
    if a.stills:
        times = [(f"t{float(s):05.2f}", float(s)) for s in a.stills.split(",")]
    else:
        n = int(round((t1 - t0) * FPS))
        f1 = n if a.f1 < 0 else min(a.f1, n)
        times = [(f"{f:04d}", t0 + f / FPS) for f in range(a.f0, f1 + 1)]
    render(a.seg, times, a.out, a.res)
    print("DONE", len(times))


main()
