"""Render the generated STLs with the scan mesh inside: driver iso, rear iso, front, side, section, exploded. pyvista offscreen."""
import numpy as np, pyvista as pv
from pathlib import Path
pv.OFF_SCREEN = True
HERE = Path(__file__).parent; OUT = HERE / "output"; R = OUT / "renders"; R.mkdir(exist_ok=True)
REF = HERE.parent / "onshape_reference_package"
COL = {"shell_l": "#2f3136", "shell_r": "#2f3136", "spine_bar": "#6f3fbf", "keel_bar": "#6f3fbf", "test_coupon": "#9a9da3"}
CLUSTER = "#b8b0a0"
parts = {p: pv.read(str(OUT / f"{p}.stl")) for p in COL}
cluster = pv.read(str(REF / "cluster_onshape_reference_mm.stl"))
CENTER = np.array([-4.0, 5.0, 10.0])

def shot(meshes, fn, d, up=(0, -1, 0), zoom=1.0, clip=None, size=(1600, 1000), focus=None, dist=900):
    pl = pv.Plotter(off_screen=True, window_size=size); pl.set_background("#eceae5")
    for m, c, op in meshes:
        mm = m.clip(normal=clip[0], origin=clip[1], invert=False) if clip else m
        if mm.n_points == 0: continue
        pl.add_mesh(mm, color=c, opacity=op, smooth_shading=False, specular=0.2, specular_power=20)
    c = np.array(focus if focus is not None else CENTER, float)
    d = np.array(d, float); d /= np.linalg.norm(d)
    pl.camera_position = [tuple(c + d * dist), tuple(c), up]; pl.camera.zoom(zoom)
    pl.add_light(pv.Light(position=tuple(c + np.array([300, -500, 700])), intensity=0.75))
    pl.add_light(pv.Light(position=tuple(c + np.array([-500, -200, -400])), intensity=0.45))
    pl.add_light(pv.Light(position=tuple(c + np.array([0, 600, 200])), intensity=0.3))
    pl.screenshot(str(fn)); pl.close()

asm = [(parts[p], COL[p], 1.0) for p in ("shell_l", "shell_r", "spine_bar", "keel_bar")]
with_cluster = asm + [(cluster, CLUSTER, 1.0)]
# car-up is -Y: camera "up" vector (0,-1,0). Driver looks along -Z from +Z.
shot(with_cluster, R / "01_driver_iso.png", (0.55, -0.45, 1.0), zoom=1.15)
shot(with_cluster, R / "02_rear_iso.png", (-0.6, -0.4, -1.0), zoom=1.15)
shot(with_cluster, R / "03_front.png", (0, 0, 1), zoom=1.3)
shot(with_cluster, R / "04_rear.png", (0, 0, -1), zoom=1.3)
shot(with_cluster, R / "05_side_right.png", (1, 0, 0.05), zoom=1.3)
shot(with_cluster, R / "06_top.png", (0, -1, 0.05), up=(0, 0, 1), zoom=1.3)
# sections: keep x < -140 (through the left lug cradle) looking from -X... show cut at x=-140 looking from +X side of the cut
shot(with_cluster, R / "07_section_x-140.png", (1, -0.3, 0.4), clip=((-1, 0, 0), (-140, 0, 0)), zoom=1.6, focus=(-150, 30, 0))
shot(with_cluster, R / "08_section_x0.png", (1, -0.3, 0.3), clip=((-1, 0, 0), (-1, 0, 0)), zoom=1.2, focus=(-40, 5, 10))
# section through the top skin / visor at x = -60 looking along +X: shows the air gap and droop
shot(asm, R / "09_section_skin_x-60.png", (1, 0, 0), clip=((-1, 0, 0), (-60, 0, 0)), zoom=2.6, focus=(-60, -70, 30))
# exploded
expl = [(parts["shell_l"].translate((-60, 0, 0), inplace=False), COL["shell_l"], 1.0), (parts["shell_r"].translate((60, 0, 0), inplace=False), COL["shell_r"], 1.0),
        (parts["spine_bar"].translate((0, -50, 0), inplace=False), COL["spine_bar"], 1.0), (parts["keel_bar"].translate((0, 50, 0), inplace=False), COL["keel_bar"], 1.0),
        (cluster, CLUSTER, 1.0)]
shot(expl, R / "10_exploded.png", (0.5, -0.5, 1.0), zoom=0.9, dist=1100)
# interior views from the front (cluster removed / ghosted): lug cradle and ear pad
shot([(parts["shell_l"], COL["shell_l"], 1.0), (cluster, CLUSTER, 0.3)], R / "11_lug_cradle_L.png", (0.5, -0.6, 1.0), zoom=3.0, focus=(-142, 84, -10))
shot([(parts["shell_l"], COL["shell_l"], 1.0)], R / "11b_lug_cradle_L_empty.png", (0.5, -0.6, 1.0), zoom=3.0, focus=(-142, 84, -10))
shot([(parts["shell_l"], COL["shell_l"], 1.0), (cluster, CLUSTER, 0.3)], R / "12_ear_pad_T1.png", (0.6, 0.5, 1.0), zoom=3.5, focus=(-168, -27, 25))
shot([(parts["shell_l"], COL["shell_l"], 1.0)], R / "12b_ear_pad_T1_empty.png", (0.6, 0.5, 1.0), zoom=3.5, focus=(-168, -27, 25))
shot([(parts["test_coupon"], COL["test_coupon"], 1.0)], R / "13_coupon.png", (0.5, -0.6, 1.0), zoom=1.0, focus=(265, 70, -50), dist=200)
print("rendered", len(list(R.glob("*.png"))), "images ->", R)
