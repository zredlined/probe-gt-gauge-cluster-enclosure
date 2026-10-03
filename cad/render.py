"""Render the generated STLs with the scan mesh inside: driver iso, rear iso, front, side, section, exploded. pyvista offscreen."""
import numpy as np, pyvista as pv
from pathlib import Path
pv.OFF_SCREEN = True
HERE = Path(__file__).parent; OUT = HERE / "output"; R = HERE.parent / "renders"; R.mkdir(exist_ok=True)
REF = HERE.parent / "reference" / "cluster_scan"
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
feet = [(pv.read(str(OUT / f"{f}.stl")), "#6f3fbf", 1.0) for f in ("foot_lug_l", "foot_lug_r")]
shot(with_cluster, R / "driver_iso.png", (0.55, -0.45, 1.0), zoom=1.15)
shot(with_cluster, R / "front.png", (0, 0, 1), zoom=1.3)
shot(with_cluster, R / "rear.png", (0, 0, -1), zoom=1.3)
expl = [(parts["shell_l"].translate((-60, 0, 0), inplace=False), COL["shell_l"], 1.0), (parts["shell_r"].translate((60, 0, 0), inplace=False), COL["shell_r"], 1.0),
        (parts["spine_bar"].translate((0, -50, 0), inplace=False), COL["spine_bar"], 1.0), (parts["keel_bar"].translate((0, 50, 0), inplace=False), COL["keel_bar"], 1.0),
        (cluster, CLUSTER, 1.0)] + feet
shot(expl, R / "exploded.png", (0.5, -0.5, 1.0), zoom=0.9, dist=1100)
print("rendered ->", R)
