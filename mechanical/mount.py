#!/usr/bin/env python
"""Cage mount for the Probe GT cluster enclosure, in the CAR frame of dash_cage_reference (mm):
X along the dash crossbar (driver -> passenger), Y forward (toward cowl), Z up. Crossbar centreline = X axis, OD 44.45.

Placement: the enclosure (scan frame, see generate.py) is placed by T = pitch about the knuckle pin line after mapping
scan (x, y_down, z_toward_driver) -> car (x + X_C, -z, -y). Lift and pitch are parameters; the driver's eye is a guess
and stays adjustable. Checks: road sightline over the enclosure, gauge face visible over the wheel rim, clearances to
scan, cage, wheel disc and steering column.

Parts (car frame): 2 x crossbar clamp (lower half + upper half with blade strut and clevis), upright clamp (2 halves,
inboard half with stay ear), pitch stay. Reuses the CadQuery / FeatureScript backends from generate.py.

Usage: mount.py [--fs-only]
"""
import sys, json, math
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
import generate as G

HERE = Path(__file__).parent; OUT = HERE / "output"; REF = HERE.parent / "dash_cage_reference"

# ------------------------------------------------------------------ car geometry (from onshape_reference_geometry.json)
BAR_R = 44.45 / 2
UPRIGHT = dict(x=-0.356, y=-1.061)                       # vertical axis, straight for z -166..94
HUB = np.array([266.139, -317.480, 57.955]); HUB_AXIS = np.array([-0.006766, -0.911536, 0.411164])   # toward driver
WHEEL_OD, WHEEL_DISH = 350.0, 60.0                        # MOMO guess: rim centre 60 mm toward the driver from the hub point
EYE = np.array([266.0, -850.0, 480.0])                    # GUESS, adjustable
WINDSHIELD_BASE = (300.0, 120.0)                          # (y, z) GUESS for the lowest road sightline over the cowl
SWITCH_BOX = ((-73, -207, 79), (52, -33, 253))
# steering-column support stubs fitted from steering_supports_region_scan (2026-09-26): horizontal-ish tubes from the bar toward
# the driver, ending in the column bracket cups. OD assumed 44.45 like the cage (scan radius median ~26 incl. cups).
STUBS = {"L": ((197.2, -6.6, 7.6), (215.8, -157.9, -10.3)), "R": ((328.0, -8.5, 5.9), (322.3, -155.6, -11.0))}; STUB_OD = 44.45
COL_GOLD = (0.69, 0.55, 0.23)

# ------------------------------------------------------------------ placement parameters
X_C = 262.0            # car x of scan x = 0; scan +X is the driver's LEFT, so car x = X_C - x_scan (centre -4 -> 266 = column)
PIN_Y = -40.0          # knuckle pin line 40 mm behind the bar axis (struts rake toward the driver)
LIFT = 30.0            # enclosure bottom wall above the bar TOP
PITCH = 25.0           # degrees, top of the enclosure toward the driver
PIN_Z = BAR_R + LIFT - (G.KNUCKLE_H - G.KNUCKLE_R)   # pin sits (KNUCKLE_H - KNUCKLE_R) below the bottom wall
PIN_SCAN = np.array([0.0, G.offset(G.GAP + G.WALL).bounds[3] + G.KNUCKLE_H - G.KNUCKLE_R, G.KNUCKLE_Z])   # scan-frame pin (x free)

# ------------------------------------------------------------------ mount dimensions
CLAMP_W = 30.0; CLAMP_RO = 32.0; CLAMP_GAP = 1.0; CLAMP_BORE = BAR_R + 0.2
FLANGE_Y = 36.0; FLANGE_T = 14.0; BOLT_CLR = 6.4
BLADE_X, BLADE_T = 36.0, 12.0; CLEVIS_GAP = G.KNUCKLE_W + 0.6; CLEVIS_R = 17.0; PIN_HOLE = 8.4
UP_CLAMP_Z = (48.0, 76.0); UP_RO = 32.0; EAR_T = 8.0; EAR_X1 = 41.0
STAY_T, STAY_W, STAY_SLOT = 8.0, 16.0, 24.0
COL = dict(mount=(0.184, 0.192, 0.212), stay=(0.435, 0.247, 0.749))

def rot_x(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def placement():
    """4x4 transform scan(mm) -> car(mm)."""
    R0 = np.array([[-1, 0, 0], [0, 0, -1], [0, -1, 0]], float)     # (x, y, z)_scan -> (-x, -z, -y): a proper rotation (det +1)
    pin0 = R0 @ PIN_SCAN + np.array([X_C, 0, 0])                    # where the pin lands before pitch/lift
    Rp = rot_x(PITCH)
    A = Rp @ R0
    t = np.array([X_C, PIN_Y, PIN_Z]) - Rp @ pin0 + np.array([0, 0, 0])
    # pin0 already includes X_C in x; A @ p_scan = Rp @ R0 @ p; we want A @ pin_scan + t == (pin_x, PIN_Y, PIN_Z)
    t = np.array([0.0, PIN_Y, PIN_Z]) - Rp @ (R0 @ PIN_SCAN) + np.array([X_C, 0, 0])
    T = np.eye(4); T[:3, :3] = A; T[:3, 3] = t
    return T

def apply(T, pts): return (T[:3, :3] @ np.asarray(pts, float).T).T + T[:3, 3]

def pin_car(sign):
    return np.array([X_C + sign * abs(G.KNUCKLE_X[0]), PIN_Y, PIN_Z])

def stay_boss_car(T):
    xr = G.offset(G.GAP + G.WALL).bounds[2]; sb = G.STAY_BOSS
    return apply(T, [[xr + sb["h"], sb["y"], sb["z"]]])[0]        # outer face centre of the boss (scan +X wall -> car driver side)

# ------------------------------------------------------------------ checks
def checks(T, verbose=True):
    import trimesh
    rep = {}
    shells = [trimesh.load(OUT / f) for f in ("shell_l.stl", "shell_r.stl")]
    encl = trimesh.util.concatenate(shells); ev = apply(T, encl.vertices)
    cl = trimesh.load(HERE.parent / "onshape_reference_package" / "cluster_onshape_reference_mm.stl"); cv = apply(T, cl.vertices)
    sur = trimesh.load(REF / "dash_surroundings_mm.stl"); cage = trimesh.load(REF / "cage_primary_tubes_mm.stl")
    # road sightline: eye -> windshield base, z(y)
    e = EYE; wy, wz = WINDSHIELD_BASE; k = (e[2] - wz) / (wy - e[1])
    zline = lambda y: e[2] - (y - e[1]) * k
    m = zline(ev[:, 1]) - ev[:, 2]; rep["road_sightline_margin_mm"] = float(m.min()); rep["road_sightline_worst_point"] = ev[m.argmin()].round(1).tolist()
    # wheel rim top ray: face vertices (scan z > 10, i.e. gauge faces) above the eye->rim-top ray are seen over the rim
    up = np.array([0, HUB_AXIS[2], -HUB_AXIS[1]]); up /= np.linalg.norm(up)
    wc = HUB + HUB_AXIS * WHEEL_DISH; rim_top = wc + up * WHEEL_OD / 2; rim_bot = wc - up * WHEEL_OD / 2
    face = cv[cl.vertices[:, 2] > 10]
    def above_ray(p, q):   # fraction of face points above the ray eye->q (in the y-z plane)
        kk = (e[2] - q[2]) / (q[1] - e[1]); return float(np.mean(p[:, 2] > e[2] - (p[:, 1] - e[1]) * kk))
    rep["face_fraction_visible_over_rim_top"] = above_ray(face, rim_top)
    rep["face_fraction_above_hub_ray"] = above_ray(face, wc)
    # clearances
    def mind(mesh, pts):
        _, d, _ = trimesh.proximity.closest_point(mesh, pts[::3]); return float(d.min())
    rep["clearance_enclosure_to_scan_mm"] = mind(sur, ev); rep["clearance_enclosure_to_cage_mm"] = mind(cage, ev)
    # wheel disc (as a thin cylinder) and column (cylinder r 32 along the axis, t -350..0)
    rel = ev - wc; t = rel @ HUB_AXIS; r = np.linalg.norm(rel - np.outer(t, HUB_AXIS), axis=1)
    inside_disc = (np.abs(t) < 15) & (r < WHEEL_OD / 2 + 5)
    rep["wheel_disc_axial_clearance_mm"] = float(t[r < WHEEL_OD / 2 + 20].min()) if (r < WHEEL_OD / 2 + 20).any() else None   # enclosure is at t<0 side (forward)
    for k, (p0, p1) in STUBS.items():
        p0, p1 = np.array(p0), np.array(p1); d = p1 - p0; L = np.linalg.norm(d); d /= L
        tt = np.clip((ev - p0) @ d, 0, L); rr = np.linalg.norm(ev - p0 - np.outer(tt, d), axis=1) - STUB_OD / 2
        rep[f"clearance_enclosure_to_stub_{k}_mm"] = float(rr.min())
    rel2 = ev - HUB; t2 = rel2 @ HUB_AXIS; r2 = np.linalg.norm(rel2 - np.outer(t2, HUB_AXIS), axis=1)
    sel = (t2 > -400) & (t2 < 60); rep["column_radial_clearance_mm"] = float((r2[sel] - 32).min()) if sel.any() else None
    # switch box
    lo, hi = np.array(SWITCH_BOX[0]), np.array(SWITCH_BOX[1])
    d = np.maximum(np.maximum(lo - ev, ev - hi), 0); rep["switch_box_clearance_mm"] = float(np.linalg.norm(d, axis=1).min())
    rep["enclosure_bbox_car"] = np.vstack([ev.min(0), ev.max(0)]).round(1).tolist()
    rep["params"] = dict(X_C=X_C, LIFT=LIFT, PITCH=PITCH, PIN_Z=round(PIN_Z, 1), EYE=EYE.tolist(), WINDSHIELD_BASE=WINDSHIELD_BASE)
    if verbose:
        for k_, v_ in rep.items(): print(f"  {k_}: {v_}")
    return rep

# ------------------------------------------------------------------ mount geometry (car frame)
def build_mount(g, T, want=("clamps", "upright", "stay", "stubs")):
    parts = {}
    if "stubs" in want:
        for k, (p0, p1) in STUBS.items():
            d = np.array(p1) - np.array(p0); d = d / np.linalg.norm(d); a = np.array(p0) - d * 30.0   # start inside the bar
            parts[f"Cage stub {k}"] = g.name(g.cyl(tuple(a), tuple(p1), STUB_OD), f"Cage stub {k}", COL_GOLD)
    if "clamps" in want:
        for i, sign in enumerate((-1, 1)):
            px, py, pz = pin_car(sign); x0, x1 = px - CLAMP_W / 2, px + CLAMP_W / 2
            # rounded-slot clamp body around the bar: cylinder r CLAMP_RO + fore/aft flanges (bolt bosses)
            body = g.unite([g.cyl((x0, 0, 0), (x1, 0, 0), 2 * CLAMP_RO),
                            g.box(x0, -FLANGE_Y - FLANGE_T / 2, -FLANGE_T / 2 - 4, x1, FLANGE_Y + FLANGE_T / 2, FLANGE_T / 2 + 4),
                            g.cyl((x0, -FLANGE_Y, 0), (x1, -FLANGE_Y, 0), FLANGE_T + 8), g.cyl((x0, FLANGE_Y, 0), (x1, FLANGE_Y, 0), FLANGE_T + 8)])
            body = g.cut(body, [g.cyl((x0 - 1, 0, 0), (x1 + 1, 0, 0), 2 * CLAMP_BORE),
                                g.cyl((px, -FLANGE_Y, -40), (px, -FLANGE_Y, 40), BOLT_CLR), g.cyl((px, FLANGE_Y, -40), (px, FLANGE_Y, 40), BOLT_CLR),
                                g.box(x0 - 1, -80, -CLAMP_GAP / 2, x1 + 1, 80, CLAMP_GAP / 2)])   # split gap
            lower = g.intersect(g.copy_body(body), [g.box(x0 - 1, -80, -80, x1 + 1, 80, 0)])
            upper = g.intersect(body, [g.box(x0 - 1, -80, 0, x1 + 1, 80, 80)])
            # raked blade strut from the bar axis to the pin line + clevis on the upper half
            Lb = math.hypot(py, pz); ang = math.degrees(math.atan2(-py, pz))     # rotation about +X that tilts +Z toward -Y
            blade = g.box(px - BLADE_X / 2, -BLADE_T / 2, 0.0, px + BLADE_X / 2, BLADE_T / 2, Lb)
            blade = g.rot_about_x(blade, 0.0, 0.0, ang)
            blade = g.intersect(blade, [g.box(px - BLADE_X, -200, CLAMP_GAP / 2, px + BLADE_X, 200, 200)])
            blade = g.unite([blade, g.cyl((px - BLADE_X / 2, py, pz), (px + BLADE_X / 2, py, pz), 2 * CLEVIS_R)])
            blade = g.cut(blade, [g.box(px - CLEVIS_GAP / 2, py - 2 * BLADE_T, pz - 12.0, px + CLEVIS_GAP / 2, py + 2 * BLADE_T, pz + 40),
                                  g.cyl((px - BLADE_X, py, pz), (px + BLADE_X, py, pz), PIN_HOLE)])
            upper = g.unite([upper, blade])
            parts[f"Bar clamp lower {'L' if sign < 0 else 'R'}"] = g.name(lower, f"Bar clamp lower {'L' if sign < 0 else 'R'}", COL["mount"])
            parts[f"Bar clamp upper {'L' if sign < 0 else 'R'}"] = g.name(upper, f"Bar clamp upper {'L' if sign < 0 else 'R'}", COL["mount"])
    if "upright" in want or "stay" in want:
        ux, uy = UPRIGHT["x"], UPRIGHT["y"]; z0, z1 = UP_CLAMP_Z; sbc = stay_boss_car(T)
        ear_z = (z0 + z1) / 2
        if "upright" in want:
          body = g.unite([g.cyl((ux, uy, z0), (ux, uy, z1), 2 * UP_RO),
                        g.box(ux - FLANGE_T / 2 - 4, uy - FLANGE_Y - FLANGE_T / 2, z0, ux + FLANGE_T / 2 + 4, uy + FLANGE_Y + FLANGE_T / 2, z1),
                        g.cyl((ux, uy - FLANGE_Y, z0), (ux, uy - FLANGE_Y, z1), FLANGE_T + 8), g.cyl((ux, uy + FLANGE_Y, z0), (ux, uy + FLANGE_Y, z1), FLANGE_T + 8)])
          body = g.cut(body, [g.cyl((ux, uy, z0 - 1), (ux, uy, z1 + 1), 2 * CLAMP_BORE),
                            g.cyl((ux - 40, uy - FLANGE_Y, ear_z), (ux + 40, uy - FLANGE_Y, ear_z), BOLT_CLR), g.cyl((ux - 40, uy + FLANGE_Y, ear_z), (ux + 40, uy + FLANGE_Y, ear_z), BOLT_CLR),
                            g.box(ux - CLAMP_GAP / 2, uy - 80, z0 - 1, ux + CLAMP_GAP / 2, uy + 80, z1 + 1)])
          outb = g.intersect(g.copy_body(body), [g.box(ux - 80, uy - 80, z0 - 1, ux, uy + 80, z1 + 1)])
          inb = g.intersect(body, [g.box(ux, uy - 80, z0 - 1, ux + 80, uy + 80, z1 + 1)])
          ear = g.box(UP_RO - 4, uy - 10.0, z0, EAR_X1, uy + 10.0, z1)
          inb = g.unite([inb, ear]); inb = g.cut(inb, [g.cyl((EAR_X1 - EAR_T - 20, uy, ear_z), (EAR_X1 + 1, uy, ear_z), BOLT_CLR)])
          if True:
            parts["Upright clamp outboard"] = g.name(outb, "Upright clamp outboard", COL["mount"])
            parts["Upright clamp inboard"] = g.name(inb, "Upright clamp inboard", COL["mount"])
        if "stay" in want:
            # flat link in the plane x = EAR_X1 .. EAR_X1 + STAY_T, from the ear hole to the enclosure stay boss
            a = np.array([uy, ear_z]); b = np.array([sbc[1], sbc[2]]); d = b - a; L = np.linalg.norm(d); u = d / L; n = np.array([-u[1], u[0]])
            ang = math.degrees(math.atan2(u[1], u[0]))
            # build along +Y from (a) then rotate about X through a
            xs0, xs1 = EAR_X1, EAR_X1 + STAY_T
            bar = g.unite([g.box(xs0, a[0], a[1] - STAY_W / 2, xs1, a[0] + L, a[1] + STAY_W / 2),
                           g.cyl((xs0, a[0], a[1]), (xs1, a[0], a[1]), STAY_W), g.cyl((xs0, a[0] + L, a[1]), (xs1, a[0] + L, a[1]), STAY_W)])
            slot = g.unite([g.box(xs0 - 1, a[0] + L - STAY_SLOT / 2, a[1] - BOLT_CLR / 2, xs1 + 1, a[0] + L + STAY_SLOT / 2, a[1] + BOLT_CLR / 2),
                            g.cyl((xs0 - 1, a[0] + L - STAY_SLOT / 2, a[1]), (xs1 + 1, a[0] + L - STAY_SLOT / 2, a[1]), BOLT_CLR),
                            g.cyl((xs0 - 1, a[0] + L + STAY_SLOT / 2, a[1]), (xs1 + 1, a[0] + L + STAY_SLOT / 2, a[1]), BOLT_CLR)])
            bar = g.cut(bar, [g.cyl((xs0 - 1, a[0], a[1]), (xs1 + 1, a[0], a[1]), BOLT_CLR), slot])
            bar = g.rot_about_x(bar, a[0], a[1], ang)
            parts["Pitch stay"] = g.name(bar, "Pitch stay", COL["stay"])
    return parts

# backend additions shared by both engines
def _cq_copy(self, b): return b.copy()
def _cq_rot_about_x(self, body, y, z, deg): return body.rotate(self.cq.Vector(0, y, z), self.cq.Vector(1, y, z), deg)
G.CQ.copy_body = _cq_copy; G.CQ.rot_about_x = _cq_rot_about_x
def _fs_copy(self, b):
    v = self.var("cp"); pid = self.uid("pt")
    self.w(f"opPattern(context, {pid}, {{ \"entities\" : {b}, \"transforms\" : [identityTransform()], \"instanceNames\" : [\"c\"] }});")
    self.w(f"const {v} = qCreatedBy({pid}, EntityType.BODY);"); return v
def _fs_rot_about_x(self, body, y, z, deg):
    self.w(f"opTransform(context, {self.uid('rx')}, {{ \"bodies\" : {body}, \"transform\" : rotationAround(line(vector(0, {y:.3f}, {z:.3f}) * millimeter, vector(1, 0, 0)), {deg:.3f} * degree) }});"); return body
G.FS.copy_body = _fs_copy; G.FS.rot_about_x = _fs_rot_about_x

FS_MOUNT_HEADER = '''
annotation { "Feature Type Name" : "Cluster cage mount" }
export const clusterCageMount = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Bar clamps + struts" } definition.buildClamps is boolean;
        annotation { "Name" : "Upright clamp" } definition.buildUpright is boolean;
        annotation { "Name" : "Pitch stay" } definition.buildStay is boolean;
        annotation { "Name" : "Column support stubs (reference)" } definition.buildStubs is boolean;
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
    }, { buildClamps : true, buildUpright : true, buildStay : true, buildStubs : true });
'''

def emit_fs(T):
    fs = G.FS()
    for flag, want in (("buildClamps", ("clamps",)), ("buildUpright", ("upright",)), ("buildStay", ("stay",)), ("buildStubs", ("stubs",))):
        fs.w(f"if (definition.{flag})"); fs.w("{"); build_mount(fs, T, want=want); fs.w("}")
    return FS_MOUNT_HEADER + "\n".join(fs.lines) + "\n" + FS_MOUNT_FOOTER

def main():
    T = placement()
    np.save(OUT / "placement_T.npy", T); json.dump(dict(T=T.tolist(), X_C=X_C, LIFT=LIFT, PITCH=PITCH, PIN_Z=PIN_Z), open(OUT / "placement.json", "w"), indent=1)
    print("placement T (scan mm -> car mm):"); print(T.round(3))
    print("pin lines:", pin_car(-1).round(1), pin_car(1).round(1), " stay boss (car):", stay_boss_car(T).round(1))
    code = emit_fs(T); (OUT / "cluster_mount.fs").write_text(code); print(f"mount FeatureScript: {len(code.splitlines())} lines")
    if "--fs-only" in sys.argv: return
    import cadquery as cq
    g = G.CQ(); parts = build_mount(g, T)
    for label, body in parts.items():
        fn = OUT / ("mount_" + label.lower().replace(" ", "_") + ".stl"); cq.exporters.export(cq.Workplane(obj=body), str(fn), tolerance=0.05, angularTolerance=0.1)
        bb = body.BoundingBox(); print(f"  {label:<24} x {bb.xmin:7.1f}..{bb.xmax:6.1f} y {bb.ymin:7.1f}..{bb.ymax:6.1f} z {bb.zmin:6.1f}..{bb.zmax:6.1f} vol {body.Volume()/1000:6.1f} cm3")
    print("checks:"); rep = checks(T); json.dump(rep, open(OUT / "placement_checks.json", "w"), indent=1)

if __name__ == "__main__":
    main()
