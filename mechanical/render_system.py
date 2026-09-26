"""Full-system renders: cage tubes, dash surroundings, enclosure + cluster scan placed by placement_T, mount parts, wheel guess."""
import json, numpy as np, pyvista as pv
from pathlib import Path
pv.OFF_SCREEN = True
HERE = Path(__file__).parent; OUT = HERE / "output"; R = OUT / "renders"; REF = HERE.parent / "dash_cage_reference"
T = np.load(OUT / "placement_T.npy")
def place(m): return m.transform(T, inplace=False)
CH, PU, GOLD, GREY, BEIGE = "#2f3136", "#6f3fbf", "#b08d3a", "#9a9a96", "#b8b0a0"
encl = [(place(pv.read(str(OUT / f"{p}.stl"))), CH if "shell" in p else PU, 1.0) for p in ("shell_l", "shell_r", "spine_bar", "keel_bar")]
cluster = (place(pv.read(str(HERE.parent / "onshape_reference_package" / "cluster_onshape_reference_mm.stl"))), BEIGE, 1.0)
mount = [(pv.read(str(f)), GOLD if "stub" in f.name else (PU if "stay" in f.name else CH), 1.0) for f in sorted(OUT.glob("mount_*.stl"))]
cage = (pv.read(str(REF / "cage_primary_tubes_mm.stl")), GOLD, 1.0)
sur = (pv.read(str(REF / "dash_surroundings_mm.stl")), GREY, 0.35)
# wheel guess: 350 OD torus-ish ring perpendicular to the steering axis, 60 mm toward the driver from the hub point
hub = np.array([266.139, -317.480, 57.955]); ax = np.array([-0.006766, -0.911536, 0.411164]); wc = hub + ax * 60
wheel = (pv.ParametricTorus(ringradius=160, crosssectionradius=15).rotate_x(90, inplace=False), "#404040", 0.6)
# torus default axis is z; align to ax
import pyvista as _pv
w = pv.ParametricTorus(ringradius=160, crosssectionradius=15)
vec = np.cross([0, 0, 1], ax); ang = np.degrees(np.arccos(np.dot([0, 0, 1], ax)))
w = w.rotate_vector(vec, ang, inplace=False).translate(wc, inplace=False); wheel = (w, "#404040", 0.6)
def shot(meshes, fn, pos, focus, up=(0, 0, 1), zoom=1.0, size=(1600, 1000)):
    pl = pv.Plotter(off_screen=True, window_size=size); pl.set_background("#eceae5")
    for m, c, op in meshes: pl.add_mesh(m, color=c, opacity=op, smooth_shading=False, specular=0.2)
    pl.camera_position = [tuple(pos), tuple(focus), up]; pl.camera.zoom(zoom)
    pl.add_light(pv.Light(position=(600, -1200, 1200), intensity=0.7)); pl.add_light(pv.Light(position=(-800, 400, 800), intensity=0.4))
    pl.screenshot(str(fn)); pl.close()
scene = [cage, sur] + encl + [cluster] + mount   # wheel omitted: OD/dish/angle not measured
f = (266, -40, 150)
shot(scene, R / "sys_01_driver_oblique.png", (-500, -1300, 800), f, zoom=1.3)
shot([cage, sur] + encl + [cluster] + mount, R / "sys_02_front_left.png", (-700, -900, 500), (250, 0, 120), zoom=1.4)
shot([cage] + encl + [cluster] + mount, R / "sys_03_side.png", (-1400, -200, 200), (250, -100, 120), zoom=1.5)
shot([cage] + encl + [cluster] + mount, R / "sys_04_mount_closeup.png", (-300, -500, 250), (120, -20, 90), zoom=2.2)
shot([cage] + encl + [cluster] + mount, R / "sys_05_stay_closeup.png", (-350, -300, 220), (45, 0, 100), zoom=3.0)
shot([cage] + encl + [cluster] + mount, R / "sys_06_eye_view.png", (266, -850, 480), (266, 0, 150), zoom=1.1)
shot([cage, sur] + encl + [cluster] + mount, R / "sys_07_top.png", (266, -100, 1500), (266, -100, 0), up=(0, 1, 0), zoom=1.2)
print("system renders done")
