PANEL REVERSE STOP - BAMBU LAB A1 / PLA
========================================

Purpose
-------
This removable bracket prevents each SwingArm from folding inward under
reverse wheel force.  The sloped rail follows the underside of the arm and
transfers the load to two existing holes in the Panel through two printed
ribs.  Outward/spring motion remains free.

Parts and hardware
------------------
- Print 3x Panel Reverse Stop (one per Panel/SwingArm).
- Use 2x M3 screws per stop, 22 mm centre-to-centre.
- M3x12 is the starting recommendation; confirm engagement with the existing
  Panel/BoardTray stack before tightening.

CAD fit validation
------------------
- Minimum nominal SwingArm gap: 2.03 mm.
- Reverse/inward contact begins at approximately 2.0 degrees from the saved
  CAD pose.
- Checked clear at nominal position against Panel, Tower, Spring, and the
  official XL430 model on all three sides.
- Checked free for at least 15 degrees of outward arm travel.

Bambu Studio starting settings
------------------------------
- Printer: Bambu Lab A1, 0.4 mm nozzle.
- Material: PLA.
- Layer height: 0.20 mm.
- Walls: 4.
- Top/bottom shells: 5.
- Infill: 35% gyroid.
- Supports: off.  The supplied 3MF/STL is already lying on its full outer-rib
  face for support-free printing.
- Brim: optional 4 mm if bed adhesion is uncertain.

Assembly
--------
1. Place the flat base on the outside face of the Panel.
2. Align the two counterbored holes with the existing Panel holes at X=-22
   and X=0, Y=-20 in the first Panel orientation.
3. The open triangular frame points toward the SwingArm; the long sloped rail
   sits below the arm without touching it at rest.
4. Tighten both M3 screws evenly.  Do not rely on one screw.
5. Move the arm by hand before powering the robot.  Confirm outward motion is
   free and inward motion reaches the stop smoothly.
6. Add a thin rubber/EVA strip to the rail only if quieter contact is needed;
   it will reduce the available 2.03 mm gap.

Important
---------
This is a prototype hard stop for the current saved arm angle.  If the robot
must collapse more than about 2 degrees to enter a smaller pipe, increase the
stop clearance before printing the full set.
