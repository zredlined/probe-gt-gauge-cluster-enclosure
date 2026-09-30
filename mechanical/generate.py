#!/usr/bin/env python
"""1993 Ford Probe GT gauge cluster enclosure: scan-derived constants -> CadQuery (local renders, mesh clearance)
and FeatureScript (Onshape custom feature) from the SAME geometry description.

Frame = scan frame of onshape_reference_package (mm): X across the cluster, Y increases DOWNWARD in the car,
Z toward the driver (front/glass +Z, rear/connectors -Z).  Keep it so the STL, DXF and hole CSV line up in Onshape.

Parts (v0.5): two FEET bolted to the cluster through its OEM lug holes (chassis); Shell L / Shell R (split at X=0) as a
cover bolted to the feet from below (M4 into nuts captured in the feet); Spine bar (top ridge) and Keel bar (rear+bottom
seam) joining the halves; Test coupon.  v0.6: the front of the shell is a NOSE lofted to the scanned bezel rim, and each
ear tab bolts from the front (M4 through the lens notch) into an ear BOSS moulded into the roof with a side-entry nut channel.
Rear-corner ports for the two ribbon plugs, vents, sun brow.

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
Z_FRONT = 64.0       # shell front edge: the clear LENS stands ~11 mm proud of the scanned rim (49.5), measured 2026-09-27
# v0.6 NOSE: the bezel shroud tapers toward the face (top edge y -81.6 at the back, -70 at the rim), so from NOSE_Z0 the wall
# lofts inward to the scanned FRONT-RIM outline (hull of scan vertices with z >= NOSE_SCAN_ZMIN) plus NOSE_CLR.
NOSE_Z0, NOSE_SCAN_ZMIN, NOSE_CLR, NOSE_RIM_T = 30.0, 36.0, 2.5, 4.0
Z_REAR_IN = -61.0    # rear wall inner face: the real cluster touched a wall at -58, so 3 mm more than the scan's -55.8 + 2
Z_REAR_OUT = Z_REAR_IN - WALL_REAR
VISOR_L = 70.0       # brow length forward of the shell front edge
VISOR_RISE_R = 200.0 # brow follows an arc tangent to the roof that curls UP (toward -Y, car-up); larger = flatter
VISOR_STATIONS = 6   # loft sections along the arc
BEAD_D, BEAD_L = 5.0, 6.0   # rounded bead at the brow tip (no sharp edge to bump)
Y_SKIN_END = 5.0     # double skin / visor exist only for Y <= this (arch + short cheeks)
# ear blocks (v0.5b): the ear tabs (19.5 wide, 7 thick, 10 tall, hole ~5 below the tip, lens notched around them) are bolted
# M4 from the front into a nut captured in a small block behind each tab; the block carries two M2.5 inserts that the shell's
# roof screws reach from outside through the double skin (printed tubes bridge the air gap).
# v0.6: the ear block is MOULDED INTO THE SHELL ROOF (ear boss) with a side-entry channel for a standard M4 nut (7.0 AF x 3.2,
# loaded from the inboard side, which faces up when the half lies on its outer side); M4 x 20 from the front through the lens notch.
EAR_BLOCK_T, EAR_BLOCK_HALF_W, EAR_BLOCK_DOWN, EAR_BLOCK_UP = 10.0, 10.0, 4.0, 14.0
EAR_BOLT_CLR = 5.0                                     # a little slop: the boss is on the shell, the tab is positioned by the feet
NUT_M4_AC = 8.1                                        # M4 nut across corners (7.0 AF): the channel end must clear it
NUT_M4_SLOT_W, NUT_M4_SLOT_T, EAR_NUT_REAR_WALL = 7.2, 3.4, 1.0
EAR_CHAN_MOUTH_W = 7.6                                 # channel widens toward its mouth: the nut slides in easily and wedges snug at the end
# feet: the pad captures two M4 nuts in rear-entry slots (no inserts); M4 x 10 from below through fore-aft slots in the shell
FOOT_SLOT_HALF = 2.0; CLR_M4_SHELL = 4.5
# ribbon-cable ports: the two vertical PCB slots (left x -179..-173, right x 161..168, y ~2..50, thumb lock outboard).
# Each port opens the rear wall from 12 mm inboard of the slot out to the side wall, 12 mm above and below the slot.
RIBBON_PORT_XIN = (-163.0, 149.0); RIBBON_PORT_Y = (-14.0, 68.0); PORT_R = 8.0   # plugs measured 51 / 59.8 x 9.6 + 4 mm lock
VENT_X = (-105.0, 105.0, 7.0); VENT_ROWS = [(-48.0, -22.0), (-14.0, 12.0)]; VENT_W = 2.4   # two rows of vertical vent slots
RIB_X = [-160.0, -115.0, -60.0, 60.0, 115.0, 160.0]; RIB_T = 1.6
SPINE_RIB_X = [-6.0, 6.0]; SPINE_RIB_T = 8.0                    # thick ribs carrying the spine inserts, one per half
SPINE_W = 30.0; SPINE_SCREW_Z = [-40.0, -8.0, 22.0]; SPINE_VISOR_SCREW = [20.0, 55.0]   # straight screws end before the nose/brow at NOSE_Z0
KEEL_W = 40.0; KEEL_Y0 = 48.0; KEEL_REAR_SCREWS_Y = [58.0, 84.0]; KEEL_BOT_SCREWS_Z = [-30.0, 0.0]; KEEL_SCREW_X = 12.0; KEEL_Z_END = 12.0   # bottom leg stops short of the lock knuckles (M6 nut access, fastener_check.py)
PAD_H = 5.0
INSERT_M25_D, INSERT_M25_DEPTH = 3.4, 6.5     # coupon-verified bore for the user's M2.5 x 4 x 3.5 OD inserts
PILOT_M25 = 2.4                               # coupon-verified self-tap pilot
CLR_M25, CBORE_M25_D, CBORE_M25_H = 2.7, 5.0, 1.5
CLR_M6, NUT_M6_AF, NUT_M6_H = 6.4, 10.0, 5.2
# mount interface (v0.4): two pivot knuckles on the bottom wall under the lug blocks (M8 pin along X = pitch axis) and a
# stay boss on the left side wall (M6 along X). Car-frame placement and the mount parts live in mount.py.
KNUCKLE_X = [-155.0, 155.0]; KNUCKLE_W, KNUCKLE_D, KNUCKLE_H = 24.0, 40.0, 22.0   # X width, Z depth, protrusion below the bottom wall
KNUCKLE_Z = 7.0; PIN_D = 8.4; KNUCKLE_R = 10.0     # pin lands directly above the crossbar at the chosen placement; body overlaps the ledge blocks
# pitch-lock knuckles (M6) near the front-bottom edge, above the two steering-support arms (car x 203 / 325 -> scan x = X_C - x)
LOCK_X = [59.0, -62.5]; LOCK_W, LOCK_D, LOCK_H, LOCK_R, LOCK_Z, LOCK_HOLE = 16.0, 14.0, 12.0, 6.0, 18.0, 6.4   # LOCK_Z inside the straight wall (nose starts at 30)
STOP_GAP = 1.0                                # rear stop pads stand off the scanned faces by this
LUG_PAD_D = 8.0; FIN_T = 2.5; FIN_CLR = 0.8; LEDGE_CLR = 0.6
EAR_PAD_D, EAR_SHIFT, EAR_PAD_L, EAR_WEB_W = 7.0, 2.0, 5.0, 7.0   # ear pad sits outward of the hole: the housing wall hugs the inner side
# v0.5 chassis: two small FEET bolt to the cluster through its own OEM holes (measured 2026-09-27: all eight 5.3 mm, B6 a
# 5.3 x 8.8 slot; lug plates 4.8 thick, ear tabs 7.0; 38 mm free behind the lug plates, 50 behind the ears); the shell then
# screws to the feet from OUTSIDE (M2.5 into inserts). Only the feet depend on the scan at the millimetre level.
FOOT_T = 8.0; FOOT_STANDOFF = 0.8                      # slab thickness behind the tab; gap between tab rear face and slab
LUG_PLATE_T, EAR_TAB_T = 4.8, 7.0                      # measured tab thicknesses (bolt length); the CSV hole centre lies on the
                                                       # tab's REAR face (the holes were fitted on the rear scan), so feet seat at centre + STANDOFF
BOLT_M4_CLR, NUT_M4_AF, NUT_M4_H = 4.5, 7.3, 3.6       # M4 through the 5.3 mm OEM holes, nut captured in a hex pocket
LUG_FOOT_MARGIN_IN, LUG_FOOT_MARGIN_OUT, LUG_FOOT_UP, LUG_FOOT_DOWN = 7.0, 4.5, 7.0, 7.0   # slab around the bolt pair; the plate has a rib on its
                                                       # outer edge ~6-7 mm outboard of the outer hole, hence the short outboard margin; B1/B4 unused
LUG_PAD_Y0 = 86.0; LUG_PAD_Z = (-38.0, -14.0); LUG_PAD_SCREW_Z = -28.0; LUG_PAD_X_MARGIN = 8.5   # pad down to the shell bottom wall
# (The scan suggested the ear tabs were boxed in; the user's calipers and the notch in the lens showed room behind and in
# front of each tab, hence the ear blocks above.)
FOOT_WALL_CLR = 0.3                                    # feet stop this short of the cavity wall (offset(GAP))
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

_FRONT = None
def front_outline():
    """Smoothed convex hull of the scanned bezel front region (z >= NOSE_SCAN_ZMIN): the outline the nose hugs."""
    global _FRONT
    if _FRONT is None:
        import trimesh
        from shapely.geometry import MultiPoint
        v = trimesh.load(REF / "cluster_onshape_reference_mm.stl").vertices
        _FRONT = smooth_ring(MultiPoint(v[v[:, 2] >= NOSE_SCAN_ZMIN][:, :2]).convex_hull.buffer(0))
    return _FRONT

def front_offset(d):
    return front_outline().buffer(d, join_style=1, resolution=48).simplify(0.02)

def resample_ring(poly, n=240):
    """n points at equal arc length around the ring, CCW, starting at the point nearest the top centre (loft correspondence)."""
    from shapely.geometry.polygon import orient
    ring = LineString(orient(poly, 1.0).exterior.coords); L = ring.length
    d0 = ring.project(Point(0.0, -300.0))
    return np.array([[q.x, q.y] for q in (ring.interpolate((d0 + L * k / n) % L) for k in range(n))])

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
    return [(NOSE_Z0 + t, brow_dy(t)) for t in np.linspace(t0, t1, n)]

def tab_frame(h, across):
    """Right-handed local frame at OEM hole h: e3 = into the foot (rearward, -normal), e1 = unit projection of `across`
    (a world XY direction) onto the tab plane, e2 = e3 x e1. Origin = CSV hole centre (tab mid-plane)."""
    cx, cy, cz, n = HOLES[h]; n = unit(n); e3 = -n
    a = np.array([across[0], across[1], 0.0]); e1 = unit(a - np.dot(a, e3) * e3); e2 = np.cross(e3, e1)
    if e2[1] > 0: e1, e2 = -e1, -e2          # local +y must point UP in the car (-Y); flipping two axes keeps it right-handed
    return np.array([cx, cy, cz]), e1, e2, e3

def tab_plane_z(h, x, y, along_n):
    """World z of the plane parallel to tab h, `along_n` from its CSV centre plane along the normal, at world (x, y)."""
    cx, cy, cz, n = HOLES[h]; n = unit(n)
    return cz + (along_n - n[0] * (x - cx) - n[1] * (y - cy)) / n[2]

MARK_D, MARK_DEPTH, MARK_PITCH = 2.5, 0.8, 4.5

def side_dots(g, side, p0, du, dn):
    """1 (L) or 2 (R) debossed dots: p0 = first dot centre on the face, du = unit step along the face, dn = unit face normal (outward)."""
    p0, du, dn = np.asarray(p0, float), unit(du), unit(dn)
    return [g.cyl(tuple(p0 + du * MARK_PITCH * k - dn * MARK_DEPTH), tuple(p0 + du * MARK_PITCH * k + dn * 1.0), MARK_D) for k in range(1 if side == "L" else 2)]

def tilt_bars(g, tilt, c, du, dv, dn):
    """'-' (tilt < 0) or '+' (tilt > 0) debossed on a face centred at c; du/dv in-plane unit axes, dn outward normal."""
    if not tilt: return []
    c, du, dv, dn = (np.asarray(v, float) for v in (c, du, dv, dn)); L, W = 6.0, 1.4
    bars = [(du, L, dv, W)] + ([(dv, L, du, W)] if tilt > 0 else [])
    out = []
    for a, la, b, wb in bars:
        n = int(la / 1.0)
        out += [g.cyl(tuple(c + a * (-la / 2 + la * k / n) - dn * MARK_DEPTH), tuple(c + a * (-la / 2 + la * k / n) + dn * 1.0), wb) for k in range(n + 1)]
    return out

def build_feet(g, tilt=0.0, want=("lugs",)):
    """Two lug feet: slab behind each bottom lug plate (M4 bolts through B2 B3 / B5 B6, nuts captured in hex pockets) with a pad
    down to the shell bottom wall carrying two M2.5 inserts for the shell screws (driven from outside, directly above the knuckle)."""
    parts = {}; y_pad = offset(GAP).bounds[3] - FOOT_WALL_CLR
    tag = f" tilt{tilt:+.0f}" if tilt else ""
    for side, ids in (LUGS.items() if "lugs" in want else []):
        a, b = (HOLES[i] for i in ids); mid = (np.array(a[:3]) + np.array(b[:3])) / 2
        o, e1, e2, e3 = tab_frame(ids[0], (1.0, 0.0)); o = mid
        if tilt:   # variant: slab rotated about the bolt line so the pad stays flat if the real plate is tilted by -tilt
            c, sn = math.cos(math.radians(tilt)), math.sin(math.radians(tilt)); e2, e3 = c * e2 + sn * e3, -sn * e2 + c * e3
        half = abs(np.dot(np.array(b[:3]) - np.array(a[:3]), e1)) / 2
        z0 = FOOT_STANDOFF; z1 = z0 + FOOT_T
        m_neg, m_pos = (LUG_FOOT_MARGIN_OUT, LUG_FOOT_MARGIN_IN) if side == "L" else (LUG_FOOT_MARGIN_IN, LUG_FOOT_MARGIN_OUT)   # local +x = world +x
        slab = g.box(-(half + m_neg), -LUG_FOOT_DOWN, z0, half + m_pos, LUG_FOOT_UP, z1)
        cuts = []
        for sx in (-half, half):
            cuts.append(g.cyl((sx, 0.0, z0 - 2.0), (sx, 0.0, z1 + 2.0), BOLT_M4_CLR))
            cuts.append(g.hexprism(sx, 0.0, z1 - NUT_M4_H, z1 + 1.0, NUT_M4_AF))
        slab = g.cut(slab, cuts)
        slab = g.place(slab, o, e1, e2, e3)
        xs = sorted([a[0], b[0]])
        pad = g.box(xs[0] - LUG_PAD_X_MARGIN, LUG_PAD_Y0, LUG_PAD_Z[0], xs[1] + LUG_PAD_X_MARGIN, y_pad, LUG_PAD_Z[1])
        foot = g.unite([slab, pad])
        # two M4 nuts in rear-entry slots at mid pad height; M4 x 10 comes up from under the shell
        y_nut = (LUG_PAD_Y0 + y_pad) / 2; cuts = []
        for x in xs:
            cuts.append(g.box(x - NUT_M4_SLOT_W / 2, y_nut - NUT_M4_SLOT_T / 2, LUG_PAD_Z[0] - 1.0, x + NUT_M4_SLOT_W / 2, y_nut + NUT_M4_SLOT_T / 2, LUG_PAD_SCREW_Z + NUT_M4_AC / 2 + 0.1))
            cuts.append(g.cyl((x, y_pad + 1.0, LUG_PAD_SCREW_Z), (x, LUG_PAD_Y0 - 1.0, LUG_PAD_SCREW_Z), BOLT_M4_CLR))
        foot = g.cut(foot, cuts)
        # ID marks: side dots on the pad's rear face (faces the rear wall), tilt bars on the pad's outboard end face
        xc = (xs[0] + xs[1]) / 2; ym = (LUG_PAD_Y0 + y_pad) / 2
        foot = g.cut(foot, side_dots(g, side, (xc - MARK_PITCH / 2, ym, LUG_PAD_Z[0]), (1, 0, 0), (0, 0, -1)))
        x_end = xs[0] - LUG_PAD_X_MARGIN if side == "L" else xs[1] + LUG_PAD_X_MARGIN
        foot = g.cut(foot, tilt_bars(g, tilt, (x_end, ym, (LUG_PAD_Z[0] + LUG_PAD_Z[1]) / 2), (0, 0, 1), (0, 1, 0), (-1 if side == "L" else 1, 0, 0)))
        parts[f"Foot lug {side}{tag}"] = g.name(foot, f"Foot lug {side}{tag}", COL_BODY)
    return parts

def build(g, info, plates, want=("shell", "spine", "keel", "coupon")):
    R_in, R_out = Region(offset(GAP)), Region(offset(GAP + WALL))
    d_skin_in, d_skin_out = GAP + WALL + AIR, GAP + WALL + AIR + SKIN
    band_air = band(d_skin_in + 0.3, GAP + WALL - 0.3, y_max=Y_SKIN_END)   # ribs overlap wall and skin by 0.3: no coincident spline faces
    band_skin = band(d_skin_out, d_skin_in, y_max=Y_SKIN_END)
    band_bar = band(d_skin_out + BAR_T, d_skin_out, y_max=Y_SKIN_END)
    y_bot_in = offset(GAP).bounds[3]; y_bot_out = offset(GAP + WALL).bounds[3]
    y_ridge = offset(d_skin_out).bounds[1]          # outer skin at the ridge (X ~ 0)
    parts = {}

    N_in, N_out = Region(front_offset(NOSE_CLR)), Region(front_offset(NOSE_CLR + NOSE_RIM_T))
    if "shell" in want:
        # straight wall to NOSE_Z0, then the nose: wall lofted inward to the scanned front rim (+ clearance), rim NOSE_RIM_T thick
        shell = g.prism(R_out, Z_REAR_OUT, NOSE_Z0)
        shell = g.unite([shell, g.loft_regions(R_out, NOSE_Z0, N_out, Z_FRONT)])
        shell = g.cut(shell, [g.prism(R_in, Z_REAR_IN, NOSE_Z0 + 1.0), g.loft_regions(R_in, NOSE_Z0, N_in, Z_FRONT), g.prism(N_in, Z_FRONT - 0.5, Z_FRONT + 2.0)])
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
        # double skin over the arch, ribs in the air gap, arched brow with a rounded bead (skin and brow spring from NOSE_Z0)
        skin = g.prism(band_skin, Z_REAR_OUT, NOSE_Z0)
        # brow: the skin band lofted along an arc that leaves the roof tangentially and curls up; rounded bead at the tip
        visor = g.sweep_prism(band_skin, brow_stations(0.0, VISOR_L - BEAD_L + 0.5, VISOR_STATIONS))
        band_bead = band(d_skin_out + (BEAD_D - SKIN) / 2, d_skin_in - (BEAD_D - SKIN) / 2, y_max=Y_SKIN_END)
        vlip = g.sweep_prism(band_bead, brow_stations(VISOR_L - BEAD_L, VISOR_L, 2))
        vlip = g.fillet_try(vlip, (BEAD_D - SKIN) / 2 - 0.1)
        airgap = g.prism(band_air, Z_REAR_OUT, NOSE_Z0)
        ribs = [g.box(x - RIB_T / 2, -200, Z_REAR_OUT, x + RIB_T / 2, Y_SKIN_END + 1, NOSE_Z0) for x in RIB_X]
        ribs += [g.box(x - SPINE_RIB_T / 2, -200, Z_REAR_OUT, x + SPINE_RIB_T / 2, Y_SKIN_END + 1, NOSE_Z0) for x in SPINE_RIB_X]
        ribs += [g.box(-300, Y_SKIN_END - 3.0, Z_REAR_OUT, 300, Y_SKIN_END + 1, NOSE_Z0)]          # end closers
        ribs = g.intersect(g.unite(ribs), [airgap])
        shell = g.unite([shell, skin, visor, vlip, ribs])
        # ear bosses moulded into the roof: M4 through the OEM ear hole from the front into a nut in a side-entry channel
        for h in EARS:
            cx, cy, cz, n = HOLES[h]; sgn_in = -1.0 if cx > 0 else 1.0
            o, e1, e2, e3 = tab_frame(h, (sgn_in, 0.0))
            xin = 1.0 if np.dot(e1, [sgn_in, 0.0, 0.0]) > 0 else -1.0        # local x sign that points inboard (toward x = 0)
            z0 = FOOT_STANDOFF; z1 = z0 + EAR_BLOCK_T
            boss = g.box(-EAR_BLOCK_HALF_W, -EAR_BLOCK_DOWN, z0, EAR_BLOCK_HALF_W, EAR_BLOCK_UP, z1)
            zc0 = z1 - EAR_NUT_REAR_WALL - NUT_M4_SLOT_T
            # nut channel: flat end NUT_M4_AC/2 beyond the bolt axis (a corner of the nut touches it when the nut is centred),
            # flats guided by the channel walls, width tapering from EAR_CHAN_MOUTH_W at the mouth to NUT_M4_SLOT_W at the end
            x_end, x_mouth = -xin * (NUT_M4_AC / 2 + 0.1), xin * (EAR_BLOCK_HALF_W + 1.0)
            chan = g.prism(Region(Polygon([(x_end, -NUT_M4_SLOT_W / 2), (x_end, NUT_M4_SLOT_W / 2), (x_mouth, EAR_CHAN_MOUTH_W / 2), (x_mouth, -EAR_CHAN_MOUTH_W / 2)])), zc0, zc0 + NUT_M4_SLOT_T)
            boss = g.cut(boss, [g.cyl((0.0, 0.0, z0 - 2.0), (0.0, 0.0, z1 + 2.0), EAR_BOLT_CLR), chan])
            boss = g.place(boss, o, e1, e2, e3)
            boss = g.intersect(boss, [g.prism(Region(offset(GAP + WALL - 0.3)), Z_REAR_IN, Z_FRONT)])   # reaches 2.2 mm into the wall
            shell = g.unite([shell, boss])
        # mount interface: pivot knuckles under the feet, pitch-lock knuckles near the front-bottom edge
        yb = y_bot_out
        for kx in KNUCKLE_X:
            kn = g.unite([g.box(kx - KNUCKLE_W / 2, yb - 1.0, KNUCKLE_Z - KNUCKLE_D / 2, kx + KNUCKLE_W / 2, yb + KNUCKLE_H - KNUCKLE_R, KNUCKLE_Z + KNUCKLE_D / 2),
                          g.cyl((kx - KNUCKLE_W / 2, yb + KNUCKLE_H - KNUCKLE_R, KNUCKLE_Z), (kx + KNUCKLE_W / 2, yb + KNUCKLE_H - KNUCKLE_R, KNUCKLE_Z), 2 * KNUCKLE_R)])
            shell = g.unite([shell, kn])
            shell = g.cut(shell, [g.cyl((kx - KNUCKLE_W / 2 - 1, yb + KNUCKLE_H - KNUCKLE_R, KNUCKLE_Z), (kx + KNUCKLE_W / 2 + 1, yb + KNUCKLE_H - KNUCKLE_R, KNUCKLE_Z), PIN_D)])
        for lx in LOCK_X:
            lk = g.unite([g.box(lx - LOCK_W / 2, yb - 1.0, LOCK_Z - LOCK_D / 2, lx + LOCK_W / 2, yb + LOCK_H - LOCK_R, LOCK_Z + LOCK_D / 2),
                          g.cyl((lx - LOCK_W / 2, yb + LOCK_H - LOCK_R, LOCK_Z), (lx + LOCK_W / 2, yb + LOCK_H - LOCK_R, LOCK_Z), 2 * LOCK_R)])
            shell = g.unite([shell, lk])
            shell = g.cut(shell, [g.cyl((lx - LOCK_W / 2 - 1, yb + LOCK_H - LOCK_R, LOCK_Z), (lx + LOCK_W / 2 + 1, yb + LOCK_H - LOCK_R, LOCK_Z), LOCK_HOLE)])
        # insert bores for the spine (from the skin surface into the thick ribs) and visor through-holes
        bores = []
        for x in SPINE_RIB_X:
            for z in SPINE_SCREW_Z:
                bores.append(g.cyl((x, y_ridge - 1.0, z), (x, y_ridge + INSERT_M25_DEPTH, z), INSERT_M25_D))
            for s in SPINE_VISOR_SCREW:
                zz = NOSE_Z0 + s; yy = y_ridge + brow_dy(s)
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
        # shell -> feet: fore-aft SLOTS (+-FOOT_SLOT_HALF) with slotted counterbores through the bottom wall, under the M4 bolts
        def yslot(x, z, y0, y1, d, half):
            return [g.box(x - d / 2, min(y0, y1), z - half, x + d / 2, max(y0, y1), z + half),
                    g.cyl((x, y0, z - half), (x, y1, z - half), d), g.cyl((x, y0, z + half), (x, y1, z + half), d)]
        for h in list(LUGS["L"]) + list(LUGS["R"]):
            bores += yslot(HOLES[h][0], LUG_PAD_SCREW_Z, y_bot_in - 1.0, y_bot_out + 1.0, CLR_M4_SHELL, FOOT_SLOT_HALF)   # M4 from below, heads on the bottom face
        shell = g.unite([shell] + pads)
        shell = g.cut(shell, bores)
        # split into halves at X = 0
        left, right = g.split_x0(shell)
        parts["Shell L"] = g.name(left, "Shell L", COL_BODY)
        parts["Shell R"] = g.name(right, "Shell R", COL_BODY)

    if "spine" in want:
        bar = g.unite([g.prism(band_bar, Z_REAR_OUT, NOSE_Z0), g.sweep_prism(band_bar, brow_stations(0.0, VISOR_L - BEAD_L, VISOR_STATIONS))])
        bar = g.intersect(bar, [g.box(-SPINE_W / 2, -300, -300, SPINE_W / 2, 300, 300)])
        holes = []
        for x in SPINE_RIB_X:
            for z in SPINE_SCREW_Z:
                holes.append(g.cyl((x, y_ridge - BAR_T - 2, z), (x, y_ridge + 1, z), CLR_M25))
                holes.append(g.cyl((x, y_ridge - BAR_T - 2, z), (x, y_ridge - BAR_T + CBORE_M25_H, z), CBORE_M25_D))
            for s in SPINE_VISOR_SCREW:
                zz = NOSE_Z0 + s; yy = y_ridge + brow_dy(s)
                holes.append(g.cyl((x, yy - BAR_T - 2, zz), (x, yy + 1, zz), CLR_M25))
                holes.append(g.cyl((x, yy - BAR_T - 2, zz), (x, yy - BAR_T + CBORE_M25_H, zz), CBORE_M25_D))
        parts["Spine bar"] = g.name(g.cut(bar, holes), "Spine bar", COL_ACCENT)

    if "keel" in want:
        yb = y_bot_out
        keel = g.unite([g.box(-KEEL_W / 2, KEEL_Y0, Z_REAR_OUT - BAR_T, KEEL_W / 2, yb + BAR_T, Z_REAR_OUT),
                        g.box(-KEEL_W / 2, yb, Z_REAR_OUT - BAR_T, KEEL_W / 2, yb + BAR_T, KEEL_Z_END)])
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

    if "feet" in want:
        parts.update(build_feet(g))

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
    def loft_regions(self, regA, zA, regB, zB, n=240):
        """Ruled loft between two different rings (resampled to n matched points)."""
        cq = self.cq
        wires = [cq.Wire.makePolygon([cq.Vector(float(p[0]), float(p[1]), z) for p in pts] + [cq.Vector(float(pts[0][0]), float(pts[0][1]), z)])
                 for pts, z in ((resample_ring(regA.poly, n), zA), (resample_ring(regB.poly, n), zB))]
        return cq.Solid.makeLoft(wires, ruled=True)
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
    def place(self, body, origin, e1, e2, e3):
        cq = self.cq
        # re-orthonormalise (the frame is built from unit vectors but float noise trips gp_Trsf), then use a gp_Trsf directly
        from OCP.gp import gp_Trsf, gp_Ax3, gp_Pnt, gp_Dir
        from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
        e3 = unit(e3); e1 = unit(np.asarray(e1, float) - np.dot(e1, e3) * e3)
        ax = gp_Ax3(gp_Pnt(*map(float, origin)), gp_Dir(*map(float, e3)), gp_Dir(*map(float, e1)))
        tr = gp_Trsf(); tr.SetTransformation(ax, gp_Ax3())   # local (ax) -> world (verified numerically)
        return cq.Solid(BRepBuilderAPI_Transform(body.wrapped, tr, True).Shape())
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
    def loft_regions(self, regA, zA, regB, zB):
        skA, skB = self._sketch(regA, zA), self._sketch(regB, zB); lf = self.uid("lf"); v = self.var("b")
        self.w(f"opLoft(context, {lf}, {{ \"profileSubqueries\" : [qSketchRegion({skA}), qSketchRegion({skB})] }});")
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
        if not tools: return target          # an empty tool list is a no-op (qUnion([]) would be CANNOT_RESOLVE_ENTITIES)
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
    def place(self, body, origin, e1, e2, e3):
        # coordSystem() demands exactly perpendicular axes: re-orthogonalise the rounded x axis against z inside FS
        z, x = self.var("az"), self.var("ax")
        self.w(f"const {z} = normalize(vector({e3[0]:.6f}, {e3[1]:.6f}, {e3[2]:.6f}));")
        self.w(f"const {x} = normalize(vector({e1[0]:.6f}, {e1[1]:.6f}, {e1[2]:.6f}) - dot(vector({e1[0]:.6f}, {e1[1]:.6f}, {e1[2]:.6f}), {z}) * {z});")
        self.w(f"opTransform(context, {self.uid('pl')}, {{ \"bodies\" : {body}, \"transform\" : toWorld(coordSystem(vector({origin[0]:.3f}, {origin[1]:.3f}, {origin[2]:.3f}) * millimeter, {x}, {z})) }});"); return body
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
        annotation { "Name" : "Cradle feet" } definition.buildFeet is boolean;
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
    }, { buildShell : true, buildSpine : true, buildKeel : true, buildCoupon : true, buildFeet : true });
'''

def emit_fs(info, plates):
    fs = FS()
    for flag, want in (("buildShell", ("shell",)), ("buildSpine", ("spine",)), ("buildKeel", ("keel",)), ("buildCoupon", ("coupon",)), ("buildFeet", ("feet",))):
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
    g = CQ(); parts = build(g, info, plates, want=("shell", "spine", "keel", "coupon", "feet"))
    for t in (-3.0, 3.0): parts.update(build_feet(g, tilt=t, want=("lugs",)))    # angle variants for the bench test
    for label, body in parts.items():
        fn = OUT / (label.lower().replace(" ", "_") + ".stl")
        cq.exporters.export(cq.Workplane(obj=body), str(fn), tolerance=0.05, angularTolerance=0.1)
        bb = body.BoundingBox()
        print(f"  {label:<12} bbox x {bb.xmin:7.1f}..{bb.xmax:6.1f}  y {bb.ymin:6.1f}..{bb.ymax:5.1f}  z {bb.zmin:6.1f}..{bb.zmax:6.1f}  vol {body.Volume()/1000:7.1f} cm3  solids {len(body.Solids())}")
    # fit-test coupons: sections of the real shells that test the scan-dependent features with the cluster in hand
    # (front ring = lips, chin, silhouette; cradle corners = ledge, fin, block, stop pads; ear corners = ear pads + lip)
    FIT = {}
    for side, h in zip(("L", "R"), EARS):      # ear-boss coupons: the boss with the roof above it, cut from the shell (test the nut channel and the tab fit)
        cx, cy, cz, n = HOLES[h]
        FIT[f"ear_coupon_{side}"] = (f"Shell {side}", (cx - 16.0, -300, cz - 18.0, cx + 16.0, cy + 6.0, cz + 6.0))
    for name, (src, bx) in FIT.items():
        piece = parts[src].intersect(g.box(*bx))
        cq.exporters.export(cq.Workplane(obj=piece), str(OUT / f"{name}.stl"), tolerance=0.05, angularTolerance=0.1)
        bb = piece.BoundingBox(); print(f"  {name:<13} x {bb.xmin:7.1f}..{bb.xmax:6.1f}  y {bb.ymin:6.1f}..{bb.ymax:5.1f}  z {bb.zmin:6.1f}..{bb.zmax:6.1f}  {piece.Volume()/1000:5.1f} cm3")
    if not a.no_mesh:
        import trimesh, collections
        v = mesh.vertices
        for label in ("Shell L", "Shell R", "Foot lug L", "Foot lug R"):
            body = parts[label]
            sm = trimesh.load(OUT / (label.lower().replace(" ", "_") + ".stl"))
            sel = v[(v[:, 0] <= 2) if label.endswith("L") else (v[:, 0] >= -2)]
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
