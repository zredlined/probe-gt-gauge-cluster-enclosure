# Probe GT gauge cluster mounts

3D-printed mounts for the stock 1993 Ford Probe GT gauge cluster in our 24 Hours of Lemons car. The dash is gone; the
cluster bolts through its own OEM mounting holes to printed parts that clamp to the roll cage's dash crossbar. Everything
is designed from a 3D scan of the cluster and of the cage, generated from code, and checked for fit, fastener access and
assembly before it is printed. Charcoal ASA with one purple accent, exposed aligned screws, no heat-set inserts.

There are two ways to build it. Each has its own folder with print files, renders, bill of materials, print settings and
assembly steps. Pick one and go there.

| | [Skeleton mount](skeleton-mount/README.md) | [Shell enclosure](shell-enclosure/README.md) |
|---|---|---|
| | ![](skeleton-mount/renders/onshape_iso.png) | ![](shell-enclosure/renders/system_driver.png) |
| What | Two flat side plates on two crossbar clamps, bare cluster | Two-piece shell with a sun brow, four clamps with pivots |
| Height | bezel top 154 mm above the bar | bezel top 201 mm above the bar |
| Position | face 28° back, cluster in front of the bar | face 20° back, cluster over the bar, pitch adjustable |
| Printing | 10 flat parts, no supports, about 290 g, every part under 2 h | 16 parts, about 1.2 kg, two 11-hour shells |
| Hardware | 22 bolts, all captured nuts; four M6 is all you touch in the car | 40 fasteners, M2.5 self-tappers for the bars |
| Status | geometry-checked, not yet printed or fitted | printed and fitted in the car; sat high for a short driver |

A third option, a minimal shell, is in the works and will get its own folder the same way.

## Repository

```
skeleton-mount/   option 1: README (BOM, print, assembly), stl/, renders/ (incl. shaded views from Onshape)
shell-enclosure/  option 2: README, stl/ (+ stl/test fit aids), renders/
cad/              the generators and checks for both options, print prep, renders, Onshape push
reference/        cluster_scan (mesh, silhouettes, hole CSV), cage_scan (fitted tubes, dash remnants), open28 (the
                  prototype the skeleton mount came from)
docs/             engineering notes: frames, what the scan got wrong, design decisions and why
```

Both options share the frames and the scans. Scan frame: X across the cluster, Y down, Z toward the driver; L parts are
the face-right (passenger) side, R parts the face-left (driver) side, marked with 1 and 2 dots. Car frame: X along the
crossbar from the driver upright, Y toward the cowl, Z up.

CAD: Onshape document [937c54b34f0ccb974f37f949](https://cad.onshape.com/documents/937c54b34f0ccb974f37f949): "Side mount
system (car frame)" for the skeleton mount, "Full system (car frame)" and "Enclosure assembly" for the shell (element ids
in `cad/output/onshape_ids.json`). Onshape is a viewer; the generators are the source of truth.

## Regenerate

Everything is generated from constants: `cad/sidemount.py` (skeleton mount), `cad/generate.py` and `cad/mount.py`
(shell, feet, clamps). `cad/build.sh` runs geometry, the fastener and interference checks, bed-oriented STLs into each
option's `stl/` and renders into each option's `renders/`. `cad/push.py` updates Onshape (`--sidemount` about 15 API
requests, the shell about 30); `cad/onshape_views.py` pulls shaded views (one request each). Environment, once:

```bash
uv venv cad/.venv && uv pip install --python cad/.venv/bin/python cadquery trimesh shapely scipy ezdxf pyvista requests rtree networkx
```
