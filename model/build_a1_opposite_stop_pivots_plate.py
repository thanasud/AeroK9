"""Build one Bambu Lab A1 plate: 3 stops, 5 extended studs, 5 caps."""

import os

import FreeCAD as App
import Mesh
import Part


ROOT = os.path.abspath(os.getcwd())
STOP_SOURCE = os.path.join(
    ROOT, "model", "PipeRobotV2_XL430_OppositeSideStop_PREVIEW.FCStd"
)
STUD_SOURCE = os.path.join(ROOT, "model", "PivotStud_ExtendedPlus4mm.FCStd")
OUTPUT = os.path.join(
    ROOT, "model", "BambuA1_3OppositeStops_5ExtendedStuds_5PivotCaps.FCStd"
)
EXPORT_DIR = os.path.join(ROOT, "model", "exports")
OUTPUT_BASENAME = "BambuA1_PLA_3OppositeStops_5ExtendedPivotStuds_5PivotCaps"

BED_X = 256.0
BED_Y = 256.0
GAP = 8.0


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


def centered_row(shape, count, y, prefix, label, color, doc):
    bounds = shape.BoundBox
    width = count * bounds.XLength + (count - 1) * GAP
    x0 = (BED_X - width) / 2.0
    objects = []
    shapes = []
    for index in range(count):
        piece = shape.copy()
        piece.translate(
            App.Vector(x0 + index * (bounds.XLength + GAP), y, 0.0)
        )
        obj = add_shape(
            doc,
            f"{prefix}_{index + 1}",
            f"A1 PLATE - {label} {index + 1} of {count}",
            piece,
            color,
        )
        objects.append(obj)
        shapes.append(piece)
    return objects, shapes, y + bounds.YLength


def main():
    stop_doc = App.openDocument(STOP_SOURCE)
    stud_doc = App.openDocument(STUD_SOURCE)

    stop_obj = stop_doc.getObject("OppositeSideStop_1")
    stud_obj = stud_doc.getObject("PRINT_ORIENTED_PivotStud_ExtendedPlus4mm")
    cap_obj = stop_doc.getObject("PRINT_ORIENTED_PivotCap_RotatingFit")
    if None in (stop_obj, stud_obj, cap_obj):
        raise RuntimeError("required stop, extended PivotStud, or PivotCap missing")

    # The stop already has a wide flat Panel base, so Z-min/base-down is the
    # most stable quick-print orientation.  Stud and Cap retain their proven
    # flange-on-bed orientations from the earlier print files.
    stop_shape = moved_to_origin(stop_obj.Shape)
    stud_shape = moved_to_origin(stud_obj.Shape)
    cap_shape = moved_to_origin(cap_obj.Shape)

    out_doc = App.newDocument("BambuA1_OppositeStops_ExtendedPivots")
    all_objects = []
    all_shapes = []

    y = 18.0
    objects, shapes, y_end = centered_row(
        stop_shape, 3, y,
        "A1_OppositeStop", "Opposite-side reinforced stop",
        (0.72, 0.20, 0.88), out_doc,
    )
    all_objects.extend(objects)
    all_shapes.extend(shapes)

    y = y_end + 12.0
    objects, shapes, y_end = centered_row(
        stud_shape, 5, y,
        "A1_ExtendedPivotStud", "PivotStud extended +4 mm",
        (0.25, 0.80, 0.95), out_doc,
    )
    all_objects.extend(objects)
    all_shapes.extend(shapes)

    y = y_end + 12.0
    objects, shapes, y_end = centered_row(
        cap_shape, 5, y,
        "A1_PivotCap", "PivotCap rotating fit D4.80",
        (0.25, 0.90, 0.45), out_doc,
    )
    all_objects.extend(objects)
    all_shapes.extend(shapes)

    plate = Part.makeCompound(all_shapes)
    bounds = plate.BoundBox
    if bounds.XMin < 0 or bounds.YMin < 0 or bounds.XMax > BED_X or bounds.YMax > BED_Y:
        raise RuntimeError(
            f"plate exceeds A1 bed: X={bounds.XMin:.1f}..{bounds.XMax:.1f}, "
            f"Y={bounds.YMin:.1f}..{bounds.YMax:.1f}"
        )

    summary = add_shape(
        out_doc,
        "A1_Plate_Summary",
        "Bambu A1 PLA - 3 stops + 5 extended studs + 5 caps",
        plate,
        (0.70, 0.70, 0.72),
    )
    summary.Visibility = False
    summary.addProperty("App::PropertyString", "Contents", "A1 Plate")
    summary.Contents = (
        "3x OppositeSideStop; 5x PivotStud +4 mm; "
        "5x PivotCap rotating fit D4.80"
    )
    summary.addProperty("App::PropertyString", "PrintSetup", "A1 Plate")
    summary.PrintSetup = (
        "Bambu Lab A1; PLA; 0.20 mm; 4 walls; 35% gyroid; "
        "enable build-plate-only supports for the 3 tall stop brackets"
    )

    out_doc.recompute()
    out_doc.saveAs(OUTPUT)

    stl_path = os.path.join(EXPORT_DIR, OUTPUT_BASENAME + ".stl")
    three_mf_path = os.path.join(EXPORT_DIR, OUTPUT_BASENAME + ".3mf")
    Mesh.export(all_objects, stl_path)
    Mesh.export(all_objects, three_mf_path)

    print("A1_13_PART_PLATE_OK")
    print(f"  output={OUTPUT}")
    print(f"  stl={stl_path}")
    print(f"  3mf={three_mf_path}")
    print("  contents=3 stops, 5 PivotStud +4 mm, 5 PivotCap D4.80")
    print(
        f"  bounds={bounds.XLength:.2f} x {bounds.YLength:.2f} x "
        f"{bounds.ZLength:.2f} mm"
    )


main()
