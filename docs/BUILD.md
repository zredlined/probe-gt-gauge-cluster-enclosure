# Build guide: Probe GT gauge cluster enclosure

Printed parts, hardware, print settings and assembly order for v0.3. The gauge cluster itself is never drilled or
screwed: it sits in a cradle and the two shell halves clamp around it.

![Driver view](../mechanical/output/renders/01_driver_iso.png)

## 1. Printed parts

| Part | File | Qty | Colour | Notes |
|---|---|---|---|---|
| Shell L | `mechanical/output/shell_l.stl` | 1 | charcoal ASA | 213 x 208 x 184 mm, fits the Bambu P1S diagonally |
| Shell R | `mechanical/output/shell_r.stl` | 1 | charcoal ASA | mirror-ish of L (not identical: the cluster is not symmetric) |
| Spine bar | `mechanical/output/spine_bar.stl` | 1 | purple ASA | joins the halves along the roof ridge and brow |
| Keel bar | `mechanical/output/keel_bar.stl` | 1 | purple ASA | L-shaped, joins the halves across the rear wall and bottom |
| Test coupon | `mechanical/output/test_coupon.stl` | 1 | any | print first, see section 3 |
| Bar clamp lower L / R | `mechanical/output/mount_bar_clamp_lower_l.stl`, `..._r.stl` | 2 | charcoal ASA | split clamp halves on the 1.75 in crossbar |
| Bar clamp upper L / R | `mechanical/output/mount_bar_clamp_upper_l.stl`, `..._r.stl` | 2 | charcoal ASA | upper halves with the raked blade strut and clevis |
| Upright clamp inboard / outboard | `mechanical/output/mount_upright_clamp_inboard.stl`, `..._outboard.stl` | 2 | charcoal ASA | on the A-pillar bar, z 48..76 |
| Pitch stay | `mechanical/output/mount_pitch_stay.stl` | 1 | purple ASA | slotted link, sets pitch |

Coordinates in the STLs are the scan frame (X across, Y down in the car, Z toward the driver). Rotate in the slicer as
described below.

## 2. Hardware

| Item | Qty | Used for |
|---|---|---|
| M2.5 x 4 heat-set inserts, 3.5 mm OD | 14 | 6 under the spine bar (thick roof ribs), 8 under the keel bar |
| M2.5 x 8 socket or button head screws | 18 | 14 into inserts, 4 through the brow with nuts |
| M2.5 nuts + small washers | 4 | the two screw pairs on the brow (2 mm skin, no rib for an insert) |
| M8 x 50 bolts + nyloc nuts + nylon washers | 2 | pivot pins through the strut clevises and enclosure knuckles |
| M6 x 60 bolts + nuts | 4 | the two crossbar clamps (2 each) |
| M6 x 60 bolts + nuts | 2 | the upright clamp |
| M6 x 25 bolts + nuts + washers | 2 | pitch stay: one into the upright-clamp ear, one through the enclosure boss (nut inside the shell) |
| Adhesive foam tape, 3 mm EPDM | ~300 mm | rear faces of the top lip and chin, the six stop pads |

Nothing else. The cluster is located by ledges under its two bottom lug plates, fins outside the plates, tilted stop
pads behind lug holes B2 B3 B5 B6 and ears T1 T2, and the front lip and chin over the bezel rim.

## 3. Print

Material: ASA (the cluster sits in the sun). 0.2 mm layers, 4 walls, 30 percent gyroid infill for the shells, 100 percent
for the bars and coupon.

1. **Coupon first.** It carries a 3.4 mm insert bore, a 2.4 mm self-tap pilot, an M6 nut pocket with clearance hole and a
   slot the width of a cradle fin. Seat an insert, run a screw into the pilot, drop an M6 nut in the pocket. If the
   insert bore is loose or tight, change `INSERT_M25_D` in `mechanical/generate.py` and regenerate before printing the shells.
2. **Shells**: rear face down (the flat rear wall is the bed face, the brow points up). Supports only under the top lip,
   the chin and the small ear-pad webs; everything else is vertical walls. Each half is one 12 to 16 hour print.
3. **Spine bar**: ridge face down. **Keel bar**: rear face down.
4. Heat-set the 14 inserts: 6 from the roof skin surface at x +-6 mm, z -40 / 0 / +40 (they land in the 8 mm ribs inside
   the air gap), 4 in the rear wall pads at x +-12, y 58 and 84, 4 in the bottom wall pads at x +-12, z -30 and +20.
   Bores are 6.5 mm deep; the insert sits flush.

## 4. Assembly

1. Drop the four M6 nuts into their pockets on the inside of the rear wall (two per half). They are captured once the
   cluster is in.
2. Stick foam tape on the rear face of the top lip and chin in both halves, and a 20 x 20 mm pad on each of the six stop
   pads (two behind each lug plate, one behind each ear).
3. Lay Shell L on its side, outer face down. Lower the cluster in from the split plane: the left lug plate lands on its
   ledge with the fin outside it, the left ear rests on its pad, the bezel rim tucks behind the lip and chin.
4. Bring Shell R over the cluster the same way until the halves meet at the centre seam.
5. Fit the spine bar over the ridge, six M2.5 x 8 into the inserts. Then the four brow screws with nuts and washers
   underneath.
6. Fit the keel bar over the rear and bottom seam, eight M2.5 x 8.
7. Plug the two ribbon cables into the PCB slots through the rear-corner ports; the thumb locks face outboard. Check the
   plugs seat and release with the enclosure on before mounting the pod to the cage.

To remove the cluster later: keel bar off, spine bar off, halves apart. Nothing else moves.

## 5. Mounting to the cage

1. Print a clamp-fit sample first (one lower clamp half) and check it on the painted 44.45 mm bar; adjust `CLAMP_BORE` in
   `mechanical/mount.py` if it binds or rattles.
2. Fit the two crossbar clamps at 127 and 437 mm from the driver-upright junction (either side of the column stubs),
   arms up and raked toward the driver, M6 x 60 loosely.
3. Fit the upright clamp on the A-pillar bar just above the crossbar junction (48 to 76 mm up), ear toward the cluster.
4. Lower the assembled enclosure so its two knuckles enter the clevises; push the M8 pins through with nylon washers.
5. Bolt the pitch stay between the upright-clamp ear and the enclosure boss. Sit in the car, set the pitch so the gauge
   face looks straight at your eyes (the model assumes 20 deg leaning back), tighten the stay, then the clamps.
6. Height check: the brow should sit at or just above the line from your eyes to the base of the windshield. If it is
   not, change `LIFT` in `mechanical/mount.py` (currently 100 mm bottom-wall-to-bar-top) and reprint the four bar clamp halves.

## 6. Regenerating

Everything is generated from `mechanical/generate.py` (constants at the top). `python mechanical/generate.py` rebuilds the
STLs and checks the scan mesh for interference; `python mechanical/render.py` remakes the renders; `python mechanical/push.py`
uploads both FeatureScript features to Onshape and rebuilds both assemblies there (about 13 Onshape API requests, so push only when
you want to look).

![In the car](../mechanical/output/renders/sys_01_driver_oblique.png)
![Rear](../mechanical/output/renders/04_rear.png)
![Exploded](../mechanical/output/renders/10_exploded.png)
