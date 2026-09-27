# Print plan (Bambu P1S, 256 x 256 x 256 mm, ASA)

| Plate | Part | File | Footprint x*y mm | Height mm | ASA g | Fits | Orientation |
|---|---|---|---|---|---|---|---|
| A (alone) | shell_L | `output/print/print_shell_L.stl` | 213.1 x 229.3 | 183.5 | 430 | yes | rear wall on the bed, brow up; supports under top lip, chin, ear webs, knuckles |
| B (alone) | shell_R | `output/print/print_shell_R.stl` | 204.3 x 230.2 | 183.5 | 416 | yes | same as Shell L |
| C | spine_bar | `output/print/print_spine_bar.stl` | 30.0 x 177.5 | 15.7 | 17 | yes | inner (concave) face down; small support under the curled brow end |
| C | keel_bar | `output/print/print_keel_bar.stl` | 40.0 x 53.7 | 111.5 | 20 | yes | rear leg flat on the bed, bottom leg standing |
| C | test_coupon | `output/print/print_test_coupon.stl` | 50.0 x 20.0 | 8.0 | 8 | yes | as is |
| FIT | fit_ring_L | `output/print/print_fit_ring_L.stl` | 213.1 x 205.8 | 21.0 | 63 | yes | front face (lips) on the bed, no supports |
| FIT | fit_cradle_L | `output/print/print_fit_cradle_L.stl` | 112.7 x 65.7 | 73.0 | 86 | yes | rear wall on the bed like the shell; support under the knuckle if present |
| FIT | fit_ear_L | `output/print/print_fit_ear_L.stl` | 68.7 x 55.0 | 41.5 | 18 | yes | front face on the bed; small support under the ear-pad web |
| FIT | fit_ring_R | `output/print/print_fit_ring_R.stl` | 204.3 x 206.7 | 21.0 | 61 | yes | front face (lips) on the bed, no supports |
| FIT | fit_cradle_R | `output/print/print_fit_cradle_R.stl` | 118.6 x 65.7 | 73.0 | 89 | yes | rear wall on the bed like the shell; support under the knuckle if present |
| FIT | fit_ear_R | `output/print/print_fit_ear_R.stl` | 68.8 x 55.0 | 41.5 | 18 | yes | front face on the bed; small support under the ear-pad web |
| D | bar_clamp_upper_driver | `output/print/print_bar_clamp_upper_driver.stl` | 40.0 x 94.0 | 61.9 | 65 | yes | split face down, clevis up, no supports |
| D | bar_clamp_lower_driver | `output/print/print_bar_clamp_lower_driver.stl` | 30.0 x 94.0 | 31.5 | 34 | yes | flipped: split face down |
| D | arm_clamp_upper_driver | `output/print/print_arm_clamp_upper_driver.stl` | 95.5 x 51.3 | 72.1 | 50 | yes | split face down, strut + clevis up (small support under the strut lean) |
| D | arm_clamp_lower_driver | `output/print/print_arm_clamp_lower_driver.stl` | 95.5 x 35.3 | 31.5 | 34 | yes | flipped: split face down |
| D | bar_clamp_upper_center | `output/print/print_bar_clamp_upper_center.stl` | 40.0 x 94.0 | 61.9 | 65 | yes | split face down, clevis up, no supports |
| D | bar_clamp_lower_center | `output/print/print_bar_clamp_lower_center.stl` | 30.0 x 94.0 | 31.5 | 34 | yes | flipped: split face down |
| D | arm_clamp_upper_center | `output/print/print_arm_clamp_upper_center.stl` | 94.3 x 50.0 | 71.7 | 49 | yes | split face down, strut + clevis up (small support under the strut lean) |
| D | arm_clamp_lower_center | `output/print/print_arm_clamp_lower_center.stl` | 94.3 x 31.2 | 31.5 | 34 | yes | flipped: split face down |

Total ASA about 1591 g (solid volume x 1.07 g/cm3; real usage depends on infill and supports).

Plates: FIT = the six fit-test sections (print first), A = Shell L alone, B = Shell R alone, C = spine bar + keel bar + coupon, D = all eight clamp halves.
Print order: plate FIT (test on the cluster) -> one bar-clamp lower (tube fit) -> plate D -> plate C -> shells.
