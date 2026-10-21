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
ARM_Z1 = Z_SADDLE + SADDLE_W / 2 + 2.0           # forward bar ends just past the saddle

def placement():
    """scan -> car: the forward bar's bottom face over the bar axis sits CR_OVERLAP into the saddle ring top."""
    R0 = np.array([[-1, 0, 0], [0, 0, -1], [0, -1, 0]], float); A = M.rot_x(-CR_PITCH) @ R0
    t = np.array([M.X_C, 0.0, M.CLAMP_RO - CR_OVERLAP]) - A @ np.array([0.0, ARM_Y1, Z_SADDLE])
    T = np.eye(4); T[:3, :3] = A; T[:3, 3] = t; return T

def build(g, T):
    Tinv = np.linalg.inv(T); R, t = Tinv[:3, :3], Tinv[:3, 3]
    feet = G.build_feet(g); parts = {}
    for side, ids in G.LUGS.items():
        xs = sorted(G.HOLES[i][0] for i in ids); x_scan = (xs[0] + xs[1]) / 2
        x0, x1 = xs[0] - G.LUG_PAD_X_MARGIN, xs[1] + G.LUG_PAD_X_MARGIN
        arm = g.box(x0, ARM_Y0, ARM_Z0 - 1.0, x1, ARM_Y1, ARM_Z1)                      # forward bar, overlaps the pad by 1
        x_car = (T[:3, :3] @ np.array([x_scan, 0.0, 0.0]))[0] + T[0, 3]
        upper, _ = M.split_clamp(g, (x_car, 0.0, 0.0), (1, 0, 0), SADDLE_W, split_normal_local=(0, 0, 1), bolt_dir_local=(0, 0, 1), flange_dir_local=(1, 0, 0))
        saddle = g.place(upper, t, R[:, 0], R[:, 1], R[:, 2])                           # car -> scan
        foot = g.unite([feet[f"Foot lug {side}"], arm, saddle])
        parts[f"Saddle foot {side}"] = g.name(foot, f"Saddle foot {side}", G.COL_ACCENT)
    return parts

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

def main():
    T = placement(); np.save(OUT / "placement_cradle_T.npy", T)
    g = G.CQ(); parts = build(g, T); checks(T, parts)
    json.dump({"pitch_deg": CR_PITCH, "bar_behind_face_mm": CR_BAR_BEHIND_FACE, "windshield_assumption": {"through_v07_touch_point": True, "angle_deg": WS_ANGLE}, "T": T.tolist()}, open(OUT / "placement_cradle.json", "w"), indent=1)

if __name__ == "__main__":
    main()
