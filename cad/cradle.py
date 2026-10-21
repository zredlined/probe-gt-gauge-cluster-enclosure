"""Low-profile cradle: the cluster sits on the dash crossbar, no shell.

Each foot is an L-bracket: the proven slab bolted through the OEM lug holes (B2 B3 / B5 B6), a thin bar running forward
under the lug plate and the bezel chin, and a clamp saddle (the upper half of the mount's split clamp) sitting on the bar
CR_BAR_BEHIND_FACE mm behind the gauge face. The printed `bar_clamp_lower_*` halves and M6 x 40s close the clamp.
Face leans back CR_PITCH deg. Built in the scan frame; the saddle is built in the car frame and transformed in.
Outputs: cad/output/saddle_foot_{l,r}.stl, placement_cradle_T.npy, placement_cradle.json, checks on stdout."""
import sys, math, json
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
import generate as G
import mount as M

HERE = Path(__file__).parent; OUT = HERE / "output"; REF = HERE.parent / "reference" / "cage_scan"
CR_PITCH = 24.0                 # face lean-back (hedge between 20 and 28 until the glass is measured)
CR_BAR_BEHIND_FACE = 45.0       # bar axis this far behind the gauge face: face stays ~20 mm in front of the bar axis
CR_OVERLAP = 1.0                # saddle ring top buried this far into the forward bar (solid union)
ARM_Y0, ARM_Y1, ARM_T = 92.5, 98.0, 5.5    # forward bar: scan y range (just under the lug plate bottom at 92 / 90.5), thickness
ARM_Z0 = G.LUG_PAD_Z[1]         # starts where the pad ends (behind the plate) ...
SADDLE_W = M.CLAMP_W            # must match the printed lower halves
# windshield ASSUMPTION (replace with a measurement): the v0.7 shell's top-rear corner touched the glass in the car, so the
# glass passes through that corner (computed from the v0.7 placement) and rises WS_ANGLE deg from horizontal toward the cowl.
WS_ANGLE = 25.0

Z_SADDLE = G.Z_FRONT - CR_BAR_BEHIND_FACE        # scan z of the bar axis (19)
ARM_Z1 = Z_SADDLE + SADDLE_W / 2                 # forward bar ends flush with the saddle's width
# backplate: follows the front silhouette inset PL_INSET (hidden behind the bezel), PL_T thick, front face PL_Z1 behind the
# rear housings; two halves lapped at x = 0; perimeter rib; two ribbon ports; ear ties straight back from the proven ear
# blocks; a flange under each saddle foot's pad using the pad's two M4 nut slots.
PL_INSET, PL_T, PL_Z1 = 2.0, 4.0, G.Z_REAR_IN           # plate front face at scan z -61 (rearmost housing -55.8)
PL_Z0 = PL_Z1 - PL_T
PL_LAP = 8.0                                             # no rear rib: the plate prints flat on its rear face with the ties standing up
EAR_BAR_Y0, EAR_BAR_Y1 = -41.0, -31.0                   # ear tie: 10 mm tall, bottom 2 mm above the housing top behind the ears
EAR_BAR_HALF_W = G.EAR_BLOCK_HALF_W
BOSS_Y0, BOSS_Y1, BOSS_Z1 = 86.0, 96.0, G.LUG_PAD_Z[0] - 0.3   # plate boss from the plate forward to 0.3 off the pad's rear face
PAD_NUT_Y = 91.0; PAD_NUT_DEPTH = 3.6                           # M4 nut pockets (axis z) in the pad's rear face; M4 x 30 from behind the plate
DRIVER_GROOVE_D = 9.5                                           # clearance along each lug-bolt axis through the foot's bar (driver from the front)
# louvres: vertical slots on an 8 mm pitch whose tops follow the arch (outline + VENT_TOP_INSET), bottoms at VENT_Y1; the band
# around the centre spine and the logo panel (and its mirror) stay solid
VENT_X_PL = (-150.0, 150.0, 8.0); VENT_W_PL = 2.6; VENT_TOP_INSET = 24.0; VENT_Y1 = 44.0; VENT_X_CLEAR = 22.0; LOGO_PANEL_Y = -14.0
SPINE_W, SPINE_T, SPINE_CBORE_D, SPINE_CBORE_H = 30.0, 3.0, 8.0, 2.5    # purple centre spine over the lap, carries the two lap screws
LAP_Y = (-45.0, 45.0); LAP_BOSS = 4.0                                 # lap screws; L carries a nut-pocket boss on its front face (30 mm of room there)
NUT_M6_AF, NUT_M6_POCKET = 10.3, 6.5                                  # M6 nyloc captured in the saddle flange tops: bolt from below, no tool on top
WIN_XC = (48.0, 83.0, 118.0); WIN_W, WIN_Y0, WIN_Y1, WIN_SLANT = 20.0, -6.0, 40.0, 18.0   # slanted windows at the logo's italic angle
SHOULDER_R = 16.0; GUSSET_T = 3.0
FIN_Y_TOP, FIN_Y_BOT_PLATE, FIN_Z_TAPER_END = -41.0, -20.0, -24.0     # ear fin: top edge, root depth at the plate, where the taper reaches the 10 mm bar (housing top is at y -29 from z -15 forward)
# 4OGS logo: 1.2 mm recess in the rear face of Backplate R with a matching inlay part (print both as one multi-colour object)
LOGO_SVG = HERE.parent / "reference" / "4ogs_logo_3in.svg"; LOGO_W, LOGO_CX, LOGO_CY, LOGO_DEPTH = 70.0, 58.0, -38.0, 1.2

def placement():
    """scan -> car: the forward bar's bottom face over the bar axis sits CR_OVERLAP into the saddle ring top."""
    R0 = np.array([[-1, 0, 0], [0, 0, -1], [0, -1, 0]], float); A = M.rot_x(-CR_PITCH) @ R0
    t = np.array([M.X_C, 0.0, M.CLAMP_RO - CR_OVERLAP]) - A @ np.array([0.0, ARM_Y1, Z_SADDLE])
    T = np.eye(4); T[:3, :3] = A; T[:3, 3] = t; return T

def build(g, T):
    Tinv = np.linalg.inv(T); R, t = Tinv[:3, :3], Tinv[:3, 3]
    feet = G.build_feet(g, pad_nuts=False); parts = {}
    for side, ids in G.LUGS.items():
        xs = sorted(G.HOLES[i][0] for i in ids); x_scan = (xs[0] + xs[1]) / 2
        x0, x1 = xs[0] - G.LUG_PAD_X_MARGIN, xs[1] + G.LUG_PAD_X_MARGIN
        arm = g.box(x0, ARM_Y0, ARM_Z0 - 1.0, x1, ARM_Y1, ARM_Z1)                      # forward bar, overlaps the pad by 1
        x_car = (T[:3, :3] @ np.array([x_scan, 0.0, 0.0]))[0] + T[0, 3]
        upper, lower = M.split_clamp(g, (x_car, 0.0, 0.0), (1, 0, 0), SADDLE_W, split_normal_local=(0, 0, 1), bolt_dir_local=(0, 0, 1), flange_dir_local=(1, 0, 0))
        g.delete_body(lower)                                                            # the printed lowers already exist
        z_top = M.FLANGE_T / 2 + 4.0
        upper = g.cut(upper, [g.hexprism(x_car, sy * M.FLANGE_Y, z_top - NUT_M6_POCKET, z_top + 1.0, NUT_M6_AF) for sy in (-1, 1)])   # captured M6 nylocs
        saddle = g.place(upper, t, R[:, 0], R[:, 1], R[:, 2])                           # car -> scan
        # fill the wedge between the flat bar and the round ring: a block from the bar down past the ring top, then re-cut the
        # bore and trim everything below the clamp's split plane so the printed lower half still mates
        axis_scan = R @ np.array([x_car, 0.0, 0.0]) + t                                  # bar axis point in scan coords (axis runs along x)
        fill = g.box(x0, ARM_Y0, Z_SADDLE - SADDLE_W / 2, x1, axis_scan[1] + 2.0, Z_SADDLE + SADDLE_W / 2)
        foot = g.unite([feet[f"Foot lug {side}"], arm, fill, saddle])
        foot = g.cut(foot, [g.cyl((x0 - 1.0, axis_scan[1], axis_scan[2]), (x1 + 1.0, axis_scan[1], axis_scan[2]), 2 * M.CLAMP_BORE)])
        below_split = g.place(g.box(x_car - 200.0, -200.0, -400.0, x_car + 200.0, 200.0, M.CLAMP_GAP / 2), t, R[:, 0], R[:, 1], R[:, 2])
        foot = g.cut(foot, [below_split])
        # rear-face nut pockets for the backplate bolts (axis z), and driver clearance grooves along the lug-bolt axes
        foot = g.cut(foot, [g.hexprism(x, PAD_NUT_Y, G.LUG_PAD_Z[0] - 1.0, G.LUG_PAD_Z[0] + PAD_NUT_DEPTH, G.NUT_M4_AF) for x in xs] +
                           [g.cyl((x, PAD_NUT_Y, G.LUG_PAD_Z[0] - 1.0), (x, PAD_NUT_Y, G.LUG_PAD_Z[0] + 12.0), G.BOLT_M4_CLR) for x in xs])
        for h in ids:
            cx, cy, cz, n = G.HOLES[h]; n = G.unit(n); c = np.array([cx, cy, cz])
            foot = g.cut(foot, [g.cyl(tuple(c + n * (G.LUG_PLATE_T + 1.0)), tuple(c + n * 70.0), DRIVER_GROOVE_D)])
        parts[f"Saddle foot {side}"] = g.name(foot, f"Saddle foot {side}", G.COL_ACCENT)
    return parts

def logo_shape():
    """The 4OGS logo as shapely polygons (with holes) in scan XY on the plate's rear face. Read from the car's front, i.e.
    looking at the rear face, scan +x is on the viewer's right, so SVG x maps straight onto scan x (no mirror)."""
    from svgelements import SVG, Path as SPath, Shape
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    svg = SVG.parse(str(LOGO_SVG)); polys = []
    for el in svg.elements():
        if not isinstance(el, Shape) or isinstance(el, SVG): continue
        try: path = el if isinstance(el, SPath) else SPath(el)
        except Exception: continue
        rings = []
        for sub in path.as_subpaths():
            sp = SPath(sub)
            if not len(sp): continue
            pts = [(q.x, q.y) for seg in sp for q in (seg.point(t) for t in np.linspace(0, 1, 12))]
            if len(pts) >= 3:
                poly = Polygon(pts).buffer(0)
                if poly.area > 0.5: rings.append(poly)
        if not rings: continue
        rings.sort(key=lambda r: -r.area); outer = rings[0]; shape = outer
        for r in rings[1:]:
            shape = shape.difference(r) if outer.contains(r.representative_point()) else shape.union(r)
        polys.append(shape)
    logo = unary_union(polys); b = logo.bounds; sc = LOGO_W / (b[2] - b[0]); mx, my = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    from shapely.affinity import affine_transform
    return affine_transform(logo, [sc, 0, 0, sc, LOGO_CX - mx * sc, LOGO_CY - my * sc])

def _cq_prism_poly(self, poly, z0, z1):
    """Extrude a shapely (Multi)Polygon WITH holes (the generator's prism() ignores holes)."""
    cq = self.cq; solids = []
    for pg in (poly.geoms if hasattr(poly, "geoms") else [poly]):
        def wire(coords): 
            pts = [cq.Vector(float(x), float(y), z0) for x, y in list(coords)[:-1]]; return cq.Wire.makePolygon(pts + pts[:1])
        face = cq.Face.makeFromWires(wire(pg.exterior.coords), [wire(r.coords) for r in pg.interiors])
        solids.append(cq.Solid.extrudeLinear(face, cq.Vector(0, 0, z1 - z0)))
    return self.unite(solids)
G.CQ.prism_poly = _cq_prism_poly

def build_plate(g):
    """Backplate halves L (x <= 0) and R, scan frame."""
    from shapely.geometry import Polygon
    from shapely.ops import nearest_points
    outline = G.Region(G.offset(-PL_INSET))
    plate = g.prism(outline, PL_Z0, PL_Z1)
    # ribbon ports (same as the shell's) and vents
    def rrect(x0, y0, x1, y1, r):
        z0, z1 = PL_Z0 - 1.0, PL_Z1 + 1.0
        return g.unite([g.box(x0 + r, y0, z0, x1 - r, y1, z1), g.box(x0, y0 + r, z0, x1, y1 - r, z1)] +
                       [g.cyl((cx, cy, z0), (cx, cy, z1), 2 * r) for cx in (x0 + r, x1 - r) for cy in (y0 + r, y1 - r)])
    y0, y1 = G.RIBBON_PORT_Y
    plate = g.cut(plate, [rrect(-400.0, y0, G.RIBBON_PORT_XIN[0], y1, 12.0), rrect(G.RIBBON_PORT_XIN[1], y0, 400.0, y1, 12.0)])
    from shapely.geometry import Polygon as _Poly
    sh = (WIN_Y1 - WIN_Y0) * math.tan(math.radians(WIN_SLANT))          # top edge shifted +x (the 4OGS frame leans the same way)
    wins = []
    for xc in WIN_XC:
        for sgn in (-1, 1):
            x = sgn * xc
            wins.append(g.prism(G.Region(_Poly([(x - WIN_W / 2, WIN_Y1), (x + WIN_W / 2, WIN_Y1), (x + WIN_W / 2 + sh, WIN_Y0), (x - WIN_W / 2 + sh, WIN_Y0)])), PL_Z0 - 1.0, PL_Z1 + 1.0))
    plate = g.cut(plate, wins)
    # ear ties: proven ear block at the tab + a 20 x 10 bar straight back to the plate, plus a corner bump on the plate to meet it
    for h in G.EARS:
        cx, cy, cz, n = G.HOLES[h]; sgn_in = -1.0 if cx > 0 else 1.0
        o, e1, e2, e3 = G.tab_frame(h, (sgn_in, 0.0)); xin = 1.0 if np.dot(e1, [sgn_in, 0.0, 0.0]) > 0 else -1.0
        z0, z1 = G.FOOT_STANDOFF, G.FOOT_STANDOFF + G.EAR_BLOCK_T
        blk = g.box(-G.EAR_BLOCK_HALF_W, -G.EAR_BLOCK_DOWN, z0, G.EAR_BLOCK_HALF_W, G.EAR_BLOCK_UP, z1)
        zc0 = z1 - G.EAR_NUT_REAR_WALL - G.NUT_M4_SLOT_T
        x_end, x_mouth = -xin * (G.NUT_M4_AC / 2 + 0.1), xin * (G.EAR_BLOCK_HALF_W + 1.0)
        chan = g.prism(G.Region(Polygon([(x_end, -G.NUT_M4_SLOT_W / 2), (x_end, G.NUT_M4_SLOT_W / 2), (x_mouth, G.EAR_CHAN_MOUTH_W / 2), (x_mouth, -G.EAR_CHAN_MOUTH_W / 2)])), zc0, zc0 + G.NUT_M4_SLOT_T)
        blk = g.cut(blk, [g.cyl((0.0, 0.0, z0 - 2.0), (0.0, 0.0, z1 + 2.0), G.EAR_BOLT_CLR), chan])
        blk = g.place(blk, o, e1, e2, e3)
        # tapered fin: a tall section where it leaves the plate, lofted to the block's 10 mm section behind the ear
        from shapely.geometry import box as sbox
        sec_plate = G.Region(sbox(cx - EAR_BAR_HALF_W, FIN_Y_TOP, cx + EAR_BAR_HALF_W, FIN_Y_BOT_PLATE))
        sec_ear = G.Region(sbox(cx - EAR_BAR_HALF_W, FIN_Y_TOP, cx + EAR_BAR_HALF_W, EAR_BAR_Y1))
        fin = g.loft_regions(sec_plate, PL_Z0 + 0.5, sec_ear, FIN_Z_TAPER_END)                                     # taper over the first 36 mm
        bar = g.box(cx - EAR_BAR_HALF_W, FIN_Y_TOP, FIN_Z_TAPER_END - 0.5, cx + EAR_BAR_HALF_W, EAR_BAR_Y1, cz - 6.0)   # then the 10 mm bar to the block
        root = g.box(cx - EAR_BAR_HALF_W, FIN_Y_TOP, PL_Z0, cx + EAR_BAR_HALF_W, FIN_Y_BOT_PLATE, PL_Z1)          # fin root through the plate thickness
        shoulder = g.unite([g.cyl((cx, FIN_Y_TOP + SHOULDER_R, PL_Z0), (cx, FIN_Y_TOP + SHOULDER_R, PL_Z1), 2 * SHOULDER_R),
                            g.box(cx - SHOULDER_R, FIN_Y_TOP + SHOULDER_R, PL_Z0, cx + SHOULDER_R, FIN_Y_BOT_PLATE + 12.0, PL_Z1)])   # rounded hump the edge flows into
        plate = g.unite([plate, shoulder, root, fin, bar, blk])
    # foot bosses: from the plate forward to each pad's rear face; two M4 x 30 from behind the plate into nut pockets in the pad
    for side, ids in G.LUGS.items():
        xs = sorted(G.HOLES[i][0] for i in ids); x0, x1 = xs[0] - G.LUG_PAD_X_MARGIN, xs[1] + G.LUG_PAD_X_MARGIN
        plate = g.unite([plate, g.box(x0, BOSS_Y0, PL_Z0 + 0.5, x1, BOSS_Y1, BOSS_Z1)])
        plate = g.cut(plate, [g.cyl((x, PAD_NUT_Y, PL_Z0 - 1.0), (x, PAD_NUT_Y, BOSS_Z1 + 1.0), G.BOLT_M4_CLR) for x in xs])
    # split into lapped halves: L keeps the front half of the plate thickness in the lap, R the rear half; two M4 through the lap
    lap_cut_L = g.box(0.0, -300, PL_Z0 - 1, PL_LAP, 300, PL_Z0 + PL_T / 2)      # L loses the rear half-thickness in the lap
    lap_cut_R = g.box(0.0, -300, PL_Z0 + PL_T / 2, PL_LAP, 300, PL_Z1 + 1)                 # R loses the front half-thickness in the lap
    L = g.intersect(g.copy_body(plate), [g.box(-400, -300, -300, PL_LAP, 300, 300)]); L = g.cut(L, [lap_cut_L])
    R = g.intersect(plate, [g.box(0.0, -300, -300, 400, 300, 300)]); R = g.cut(R, [lap_cut_R])
    L = g.unite([L] + [g.box(-4.0, yy - 6.5, PL_Z1 - 0.3, PL_LAP, yy + 6.5, PL_Z1 + LAP_BOSS) for yy in LAP_Y])        # nut bosses on L's front face
    L = g.cut(L, [g.hexprism(PL_LAP / 2, yy, PL_Z1 + LAP_BOSS - G.NUT_M4_SLOT_T, PL_Z1 + LAP_BOSS + 1.0, G.NUT_M4_AF) for yy in LAP_Y])
    def lap_holes(): return [g.cyl((PL_LAP / 2, yy, PL_Z0 - 1), (PL_LAP / 2, yy, PL_Z1 + LAP_BOSS + 1), G.CLR_M4_SHELL) for yy in LAP_Y]
    L = g.cut(L, lap_holes()); R = g.cut(R, lap_holes())          # fresh tool bodies per cut (FeatureScript consumes tools)
    spine = g.intersect(g.box(-SPINE_W / 2, -300, PL_Z0 - SPINE_T, SPINE_W / 2, 300, PL_Z0), [g.prism(G.Region(G.offset(-PL_INSET)), PL_Z0 - SPINE_T - 1, PL_Z0 + 1)])
    spine = g.cut(spine, [g.cyl((PL_LAP / 2, yy, PL_Z0 - SPINE_T - 1), (PL_LAP / 2, yy, PL_Z0 + 1), G.CLR_M4_SHELL) for yy in LAP_Y] +
                         [g.cyl((PL_LAP / 2, yy, PL_Z0 - SPINE_T - 1), (PL_LAP / 2, yy, PL_Z0 - SPINE_T + SPINE_CBORE_H), SPINE_CBORE_D) for yy in LAP_Y])
    out = {"Backplate L": g.name(L, "Backplate L", G.COL_BODY), "Backplate spine": g.name(spine, "Backplate spine", G.COL_ACCENT)}
    if hasattr(g, "prism_poly"):      # CadQuery only: logo recess in R's rear face + the matching inlay
        logo = logo_shape()
        pocket = g.prism_poly(logo, PL_Z0 - 1.0, PL_Z0 + LOGO_DEPTH)
        R = g.cut(R, [pocket])
        out["Logo inlay"] = g.name(g.prism_poly(logo, PL_Z0, PL_Z0 + LOGO_DEPTH), "Logo inlay", G.COL_ACCENT)
    out["Backplate R"] = g.name(R, "Backplate R", G.COL_BODY)
    return out

def checks(T, parts):
    import trimesh, cadquery as cq
    cl = trimesh.load(HERE.parent / "reference" / "cluster_scan" / "cluster_onshape_reference_mm.stl"); V = cl.vertices
    cv = M.apply(T, V); bt = M.BAR_R
    bezel = cv[(V[:, 2] > 30) & (V[:, 1] < -70)]
    print(f"cluster: bezel top {bezel[:, 2].max() - bt:.0f} mm above the bar top (ear tips {cv[:, 2].max() - bt:.0f}); face front at car y {cv[:, 1].min():.0f} (bar axis 0, bar surface -{bt:.0f})")
    rear_top = cv[np.argmax(cv[:, 1] * 0.5 + cv[:, 2])]
    print(f"top-rear corner at car y {rear_top[1]:.0f} (behind the axis), z {rear_top[2] - bt:.0f} above the bar top; lowest point {cv[:, 2].min() - bt:.0f} above the bar top")
    # windshield assumption: plane through the v0.7 shell's top-rear corner (where it touched the glass), WS_ANGLE from horizontal
    Tn = np.load(OUT / "placement_T.npy"); sh = trimesh.load(OUT / "shell_l.stl"); sv = M.apply(Tn, sh.vertices)
    corner = sv[np.argmax(sv[:, 1] + sv[:, 2])]
    n = np.array([0.0, math.sin(math.radians(WS_ANGLE)), math.cos(math.radians(WS_ANGLE))])   # glass rises toward the driver (-y); positive = outside the glass
    dist = (cv - corner) @ n                     # > 0 = above/behind the glass
    print(f"windshield ASSUMED through the v0.7 shell's touch point (car y {corner[1]:.0f}, z {corner[2] - bt:.0f} above the bar top), {WS_ANGLE:.0f} deg: " + (f"cluster clears it by {-dist.max():.0f} mm" if dist.max() < 0 else f"cluster crosses it by {dist.max():.0f} mm"))
    tubes = [trimesh.load(REF / f) for f in ("cage_primary_tubes_mm.stl", "cage_steering_support_tubes_mm.stl")]; sur = trimesh.load(REF / "dash_surroundings_mm.stl")
    rng = np.random.default_rng(0); q = cv[rng.choice(len(cv), 6000, replace=False)]
    for nm, m in (("crossbar/cage", tubes[0]), ("steering-support arms", tubes[1]), ("dash surroundings", sur)):
        _, d, _ = trimesh.proximity.closest_point(m, q); i = d.argmin()
        print(f"cluster to {nm:<22} min {d.min():5.1f} mm at car {q[i].round(0).astype(int).tolist()}")
    for label, body in parts.items():
        fn = OUT / (label.lower().replace(" ", "_") + ".stl"); cq.exporters.export(cq.Workplane(obj=body), str(fn), tolerance=0.05, angularTolerance=0.1)
        sm = trimesh.load(fn); p, _ = trimesh.sample.sample_surface(sm, 8000); p_car = M.apply(T, p)
        in_tube = sum(int(tb.contains(p_car).sum()) for tb in tubes)
        near = V[np.linalg.norm(V - sm.centroid, axis=1) < 100]; sel = near[rng.choice(len(near), min(4000, len(near)), replace=False)]
        inside = int(sum(body.isInside(cq.Vector(*v), 0.01) for v in sel))
        _, d, _ = trimesh.proximity.closest_point(sm, sel)
        print(f"{label}: {sm.volume / 1000:.1f} cm3, bbox {np.round(sm.bounds[1] - sm.bounds[0]).astype(int).tolist()} mm, solids {len(body.Solids())}; points in cage tubes {in_tube}; cluster vertices inside {inside}; min cluster distance {d.min():.2f}")

FS_HEADER = '''
annotation { "Feature Type Name" : "Cluster cradle" }
export const clusterCradle = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Saddle feet" } definition.buildFeet is boolean;
        annotation { "Name" : "Backplate" } definition.buildPlate is boolean;
    }
    {
        var step = "start";
        try
        {
'''
FS_FOOTER = '''        }
        catch (e)
        {
            fCuboid(context, id + "errbox", { "corner1" : vector(300, -100, -55) * millimeter, "corner2" : vector(310, -90, -45) * millimeter });
            setProperty(context, { "entities" : qCreatedBy(id + "errbox", EntityType.BODY), "propertyType" : PropertyType.NAME, "value" : "FAILED step " ~ step ~ ": " ~ toString(e) });
        }
    }, { buildFeet : true, buildPlate : true });
'''

def emit_fs(T):
    """Third custom feature for the shared Feature Studio (scan frame, like the enclosure feature)."""
    fs = G.FS()
    fs.w("if (definition.buildFeet)"); fs.w("{"); build(fs, T); fs.w("}")
    fs.w("if (definition.buildPlate)"); fs.w("{"); build_plate(fs); fs.w("}")
    return FS_HEADER + "\n".join(fs.lines) + "\n" + FS_FOOTER

def main():
    T = placement(); np.save(OUT / "placement_cradle_T.npy", T)
    (OUT / "cluster_cradle.fs").write_text(emit_fs(T)); print("FeatureScript -> output/cluster_cradle.fs")
    g = G.CQ(); parts = build(g, T); parts.update(build_plate(g)); checks(T, parts)
    json.dump({"pitch_deg": CR_PITCH, "bar_behind_face_mm": CR_BAR_BEHIND_FACE, "windshield_assumption": {"through_v07_touch_point": True, "angle_deg": WS_ANGLE}, "T": T.tolist()}, open(OUT / "placement_cradle.json", "w"), indent=1)

if __name__ == "__main__":
    main()
