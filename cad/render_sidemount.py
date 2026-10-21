"""Side-mount renders (pyvista, car frame): cage tubes, dash surroundings, cluster scan placed by placement_sidemount_T,
the eight printed parts and the reused clamp lowers. -> skeleton-mount/renders/"""
import sys, numpy as np, pyvista as pv
from pathlib import Path
pv.OFF_SCREEN = True
HERE = Path(__file__).parent; OUT = HERE / "output"; R = HERE.parent / "skeleton-mount" / "renders"; REF = HERE.parent / "reference" / "cage_scan"
sys.path.insert(0, str(HERE)); import sidemount as S
T = np.load(OUT / "placement_sidemount_T.npy")
CH, PU, GOLD, GREY, BEIGE = "#2f3136", "#6f3fbf", "#b08d3a", "#9a9a96", "#b8b0a0"
COL = {"side_plate": CH, "lower_adapter": PU, "ear_adapter": PU, "clamp_upper": CH, "clamp_lower": CH}
parts = []
for f in sorted(OUT.glob("sidemount_*.stl")):
    key = f.stem.replace("sidemount_", "")[:-2]; parts.append((pv.read(str(f)), COL[key], 1.0))
lowers = []
cluster = (pv.read(str(HERE.parent / "reference" / "cluster_scan" / "cluster_onshape_reference_mm.stl")).transform(T, inplace=False), BEIGE, 1.0)
cage = (pv.read(str(REF / "cage_primary_tubes_mm.stl")), GOLD, 1.0)
arms = (pv.read(str(REF / "cage_steering_support_tubes_mm.stl")), GOLD, 1.0)
sur = (pv.read(str(REF / "dash_surroundings_mm.stl")), GREY, 0.35)

def shot(meshes, fn, pos, focus, up=(0, 0, 1), zoom=1.0, size=(1600, 1000)):
    pl = pv.Plotter(off_screen=True, window_size=size); pl.set_background("#eceae5")
    for m, c, op in meshes: pl.add_mesh(m, color=c, opacity=op, smooth_shading=False, specular=0.2)
    pl.camera_position = [tuple(pos), tuple(focus), up]; pl.camera.zoom(zoom)
    pl.add_light(pv.Light(position=(600, -1200, 1200), intensity=0.7)); pl.add_light(pv.Light(position=(-800, 400, 800), intensity=0.4)); pl.add_light(pv.Light(position=(300, 900, -300), intensity=0.3))
    pl.screenshot(str(fn)); pl.close()

f = (266, -30, 90)
shot([cage, arms, sur, cluster] + parts + lowers, R / "driver_iso.png", (-450, -1200, 700), f, zoom=1.5)
shot([cage, arms, cluster] + parts + lowers, R / "rear.png", (300, 900, 500), f, zoom=1.6)
shot([cage, arms, sur, cluster] + parts + lowers, R / "side.png", (-900, -60, 120), f, zoom=1.7)
shot([cage, arms] + parts + lowers, R / "mount_only.png", (-350, -900, 600), f, zoom=1.6)
print("sidemount renders done")
