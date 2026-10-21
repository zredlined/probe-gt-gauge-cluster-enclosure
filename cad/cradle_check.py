"""Cradle fastener access + part interference, stage-aware (like fastener_check.py for the enclosure).
Stages: 0 feet (cluster + feet), 1 plate (+ backplate halves, spine, inlay; all bench), 2 car (+ clamp lowers, cage tubes,
dash surroundings). Each fastener is swept with an 8 mm driver from its head at the stage it is driven and must have its
reach; in-car free length is reported for service. Interference: sample points of every cradle part inside every other
part / the cluster / the tubes / the dash, and the cluster inside the cradle parts."""
import sys, math
from pathlib import Path
import numpy as np, trimesh
sys.path.insert(0, str(Path(__file__).parent))
import generate as G, mount as M, cradle as C

HERE = Path(__file__).parent; OUT = HERE / "output"; REF = HERE.parent / "reference" / "cage_scan"
TOOL_D, TOOL_L, START = 8.0, 150.0, 2.5; NEED = {"driver": 60.0, "stubby": 35.0, "nut": 30.0}
T = np.load(OUT / "placement_cradle_T.npy"); Tinv = np.linalg.inv(T)
rng = np.random.default_rng(0)

def pts(m, n=5000):
    p, _ = trimesh.sample.sample_surface(m, n); return np.vstack([m.vertices[rng.choice(len(m.vertices), min(2000, len(m.vertices)), replace=False)], p])
parts = {}   # name -> (stage, trimesh in scan frame)
parts["cluster"] = (0, trimesh.load(HERE.parent / "reference" / "cluster_scan" / "cluster_onshape_reference_mm.stl"))
for nm in ("saddle_foot_l", "saddle_foot_r"): parts[nm] = (0, trimesh.load(OUT / f"{nm}.stl"))
for nm in ("backplate_l", "backplate_r", "backplate_spine", "logo_inlay"): parts[nm] = (1, trimesh.load(OUT / f"{nm}.stl"))
# car-frame things, brought into the scan frame
lowers = []
for side, ids in G.LUGS.items():
    x_scan = sum(G.HOLES[i][0] for i in ids) / 2; x_car = (T[:3, :3] @ np.array([x_scan, 0, 0]))[0] + T[0, 3]
    lo = trimesh.load(OUT / "mount_bar_clamp_lower_driver.stl"); lo.apply_translation([x_car - lo.centroid[0] + (lo.centroid[0] - 107.0) * 0 - (lo.bounds.mean(axis=0)[0] - 107.0), 0, 0])
    lo.apply_translation([x_car - lo.bounds.mean(axis=0)[0], 0, 0]); lo.apply_transform(Tinv); parts[f"clamp_lower_{side}"] = (2, lo)
for f, nm in (("cage_primary_tubes_mm.stl", "cage"), ("cage_steering_support_tubes_mm.stl", "arms"), ("dash_surroundings_mm.stl", "dash")):
    m = trimesh.load(REF / f); m.apply_transform(Tinv); parts[nm] = (2, m)
samples = {k: pts(v[1]) for k, v in parts.items()}

# ---- fasteners (scan frame): name, head point, outward direction (driver side), stage, tool
def fasteners():
    F = []; yb = G.offset(G.GAP).bounds[3] - G.FOOT_WALL_CLR
    for h in ("B2", "B3", "B5", "B6"):
        cx, cy, cz, n = G.HOLES[h]; n = G.unit(n); F.append((f"lug M4x16 @ {h} (front)", np.array([cx, cy, cz]) + n * G.LUG_PLATE_T, n, 0, "driver"))
    for h in G.EARS:
        cx, cy, cz, n = G.HOLES[h]; n = G.unit(n); F.append((f"ear M4x20 @ {h} (front, lens notch)", np.array([cx, cy, cz]) + n * G.EAR_TAB_T, n, 1, "driver"))
    for side, ids in G.LUGS.items():
        for h in ids:
            F.append((f"plate boss M4x30 @ {h} (from the rear)", np.array([G.HOLES[h][0], C.PAD_NUT_Y, C.PL_Z0]), np.array([0, 0, -1.0]), 1, "driver"))
    for yy in C.LAP_Y:
        F.append((f"lap M4x12 @ y{yy:+.0f} (from the rear through the spine)", np.array([C.PL_LAP / 2, yy, C.PL_Z0 - C.SPINE_T]), np.array([0, 0, -1.0]), 1, "driver"))
    zf = M.FLANGE_T / 2 + 4.0
    for side, ids in G.LUGS.items():
        x_scan = sum(G.HOLES[i][0] for i in ids) / 2; x_car = (T[:3, :3] @ np.array([x_scan, 0, 0]))[0] + T[0, 3]
        for sy in (-1, 1):
            p_car = np.array([x_car, sy * M.FLANGE_Y, -zf]); F.append((f"saddle M6x40 {side} y{sy * M.FLANGE_Y:+.0f} (from below)", Tinv[:3, :3] @ p_car + Tinv[:3, 3], Tinv[:3, :3] @ np.array([0, 0, -1.0]), 2, "nut"))
    return F

def sweep(p, d, stage, excl=()):
    d = G.unit(d); best = (TOOL_L, None)
    for name, (st, m) in parts.items():
        if st > stage or name in excl: continue
        rel = samples[name] - p; t = rel @ d; radial = np.linalg.norm(rel - np.outer(t, d), axis=1)
        msk = (t > START) & (t < TOOL_L) & (radial < TOOL_D / 2)
        if msk.any() and t[msk].min() < best[0]: best = (float(t[msk].min()), name)
    return best

print("== fastener access (free mm along the driver at the stage it is driven; in-car free mm for service)")
bad = 0
for name, p, d, stage, tool in fasteners():
    excl = {"cluster"} if "lug" in name or "ear" in name else set()
    excl |= {"backplate_l", "backplate_r"} if "boss" in name else set()
    excl |= {"backplate_spine"} if "lap" in name else set()
    excl |= {f"clamp_lower_{s}" for s in ("L", "R")} if "saddle" in name else set()
    free, hit = sweep(p, d, stage, excl); car_free, car_hit = sweep(p, d, 2, excl); ok = free >= NEED[tool]; bad += not ok
    print(f"  {'ok ' if ok else 'XX '}{name:<48} stage {stage}: {free:4.0f} mm{(' (' + hit + ')') if hit else '':<22}  in car: {car_free:4.0f} mm{(' (' + car_hit + ')') if car_hit else ''}")
print("\n== part interference (sample points inside another solid)")
names = list(parts)
for a in names:
    if parts[a][0] == 2 and a != "cage" and a != "arms": continue
    row = []
    for b in names:
        if a == b: continue
        if a in ("cage", "arms") and parts[b][0] == 2: continue
        n = int(parts[b][1].contains(samples[a]).sum()) if parts[b][1].is_watertight else -1
        if n: row.append(f"{b}:{n}")
    print(f"  {a:<16} inside -> {', '.join(row) if row else 'nothing'}")
print(f"\n{bad} fasteners short of reach")
