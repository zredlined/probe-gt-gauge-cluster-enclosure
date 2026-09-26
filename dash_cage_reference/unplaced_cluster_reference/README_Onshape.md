# Probe gauge cluster — enclosure reference for Onshape

## Start here

Import **cluster_onshape_reference_mm.stl** into Onshape, selecting **millimeters**. This is a scan reference mesh, not the enclosure and not a watertight printable part. It has 149,999 triangles and is approximately 404.5 × 173.6 × 105.3 mm in its supplied coordinate frame. Those are scan-envelope dimensions, not nominal factory dimensions.

The original EXStar projects and the earlier merged point cloud were not modified. CloudCompare performed 0.5 mm spatial subsampling and an independent cloud-to-mesh distance check. Open3D performed depth-10 Poisson reconstruction with four threads. Surface farther than 1.25 mm from the prepared input samples was trimmed, very small disconnected components were removed, and a simplified reference was exported. No extra surface smoothing was applied. The installed CloudCompare Poisson plugin has no command-line entry point, so reconstruction itself ran outside CloudCompare.

## Deliverables

- `cluster_onshape_reference_mm.stl`: light mesh to import into Onshape, **millimeters**; STL cannot carry colors.
- `cluster_onshape_reference_color.ply`: same light mesh with captured colors for CloudCompare.
- `cluster_detailed_color.ply`: 1.77-million-triangle color mesh for detailed inspection.
- `cluster_observed_surface_color.ply`: ball-pivot mesh for inspecting scan-supported edges and openings; less complete than the Poisson mesh and not a manufactured solid.
- `case_outline_xy_mm.dxf`: the projected outer silhouette only, simplified by 0.2 mm from the light mesh's XY projection. This includes protrusions and mounting tabs; it is not a section at a particular depth.
- `case_outline_and_mounts_xy_mm.dxf`: the same silhouette plus projected opening fits, center crosses and labels. These are scan-derived references, not nominal hole sizes or a drill template.
- `mounting_hole_estimates_mm.csv`: eight fitted 3D opening centers, local face normals, apparent rim dimensions and fit residuals.
- `mounting_holes_identification.png`: the eight holes confirmed by the user.
- `mounting_hole_fits.png`: original rear-scan samples and fitted rims.
- `reference_cloud_cad_mm_color.ply`: prepared input cloud in the same coordinates as the meshes and guides.
- `cloudcompare_mesh_deviation.ply`: CloudCompare's independent unsigned distance check, saved as a scalar field on the cloud.

PLY colors come from nearest captured samples. Reconstruction does not recreate uncaptured marker imagery; EXStar's marker symbols remain separate app annotations.

## Eight mounting references

All eight estimates were fitted to the **original rear scan only**, not to the merged mesh. Their relative positions therefore do not depend on the front-to-back registration. Local planar faces were isolated and rim boundary samples fitted with circles or capsule approximations. B6 is clearly elongated; B2's fit is only mildly elongated. Do not choose screws or nominal drill sizes from these apparent rim dimensions: chamfers, incomplete bore sampling and point spacing bias the observed opening size.

Coordinates are in the exact same frame as the STL and DXF. X runs across the case. In the labeled rear view, Y increases downward. Z is depth, with the rear viewed from negative Z. The DXF is an XY projection at Z=0; the actual mounting faces are at different Z values. Use the 3D values and local face orientation when creating mounting surfaces. Face normals describe the scanned faces, not a measured internal bore axis.

| Hole | X mm | Y mm | Z mm | Rim fit RMS mm |
|---|---:|---:|---:|---:|
| T1 | -167.25 | -26.59 | 31.86 | 0.25 |
| T2 | 155.52 | -23.87 | 27.81 | 0.25 |
| B1 | -131.73 | 75.47 | -6.04 | 0.11 |
| B2 | -152.73 | 84.13 | -7.47 | 0.15 |
| B3 | -132.89 | 84.01 | -8.23 | 0.19 |
| B4 | 121.96 | 74.32 | -8.44 | 0.31 |
| B5 | 117.60 | 82.88 | -10.43 | 0.13 |
| B6 | 137.93 | 82.74 | -10.35 | 0.18 |

Numeric precision in the CSV is for reproducibility and does not imply that level of physical accuracy. The source scan spacing is 0.5 mm. Rim fit RMS values of about 0.11–0.31 mm describe agreement to sampled rim points, not true-location accuracy. Independent physical measurements remain necessary for bolt fit.

## Verification and limits

- Against the earlier 1.2-million-point cropped cloud, median distance to the light mesh is 0.058 mm, 95th percentile 0.467 mm, and about 99.0% is within 1 mm. This measures reconstruction fidelity, not scanner accuracy. The maximum is 36.8 mm; some source samples have no nearby retained surface, so coverage is not universal.
- In the eight original rear-scan rim neighborhoods, the 95th-percentile point-to-mesh distances range from 0.16 to 0.28 mm. The actual opening-center references are fitted to raw scan data independently of those mesh facets.
- Original scans were aligned with 20 shared markers, 0.50 mm marker RMS mismatch. This affects the merged enclosure envelope, even though the eight-hole layout uses only the rear scan.
- The earlier ground removal used a 6 mm plane clearance and a bounding crop. Full untrimmed aligned copies remain in `../gauge_cluster_alignment_2026-09-25/` for recovering any contact-adjacent region. Hole fitting used those full copies and isolated the relevant faces.
- Poisson reconstruction may interpolate gaps and soften small openings. Use the fitted center references and physical measurements for mounts, not triangulated hole edges as nominal geometry.
- The STL is intentionally open where scan support was insufficient. Do not run automatic hole filling just to make the reference printable.

## Suggested Onshape workflow

1. Import the STL in millimeters and keep it as a reference in a Part Studio. Verify that its width is approximately 405 mm to catch an import-unit error. Avoid converting every mesh triangle into a CAD face.
2. Import the DXF, create an empty XY sketch and use **Insert DXF or DWG**, in millimeters. Preserve its coordinates relative to the mesh. The outline is useful for a first enclosure profile; it is not a constant-depth mating edge. Add your intended clearance to new enclosure geometry rather than rescaling the scan.
3. Create a dimensioned mounting layout from the eight centers, using the CSV for depth. Measure actual hole diameters/slots, mounting-face heights and a few spans before fixing the CAD dimensions. Model bosses against the structural mounting tabs rather than against the PCB or connector bodies.
4. First make small test pieces that engage the left and right three-hole groups. Confirm screw fit, spacing and seating. Check the two upper mounting points before committing to a full shell. A useful cross-check is the top T1–T2 center distance: the scan estimate is 322.80 mm; the lower B2–B3 span is 19.86 mm, B5–B6 is 20.33 mm, and B3–B5 is 250.51 mm. These are 3D straight-line center distances, not measurements along a curved surface.
5. Build a separate rear shell with working clearance around the scanned body and electronics. A few millimeters is a reasonable initial packaging allowance, to adjust after a fit check; leave additional deliberate room for connector plugs, wire bends and tool access. Add a removable cover, mounting bosses and cable openings as normal parametric CAD features.
6. Design the race-car brackets around the verified enclosure mounting structure. The scan alone does not establish material choice, vibration strength or final bracket loads.

Official references:
- Onshape mesh reference/mixed modeling: https://cad.onshape.com/help/Content/PartStudio/mixed_modeling.htm
- STL/OBJ import units: https://cad.onshape.com/help/Content/uploadfiles.htm
- DXF insertion into a sketch: https://cad.onshape.com/help/Content/Sketch/insert_dwg_or_dxf.htm
- CloudCompare Poisson reconstruction: https://cloudcompare.org/doc/wiki/index.php/Poisson_Surface_Reconstruction_%28plugin%29
