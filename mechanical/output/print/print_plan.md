# Print plan (Bambu P1S, 256 x 256 x 256 mm, ASA)

| Plate | Part | File | Footprint x*y mm | Height mm | ASA g | Fits | Orientation |
|---|---|---|---|---|---|---|---|
| A (alone) | shell_L | `output/print/print_shell_L.stl` | 213.1 x 231.3 | 164.0 | 396 | yes | rear wall on the bed, brow up; supports only under the two knuckles (the nose leans in at 20-35 deg and prints unsupported) |
| B (alone) | shell_R | `output/print/print_shell_R.stl` | 204.3 x 232.2 | 164.0 | 378 | yes | same as Shell L |
| C | spine_bar | `output/print/print_spine_bar.stl` | 30.0 x 158.0 | 15.7 | 15 | yes | inner (concave) face down; small support under the curled brow end |
| C | keel_bar | `output/print/print_keel_bar.stl` | 40.0 x 53.7 | 79.0 | 16 | yes | rear leg flat on the bed, bottom leg standing |
| C | test_coupon | `output/print/print_test_coupon.stl` | 50.0 x 20.0 | 8.0 | 8 | yes | as is |
| FEET | foot_lug_L | `output/print/print_foot_lug_L.stl` | 36.8 x 31.4 | 20.7 | 11 | yes | pad face (shell bottom wall side) on the bed; no supports |
| FEET | foot_lug_R | `output/print/print_foot_lug_R.stl` | 37.3 x 28.6 | 22.0 | 11 | yes | same as lug L |
| FEET-VAR | foot_lug_L_tilt-3 | `output/print/print_foot_lug_L_tilt-3.stl` | 36.8 x 31.8 | 21.0 | 11 | yes | angle variant: slab -3 deg about the bolt line, pad flat |
| FEET-VAR | foot_lug_R_tilt-3 | `output/print/print_foot_lug_R_tilt-3.stl` | 37.3 x 29.0 | 22.3 | 11 | yes | angle variant: slab -3 deg about the bolt line, pad flat |
| FEET-VAR | foot_lug_L_tilt+3 | `output/print/print_foot_lug_L_tilt+3.stl` | 36.8 x 31.1 | 20.3 | 11 | yes | angle variant: slab +3 deg about the bolt line, pad flat |
| FEET-VAR | foot_lug_R_tilt+3 | `output/print/print_foot_lug_R_tilt+3.stl` | 37.3 x 28.2 | 21.6 | 11 | yes | angle variant: slab +3 deg about the bolt line, pad flat |
| COUPON | ear_coupon_L | `output/print/print_ear_coupon_L.stl` | 32.0 x 35.7 | 24.0 | 7 | yes | rear cut face on the bed, nut channel horizontal; no supports |
| COUPON | ear_coupon_R | `output/print/print_ear_coupon_R.stl` | 32.0 x 39.1 | 24.0 | 7 | yes | same |
| D | bar_clamp_upper_driver | `output/print/print_bar_clamp_upper_driver.stl` | 40.0 x 94.0 | 49.2 | 41 | yes | split face down, clevis up, no supports |
| D | bar_clamp_lower_driver | `output/print/print_bar_clamp_lower_driver.stl` | 30.0 x 94.0 | 31.5 | 34 | yes | flipped: split face down |
| D | arm_clamp_upper_driver | `output/print/print_arm_clamp_upper_driver.stl` | 95.5 x 60.8 | 60.5 | 44 | yes | split face down, strut + clevis up (small support under the strut lean) |
| D | arm_clamp_lower_driver | `output/print/print_arm_clamp_lower_driver.stl` | 95.5 x 35.3 | 31.5 | 34 | yes | flipped: split face down |
| D | bar_clamp_upper_center | `output/print/print_bar_clamp_upper_center.stl` | 40.0 x 94.0 | 49.2 | 41 | yes | split face down, clevis up, no supports |
| D | bar_clamp_lower_center | `output/print/print_bar_clamp_lower_center.stl` | 30.0 x 94.0 | 31.5 | 34 | yes | flipped: split face down |
| D | arm_clamp_upper_center | `output/print/print_arm_clamp_upper_center.stl` | 94.3 x 59.3 | 59.9 | 44 | yes | split face down, strut + clevis up (small support under the strut lean) |
| D | arm_clamp_lower_center | `output/print/print_arm_clamp_lower_center.stl` | 94.3 x 31.2 | 31.5 | 34 | yes | flipped: split face down |

Total ASA about 1199 g (solid volume x 1.07 g/cm3; real usage depends on infill and supports).

Plates: FEET = the two lug feet (print first, ~1 h each), FEET-VAR = +-3 deg lug-foot variants for the angle check, COUPON = ear-boss coupons (15 min each), A = Shell L alone, B = Shell R alone, C = spine bar + keel bar + coupon, D = all eight clamp halves.
Print order: plate FEET (bolt the cluster to them) -> Shell L -> Shell R -> plate C -> one bar-clamp lower (tube fit) -> plate D.
