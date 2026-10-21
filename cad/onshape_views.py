"""Shaded views of the side-mount assembly straight from Onshape (one API request per view) -> skeleton-mount/renders/onshape_*.png.
Car frame: x along the bar (driver -> passenger), y toward the cowl, z up. Onshape's view matrix is the top 3 rows of the
model -> camera transform in METRES; camera looks down its -Z, X right, Y up; with pixelSize > 0 the image is centred on the
camera-space origin. Usage: source ~/.zshrc; python onshape_views.py [view ...]  (default: all)"""
import sys, json, base64
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
import push

HERE = Path(__file__).parent; R = HERE.parent / "skeleton-mount" / "renders"; R.mkdir(parents=True, exist_ok=True)
state = json.loads((HERE / "output" / "onshape_ids.json").read_text()); ASM = state["sidemount_asm"]
FOCUS = np.array([0.266, -0.030, 0.090])          # cluster centre, metres

def matrix(cam_dir, up=(0, 0, 1.0), focus=FOCUS):
    """Camera at focus + cam_dir looking at focus. Returns the 12 comma-separated values."""
    z = np.asarray(cam_dir, float); z /= np.linalg.norm(z)                 # toward the viewer
    x = np.cross(up, z); x /= np.linalg.norm(x); y = np.cross(z, x)
    Rm = np.vstack([x, y, z]); t = -Rm @ focus
    return ",".join(f"{v:.6f}" for v in np.hstack([Rm, t[:, None]]).flatten())

VIEWS = {
    "driver_view": dict(viewMatrix=matrix((0, -1, 0.15)), pixelSize=0.00045),          # from the seat, toward the windshield
    "iso": dict(viewMatrix=matrix((-0.6, -1, 0.7)), pixelSize=0.00045),                # driver-side high iso
    "iso_rear": dict(viewMatrix=matrix((0.7, 1, 0.5)), pixelSize=0.00045),             # from the cowl side, the plates and clamps
}

def fetch(name, spec):
    q = f"viewMatrix={spec['viewMatrix']}&outputHeight=1000&outputWidth=1600&pixelSize={spec['pixelSize']}&edges=show&showAllParts=true&includeSurfaces=true&useAntiAliasing=true"
    j = push.api("GET", f"/assemblies/d/{push.DID}/w/{push.WID}/e/{ASM}/shadedviews?{q}")
    img = base64.b64decode(j["images"][0]); fn = R / f"onshape_{name}.png"; fn.write_bytes(img); print(f"  {fn.name}: {len(img) // 1024} kB")

if __name__ == "__main__":
    wanted = sys.argv[1:] or list(VIEWS)
    for n in wanted: fetch(n, VIEWS[n])
    print(f"API requests this run: {push.CALLS}")
