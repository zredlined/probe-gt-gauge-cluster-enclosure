# Engineering notes

The non-obvious facts you need to change the design without re-learning them on the printer. Two options live in the
repo (`skeleton-mount/`, `shell-enclosure/`); the low-profile cradle (v1.0 to v1.2, `cad/cradle.py`) sat between them
and is superseded by the skeleton mount: its code and checks stay in `cad/` for reference, its print files were removed
(regenerable with `cad/cradle.py` + `cad/print_prep.py` if ever wanted).

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
- **Known tight spot**: the rear-bottom corner of Shell R passes 2.9 mm from the scanned dash remnant on the driver
  side (car x 76, y 90, z 50). If it touches in the car, `FACE_Y` -38 -> -35 moves the whole enclosure 3 mm toward the
  driver; everything else re-derives.
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

## Side mount (October 2026)

- **Where it came from.** The OPEN28 prototype (`reference/open28/`) was built by another model from the handoff
  package: flat side plates behind the cluster on two crossbar clamps, separate lug and ear adapters, pitch 28, scan
  origin at car (262, -40, 95). Its geometry checks were envelope-only (no driver sweeps, no stage logic), and its joints
  were new: countersunk M5 into 12 mm bosses, 28 mm printed spacers on the passenger side, M4 x 45 into a nut 28 mm down
  a 10 mm well at the ears, round nut bores needing a socket at the lugs. `cad/sidemount.py` keeps the architecture and
  the placement and swaps every joint for a proven one (mount.split_clamp, the v0.5 lug slab, the ear block with the
  side-entry channel, captured nuts in pockets and top-entry slots).
- **Placement.** The whole cluster sits in front of the bar (car y -120 to +25) where the cradle and the shell kept it
  over the bar (y -19 to +120): 100 mm closer to the driver for 17 mm less height than the cradle. Nobody has sat behind
  it yet; the wheel and stalks are not scanned. `PITCH` and `ORIGIN` in `sidemount.py` are the only knobs; the truss
  re-derives from them (clamp nodes are the clamp bosses mapped into the scan frame).
- **Passenger side.** The dash scan has hardware under the bar from x 390 to 430 (z -18 to -59), so the clamp stays at
  375 and the upper continues as a half-ring saddle out to the plate at 420 (the OPEN28 spacers). A flat two-hole strap
  stands just outboard of the passenger plate (x 432 to 450, y -69 to -11, z -31 to 22): it blocks a driver on the front
  M5 head in the car, which is why the M5s are bench fasteners (uppers bolted to the plates before the assembly goes on
  the bar), and it passes 3.6 mm from the passenger ribbon plug body (the 25 mm straight-cable allowance behind the plug
  touches it). Raising `ORIGIN` z by 5 mm gives the whole plug envelope 4 mm.
- **Clearances.** Side plates 7.3 (L) and 4.6 mm (R) from the cluster scan; the real cluster is 2 to 3 mm deeper at the
  rear, hence the spine at z -58 and the clamp bosses at z 15 rather than 18. The ear blocks show 7 to 9 scan vertices
  inside, the same spot where the scan's housing top disagreed with the calipers for the shell's ear bosses.
- **Lesson repeated.** The first build of the cleaned design had three interferences and one unreachable nut: the lower
  adapter block ran into the clamp flanges (now trimmed by the car plane y = -50), the L plate's bar notch was never cut
  (the cutting cylinder did not reach that side), and the lug-nut channels opened against the clamp. All found by
  `sidemount_check.py` before anything was printed.
- **Assembly walkthrough (2026-10-21, after the user asked).** Beyond driver sweeps: an M6 x 40 from below would end
  at z 29 while the cluster bottom sits at z 26 over the driver-side front flange, hence M6 x 30 (tip 8 mm past the
  nyloc). The plates wrap the bar from the cowl side over the top to the driver-side equator (10 to 180 deg), so the
  assembly drops straight on. The dash shelf under the bar on the driver side (z -41 at x 130 to 160) leaves the driver
  lower 9 mm of vertical travel, so it slides on from near the upright (nothing within 50 mm of the tube for x 40 to
  120); the passenger lower has 62 mm. M5 slots are 8.2 for an 8.0 nut so the nuts stay put with the slots sideways.
  Ribbons go in on the bench. The reused lowers are now in the side-mount export so Onshape shows them.
- **Onshape.** `push.py --sidemount` uploads `output/sidemount_car.step` as a Part Studio (no FeatureScript; the previous
  Part Studio and STEP tab are deleted first) and builds "Side mount system (car frame)" from the cage tubes, surroundings,
  the mount and the cluster scan placed by `placement_sidemount_T.npy`; 15 to 16 requests. `onshape_views.py` fetches
  shaded views of that assembly (view matrix = top 3 rows of model-to-camera in metres, camera looks down -Z, pixelSize in
  metres centres the image on the camera origin); one request per view.
