"""Create a quick FreeCAD preview of an opposite-side SwingArm stop.

This is intentionally a design preview, not a print-release build.  The new
bracket bolts to two existing Panel holes and places a reinforced sloped stop
above the SwingArm so it reacts the opposite rotation direction.
"""

import os

import FreeCAD as App
import Part


ROOT = os.path.abspath(os.getcwd())
SOURCE = os.path.join(ROOT, "model", "PipeRobotV2_XL430_PanelReverseStop.FCStd")
OUTPUT = os.path.join(
    ROOT, "model", "PipeRobotV2_XL430_OppositeSideStop_PREVIEW.FCStd"
)

BASE_Z = 38.0
MOUNT_HOLES = ((0.0, -20.0), (0.0, 0.0))
M3_CLEARANCE_D = 3.8
M3_COUNTERBORE_D = 7.0

# Measured upper edge of the arm in the selected clear region X=2..12.
ARM_TOP_Z_AT_X0 = 87.18
ARM_SLOPE = -0.42
ARM_GAP = 2.0
PAD_THICKNESS = 6.0


def add_shape(doc, name, label, shape, color):
    obj = doc.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = color
        obj.ViewObject.LineColor = (0.20, 0.08, 0.25)
    return obj


def face(points):
    return Part.Face(Part.makePolygon(points + [points[0]]))


def pad_lower_z(x):
    return ARM_TOP_Z_AT_X0 + ARM_SLOPE * x + ARM_GAP


def make_opposite_stop():
    # Six-millimetre base; the two large counterbores remain visible and easy
    # to reach with a hex key after assembly.
    base = Part.makeBox(18.0, 30.0, 6.0, App.Vector(-4.0, -25.0, BASE_Z))
    for x, y in MOUNT_HOLES:
        through = Part.makeCylinder(
            M3_CLEARANCE_D / 2.0,
            6.4,
            App.Vector(x, y, BASE_Z - 0.2),
        )
        counterbore = Part.makeCylinder(
            M3_COUNTERBORE_D / 2.0,
            3.2,
            App.Vector(x, y, BASE_Z + 2.9),
        )
        base = base.cut(through.fuse(counterbore))

    # Sloped upper stop follows the top of the SwingArm.  Reverse force in the
    # new wheel direction pushes the arm into the lower face of this rail.
    x0, x1 = 2.0, 12.0
    pad_points = [
        App.Vector(x0, -45.0, pad_lower_z(x0)),
        App.Vector(x1, -45.0, pad_lower_z(x1)),
        App.Vector(x1, -45.0, pad_lower_z(x1) + PAD_THICKNESS),
        App.Vector(x0, -45.0, pad_lower_z(x0) + PAD_THICKNESS),
    ]
    pad = face(pad_points).extrude(App.Vector(0, 8.0, 0))

    # Twin 4 mm triangular side plates create a direct load path from the
    # upper rail to the long two-bolt base.  The broad profile resists both
    # bending and twisting when the wheel changes direction.
    rib_profile_yz = [
        (-25.0, BASE_Z + 5.0),
        (5.0, BASE_Z + 5.0),
        (-18.0, BASE_Z + 13.0),
        (-36.5, 90.0),
        (-40.5, 94.0),
        (-45.0, 94.0),
        (-37.0, 86.0),
        (-27.0, BASE_Z + 13.0),
    ]
    ribs = []
    for rib_x0 in (2.0, 8.0):
        points = [App.Vector(rib_x0, y, z) for y, z in rib_profile_yz]
        ribs.append(face(points).extrude(App.Vector(4.0, 0, 0)))

    # Cross-tie stays inside the clear side of the motor and joins both ribs.
    tie = Part.makeBox(10.0, 8.0, 7.0, App.Vector(2.0, -37.0, 86.0))

    result = base.fuse(ribs[0]).fuse(ribs[1]).fuse(tie).fuse(pad)
    result = result.removeSplitter()
    if not result.isValid() or len(result.Solids) != 1:
        raise RuntimeError("opposite stop preview did not form one valid solid")
    return result


def rotate_about_robot(shape, degrees):
    result = shape.copy()
    result.rotate(App.Vector(), App.Vector(1, 0, 0), degrees)
    return result


def main():
    doc = App.openDocument(SOURCE)

    # Keep the first concept in the file but hide it so comparison remains
    # possible from the Model tree.
    for index in (1, 2, 3):
        old = doc.getObject(f"PanelReverseStop_{index}")
        if old:
            old.Visibility = False

    stop = make_opposite_stop()
    for index, angle in enumerate((0.0, 120.0, 240.0), 1):
        obj = add_shape(
            doc,
            f"OppositeSideStop_{index}",
            f"PREVIEW - Opposite-side reinforced stop {index}",
            rotate_about_robot(stop, angle),
            (0.72, 0.20, 0.88),
        )
        obj.addProperty("App::PropertyString", "Concept", "Opposite Stop")
        obj.Concept = (
            "Upper-side SwingArm stop; 2x M3 Panel mount; twin 4 mm ribs; "
            "6 mm contact rail"
        )

    doc.recompute()
    doc.saveAs(OUTPUT)
    print("OPPOSITE_SIDE_STOP_PREVIEW_OK")
    print(f"  output={OUTPUT}")
    print("  mount=2x M3 at Panel centres (0,-20) and (0,0)")
    print("  structure=6 mm base, twin 4 mm ribs, 6 mm upper stop rail")


main()
