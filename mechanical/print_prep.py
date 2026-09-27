"""Print-ready STLs: every part re-oriented with its bed face on z = 0 and moved to the origin, plus a plate plan with
footprints, heights and ASA mass estimates. Output: mechanical/output/print/*.stl and print_plan.md."""
import sys, math, json
from pathlib import Path
import numpy as np, trimesh
sys.path.insert(0, str(Path(__file__).parent))
import mount as M

HERE = Path(__file__).parent; OUT = HERE / "output"; P = OUT / "print"; P.mkdir(exist_ok=True)
BED = 256.0; ASA_G_PER_CM3 = 1.07

def rot_to(v, target):
    """Rotation matrix taking unit vector v onto unit vector target."""
    v = np.asarray(v, float) / np.linalg.norm(v); t = np.asarray(target, float) / np.linalg.norm(target)
    c = np.dot(v, t)
    if c > 1 - 1e-9: return np.eye(3)
    if c < -1 + 1e-9:
        a = np.array([1, 0, 0]) if abs(v[0]) < 0.9 else np.array([0, 1, 0]); a = np.cross(v, a); a /= np.linalg.norm(a)
        K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]]); return np.eye(3) + 2 * K @ K
    a = np.cross(v, t); s = np.linalg.norm(a); a /= s
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]]); return np.eye(3) + s * K + (1 - c) * K @ K

def prep(src, dst, down, note, plate, spin_z=0.0):
    """down = direction (in the source frame) that should point at the bed."""
    m = trimesh.load(OUT / src)
    R = rot_to(down, [0, 0, -1])
    if spin_z:
        c, s = math.cos(math.radians(spin_z)), math.sin(math.radians(spin_z)); R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]) @ R
    T = np.eye(4); T[:3, :3] = R; m.apply_transform(T)
    m.apply_translation(-m.bounds[0])
    m.export(P / dst)
    ext = m.bounds[1] - m.bounds[0]; vol = abs(m.volume) / 1000.0 if m.is_volume else float("nan")
    fits = ext[0] <= BED and ext[1] <= BED and ext[2] <= BED
    return dict(file=dst, x=round(ext[0], 1), y=round(ext[1], 1), z=round(ext[2], 1), cm3=round(vol, 1), g=round(vol * ASA_G_PER_CM3), fits=fits, note=note, plate=plate)

def arm_split_normal(name):
    _, d = M.arm_axis(name)
    for rot in M.align_rotations(d): pass
    # local +Z (split normal, pointing to the upper half) after the alignment rotations
    n = np.array([0, 0, 1.0])
    for axis, deg in M.align_rotations(d):
        a = np.asarray(axis, float) / np.linalg.norm(axis); c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]]); n = (np.eye(3) + s * K + (1 - c) * K @ K) @ n
    return n

rows = []
# enclosure (scan frame: rear wall is -Z, brow is +Z, bottom wall is +Y)
rows.append(prep("shell_l.stl", "print_shell_L.stl", [0, 0, -1], "rear wall on the bed, brow up; supports under top lip, chin, ear webs, knuckles", "A (alone)"))
rows.append(prep("shell_r.stl", "print_shell_R.stl", [0, 0, -1], "same as Shell L", "B (alone)"))
rows.append(prep("spine_bar.stl", "print_spine_bar.stl", [0, 1, 0], "inner (concave) face down; small support under the curled brow end", "C"))
rows.append(prep("keel_bar.stl", "print_keel_bar.stl", [0, 0, -1], "rear leg flat on the bed, bottom leg standing", "C"))
rows.append(prep("test_coupon.stl", "print_test_coupon.stl", [0, 0, -1], "as is", "C"))
# mount (car frame): bar clamps split horizontally at z = 0
for side in ("driver", "center"):
    rows.append(prep(f"mount_bar_clamp_upper_{side}.stl", f"print_bar_clamp_upper_{side}.stl", [0, 0, -1], "split face down, clevis up, no supports", "D"))
    rows.append(prep(f"mount_bar_clamp_lower_{side}.stl", f"print_bar_clamp_lower_{side}.stl", [0, 0, 1], "flipped: split face down", "D"))
    n = arm_split_normal(side)
    rows.append(prep(f"mount_arm_clamp_upper_{side}.stl", f"print_arm_clamp_upper_{side}.stl", -n, "split face down, strut + clevis up (small support under the strut lean)", "D"))
    rows.append(prep(f"mount_arm_clamp_lower_{side}.stl", f"print_arm_clamp_lower_{side}.stl", n, "flipped: split face down", "D"))

lines = ["# Print plan (Bambu P1S, 256 x 256 x 256 mm, ASA)", "", "| Plate | Part | File | Footprint x*y mm | Height mm | ASA g | Fits | Orientation |", "|---|---|---|---|---|---|---|---|"]
for r in rows:
    lines.append(f"| {r['plate']} | {r['file'].replace('print_', '').replace('.stl', '')} | `output/print/{r['file']}` | {r['x']} x {r['y']} | {r['z']} | {r['g']} | {'yes' if r['fits'] else 'NO'} | {r['note']} |")
tot = sum(r['g'] for r in rows if not math.isnan(r['g']))
lines += ["", f"Total ASA about {tot} g (solid volume x 1.07 g/cm3; real usage depends on infill and supports).", "",
          "Plates: A = Shell L alone, B = Shell R alone, C = spine bar + keel bar + coupon, D = all eight clamp halves.",
          "Print order: coupon -> one bar-clamp lower (tube fit) -> plate D -> plate C -> shells."]
(P / "print_plan.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
