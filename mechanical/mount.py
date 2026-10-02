#!/usr/bin/env python
"""Cage mount v0.3 for the Probe GT cluster enclosure, in the CAR frame of dash_cage_reference rev 2 (mm):
X along the dash crossbar (driver -> passenger), Y forward (toward cowl), Z up. Crossbar centreline = X axis, OD 44.45.
The two 1.75 in steering-support arms run from the crossbar toward the driver (-Y) at x ~203 and ~325.

Placement (user direction 2026-09-26): gauge face just behind the crossbar on the driver side, body over the bar toward
the windshield, lowest edge 1-2 in above the bar, face leaning back 20 deg like the OEM binnacle.
Scan -> car: car = (X_C - x_s, -z_s, -y_s), then pitch about X, then translate so the front-bottom edge lands at
(X_C, FACE_Y, BAR_R + EDGE_LIFT).

Mount (4 clamp points, no side-bar stay): two split clamps on the crossbar whose upper halves carry clevises for the
enclosure's M8 pivot knuckles (pitch axis), and two split clamps on the arms whose upper halves carry short struts with
slotted clevises for the enclosure's M6 lock knuckles (pitch trim +-5 deg, then locked).

Usage: mount.py [--fs-only]
"""
import sys, json, math
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
import generate as G

HERE = Path(__file__).parent; OUT = HERE / "output"; REF = HERE.parent / "dash_cage_reference"

# ------------------------------------------------------------------ car geometry (onshape_reference_geometry.json rev 2)
BAR_R = 44.45 / 2
ARMS = {"driver": ((199.715, 0.0, -0.864), (205.404, -100.0, 7.629)), "center": ((323.854, 0.0, -0.068), (325.098, -100.0, 7.220))}
ARM_R = BAR_R
HUB = np.array([266.139, -317.480, 57.955]); HUB_AXIS = np.array([-0.006766, -0.911536, 0.411164])
WHEEL_OD, WHEEL_DISH = 350.0, 60.0                        # guesses, for visibility estimates only
EYE = np.array([266.0, -800.0, 580.0]); WINDSHIELD_BASE = (280.0, 210.0)   # GUESSES
SWITCH_BOX = ((-73, -207, 79), (52, -33, 253))

# ------------------------------------------------------------------ placement parameters
X_C = 262.0            # car x of scan x = 0 (cluster centre scan x -4 -> 266, the steering column)
FACE_Y = -38.0         # gauge face plane (scan Z_FRONT): 16 mm behind the bar's driver-side surface (-22.2)
EDGE_LIFT = 50.0       # front-bottom edge above the bar TOP; the bottom wall passes ~36 mm above the bar top at the bar axis
PITCH = 20.0           # face leans back (top toward the windshield)
ARM_CLAMP_Y = -55.0    # arm clamp centre (fit report: straight, clean tube between y -80 and -35)

# ------------------------------------------------------------------ mount dimensions
CLAMP_W = 30.0; CLAMP_RO = 32.0; CLAMP_GAP = 1.0; CLAMP_BORE = BAR_R + 0.2
FLANGE_Y = 36.0; FLANGE_T = 14.0; BOLT_CLR = 6.4
# v0.7: one hardware family (M6) and clevises that clear the shell: clevis radius < pin depth below the wall (16) by >= 3 mm
BLADE_X, BLADE_T = 40.0, 10.0; CLEVIS_GAP = G.KNUCKLE_W + 0.6; CLEVIS_R = 12.0; PIN_HOLE = 6.4
LOCK_BLADE_X, LOCK_BLADE_T = 30.0, 10.0; LOCK_GAP = G.LOCK_W + 0.6; LOCK_CLEVIS_R = 13.0; LOCK_HOLE = 6.4; LOCK_SLOT = 12.0
COL = dict(mount=(0.184, 0.192, 0.212), accent=(0.435, 0.247, 0.749))

def rot_x(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg)); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def placement():
    R0 = np.array([[-1, 0, 0], [0, 0, -1], [0, -1, 0]], float)     # scan (x, y_down, z_toward_driver) -> car (-x, -z, -y)
    A = rot_x(-PITCH) @ R0                                          # rot_x(-p): +Z tips toward +Y = face leans back
    edge_scan = np.array([0.0, G.offset(G.GAP + G.WALL).bounds[3], G.Z_FRONT])
    t = np.array([X_C, FACE_Y, BAR_R + EDGE_LIFT]) - A @ edge_scan
    T = np.eye(4); T[:3, :3] = A; T[:3, 3] = t; return T

def apply(T, pts): return (T[:3, :3] @ np.asarray(pts, float).T).T + T[:3, 3]

def yb_scan(): return G.offset(G.GAP + G.WALL).bounds[3]
def knuckle_pins(T):   # (car point, car axis direction) for the two M8 pins
    return [apply(T, [[kx, yb_scan() + G.KNUCKLE_H - G.KNUCKLE_R, G.KNUCKLE_Z]])[0] for kx in G.KNUCKLE_X]
def lock_pins(T):
    return [apply(T, [[lx, yb_scan() + G.LOCK_H - G.LOCK_R, G.LOCK_Z]])[0] for lx in G.LOCK_X]

def arm_axis(name):
    p0, p1 = np.array(ARMS[name][0]), np.array(ARMS[name][1]); d = p1 - p0; return p0, d / np.linalg.norm(d)
def arm_point(name, y):
    p0, d = arm_axis(name); return p0 + d * ((y - p0[1]) / d[1])

# ------------------------------------------------------------------ checks
def checks(T, verbose=True):
    import trimesh
    rep = {}
    encl = trimesh.util.concatenate([trimesh.load(OUT / "shell_l.stl"), trimesh.load(OUT / "shell_r.stl")]); ev = apply(T, encl.vertices)
    cl = trimesh.load(HERE.parent / "onshape_reference_package" / "cluster_onshape_reference_mm.stl"); cv = apply(T, cl.vertices)
    sur = trimesh.load(REF / "dash_surroundings_mm.stl"); cage = trimesh.load(REF / "cage_primary_tubes_mm.stl")
    e = EYE; wy, wz = WINDSHIELD_BASE; k = (e[2] - wz) / (wy - e[1])
    m = e[2] - (ev[:, 1] - e[1]) * k - ev[:, 2]; rep["brow_above_windshield_sightline_mm"] = float(-m.min())
    up = np.array([0, HUB_AXIS[2], -HUB_AXIS[1]]); up /= np.linalg.norm(up); wc = HUB + HUB_AXIS * WHEEL_DISH; rim_top = wc + up * WHEEL_OD / 2
    face = cv[cl.vertices[:, 2] > 10]
    kk = (e[2] - rim_top[2]) / (rim_top[1] - e[1]); rep["face_fraction_visible_over_rim_top"] = float(np.mean(face[:, 2] > e[2] - (face[:, 1] - e[1]) * kk))
    n = T[:3, :3] @ np.array([0, 0, 1.0]); fc = face.mean(0); te = e - fc; te /= np.linalg.norm(te)
    rep["face_normal_to_eye_deg"] = float(np.degrees(np.arccos(np.clip(n @ te, -1, 1)))); rep["face_centre_car"] = fc.round(1).tolist()
    def mind(mesh, pts):
        _, d, _ = trimesh.proximity.closest_point(mesh, pts[::3]); return float(d.min())
    rep["clearance_enclosure_to_scan_mm"] = mind(sur, ev); rep["clearance_enclosure_to_cage_mm"] = mind(cage, ev)
    rel2 = ev - HUB; t2 = rel2 @ HUB_AXIS; r2 = np.linalg.norm(rel2 - np.outer(t2, HUB_AXIS), axis=1); sel = (t2 > -400) & (t2 < 60)
    rep["column_radial_clearance_mm"] = float((r2[sel] - 32).min()) if sel.any() else None
    lo, hi = np.array(SWITCH_BOX[0]), np.array(SWITCH_BOX[1]); d = np.maximum(np.maximum(lo - ev, ev - hi), 0); rep["switch_box_clearance_mm"] = float(np.linalg.norm(d, axis=1).min())
    rep["enclosure_bbox_car"] = np.vstack([ev.min(0), ev.max(0)]).round(1).tolist()
    rep["lowest_point_above_bar_top_mm"] = float(ev[:, 2].min() - BAR_R)
    rep["params"] = dict(X_C=X_C, FACE_Y=FACE_Y, EDGE_LIFT=EDGE_LIFT, PITCH=PITCH, ARM_CLAMP_Y=ARM_CLAMP_Y, EYE=EYE.tolist(), WINDSHIELD_BASE=WINDSHIELD_BASE)
    if verbose:
        for k_, v_ in rep.items(): print(f"  {k_}: {v_}")
    return rep

# ------------------------------------------------------------------ helpers shared by both backends
def _cq_copy(self, b): return b.copy()
def _cq_rot_axis(self, body, p, d, deg): return body.rotate(self.cq.Vector(*p), self.cq.Vector(*(np.array(p) + np.array(d))), deg)
G.CQ.copy_body = _cq_copy; G.CQ.rot_axis = _cq_rot_axis
def _fs_copy(self, b):
    v = self.var("cp"); pid = self.uid("pt")
    self.w(f"opPattern(context, {pid}, {{ \"entities\" : {b}, \"transforms\" : [identityTransform()], \"instanceNames\" : [\"c\"] }});")
    self.w(f"const {v} = qCreatedBy({pid}, EntityType.BODY);"); return v
def _fs_rot_axis(self, body, p, d, deg):
    self.w(f"opTransform(context, {self.uid('ra')}, {{ \"bodies\" : {body}, \"transform\" : rotationAround(line(vector({p[0]:.3f}, {p[1]:.3f}, {p[2]:.3f}) * millimeter, vector({d[0]:.6f}, {d[1]:.6f}, {d[2]:.6f})), {deg:.4f} * degree) }});"); return body
G.FS.copy_body = _fs_copy; G.FS.rot_axis = _fs_rot_axis

def align_rotations(d):
    """Rotations (about Z, then about the horizontal perpendicular) that take the local -Y axis onto unit vector d.
    Returned as [(axis_dir, deg), ...]; verified numerically."""
    d = np.asarray(d, float) / np.linalg.norm(d)
    yaw = math.degrees(math.atan2(d[0], -d[1]))                     # about +Z
    tilt = math.degrees(math.asin(np.clip(d[2], -1, 1)))            # about the horizontal axis perpendicular to d_h
    dh = np.array([d[0], d[1], 0.0]); dh /= np.linalg.norm(dh); perp = np.cross(dh, [0, 0, 1])
    for sy in (1, -1):
        for st in (1, -1):
            def R(axis, deg):
                a = np.asarray(axis, float) / np.linalg.norm(axis); c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
                K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]]); return np.eye(3) + s * K + (1 - c) * K @ K
            Rm = R(perp, st * tilt) @ R([0, 0, 1], sy * yaw)
            if np.allclose(Rm @ np.array([0, -1, 0]), d, atol=1e-6): return [((0, 0, 1), sy * yaw), (tuple(perp), st * tilt)]
    raise RuntimeError("no rotation found")

def split_clamp(g, c, d, w, split_normal_local, bolt_dir_local, flange_dir_local):
    """Split clamp around a 44.45 tube: centre c, axis unit d (built along local -Y then rotated), width w.
    Returns (half_A, half_B) where A is on the +split_normal side. Local frame: axis -Y, flanges along +-flange_dir."""
    cx, cy, cz = c
    ring = g.cyl((cx, cy + w / 2, cz), (cx, cy - w / 2, cz), 2 * CLAMP_RO)
    f = np.array(flange_dir_local, float); b = np.array(bolt_dir_local, float)
    lugs = [g.cyl(tuple(np.array([cx, cy + w / 2, cz]) + f * s * FLANGE_Y), tuple(np.array([cx, cy - w / 2, cz]) + f * s * FLANGE_Y), FLANGE_T + 8) for s in (-1, 1)]
    web_half = f * (FLANGE_Y + FLANGE_T / 2) + b * (FLANGE_T / 2 + 4) + np.array([0, w / 2, 0])
    web = g.box(*(np.array(c) - np.abs(web_half)), *(np.array(c) + np.abs(web_half)))
    body = g.unite([ring] + lugs + [web])
    tools = [g.cyl((cx, cy + w / 2 + 1, cz), (cx, cy - w / 2 - 1, cz), 2 * CLAMP_BORE)]
    for s in (-1, 1):
        p = np.array(c) + f * s * FLANGE_Y
        tools.append(g.cyl(tuple(p - b * 40), tuple(p + b * 40), BOLT_CLR))
    n = np.array(split_normal_local, float); gap_half = np.abs(n) * CLAMP_GAP / 2 + (1 - np.abs(n)) * 80
    tools.append(g.box(*(np.array(c) - gap_half), *(np.array(c) + gap_half)))
    body = g.cut(body, tools)
    other = g.copy_body(body)
    boxA = (np.array(c) + n * 40, 80.0); half = np.array([80.0, 80.0, 80.0]) - np.abs(n) * 40
    A = g.intersect(body, [g.box(*(boxA[0] - half), *(boxA[0] + half))])
    B = g.intersect(other, [g.box(*(np.array(c) - n * 40 - half), *(np.array(c) - n * 40 + half))])
    for rot in align_rotations(d):
        A = g.rot_axis(A, c, rot[0], rot[1]); B = g.rot_axis(B, c, rot[0], rot[1])
    return A, B

def strut_to_clevis(g, base, pin, blade_x, blade_t, clevis_r, gap, hole, slot=0.0, knuckle_r=8.0):
    """Blade from `base` (on the clamp) to `pin` (knuckle axis point), with a clevis around the knuckle. Axis of pin = X."""
    base, pin = np.array(base, float), np.array(pin, float); v = pin - base; L = np.linalg.norm(v)
    ang = math.degrees(math.atan2(-v[1], v[2]))                    # rotation about +X tilting +Z toward the strut direction
    blade = g.box(base[0] - blade_x / 2, base[1] - blade_t / 2, base[2], base[0] + blade_x / 2, base[1] + blade_t / 2, base[2] + L)
    blade = g.rot_axis(blade, base, (1, 0, 0), ang)
    blade = g.unite([blade, g.cyl((pin[0] - blade_x / 2, pin[1], pin[2]), (pin[0] + blade_x / 2, pin[1], pin[2]), 2 * clevis_r)])
    # clevis slot floor sits knuckle_r + 2 below the pin so the round knuckle never bottoms on the blade (v0.7 interference check)
    tools = [g.box(pin[0] - gap / 2, pin[1] - 2 * blade_t, pin[2] - (knuckle_r + 2.0), pin[0] + gap / 2, pin[1] + 2 * blade_t, pin[2] + 60)]
    if slot > 0:   # vertical slot for pitch trim
        tools += [g.box(pin[0] - blade_x, pin[1] - hole / 2, pin[2] - slot / 2, pin[0] + blade_x, pin[1] + hole / 2, pin[2] + slot / 2),
                  g.cyl((pin[0] - blade_x, pin[1], pin[2] - slot / 2), (pin[0] + blade_x, pin[1], pin[2] - slot / 2), hole),
                  g.cyl((pin[0] - blade_x, pin[1], pin[2] + slot / 2), (pin[0] + blade_x, pin[1], pin[2] + slot / 2), hole)]
    else:
        tools.append(g.cyl((pin[0] - blade_x, pin[1], pin[2]), (pin[0] + blade_x, pin[1], pin[2]), hole))
    return g.cut(blade, tools)

def build_mount(g, T, want=("bar", "arms")):
    parts = {}
    if "bar" in want:
        for pin in knuckle_pins(T):
            tag = "driver" if pin[0] < X_C else "center"; c = (pin[0], 0.0, 0.0)
            upper, lower = split_clamp(g, c, (1, 0, 0), CLAMP_W, split_normal_local=(0, 0, 1), bolt_dir_local=(0, 0, 1), flange_dir_local=(1, 0, 0))
            # clamp built along local -Y then rotated onto +X: after rotation flanges lie fore/aft (Y), split is horizontal (Z)
            # strut starts inside the ring wall (4 mm below its outer surface), NOT at the tube axis: the first print had the
            # blade filling the half-bore. The bore is re-cut after the union as a guard.
            strut = strut_to_clevis(g, (pin[0], 0.0, CLAMP_RO - 4.0), pin, BLADE_X, BLADE_T, CLEVIS_R, CLEVIS_GAP, PIN_HOLE, knuckle_r=G.KNUCKLE_R)
            upper = g.unite([upper, strut])
            # the knuckle's round bottom reaches KNUCKLE_R below the pin, which is below the ring's top: notch the whole upper
            # (ring included) to knuckle_r + 2 under the pin, then re-cut the bore (5 mm of ring wall remains under the notch)
            upper = g.cut(upper, [g.box(pin[0] - CLEVIS_GAP / 2, pin[1] - 2 * BLADE_T, pin[2] - (G.KNUCKLE_R + 2.0), pin[0] + CLEVIS_GAP / 2, pin[1] + 2 * BLADE_T, pin[2] + 60)])
            upper = g.cut(upper, [g.cyl((pin[0] - CLAMP_W / 2 - 1, 0.0, 0.0), (pin[0] + CLAMP_W / 2 + 1, 0.0, 0.0), 2 * CLAMP_BORE)])
            parts[f"Bar clamp upper {tag}"] = g.name(upper, f"Bar clamp upper {tag}", COL["mount"])
            parts[f"Bar clamp lower {tag}"] = g.name(lower, f"Bar clamp lower {tag}", COL["mount"])
    if "arms" in want:
        for (name, lockpin) in zip(("driver", "center"), lock_pins(T)):
            p0, d = arm_axis(name); c = arm_point(name, ARM_CLAMP_Y)
            upper, lower = split_clamp(g, tuple(c), d, CLAMP_W, split_normal_local=(0, 0, 1), bolt_dir_local=(0, 0, 1), flange_dir_local=(1, 0, 0))
            base = c + np.array([0, 0, CLAMP_RO - 4.0])
            strut = strut_to_clevis(g, base, lockpin, LOCK_BLADE_X, LOCK_BLADE_T, LOCK_CLEVIS_R, LOCK_GAP, LOCK_HOLE, slot=LOCK_SLOT, knuckle_r=G.LOCK_R)
            upper = g.unite([upper, strut])
            upper = g.cut(upper, [g.box(lockpin[0] - LOCK_GAP / 2, lockpin[1] - 2 * LOCK_BLADE_T, lockpin[2] - (G.LOCK_R + 2.0), lockpin[0] + LOCK_GAP / 2, lockpin[1] + 2 * LOCK_BLADE_T, lockpin[2] + 60)])
            upper = g.cut(upper, [g.cyl(tuple(c - d * (CLAMP_W / 2 + 1)), tuple(c + d * (CLAMP_W / 2 + 1)), 2 * CLAMP_BORE)])   # bore guard
            tag = "driver" if name == "driver" else "center"
            parts[f"Arm clamp upper {tag}"] = g.name(upper, f"Arm clamp upper {tag}", COL["accent"])
            parts[f"Arm clamp lower {tag}"] = g.name(lower, f"Arm clamp lower {tag}", COL["mount"])
    return parts

FS_MOUNT_HEADER = '''
annotation { "Feature Type Name" : "Cluster cage mount" }
export const clusterCageMount = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Crossbar clamps + pivot clevises" } definition.buildBar is boolean;
        annotation { "Name" : "Arm clamps + lock clevises" } definition.buildArms is boolean;
    }
    {
        var step = "start";
        try
        {
'''
FS_MOUNT_FOOTER = '''        }
        catch (e)
        {
            fCuboid(context, id + "errbox", { "corner1" : vector(600, -100, 0) * millimeter, "corner2" : vector(610, -90, 10) * millimeter });
            setProperty(context, { "entities" : qCreatedBy(id + "errbox", EntityType.BODY), "propertyType" : PropertyType.NAME, "value" : "FAILED step " ~ step ~ ": " ~ toString(e) });
        }
    }, { buildBar : true, buildArms : true });
'''

def emit_fs(T):
    fs = G.FS()
    for flag, want in (("buildBar", ("bar",)), ("buildArms", ("arms",))):
        fs.w(f"if (definition.{flag})"); fs.w("{"); build_mount(fs, T, want=want); fs.w("}")
    return FS_MOUNT_HEADER + "\n".join(fs.lines) + "\n" + FS_MOUNT_FOOTER

def main():
    T = placement()
    np.save(OUT / "placement_T.npy", T)
    json.dump(dict(T=T.tolist(), X_C=X_C, FACE_Y=FACE_Y, EDGE_LIFT=EDGE_LIFT, PITCH=PITCH, knuckle_pins=[p.round(2).tolist() for p in knuckle_pins(T)],
                   lock_pins=[p.round(2).tolist() for p in lock_pins(T)]), open(OUT / "placement.json", "w"), indent=1)
    print("placement T (scan mm -> car mm):"); print(T.round(3))
    print("pivot pins (car):", [p.round(1).tolist() for p in knuckle_pins(T)]); print("lock pins (car): ", [p.round(1).tolist() for p in lock_pins(T)])
    for n in ("driver", "center"): print(f"arm clamp {n} centre:", arm_point(n, ARM_CLAMP_Y).round(1).tolist())
    code = emit_fs(T); (OUT / "cluster_mount.fs").write_text(code); print(f"mount FeatureScript: {len(code.splitlines())} lines")
    if "--fs-only" in sys.argv: return
    import cadquery as cq
    for old in OUT.glob("mount_*.stl"): old.unlink()
    g = G.CQ(); parts = build_mount(g, T)
    for label, body in parts.items():
        fn = OUT / ("mount_" + label.lower().replace(" ", "_") + ".stl"); cq.exporters.export(cq.Workplane(obj=body), str(fn), tolerance=0.05, angularTolerance=0.1)
        bb = body.BoundingBox(); print(f"  {label:<24} x {bb.xmin:7.1f}..{bb.xmax:6.1f} y {bb.ymin:7.1f}..{bb.ymax:6.1f} z {bb.zmin:6.1f}..{bb.zmax:6.1f} vol {body.Volume()/1000:6.1f} cm3 solids {len(body.Solids())}")
    print("checks:"); rep = checks(T); json.dump(rep, open(OUT / "placement_checks.json", "w"), indent=1)

if __name__ == "__main__":
    main()
