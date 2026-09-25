# 1993 Ford Probe GT gauge cluster enclosure

![Driver view](mechanical/output/renders/01_driver_iso.png)

Roll-cage-mounted enclosure and sun brow for the OEM Probe GT gauge cluster, designed from a 3D scan of the cluster.
Aesthetic brief: the same "Teenage Engineering designs for a race car" language as the 4OGS race logger (charcoal body,
one purple accent, exposed aligned fasteners), mounted Ducati-Monster style off the exposed cage over time.

Build guide (parts, hardware, print and assembly): [docs/BUILD.md](docs/BUILD.md).

## Layout

```
onshape_reference_package/   scan deliverables (STL, colour PLY, DXF silhouettes, hole CSV, README_Onshape.md)
mechanical/generate.py       single source of truth: constants -> CadQuery (local STLs + mesh clearance check) and FeatureScript
mechanical/render.py         pyvista renders of the STLs with the scan mesh inside -> mechanical/output/renders
mechanical/push.py           uploads the FeatureScript to the Onshape Feature Studio and (re)inserts the custom feature (spends API allocation)
mechanical/output/           generated: *.stl, probe_cluster_enclosure.fs, seat_data.json, onshape_ids.json, renders/
```

Run (scratch env with cadquery, trimesh, shapely, scipy, ezdxf, pyvista, requests):

```bash
python mechanical/generate.py        # geometry + clearance report (~20 s)
python mechanical/render.py          # renders
source ~/.zshrc && python mechanical/push.py   # ~7 Onshape API requests
```

## Coordinate frame

Scan frame, millimetres: **X** across the cluster, **Y increases downward in the car**, **Z toward the driver**
(bezel front at about +50, harness connectors at the rear down to -56). Everything (STL, DXF, hole CSV, FeatureScript)
shares this frame so it lines up in Onshape without transforms.

## Design (v0.3, 2026-09-25)

- **Shell L / Shell R**, split at X = 0 (a 405 mm part does not fit the P1S bed). The halves close around the cluster;
  the cluster is never drilled or screwed. Cavity is the scan silhouette hull (corners rounded to R12) offset 4 mm.
- **Cradle retention**: ledges under the two bottom lug plates carry the weight; a fin outside each plate fixes X and yaw;
  tilted stop pads behind lug holes B2 B3 B5 B6 and ears T1 T2 stop rearward motion; a top lip (4 mm over the rim) and a
  bottom chin (reaches the bezel's lower rim) stop forward motion. All pad heights come from the scan (1 mm standoff).
  Add thin foam tape on the lip rear faces if the cluster rattles.
- **Closed back with two ribbon ports** (v0.3): the rear wall (inner face z -58) covers the PCB and both centre connector
  housings. The ribbon cables plug into two vertical PCB slots (left x -179..-173, right x 161..168, y 2..50, thumb locks
  facing outboard); each rear corner has a port from 12 mm inboard of its slot out to the side wall, 12 mm above and below
  the slot, so a plug can be pushed in and its thumb lock worked from behind. Two rows of 2.4 mm vent slots (x +-105,
  y -48..-22 and -14..12) cool the PCB. Four M6 nut-pocket pads (x = +-60, y = 26 and 48) are the cage-bracket interface.
- **Double skin**: the sun-facing arch has a second 2 mm skin on a 6 mm ventilated air gap (ribs at x = +-60, +-115,
  +-160 and two 8 mm ribs at x = +-6 that carry the spine inserts). The skin continues forward as a 70 mm brow that follows a
  200 mm arc curling up toward the driver (lofted through 6 sections) and ends in a 5 mm rounded bead, so there is no
  sharp edge to bump against (Brian's suggestion).
- **Spine bar** (top ridge, purple) and **Keel bar** (rear + bottom seam, purple) join the halves: M2.5 x 8 socket screws
  into the user's M2.5 x 4 heat-set inserts (3.4 mm bores), two visor screws with nuts underneath.
- **Test coupon**: M2.5 insert bore, M2.5 self-tap pilot, M6 nut pocket + clearance, fin slot.

Print: halves rear-face down (the front lips are the only overhangs, small support strips), ASA, charcoal; bars purple.

## Onshape

Document `probe-gt-gauge-cluster-enclosure`: did `937c54b34f0ccb974f37f949`, wid `275b479cd4996a16dce317f4`,
Part Studio 1 `c10029ec19783bb5bae02ce9`, Feature Studio "Cluster enclosure FeatureScript" `4b35d3a06a0b574150eddd3c`.
Custom feature "Probe cluster enclosure" with toggles for the four part groups. push.py also rebuilds "Enclosure
assembly" (id in onshape_ids.json) after every successful push because regenerated parts get new IDs; the scan mesh
Part Studio `177864c843a60c8c5b179426` is inserted as PARTS and SURFACES. The feature carries step tracking: if an
op fails it creates a body named `FAILED step N: ...` instead of an opaque error (push.py prints part names).
FeatureScript notes learned on this project: intersections use SUBTRACT_COMPLEMENT (keeps the target's identity), the
visor is a two-profile loft (a sheared prism), halves come from opSplitPart, and bodies that must merge overlap by 0.3 mm
rather than sharing spline faces. Import
`onshape_reference_package/cluster_onshape_reference_mm.stl` (millimetres) by drag-and-drop for a visual overlay; that
costs no API allocation.

## Renders

| Rear (ribbon ports, vents) | Side (brow) | Exploded |
|---|---|---|
| ![](mechanical/output/renders/04_rear.png) | ![](mechanical/output/renders/05_side_right.png) | ![](mechanical/output/renders/10_exploded.png) |

## Open items

- Roll-cage bracket (needs the cage model).
- Physical check of the lug plate ledge/fin fit and rim lip clearance with the coupon and a lug-corner test print.
- Visor length/droop and skin end position are constants in generate.py; tune after the first look in the car.
