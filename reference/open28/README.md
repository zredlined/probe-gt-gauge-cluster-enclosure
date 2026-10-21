# OPEN / 28 — Ford Probe cluster mount

**Geometry-checked fit prototype for a Bambu P1S.** New CAD built around the supplied scans and OEM mounting points. No rear cover, front bezel, or tall hood. Physical fit, seated visibility, clamp retention and vibration performance have not yet been established.

## What changed

- 28° lean back from vertical, with the cluster centred at vehicle X = 262 mm.
- Cluster-frame origin translated to vehicle `(262, -40, 95)` mm. Relative to the recorded v0.7 transform, this moves the cluster about 96 mm toward the driver and 48 mm down; the change in tilt also affects individual points.
- The new scanned cluster crown is 176.0 mm above the dash-bar centre. A deliberately conservative front/lens envelope reaches 184.4 mm. The old recorded enclosure bounding box reached 279.8 mm: approximately **95 mm less overall height**, including that conservative allowance.
- Two lined, split crossbar clamps at vehicle X = 133.3 and 375 mm. The passenger clamp moves inward to avoid scanned hardware under the bar; two 28 mm spacers connect it to its side plate.
- Four lower OEM holes B2/B3/B5/B6 carry the principal mounting load. T1/T2 provide upper support. B1/B4 are unused. Six custom contact seats follow the recorded 3D mounting-face normals.
- Separate flat side plates, lower adapters and upper adapters make fit revisions and printing manageable. The final design has **12 printed assembly parts**, plus two optional clamp-fit samples.
- Graphite structural parts and small orange spacers are a suggested finish; rendered colours are not functional requirements.

## Start with these files

| File | Purpose |
|---|---|
| `output/plates/00_fit_check.3mf` | Two reduced-width clamp samples plus the four actual tab adapters. Print these first. |
| `output/plates/01_side_plates.3mf` | Two flat side plates, in print orientation. |
| `output/plates/02_cage_clamps.3mf` | Four clamp halves and two bridge spacers. |
| `output/plates/03_tab_adapters.3mf` | Four tab adapters; already included in the fit-check plate, so do not print them twice unless changing material. |
| `output/print/` | Individual STL files, in print orientation, millimetres. |
| `output/open28_assembly.step` | Editable B-rep assembly of printed components in vehicle coordinates. |
| `output/step/` | Individual STEP solids; their native frame is identified in `parts_manifest.json`. |
| `output/assembly/` | Installed-coordinate STLs for review, **not** bed-oriented print files. |
| `output/review.blend` | Full orbitable review scene, supplied scans, printed parts, nominal hardware and connector allowance outlines. |
| `renders/` | Installed, rear, side, front, bare-mount and ribbon-clearance views, plus the placement comparison. |

The 3MF files are **geometry-only model plates**, not printer presets or ready-to-run jobs. Select your P1S, actual nozzle and filament in Bambu Studio. Keep the supplied part orientations. Arrangement leaves room around the P1S front-left exclusion. All individual parts are well within a 256 mm bed; the side plates are approximately 167 × 87 × 8 mm.

## First printing and fitting sequence

1. Print the clamp samples and four tab adapters in PLA for inexpensive fit checks. Confirm the actual painted tube diameter and the OEM hole spacing. The source notes describe 5.3 mm OEM holes, but the scan itself is not a drill specification.
2. Test both upper adapters and both lower adapters independently on the cluster. Use approximately 0.8 mm firm, thin isolation washers at the six OEM seats. These are the intended seat gaps, not a licence to pull a misaligned adapter into place with a screw.
3. Insert the real ribbon plugs, latch them, and check removal access with the adapters fitted. Inspect the actual cable bends and strain relief. The blue rendered boxes are reserved space, not models of your harness.
4. Print the side plates and full clamps for a stationary placement check. Fit the clamps around the dash bar, with their split faces approximately horizontal. `clamp_body` is the upper half; `clamp_cap` is the lower half. Use the 28 mm spacers only on the passenger assembly.
5. Attach the lower adapters to the side plates, then the upper adapters. Leave hardware loose until all six OEM locations seat without preload. The M5 side-plate screws have flush countersunk heads on the outboard faces; their washers and nuts are inboard of the clamps. This preserves connector access.
6. Sit in the actual race seat with helmet and wheel installed. Check forward view, gauge readability through the wheel, hand clearance through full steering travel, wheel removal and master-switch operation. The new position moves the cluster toward the driver as well as lowering it.
7. After fit is confirmed, use ASA for the installed printed parts and check clamp rotation and vibration in the actual installation. The supplied geometry does not establish a torque setting, allowable load or fatigue life. These two crossbar clamps resist rotation through liner friction; this version has no separate torque link to a steering-support arm.

Use roughly 0.5 mm **firm rubber liner**, rather than thick foam, between the clamps and the cage. The nominal clamp bore is 45.25 mm, the reference tube OD is 44.45 mm, and the split gap is 1 mm. Verify the fit sample with your actual paint and liner thickness before committing to the full clamps. The sample pair is only a fit gauge, not a load-bearing mount.

## Printing

- Assumed nozzle: 0.4 mm. Starting process: 0.20 mm layers, 6 walls, 6 top/bottom layers, 40% gyroid and a 5 mm outer brim.
- Side plates: flat, as supplied, without support.
- Clamp halves: flat end face on the bed, so the large tube bore prints vertically; no supports in the bore. Small transverse bolt holes may need cleaning to their specified clearance diameters.
- Bridge spacers: print as supplied; a brim helps the narrow footprint.
- Tab adapters: use tree supports from the build plate as needed for the inclined contact pads. The grouped adapter and fit-check plates were slice-checked with those supports enabled. Keep supports out of the fitted contact faces and clear every fastener/access bore before assembly.
- The mounting holes use through-bolts and nuts; there are no heat-set inserts or printed threads. The upper adapters have 10 mm rear nut-access channels with a seating plane 28 mm behind the reference ear face; use a slim 7 mm nut driver that fits the channel.

All four grouped plates successfully sliced in the installed **Bambu Studio 02.08.02.61**, using fully resolved P1S 0.4 mm, Bambu ASA reference and the process above. No slicer warnings were returned. Detailed results are in `output/slicer_verification.json`. Actual ASA calibration and resulting strength remain printer/material dependent. Verification G-code is not part of the deliverable; slice the supplied models for your own machine.

The three main plates total approximately **217 g and 11 hours** in that slicer estimate. The separate fit-check plate is approximately 83 g / 4.7 hours; it duplicates the four tab adapters, so these estimates should not simply be added when reusing those parts.

PLA is for fit checks here. ASA is preferred for the installed mount because of cabin heat; see the [Bambu filament comparison](https://bambulab.com/it/filament-guide). The [P1S specification](https://us.store.bambulab.com/collections/3d-printer/products/p1s) lists the 256 mm build volume and ASA capability.

## Nominal hardware

Lengths are derived from the model and the prior tab-thickness notes. Confirm with the fitted parts and the actual washer/nut stack before ordering in quantity. Socket-cap lengths exclude the head; countersunk lengths include the head.

| Use | Quantity | Fastener |
|---|---:|---|
| Cage clamps | 4 | M6 × 40 socket cap, washers and locking nuts |
| Driver plate to clamp | 2 | **M5 × 50, 90° countersunk**, rear washers and locking nuts |
| Passenger plate to clamp, through 28 mm spacers | 2 | **M5 × 80, 90° countersunk**, rear washers and locking nuts |
| Driver lower adapter to plate | 2 | M4 × 55 socket cap, washers and locking nuts |
| Passenger lower adapter to plate | 2 | M4 × 50 socket cap, washers and locking nuts |
| Upper adapters to plates | 4 | M4 × 35 socket cap, washers and locking nuts |
| Driver OEM lower tabs B5/B6 | 2 | M4 × 25 socket cap, small washers and locking nuts |
| Passenger OEM lower tabs B2/B3 | 2 | M4 × 30 socket cap, small washers and locking nuts |
| OEM upper ears T1/T2 | 2 | M4 × 45 socket cap, small washers and locking nuts in the access channels |

Use M4 washers small enough to enter the 10/10.4 mm nut-access/spotface diameters; about 9 mm OD is suitable geometrically. The nominal hardware checks use conservative cylindrical head/nut envelopes, not an exact supplier catalogue model. Avoid substituting protruding heads for the four countersunk screws beside the ribbon routes. The lower adapter nut seats are angled to match their bolts.

## Geometry checks and limits

`output/geometry_check.json`, `hardware_check.json`, `parts_manifest.json` and `slicer_verification.json` record the checks.

- Every printed part is a single valid CAD solid and a closed, watertight STL.
- Exact CAD booleans found no part-to-part intersections and no interference between nominal hardware and printed parts, or between hardware items.
- No supplied cage/context mesh vertices were found inside the printed parts or hardware. No cluster vertices were found inside printed parts. OEM screws are deliberately excluded from the cluster-vertex hardware check because their reconstructed holes are not reliable bore models.
- Surface-to-triangle clearance checks sample vertices plus deterministic surface points. They are estimates, **not mathematical minimum clearances**. The minimum sampled mount-to-context gap is about 6.8 mm. Intended tab seats and the clamp/liner interfaces have much smaller gaps by design. Parts near the cage outside the clamp interfaces have roughly 2 mm or more geometric clearance.
- A separate placement check estimates 10.7 mm between the cluster and observed context, 20.1 mm to the dash crossbar, and 13.5–13.6 mm to the two steering-support tubes. These are sampled surface checks; see `output/cluster_placement_check.json`.
- Both ribbon zones reserve **18 × 90 × 70 mm**, in cluster coordinates: passenger X `[-185,-167]`, driver X `[155.5,173.5]`, Y `[-18,72]`, Z `[-100,-30]`. They cover the old slot references plus space for insertion and initial routing. Exact CAD checks include both printed parts and nominal hardware against these volumes. The routes are open to the sides/rear; there is no closed cable hole to thread through. These boxes do not prove a particular cable bend radius, insertion motion or installed harness fit.
- Your current **9 mm lens-proud dimension** takes precedence over the conflicting older 5/11 mm notes. The packaging illustration places a conservative front boundary 9 mm beyond the foremost scanned surface over the front scan silhouette. This is an overall-space proxy, not a reconstruction of the clear lens or a measured gauge-face datum. No new front enclosure or retaining lip has been added.
- The wheel, seated eye point, complete windshield, full switch motion and complete harness are missing from the scan. Camera renders are inspection views, not validated driver sightlines. The old enclosure in the comparison is its recorded bounding box, not an invented reconstruction.
- Geometry checks are against the supplied, open and incomplete references. They cannot prove clearance to unseen surfaces or replace a physical test fit. Structural loads, material creep, vibration and impact retention are untested.

## Rebuild or revise

Run from the original project root with the local virtual environment:

```sh
.venv/bin/python design/scripts/build_mount.py
.venv/bin/python design/scripts/check_geometry.py
.venv/bin/python design/scripts/hardware.py
.venv/bin/python design/scripts/package_prints.py
.venv/bin/python design/scripts/slicer_check.py
.venv/bin/python design/scripts/placement_figure.py
/Applications/Blender.app/Contents/MacOS/Blender -b -t 6 -P design/scripts/render.py
```

The CadQuery generator is the editable parametric source. STEP preserves solid geometry, but not a native Onshape feature history. Changing placement requires rebuilding the support geometry and re-running every collision check; do not rotate only the cluster or move only the clamps in the assembly. The recorded source files remain untouched. No Onshape connection or MCP credits were used.
