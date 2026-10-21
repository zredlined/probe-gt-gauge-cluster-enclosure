"""Side-mount fastener access + part interference, stage-aware (like cradle_check.py). Car frame throughout.
Stages: 0 adapters onto the cluster (bench), 1 plates onto the adapters and clamp uppers onto the plates (bench),
2 the whole assembly onto the bar, reused lowers + M6 from below (car: tubes, dash), 3 everything fitted (service). Each fastener is swept with an 8 mm
driver from its head at the stage it is driven; nut insertions are swept along their channels with the nut's own width.
Interference: sample points of every part inside every other part / the cluster / the tubes / the dash / the ribbon
plug envelopes, and the closest approach of each part to the cluster scan (the real cluster is 2-3 mm deeper at the
rear than the scan, so anything under 4 mm there is flagged)."""
import sys, json
from pathlib import Path
import numpy as np, trimesh
sys.path.insert(0, str(Path(__file__).parent))
import generate as G, mount as M, sidemount as S

HERE = Path(__file__).parent; OUT = HERE / "output"; REF = HERE.parent / "reference" / "cage_scan"
TOOL_D, TOOL_L, START = 8.0, 150.0, 2.5; NEED = {"driver": 60.0, "stubby": 35.0, "nut": 30.0, "socket": 50.0, "slide": 20.0, "drop": 12.0}
T = S.T; R, t = T[:3, :3], T[:3, 3]
info = json.load(open(OUT / "placement_sidemount.json"))
rng = np.random.default_rng(0)
def pts(m, n=6000):
    p, _ = trimesh.sample.sample_surface(m, n); return np.vstack([m.vertices[rng.choice(len(m.vertices), min(3000, len(m.vertices)), replace=False)], p])
def car(m): m.apply_transform(T); return m
PLUGS = {"L": dict(x=(-185.0, -171.2), y=(0.5, 51.5)), "R": dict(x=(159.7, 173.3), y=(-4.0, 56.0))}; PLUG_Z = (-80.0, -35.0)   # body + lock + 25 mm of cable

parts = {"cluster": (0, car(trimesh.load(HERE.parent / "reference" / "cluster_scan" / "cluster_onshape_reference_mm.stl")))}
for side in ("l", "r"):
    parts[f"lower_adapter_{side}"] = (0, trimesh.load(OUT / f"sidemount_lower_adapter_{side}.stl"))
    parts[f"ear_adapter_{side}"] = (0, trimesh.load(OUT / f"sidemount_ear_adapter_{side}.stl"))
    parts[f"side_plate_{side}"] = (1, trimesh.load(OUT / f"sidemount_side_plate_{side}.stl"))
    parts[f"clamp_upper_{side}"] = (2, trimesh.load(OUT / f"sidemount_clamp_upper_{side}.stl"))
    parts[f"clamp_lower_{side}"] = (2, trimesh.load(OUT / f"sidemount_clamp_lower_{side}.stl"))
    pb = PLUGS[side.upper()]; parts[f"plug_{side}"] = (0, car(trimesh.creation.box(bounds=[[pb["x"][0], pb["y"][0], PLUG_Z[0]], [pb["x"][1], pb["y"][1], PLUG_Z[1]]])))
for f, nm in (("cage_primary_tubes_mm.stl", "cage"), ("cage_steering_support_tubes_mm.stl", "arms"), ("dash_surroundings_mm.stl", "dash")):
    parts[nm] = (2, trimesh.load(REF / f))
samples = {k: pts(v[1]) for k, v in parts.items()}

def fasteners():
    F = []   # name, head point (car), outward direction (car), stage, tool, tool diameter
    def sc(p): return R @ np.asarray(p, float) + t
    def sd(d): return R @ np.asarray(d, float)
    for h in ("B2", "B3", "B5", "B6"):
        cx, cy, cz, n = G.HOLES[h]; n = G.unit(n)
        F.append((f"lug M4x16 @ {h} (from the front)", sc(np.array([cx, cy, cz]) + n * G.LUG_PLATE_T), sd(n), 0, "driver", TOOL_D))
        F.append((f"lug nut drop-in @ {h} (from the rear of the block)", sc(np.array([cx, cy, cz]) - n * (G.FOOT_STANDOFF + G.FOOT_T + 30.0)), sd(-n), 0, "drop", G.NUT_M4_AF))
    for h in G.EARS:
        cx, cy, cz, n = G.HOLES[h]; n = G.unit(n); side = "L" if h == "T1" else "R"; s = S.side_geom(side)
        F.append((f"ear M4x20 @ {h} (from the front, lens notch)", sc(np.array([cx, cy, cz]) + n * G.EAR_TAB_T), sd(n), 0, "driver", TOOL_D))
        o, e1, e2, e3 = G.tab_frame(h, (s["out"], 0.0)); zc = G.FOOT_STANDOFF + G.EAR_BLOCK_T - G.EAR_NUT_REAR_WALL - G.NUT_M4_SLOT_T / 2
        mouth = o + e3 * zc + np.array([s["out"], 0, 0]) * (abs(s["x_arm"] - s["x_ear"]) + 0.5)
        F.append((f"ear nut slide-in @ {h} (from outboard, {abs(s['x_arm'] - s['x_ear']) + G.NUT_M4_AC / 2 + 2:.0f} mm needed)", sc(mouth), sd(np.array([-s["out"], 0.0, 0.0])), 0, abs(s["x_arm"] - s["x_ear"]) + G.NUT_M4_AC / 2 + 2.0, G.NUT_M4_SLOT_W))
    for side in ("L", "R"):
        s = S.side_geom(side); nd = info["sides"][side]["nodes"]
        for (y, z) in nd["Lw"]: F.append((f"lower cross M4x40 {side} z{z:+.0f} (from outboard)", sc([s["x_po"], y, z]), sd([s["out"], 0, 0]), 1, "driver", TOOL_D))
        for (y, z) in nd["U"]: F.append((f"upper cross M4x20 {side} z{z:+.0f} (from outboard)", sc([s["x_arm"], y, z]), sd([s["out"], 0, 0]), 1, "driver", TOOL_D))
        ci = info["sides"][side]["clamp"]; inb = 1.0 if side == "R" else -1.0; zf = M.FLANGE_T / 2 + 4.0
        for sy in (-1, 1):
            F.append((f"clamp M6x30 {side} y{sy * M.FLANGE_Y:+.0f} (from below, 10 mm socket)", np.array([ci["x_c"], sy * M.FLANGE_Y, -zf]), np.array([0, 0, -1.0]), 2, "socket", 16.0))
            F.append((f"clamp M6x30 {side} y{sy * M.FLANGE_Y:+.0f} in-car service (10 mm socket)", np.array([ci["x_c"], sy * M.FLANGE_Y, -zf]), np.array([0, 0, -1.0]), 3, "socket", 16.0))
            F.append((f"clamp M6x30 {side} y{sy * M.FLANGE_Y:+.0f} bolt tip above the flange (M6 x 30 ends 8 mm past the nyloc)", np.array([ci["x_c"], sy * M.FLANGE_Y, zf]), np.array([0, 0, 1.0]), 3, 9.0, 6.4))
        for (by, bz) in S.BOSS_YZ:
            F.append((f"plate M5x25 {side} y{by:+.0f} (from outboard, bench: uppers onto the plates)", sc([s["x_po"], 0, 0]) * [1, 0, 0] + [0, by, bz], np.array([-inb, 0, 0.0]), 1, "driver", TOOL_D))
            F.append((f"M5 nut drop-in {side} y{by:+.0f} (from above, bench)", np.array([ci["x_end"] + inb * (S.NUT_M5_X + S.NUT_M5_T / 2), by, bz + 25.0]), np.array([0, 0, 1.0]), 1, "drop", S.NUT_M5_AF))
    return F

def sweep(p, d, stage, excl=(), dia=TOOL_D):
    d = G.unit(d); best = (TOOL_L, None)
    for name, (st, m) in parts.items():
        if st > stage or name in excl: continue
        rel = samples[name] - p; tt = rel @ d; radial = np.linalg.norm(rel - np.outer(tt, d), axis=1)
        msk = (tt > START) & (tt < TOOL_L) & (radial < dia / 2)
        if msk.any() and tt[msk].min() < best[0]: best = (float(tt[msk].min()), name)
    return best

print("== fastener access (free mm along the tool at the stage it is driven; with everything fitted for service)")
bad = 0
for name, p, d, stage, tool, dia in fasteners():
    excl = set()
    if "lug M4" in name or "ear M4" in name: excl |= {"cluster"}
    if "drop-in @" in name: excl |= {"lower_adapter_l", "lower_adapter_r"}
    if "slide-in" in name: excl |= {"ear_adapter_l", "ear_adapter_r"}
    if "M6x30" in name: excl |= {"clamp_lower_l", "clamp_lower_r"}
    if "bolt tip" in name: excl |= {"clamp_upper_l", "clamp_upper_r"}
    if "M5 nut" in name: excl |= {"clamp_upper_l", "clamp_upper_r", "cluster", "lower_adapter_l", "lower_adapter_r", "ear_adapter_l", "ear_adapter_r", "side_plate_l", "side_plate_r", "plug_l", "plug_r"}   # nuts go in before the cluster assembly arrives
    free, hit = sweep(p, d, stage, excl, dia); car_free, car_hit = sweep(p, d, 3, excl, dia); ok = free >= (NEED[tool] if isinstance(tool, str) else tool); bad += not ok
    print(f"  {'ok ' if ok else 'XX '}{name:<58} stage {stage}: {free:4.0f} mm{(' (' + hit + ')') if hit else '':<22}  all fitted: {car_free:4.0f} mm{(' (' + car_hit + ')') if car_hit else ''}")

print("\n== part interference (sample points inside another solid) and closest approach to the cluster scan")
names = [n for n in parts if n not in ("cage", "arms", "dash")]
cl = parts["cluster"][1]
for a in names:
    if a == "cluster" or a.startswith("plug"): continue
    row = []
    for b in list(parts):
        if a == b: continue
        if not parts[b][1].is_watertight: continue
        sd = trimesh.proximity.signed_distance(parts[b][1], samples[a][::2]); n = int((sd > 0.3).sum())   # > 0.3 mm inside: coincident faces do not count
        if n: row.append(f"{b}:{n}")
    inside_cl = int(sum(1 for _ in []))
    _, dcl, _ = trimesh.proximity.closest_point(cl, samples[a][::3]); dmin = float(dcl.min())
    _, dd, _ = trimesh.proximity.closest_point(parts["dash"][1], samples[a][::3]); ddash = float(dd.min())
    flag = "" if (dmin >= 4.0 or "adapter" in a) else "   <-- under 4 mm to the scan (real cluster is 2-3 mm deeper at the rear)"
    print(f"  {a:<16} inside -> {', '.join(row) if row else 'nothing':<40} cluster {dmin:5.1f} mm   dash {ddash:5.1f} mm{flag}")
# cluster vertices inside printed parts (scan noise excluded by requiring > 40 vertices)
for a in names:
    if a == "cluster" or a.startswith("plug") or a.startswith("clamp_lower"): continue
    m = parts[a][1]; lo, hi = m.bounds; v = cl.vertices[((cl.vertices > lo) & (cl.vertices < hi)).all(axis=1)]
    n = int(m.contains(v).sum()) if len(v) else 0
    if n: print(f"  cluster scan vertices inside {a}: {n}")
print("\n== installation paths (first dash-scan vertex within 3 mm laterally along the move, mm)")
from scipy.spatial import cKDTree
D = parts["dash"][1].vertices; tree_xy = cKDTree(D[:, :2]); tree_yz = cKDTree(D[:, 1:])
def path(m, axis, sign, L=80.0):
    p, _ = trimesh.sample.sample_surface(m, 4000); best = L
    tree = tree_xy if axis == 2 else tree_yz; keep = [0, 1] if axis == 2 else [1, 2]
    for q in p:
        idx = tree.query_ball_point(q[keep], 3.0)
        if not idx: continue
        dd = (D[idx, axis] - q[axis]) * sign; dd = dd[(dd > 0.5) & (dd < L)]
        if len(dd) and dd.min() < best: best = float(dd.min())
    return best
asm = trimesh.util.concatenate([parts[n][1] for n in parts if parts[n][0] <= 1 and not n.startswith("plug")] + [parts["clamp_upper_l"][1], parts["clamp_upper_r"][1]])
print(f"  cluster assembly with the uppers, lowered straight down onto the bar: {path(asm, 2, +1):5.1f} mm of clear travel above the final spot (80 = all checked)")
for side in ("l", "r"):
    lo = parts[f"clamp_lower_{side}"][1]
    print(f"  clamp lower {side} straight up from below: {path(lo, 2, -1):5.1f} mm of clear travel below its final spot; slid in along the bar from the driver side: {path(lo, 0, -1, 60.0):5.1f} mm clear (60 = all checked)")
print(f"\n{bad} fasteners short of reach")
