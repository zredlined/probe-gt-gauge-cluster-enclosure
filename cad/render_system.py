"""Full-system renders: cage tubes, dash surroundings, enclosure + cluster scan placed by placement_T, mount parts."""
import json, numpy as np, pyvista as pv
from pathlib import Path
pv.OFF_SCREEN = True
HERE = Path(__file__).parent; OUT = HERE / "output"; R = HERE.parent / "renders"; REF = HERE.parent / "reference" / "cage_scan"
T = np.load(OUT / "placement_T.npy")
def place(m): return m.transform(T, inplace=False)
CH, PU, GOLD, GREY, BEIGE = "#2f3136", "#6f3fbf", "#b08d3a", "#9a9a96", "#b8b0a0"
encl = [(place(pv.read(str(OUT / f"{p}.stl"))), CH if "shell" in p else PU, 1.0) for p in ("shell_l", "shell_r", "spine_bar", "keel_bar")]
cluster = (place(pv.read(str(HERE.parent / "reference" / "cluster_scan" / "cluster_onshape_reference_mm.stl"))), BEIGE, 1.0)
mount = [(pv.read(str(f)), PU if "arm_clamp_upper" in f.name else CH, 1.0) for f in sorted(OUT.glob("mount_*.stl"))]
cage = (pv.read(str(REF / "cage_primary_tubes_mm.stl")), GOLD, 1.0)
sur = (pv.read(str(REF / "dash_surroundings_mm.stl")), GREY, 0.35)
def shot(meshes, fn, pos, focus, up=(0, 0, 1), zoom=1.0, size=(1600, 1000)):
    pl = pv.Plotter(off_screen=True, window_size=size); pl.set_background("#eceae5")
    for m, c, op in meshes: pl.add_mesh(m, color=c, opacity=op, smooth_shading=False, specular=0.2)
    pl.camera_position = [tuple(pos), tuple(focus), up]; pl.camera.zoom(zoom)
    pl.add_light(pv.Light(position=(600, -1200, 1200), intensity=0.7)); pl.add_light(pv.Light(position=(-800, 400, 800), intensity=0.4))
    pl.screenshot(str(fn)); pl.close()
f = (266, -40, 150)
shot([cage, sur] + encl + [cluster] + mount, R / "system_driver.png", (-500, -1300, 800), f, zoom=1.3)
shot([cage] + encl + [cluster] + mount, R / "system_mount.png", (-300, -500, 250), (120, -20, 90), zoom=2.2)
print("system renders done")
