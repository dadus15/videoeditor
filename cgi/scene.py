"""Turismo Inventa wheel + white studio, built procedurally with Blender's Python module (bpy).

The wheel is modelled after the Turismo Inventa seen on the client's Audi S8 film: five split (twin)
spokes in a star, a deep concave face, a polished outer lip, five lug nuts between the arms and a dark
centre cap carrying the Turismo GT mark. It is an approximation built from the film, not CAD data.

Local wheel space: axle = +Z, face toward +Z, wheel centre at the origin, units = metres (19" class).
`WheelRig.root` stands the wheel up (face toward -Y), `WheelRig.spin` turns it about the axle.
"""
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / "work" / "tex"

R_LIP = 0.262          # outer radius of the lip
R_LIP_IN = 0.229       # where the spokes meet the lip
R_HUB = 0.064
N_ARMS = 5

# Six finishes, like the reference film's line-up. Values are linear-space Principled BSDF settings.
FINISHES = {
    "gloss_black":  dict(base=(0.012, 0.012, 0.014), metallic=0.0, rough=0.06, coat=1.0, lip=(0.80, 0.81, 0.83)),
    "satin_black":  dict(base=(0.010, 0.010, 0.011), metallic=0.0, rough=0.38, coat=0.0, lip=None),
    "hyper_silver": dict(base=(0.62, 0.63, 0.66), metallic=1.0, rough=0.24, coat=0.3, lip=None),
    "brushed":      dict(base=(0.86, 0.87, 0.89), metallic=1.0, rough=0.14, coat=0.0, lip=(0.92, 0.92, 0.93), aniso=0.6),
    "gunmetal":     dict(base=(0.20, 0.21, 0.23), metallic=1.0, rough=0.30, coat=0.4, lip=None),
    "bronze":       dict(base=(0.40, 0.31, 0.21), metallic=1.0, rough=0.30, coat=0.4, lip=None),
}


# ----------------------------------------------------------------------------------------- helpers

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def link(obj, parent=None):
    bpy.context.scene.collection.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def mesh_obj(name, bm, parent=None, sharp_deg=32.0):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    if hasattr(me, "set_sharp_from_angle"):
        me.set_sharp_from_angle(angle=math.radians(sharp_deg))
    return link(bpy.data.objects.new(name, me), parent)


def lathe(profile, steps=192):
    """Spin a closed (r, z) profile around Z."""
    bm = bmesh.new()
    verts = [bm.verts.new((r, 0.0, z)) for r, z in profile]
    edges = [bm.edges.new((verts[i], verts[(i + 1) % len(verts)])) for i in range(len(verts))]
    bmesh.ops.spin(bm, geom=verts + edges, cent=(0, 0, 0), axis=(0, 0, 1),
                   angle=math.tau, steps=steps, use_merge=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def sweep(stations, section):
    """Loft a closed cross-section along a list of (centre, width, thickness) stations.

    section: list of (u, v) in units of (width, thickness); v = 0 is the top face, v < 0 goes back."""
    bm = bmesh.new()
    rings = []
    n = len(stations)
    for i, (c, w, t) in enumerate(stations):
        a = stations[max(i - 1, 0)][0]
        b = stations[min(i + 1, n - 1)][0]
        tang = (b - a).normalized()
        lat = Vector((0, 0, 1)).cross(tang).normalized()
        up = tang.cross(lat).normalized()
        rings.append([bm.verts.new(c + lat * (u * w) + up * (v * t)) for u, v in section])
    m = len(section)
    for i in range(n - 1):
        for j in range(m):
            bm.faces.new((rings[i][j], rings[i][(j + 1) % m], rings[i + 1][(j + 1) % m], rings[i + 1][j]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


# ---------------------------------------------------------------------------------------- materials

def principled(name, base, metallic, rough, coat=0.0, aniso=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    p = mat.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*base, 1)
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = rough
    p.inputs["Coat Weight"].default_value = coat
    p.inputs["Coat Roughness"].default_value = 0.03
    if aniso:
        p.inputs["Anisotropic"].default_value = aniso
    return mat


def rim_material(name, f):
    """Rim finish plus the engraved TURISMO / INVENTA lettering mapped around the lip face."""
    lip = f["lip"] or f["base"]
    mat = principled(name, f["base"], f["metallic"], f["rough"], f["coat"])
    nt = mat.node_tree
    N, L = nt.nodes, nt.links
    p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], sep.inputs[0])
    ang = N.new("ShaderNodeMath"); ang.operation = "ARCTAN2"
    L.new(sep.outputs["Y"], ang.inputs[0]); L.new(sep.outputs["X"], ang.inputs[1])
    u = N.new("ShaderNodeMath"); u.operation = "MULTIPLY_ADD"
    u.inputs[1].default_value = -1 / math.tau; u.inputs[2].default_value = 0.5
    L.new(ang.outputs[0], u.inputs[0])
    vec = N.new("ShaderNodeCombineXYZ")
    L.new(sep.outputs["X"], vec.inputs["X"]); L.new(sep.outputs["Y"], vec.inputs["Y"])
    rad = N.new("ShaderNodeVectorMath"); rad.operation = "LENGTH"
    L.new(vec.outputs[0], rad.inputs[0])
    v = N.new("ShaderNodeMapRange")
    v.inputs["From Min"].default_value = 0.2425
    v.inputs["From Max"].default_value = 0.2555
    v.inputs["To Min"].default_value = 0.0
    v.inputs["To Max"].default_value = 1.0
    v.clamp = False
    L.new(rad.outputs["Value"], v.inputs["Value"])
    uv = N.new("ShaderNodeCombineXYZ")
    L.new(u.outputs[0], uv.inputs["X"]); L.new(v.outputs["Result"], uv.inputs["Y"])
    img = N.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(str(TEX / "lip_text.png"), check_existing=True)
    img.extension = "CLIP"
    L.new(uv.outputs[0], img.inputs["Vector"])
    front = N.new("ShaderNodeMath"); front.operation = "GREATER_THAN"
    front.inputs[1].default_value = 0.0085
    L.new(sep.outputs["Z"], front.inputs[0])
    mask = N.new("ShaderNodeMath"); mask.operation = "MULTIPLY"
    L.new(img.outputs["Color"], mask.inputs[0]); L.new(front.outputs[0], mask.inputs[1])
    # polished lip face (two-tone finishes): r > 0.2335 and z > 0.004
    lr = N.new("ShaderNodeMath"); lr.operation = "GREATER_THAN"; lr.inputs[1].default_value = 0.2335
    L.new(rad.outputs["Value"], lr.inputs[0])
    lz = N.new("ShaderNodeMath"); lz.operation = "GREATER_THAN"; lz.inputs[1].default_value = 0.004
    L.new(sep.outputs["Z"], lz.inputs[0])
    lipm = N.new("ShaderNodeMath"); lipm.operation = "MULTIPLY"
    L.new(lr.outputs[0], lipm.inputs[0]); L.new(lz.outputs[0], lipm.inputs[1])
    if not f["lip"]:
        lipm.inputs[1].default_value = 0.0
        L.remove(lipm.inputs[1].links[0])
    basec = N.new("ShaderNodeMix"); basec.data_type = "RGBA"
    basec.inputs["A"].default_value = (*f["base"], 1)
    basec.inputs["B"].default_value = (*lip, 1)
    L.new(lipm.outputs[0], basec.inputs["Factor"])
    for inp, a_val, b_val in (("Metallic", f["metallic"], 1.0), ("Coat Weight", f["coat"], 0.0)):
        mr = N.new("ShaderNodeMapRange")
        mr.inputs["To Min"].default_value = a_val; mr.inputs["To Max"].default_value = b_val
        L.new(lipm.outputs[0], mr.inputs["Value"]); L.new(mr.outputs["Result"], p.inputs[inp])
    dark = N.new("ShaderNodeMix"); dark.data_type = "RGBA"
    L.new(basec.outputs["Result"], dark.inputs["A"])
    dark.inputs["B"].default_value = (0.05, 0.05, 0.055, 1)
    L.new(mask.outputs[0], dark.inputs["Factor"])
    L.new(dark.outputs["Result"], p.inputs["Base Color"])
    r0 = N.new("ShaderNodeMapRange")
    r0.inputs["To Min"].default_value = f["rough"]
    r0.inputs["To Max"].default_value = 0.09
    L.new(lipm.outputs[0], r0.inputs["Value"])
    rr = N.new("ShaderNodeMapRange")
    L.new(r0.outputs["Result"], rr.inputs["To Min"])
    rr.inputs["To Max"].default_value = 0.55
    L.new(mask.outputs[0], rr.inputs["Value"])
    L.new(rr.outputs["Result"], p.inputs["Roughness"])
    return mat


def cap_material(radius):
    mat = principled("cap", (0.03, 0.03, 0.03), 0.6, 0.28, 0.6)
    nt = mat.node_tree
    N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / (2 * radius), 1 / (2 * radius), 1)
    mp.inputs["Location"].default_value = (0.5, 0.5, 0)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    img = N.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(str(TEX / "cap.png"), check_existing=True)
    img.extension = "EXTEND"
    L.new(mp.outputs["Vector"], img.inputs["Vector"])
    p = N["Principled BSDF"]
    L.new(img.outputs["Color"], p.inputs["Base Color"])
    # lettering reads as metal, the cap body as satin paint
    met = N.new("ShaderNodeMapRange")
    met.inputs["From Min"].default_value = 0.15
    met.inputs["From Max"].default_value = 0.5
    met.inputs["To Min"].default_value = 0.0
    met.inputs["To Max"].default_value = 1.0
    bw = N.new("ShaderNodeRGBToBW")
    L.new(img.outputs["Color"], bw.inputs[0])
    L.new(bw.outputs[0], met.inputs["Value"])
    L.new(met.outputs["Result"], p.inputs["Metallic"])
    return mat


# -------------------------------------------------------------------------------------------- wheel

class WheelRig:
    def __init__(self, finish="brushed", name="wheel"):
        f = FINISHES[finish]
        self.finish = finish
        self.root = link(bpy.data.objects.new(name, None))
        self.root.rotation_euler = Euler((math.radians(90), 0, 0))
        self.spin = link(bpy.data.objects.new(name + "_spin", None), self.root)
        body = principled(name + "_body", f["base"], f["metallic"], f["rough"], f["coat"], f.get("aniso", 0))
        rim = rim_material(name + "_rim", f)
        chrome = principled(name + "_chrome", (0.9, 0.9, 0.92), 1.0, 0.08)
        hole = principled(name + "_hole", (0.004, 0.004, 0.004), 0.0, 0.5)
        self.parts = []

        # rim: lip face, flange, barrel and the inner well, lathed
        prof = [
            (R_LIP_IN, 0.006), (0.2335, 0.0098), (0.2425, 0.0102), (0.2555, 0.0102), (0.2605, 0.0085),
            (R_LIP, 0.0040), (R_LIP, -0.0120), (0.2585, -0.0170), (0.2465, -0.0250), (0.2445, -0.0400),
            (0.2420, -0.0520), (0.2180, -0.0760), (0.2120, -0.1700), (0.2380, -0.2050), (0.2440, -0.2180),
            (0.2560, -0.2260), (0.2590, -0.2420), (0.2500, -0.2480), (0.2380, -0.2300), (0.2010, -0.1720),
            (0.2050, -0.0700), (0.2200, -0.0300), (0.2240, -0.0080),
        ]
        o = mesh_obj(name + "_rim", lathe(prof), self.spin)
        o.data.materials.append(rim)
        self.parts.append(o)

        # hub disc
        hub = [(0.0330, -0.0395), (0.0372, -0.0412), (0.0405, -0.0462), (0.0700, -0.0500), (0.0790, -0.0540),
               (0.0830, -0.0620), (0.0830, -0.1000), (0.0330, -0.1000)]
        o = mesh_obj(name + "_hub", lathe(hub, 128), self.spin)
        o.data.materials.append(body)
        self.parts.append(o)

        # spokes: a five-point star. Ten straight blades; each pair meets in a sharp V at the lip
        # (points at 90 + 72k degrees) and splits toward the hub, where it meets the next pair.
        section = [(-0.5, -1.0), (0.5, -1.0), (0.5, -0.30), (0.28, 0.0), (-0.28, 0.0), (-0.5, -0.30)]
        n = 44
        for k in range(N_ARMS):
            p0 = math.radians(90 + k * 360 / N_ARMS)
            for side in (-1, 1):
                th_r = p0 + side * math.radians(3.2)
                th_h = p0 + side * math.radians(36 - 7.5)
                r_h, r_r = R_HUB + 0.004, R_LIP_IN + 0.012
                a = Vector((r_h * math.cos(th_h), r_h * math.sin(th_h)))
                b = Vector((r_r * math.cos(th_r), r_r * math.sin(th_r)))
                st = []
                for i in range(n):
                    s = i / (n - 1)
                    q = a.lerp(b, s)
                    z = -0.0480 + 0.0570 * s ** 1.30 - 0.0040 * math.sin(math.pi * s)
                    w = 0.0230 - 0.0060 * s
                    t = 0.036 - 0.010 * s
                    st.append((Vector((q.x, q.y, z)), w, t))
                o = mesh_obj(f"{name}_spoke{k}{side}", sweep(st, section), self.spin, 28)
                bev = o.modifiers.new("bevel", "BEVEL")
                bev.width = 0.0011
                bev.segments = 2
                bev.limit_method = "ANGLE"
                o.modifiers.new("wn", "WEIGHTED_NORMAL").keep_sharp = True
                o.data.materials.append(body)
                self.parts.append(o)

        # lug nuts in dark pockets, between the arms
        for k in range(N_ARMS):
            a = math.radians(90 + k * 72)
            c = Vector((0.057 * math.cos(a), 0.057 * math.sin(a), 0))
            bm = bmesh.new()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=0.0125, radius2=0.0125, depth=0.006,
                                  matrix=Matrix.Translation(c + Vector((0, 0, -0.0505))))
            o = mesh_obj(f"{name}_pocket{k}", bm, self.spin)
            o.data.materials.append(hole)
            bm = bmesh.new()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.0098, radius2=0.0098, depth=0.013,
                                  matrix=Matrix.Translation(c + Vector((0, 0, -0.0495))) @ Matrix.Rotation(math.radians(30) + a, 4, "Z"))
            o = mesh_obj(f"{name}_nut{k}", bm, self.spin, 40)
            bev = o.modifiers.new("bevel", "BEVEL"); bev.width = 0.0008; bev.segments = 2
            o.data.materials.append(chrome)
            self.parts.append(o)

        # centre cap with the GT mark
        cr = 0.031
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=96, radius1=cr, radius2=cr * 0.985, depth=0.012,
                              matrix=Matrix.Translation((0, 0, -0.0425)))
        o = mesh_obj(name + "_cap", bm, self.spin, 40)
        bev = o.modifiers.new("bevel", "BEVEL"); bev.width = 0.0012; bev.segments = 3
        o.data.materials.append(cap_material(cr))
        self.parts.append(o)

    def place(self, loc=(0, 0, 0), rot_deg=(90, 0, 0)):
        self.root.location = loc
        self.root.rotation_euler = Euler([math.radians(a) for a in rot_deg])

    def hide(self, state):
        for o in [self.root, self.spin] + self.parts:
            o.hide_render = state


# ------------------------------------------------------------------------------------------ studio

def studio(world_strength=0.8):
    sc = bpy.context.scene
    w = bpy.data.worlds.new("studio")
    sc.world = w
    w.use_nodes = True
    N, L = w.node_tree.nodes, w.node_tree.links
    bg = N["Background"]
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Generated"], sep.inputs[0])
    # vertical gradient: bright ceiling, a dark horizon band (reads as metal), light floor
    zr = N.new("ShaderNodeMapRange")
    zr.inputs["From Min"].default_value = -1
    zr.inputs["From Max"].default_value = 1
    L.new(sep.outputs["Z"], zr.inputs["Value"])
    ramp = N.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0; cr.elements[0].color = (0.30, 0.30, 0.31, 1)
    cr.elements[1].position = 1.0; cr.elements[1].color = (1.60, 1.60, 1.60, 1)
    for pos, v in [(0.38, 0.22), (0.46, 0.05), (0.50, 0.015), (0.56, 0.06), (0.66, 0.20), (0.78, 0.9), (0.90, 1.5)]:
        e = cr.elements.new(pos); e.color = (v, v, v * 1.01, 1)
    L.new(zr.outputs["Result"], ramp.inputs["Fac"])
    # two dark flags left and right so the face of the wheel has contrast
    xr = N.new("ShaderNodeMapRange")
    xr.inputs["From Min"].default_value = -1
    xr.inputs["From Max"].default_value = 1
    L.new(sep.outputs["X"], xr.inputs["Value"])
    ramp2 = N.new("ShaderNodeValToRGB")
    c2 = ramp2.color_ramp
    c2.elements[0].position = 0.0; c2.elements[0].color = (1, 1, 1, 1)
    c2.elements[1].position = 1.0; c2.elements[1].color = (1, 1, 1, 1)
    for pos, v in [(0.10, 1.0), (0.16, 0.18), (0.24, 0.18), (0.30, 1.0), (0.72, 1.0), (0.78, 0.25), (0.86, 0.25), (0.92, 1.0)]:
        e = c2.elements.new(pos); e.color = (v, v, v, 1)
    L.new(xr.outputs["Result"], ramp2.inputs["Fac"])
    mul = N.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    L.new(ramp.outputs["Color"], mul.inputs["A"]); L.new(ramp2.outputs["Color"], mul.inputs["B"])
    L.new(mul.outputs["Result"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = world_strength

    # key softbox above, slightly left, and a long strip from the right
    def area(name, loc, rot, size, power, sx=None):
        ld = bpy.data.lights.new(name, "AREA")
        ld.shape = "RECTANGLE"
        ld.size = size
        ld.size_y = sx or size
        ld.energy = power
        o = link(bpy.data.objects.new(name, ld))
        o.location = loc
        o.rotation_euler = Euler([math.radians(a) for a in rot])
        return o
    area("key", (-1.2, -1.6, 2.4), (35, 0, -35), 2.2, 520)
    area("strip", (2.0, -0.6, 0.6), (0, 75, 15), 0.35, 260, 2.5)
    area("kick", (-2.2, 0.8, 0.9), (0, -70, 0), 0.4, 160, 2.0)


def floor(z):
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, z))
    o = bpy.context.active_object
    o.is_shadow_catcher = True
    o.visible_glossy = False
    o.visible_diffuse = False
    o.visible_transmission = False
    return o


def camera(name="cam", lens=50):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36
    cd.clip_start = 0.005
    o = link(bpy.data.objects.new(name, cd))
    bpy.context.scene.camera = o
    return o


def aim(cam, target, roll_deg=0.0):
    d = Vector(target) - cam.location
    q = d.to_track_quat("-Z", "Y")
    cam.rotation_euler = (q.to_matrix().to_4x4() @ Matrix.Rotation(math.radians(roll_deg), 4, "Z")).to_euler()


def render_setup(w=1920, h=1080, samples=48, fps=25, motion_blur=False, shutter=0.5):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 6
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 4
    sc.cycles.transmission_bounces = 0
    sc.cycles.transparent_max_bounces = 2
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.render.fps = fps
    sc.render.use_motion_blur = motion_blur
    sc.render.motion_blur_shutter = shutter
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.color_depth = "8"
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.render.threads_mode = "AUTO"
