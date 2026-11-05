"""Free previs (no AI credits) of the reel core, 1:1 with ANALIZA_ORYGINALU.md.

Blender 4.5 headless, EEVEE (Next) in the Higgsfield sandbox. Same car mesh and scenery as guide.py, plus what
the analysis found and the grey-box guide lacked:
  - materials: gloss paint with clear coat, tinted glass, black trim, tyres, stock black rims (before) and gold
    MSP02 rims with a chrome lip (after); a cloudy overcast sky; a wet, reflective road in the snow world;
  - time dilation of the whole scene (road, wheels): real time to 2.5 s, ramp-down to about 1/40 by 3.0 s,
    slow motion to 6.5 s, ramp-up back to real time by 8.25 s;
  - the stock bonnet opens on its hinge (2.20-2.42) and then tears off up and to the left (2.42-2.75);
  - the new bonnet (white, two black louvred vents) drops in from far above standing upright like a shield
    (3.05-3.40), tips from vertical to flat over its front edge while it hovers (3.40-6.10) and lands (6.30-6.80);
  - the camera moves to the front-right 3/4 and dives low along the bonnet into the right vent until the frame
    is only paint (8.45); the snow world starts on the right-side door paint below the window and pulls out
    (8.95), the swan-neck wing deploys (10.40-10.90);
  - real motion blur (270 deg shutter) and depth of field from keyframed animation.

    blender -b -P previs.py -- --seg A --stills 2.3,3.3,4.5,8.0 --out DIR [--res 960]
    blender -b -P previs.py -- --seg A --f0 0 --f1 60 --out DIR        # frames, 30 fps, from SEG start

Segment A = film 1.04-8.45 s, segment B = film 8.95-13.30 s. The 8.45-8.95 paint hold and the bookends are
added in the edit (previs_edit.sh). Car frame: car at the origin facing +X, left = +Y, metres.
"""
import argparse
import math
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

FPS = 30
CAR_GLB = "/home/user/guide/car.glb"
SCALE = 4.24
SEG = {"A": (1.04, 8.75), "B": (8.65, 13.32)}      # A and B overlap 8.65-8.75 for the paint match
ROAD_SPEED = {"A": 22.0, "B": 25.0}

# camera keys on the PATH clock: (path t, camera xyz, target xyz, roll deg, lens mm on a 24 mm vertical sensor).
# "DIVE*" / "DOOR*" entries are replaced at setup by points found on the actual car surface.
KEYS = {
    "A": [
        (1.04, (2.35, 1.40, 0.50), (0.40, 0.95, 0.40), -90, 14),
        (1.40, (2.30, 1.25, 0.95), (1.20, 0.80, 0.45), -84, 14),
        (1.75, (2.70, 1.10, 1.05), (1.60, 0.55, 0.50), -65, 15),
        (2.05, (3.00, 1.50, 0.60), (1.60, 0.70, 0.50), -45, 16),
        (2.30, (3.40, 1.65, 0.55), (1.50, 0.55, 0.55), -32, 17),
        (2.60, (4.50, 1.40, 0.50), (1.50, 0.20, 0.70), -10, 19),
        # metamorphosis: the camera never stops (measured on the reference at 5 fps):
        # arc from the front-left 3/4 to dead front (2.8-3.45), slow drift (3.45-5.0), then a continuous arc to
        # the front-right 3/4 with a push-in (5.0-6.9) that runs straight into the dive
        (2.85, (5.00, 1.75, 0.75), (1.40, 0.30, 0.85), -6, 20),
        (3.10, (5.90, 0.95, 0.85), (1.40, 0.10, 1.00), -3, 21),
        (3.45, (6.40, 0.15, 0.95), (1.40, 0.00, 1.20), 0, 22),
        (4.20, (6.35, 0.00, 0.95), (1.40, 0.00, 1.20), 1, 22),
        (5.00, (6.20, -0.30, 0.98), (1.40, -0.03, 1.15), 0, 22),
        (5.60, (5.85, -0.85, 1.02), (1.45, -0.06, 1.05), -1, 22),
        (6.20, (5.20, -1.40, 1.10), (1.50, -0.10, 0.95), 0, 22),
        (6.90, (4.30, -1.85, 1.20), (1.60, -0.18, 0.85), -2, 21),
        (7.55, (3.40, -1.60, 1.20), (1.80, -0.25, 0.75), -5, 20),
        (8.00, "DIVE1", "DIVEP", -9, 20),
        (8.33, "DIVE2", "DIVEP", -13, 20),
        # the reference never stops on the paint: the camera skims over the vent (it slides out of the bottom of
        # the frame) and glides on, slowing, over the bonnet paint, which becomes the new car's door paint in B
        (8.45, "VENT", "BEHIND", -13, 20),
        (8.75, "GLIDE", "GLIDET", -15, 20),
    ],
    "B": [   # path shape only: the speed along it comes from SPEED (arc length), so the motion has no stalls
        (8.65, "DOORA", "DOORAT", -36, 20),          # skimming the right-door paint, moving up towards the window
        (8.95, "DOORB", "DOORBT", -35, 20),          # the window edge slides in from the top
        (9.30, (-0.15, -1.20, 1.05), (-0.25, -0.60, 1.00), -30, 20),
        (9.60, (-0.05, -1.75, 1.10), (-0.20, -0.70, 0.95), -22, 21),
        (9.95, (0.40, -2.70, 1.08), (0.00, -0.80, 0.85), -12, 22),
        (10.30, (-1.20, -3.40, 0.95), (-0.30, -0.50, 0.75), -5, 24),
        (10.80, (-5.00, -3.10, 0.90), (-0.60, -0.20, 0.70), 0, 26),
        (11.60, (-11.0, -2.20, 1.00), (-0.50, 0.00, 0.70), 0, 28),
        (13.30, (-32.0, -1.00, 1.30), (-0.40, 0.00, 0.70), 0, 30),
    ],
}
# film clock -> path clock (speed ramps, measured): (film t0, t1, path p0, p1, shape (a, b) of u^a (1-u)^b)
WARP = {
    "A": [(1.04, 8.75, 1.04, 8.75, (0.0, 0.0))],      # keys are on the film clock: speed comes from their spacing
}
# relative camera speed (m/s, before scaling to the path length) for B: a slow glide on the door paint (continuous
# with the end of A), the burst out of the glass peaking at about 9.6, then the car pulls away ever faster; the
# curve is Gaussian-smoothed so the speed has no corners
SPEED = {"B": [(8.65, 0.5), (8.95, 0.8), (9.25, 2.2), (9.55, 6.0), (9.70, 7.5), (10.0, 6.5), (10.5, 3.0),
               (11.0, 3.0), (11.6, 5.0), (12.4, 10.0), (13.32, 16.0)]}
_ARC = {}


def arc_param(seg, K, t):
    """Path parameter at film time t such that the speed along the path follows SPEED[seg]."""
    if seg not in _ARC:
        ps = np.linspace(K[0][0], K[-1][0], 3000)
        P = np.array([hermite(K, p, 1) for p in ps])
        d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        t0, t1 = SEG[seg]
        tt = np.arange(t0 - 0.05, t1 + 0.05, 0.002)
        c = SPEED[seg]
        g = np.interp(tt, [a for a, _ in c], [b for _, b in c])
        k = np.exp(-0.5 * (np.arange(-150, 151) * 0.002 / 0.12) ** 2)
        g = np.convolve(np.pad(g, 150, mode="edge"), k / k.sum(), mode="valid")
        S = np.concatenate([[0], np.cumsum(g[:-1])])
        S = S / S[-1] * d[-1]
        _ARC[seg] = (tt, S, ps, d)
        print("PATH", seg, "length", round(float(d[-1]), 2), "m")
    tt, S, ps, d = _ARC[seg]
    return float(np.interp(np.interp(t, tt, S), d, ps))


def smoothstep(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def hermite(keys, t, idx):
    ts = [k[0] for k in keys]
    if t <= ts[0]:
        return np.array(keys[0][idx], float)
    if t >= ts[-1]:
        return np.array(keys[-1][idx], float)
    i = max(j for j in range(len(ts) - 1) if ts[j] <= t)
    t0, t1 = ts[i], ts[i + 1]
    u = (t - t0) / (t1 - t0)

    def val(j):
        return np.array(keys[min(max(j, 0), len(keys) - 1)][idx], float)
    p0, p1 = val(i), val(i + 1)
    m0 = (val(i + 1) - val(i - 1)) / (ts[min(i + 1, len(ts) - 1)] - ts[max(i - 1, 0)]) * (t1 - t0)
    m1 = (val(i + 2) - val(i)) / (ts[min(i + 2, len(ts) - 1)] - ts[i]) * (t1 - t0)
    h00, h10, h01, h11 = 2*u**3 - 3*u**2 + 1, u**3 - 2*u**2 + u, -2*u**3 + 3*u**2, u**3 - u**2
    return h00 * p0 + h10 * m0 + h01 * p1 + h11 * m1


def _ramp(u, shape):
    a, b = shape
    n = 400
    xs = (np.arange(n) + 0.5) / n
    w = xs ** a * (1 - xs) ** b
    c = np.concatenate([[0], np.cumsum(w)]) / w.sum()
    return float(np.interp(min(max(u, 0.0), 1.0), np.linspace(0, 1, n + 1), c))


def path_time(seg, t):
    W = WARP[seg]
    for t0, t1, p0, p1, shape in W:
        if t < t1 or (t0, t1) == W[-1][:2]:
            return p0 + (p1 - p0) * _ramp((t - t0) / (t1 - t0), shape)
    return W[-1][3]


# scene-time dilation (whole world slows): speed factor s(film t), integrated into scene time tau(t)
def dilation(t):
    def logmix(a, b, u):
        return math.exp(math.log(a) + (math.log(b) - math.log(a)) * u)
    if t < 2.5:
        return 1.0
    if t < 3.0:
        return logmix(1.0, 0.025, smoothstep((t - 2.5) / 0.5))
    if t < 6.5:
        return logmix(0.025, 0.07, (t - 3.0) / 3.5)
    if t < 8.25:
        return logmix(0.07, 1.0, ((t - 6.5) / 1.75) ** 1.6)
    return 1.0


def scene_time(seg, t):
    t0 = SEG[seg][0]
    if seg == "B":
        return t - t0
    xs = np.arange(t0, max(t, t0) + 1e-9, 0.001)
    return float(sum(dilation(x) for x in xs) * 0.001)


# ----------------------------------------------------------------------------------------------- materials
def principled(name, rgb, rough=0.4, metal=0.0, coat=0.0, alpha=1.0, spec=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.03
    b.inputs["Specular IOR Level"].default_value = spec
    m.diffuse_color = (*rgb, 1)
    return m


def paint_with_underside(name, rgb, under=(0.16, 0.09, 0.05)):
    """Paint on top, brown carpet-like underside (seen when the bonnet opens)."""
    m = principled(name, rgb, 0.18, 0, 1.0)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.inputs[1].default_value = (*rgb, 1)
    mix.inputs[2].default_value = (*under, 1)
    nt.links.new(geo.outputs["Backfacing"], mix.inputs[0])
    nt.links.new(mix.outputs[0], b.inputs["Base Color"])
    return m


def materials(seg):
    M = {}
    M["paint"] = principled("paint", (0.95, 0.50, 0.0) if seg == "A" else (0.80, 0.81, 0.83), 0.18, 0, 1.0)
    M["hoodpaint"] = paint_with_underside("hoodpaint", (0.95, 0.50, 0.0))
    M["newpaint"] = paint_with_underside("newpaint", (0.80, 0.81, 0.83), (0.03, 0.03, 0.03))
    M["glass"] = principled("glass", (0.010, 0.011, 0.013), 0.03, 0, 0, spec=1.0)
    M["trim"] = principled("trim", (0.015, 0.015, 0.016), 0.45)
    M["carbon"] = principled("carbon", (0.02, 0.02, 0.022), 0.28, 0, 0.6)
    M["tyre"] = principled("tyre", (0.012, 0.012, 0.012), 0.75)
    M["rim"] = principled("rim", (0.02, 0.02, 0.02), 0.35, 0.5) if seg == "A" else \
        principled("rim", (0.80, 0.55, 0.22), 0.28, 1.0)
    M["lip"] = principled("lip", (0.02, 0.02, 0.02), 0.35, 0.5) if seg == "A" else \
        principled("lip", (0.92, 0.92, 0.93), 0.06, 1.0)
    M["lamp"] = principled("lamp", (0.6, 0.62, 0.65), 0.05, 0.6, 1.0)
    M["caliper"] = principled("caliper", (0.6, 0.02, 0.02), 0.3)
    return M


# ----------------------------------------------------------------------------------------------- car
def classify(c, n):
    x, y, z = c.x, c.y, c.z                                      # model coords: front at -X
    if -0.27 < x < 0.21 and z > 0.215 and abs(n.z) < 0.85:
        return "glass"
    if z < 0.035:
        return "trim"
    if x < -0.47 and n.x < -0.55 and z < 0.095:
        return "trim"                                             # bumper intakes / splitter
    if x < -0.42 and 0.12 < z < 0.19 and abs(y) > 0.10 and n.x < -0.3:
        return "lamp"
    if x > 0.47 and n.x > 0.5 and z < 0.09:
        return "trim"                                             # diffuser
    return "paint"


def build_car(seg, M):
    bpy.ops.import_scene.gltf(filepath=CAR_GLB)
    src = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
    for o in list(bpy.context.scene.objects):
        if o != src and o.type != "MESH":
            bpy.data.objects.remove(o)
    me = src.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    groups = {"hood": [], "wing": [], "wFL": [], "wFR": [], "wRL": [], "wRR": [], "body": []}
    wheels = {"wFL": (-0.355, 1), "wFR": (-0.355, -1), "wRL": (0.225, 1), "wRR": (0.225, -1)}
    face_mat = {}
    for f in bm.faces:
        c, n = f.calc_center_median(), f.normal
        g = "body"
        for k, (wx, side) in wheels.items():
            d = math.hypot(c.x - wx, c.z - 0.083)
            if d < 0.088 and c.y * side > 0.13:
                g = k
                face_mat[f.index] = "rim" if d < 0.052 else ("lip" if d < 0.064 else "tyre")
        if g == "body":
            if -0.555 < c.x < -0.29 and abs(c.y) < 0.16 and c.z > 0.122 + (c.x + 0.591) * 0.30 - 0.012 and n.z > 0.45:
                g = "hood"
                face_mat[f.index] = "paint"
            elif c.x > 0.345 and c.z > 0.252:
                g = "wing"
                face_mat[f.index] = "carbon"
            else:
                face_mat[f.index] = classify(c, n)
        groups[g].append(f.index)
    bm.free()
    objs = {}
    S = Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Scale(SCALE, 4)
    for g, faces in groups.items():
        if not faces:
            continue
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        keep = set(faces)
        names = sorted({face_mat[i] for i in faces})
        slot = {nm: k for k, nm in enumerate(names)}
        for f in bm.faces:
            if f.index in keep:
                f.material_index = slot[face_mat[f.index]]
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context="FACES")
        nm = bpy.data.meshes.new(g)
        bm.to_mesh(nm)
        bm.free()
        nm.transform(S)
        for nmn in names:
            mm = M["hoodpaint"] if (g == "hood" and nmn == "paint" and seg == "A") else M[nmn]
            nm.materials.append(mm)
        ob = bpy.data.objects.new("CAR_" + g, nm)
        bpy.context.scene.collection.objects.link(ob)
        for p in nm.polygons:
            p.use_smooth = True
        cen = sum((v.co for v in nm.vertices), Vector()) / max(len(nm.vertices), 1)
        if g.startswith("w"):
            cen = Vector((cen.x, cen.y, 0.35))
        nm.transform(Matrix.Translation(-cen))
        ob.location = cen
        objs[g] = ob
    bpy.data.objects.remove(src)
    # dark engine-bay / luggage box under the bonnet (seen once it is gone)
    hb = objs["hood"]
    xs = [v.co.x + hb.location.x for v in hb.data.vertices]
    zs = [v.co.z + hb.location.z for v in hb.data.vertices]
    bpy.ops.mesh.primitive_cube_add(size=1, location=((min(xs) + max(xs)) / 2, 0, min(zs) - 0.12))
    bay = bpy.context.object
    bay.scale = ((max(xs) - min(xs)) * 0.92, 1.25, 0.25)
    bay.data.materials.append(principled("bay", (0.10, 0.06, 0.035), 0.8))
    if seg == "B":       # red calipers behind the gold rims
        for k in ("wFL", "wFR", "wRL", "wRR"):
            w = objs[k]
            side = 1 if w.location.y > 0 else -1
            bpy.ops.mesh.primitive_cube_add(size=1, location=(w.location.x + 0.12, w.location.y - side * 0.08,
                                                              w.location.z + 0.10))
            cp = bpy.context.object
            cp.scale = (0.16, 0.05, 0.10)
            cp.data.materials.append(M["caliper"])
    else:                # the new bonnet: white copy with two louvred vents
        nb = hb.copy()
        nb.data = hb.data.copy()
        nb.name = "CAR_newhood"
        nb.data.materials.clear()
        nb.data.materials.append(M["newpaint"])
        bpy.context.scene.collection.objects.link(nb)
        objs["newhood"] = nb
        add_vents(nb, M)
        # hinge at the bonnet's rear edge (towards the windscreen = smaller x)
        hinge = bpy.data.objects.new("HINGE", None)
        bpy.context.scene.collection.objects.link(hinge)
        rear = [hb.matrix_world @ v.co for v in hb.data.vertices]
        xr = min(p.x for p in rear)
        zr = max(p.z for p in rear if p.x < xr + 0.08)
        hinge.location = (xr, 0, zr)
        bpy.context.view_layer.update()
        hb.parent = hinge
        hb.matrix_parent_inverse = hinge.matrix_world.inverted()
        objs["hinge"] = hinge
    print("PARTS", {k: len(v) for k, v in groups.items()})
    return objs


def surface(ob, x, y, down=Vector((0, 0, -1))):
    """World hit point and normal on ob for a ray from high above (x, y)."""
    mw = ob.matrix_world
    inv = mw.inverted()
    o = inv @ Vector((x, y, 5.0))
    d = (inv.to_3x3() @ down).normalized()
    ok, loc, nrm, _ = ob.ray_cast(o, d)
    if not ok:
        return None, None
    n = (mw.to_3x3().inverted().transposed() @ nrm).normalized()
    return mw @ loc, n


def add_vents(nb, M):
    bpy.context.view_layer.update()
    xs = [v.co.x for v in nb.data.vertices]
    L = max(xs) - min(xs)
    cx = nb.location.x + min(xs) + 0.55 * L
    for side in (1, -1):
        p, n = surface(nb, cx, side * 0.30)
        if p is None:
            continue
        q = n.to_track_quat("Z", "X")
        for k, (dx, w, h, mat) in enumerate([(0, 0.36, 0.34, "trim")] + [(-0.12 + 0.08 * i, 0.035, 0.33, "carbon")
                                                                       for i in range(4)]):
            bpy.ops.mesh.primitive_cube_add(size=1)
            v = bpy.context.object
            v.name = f"VENT{side}_{k}"
            v.scale = (w, h, 0.012 if k == 0 else 0.05)
            v.rotation_mode = "QUATERNION"
            v.rotation_quaternion = q @ Quaternion((0, 1, 0), 0.0 if k == 0 else 0.5)
            v.location = p + n * (0.002 if k == 0 else 0.012) + Vector((dx, 0, 0))
            v.data.materials.append(M[mat])
            bpy.context.view_layer.update()
            mw = v.matrix_world.copy()
            v.parent = nb
            v.matrix_parent_inverse = nb.matrix_world.inverted()
            v.matrix_world = mw


# ----------------------------------------------------------------------------------------------- scenery
def obj_mat(o, m):
    o.data.materials.clear()
    o.data.materials.append(m)


_MESH = {}


def link(name, me, loc=(0, 0, 0), rot=(0, 0, 0), size=(1, 1, 1), parent=None):
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.location, o.rotation_euler, o.scale = loc, rot, size
    if parent:
        o.parent = parent
    return o


def box(name, loc, size, m, parent=None, rot=(0, 0, 0)):
    """Instanced unit cube (one mesh per material: fast even for thousands of boxes)."""
    me = _MESH.get("cube_" + m.name)
    if me is None:
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        me = bpy.data.meshes.new("cube_" + m.name)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(m)
        _MESH["cube_" + m.name] = me
    return link(name, me, loc, rot, size, parent)


def _cone(bm, r1, r2, depth, M, segs=8, mat=0):
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r1, radius2=r2, depth=depth, matrix=M)
    for f in {f for v in res["verts"] for f in v.link_faces}:
        f.material_index = mat


def proto_palm(h, mt, ml, rng, key):
    bm = bmesh.new()
    _cone(bm, 0.28, 0.16, h, Matrix.Translation((0, 0, h / 2)), 10, 0)
    for k in range(9):
        a = k / 9 * 2 * math.pi + rng.uniform(0, 0.4)
        M = (Matrix.Translation((math.cos(a) * 1.4, math.sin(a) * 1.4, h - 0.35))
             @ Matrix.Rotation(a, 4, "Z") @ Matrix.Rotation(0.45, 4, "Y")
             @ Matrix.Rotation(rng.uniform(-0.2, 0.2), 4, "X") @ Matrix.Diagonal((2.8, 0.55, 1, 1)))
        res = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5, matrix=M)
        for f in {f for v in res["verts"] for f in v.link_faces}:
            f.material_index = 1
    me = bpy.data.meshes.new(key)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mt)
    me.materials.append(ml)
    return me


def proto_tree(h, mt, rng, key):
    bm = bmesh.new()
    _cone(bm, 0.22, 0.04, h, Matrix.Translation((0, 0, h / 2)), 8)
    for k in range(7):
        z = h * rng.uniform(0.35, 0.85)
        a = rng.uniform(0, 2 * math.pi)
        L = h * rng.uniform(0.18, 0.32)
        M = (Matrix.Translation((math.cos(a) * L * 0.35, math.sin(a) * L * 0.35, z + L * 0.3))
             @ Matrix.Rotation(-0.9 * math.cos(a), 4, "Y") @ Matrix.Rotation(0.9 * math.sin(a), 4, "X"))
        _cone(bm, 0.04, 0.02, L, M, 6)
    me = bpy.data.meshes.new(key)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mt)
    return me


def palm(env, x, y, h, lean, rng, mt, ml):
    key = f"palm{int(round(h))}"
    if key not in _MESH:
        _MESH[key] = proto_palm(round(h), mt, ml, rng, key)
    link("ENV_palm", _MESH[key], (x, y, 0), (lean, 0, rng.uniform(0, 6.28)), parent=env)


def bare_tree(env, x, y, h, rng, mt):
    key = f"tree{int(round(h))}"
    if key not in _MESH:
        _MESH[key] = proto_tree(round(h), mt, rng, key)
    link("ENV_tree", _MESH[key], (x, y, 0), (0, 0, rng.uniform(0, 6.28)), parent=env)


def road_material(name, rgb, rough, wet=False):
    m = principled(name, rgb, rough)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.35 if wet else 2.0
    nz.inputs["Detail"].default_value = 6
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    if wet:                       # puddles: mirror-like patches
        ramp.color_ramp.elements[0].position = 0.45
        ramp.color_ramp.elements[0].color = (0.02, 0.02, 0.02, 1)
        ramp.color_ramp.elements[1].position = 0.55
        ramp.color_ramp.elements[1].color = (0.30, 0.30, 0.30, 1)
        nt.links.new(ramp.outputs["Color"], b.inputs["Roughness"])
    else:
        # asphalt that reads in motion: large patches x fine aggregate grain (about 2 cm), like the reference
        ramp.color_ramp.elements[0].color = (rgb[0] * 0.7, rgb[1] * 0.7, rgb[2] * 0.7, 1)
        ramp.color_ramp.elements[1].color = (rgb[0] * 1.3, rgb[1] * 1.3, rgb[2] * 1.3, 1)
        grain = nt.nodes.new("ShaderNodeTexNoise")
        grain.inputs["Scale"].default_value = 55.0
        grain.inputs["Detail"].default_value = 2
        nt.links.new(tc.outputs["Object"], grain.inputs["Vector"])
        gr = nt.nodes.new("ShaderNodeValToRGB")
        gr.color_ramp.elements[0].position, gr.color_ramp.elements[0].color = 0.35, (0.55, 0.55, 0.55, 1)
        gr.color_ramp.elements[1].position, gr.color_ramp.elements[1].color = 0.65, (1.45, 1.45, 1.45, 1)
        nt.links.new(grain.outputs["Fac"], gr.inputs["Fac"])
        mul = nt.nodes.new("ShaderNodeMix")
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        mul.inputs["Factor"].default_value = 1.0
        nt.links.new(ramp.outputs["Color"], mul.inputs["A"])
        nt.links.new(gr.outputs["Color"], mul.inputs["B"])
        nt.links.new(mul.outputs["Result"], b.inputs["Base Color"])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.35
        nt.links.new(grain.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def build_env(seg):
    rng = np.random.default_rng(7)
    env = bpy.data.objects.new("ENV", None)
    bpy.context.scene.collection.objects.link(env)
    L, X0 = 700, 150
    line = principled("line", (0.75, 0.75, 0.72), 0.5)
    if seg == "A":
        road = box("ENV_road", (X0, 0, -0.02), (L, 14, 0.04), road_material("asphalt", (0.10, 0.10, 0.10), 0.7), env)
        for x in np.arange(X0 - L / 2, X0 + L / 2, 9):
            box("ENV_dash", (x, 2.1, 0.005), (3.0, 0.14, 0.01), line, env)
            box("ENV_dash", (x + 4.5, -5.3, 0.005), (3.0, 0.14, 0.01), line, env)
        kerb = principled("kerb", (0.45, 0.44, 0.41), 0.8)
        box("ENV_kerbL", (X0, 7.6, 0.1), (L, 1.2, 0.2), kerb, env)
        box("ENV_kerbR", (X0, -7.6, 0.1), (L, 1.2, 0.2), kerb, env)
        rock = principled("rock", (0.20, 0.18, 0.15), 0.9)
        for x in np.arange(X0 - L / 2, X0 + L / 2, 3.2):
            s = rng.uniform(0.8, 1.6)
            box("ENV_rock", (x, 9.3 + rng.uniform(-0.4, 0.4), 0.3), (s, s * 0.9, s * 0.7), rock, env,
                rot=(rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(0, 3)))
        box("ENV_sea", (0, 160, -0.3), (L * 2, 300, 0.1), principled("sea", (0.30, 0.38, 0.42), 0.15), env)
        box("ENV_verge", (0, -60, -0.03), (L * 2, 100, 0.05), principled("verge", (0.32, 0.29, 0.22), 0.9), env)
        mt, ml = principled("trunk", (0.22, 0.17, 0.12), 0.9), principled("leaf", (0.06, 0.13, 0.05), 0.6)
        for x in np.arange(X0 - L / 2, X0 + L / 2, 16):
            palm(env, x + rng.uniform(-2, 2), -9.5, rng.uniform(9, 13), rng.uniform(-0.12, 0.05), rng, mt, ml)
            if rng.random() < 0.5:
                palm(env, x + 8, 8.6, rng.uniform(8, 12), rng.uniform(-0.05, 0.12), rng, mt, ml)
    else:
        road = box("ENV_road", (X0, 0, -0.02), (L, 10, 0.04), road_material("wet", (0.025, 0.027, 0.03), 0.1, True), env)
        for x in np.arange(X0 - L / 2, X0 + L / 2, 9):
            box("ENV_dash", (x, -1.9, 0.005), (3.0, 0.13, 0.01), line, env)
        box("ENV_edgeL", (X0, 4.6, 0.005), (L, 0.12, 0.01), line, env)
        box("ENV_edgeR", (X0, -4.6, 0.005), (L, 0.12, 0.01), line, env)
        snow = principled("snow", (0.78, 0.80, 0.84), 0.85)
        box("ENV_snowL", (X0, 40, 0.15), (L, 70, 0.3), snow, env)
        box("ENV_snowR", (X0, -40, 0.15), (L, 70, 0.3), snow, env)
        mt = principled("bark", (0.04, 0.035, 0.03), 0.9)
        for x in np.arange(X0 - L / 2, X0 + L / 2, 11):
            bare_tree(env, x + rng.uniform(-3, 3), 8 + rng.uniform(0, 6), rng.uniform(7, 12), rng, mt)
            bare_tree(env, x + rng.uniform(-3, 3), -8 - rng.uniform(0, 6), rng.uniform(7, 12), rng, mt)
        # jagged snowy ranges: many overlapping low-poly peaks, snow and dark rock (static, far away)
        mtn = principled("mountain", (0.78, 0.82, 0.88), 0.9)
        rock = principled("mrock", (0.36, 0.41, 0.48), 0.9)
        for k in range(110):
            a = rng.uniform(0, 2 * math.pi)
            r = rng.uniform(900, 1500)
            h = rng.uniform(50, 150)
            bm = bmesh.new()
            _cone(bm, h * rng.uniform(0.8, 1.5), 0.0, h, Matrix(), int(rng.integers(4, 7)))
            me = bpy.data.meshes.new("peak")
            bm.to_mesh(me)
            bm.free()
            me.materials.append(mtn if rng.random() < 0.7 else rock)
            link("ENV_peak", me, (math.cos(a) * r, math.sin(a) * r, h / 2 - 15),
                 (rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), rng.uniform(0, 3)))
    road.data.transform(Matrix.Diagonal((*road.scale, 1)))       # real metres for the asphalt texture
    road.scale = (1, 1, 1)
    return env


def world(seg):
    w = bpy.data.worlds.new("SKY")
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    z01 = nt.nodes.new("ShaderNodeMath")
    z01.operation = "MULTIPLY_ADD"
    z01.inputs[1].default_value = 0.5
    z01.inputs[2].default_value = 0.5
    nt.links.new(sep.outputs["Z"], z01.inputs[0])
    nt.links.new(z01.outputs[0], ramp.inputs["Fac"])
    hor, zen, gnd = ((1.00, 0.97, 0.93), (0.80, 0.82, 0.85), (0.25, 0.24, 0.22)) if seg == "A" else \
        ((0.88, 0.93, 0.98), (0.62, 0.68, 0.76), (0.25, 0.27, 0.30))
    r = ramp.color_ramp
    r.elements[0].position, r.elements[0].color = 0.49, (*gnd, 1)
    r.elements[1].position, r.elements[1].color = 0.85, (*zen, 1)
    e = r.elements.new(0.502)
    e.color = (*hor, 1)
    # soft clouds: noise on the view direction, only above the horizon
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 4.5
    nz.inputs["Detail"].default_value = 8
    nz.inputs["Roughness"].default_value = 0.62
    nt.links.new(tc.outputs["Generated"], nz.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position, cr.color_ramp.elements[0].color = 0.42, (1, 1, 1, 1)
    cr.color_ramp.elements[1].position = 0.62
    cr.color_ramp.elements[1].color = (0.70, 0.71, 0.74, 1) if seg == "A" else (0.42, 0.47, 0.55, 1)
    nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"])
    mask = nt.nodes.new("ShaderNodeMapRange")
    mask.inputs["From Min"].default_value = 0.505
    mask.inputs["From Max"].default_value = 0.56
    mask.inputs["To Min"].default_value = 0.0
    mask.inputs["To Max"].default_value = 0.9
    nt.links.new(z01.outputs[0], mask.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    nt.links.new(mask.outputs[0], mix.inputs["Factor"])
    nt.links.new(ramp.outputs["Color"], mix.inputs["A"])
    nt.links.new(cr.outputs["Color"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.25
    return w


# ----------------------------------------------------------------------------------------------- animation
def resolve_keys(seg, objs):
    """Replace the symbolic dive / door keys with points on the real surface."""
    K = []
    if seg == "A":
        nb = objs["newhood"]
        bpy.context.view_layer.update()
        xs = [v.co.x for v in nb.data.vertices]
        L = max(xs) - min(xs)
        px = nb.location.x + min(xs) + 0.80 * L                       # just ahead of the right vent
        P, N = surface(nb, px, -0.30)
        print("DIVE point", P, N)
        sym = {"DIVEP": P, "DIVE1": P + Vector((0.95, -0.60, 0.35)), "DIVE2": P + Vector((0.22, -0.10, 0.14)),
               }
        xv = nb.location.x + min(xs) + 0.55 * L                       # vent centre (see add_vents)
        V, NV = surface(nb, xv, -0.30)
        B1, NB1 = surface(nb, xv - 0.34, -0.30)       # vent spans xv +-0.18
        B2, _ = surface(nb, xv - 0.44, -0.30)
        # look down into the paint (targets below the surface), so the frame is paint only once past the vent
        sym.update({"VENT": V + NV * 0.13, "BEHIND": B1 - NB1 * 0.30,
                    "GLIDE": B1 + NB1 * 0.06 + Vector((-0.03, 0, 0)), "GLIDET": B2 - NB1 * 0.20})
    else:
        body = objs["body"]
        mw = body.matrix_world
        inv = mw.inverted()

        def door(z):
            o = inv @ Vector((-0.25, -4.0, z))
            ok, loc, nrm, _ = body.ray_cast(o, (inv.to_3x3() @ Vector((0, 1, 0))).normalized())
            return mw @ loc if ok else Vector((-0.25, -0.90, z))
        DA, DB = door(0.62), door(0.80)
        print("DOOR points", DA, DB)
        sym = {"DOORA": DA + Vector((0.0, -0.05, 0.0)), "DOORAT": DA + Vector((0.04, 0.5, 0.12)),
               "DOORB": DB + Vector((0.0, -0.10, 0.0)), "DOORBT": DB + Vector((0.0, 0.5, 0.15))}
    for t, c, g, r, l in KEYS[seg]:
        K.append((t, tuple(sym[c]) if isinstance(c, str) else c, tuple(sym[g]) if isinstance(g, str) else g, r, l))
    return K


def cam_at(seg, K, t):
    p = arc_param(seg, K, t) if seg in SPEED else path_time(seg, t)
    loc = Vector(hermite(K, p, 1))
    tgt = Vector(hermite(K, p, 2))
    roll, lens = float(hermite(K, p, 3)), float(hermite(K, p, 4))
    if seg == "A":       # drone float during the slow-motion act: tiny drift and roll, never a locked frame
        w = smoothstep((t - 2.9) / 0.6) * (1 - smoothstep((t - 6.6) / 0.6))
        loc += Vector((0, 0.05 * math.sin(2 * math.pi * (t - 2.9) / 3.3), 0.03 * math.sin(2 * math.pi * (t - 2.9) / 2.4))) * w
        roll += 1.4 * math.sin(2 * math.pi * (t - 2.9) / 2.8) * w
    q = (tgt - loc).to_track_quat("-Z", "Y") @ Quaternion((0, 0, 1), math.radians(roll))
    return loc, q, lens, (tgt - loc).length


def pose(seg, objs, env, t, rest):
    tau = scene_time(seg, t)
    # the car is not on rails: sprung body (heave, pitch, roll) over the wheels, a little lane wander and yaw,
    # all on the scene clock so they slow down with the slow motion; squat as it pulls away in B
    T = tau
    pitch = math.radians(0.22) * math.sin(2 * math.pi * 1.3 * T + 0.5) + math.radians(0.08) * math.sin(2 * math.pi * 2.9 * T)
    if seg == "B":
        pitch -= math.radians(0.7) * smoothstep((t - 10.3) / 0.6) * (1 - 0.5 * smoothstep((t - 11.6) / 1.2))
    objs["rig"].location = rest["rig"] + Vector((0, 0, 0.004 * math.sin(2 * math.pi * 1.7 * T)
                                                   + 0.002 * math.sin(2 * math.pi * 3.1 * T + 1.0)))
    objs["rig"].rotation_euler = (math.radians(0.18) * math.sin(2 * math.pi * 0.9 * T + 2.0), pitch, 0)
    objs["all"].location = (0, 0.05 * math.sin(2 * math.pi * 0.22 * T), 0)
    objs["all"].rotation_euler = (0, 0, math.radians(0.35) * math.sin(2 * math.pi * 0.22 * T + 1.3))
    env.location.x = -ROAD_SPEED[seg] * tau
    spin = ROAD_SPEED[seg] * tau / 0.35
    for k in ("wFL", "wFR", "wRL", "wRR"):
        objs[k].rotation_euler = (0, -spin, 0)
    if seg == "A":
        hg = objs["hinge"]
        h0 = rest["hinge"]
        a = smoothstep((t - 2.20) / 0.22) * math.radians(62)               # opens on the hinge
        u = smoothstep((t - 2.42) / 0.33)                                   # then tears off up and left
        hg.location = h0 + Vector((-1.6 * u, -2.4 * u, 5.0 * u ** 1.4))
        hg.rotation_euler = (0.9 * u, -a - 1.4 * u, 0.6 * u)
        objs["hood"].hide_render = t > 2.80
        n = objs["newhood"]
        n0 = rest["newhood"]
        n.hide_render = t < 3.05
        n.rotation_mode = "XYZ"
        up = math.radians(78)                   # upright, leaning back a little, as in the reference
        if t < 3.40:          # from far above, upright like a shield facing the camera, growing as it nears
            v = smoothstep((t - 3.05) / 0.35) ** 0.7
            off = Vector((-0.35, 0, -0.12)).lerp(Vector((-28.0, 0, 22.0)), 1 - v)
            rot = (0.0, up, 0.25 * (1 - v))
        else:                 # hovers upright to 4.4, tips flat over its front edge by 6.2, lands 6.2-6.65
            tilt = smoothstep((t - 4.40) / 1.80)
            land = smoothstep((t - 6.20) / 0.45)
            a = smoothstep((t - 3.40) / 0.6) * (1 - land)           # sway fades in after the entry, out on landing
            lean = up - math.radians(6) * smoothstep((t - 3.40) / 1.0)
            off = Vector(((-0.35 * (1 - tilt) + 0.05 * tilt) * (1 - land), 0.05 * math.sin(t * 1.6) * a,
                          (-0.12 * (1 - tilt) + 0.25 * tilt) * (1 - land)))
            rot = (0.05 * math.sin(t * 1.2) * a, lean * (1 - tilt), 0.05 * math.sin(t * 0.9) * a)
        # pivot about the bonnet's front edge while upright: shift so the front edge stays put
        L = rest["hoodlen"]
        piv = Vector((L / 2, 0, 0))
        R = Matrix.Rotation(rot[0], 3, "X") @ Matrix.Rotation(rot[1], 3, "Y") @ Matrix.Rotation(rot[2], 3, "Z")
        n.location = n0 + off + (piv - R @ piv)
        n.rotation_euler = rot
    else:
        w = objs["wing"]
        u = smoothstep((t - 10.40) / 0.50)
        w.location = rest["wing"] + Vector((0.15 * (1 - u), 0, -0.45 * (1 - u)))
        w.rotation_euler = (0, 0.25 * (1 - u), 0)


def setup(seg, res, samples):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    M = materials(seg)
    objs = build_car(seg, M)
    env = build_env(seg)
    sc.world = world(seg)
    sun = bpy.data.objects.new("SUN", bpy.data.lights.new("SUN", "SUN"))
    sc.collection.objects.link(sun)
    sun.data.energy = 2.2 if seg == "A" else 1.6
    sun.data.angle = math.radians(25)
    sun.data.color = (1.0, 0.97, 0.92) if seg == "A" else (0.92, 0.96, 1.0)
    sun.rotation_euler = (math.radians(35), 0, math.radians(-40 if seg == "A" else 140))
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    ee = sc.eevee
    ee.taa_render_samples = samples
    ee.use_raytracing = seg == "B"                               # wet-road reflections; saves time in A
    ee.ray_tracing_method = "SCREEN"
    ee.ray_tracing_options.resolution_scale = "2"
    ee.use_shadows = True
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.75                          # 270 deg
    sc.render.resolution_x = res * 9 // 16 // 2 * 2
    sc.render.resolution_y = res
    sc.render.fps = FPS
    sc.view_settings.view_transform = "Khronos PBR Neutral"
    sc.view_settings.exposure = 0.0
    cam = bpy.data.objects.new("CAM", bpy.data.cameras.new("CAM"))
    sc.collection.objects.link(cam)
    cam.data.sensor_fit = "VERTICAL"
    cam.data.sensor_height = 24
    cam.data.clip_start = 0.01
    cam.data.clip_end = 6000
    cam.data.dof.use_dof = True
    cam.rotation_mode = "QUATERNION"
    sc.camera = cam
    bpy.context.view_layer.update()
    # rig: CAR_ALL (lane wander, yaw) > wheels, calipers and CAR_RIG (sprung body, pivot near the axle line)
    allr = bpy.data.objects.new("CAR_ALL", None)
    rig = bpy.data.objects.new("CAR_RIG", None)
    sc.collection.objects.link(allr)
    sc.collection.objects.link(rig)
    rig.location = (0.1, 0, 0.45)
    bpy.context.view_layer.update()
    tops = [o for o in sc.objects if o.parent is None and o not in (allr, rig, cam, sun, env)
            and not o.name.startswith("ENV")]
    rig.parent = allr
    for o in tops:
        unsprung = o.name.startswith("CAR_w") or "caliper" in [m.name for m in getattr(o.data, "materials", [])]
        p = allr if unsprung else rig
        o.parent = p
        o.matrix_parent_inverse = p.matrix_world.inverted()
    print("RIG", sorted(o.name for o in tops))
    objs["rig"], objs["all"] = rig, allr
    bpy.context.view_layer.update()
    rest = {k: objs[k].location.copy() for k in ("hinge", "newhood", "wing", "rig") if k in objs}
    if "newhood" in objs:
        xs = [v.co.x for v in objs["newhood"].data.vertices]
        rest["hoodlen"] = max(xs) - min(xs)
    return sc, cam, objs, env, rest


def fstop(seg, t):
    if seg == "A":
        return 2.0 if t > 7.4 else (5.6 if t < 2.9 else 4.0)
    return 2.0 if t < 9.8 else 4.0


def animate(seg, sc, cam, objs, env, rest, K):
    t0, t1 = SEG[seg]
    n = int(round((t1 - t0) * FPS))
    sc.frame_start, sc.frame_end = 1, n + 1
    movers = [o for k, o in objs.items() if k in ("wFL", "wFR", "wRL", "wRR", "hinge", "hood", "newhood", "wing",
                                                       "rig", "all")]
    for f in range(0, n + 3):
        t = t0 + (f - 1) / FPS
        loc, q, lens, dist = cam_at(seg, K, t)
        cam.location, cam.rotation_quaternion, cam.data.lens = loc, q, lens
        cam.data.dof.focus_distance = max(dist, 0.05)
        cam.data.dof.aperture_fstop = fstop(seg, t)
        pose(seg, objs, env, t, rest)
        for p in ("location", "rotation_quaternion"):
            cam.keyframe_insert(p, frame=f)
        cam.data.keyframe_insert("lens", frame=f)
        cam.data.dof.keyframe_insert("focus_distance", frame=f)
        cam.data.dof.keyframe_insert("aperture_fstop", frame=f)
        env.keyframe_insert("location", frame=f)
        for o in movers:
            o.keyframe_insert("location", frame=f)
            o.keyframe_insert("rotation_euler", frame=f)
            o.keyframe_insert("hide_render", frame=f)
    for a in bpy.data.actions:
        for fc in (a.fcurves if hasattr(a, "fcurves") else []):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT" if fc.data_path == "hide_render" else "LINEAR"
    return n


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--seg", default="A")
    ap.add_argument("--f0", type=int, default=0)
    ap.add_argument("--f1", type=int, default=-1)
    ap.add_argument("--stills", default="")
    ap.add_argument("--out", default="/home/user/previs/out")
    ap.add_argument("--res", type=int, default=960)
    ap.add_argument("--samples", type=int, default=12)
    ap.add_argument("--probe", action="store_true", help="print what the camera sees instead of rendering")
    a = ap.parse_args(argv)
    sc, cam, objs, env, rest = setup(a.seg, a.res, a.samples)
    K = resolve_keys(a.seg, objs)
    n = animate(a.seg, sc, cam, objs, env, rest, K)
    t0 = SEG[a.seg][0]
    if a.stills:
        frames = [(f"t{float(s):05.2f}", int(round((float(s) - t0) * FPS))) for s in a.stills.split(",")]
    else:
        f1 = n if a.f1 < 0 else min(a.f1, n)
        frames = [(f"{f:04d}", f) for f in range(a.f0, f1 + 1)]
    import time
    import os
    for name, f in frames:
        if not a.stills and os.path.exists(f"{a.out}/{name}.png"):
            continue                                              # resume an interrupted chunk
        st = time.time()
        sc.frame_set(f + 1)
        if a.probe:                       # what does the camera see? (centre and corners), no render
            dg = bpy.context.evaluated_depsgraph_get()
            cw = cam.matrix_world
            for u, v in ((0, 0), (-0.25, -0.4), (0.25, 0.4)):
                d = (cw.to_3x3() @ Vector((u * 0.56, v, -1.0))).normalized()
                hit, loc, nrm, idx, ob, _ = sc.ray_cast(dg, cw.translation, d)
                print("PROBE", name, (u, v), ob.name if hit else None, round((loc - cw.translation).length, 3) if hit else None)
            print("CAM", name, tuple(round(x, 3) for x in cw.translation))
            continue
        sc.render.filepath = f"{a.out}/{name}.png"
        bpy.ops.render.render(write_still=True)
        print("FRAME", name, round(time.time() - st, 1), flush=True)
    print("DONE", len(frames))


main()
