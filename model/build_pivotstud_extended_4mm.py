"""Create a separate PivotStud with a 4 mm longer PivotCap-side pin."""

import os

import FreeCAD as App
import Mesh
import Part


ROOT = os.path.abspath(os.getcwd())
SOURCE = os.path.join(
    ROOT, "model", "PipeRobotV2_XL430_NoCapsule_PivotCapFit_A1Plate.FCStd"
)
OUTPUT = os.path.join(ROOT, "model", "PivotStud_ExtendedPlus4mm.FCStd")
EXPORT_DIR = os.path.join(ROOT, "model", "exports")

PIVOT_X = 36.0
PIVOT_Z = 62.0
ORIGINAL_PIN_END_Y = -36.0
PIN_DIAMETER = 4.60
EXTENSION_LENGTH = 4.0
BOOLEAN_OVERLAP = 0.05


def moved_to_origin(shape):
    result = shape.copy()
    bounds = result.BoundBox
    result.translate(App.Vector(-bounds.XMin, -bounds.YMin, -bounds.ZMin))
    return result


def add_shape(doc, name, label, shape, color):
    obj = doc.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = color
    return obj


def main():
    if not os.path.exists(SOURCE):
        raise RuntimeError(f"source file not found: {SOURCE}")
    if not os.path.isdir(EXPORT_DIR):
        raise RuntimeError(f"export directory not found: {EXPORT_DIR}")

    source_doc = App.openDocument(SOURCE)
    original_obj = source_doc.getObject("PivotStud_1")
    cap_obj = source_doc.getObject("PivotCap_RotatingFit_1")
    if original_obj is None or cap_obj is None:
        raise RuntimeError("PivotStud_1 or corrected PivotCap is missing")

    original = original_obj.Shape
    extension = Part.makeCylinder(
        PIN_DIAMETER / 2.0,
        EXTENSION_LENGTH + BOOLEAN_OVERLAP,
        App.Vector(
            PIVOT_X,
            ORIGINAL_PIN_END_Y - BOOLEAN_OVERLAP,
            PIVOT_Z,
        ),
        App.Vector(0, 1, 0),
    )
    extended = original.fuse(extension).removeSplitter()
    if not extended.isValid() or len(extended.Solids) != 1:
        raise RuntimeError(
            "extended PivotStud is not one valid solid: "
            f"valid={extended.isValid()} solids={len(extended.Solids)}"
        )

    old_bounds = original.BoundBox
    new_bounds = extended.BoundBox
    actual_extension = new_bounds.YMax - old_bounds.YMax
    if abs(actual_extension - EXTENSION_LENGTH) > 0.001:
        raise RuntimeError(
            "PivotStud extension length is wrong: "
            f"actual={actual_extension:.6f} expected={EXTENSION_LENGTH:.6f}"
        )

    cap_overlap = extended.common(cap_obj.Shape).Volume
    if cap_overlap > 0.001:
        raise RuntimeError(
            "extended PivotStud interferes with corrected PivotCap: "
            f"overlap={cap_overlap:.6f} mm^3"
        )

    output_doc = App.newDocument("PivotStud_ExtendedPlus4mm")
    assembly_obj = add_shape(
        output_doc,
        "PivotStud_ExtendedPlus4mm",
        "PivotStud Extended +4 mm (PivotCap side)",
        extended,
        (0.85, 0.55, 0.15),
    )
    assembly_obj.addProperty("App::PropertyString", "Modification", "PivotStud")
    assembly_obj.Modification = (
        "D4.60 center pin extended 4.00 mm toward +Y/PivotCap side; "
        "base geometry unchanged"
    )
    assembly_obj.addProperty("App::PropertyString", "Material", "PivotStud")
    assembly_obj.Material = "PLA"

    # Put the original D16 flange on the bed.  Original +Y becomes print +Z.
    print_shape = extended.copy()
    print_shape.rotate(
        App.Vector(0, 0, 0), App.Vector(1, 0, 0), 90.0
    )
    print_shape = moved_to_origin(print_shape)
    print_obj = add_shape(
        output_doc,
        "PRINT_ORIENTED_PivotStud_ExtendedPlus4mm",
        "PRINT - PivotStud Extended +4 mm (flange on bed)",
        print_shape,
        (0.25, 0.80, 0.95),
    )

    output_doc.recompute()
    output_doc.saveAs(OUTPUT)

    stl_path = os.path.join(
        EXPORT_DIR, "PivotStud_ExtendedPlus4mm_PLA_PRINT.stl"
    )
    three_mf_path = os.path.join(
        EXPORT_DIR, "PivotStud_ExtendedPlus4mm_PLA_PRINT.3mf"
    )
    step_path = os.path.join(
        EXPORT_DIR, "PivotStud_ExtendedPlus4mm.step"
    )
    Mesh.export([print_obj], stl_path)
    Mesh.export([print_obj], three_mf_path)
    Part.export([assembly_obj], step_path)

    added_volume = extended.Volume - original.Volume
    print("PIVOTSTUD_EXTENDED_BUILD_OK")
    print(f"  output={OUTPUT}")
    print(f"  stl={stl_path}")
    print(f"  3mf={three_mf_path}")
    print(f"  step={step_path}")
    print(
        "  geometry "
        f"pin_d={PIN_DIAMETER:.2f} extension={actual_extension:.2f} "
        f"old_axis_length={old_bounds.YLength:.2f} "
        f"new_axis_length={new_bounds.YLength:.2f} "
        f"added_volume={added_volume:.3f}"
    )
    print(
        "  print_bounds "
        f"({print_shape.BoundBox.XLength:.3f}, "
        f"{print_shape.BoundBox.YLength:.3f}, "
        f"{print_shape.BoundBox.ZLength:.3f})"
    )
    print(f"  corrected_cap_overlap={cap_overlap:.6f}")

    App.closeDocument(source_doc.Name)


main()
