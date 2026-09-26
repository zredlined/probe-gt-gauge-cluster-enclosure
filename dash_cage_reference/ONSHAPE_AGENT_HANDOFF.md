# Probe race-car cage and dash — Onshape handoff

Revision 2, September 26, 2026: added both 1.75-inch tubes projecting toward the steering column as fitted reference geometry. Supersedes the initial package. All model coordinates are **millimeters**.

## User's intended outcome

Design a stable, serviceable cage-mounted support for the gauge-cluster enclosure the user is building. Keep the cluster approximately in its OEM driver-side location behind the steering wheel, lifted above where it rests in the supplied photo. Use multiple separated attachment points on the front cage to limit rotation and vibration. The user also confirmed that the two tubes reaching toward the steering column are 1.75 inches and should be considered as candidate anchors. The user has not specified lift, pitch, or final mount dimensions. Keep the driver's eye position adjustable.

This package supplies the surrounding reference geometry and fitted cage, not a completed mount. Start with the user's current enclosure CAD when it becomes available. The previous gauge-cluster mesh describes the cluster itself; it is not the new enclosure.

## Start here

1. Import `cage_and_dash_reference_mm.stl` with units set to **millimeters** for a combined context reference.
2. For separate selection/visibility, instead import `cage_primary_tubes_mm.stl` and `dash_surroundings_mm.stl`. These share the same origin and orientation. Do not independently center or align them. Avoid displaying these together with the combined STL, which duplicates their surfaces.
3. Use `onshape_reference_geometry.json` and `cage_centerlines_mm.csv` to reconstruct native CAD cage envelopes if useful. The crossbar is a straight 44.45 mm diameter cylinder; the driver upright is a straight–circular-bend–straight sweep of the same diameter. The two short steering-support arms are straight cylinders of the same diameter, each with its own fitted axis.
4. Bring in the user's enclosure and establish its placement separately. The car scan and earlier cluster scan have **not** been registered to each other. Do not import the earlier cluster at identity and assume the placement is meaningful.
5. Add adjustable eye, steering-wheel, cluster-lift and pitch references, then resolve visibility, access and mounting geometry together.

`car_reference_photo.png` provides installed-wheel and loose-cluster context. It is not a calibrated camera view or a source of precise dimensions. The hood is raised in the photograph.

## Files and purpose

| File | Purpose |
|---|---|
| `cage_and_dash_reference_mm.stl` | Combined nominal cage and surrounding scanned geometry; easiest starting reference |
| `cage_primary_tubes_mm.stl` | Fitted main dash crossbar, driver front upright/bend, and both steering-support arms |
| `cage_dash_crossbar_mm.stl`, `cage_driver_upright_mm.stl` | Individual tube envelopes |
| `cage_steering_support_tubes_mm.stl` | Both fitted 44.45 mm arms projecting toward the steering column |
| `driver_side_steering_support_mm.stl`, `center_side_steering_support_mm.stl` | Individual fitted arm envelopes |
| `steering_arm_fit_report.json` | Arm axes, model bounds, fit residuals and limitations |
| `steering_support_detail_reference.png` | Close-up showing the newly fitted arms and scanned end fittings |
| `dash_surroundings_mm.stl` | Scanned context with most duplicate main-tube surfaces removed |
| `dash_context_mm.stl` | Complete reconstructed scan before replacing primary cage surfaces; use to compare fits |
| `master_switch_region_scan_mm.stl` | Cropped switch, plate and nearby surfaces, already in car coordinates |
| `steering_supports_region_scan_mm.stl` | Cropped scanned support area; includes nearby surfaces |
| `cage_and_dash_reference_color.ply` | Gold cage/gray context for CloudCompare or other color-capable viewers |
| `onshape_reference_geometry.json` | Exact reference coordinates, bend definition and unset placement parameters |
| `cage_centerlines_mm.csv` | Ordered tube centerline samples, with nominal outside diameter |
| `native_scan_to_cad_mm.txt` | Homogeneous 4×4 native-scan-to-delivered-frame transform |
| `cage_fit_report.json`, `mesh_quality_report.json`, `export_validation.json` | Fit residuals, scan comparison and export checks |
| `driver_view_reference.png`, `driver_oblique_reference.png`, `top_view_reference.png`, `cage_only_reference.png` | Orientation and coverage previews |
| `unplaced_cluster_reference/` | Prior cluster mesh and eight-hole estimates, in their own separate coordinate system |

STL has no reliable color or units metadata. Select millimeters explicitly. The PLY's gold/gray colors are assigned for identification, not recovered scan texture. No source colors were available in this car scan.

## Coordinate system and cage geometry

Origin: main crossbar centerline at its closest approach to the driver-side upright axis, near the left junction.

- **+X:** along the crossbar from the driver side toward the center/passenger side.
- **+Y:** forward toward the lower cowl/windshield.
- **+Z:** upward, derived from the driver upright and orthogonalized to the crossbar. This is an approximate vehicle frame, not a measured gravity datum.

| Reference | Delivered geometry, mm |
|---|---|
| Nominal cage outside diameter | **44.45** (user-specified 1.75 inches) |
| Crossbar centerline | (0, 0, 0) to (782.252, 0, 0) |
| Driver upright bottom center | (-0.356, -1.061, -166.519) |
| Driver upright top center | (36.380, -182.935, 287.977) |
| Upright bend centerline radius | 134.578, fitted approximation |
| Bend turn angle | 56.918 degrees |
| Bend start | (0.206, -1.061, 94.360) |
| Bend end | (12.238, -61.034, 207.097) |
| Approximate steering axis point near hub | (266.139, -317.480, 57.955) |
| Steering axis direction toward driver | (-0.006766, -0.911536, 0.411164) |

The steering axis was estimated from cylindrical column surfaces; the point near the hub is an approximate axial endpoint, **not a measured wheel mounting face**. The steering column is not a cage member.

The crossbar was extended a short distance through the obscured left weld junction to the upright. All tube end caps are artificial model truncations. They do not represent physical tube ends. Tube models are solid outside envelopes; no wall thickness is inferred. The four members overlap at their joints and are not boolean-unioned. Surrounding scan surfaces are open and incomplete; the combined STL is a spatial reference, not a watertight printable object.

For an analytic upright path, use the JSON bend center C, radius R, start tangent u and direction h:

`P(theta) = C + R * (-cos(theta) * h + sin(theta) * u)`

for theta from 0 to the reported turn angle. Connect the reported bottom to bend start, and bend end to top. Use a circular 44.45 mm section. Exact data are in the JSON; do not use the rounded table for reconstruction.

## Coverage and uncertainty

Source project: `/Users/redlined/Documents/EXStar Hub/probe fuel dash monster` (the matching project on disk; the user called it “probe fuel dash monitor”). Source point data: `Project_1/frame0/cloud.bin`. Project metadata identifies an Einstar Rockit scan, marker alignment and 0.5 mm point spacing. The source contains 2,928,868 points. It was reduced to 438,812 prepared points using 1.25 mm voxel sampling and isolated-point filtering. The mesh was reconstructed, trimmed near the observed surface, and reduced to 220,000 triangles before fitted tubes were substituted.

The fitted primary tubes are the main dash crossbar, driver-side front upright/bend, and both 44.45 mm arms reaching toward the steering column. The user explicitly identified those arms as candidate mounting locations. Their terminal fittings, welds, brackets, steering hardware, switch, lower cowl and center-dash supports remain scanned context. Geometry alone does not establish the available clamping space or load capacity. Passenger upright, door bars, roof bars and full windshield boundary are not reconstructed from this scan. Do not extend the model into a complete cage without new measurements.

At nominal 44.45 mm OD, radial RMS residuals on selected straight tube surfaces are approximately 0.38 mm for the crossbar, 0.31 mm for the lower upright, and 0.33 mm for the upper upright. The inferred circular bend has approximately 0.45 mm surface RMS residual. Free-diameter checks gave about 44.70, 44.80 and 44.57 mm respectively. These are fit statistics on partial surfaces, **not guarantees of physical accuracy or clamp clearance**.

The scan-to-mesh check for the original context has approximately 0.32 mm 95th-percentile distance; the combined nominal-cage/context reference is approximately 0.50 mm. This measures reproduction of the prepared scan, not scanner calibration, unobserved surfaces or absolute accuracy. All four individual tube-envelope exports were read back and checked as watertight, orientable and non-self-intersecting after welding duplicate STL vertices. This does not make the combined scene watertight. Larger local errors remain around edges, thin parts and gaps. Confirm actual painted OD and chosen clamp locations before fixing a production fit.

## Newly included steering-support arms

These are the two short gold tubes visible in the supplied photo, one on each side of the steering column. They project rearward from the dash crossbar toward the driver (negative Y), with a slight rise. They are separate from the central steering column itself.

| Member | Axis at crossbar plane Y=0, mm | Axis at model boundary Y=-100, mm |
|---|---|---|
| Driver-side arm | (199.715, 0, -0.864) | (205.404, -100, 7.629) |
| Center-side arm | (323.854, 0, -0.068) | (325.098, -100, 7.220) |

Both use the user-confirmed **44.45 mm OD**. The clean straight scan surfaces between roughly Y=-24 and Y=-92 were used for fitting, excluding the terminal fittings. They give radial RMS residuals of approximately 0.10 and 0.09 mm respectively; free-diameter checks give 44.60 and 44.58 mm. These fit statistics are not physical accuracy or clamp-fit guarantees. Exact axes and selected point counts are in `steering_arm_fit_report.json`.

The fitted envelopes extend into the crossbar junction and end at Y=-100 where the terminal fittings begin. These are model transition boundaries, not the physical overall lengths of the complete supports. Open terminal fittings and weld details remain in the scan mesh; no bore diameter, wall thickness or fabricated end feature is inferred. Do not use the capped envelopes as hole geometry or fill in the missing interiors in the production design.

A preliminary search region for a clamp is Y=-80 to -35 on each straight arm. This is a region to inspect, not 45 mm of guaranteed unobstructed clamp width. Compare against the complete scan, brackets, welds, wiring and the real car. Retain the existing steering assembly and its clearance when evaluating the arms.

## Placement, sight lines and access

Keep the enclosure in the original gauge-binnacle region behind the wheel. Use the steering axis and photo as initial qualitative references; neither fixes the cluster's final transform. Lift and tilt the enclosure as parameters. Do not default to relocating it over the center stack.

The wheel and cluster are absent from this car scan. Add a wheel reference using measured rim OD, rim thickness, dish/offset and its mounting datum before assessing obstruction. The photo alone does not establish these dimensions. Keep eye position and an optional eye box adjustable, as requested. Do not present a chosen camera render as a verified driver's view.

With a candidate placement, check rays from the adjustable eye positions to the gauge face/corners against the wheel, enclosure lip and cage. Check forward visibility using the real windshield opening and seated-driver position when available; the scanned lower cowl alone cannot establish the complete road view. Also check hands at the rim, steering controls and wheel removal/installation space.

The left master power switch must remain visible and reachable. The supplied crop contains its observed plate/handle pose and nearby surfaces; its bounding box is **not** an operational clearance envelope. Allow for the full lever throw, hand access and rear wiring after confirming them on the car. The scan and supplied photo may capture different handle positions.

## Mount concept to develop next

Evaluate a stiff enclosure support using separated attachments on the front crossbar and the two newly modeled steering-support arms. The arms offer attachment positions offset toward the driver from the crossbar axis, potentially helping resist enclosure pitch without a long brace toward the left upright. Compare a crossbar-plus-arms layout against a simpler pair of arm clamps with sufficient rotational restraint. Place clamps around existing welds, end fittings, brackets and wiring. Keep a driver-upright brace as an alternative only where switch access and space permit. A brace off the crossbar axis provides another way to resist enclosure pitch; exact anchors and geometry are not fixed by this package.

Use the enclosure's structural mounting features to carry loads, with multiple enclosure attachment points. Do not use the PCB as the structural connection. Include service access and cable routing. Split clamps are a starting concept that preserves the existing cage; no cage drilling or welding has been designed here. Mount stiffness, hardware sizing and any vibration isolation must be resolved with the enclosure mass and available space. Multiple attachments alone do not establish vibration performance.

Before completing the full mount, make a small clamp-fit sample and a simple placement mockup to confirm fit, desired lift, switch access and actual seated visibility. No final bracket thickness, hardware torque, load capacity or vibration performance has been established.

## Related cluster reference

The package's `unplaced_cluster_reference/` contains copies of the earlier `cluster_onshape_reference_mm.stl`, `mounting_hole_estimates_mm.csv` and `README_Onshape.md`. The user confirmed the labeled T1–T2 and B1–B6 are the eight intended mounting holes. Preserve the uncertainty and measurement guidance in that earlier README. These files are independent cluster coordinates and require a placement transform into this car frame; the new enclosure geometry is still needed for mount design.

Original folder: `/Users/redlined/Documents/Playground/gauge_cluster_mesh_2026-09-25/`.

## Suggested prompt for the next agent

“Read ONSHAPE_AGENT_HANDOFF.md and import the cage/dash references in millimeters. Use my current gauge-cluster enclosure CAD. Keep it behind the steering wheel near the OEM location, lifted above the loose position in the photo. Consider the two modeled 1.75-inch steering-support arms as well as the crossbar. Develop a mount from multiple separated front-cage attachments that controls rotation and vibration while preserving power-switch access, steering clearance and serviceability. Leave the driver's eye position adjustable. The cluster/enclosure is not yet registered to the car; establish and expose that placement rather than assuming the imports align. Show candidate placement and attachment geometry before finalizing fit-dependent dimensions.”
