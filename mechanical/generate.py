#!/usr/bin/env python
"""1993 Ford Probe GT gauge cluster enclosure: scan-derived constants -> CadQuery (local renders, mesh clearance)
and FeatureScript (Onshape custom feature) from the SAME geometry description.

Frame = scan frame of onshape_reference_package (mm): X across the cluster, Y increases DOWNWARD in the car,
Z toward the driver (front/glass +Z, rear/connectors -Z).  Keep it so the STL, DXF and hole CSV line up in Onshape.

Parts: Shell L / Shell R (split at X=0, closed around the cluster), Spine bar (top ridge), Keel bar (rear+bottom seam),
Test coupon.  Cluster retention is a CRADLE, no fasteners into the old plastic: ledges under the two lug plates (weight),
outer fins beside the plates (X + yaw), tilted rear stop pads at lug holes B2 B3 B5 B6 and ears T1 T2 (rearward),
front lips over the bezel rim (forward).  Rear wall opening for both harness connectors and the bulb row.

Usage: generate.py [--fs-only] [--no-mesh]
"""
import sys, json, math, csv, argparse
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box as sbox
from shapely.ops import nearest_points

HERE = Path(__file__).parent
REF = HERE.parent / "onshape_reference_package"
OUT = HERE / "output"; OUT.mkdir(exist_ok=True)

# ------------------------------------------------------------------ constants (mm)
GAP = 4.0            # cavity clearance to the scanned silhouette (scan + registration slop)
WALL = 2.5           # side / top / bottom walls
WALL_REAR = 3.0
AIR = 6.0            # ventilated air gap between top wall and outer skin (heat barrier)
SKIN = 2.0           # outer skin / visor thickness
BAR_T = 3.0          # spine and keel bar thickness
CORNER_R = 12.0      # minimum corner radius applied to the silhouette hull
Z_FRONT = 52.5       # shell front edge (bezel rim peaks at 49.5)
Z_REAR_IN = -58.0    # rear wall inner face: covers the two centre connector housings (rearmost point -55.8) with 2 mm to spare
Z_REAR_OUT = Z_REAR_IN - WALL_REAR
VISOR_L = 70.0       # brow length forward of the shell front edge
VISOR_RISE_R = 200.0 # brow follows an arc tangent to the roof that curls UP (toward -Y, car-up); larger = flatter
VISOR_STATIONS = 6   # loft sections along the arc
BEAD_D, BEAD_L = 5.0, 6.0   # rounded bead at the brow tip (no sharp edge to bump)
Y_SKIN_END = 5.0     # double skin / visor exist only for Y <= this (arch + short cheeks)
LIP_TOP_IN, LIP_TOP_Z0, LIP_TOP_YMAX = 4.0, 50.3, 30.0      # top lip: 4 mm over the silhouette, rear face 0.8 above the rim peak
CHIN_IN, CHIN_Z0, CHIN_YMIN = 9.0, 47.0, 62.0                # bottom "chin": reaches the bezel's lower rim (y 77-85, z <= 46)
# ribbon-cable ports: the two vertical PCB slots (left x -179..-173, right x 161..168, y ~2..50, thumb lock outboard).
# Each port opens the rear wall from 12 mm inboard of the slot out to the side wall, 12 mm above and below the slot.
RIBBON_PORT_XIN = (-163.0, 149.0); RIBBON_PORT_Y = (-10.0, 64.0); PORT_R = 8.0
VENT_X = (-105.0, 105.0, 7.0); VENT_ROWS = [(-48.0, -22.0), (-14.0, 12.0)]; VENT_W = 2.4   # two rows of vertical vent slots
RIB_X = [-160.0, -115.0, -60.0, 60.0, 115.0, 160.0]; RIB_T = 1.6
SPINE_RIB_X = [-6.0, 6.0]; SPINE_RIB_T = 8.0                    # thick ribs carrying the spine inserts, one per half
SPINE_W = 30.0; SPINE_SCREW_Z = [-40.0, 0.0, 40.0]; SPINE_VISOR_SCREW = [20.0, 55.0]
KEEL_W = 40.0; KEEL_Y0 = 48.0; KEEL_REAR_SCREWS_Y = [58.0, 84.0]; KEEL_BOT_SCREWS_Z = [-30.0, 20.0]; KEEL_SCREW_X = 12.0
PAD_H = 5.0
INSERT_M25_D, INSERT_M25_DEPTH = 3.4, 6.5     # coupon-verified bore for the user's M2.5 x 4 x 3.5 OD inserts
PILOT_M25 = 2.4                               # coupon-verified self-tap pilot
CLR_M25, CBORE_M25_D, CBORE_M25_H = 2.7, 5.0, 1.5
CLR_M6, NUT_M6_AF, NUT_M6_H = 6.4, 10.0, 5.2
# mount interface (v0.4): two pivot knuckles on the bottom wall under the lug blocks (M8 pin along X = pitch axis) and a
# stay boss on the left side wall (M6 along X). Car-frame placement and the mount parts live in mount.py.
KNUCKLE_X = [-155.0, 155.0]; KNUCKLE_W, KNUCKLE_D, KNUCKLE_H = 24.0, 30.0, 22.0   # X width, Z depth, protrusion below the bottom wall
KNUCKLE_Z = -35.0; PIN_D = 8.4; KNUCKLE_R = 10.0   # under the middle of the lug blocks (scan z -58..-13)
STAY_BOSS = dict(y=40.0, z=-25.0, d=16.0, h=8.0, hole=6.4)   # on the scan +X wall = driver's LEFT (A-pillar bar side)
STOP_GAP = 1.0                                # rear stop pads stand off the scanned faces by this
LUG_PAD_D = 8.0; FIN_T = 2.5; FIN_CLR = 0.8; LEDGE_CLR = 0.6
EAR_PAD_D, EAR_SHIFT, EAR_PAD_L, EAR_WEB_W = 7.0, 2.0, 5.0, 7.0   # ear pad sits outward of the hole: the housing wall hugs the inner side
COL_BODY = (0.184, 0.192, 0.212); COL_ACCENT = (0.435, 0.247, 0.749); COL_COUPON = (0.6, 0.62, 0.64)

HOLES = {r["id"]: (float(r["center_x_mm"]), float(r["center_y_mm"]), float(r["center_z_mm"]),
                   np.array([float(r["normal_x"]), float(r["normal_y"]), float(r["normal_z"])]))
         for r in csv.DictReader(open(REF / "mounting_hole_estimates_mm.csv"))}
LUGS = {"L": ("B2", "B3"), "R": ("B5", "B6")}; EARS = ["T1", "T2"]

# ------------------------------------------------------------------ silhouette -> smooth master curve
def load_outline():
    import ezdxf
    d = ezdxf.readfile(REF / "case_outline_xy_mm.dxf")
    for e in d.modelspace():
        if e.dxftype() == "LWPOLYLINE":
            return Polygon([p[:2] for p in e.get_points()])
    raise SystemExit("no outline polyline in DXF")

OUTLINE = load_outline()
_ob = OUTLINE.bounds
_flat = Polygon(list(OUTLINE.exterior.coords) + [(_ob[0] + 40, _ob[3]), (_ob[2] - 40, _ob[3])]).convex_hull   # flat bottom edge
HULL = _flat.buffer(-CORNER_R, join_style=1, resolution=32).buffer(CORNER_R, join_style=1, resolution=32)

def smooth_ring(poly, step=0.75):
    """Periodic cubic spline through adaptive samples of the ring, evaluated densely: one smooth master curve that the
    FeatureScript fit-splines and the CadQuery polylines both follow to within ~0.05 mm."""
    from scipy.interpolate import CubicSpline
    ring = np.array(poly.exterior.coords)[:-1]
    L = LineString(np.vstack([ring, ring[:1]])); total = L.length
    samples = []; d = 0.0
    while d < total:
        p = L.interpolate(d); samples.append([p.x, p.y])
        q0, q1 = L.interpolate(max(d - 2.0, 0)), L.interpolate(min(d + 2.0, total))
        v1 = np.array([p.x - q0.x, p.y - q0.y]); v2 = np.array([q1.x - p.x, q1.y - p.y])
        turn = math.degrees(math.acos(np.clip(np.dot(v1, v2) / max(np.linalg.norm(v1) * np.linalg.norm(v2), 1e-9), -1, 1)))
        d += 3.0 if turn > 0.6 else 10.0
    pts = np.array(samples); pts = np.vstack([pts, pts[:1]])
    t = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    cs = CubicSpline(t, pts, bc_type="periodic")
    return Polygon(cs(np.arange(0, t[-1], step))).buffer(0)

MASTER = smooth_ring(HULL)

def offset(d):
    """Master silhouette offset by d (outward for d > 0, inward for d < 0)."""
    return MASTER.buffer(d, join_style=1, resolution=48).simplify(0.02)

def clip(poly, y_min=None, y_max=None):
    return poly.intersection(sbox(-1000, -1000 if y_min is None else y_min, 1000, 1000 if y_max is None else y_max))

class Region:
    """A planar region (shapely polygon, single ring). CQ uses the dense ring; FS gets it as lines + fit splines."""
    def __init__(self, poly):
        if poly.geom_type == "MultiPolygon": poly = max(poly.geoms, key=lambda g: g.area)
        self.poly = poly
    def chunks(self):
        ring = np.array(self.poly.exterior.coords)[:-1]; n = len(ring)
        v = np.roll(ring, -1, axis=0) - ring; L = np.linalg.norm(v, axis=1); u = v / L[:, None]
        turn = np.degrees(np.arccos(np.clip(np.einsum("ij,ij->i", np.roll(u, 1, axis=0), u), -1, 1)))   # turn AT vertex i
        corners = [i for i in range(n) if turn[i] > 20.0]
        if len(corners) < 2:   # closed smooth ring: split at the two extreme-x points (curvature there is gentle)
            corners = sorted({int(np.argmin(ring[:, 0])), int(np.argmax(ring[:, 0]))})
        runs = []
        for k in range(len(corners)):
            a, b = corners[k], corners[(k + 1) % len(corners)]
            idx = list(range(a, b + 1)) if b > a else list(range(a, n)) + list(range(0, b + 1))
            runs.append(ring[idx])
        out = []
        for pts in runs:
            chord = LineString([pts[0], pts[-1]]) if len(pts) > 2 else None
            dev = max(chord.distance(Point(p)) for p in pts[1:-1]) if chord is not None and chord.length > 1e-6 else 0.0
            if len(pts) <= 2 or dev < 0.05:
                out.append(("line", pts[0], pts[-1])); continue
            sub = [pts[0]]; acc = 0.0
            for i in range(1, len(pts)):
                seg = np.linalg.norm(pts[i] - pts[i - 1]); acc += seg
                a_, b_, c_ = pts[max(i - 1, 0)], pts[i], pts[min(i + 1, len(pts) - 1)]
                v1, v2 = b_ - a_, c_ - b_
                t_ = math.degrees(math.acos(np.clip(np.dot(v1, v2) / max(np.linalg.norm(v1) * np.linalg.norm(v2), 1e-9), -1, 1)))
                if acc >= (3.0 if t_ > 0.8 else 10.0) and i < len(pts) - 1 and np.linalg.norm(pts[-1] - b_) > 1.0: sub.append(b_); acc = 0.0
            sub.append(pts[-1])
            out.append(("spline", np.array(sub)))
        return out

def band(d_out, d_in, y_min=None, y_max=None):
    return Region(clip(offset(d_out).difference(offset(d_in)), y_min, y_max))

# ------------------------------------------------------------------ mesh-derived seat data
def mesh_probe():
    import trimesh
    m = trimesh.load(REF / "cluster_onshape_reference_mm.stl"); v = m.vertices
    info = {}
    for h in list(HOLES):
        cx, cy, cz, n = HOLES[h]
        r = np.hypot(v[:, 0] - cx, v[:, 1] - cy); ring = v[(r > 3.6) & (r < 6.0)]
        face = ring[np.abs(ring[:, 2] - cz) < 4.0]
        info[h] = dict(seat=cz, mesh_face=float(np.median(face[:, 2])) if len(face) else None, n=len(face))
    plates = {}
    for side, ids in LUGS.items():
        xs = [HOLES[i][0] for i in ids]; xc = sum(xs) / 2
        sel = v[(np.abs(v[:, 0] - xc) < 40) & (v[:, 1] > 78) & (v[:, 2] < 0)]      # the lug plate (rear side, below the housing body)
        rows = sel[(sel[:, 1] > 79) & (sel[:, 1] < 89)]
        x_out = float(rows[:, 0].min()) if side == "L" else float(rows[:, 0].max())
        x_in = float(rows[:, 0].max()) if side == "L" else float(rows[:, 0].min())
        mid = sel[np.abs(sel[:, 0] - xc) < 8]
        plates[side] = dict(x_out=x_out, x_in=x_in, y_bot=float(mid[:, 1].max()), z_front=float(sel[:, 2].max()), z_rear=float(sel[:, 2].min()),
                            zmin_block=float(v[(v[:, 0] > min(xs) - 9) & (v[:, 0] < max(xs) + 9) & (v[:, 1] > min(HOLES[i][1] for i in ids) - 8)][:, 2].min()))
    return m, info, plates

# ------------------------------------------------------------------ geometry description (backend-agnostic)
def unit(v): v = np.asarray(v, float); return v / np.linalg.norm(v)

def brow_dy(t):
    """Vertical offset (Y, negative = up) of the brow arc at distance t forward of the shell front edge."""
    return -(VISOR_RISE_R - math.sqrt(max(VISOR_RISE_R ** 2 - t ** 2, 0.0)))

def brow_stations(t0, t1, n):
    return [(Z_FRONT + t, brow_dy(t)) for t in np.linspace(t0, t1, n)]

def build(g, info, plates, want=("shell", "spine", "keel", "coupon")):
    R_in, R_out = Region(offset(GAP)), Region(offset(GAP + WALL))
    d_skin_in, d_skin_out = GAP + WALL + AIR, GAP + WALL + AIR + SKIN
    band_air = band(d_skin_in + 0.3, GAP + WALL - 0.3, y_max=Y_SKIN_END)   # ribs overlap wall and skin by 0.3: no coincident spline faces
    band_skin = band(d_skin_out, d_skin_in, y_max=Y_SKIN_END)
    band_bar = band(d_skin_out + BAR_T, d_skin_out, y_max=Y_SKIN_END)
    y_bot_in = offset(GAP).bounds[3]; y_bot_out = offset(GAP + WALL).bounds[3]
    y_ridge = offset(d_skin_out).bounds[1]          # outer skin at the ridge (X ~ 0)
    parts = {}

    if "shell" in want:
        shell = g.prism(R_out, Z_REAR_OUT, Z_FRONT)
        shell = g.cut(shell, [g.prism(R_in, Z_REAR_IN, Z_FRONT + 1.0)])
        # ribbon-cable ports at the two rear corners (rounded inner corners) and the vent field
        def rrect(x0, y0, x1, y1, r):
            z0, z1 = Z_REAR_OUT - 1.0, Z_REAR_IN + 1.0
            return g.unite([g.box(x0 + r, y0, z0, x1 - r, y1, z1), g.box(x0, y0 + r, z0, x1, y1 - r, z1)] +
                           [g.cyl((cx, cy, z0), (cx, cy, z1), 2 * r) for cx in (x0 + r, x1 - r) for cy in (y0 + r, y1 - r)])
        y0, y1 = RIBBON_PORT_Y
        shell = g.cut(shell, [rrect(-400.0, y0, RIBBON_PORT_XIN[0], y1, PORT_R), rrect(RIBBON_PORT_XIN[1], y0, 400.0, y1, PORT_R)])
        vents = [g.box(x - VENT_W / 2, vy0, Z_REAR_OUT - 1.0, x + VENT_W / 2, vy1, Z_REAR_IN + 1.0)
                 for x in np.arange(VENT_X[0], VENT_X[1] + 0.1, VENT_X[2]) for (vy0, vy1) in VENT_ROWS]
        shell = g.cut(shell, vents)
        # front lips: top arch lip and bottom chin, both in front of the bezel rim
        lip_top = g.prism(band(GAP + 0.3, -LIP_TOP_IN, y_max=LIP_TOP_YMAX), LIP_TOP_Z0, Z_FRONT)
        chin = g.prism(band(GAP + 0.3, -CHIN_IN, y_min=CHIN_YMIN), CHIN_Z0, Z_FRONT)
        # double skin over the arch, ribs in the air gap, arched brow with a rounded bead
        skin = g.prism(band_skin, Z_REAR_OUT, Z_FRONT)
        # brow: the skin band lofted along an arc that leaves the roof tangentially and curls up; rounded bead at the tip
        visor = g.sweep_prism(band_skin, brow_stations(0.0, VISOR_L - BEAD_L + 0.5, VISOR_STATIONS))
        band_bead = band(d_skin_out + (BEAD_D - SKIN) / 2, d_skin_in - (BEAD_D - SKIN) / 2, y_max=Y_SKIN_END)
        vlip = g.sweep_prism(band_bead, brow_stations(VISOR_L - BEAD_L, VISOR_L, 2))
        vlip = g.fillet_try(vlip, (BEAD_D - SKIN) / 2 - 0.1)
        airgap = g.prism(band_air, Z_REAR_OUT, Z_FRONT)
        ribs = [g.box(x - RIB_T / 2, -200, Z_REAR_OUT, x + RIB_T / 2, Y_SKIN_END + 1, Z_FRONT) for x in RIB_X]
        ribs += [g.box(x - SPINE_RIB_T / 2, -200, Z_REAR_OUT, x + SPINE_RIB_T / 2, Y_SKIN_END + 1, Z_FRONT) for x in SPINE_RIB_X]
        ribs += [g.box(-300, Y_SKIN_END - 3.0, Z_REAR_OUT, 300, Y_SKIN_END + 1, Z_FRONT)]          # end closers
        ribs = g.intersect(g.unite(ribs), [airgap])
        shell = g.unite([shell, lip_top, chin, skin, visor, vlip, ribs])
        # lug cradle: block behind each plate with tilted stop pads at the holes, ledge under the plate, fin outside it
        for side, ids in LUGS.items():
            p = plates[side]; sgn = -1 if side == "L" else 1
            xs = [HOLES[i][0] for i in ids]; ys = [HOLES[i][1] for i in ids]
            ztop = p["zmin_block"] - STOP_GAP
            blk = g.box(min(xs) - 7.5, min(ys) - 7.0, Z_REAR_IN - 1.0, max(xs) + 7.5, y_bot_in + 1.0, ztop)
            tools = [blk]
            for h in ids:
                cx, cy, cz, n = HOLES[h]; n = unit(n); c = np.array([cx, cy, info[h]["seat"]])
                tools.append(g.cyl(tuple(c - n * ((info[h]["seat"] - ztop) / n[2] + 2.0)), tuple(c - n * STOP_GAP), LUG_PAD_D))
            fx0 = p["x_out"] + sgn * FIN_CLR; fx1 = fx0 + sgn * FIN_T
            tools.append(g.box(min(fx0, fx1), 79.0, Z_REAR_IN - 1.0, max(fx0, fx1), y_bot_in + 1.0, p["z_front"] + 3.0))
            lx = sorted([p["x_in"] - sgn * 8.0, p["x_out"] - sgn * 6.0])
            tools.append(g.box(lx[0], p["y_bot"] + LEDGE_CLR, Z_REAR_IN - 1.0, lx[1], y_bot_in + 1.0, p["z_front"] + 3.0))
            shell = g.unite([shell] + tools)
        # ear stop pads: small tilted pad outward of the hole, webbed to the side wall
        for h in EARS:
            cx, cy, cz, n = HOLES[h]; n = unit(n); seat = info[h]["seat"]
            q = nearest_points(Point(cx, cy), offset(GAP).exterior)[1]
            u = unit([q.x - cx, q.y - cy, 0.0]); wall_d = math.hypot(q.x - cx, q.y - cy)
            c = np.array([cx, cy, seat]) + u * EAR_SHIFT
            pad = g.cyl(tuple(c - n * (STOP_GAP + EAR_PAD_L)), tuple(c - n * STOP_GAP), EAR_PAD_D)
            z_pad_bot = c[2] - (STOP_GAP + EAR_PAD_L) * n[2]
            web = g.rotbox(c[0], c[1], z_pad_bot - 5.0, seat - STOP_GAP - 2.5, wall_d - EAR_SHIFT + WALL + 1.0, EAR_WEB_W, math.degrees(math.atan2(u[1], u[0])))
            web = g.chamfer_bottom_try(web, 4.0)
            tb = g.intersect(g.unite([pad, web]), [g.prism(Region(offset(GAP + WALL - 0.3)), Z_REAR_OUT, Z_FRONT)])   # web ends 0.3 inside the wall
            shell = g.unite([shell, tb])
        # mount interface: pivot knuckles under the lug blocks + stay boss on the left side wall
        yb = y_bot_out
        for kx in KNUCKLE_X:
            kn = g.unite([g.box(kx - KNUCKLE_W / 2, yb - 1.0, KNUCKLE_Z - KNUCKLE_D / 2, kx + KNUCKLE_W / 2, yb + KNUCKLE_H - KNUCKLE_R, KNUCKLE_Z + KNUCKLE_D / 2),
                          g.cyl((kx - KNUCKLE_W / 2, yb + KNUCKLE_H - KNUCKLE_R, KNUCKLE_Z), (kx + KNUCKLE_W / 2, yb + KNUCKLE_H - KNUCKLE_R, KNUCKLE_Z), 2 * KNUCKLE_R)])
            shell = g.unite([shell, kn])
            shell = g.cut(shell, [g.cyl((kx - KNUCKLE_W / 2 - 1, yb + KNUCKLE_H - KNUCKLE_R, KNUCKLE_Z), (kx + KNUCKLE_W / 2 + 1, yb + KNUCKLE_H - KNUCKLE_R, KNUCKLE_Z), PIN_D)])
        sb = STAY_BOSS; xr = offset(GAP + WALL).bounds[2]   # scan +X outer wall (driver's left, toward the A-pillar bar)
        shell = g.unite([shell, g.cyl((xr - 1.0, sb["y"], sb["z"]), (xr + sb["h"], sb["y"], sb["z"]), sb["d"])])
        shell = g.cut(shell, [g.cyl((xr - WALL - 1.0, sb["y"], sb["z"]), (xr + sb["h"] + 1.0, sb["y"], sb["z"]), sb["hole"])])
        # insert bores for the spine (from the skin surface into the thick ribs) and visor through-holes
        bores = []
        for x in SPINE_RIB_X:
            for z in SPINE_SCREW_Z:
                bores.append(g.cyl((x, y_ridge - 1.0, z), (x, y_ridge + INSERT_M25_DEPTH, z), INSERT_M25_D))
            for s in SPINE_VISOR_SCREW:
                zz = Z_FRONT + s; yy = y_ridge + brow_dy(s)
                bores.append(g.cyl((x, yy - 6.0, zz), (x, yy + 6.0, zz), 3.0))
        # keel: interior pads + insert bores through rear and bottom walls
        pads = []
        for sy in KEEL_REAR_SCREWS_Y:
            for sx in (-KEEL_SCREW_X, KEEL_SCREW_X):
                pads.append(g.cyl((sx, sy, Z_REAR_IN - 1), (sx, sy, Z_REAR_IN + PAD_H), 9.0))
                bores.append(g.cyl((sx, sy, Z_REAR_OUT - 1), (sx, sy, Z_REAR_OUT + INSERT_M25_DEPTH), INSERT_M25_D))
        for sz in KEEL_BOT_SCREWS_Z:
            for sx in (-KEEL_SCREW_X, KEEL_SCREW_X):
                pads.append(g.cyl((sx, y_bot_in + 1, sz), (sx, y_bot_in - PAD_H, sz), 9.0))
                bores.append(g.cyl((sx, y_bot_out + 1, sz), (sx, y_bot_out - INSERT_M25_DEPTH, sz), INSERT_M25_D))
        shell = g.unite([shell] + pads)
        shell = g.cut(shell, bores)
        # split into halves at X = 0
        left, right = g.split_x0(shell)
        parts["Shell L"] = g.name(left, "Shell L", COL_BODY)
        parts["Shell R"] = g.name(right, "Shell R", COL_BODY)

    if "spine" in want:
        bar = g.unite([g.prism(band_bar, Z_REAR_OUT, Z_FRONT), g.sweep_prism(band_bar, brow_stations(0.0, VISOR_L - BEAD_L, VISOR_STATIONS))])
        bar = g.intersect(bar, [g.box(-SPINE_W / 2, -300, -300, SPINE_W / 2, 300, 300)])
        holes = []
        for x in SPINE_RIB_X:
            for z in SPINE_SCREW_Z:
                holes.append(g.cyl((x, y_ridge - BAR_T - 2, z), (x, y_ridge + 1, z), CLR_M25))
                holes.append(g.cyl((x, y_ridge - BAR_T - 2, z), (x, y_ridge - BAR_T + CBORE_M25_H, z), CBORE_M25_D))
            for s in SPINE_VISOR_SCREW:
                zz = Z_FRONT + s; yy = y_ridge + brow_dy(s)
                holes.append(g.cyl((x, yy - BAR_T - 2, zz), (x, yy + 1, zz), CLR_M25))
                holes.append(g.cyl((x, yy - BAR_T - 2, zz), (x, yy - BAR_T + CBORE_M25_H, zz), CBORE_M25_D))
        parts["Spine bar"] = g.name(g.cut(bar, holes), "Spine bar", COL_ACCENT)

    if "keel" in want:
        yb = y_bot_out
        keel = g.unite([g.box(-KEEL_W / 2, KEEL_Y0, Z_REAR_OUT - BAR_T, KEEL_W / 2, yb + BAR_T, Z_REAR_OUT),
                        g.box(-KEEL_W / 2, yb, Z_REAR_OUT - BAR_T, KEEL_W / 2, yb + BAR_T, Z_FRONT - 5.0)])
        holes = []
        for sy in KEEL_REAR_SCREWS_Y:
            for sx in (-KEEL_SCREW_X, KEEL_SCREW_X):
                holes.append(g.cyl((sx, sy, Z_REAR_OUT - BAR_T - 1), (sx, sy, Z_REAR_OUT + 1), CLR_M25))
                holes.append(g.cyl((sx, sy, Z_REAR_OUT - BAR_T - 1), (sx, sy, Z_REAR_OUT - BAR_T + CBORE_M25_H), CBORE_M25_D))
        for sz in KEEL_BOT_SCREWS_Z:
            for sx in (-KEEL_SCREW_X, KEEL_SCREW_X):
                holes.append(g.cyl((sx, yb + BAR_T + 1, sz), (sx, yb - 1, sz), CLR_M25))
                holes.append(g.cyl((sx, yb + BAR_T + 1, sz), (sx, yb + BAR_T - CBORE_M25_H, sz), CBORE_M25_D))
        parts["Keel bar"] = g.name(g.cut(keel, holes), "Keel bar", COL_ACCENT)

    if "coupon" in want:
        # fit coupon beside the shell: M2.5 insert bore, M2.5 self-tap pilot, M6 nut pocket + clearance, a fin slot
        x0, y0 = 240.0, 60.0; zt = Z_REAR_OUT + 8
        cp = g.box(x0, y0, Z_REAR_OUT, x0 + 50, y0 + 20, zt)
        cp = g.cut(cp, [g.cyl((x0 + 8, y0 + 10, zt + 1), (x0 + 8, y0 + 10, zt - INSERT_M25_DEPTH), INSERT_M25_D),
                        g.cyl((x0 + 18, y0 + 10, zt + 1), (x0 + 18, y0 + 10, zt - 6.0), PILOT_M25),
                        g.cyl((x0 + 32, y0 + 10, Z_REAR_OUT - 1), (x0 + 32, y0 + 10, zt + 1), CLR_M6),
                        g.hexprism(x0 + 32, y0 + 10, zt - NUT_M6_H, zt + 1, NUT_M6_AF),
                        g.box(x0 + 43, y0 + 3, zt - 4.0, x0 + 43 + FIN_T + 2 * FIN_CLR, y0 + 17, zt + 1)])
        parts["Test coupon"] = g.name(cp, "Test coupon", COL_COUPON)
    return parts

# ------------------------------------------------------------------ CadQuery backend
class CQ:
    def __init__(self):
        import cadquery as cq; self.cq = cq
    def _ring_wire(self, poly, z):
        cq = self.cq; ring = np.array(poly.exterior.coords)[:-1]
        return cq.Wire.makePolygon([cq.Vector(float(p[0]), float(p[1]), z) for p in ring] + [cq.Vector(float(ring[0][0]), float(ring[0][1]), z)])
    def prism(self, region, z0, z1):
        cq = self.cq
        return cq.Solid.extrudeLinear(cq.Face.makeFromWires(self._ring_wire(region.poly, z0)), cq.Vector(0, 0, z1 - z0))
    def sweep_prism(self, region, stations):
        """Smooth loft through copies of the region placed at (z, dy) stations."""
        cq = self.cq
        wires = [self._ring_wire(region.poly, z).translate(cq.Vector(0, dy, 0)) for z, dy in stations]
        return cq.Solid.makeLoft(wires, ruled=len(wires) == 2)
    def fillet_try(self, body, r):
        try: return self.cq.Workplane(obj=body).edges(">Z").fillet(r).val()
        except Exception as e: print("  (fillet skipped:", str(e)[:50], ")"); return body
    def box(self, x0, y0, z0, x1, y1, z1):
        return self.cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, self.cq.Vector(x0, y0, z0))
    def cyl(self, p0, p1, d):
        cq = self.cq; a, b = cq.Vector(*p0), cq.Vector(*p1); v = b - a
        return cq.Solid.makeCylinder(d / 2, v.Length, a, v.normalized())
    def rotbox(self, cx, cy, z0, z1, L, W, deg):
        b = self.cq.Solid.makeBox(L, W, z1 - z0, self.cq.Vector(cx, cy - W / 2, z0))
        return b.rotate(self.cq.Vector(cx, cy, 0), self.cq.Vector(cx, cy, 1), deg)
    def hexprism(self, cx, cy, z0, z1, af):
        cq = self.cq; r = af / math.sqrt(3)
        pts = [cq.Vector(cx + r * math.cos(math.radians(60 * k + 30)), cy + r * math.sin(math.radians(60 * k + 30)), z0) for k in range(6)]
        return cq.Solid.extrudeLinear(cq.Face.makeFromWires(cq.Wire.makePolygon(pts + pts[:1])), cq.Vector(0, 0, z1 - z0))
    def unite(self, bodies):
        b = bodies[0]
        for t in bodies[1:]: b = b.fuse(t)
        return b.clean()
    def cut(self, target, tools):
        for t in tools: target = target.cut(t)
        return target
    def intersect(self, target, tools):
        for t in tools: target = target.intersect(t)
        return target
    def split_x0(self, body):
        other = body.copy()
        return (body.intersect(self.box(-400, -300, -300, 0.0, 300, 300)), other.intersect(self.box(0.0, -300, -300, 400, 300, 300)))
    def chamfer_bottom_try(self, body, w):
        try: return self.cq.Workplane(obj=body).faces("<Z").chamfer(w).val()
        except Exception as e: print("  (chamfer skipped:", str(e)[:50], ")"); return body
    def name(self, body, label, rgb): body.label = label; body.rgb = rgb; return body

# ------------------------------------------------------------------ FeatureScript backend
class FS:
    def __init__(self): self.lines = []; self.n = 0
    def uid(self, tag): self.n += 1; return f'id + "{tag}{self.n}"'
    def var(self, tag): self.n += 1; return f"{tag}{self.n}"
    def w(self, s):
        if not s.startswith(("if (", "{", "}")):
            self.lines.append(f'        step = "{len(self.lines)}";')
        self.lines.append("        " + s)
    def _pts(self, pts): return "[" + ", ".join(f"vector({p[0]:.3f}, {p[1]:.3f}) * millimeter" for p in pts) + "]"
    def _sketch(self, region, z0, dy=0.0):
        sk = self.var("sk"); skid = self.uid("sk")
        self.w(f"var {sk} = newSketchOnPlane(context, {skid}, {{ \"sketchPlane\" : plane(vector(0, 0, {z0:.3f}) * millimeter, vector(0, 0, 1), vector(1, 0, 0)) }});")
        for k, ch in enumerate(region.chunks()):
            if ch[0] == "spline":
                self.w(f"skFitSpline({sk}, \"c{k}\", {{ \"points\" : {self._pts([(p[0], p[1] + dy) for p in ch[1]])} }});")
            else:
                self.w(f"skLineSegment({sk}, \"c{k}\", {{ \"start\" : vector({ch[1][0]:.3f}, {ch[1][1] + dy:.3f}) * millimeter, \"end\" : vector({ch[2][0]:.3f}, {ch[2][1] + dy:.3f}) * millimeter }});")
        self.w(f"skSolve({sk});")
        return skid
    def prism(self, region, z0, z1):
        skid = self._sketch(region, z0); ex = self.uid("ex"); v = self.var("b")
        self.w(f"opExtrude(context, {ex}, {{ \"entities\" : qSketchRegion({skid}), \"direction\" : vector(0, 0, 1), \"endBound\" : BoundingType.BLIND, \"endDepth\" : {z1 - z0:.3f} * millimeter }});")
        self.w(f"const {v} = qCreatedBy({ex}, EntityType.BODY);")
        return v
    def sweep_prism(self, region, stations):
        """Loft through copies of the region at (z, dy) stations (verified: opLoft with spline-band profiles)."""
        sks = [self._sketch(region, z, dy) for z, dy in stations]; lf = self.uid("lf"); v = self.var("b")
        self.w(f"opLoft(context, {lf}, {{ \"profileSubqueries\" : [{', '.join(f'qSketchRegion({k})' for k in sks)}] }});")
        self.w(f"const {v} = qCreatedBy({lf}, EntityType.BODY);")
        return v
    def fillet_try(self, body, r):
        self.w(f"try silent {{ opFillet(context, {self.uid('fl')}, {{ \"entities\" : qAdjacent(qFarthestAlong(qOwnedByBody({body}, EntityType.FACE), vector(0, 0, 1)), AdjacencyType.EDGE, EntityType.EDGE), \"radius\" : {r:.3f} * millimeter }}); }}"); return body
    def box(self, x0, y0, z0, x1, y1, z1):
        v = self.var("b"); self.w(f"const {v} = mkBox(context, {self.uid('bx')}, {x0:.3f}, {y0:.3f}, {z0:.3f}, {x1:.3f}, {y1:.3f}, {z1:.3f});"); return v
    def cyl(self, p0, p1, d):
        v = self.var("b"); self.w(f"const {v} = mkCyl(context, {self.uid('cy')}, vector({p0[0]:.3f}, {p0[1]:.3f}, {p0[2]:.3f}), vector({p1[0]:.3f}, {p1[1]:.3f}, {p1[2]:.3f}), {d:.3f});"); return v
    def rotbox(self, cx, cy, z0, z1, L, W, deg):
        v = self.box(cx, cy - W / 2, z0, cx + L, cy + W / 2, z1)
        self.w(f"rotZ(context, {self.uid('rz')}, {v}, {cx:.3f}, {cy:.3f}, {deg:.3f});"); return v
    def hexprism(self, cx, cy, z0, z1, af):
        v = self.var("b"); self.w(f"const {v} = mkHex(context, {self.uid('hx')}, {cx:.3f}, {cy:.3f}, {z0:.3f}, {z1:.3f}, {af:.3f});"); return v
    def unite(self, bodies):
        if len(bodies) == 1: return bodies[0]
        acc = bodies[0]
        for b in bodies[1:]:
            v = self.var("u"); self.w(f"const {v} = mkUnite(context, {self.uid('un')}, [{acc}, {b}]);"); acc = v
        return acc
    def cut(self, target, tools):
        self.w(f"mkCut(context, {self.uid('ct')}, {target}, [{', '.join(tools)}]);"); return target
    def intersect(self, target, tools):
        self.w(f"mkIntersect(context, {self.uid('it')}, {target}, [{', '.join(tools)}]);"); return target
    def split_x0(self, body):
        pl = self.uid("pl"); sp = self.uid("sp"); L = self.var("left"); R = self.var("right")
        self.w(f"opPlane(context, {pl}, {{ \"plane\" : plane(vector(0, 0, 0) * millimeter, vector(1, 0, 0)), \"width\" : 900 * millimeter, \"height\" : 900 * millimeter }});")
        self.w(f"opSplitPart(context, {sp}, {{ \"targets\" : {body}, \"tool\" : qCreatedBy({pl}, EntityType.FACE), \"keepTools\" : false }});")
        self.w(f"const {L} = qFarthestAlong({body}, vector(-1, 0, 0));")
        self.w(f"const {R} = qSubtraction({body}, {L});")
        return L, R
    def chamfer_bottom_try(self, body, w):
        self.w(f"try silent {{ chamferBottom(context, {self.uid('cb')}, {body}, {w:.3f}); }}"); return body
    def name(self, body, label, rgb):
        self.w(f"nameBody(context, {body}, \"{label}\", color({rgb[0]:.3f}, {rgb[1]:.3f}, {rgb[2]:.3f}));"); return body

FS_HEADER = '''FeatureScript 3083;
import(path : "onshape/std/common.fs", version : "3083.0");

// GENERATED by mechanical/generate.py in probe-gauge-cluster-enclosure. Edit the Python constants, not this file.
// 1993 Ford Probe GT gauge cluster enclosure. Frame = scan frame (X across, Y down, Z toward the driver), millimetres.

function mkBox(context is Context, id is Id, x0 is number, y0 is number, z0 is number, x1 is number, y1 is number, z1 is number) returns Query
{
    fCuboid(context, id, { "corner1" : vector(x0, y0, z0) * millimeter, "corner2" : vector(x1, y1, z1) * millimeter });
    return qCreatedBy(id, EntityType.BODY);
}
function mkCyl(context is Context, id is Id, p0 is Vector, p1 is Vector, d is number) returns Query
{
    fCylinder(context, id, { "topCenter" : p1 * millimeter, "bottomCenter" : p0 * millimeter, "radius" : d / 2 * millimeter });
    return qCreatedBy(id, EntityType.BODY);
}
function mkHex(context is Context, id is Id, cx is number, cy is number, z0 is number, z1 is number, af is number) returns Query
{
    var sk = newSketchOnPlane(context, id + "sk", { "sketchPlane" : plane(vector(0, 0, z0) * millimeter, vector(0, 0, 1), vector(1, 0, 0)) });
    const r = af / sqrt(3);
    skRegularPolygon(sk, "hex", { "center" : vector(cx, cy) * millimeter, "firstVertex" : vector(cx + r * cos(30 * degree), cy + r * sin(30 * degree)) * millimeter, "sides" : 6 });
    skSolve(sk);
    opExtrude(context, id + "ex", { "entities" : qSketchRegion(id + "sk"), "direction" : vector(0, 0, 1), "endBound" : BoundingType.BLIND, "endDepth" : (z1 - z0) * millimeter });
    return qCreatedBy(id + "ex", EntityType.BODY);
}
function mkUnite(context is Context, id is Id, bodies is array) returns Query
{
    opBoolean(context, id, { "tools" : qUnion(bodies), "operationType" : BooleanOperationType.UNION });
    return qUnion(bodies);
}
function mkCut(context is Context, id is Id, target is Query, tools is array)
{
    opBoolean(context, id, { "targets" : target, "tools" : qUnion(tools), "operationType" : BooleanOperationType.SUBTRACTION });
}
function mkIntersect(context is Context, id is Id, target is Query, tools is array)
{
    // target ∩ tools while keeping the target's identity (INTERSECTION would create a new body under the boolean id)
    opBoolean(context, id, { "targets" : target, "tools" : qUnion(tools), "operationType" : BooleanOperationType.SUBTRACT_COMPLEMENT });
}
function rotZ(context is Context, id is Id, body is Query, cx is number, cy is number, deg is number)
{
    opTransform(context, id, { "bodies" : body, "transform" : rotationAround(line(vector(cx, cy, 0) * millimeter, vector(0, 0, 1)), deg * degree) });
}
function chamferBottom(context is Context, id is Id, body is Query, w is number)
{
    const bot = qFarthestAlong(qOwnedByBody(body, EntityType.FACE), vector(0, 0, -1));
    opChamfer(context, id, { "entities" : qAdjacent(bot, AdjacencyType.EDGE, EntityType.EDGE), "chamferType" : ChamferType.EQUAL_OFFSETS, "width" : w * millimeter });
}
function nameBody(context is Context, body is Query, name is string, c is Color)
{
    setProperty(context, { "entities" : body, "propertyType" : PropertyType.NAME, "value" : name });
    setProperty(context, { "entities" : body, "propertyType" : PropertyType.APPEARANCE, "value" : c });
}

annotation { "Feature Type Name" : "Probe cluster enclosure" }
export const probeClusterEnclosure = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Shell halves" } definition.buildShell is boolean;
        annotation { "Name" : "Spine bar" } definition.buildSpine is boolean;
        annotation { "Name" : "Keel bar" } definition.buildKeel is boolean;
        annotation { "Name" : "Test coupon" } definition.buildCoupon is boolean;
    }
    {
        var step = "start";
        try
        {
'''
FS_FOOTER = '''        }
        catch (e)
        {
            // diagnostic: surface the failing step as a part name (readable through the REST parts endpoint)
            fCuboid(context, id + "errbox", { "corner1" : vector(300, -100, -55) * millimeter, "corner2" : vector(310, -90, -45) * millimeter });
            setProperty(context, { "entities" : qCreatedBy(id + "errbox", EntityType.BODY), "propertyType" : PropertyType.NAME, "value" : "FAILED step " ~ step ~ ": " ~ toString(e) });
        }
    }, { buildShell : true, buildSpine : true, buildKeel : true, buildCoupon : true });
'''

def emit_fs(info, plates):
    fs = FS()
    for flag, want in (("buildShell", ("shell",)), ("buildSpine", ("spine",)), ("buildKeel", ("keel",)), ("buildCoupon", ("coupon",))):
        fs.w(f"if (definition.{flag})"); fs.w("{")
        build(fs, info, plates, want=want)
        fs.w("}")
    return FS_HEADER + "\n".join(fs.lines) + "\n" + FS_FOOTER

# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fs-only", action="store_true"); ap.add_argument("--no-mesh", action="store_true")
    a = ap.parse_args()
    mesh, info, plates = mesh_probe()
    print("seat data (CSV hole-centre Z is the seat; mesh median for comparison):")
    for h in list(LUGS["L"]) + list(LUGS["R"]) + EARS:
        d = info[h]; print(f"  {h}: seat z={d['seat']:.1f}  mesh {d['mesh_face']:.1f} (n={d['n']})")
    for k, p in plates.items():
        print(f"  lug plate {k}: outer edge x={p['x_out']:.1f} inner x={p['x_in']:.1f} bottom y={p['y_bot']:.1f} z {p['z_rear']:.1f}..{p['z_front']:.1f}  block min z={p['zmin_block']:.1f}")
    cav = offset(GAP); d = min(Point(p).distance(cav.exterior) for p in OUTLINE.exterior.coords[::2])
    print(f"cavity min clearance to scanned silhouette: {d:.2f} mm (target {GAP})")
    code = emit_fs(info, plates)
    (OUT / "probe_cluster_enclosure.fs").write_text(code)
    print(f"FeatureScript: {len(code.splitlines())} lines, {len(code)//1024} kB -> output/probe_cluster_enclosure.fs")
    json.dump(dict(info={k: dict(seat=v['seat'], mesh_face=v['mesh_face']) for k, v in info.items()}, plates=plates), open(OUT / "seat_data.json", "w"), indent=1)
    if a.fs_only: return
    import cadquery as cq
    g = CQ(); parts = build(g, info, plates)
    for label, body in parts.items():
        fn = OUT / (label.lower().replace(" ", "_") + ".stl")
        cq.exporters.export(cq.Workplane(obj=body), str(fn), tolerance=0.05, angularTolerance=0.1)
        bb = body.BoundingBox()
        print(f"  {label:<12} bbox x {bb.xmin:7.1f}..{bb.xmax:6.1f}  y {bb.ymin:6.1f}..{bb.ymax:5.1f}  z {bb.zmin:6.1f}..{bb.zmax:6.1f}  vol {body.Volume()/1000:7.1f} cm3  solids {len(body.Solids())}")
    if not a.no_mesh:
        import trimesh, collections
        v = mesh.vertices
        for label in ("Shell L", "Shell R"):
            body = parts[label]
            sm = trimesh.load(OUT / (label.lower().replace(" ", "_") + ".stl"))
            sel = v[(v[:, 0] <= 2) if label == "Shell L" else (v[:, 0] >= -2)]
            _, dist, _ = trimesh.proximity.closest_point(sm, sel)
            near = sel[dist < 1.5]
            inside = np.array([p for p in near if body.isInside(cq.Vector(*p), 0.01)]) if len(near) else np.zeros((0, 3))
            print(f"  {label}: cluster vertices within 1.5 mm of the shell: {len(near)}; INSIDE the shell solid: {len(inside)}; min distance {dist.min():.2f} mm")
            if len(near):
                cells = collections.Counter((round(p[0] / 10) * 10, round(p[1] / 10) * 10, round(p[2] / 10) * 10) for p in (inside if len(inside) else near))
                print("    " + ("PENETRATION" if len(inside) else "closest approach") + " cells (x,y,z rounded to 10):")
                for c, n in cells.most_common(8): print(f"      {c}: {n}")

if __name__ == "__main__":
    main()
