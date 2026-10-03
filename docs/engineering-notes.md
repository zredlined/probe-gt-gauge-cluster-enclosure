# Engineering notes

The non-obvious facts you need to change the design without re-learning them on the printer.

## Frames

- **Scan frame** (enclosure, feet, `cad/generate.py`): X across the cluster, **Y down in the car**, Z toward the driver.
  Scan +X is the driver's left. Part names L / R follow the scan: **L is the face-right side** of the cluster (round-hole
  lug plate, scan holes B2 B3 T1), **R is the face-left side** (slotted lug hole, B5 B6 T2). Every bracket carries dots:
  1 = L, 2 = R.
- **Car frame** (mount, `cad/mount.py`): X along the dash crossbar driver to passenger, Y toward the cowl, Z up, origin on
  the crossbar axis at the driver upright. Scan to car is `car = (X_C - x, -z, -y)` then a 20 deg pitch about X; the
  front-bottom edge of the shell lands `FACE_Y` behind the bar and `EDGE_LIFT` above it.

## What the scan got wrong (calipers, 2026-09-27 to 10-02)

- Mounting holes are all 5.3 mm (B6 is a 5.3 x 8.8 slot); the scan said 5.3 to 6.8. Hole pair spacing 19.7, not 20.2.
- The CSV hole centres lie on the tabs' rear faces. Lug plates 4.8 thick, ear tabs 7.0 thick, 19.5 wide, 10 tall, hole
  5 below the tip; the lens is notched around each tab. Each lug plate has a rib on its outer edge 6 to 7 mm outboard of
  the outer hole.
- The scanner did not see the clear lens: it stands 11 mm proud of the scanned rim and 5 mm proud of the black frame.
- The cluster is 2 to 3 mm deeper than the scan at the rear.
- The bezel shroud tapers toward the face (scanned top edge y -81.6 at the back, -70 at the rim). An opening drawn to the
  widest outline leaves 17 to 29 mm of air; the nose is lofted to the hull of scan vertices with z >= 36 instead.
- Ribbon plugs are 51 and 59.8 x 9.6 mm with a 4 mm thumb lock outboard.

## Design decisions, and why

- **Feet and ear bosses, not a cradle.** v0.4 held the cluster by shape and foam; the solid bosses had no line of sight
  and no fasteners. The cluster now bolts through its own holes: four M4 into nuts captured in two printed feet, two M4
  from the front into nuts in bosses moulded into the roof.
- **No heat-set inserts.** Angled inserts wander when melted in. Nuts sit in printed channels; the only small screws
  (bars) self-tap into 2.4 mm pilots, the value coupon-tested on the race logger. Repair: drill to 3.4, press an insert.
- **Everything is driven from outside or on the bench.** `cad/fastener_check.py` sweeps an 8 mm driver from every head
  at the stage where it is driven and reports the free length with everything fitted; it also samples every clamp against
  the shell and the shell against the cage tubes. Both checks exist because printed parts found the problems first.
- **Knuckles**: four identical, M6, pin 16 mm below the wall so 12 to 13 mm clevises clear it; clamp rings are notched
  under the knuckles. Lock knuckles sit 33 mm forward of the pivots for a usable pitch-lock lever arm.
- **Placement**: gauge face about 16 mm behind the crossbar's driver-side surface, front-bottom edge 50 mm above the bar
  top, face leaning back 20 deg, centred on the steering column. Eye point and windshield base in `mount.py` are guesses.

## Generator

One geometry description drives two backends: CadQuery (dense polylines, local STLs, mesh checks) and FeatureScript (fit
splines, the Onshape custom features). Verified FeatureScript behaviours: intersections via SUBTRACT_COMPLEMENT, sheared
prisms via opLoft, halves via opSplitPart, 0.3 mm overlaps instead of coincident spline faces, boolean tools are consumed
(build a fresh tool per boolean), `coordSystem()` needs exactly perpendicular axes (re-orthogonalise in FS), an empty tool
list is an error. The feature carries step tracking: on failure it creates a body named `FAILED step N: ...`.

Onshape document `937c54b34f0ccb974f37f949`: Part Studio 1 (enclosure + feet), "Mount (car frame)" Part Studio, Feature
Studio "Cluster enclosure FeatureScript" (both features), "Enclosure assembly" and "Full system (car frame)" assemblies
(ids in `cad/output/onshape_ids.json`, rebuilt by `push.py`). A push is about 29 API requests.
