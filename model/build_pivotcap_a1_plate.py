"""Fix the PivotCap rotating fit and prepare a Bambu Lab A1 print plate.

Run inside a FreeCAD Python console from the repository root:

    exec(open("model/build_pivotcap_a1_plate.py").read())

The source assembly is not overwritten.  The generated plate contains four
real-motor-verified SwingArms and six corrected PivotCaps.
"""

import os

import FreeCAD as App
import Mesh
import Part


ROOT = os.path.abspath(os.getcwd())
SOURCE = os.path.join(
    ROOT, "model", "PipeRobotV2_XL430_RealMotor_NoCapsuleBoss.FCStd"
)
OUTPUT = os.path.join(
    ROOT, "model", "PipeRobotV2_XL430_NoCapsule_PivotCapFit_A1Plate.FCStd"
)
EXPORT_DIR = os.path.join(ROOT, "model", "exports")

# Bambu Lab A1 with the included 0.4 mm nozzle.
BED_X = 256.0
BED_Y = 256.0
PART_GAP = 6.0

# Measured from the current CAD:
#   PivotStud centre pin = 4.60 mm
#   Original PivotCap through-hole = 4.50 mm (0.10 mm interference)
# A 4.80 mm nominal hole gives 0.10 mm radial design clearance.  Small FDM
# holes normally print slightly undersize, leaving a snug but rotatable fit.
STUD_PIN_DIAMETER = 4.60
ORIGINAL_CAP_HOLE_DIAMETER = 4.50
CAP_HOLE_DIAMETER = 4.80
ENTRY_CHAMFER_DIAMETER = 5.10

PIVOT_X = 36.0
PIVOT_Z = 62.0
CAP_Y_MIN = -43.0
CAP_Y_MAX = -36.0


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


def translated(shape, x, y, z=0.0):
    result = shape.copy()
    result.translate(App.Vector(x, y, z))
    return result


def rotated_about_robot_axis(shape, angle_degrees):
    result = shape.copy()
    result.rotate(
        App.Vector(0, 0, 0), App.Vector(1, 0, 0), angle_degrees
    )
    return result


def make_corrected_cap(original_cap):
    """Enlarge only the centre hole; retain the 9.90 mm outer bushing."""
    main_hole = Part.makeCylinder(
        CAP_HOLE_DIAMETER / 2.0,
        (CAP_Y_MAX - CAP_Y_MIN) + 0.2,
        App.Vector(PIVOT_X, CAP_Y_MIN - 0.1, PIVOT_Z),
        App.Vector(0, 1, 0),
    )
    entry_chamfer = Part.makeCone(
        ENTRY_CHAMFER_DIAMETER / 2.0,
        CAP_HOLE_DIAMETER / 2.0,
        0.5,
        App.Vector(PIVOT_X, CAP_Y_MIN - 0.05, PIVOT_Z),
        App.Vector(0, 1, 0),
    )
    exit_chamfer = Part.makeCone(
        ENTRY_CHAMFER_DIAMETER / 2.0,
        CAP_HOLE_DIAMETER / 2.0,
        0.5,
        App.Vector(PIVOT_X, CAP_Y_MAX + 0.05, PIVOT_Z),
        App.Vector(0, -1, 0),
    )
    corrected = original_cap.cut(
        main_hole.fuse(entry_chamfer).fuse(exit_chamfer)
    ).removeSplitter()
    if not corrected.isValid() or len(corrected.Solids) != 1:
        raise RuntimeError(
            "corrected PivotCap is not one valid solid: "
            f"valid={corrected.isValid()} solids={len(corrected.Solids)}"
        )
    return corrected


def make_print_cap(corrected_cap):
    # Put the flat flange face on Z=0 and leave the bushing/socket upward.
    result = corrected_cap.copy()
    result.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), -90.0)
    return moved_to_origin(result)


def main():
    if not os.path.exists(SOURCE):
        raise RuntimeError(f"source file not found: {SOURCE}")
    if not os.path.isdir(EXPORT_DIR):
        raise RuntimeError(f"export directory not found: {EXPORT_DIR}")

    doc = App.openDocument(SOURCE)
    original_cap = doc.getObject("PivotCap_1")
    stud = doc.getObject("PivotStud_1")
    print_arm = doc.getObject("PRINT_ORIENTED_SwingArm_XL430_NoCapsule")
    if original_cap is None or stud is None or print_arm is None:
        raise RuntimeError("PivotCap_1, PivotStud_1, or print arm is missing")

    corrected_cap = make_corrected_cap(original_cap.Shape)
    stud_cap_overlap = stud.Shape.common(corrected_cap).Volume
    if stud_cap_overlap > 0.001:
        raise RuntimeError(
            "corrected PivotCap still interferes with PivotStud: "
            f"overlap={stud_cap_overlap:.6f} mm^3"
        )

    # Replace visual assembly references without modifying the originals.
    corrected_cap_objects = []
    for index, angle in enumerate((0.0, 120.0, 240.0), start=1):
        old_cap = doc.getObject(f"PivotCap_{index}")
        if old_cap is not None:
            old_cap.Visibility = False
        cap_obj = add_shape(
            doc,
            f"PivotCap_RotatingFit_{index}",
            f"PivotCap Rotating Fit D4.80 {index}",
            rotated_about_robot_axis(corrected_cap, angle),
            (0.25, 0.80, 0.35),
        )
        cap_obj.addProperty("App::PropertyString", "FitSpecification", "PivotCap")
        cap_obj.FitSpecification = (
            "Stud pin D4.60; cap hole D4.80; radial clearance 0.10 mm; "
            "D5.10 entry chamfer"
        )
        corrected_cap_objects.append(cap_obj)

    print_cap_shape = make_print_cap(corrected_cap)
    print_cap_obj = add_shape(
        doc,
        "PRINT_ORIENTED_PivotCap_RotatingFit",
        "PRINT 6X - PivotCap Rotating Fit D4.80",
        print_cap_shape,
        (0.25, 0.90, 0.45),
    )
    print_cap_obj.Visibility = False

    arm_shape = moved_to_origin(print_arm.Shape)
    arm_bounds = arm_shape.BoundBox
    cap_bounds = print_cap_shape.BoundBox

    # Fit four arms in a 2x2 grid.  Centre the group in X and keep enough
    # room below it for one row of six caps.
    arms_width = 2.0 * arm_bounds.XLength + PART_GAP
    arms_x0 = (BED_X - arms_width) / 2.0
    arms_y0 = 18.0
    second_row_y = arms_y0 + arm_bounds.YLength + PART_GAP
    plate_shapes = []
    plate_objects = []
    arm_positions = (
        (arms_x0, arms_y0),
        (arms_x0 + arm_bounds.XLength + PART_GAP, arms_y0),
        (arms_x0, second_row_y),
        (arms_x0 + arm_bounds.XLength + PART_GAP, second_row_y),
    )
    for index, (x, y) in enumerate(arm_positions, start=1):
        shape = translated(arm_shape, x, y)
        obj = add_shape(
            doc,
            f"A1_Plate_SwingArm_{index}",
            f"A1 PLA PLATE - SwingArm No Capsule {index} of 4",
            shape,
            (0.35, 0.75, 0.95),
        )
        plate_shapes.append(shape)
        plate_objects.append(obj)

    caps_y = second_row_y + arm_bounds.YLength + 8.0
    caps_width = 6.0 * cap_bounds.XLength + 5.0 * PART_GAP
    caps_x0 = (BED_X - caps_width) / 2.0
    for index in range(6):
        x = caps_x0 + index * (cap_bounds.XLength + PART_GAP)
        shape = translated(print_cap_shape, x, caps_y)
        obj = add_shape(
            doc,
            f"A1_Plate_PivotCap_{index + 1}",
            f"A1 PLATE - PivotCap {index + 1} of 6",
            shape,
            (0.25, 0.90, 0.45),
        )
        plate_shapes.append(shape)
        plate_objects.append(obj)

    plate_compound = Part.makeCompound(plate_shapes)
    plate_bounds = plate_compound.BoundBox
    if (
        plate_bounds.XMin < 0.0
        or plate_bounds.YMin < 0.0
        or plate_bounds.XMax > BED_X
        or plate_bounds.YMax > BED_Y
    ):
        raise RuntimeError(
            "four arms and six caps do not fit the A1 bed: "
            f"bounds=({plate_bounds.XMin}, {plate_bounds.XMax}, "
            f"{plate_bounds.YMin}, {plate_bounds.YMax})"
        )

    plate_summary = add_shape(
        doc,
        "A1_Plate_4SwingArms_6PivotCaps",
        "Bambu Lab A1 PLA - 4 No-Capsule SwingArms + 6 PivotCaps",
        plate_compound,
        (0.65, 0.65, 0.70),
    )
    plate_summary.Visibility = False
    plate_summary.addProperty("App::PropertyString", "Printer", "A1 Print Plate")
    plate_summary.Printer = "Bambu Lab A1; 256 x 256 x 256 mm; 0.4 mm nozzle"
    plate_summary.addProperty("App::PropertyString", "PlateContents", "A1 Print Plate")
    plate_summary.PlateContents = "4x SwingArm XL430 NoCapsuleBoss + 6x PivotCap D4.80"
    plate_summary.addProperty("App::PropertyString", "PlateBounds", "A1 Print Plate")
    plate_summary.PlateBounds = (
        f"{plate_bounds.XLength:.2f} x {plate_bounds.YLength:.2f} x "
        f"{plate_bounds.ZLength:.2f} mm"
    )

    doc.recompute()
    doc.saveAs(OUTPUT)

    cap_stl = os.path.join(
        EXPORT_DIR, "PivotCap_RotatingFit_D4p80_PLA_TEST_1X.stl"
    )
    plate_stl = os.path.join(
        EXPORT_DIR, "BambuA1_PLA_4SwingArms_NoCapsule_6PivotCaps_D4p80.stl"
    )
    plate_3mf = os.path.join(
        EXPORT_DIR, "BambuA1_PLA_4SwingArms_NoCapsule_6PivotCaps_D4p80.3mf"
    )
    Mesh.export([print_cap_obj], cap_stl)
    Mesh.export(plate_objects, plate_stl)
    Mesh.export(plate_objects, plate_3mf)

    print("PIVOTCAP_A1_BUILD_OK")
    print(f"  output={OUTPUT}")
    print(f"  cap_stl={cap_stl}")
    print(f"  plate_stl={plate_stl}")
    print(f"  plate_3mf={plate_3mf}")
    print(
        "  fit "
        f"stud_d={STUD_PIN_DIAMETER:.2f} "
        f"old_hole_d={ORIGINAL_CAP_HOLE_DIAMETER:.2f} "
        f"new_hole_d={CAP_HOLE_DIAMETER:.2f} "
        f"radial_clearance={(CAP_HOLE_DIAMETER - STUD_PIN_DIAMETER) / 2.0:.2f} "
        f"stud_cap_overlap={stud_cap_overlap:.6f}"
    )
    print(
        "  A1_plate "
        f"parts={len(plate_shapes)} solids={len(plate_compound.Solids)} "
        f"bounds=({plate_bounds.XMin:.3f}, {plate_bounds.XMax:.3f}, "
        f"{plate_bounds.YMin:.3f}, {plate_bounds.YMax:.3f}, "
        f"{plate_bounds.ZMin:.3f}, {plate_bounds.ZMax:.3f})"
    )


main()
