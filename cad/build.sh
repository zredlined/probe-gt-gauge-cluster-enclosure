#!/usr/bin/env bash
# Regenerate everything from the constants: STLs, print files, checks, renders. Needs the venv in cad/.venv
# (cadquery, trimesh, shapely, scipy, ezdxf, pyvista, requests). Onshape is NOT touched; run push.py for that.
set -euo pipefail
cd "$(dirname "$0")"
source .venv/bin/activate
python generate.py            # enclosure + feet (scan frame), mesh clearance check
python mount.py               # placement in the car + cage clamps (car frame), sightline/clearance checks
python fastener_check.py      # driver reach for every fastener, part interference
python print_prep.py          # bed-oriented files -> ../stl
python render.py              # -> ../renders
python render_system.py
