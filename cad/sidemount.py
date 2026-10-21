"""Side mount (v2.0): the cluster hangs between two flat printed side plates that bolt to two split clamps on the dash
crossbar. Cleaned-up build of the OPEN28 prototype (reference/open28/): same architecture and placement, with the
joints replaced by the ones already proven on this cluster.

Per side (L = face-right / passenger, R = face-left / driver), four printed parts:
  side plate      flat 8 mm truss in the fore-aft vertical plane just inboard of the ear tab; prints flat
  clamp upper     proven split clamp (mount.split_clamp) with two M5 bosses on the end face that meets the plate and
                  captured M5 nuts (top-entry slots); closed by the already-printed bar_clamp_lower halves, M6 x 40
                  from below into nylocs captured in the flange tops. The passenger upper continues as a 30 mm
                  half-ring saddle out to its plate (the dash hardware under the bar there allows no full clamp)
  lower adapter   proven lug slab (M4 x 16 through B2 B3 / B5 B6, nuts in hex channels open to the rear) on a block
                  that bolts to the plate's inboard face with two M4 x 40 (nuts in pockets on its inboard face)
  ear adapter     proven ear block (M4 x 20 from the front through the lens notch, nut in a side-entry channel) on an
                  arm that laps the plate's outboard face, two M4 x 20 into nuts pocketed in the plate
Frames: cluster parts in the SCAN frame (x across, y down, z toward the driver), clamps in the CAR frame (x along the
bar, y toward the cowl, z up); placement T (scan -> car) as in the OPEN28 prototype: pitch 28, scan origin at
(262, -40, 95). Outputs: cad/output/sidemount_*.stl (car frame), placement_sidemount.json, sidemount_car.step."""
import sys, math, json
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
import generate as G
import mount as M
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union

HERE = Path(__file__).parent; OUT = HERE / "output"; REF = HERE.parent / "reference"
# ---- placement (OPEN28)
PITCH = 28.0                        # face leans back from vertical
ORIGIN = (262.0, -40.0, 95.0)       # car position of the scan origin: the whole cluster sits in front of the bar
# ---- side plate
PLATE_T = 8.0; BAR_W = 15.0         # plate thickness (x), truss bar width
Z_SPINE = -58.0                     # vertical spine member (scan z) behind the housing rear
Y_SPINE_LOW = 40.0
TOP_CLR = 4.0; BOT_CLR = 4.0        # top member / bottom nodes stay this far off the scanned housing top / bottom
BORE_CLR = 2.0                      # plate notch around the crossbar
M5_CLR = 5.5; M4_CLR = G.BOLT_M4_CLR
# ---- clamp upper
BOSS_YZ = ((-25.0, 15.0), (25.0, 15.0))   # M5 bosses on the end face (car y fore/aft of the bar axis, z above it)
BOSS_R, BOSS_L = 7.0, 26.0
NUT_M5_AF, NUT_M5_T, NUT_M5_X = 8.2, 4.6, 14.0   # captured M5 nut (8.0 AF): snug slot so it stays put while the plate is offered up, thickness, distance from the end face
NUT_M6_AF, NUT_M6_POCKET = 10.3, 6.5             # M6 nylocs in the flange tops (cradle v1.2)
PASS_CLAMP_X = 375.0                # passenger clamp centre: dash hardware under the bar from x 390 to 430
# ---- lower adapter
AD_Y = (86.0, 117.0); AD_Z = (-42.0, -14.0)      # block below the lug plates: y down, z from the proven pad front back
AD_CLAMP_Y = -50.0                  # the block is trimmed by the car plane y = this (clamp front flange edge at -43)
NODE_Z_IN = 8.0                     # cross-bolt nodes this far inside the block's front / rear faces
POCKET_D = 4.5                      # captured-nut pocket depth (M4)
# ---- ear adapter
ARM_T = 13.4; ARM_H = 14.0; ARM_Z_BACK = -62.0
EAR_IN_W = 8.0                      # ear block inboard of the hole (the housing top rises inboard); 10 outboard in the shell boss
U_Z = (-50.0, -26.0)                # upper cross bolts (scan z) along the arm / top member

def placement():
    a = math.radians(PITCH); c, s = math.cos(a), math.sin(a)
    T = np.eye(4); T[:3, :3] = [[-1, 0, 0], [0, -s, -c], [0, -c, s]]; T[:3, 3] = ORIGIN; return T
T = placement(); Tinv = np.linalg.inv(T)
def to_car(p): return (T[:3, :3] @ np.asarray(p, float)) + T[:3, 3]
def to_scan(p): return (Tinv[:3, :3] @ np.asarray(p, float)) + Tinv[:3, 3]

_V = None
def scan_verts():
    global _V
    if _V is None:
        import trimesh; _V = trimesh.load(REF / "cluster_scan" / "cluster_onshape_reference_mm.stl").vertices
    return _V
def housing_y(x0, x1, z0, z1, which):
    v = scan_verts(); s = v[(v[:, 0] > min(x0, x1)) & (v[:, 0] < max(x0, x1)) & (v[:, 2] > z0) & (v[:, 2] < z1)]
    return float(s[:, 1].min() if which == "top" else s[:, 1].max())

def side_geom(side):
    ear = "T1" if side == "L" else "T2"; ids = G.LUGS[side]; out = -1.0 if side == "L" else 1.0   # outboard direction (scan x)
    xs = [G.HOLES[i][0] for i in ids]; x_outer = min(xs) if side == "L" else max(xs); x_inner = max(xs) if side == "L" else min(xs)
    x_pi = x_outer + out * (G.LUG_FOOT_MARGIN_OUT + 0.5)      # plate inboard face: just outboard of the proven lug slab
    x_po = x_pi + out * PLATE_T
    x_in = x_inner - out * G.LUG_FOOT_MARGIN_IN                # adapter inboard end
    x_arm = x_po + out * ARM_T                                 # ear arm outboard face
    return dict(ear=ear, ids=ids, out=out, x_pi=x_pi, x_po=x_po, x_in=x_in, x_arm=x_arm, x_ear=G.HOLES[ear][0])

def xr(a, b): return (min(a, b), max(a, b))
YZ = ((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
def yz_prism(g, poly, x0, x1):
    x0, x1 = xr(x0, x1); return g.place(g.prism(G.Region(poly), x0, x1), *YZ)
def bar_poly(p, q, w=BAR_W):
    return LineString([tuple(p), tuple(q)]).buffer(w / 2, resolution=24)
def hex_slot(g, centre, axis, up, af, t, up_len):
    """Captured-nut slot: hex of width af (flats parallel to `up`) and thickness t along `axis`, extended up_len in `up` so
    the nut drops in from that side. Built in a local frame (z = axis, y = up) and placed."""
    r = af / math.sqrt(3)
    hexa = Polygon([(r * math.cos(math.radians(60 * k)), r * math.sin(math.radians(60 * k))) for k in range(6)])
    slot = unary_union([hexa, Polygon([(-af / 2, 0), (af / 2, 0), (af / 2, up_len), (-af / 2, up_len)])])
    body = g.prism(G.Region(slot), -t / 2, t / 2)
    axis = G.unit(axis); up = G.unit(np.asarray(up, float) - np.dot(up, axis) * axis); e1 = np.cross(up, axis)
    return g.place(body, centre, e1, up, axis)

def lug_slab(g, side, ids):
    """Proven slab behind the lug pair (generate.build_feet geometry): 8 mm at FOOT_STANDOFF, M4 holes, hex nut channels
    from the rear. Returns (slab, cut tools in world coords)."""
    a, b = (np.array(G.HOLES[i][:3]) for i in ids); mid = (a + b) / 2
    _, e1, e2, e3 = G.tab_frame(ids[0], (1.0, 0.0)); half = abs(np.dot(b - a, e1)) / 2
    z0 = G.FOOT_STANDOFF; z1 = z0 + G.FOOT_T
    m_neg, m_pos = (G.LUG_FOOT_MARGIN_OUT, G.LUG_FOOT_MARGIN_IN) if side == "L" else (G.LUG_FOOT_MARGIN_IN, G.LUG_FOOT_MARGIN_OUT)
    slab = g.box(-(half + m_neg), -G.LUG_FOOT_DOWN, z0, half + m_pos, G.LUG_FOOT_UP, z1)
    tools = []
    for sx in (-half, half):
        tools.append(g.cyl((sx, 0.0, z0 - 2.0), (sx, 0.0, z1 + 60.0), M4_CLR))
        tools.append(g.hexprism(sx, 0.0, z1 - G.NUT_M4_H, z1 + 60.0, G.NUT_M4_AF))   # channel open to the rear of the block
    return g.place(slab, mid, e1, e2, e3), [g.place(t, mid, e1, e2, e3) for t in tools]

def ear_block(g, s, y_top):
    """Proven ear block behind the tab (generate ear boss / v0.5 ear block dims), widened outboard to the arm's outboard
    face so the adapter prints flat on that face. Returns (block, cut tools): M4 clearance + side-entry nut channel whose
    mouth is on the arm's outboard face."""
    h = s["ear"]; o, e1, e2, e3 = G.tab_frame(h, (s["out"], 0.0))          # e1 points outboard
    xo = abs(s["x_arm"] - s["x_ear"]); xi = EAR_IN_W                    # outboard / inboard half widths
    z0, z1 = G.FOOT_STANDOFF, G.FOOT_STANDOFF + G.EAR_BLOCK_T
    up = (G.HOLES[h][1] - y_top) / abs(e2[1])
    blk = g.box(-xi, -G.EAR_BLOCK_DOWN, z0, xo, up, z1)
    zc0 = z1 - G.EAR_NUT_REAR_WALL - G.NUT_M4_SLOT_T
    chan = g.prism(G.Region(Polygon([(-(G.NUT_M4_AC / 2 + 0.1), -G.NUT_M4_SLOT_W / 2), (-(G.NUT_M4_AC / 2 + 0.1), G.NUT_M4_SLOT_W / 2),
                                     (xo + 1.0, G.EAR_CHAN_MOUTH_W / 2), (xo + 1.0, -G.EAR_CHAN_MOUTH_W / 2)])), zc0, zc0 + G.NUT_M4_SLOT_T)
    tools = [g.cyl((0.0, 0.0, z0 - 2.0), (0.0, 0.0, z1 + 2.0), G.EAR_BOLT_CLR), chan]
    return g.place(blk, o, e1, e2, e3), [g.place(t, o, e1, e2, e3) for t in tools]

def clamp_upper(g, side, s, x_plate_end_car):
    """Proven split clamp upper in the car frame with M5 bosses on the face that meets the plate; the passenger side
    gets a half-ring saddle extension from the clamp to the plate. Returns (upper, info)."""
    inb = 1.0 if side == "R" else -1.0                    # inboard direction in car x (toward the centre x = 262)
    x_c = PASS_CLAMP_X if side == "L" else x_plate_end_car + inb * M.CLAMP_W / 2
    upper, lower = M.split_clamp(g, (x_c, 0.0, 0.0), (1, 0, 0), M.CLAMP_W, split_normal_local=(0, 0, 1), bolt_dir_local=(0, 0, 1), flange_dir_local=(1, 0, 0))
    lower = g.cut(lower, [g.cyl((x_c, sy * M.FLANGE_Y, -(M.FLANGE_T / 2 + 4.0) - 1.0), (x_c, sy * M.FLANGE_Y, -(M.FLANGE_T / 2 + 4.0) + 6.0), 11.0) for sy in (-1, 1)])   # M6 head counterbores as on the printed lowers
    z_top = M.FLANGE_T / 2 + 4.0
    upper = g.cut(upper, [g.hexprism(x_c, sy * M.FLANGE_Y, z_top - NUT_M6_POCKET, z_top + 1.0, NUT_M6_AF) for sy in (-1, 1)])
    parts = [upper]
    x_end = x_plate_end_car                                # end face that meets the plate
    x_clamp_end = x_c - inb * M.CLAMP_W / 2
    if abs(x_end - x_clamp_end) > 0.01:                    # saddle extension: half ring resting on the bar top
        ext = g.cyl((x_clamp_end, 0.0, 0.0), (x_end, 0.0, 0.0), 2 * M.CLAMP_RO)
        ext = g.cut(ext, [g.box(x_clamp_end - 1, -100, -100, x_end + 1, 100, M.CLAMP_GAP / 2)])
        parts.append(ext)
    for (by, bz) in BOSS_YZ:
        parts.append(g.cyl((x_end, by, bz), (x_end + inb * BOSS_L, by, bz), 2 * BOSS_R))
    body = g.unite(parts)
    tools = [g.cyl((x_c - 200, 0.0, 0.0), (x_c + 200, 0.0, 0.0), 2 * M.CLAMP_BORE)]
    for (by, bz) in BOSS_YZ:
        tools.append(g.cyl((x_end - inb * 2, by, bz), (x_end + inb * (BOSS_L + 2), by, bz), M5_CLR))
        tools.append(hex_slot(g, (x_end + inb * (NUT_M5_X + NUT_M5_T / 2), by, bz), (inb, 0, 0), (0, 0, 1), NUT_M5_AF, NUT_M5_T, 40.0))
    body = g.cut(body, tools)
    return body, lower, dict(x_c=x_c, x_end=x_end, x_span=sorted([x_clamp_end + inb * M.CLAMP_W, x_end]))

def build(g):
    parts = {}; info = {"pitch_deg": PITCH, "origin_car": list(ORIGIN), "T": T.tolist(), "sides": {}}
    for side in ("L", "R"):
        s = side_geom(side); out = s["out"]
        # ---- housing limits in this plate's region
        y_top = housing_y(s["x_arm"], s["x_pi"], ARM_Z_BACK, 40.0, "top")
        y_top = min(y_top, -29.0)                                        # calipers: housing top behind the ears is at y -29; take the higher of scan and calipers
        y_bot = housing_y(s["x_pi"], s["x_po"], -70.0, 0.0, "bottom")
        y_arm_c = y_top - TOP_CLR - ARM_H / 2                            # arm / top member centreline
        y_low = max(y_bot + BOT_CLR + BAR_W / 2, AD_Y[0] + 10.0)
        # ---- nodes (scan y, z)
        C = [tuple(to_scan([0.0, by, bz])[1:]) for (by, bz) in BOSS_YZ]                     # clamp bosses
        Lw = [(y_low, AD_Z[1] - NODE_Z_IN), (y_low + 6.0, AD_Z[0] + NODE_Z_IN)]             # lower adapter cross bolts
        U = [(y_arm_c, U_Z[0]), (y_arm_c, U_Z[1])]                                          # ear arm cross bolts
        SL = (Y_SPINE_LOW, Z_SPINE); ST = (y_arm_c, Z_SPINE)
        links = [(Lw[0], Lw[1]), (Lw[1], SL), (SL, ST), (ST, U[1]), (C[0], SL), (C[1], SL), (C[0], Lw[1]), (C[1], Lw[0])]
        # ---- side plate
        poly = unary_union([bar_poly(p, q) for p, q in links] + [bar_poly(SL, SL, BAR_W + 6)])
        plate = yz_prism(g, poly, s["x_pi"], s["x_po"])
        tools = []
        ax = to_scan([0, 0, 0]); axd = Tinv[:3, :3] @ np.array([1.0, 0, 0])
        tools.append(g.cyl(tuple(ax - axd * 600), tuple(ax + axd * 600), 2 * (M.BAR_R + BORE_CLR)))            # notch around the crossbar
        for (y, z) in C: tools.append(g.cyl((s["x_pi"] - out * 2, y, z), (s["x_po"] + out * 2, y, z), M5_CLR))
        for (y, z) in Lw: tools.append(g.cyl((s["x_pi"] - out * 2, y, z), (s["x_po"] + out * 2, y, z), M4_CLR))
        for (y, z) in U:
            tools.append(g.cyl((s["x_pi"] - out * 2, y, z), (s["x_po"] + out * 2, y, z), M4_CLR))
            tools.append(g.place(g.hexprism(0, 0, -1.0, POCKET_D, G.NUT_M4_AF), (s["x_pi"], y, z), (0, 1, 0), (0, 0, 1), (out, 0, 0)))   # nut pocket, inboard face
        plate = g.cut(plate, tools)
        plate = g.cut(plate, G.side_dots(g, side, (s["x_po"], (SL[0] + ST[0]) / 2, Z_SPINE - 3.0), (0.0, -1.0, 0.0), (-out, 0.0, 0.0)))
        parts[f"side_plate_{side.lower()}"] = plate
        # ---- lower adapter
        slab, slab_cuts = lug_slab(g, side, s["ids"])
        blk = g.box(*xr(s["x_in"], s["x_pi"])[:1], AD_Y[0], AD_Z[0], *xr(s["x_in"], s["x_pi"])[1:], AD_Y[1], AD_Z[1])
        ad = g.unite([slab, blk])
        cuts = list(slab_cuts)
        cuts.append(g.place(g.box(-1000, AD_CLAMP_Y, -300, 1000, 300, 300), Tinv[:3, 3], Tinv[:3, :3][:, 0], Tinv[:3, :3][:, 1], Tinv[:3, :3][:, 2]))   # keep clear of the clamp flanges
        for (y, z) in Lw:
            cuts.append(g.cyl((s["x_in"] - out * 2, y, z), (s["x_pi"] + out * 2, y, z), M4_CLR))
            cuts.append(g.place(g.hexprism(0, 0, -1.0, POCKET_D, G.NUT_M4_AF), (s["x_in"], y, z), (0, 1, 0), (0, 0, 1), (out, 0, 0)))   # nut pocket, inboard face
        ad = g.cut(ad, cuts)
        ad = g.cut(ad, G.side_dots(g, side, ((s["x_in"] + s["x_pi"]) / 2, AD_Y[1], AD_Z[0] + 10.0), (0.0, 0.0, 1.0), (0.0, -1.0, 0.0)))
        parts[f"lower_adapter_{side.lower()}"] = ad
        # ---- ear adapter: block + arm lapping the plate's outboard face
        blk_e, blk_cuts = ear_block(g, s, y_arm_c - ARM_H / 2)
        z_front = blk_e.BoundingBox().zmax                               # arm ends flush with the block's front
        arm = yz_prism(g, bar_poly((y_arm_c, ARM_Z_BACK + ARM_H / 2), (y_arm_c, z_front - ARM_H / 2), ARM_H), s["x_po"], s["x_arm"])
        ea = g.unite([arm, blk_e])
        cuts = list(blk_cuts)
        for (y, z) in U: cuts.append(g.cyl((s["x_po"] - out * 2, y, z), (s["x_arm"] + out * 2, y, z), M4_CLR))
        ea = g.cut(ea, cuts)
        ea = g.cut(ea, G.side_dots(g, side, (s["x_arm"], y_arm_c, ARM_Z_BACK + 12.0), (0.0, 0.0, 1.0), (-out, 0.0, 0.0)))
        parts[f"ear_adapter_{side.lower()}"] = ea
        # ---- clamp upper (car frame)
        x_plate_end_car = to_car([s["x_pi"], 0, 0])[0]
        cu, lo, ci = clamp_upper(g, side, s, x_plate_end_car)
        parts[f"clamp_upper_{side.lower()}"] = cu
        parts[f"clamp_lower_{side.lower()}"] = lo        # the already-printed bar_clamp_lower halves, shown for the assembly and the checks
        info["sides"][side] = dict(x_plate=[s["x_po"], s["x_pi"]], x_adapter_in=s["x_in"], x_arm=s["x_arm"], y_top_housing=y_top, y_bottom_housing=y_bot,
                                   y_arm_c=y_arm_c, y_low=y_low, nodes=dict(C=C, Lw=Lw, U=U, SL=SL, ST=ST), clamp=ci)
        print(f"{side}: plate x {s['x_po']:.1f}..{s['x_pi']:.1f}, adapter to {s['x_in']:.1f}, arm to {s['x_arm']:.1f}; housing top {y_top:.1f} bottom {y_bot:.1f} -> arm centre y {y_arm_c:.1f}, low nodes y {y_low:.1f}; clamp {ci}")
    return parts, info

def export(g, parts, info):
    import cadquery as cq, trimesh
    comp = []
    car_frame = {}
    for name, body in parts.items():
        if name.startswith("clamp"): car = body
        else: car = g.place(body, T[:3, 3], T[:3, :3][:, 0], T[:3, :3][:, 1], T[:3, :3][:, 2])
        car_frame[name] = car
        fn = OUT / f"sidemount_{name}.stl"; cq.exporters.export(cq.Workplane(obj=car), str(fn), tolerance=0.05, angularTolerance=0.1)
        m = trimesh.load(fn); ns = len(car.Solids())
        print(f"  {name:<18} {m.volume / 1000:6.1f} cm3 (~{m.volume / 1000 * 1.07:3.0f} g solid)  solids {ns}  watertight {m.is_watertight}")
        if ns != 1: raise SystemExit(f"{name}: {ns} solids")
        c = car.copy(); c.label = name; comp.append(c)
    cq.exporters.export(cq.Compound.makeCompound(comp), str(OUT / "sidemount_car.step"))
    np.save(OUT / "placement_sidemount_T.npy", T)
    json.dump(info, open(OUT / "placement_sidemount.json", "w"), indent=1)
    return car_frame

def main():
    g = G.CQ(); parts, info = build(g); export(g, parts, info)
    print("sidemount built ->", OUT)

if __name__ == "__main__":
    main()
