"""Fastener access check: for every screw and bolt, sweep a driver-sized cylinder outward from the head along the fastener
axis and measure the free length before it hits something. Each fastener is tested at the ASSEMBLY STAGE where it is
driven (feet: cluster + feet only; close: + shells and bars; car: + mount, cage tubes, dash) against the parts present at
that stage, and must have at least its required reach. The in-car free length is reported too (service access).
Everything is tested in the scan frame; car-frame parts come in through the inverse of placement_T.
Output: printed table + mechanical/output/fastener_check.md. Run after generate.py and mount.py."""
import sys, math
from pathlib import Path
import numpy as np, trimesh
sys.path.insert(0, str(Path(__file__).parent))
import generate as G
import mount as M

HERE = Path(__file__).parent; OUT = HERE / "output"; REF = HERE.parent / "reference" / "cage_scan"
TOOL_D, TOOL_L, START = 8.0, 150.0, 2.5          # driver body diameter, sweep length, and where the sweep starts above the head
NEED = {"driver": 60.0, "nut": 30.0}              # reach required: a screwdriver bit + handle, or a socket / nut
DENSITY = 3.0                                     # one surface sample per this many mm2

T = np.load(OUT / "placement_T.npy"); Tinv = np.linalg.inv(T)
y_bot_in = G.offset(G.GAP).bounds[3]; y_bot_out = G.offset(G.GAP + G.WALL).bounds[3]
y_ridge = G.offset(G.GAP + G.WALL + G.AIR + G.SKIN).bounds[1]

def points(mesh):
    n = max(int(mesh.area / DENSITY), 1)
    s, _ = trimesh.sample.sample_surface(mesh, n)
    return np.vstack([mesh.vertices, s])

def load(name, path, transform=None):
    m = trimesh.load(path)
    if transform is not None: m.apply_transform(transform)
    return name, points(m)

STAGE = {}   # obstacle name -> first stage at which it is present (0 feet, 1 close, 2 car)
def add(stage, item): STAGE[item[0]] = stage; obstacles.append(item)
obstacles = []
add(0, load("cluster (scan)", HERE.parent / "reference" / "cluster_scan" / "cluster_onshape_reference_mm.stl"))
add(0, load("Foot lug L", OUT / "foot_lug_l.stl")); add(0, load("Foot lug R", OUT / "foot_lug_r.stl"))
add(1, load("Shell L", OUT / "shell_l.stl")); add(1, load("Shell R", OUT / "shell_r.stl"))
add(1, load("Spine bar", OUT / "spine_bar.stl")); add(1, load("Keel bar", OUT / "keel_bar.stl"))
for f in sorted(OUT.glob("mount_*.stl")): add(2, load(f.stem.replace("mount_", "mount "), f, Tinv))
for f in ("cage_primary_tubes_mm.stl", "cage_steering_support_tubes_mm.stl", "dash_surroundings_mm.stl"):
    if (REF / f).exists(): add(2, load(f.replace("_mm.stl", ""), REF / f, Tinv))
STAGE_NAME = {0: "feet (bench)", 1: "close (bench)", 2: "car"}

def fasteners():
    F = []
    # shell -> feet: M4 from below through the bottom wall into nuts captured in the feet
    for h in ("B2", "B3", "B5", "B6"):
        F.append((f"shell->foot M4 @ {h}", (G.HOLES[h][0], y_bot_out, G.LUG_PAD_SCREW_Z), (0, 1, 0), {"Shell L", "Shell R"}, 1, "driver"))
    # cluster -> feet: M4 from the FRONT of each lug plate (head + washer on the plate's front face)
    for h in ("B2", "B3", "B5", "B6"):
        cx, cy, cz, n = G.HOLES[h]; n = G.unit(n); p = np.array([cx, cy, cz]) + n * G.LUG_PLATE_T
        F.append((f"cluster->foot M4 @ {h}", tuple(p), tuple(n), set(), 0, "driver"))
    # cluster -> ear bosses (on the shell): M4 from the FRONT of each ear tab through the lens notch, with the shell closed
    for h in G.EARS:
        cx, cy, cz, n = G.HOLES[h]; n = G.unit(n); p = np.array([cx, cy, cz]) + n * G.EAR_TAB_T
        F.append((f"cluster->ear boss M4 @ {h}", tuple(p), tuple(n), set(), 1, "driver"))
    # spine bar: M2.5 from above through the bar into the roof ribs; brow screws with nuts underneath (driver from above)
    for x in G.SPINE_RIB_X:
        for z in G.SPINE_SCREW_Z:
            F.append((f"spine M2.5 @ x{x:+.0f} z{z:+.0f}", (x, y_ridge - G.BAR_T, z), (0, -1, 0), {"Spine bar"}, 1, "driver"))
        for s in G.SPINE_VISOR_SCREW:
            F.append((f"brow M2.5 @ x{x:+.0f} s{s:.0f}", (x, y_ridge + G.brow_dy(s) - G.BAR_T, G.NOSE_Z0 + s), (0, -1, 0), {"Spine bar"}, 1, "driver"))
    # keel bar: rear leg from behind, bottom leg from below
    for sy in G.KEEL_REAR_SCREWS_Y:
        for sx in (-G.KEEL_SCREW_X, G.KEEL_SCREW_X):
            F.append((f"keel rear M2.5 @ x{sx:+.0f} y{sy:.0f}", (sx, sy, G.Z_REAR_OUT - G.BAR_T), (0, 0, -1), {"Keel bar"}, 1, "driver"))
    for sz in G.KEEL_BOT_SCREWS_Z:
        for sx in (-G.KEEL_SCREW_X, G.KEEL_SCREW_X):
            F.append((f"keel bottom M2.5 @ x{sx:+.0f} z{sz:+.0f}", (sx, y_bot_out + G.BAR_T, sz), (0, 1, 0), {"Keel bar"}, 1, "driver"))
    # pivot pins (M8) and lock pins (M6): head one side of the clevis, nut the other; driver/wrench from both sides
    yb = y_bot_out
    for kx in G.KNUCKLE_X:
        for sgn in (-1, 1):
            off = G.KNUCKLE_W / 2 + 0.3 + M.BLADE_T
            F.append((f"pivot M8 @ x{kx:+.0f} side {'+' if sgn > 0 else '-'}x", (kx + sgn * off, yb + G.KNUCKLE_H - G.KNUCKLE_R, G.KNUCKLE_Z), (sgn, 0, 0), {"mount"}, 2, "nut"))
    for lx in G.LOCK_X:
        for sgn in (-1, 1):
            off = G.LOCK_W / 2 + 0.3 + M.LOCK_BLADE_T
            F.append((f"lock M6 @ x{lx:+.0f} side {'+' if sgn > 0 else '-'}x", (lx + sgn * off, yb + G.LOCK_H - G.LOCK_R, G.LOCK_Z), (sgn, 0, 0), {"mount"}, 2, "nut"))
    return F

def sweep(p, d, excl, max_stage):
    """Free length along the driver axis before the first obstacle present at or before max_stage, and what it is."""
    p = np.asarray(p, float); d = G.unit(d); best = (TOOL_L, None)
    for name, pts in obstacles:
        if STAGE[name] > max_stage or any(name.startswith(e) for e in excl): continue
        rel = pts - p; t = rel @ d
        radial = np.linalg.norm(rel - np.outer(t, d), axis=1)
        m = (t > START) & (t < TOOL_L) & (radial < TOOL_D / 2)
        if m.any() and t[m].min() < best[0]: best = (float(t[m].min()), name)
    return best

# ---- part-to-part interference (this is what the v0.6 clevis-in-the-wall miss needed): sample points of each mount part and
# cage tube tested for containment in the shell solids, and shell points in the cage tubes
def interference():
    shells = [trimesh.load(OUT / f) for f in ("shell_l.stl", "shell_r.stl")]
    out = []
    rng = np.random.default_rng(0)
    def sub(pts, n=4000): return pts if len(pts) <= n else pts[rng.choice(len(pts), n, replace=False)]
    for name, pts in obstacles:
        if not (name.startswith("mount") or name.startswith("cage")): continue
        q = sub(pts, 3000 if name.startswith("mount") else 6000)
        n = sum(int(sh.contains(q).sum()) for sh in shells)
        out.append((f"{name} ({len(q)} pts)", n))
    cage = [trimesh.load(REF / f) for f in ("cage_primary_tubes_mm.stl", "cage_steering_support_tubes_mm.stl") if (REF / f).exists()]
    for sh_name, sh in zip(("Shell L", "Shell R"), shells):
        p = sub(points(sh), 6000); p_car = (T[:3, :3] @ p.T).T + T[:3, 3]
        out.append((f"{sh_name} in cage tubes (6000 pts)", sum(int(c.contains(p_car).sum()) for c in cage)))
    return out

rows = []; n_bad = 0
for name, p, d, excl, stage, tool in fasteners():
    free, hit = sweep(p, d, excl, stage); need = NEED[tool]
    car_free, car_hit = sweep(p, d, excl, 2)
    ok = free >= need; n_bad += not ok
    at_stage = f"{free:.0f} mm free" + (f" ({hit})" if hit else "") + f", needs {need:.0f}"
    in_car = f"{car_free:.0f} mm" + (f" ({car_hit})" if car_hit else "")
    rows.append((name, STAGE_NAME[stage], at_stage, in_car, ok))
    print(f"{'ok ' if ok else 'XX '}{name:<34} {STAGE_NAME[stage]:<14} {at_stage:<48} in car: {in_car}")
lines = ["# Fastener access check", "", f"Driver body {TOOL_D} mm swept from each head along the fastener axis (scan frame). Each fastener is "
         f"tested at the stage where it is driven against the parts present then; 'in car' is the free length with everything fitted "
         f"(service access). Reach needed: {NEED['driver']:.0f} mm for a screwdriver, {NEED['nut']:.0f} mm for a socket or nut. "
         f"{len(rows)} fasteners, {n_bad} short of reach.", "", "| Fastener | Driven at | Free at that stage | In car | OK |", "|---|---|---|---|---|"]
lines += [f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {'yes' if r[4] else 'NO'} |" for r in rows]
inter = interference(); n_int = sum(1 for _, n in inter if n)
lines += ["", "## Part interference (sample points of one part inside another)", "", "| Part | Points inside the shells / cage |", "|---|---|"]
lines += [f"| {nm} | {n} |" for nm, n in inter]
print("\ninterference:"); [print(f"  {'XX ' if n else 'ok '}{nm:<40} {n}") for nm, n in inter]
(OUT / "fastener_check.md").write_text("\n".join(lines) + "\n")
print(f"\n{len(rows)} fasteners, {n_bad} short of reach; {n_int} part interferences -> output/fastener_check.md")
