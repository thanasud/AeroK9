"""Build a removable Panel-mounted anti-fold stop for all three SwingArms.

The bracket shares two existing M3 holes in Panel_1 at (-22, -20) and
(0, -20).  Its sloped bumper sits below the SwingArm with 2 mm nominal
clearance.  Forward/outward suspension motion remains free; reverse torque
that tries to fold the arm inward is reacted into the Panel through two ribs.

Run from the repository root with FreeCADCmd:

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
        model/build_panel_reverse_stop.py
"""

import os

import FreeCAD as App
import Mesh
import Part


ROOT = os.path.abspath(os.getcwd())
SOURCE = os.path.join(
    ROOT, "model", "PipeRobotV2_XL430_NoCapsule_PivotCapFit_A1Plate.FCStd"
)
OUTPUT = os.path.join(
    ROOT, "model", "PipeRobotV2_XL430_PanelReverseStop.FCStd"
)
EXPORT_DIR = os.path.join(ROOT, "model", "exports")

# Existing Panel hole centres and printed-fit hardware sizes.
MOUNT_HOLES = ((-22.0, -20.0), (0.0, -20.0))
M3_CLEARANCE_DIAMETER = 3.60
M3_HEAD_COUNTERBORE_DIAMETER = 6.40
M3_HEAD_COUNTERBORE_DEPTH = 3.00

BASE_Z = 38.0
BASE_THICKNESS = 5.0
# The sampled line is slightly closer than the global nearest feature on the
# real SwingArm.  A 2.75 mm line offset produces a measured minimum gap of
# approximately 2.0 mm in the complete CAD assembly.
STOP_CLEARANCE = 2.75
PAD_THICKNESS = 5.0

# The lower face of the arm is almost a straight line over the bumper area.
# Measurements from the actual assembly: Z=66.8 at X=0 and about Z=75.2
# at X=-20.  The stop top follows that face and stays 2 mm below it.
ARM_UNDERSIDE_Z_AT_X0 = 66.80
ARM_UNDERSIDE_SLOPE = -0.42

BED_X = 256.0
BED_Y = 256.0
PART_GAP = 8.0


def add_shape(doc, name, label, shape, color):
    obj = doc.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = color
    return obj


def moved_to_origin(shape):
    result = shape.copy()
    bounds = result.BoundBox
    result.translate(App.Vector(-bounds.XMin, -bounds.YMin, -bounds.ZMin))
    return result


def rotated_about_robot_axis(shape, angle_degrees):
    result = shape.copy()
    result.rotate(App.Vector(), App.Vector(1, 0, 0), angle_degrees)
    return result


def face_from_points(points):
    wire = Part.makePolygon(points + [points[0]])
    return Part.Face(wire)


def stop_top_z(x):
    return (
        ARM_UNDERSIDE_Z_AT_X0
        + ARM_UNDERSIDE_SLOPE * x
        - STOP_CLEARANCE
    )


def make_reverse_stop():
    # Low base leaves the existing Panel/Tower geometry untouched.
    base = Part.makeBox(
        30.0, 12.0, BASE_THICKNESS,
        App.Vector(-26.0, -26.0, BASE_Z),
    )

    # Through holes align to two unused D3.4 holes already in the Panel.
    for x, y in MOUNT_HOLES:
        through = Part.makeCylinder(
            M3_CLEARANCE_DIAMETER / 2.0,
            BASE_THICKNESS + 0.4,
            App.Vector(x, y, BASE_Z - 0.2),
        )
        counterbore = Part.makeCylinder(
            M3_HEAD_COUNTERBORE_DIAMETER / 2.0,
            M3_HEAD_COUNTERBORE_DEPTH + 0.2,
            App.Vector(
                x, y,
                BASE_Z + BASE_THICKNESS - M3_HEAD_COUNTERBORE_DEPTH,
            ),
        )
        base = base.cut(through.fuse(counterbore))

    # A broad, sloped pad distributes reverse load over the underside of the
    # SwingArm.  It does not touch at nominal assembly position.
    x0, x1 = -26.0, 4.0
    pad_points = [
        App.Vector(x0, -45.0, stop_top_z(x0) - PAD_THICKNESS),
        App.Vector(x1, -45.0, stop_top_z(x1) - PAD_THICKNESS),
        App.Vector(x1, -45.0, stop_top_z(x1)),
        App.Vector(x0, -45.0, stop_top_z(x0)),
    ]
    pad = face_from_points(pad_points).extrude(App.Vector(0, 8.0, 0))

    # Two four-millimetre webs turn the cantilever into a boxed load path.
    # The outer web is flush with X=-26 so the print can lie on this face
    # without support material.
    ribs = []
    for rib_x0, rib_x1 in ((-26.0, -22.0), (0.0, 4.0)):
        middle_x = (rib_x0 + rib_x1) / 2.0
        pad_bottom = stop_top_z(middle_x) - PAD_THICKNESS
        rib_points = [
            App.Vector(rib_x0, -26.0, BASE_Z + 0.5),
            App.Vector(rib_x0, -16.0, BASE_Z + BASE_THICKNESS),
            App.Vector(rib_x0, -37.0, pad_bottom),
            App.Vector(rib_x0, -45.0, pad_bottom),
        ]
        ribs.append(
            face_from_points(rib_points).extrude(
                App.Vector(rib_x1 - rib_x0, 0, 0)
            )
        )

    stop = base.fuse(pad).fuse(ribs[0]).fuse(ribs[1]).removeSplitter()
    if not stop.isValid() or len(stop.Solids) != 1:
        raise RuntimeError(
            "reverse stop is not one valid solid: "
            f"valid={stop.isValid()} solids={len(stop.Solids)}"
        )
    return stop


def make_print_shape(stop):
    # Put the full outer rib silhouette on the bed.  This keeps the long
    # cantilever and both diagonal webs support-free on a Bambu Lab A1.
    result = stop.copy()
    result.rotate(App.Vector(), App.Vector(0, 1, 0), -90.0)
    return moved_to_origin(result)


def verify_motion(stop, arm):
    nominal_overlap = stop.common(arm).Volume
    nominal_distance = stop.distToShape(arm)[0]
    if nominal_overlap > 0.01:
        raise RuntimeError(
            f"stop intersects arm at nominal position: {nominal_overlap:.4f}"
        )

    first_contact = None
    for step in range(1, 61):
        angle = -step * 0.25
        moved_arm = arm.copy()
        moved_arm.rotate(
            App.Vector(36.0, 0.0, 62.0), App.Vector(0, 1, 0), angle
        )
        if stop.common(moved_arm).Volume > 0.02:
            first_contact = angle
            break
    if first_contact is None:
        raise RuntimeError("reverse stop does not contact arm within 15 degrees")

    outward_arm = arm.copy()
    outward_arm.rotate(
        App.Vector(36.0, 0.0, 62.0), App.Vector(0, 1, 0), 15.0
    )
    outward_overlap = stop.common(outward_arm).Volume
    if outward_overlap > 0.01:
        raise RuntimeError(
            "stop blocks 15 degree outward motion: "
            f"overlap={outward_overlap:.4f}"
        )
    return nominal_distance, first_contact, outward_overlap


def main():
    if not os.path.exists(SOURCE):
        raise RuntimeError(f"source file not found: {SOURCE}")
    if not os.path.isdir(EXPORT_DIR):
        raise RuntimeError(f"export directory not found: {EXPORT_DIR}")

    doc = App.openDocument(SOURCE)
    panel = doc.getObject("Panel_1")
    tower = doc.getObject("Tower_1")
    arm = doc.getObject("SwingArm_XL430_1")
    spring = doc.getObject("Spring_1")
    if None in (panel, tower, arm, spring):
        raise RuntimeError("Panel_1, Tower_1, SwingArm_XL430_1, or Spring_1 missing")

    stop = make_reverse_stop()
    nominal_distance, first_contact, outward_overlap = verify_motion(
        stop, arm.Shape
    )

    # The base may touch Panel_1 but must not consume material from Panel,
    # Tower, or Spring.  Zero-volume face contact is allowed.
    panel_overlap = stop.common(panel.Shape).Volume
    tower_overlap = stop.common(tower.Shape).Volume
    spring_overlap = stop.common(spring.Shape).Volume
    if max(panel_overlap, tower_overlap, spring_overlap) > 0.01:
        raise RuntimeError(
            "nominal assembly interference: "
            f"panel={panel_overlap:.4f} tower={tower_overlap:.4f} "
            f"spring={spring_overlap:.4f}"
        )

    stop_objects = []
    for index, angle in enumerate((0.0, 120.0, 240.0), start=1):
        obj = add_shape(
            doc,
            f"PanelReverseStop_{index}",
            f"Panel Reverse Stop {index} (2 mm arm clearance)",
            rotated_about_robot_axis(stop, angle),
            (0.95, 0.30, 0.15),
        )
        obj.addProperty("App::PropertyString", "Mounting", "Reverse Stop")
        obj.Mounting = (
            "2x M3 existing Panel holes; centres 22 mm apart; "
            "recommended M3x12 screws"
        )
        obj.addProperty("App::PropertyString", "Function", "Reverse Stop")
        obj.Function = (
            "Allows outward spring travel; limits inward/reverse folding "
            f"after approximately {abs(first_contact):.2f} degrees"
        )
        stop_objects.append(obj)

    print_shape = make_print_shape(stop)
    print_obj = add_shape(
        doc,
        "PRINT_ORIENTED_PanelReverseStop",
        "PRINT 3X - Panel Reverse Stop (outer rib on bed)",
        print_shape,
        (0.95, 0.55, 0.20),
    )
    print_obj.Visibility = False

    # Three identical pieces arranged as separate bodies on one A1 plate.
    bounds = print_shape.BoundBox
    plate_width = 3.0 * bounds.XLength + 2.0 * PART_GAP
    x_start = (BED_X - plate_width) / 2.0
    y_start = (BED_Y - bounds.YLength) / 2.0
    plate_objects = []
    plate_shapes = []
    for index in range(3):
        piece = print_shape.copy()
        piece.translate(
            App.Vector(x_start + index * (bounds.XLength + PART_GAP), y_start, 0)
        )
        obj = add_shape(
            doc,
            f"A1_Plate_PanelReverseStop_{index + 1}",
            f"A1 PLA PLATE - Panel Reverse Stop {index + 1} of 3",
            piece,
            (0.95, 0.55, 0.20),
        )
        obj.Visibility = False
        plate_objects.append(obj)
        plate_shapes.append(piece)

    plate = Part.makeCompound(plate_shapes)
    plate_bounds = plate.BoundBox
    if (
        plate_bounds.XMin < 0.0
        or plate_bounds.YMin < 0.0
        or plate_bounds.XMax > BED_X
        or plate_bounds.YMax > BED_Y
    ):
        raise RuntimeError("three reverse stops do not fit Bambu Lab A1 bed")

    plate_obj = add_shape(
        doc,
        "A1_Plate_3PanelReverseStops",
        "Bambu Lab A1 PLA - 3 Panel Reverse Stops",
        plate,
        (0.70, 0.70, 0.72),
    )
    plate_obj.Visibility = False
    plate_obj.addProperty("App::PropertyString", "PrintRecommendation", "A1 Plate")
    plate_obj.PrintRecommendation = (
        "PLA; 0.20 mm layer; 4 walls; 35% gyroid; no supports; "
        "outer rib face on bed"
    )

    doc.recompute()
    doc.saveAs(OUTPUT)

    single_stl = os.path.join(
        EXPORT_DIR, "PanelReverseStop_Clearance2mm_PLA_PRINT_1X.stl"
    )
    plate_stl = os.path.join(
        EXPORT_DIR, "BambuA1_PLA_3PanelReverseStops_Clearance2mm.stl"
    )
    plate_3mf = os.path.join(
        EXPORT_DIR, "BambuA1_PLA_3PanelReverseStops_Clearance2mm.3mf"
    )
    step_path = os.path.join(
        EXPORT_DIR, "PanelReverseStop_Clearance2mm.step"
    )
    Mesh.export([print_obj], single_stl)
    Mesh.export(plate_objects, plate_stl)
    Mesh.export(plate_objects, plate_3mf)
    Part.export([stop_objects[0]], step_path)

    print("PANEL_REVERSE_STOP_BUILD_OK")
    print(f"  output={OUTPUT}")
    print(f"  single_stl={single_stl}")
    print(f"  plate_stl={plate_stl}")
    print(f"  plate_3mf={plate_3mf}")
    print(f"  step={step_path}")
    print(
        "  fit "
        f"nominal_arm_gap={nominal_distance:.3f} mm "
        f"reverse_contact_angle={first_contact:.2f} deg "
        f"outward_15deg_overlap={outward_overlap:.4f} mm3"
    )
    print(
        "  nominal_interference "
        f"panel={panel_overlap:.4f} tower={tower_overlap:.4f} "
        f"spring={spring_overlap:.4f} mm3"
    )
    print(
        "  print_bounds_1x "
        f"{bounds.XLength:.2f} x {bounds.YLength:.2f} x "
        f"{bounds.ZLength:.2f} mm"
    )
    print(
        "  a1_plate_bounds "
        f"{plate_bounds.XLength:.2f} x {plate_bounds.YLength:.2f} x "
        f"{plate_bounds.ZLength:.2f} mm"
    )


main()
