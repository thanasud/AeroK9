"""Build a print-ready XL430 two-hole head cradle on the AeroK9 swing arms.

This script is intended to run inside a FreeCAD Python console:

    exec(open("model/build_xl430_swingarm_mount.py").read())

The assembly embeds the official ROBOTIS XL430-W250 (New) STEP geometry,
not a rectangular placeholder.  It never overwrites PipeRobotV2.fcstd.
Generated parts are saved to a new FCStd assembly plus STEP/STL exports.
"""

import math
import os

import FreeCAD as App
import Mesh
import Part


ROOT = os.path.abspath(os.getcwd())
SOURCE = os.path.join(ROOT, "model", "PipeRobotV2.fcstd")
MOTOR_STEP = os.path.join(
    ROOT, "model", "reference", "XL430-W250-T_New_ROBOTIS.stp"
)
OUTPUT = os.path.join(
    ROOT, "model", "PipeRobotV2_XL430_RealMotor_NoCapsuleBoss.FCStd"
)
EXPORT_DIR = os.path.join(ROOT, "model", "exports")

# XL430-W250-T envelope in the existing assembly coordinate system.
# The motor output axis remains +Y, exactly as in PipeRobotV2.
MOTOR_X_MIN = -48.0
MOTOR_X_SIZE = 46.5
MOTOR_REAR_Y = -37.5
MOTOR_DEPTH = 34.0
MOTOR_Z_CENTER = 92.0
MOTOR_WIDTH = 28.5
OUTPUT_AXIS_X = -36.0
OUTPUT_AXIS_Z = 92.0

# The end at native STEP Y=+11.25 has two holes on a 16 mm pitch.  In the
# assembly that face is X=-48 and the exact official CAD centers become
# world (Y=-14.5, Z=84/100).  The opposite end has four holes.  This keeps
# the original head/tail orientation and the output shaft pointing +Y.
HOLE_PITCH_Z = 16.0
TWO_HOLE_Y_CENTER = -14.5
SCREW_CLEARANCE_DIAMETER = 2.7
SCREW_HEAD_DIAMETER = 5.6
CASE_HOLE_MAX_DEPTH = 4.0

# PETG-oriented print allowances.
FRAME_THICKNESS = 5.0
COUNTERBORE_DEPTH = 3.2
BODY_CLEARANCE = 0.30
SIDE_LIP_DEPTH = 4.0
REAR_FEATURE_CLEARANCE = 0.35


def box(x_size, y_size, z_size, x, y, z):
    return Part.makeBox(x_size, y_size, z_size, App.Vector(x, y, z))


def make_mount_frame():
    """Return the integral two-hole head frame before fusing to the arm."""
    motor_front_y = MOTOR_REAR_Y + MOTOR_DEPTH
    motor_z_min = MOTOR_Z_CENTER - MOTOR_WIDTH / 2.0
    motor_z_max = MOTOR_Z_CENTER + MOTOR_WIDTH / 2.0

    # Head plate: the motor's two-hole end face at X=-48 rests against X=-48.
    # The extra perimeter gives the printed plate useful edge distance.
    plate_z_min = motor_z_min - 2.25
    plate_z_size = MOTOR_WIDTH + 4.50
    plate_y_min = -38.2  # overlaps the rear spine by 0.5 mm for a clean fuse
    plate_y_size = motor_front_y - plate_y_min
    plate = box(
        FRAME_THICKNESS,
        plate_y_size,
        plate_z_size,
        MOTOR_X_MIN - FRAME_THICKNESS,
        plate_y_min,
        plate_z_min,
    )

    # Two screw paths. Counterbores leave 1.8 mm of printed material under
    # the head, so M2.5x4 screws engage about 2.2 mm into the case and remain
    # safely below the 4 mm maximum case-hole depth.
    hole_y_center = TWO_HOLE_Y_CENTER
    hole_z_center = MOTOR_Z_CENTER
    for z in (
        hole_z_center - HOLE_PITCH_Z / 2.0,
        hole_z_center + HOLE_PITCH_Z / 2.0,
    ):
        through = Part.makeCylinder(
            SCREW_CLEARANCE_DIAMETER / 2.0,
            FRAME_THICKNESS + 0.4,
            App.Vector(MOTOR_X_MIN - FRAME_THICKNESS - 0.2, hole_y_center, z),
            App.Vector(1, 0, 0),
        )
        counterbore = Part.makeCylinder(
            SCREW_HEAD_DIAMETER / 2.0,
            COUNTERBORE_DEPTH + 0.2,
            App.Vector(MOTOR_X_MIN - FRAME_THICKNESS - 0.2, hole_y_center, z),
            App.Vector(1, 0, 0),
        )
        plate = plate.cut(through.fuse(counterbore))

    # Short locating lips key against the two 28.5 mm case edges.  They carry
    # shear and back up the two screws against case rotation. A 0.30 mm gap
    # side prevents a tight FDM fit from distorting the plastic motor case.
    lower_lip_top = motor_z_min - BODY_CLEARANCE
    upper_lip_bottom = motor_z_max + BODY_CLEARANCE
    lower_lip = box(
        SIDE_LIP_DEPTH + 0.2,
        MOTOR_DEPTH,
        lower_lip_top - plate_z_min,
        MOTOR_X_MIN - 0.2,
        MOTOR_REAR_Y,
        plate_z_min,
    )
    upper_lip = box(
        SIDE_LIP_DEPTH + 0.2,
        MOTOR_DEPTH,
        plate_z_min + plate_z_size - upper_lip_bottom,
        MOTOR_X_MIN - 0.2,
        MOTOR_REAR_Y,
        upper_lip_bottom,
    )

    return plate.fuse(lower_lip).fuse(upper_lip).removeSplitter()


def make_reinforcement():
    """Create the root spine and two ribs that join the frame to the arm."""
    motor_z_min = MOTOR_Z_CENTER - MOTOR_WIDTH / 2.0
    plate_z_min = motor_z_min - 2.25
    plate_z_max = MOTOR_Z_CENTER + MOTOR_WIDTH / 2.0 + 2.25

    # This block overlaps the original arm and the mount plate.  It also
    # closes the very thin edge left by the original, incorrect circular pad.
    spine = box(10.0, 9.3, plate_z_max - plate_z_min, -53.0, -47.0, plate_z_min)

    # Ribs live outside the motor width, so they stiffen the 34 mm cantilever
    # without blocking the motor, its cable ports, or any screw driver path.
    rib_profile = Part.makePolygon(
        [
            App.Vector(-56.0, -38.2, 0),
            App.Vector(-48.0, -38.2, 0),
            App.Vector(-53.0, -20.0, 0),
            App.Vector(-56.0, -38.2, 0),
        ]
    )
    rib_face = Part.Face(rib_profile)
    lower_rib = rib_face.extrude(App.Vector(0, 0, 2.5))
    lower_rib.translate(App.Vector(0, 0, plate_z_min))
    upper_rib = rib_face.extrude(App.Vector(0, 0, 2.5))
    upper_rib.translate(App.Vector(0, 0, plate_z_max - 2.5))

    return spine.fuse(lower_rib).fuse(upper_rib).removeSplitter()


def make_legacy_motor_hole_closure():
    """Close the obsolete 24 mm through-hole behind the motor."""
    return Part.makeCylinder(
        13.0,
        9.2,
        App.Vector(OUTPUT_AXIS_X, -47.1, OUTPUT_AXIS_Z),
        App.Vector(0, 1, 0),
    )


def make_rear_motor_clearance_pocket():
    """Clear the real rear cover/idler boss while retaining a closed back.

    The official STEP protrudes from Y=-37.5 to Y=-40.5 behind the nominal
    34 mm case.  This blind pocket adds 0.35 mm FDM clearance around the
    20.5 mm square rear feature.  More than 6 mm of the closure remains
    behind it, so the obsolete through-hole stays structurally closed.
    """
    return box(
        21.2,
        3.5,
        21.2,
        -47.35,
        -40.85,
        81.4,
    )


def make_obsolete_capsule_boss_cutter():
    """Remove the selected 4 mm-deep capsule boss from the arm underside.

    The feature is bounded by the two R4.5 end arcs whose centers are taken
    from SwingArm_XL430_1 Face13/Face15.  SwingArm_XL430_2 Face17/Face34 are
    the user-selected corresponding side and bottom faces.  Cutting only
    Y=-47..-43 makes the boss flush with the 5 mm main arm body without
    touching the pivot ring or XL430 mount.
    """
    center_a = (-1.8461538461538467, 77.76923076923077)
    center_b = (-14.769230769230774, 83.15384615384616)
    radius = 4.52  # 0.02 mm boolean tolerance beyond the original R4.50
    delta_x = center_b[0] - center_a[0]
    delta_z = center_b[1] - center_a[1]
    length = math.hypot(delta_x, delta_z)
    normal_x = -delta_z / length
    normal_z = delta_x / length
    cutter_y = -47.1
    cutter_depth = 4.1
    corners = [
        App.Vector(
            center_a[0] + radius * normal_x,
            cutter_y,
            center_a[1] + radius * normal_z,
        ),
        App.Vector(
            center_b[0] + radius * normal_x,
            cutter_y,
            center_b[1] + radius * normal_z,
        ),
        App.Vector(
            center_b[0] - radius * normal_x,
            cutter_y,
            center_b[1] - radius * normal_z,
        ),
        App.Vector(
            center_a[0] - radius * normal_x,
            cutter_y,
            center_a[1] - radius * normal_z,
        ),
    ]
    bridge = Part.Face(Part.makePolygon(corners + [corners[0]])).extrude(
        App.Vector(0, cutter_depth, 0)
    )
    end_a = Part.makeCylinder(
        radius,
        cutter_depth,
        App.Vector(center_a[0], cutter_y, center_a[1]),
        App.Vector(0, 1, 0),
    )
    end_b = Part.makeCylinder(
        radius,
        cutter_depth,
        App.Vector(center_b[0], cutter_y, center_b[1]),
        App.Vector(0, 1, 0),
    )
    return bridge.fuse(end_a).fuse(end_b).removeSplitter()


def add_shape(doc, name, label, shape, color):
    obj = doc.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    obj.addProperty("App::PropertyString", "DesignIntent", "XL430 Mount")
    obj.DesignIntent = "Fix XL430 stator at its two-hole head using two screws plus keyed rails; shaft faces +Y"
    obj.addProperty("App::PropertyString", "PrintMaterial", "XL430 Mount")
    obj.PrintMaterial = "PETG; 5 perimeters; 40-50% gyroid; layers across rib thickness"
    obj.addProperty("App::PropertyString", "Fasteners", "XL430 Mount")
    obj.Fasteners = "2x M2.5x4 thread-forming screws; do not exceed 4 mm case depth"
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = color
    return obj


def load_official_motor_reference():
    """Load and place the official ROBOTIS XL430-W250 (New) STEP model."""
    motor = Part.read(MOTOR_STEP)
    native = motor.BoundBox
    expected_native = (28.5, 46.5, 40.9)
    actual_native = (native.XLength, native.YLength, native.ZLength)
    if any(abs(actual - expected) > 0.02 for actual, expected in zip(actual_native, expected_native)):
        raise RuntimeError(
            "unexpected official motor CAD bounds: "
            f"actual={actual_native} expected={expected_native}"
        )

    # Native STEP axes: X=28.5 width, Y=46.5 height, Z=output depth.
    # Assembly axes: native -Y -> world +X, native +Z -> world +Y,
    # native -X -> world +Z.  Translation holds the shaft center at
    # world X=-36, Z=92 and keeps the two-hole end at X=-48.
    matrix = App.Matrix()
    matrix.A11, matrix.A12, matrix.A13 = 0.0, -1.0, 0.0
    matrix.A21, matrix.A22, matrix.A23 = 0.0, 0.0, 1.0
    matrix.A31, matrix.A32, matrix.A33 = -1.0, 0.0, 0.0
    motor.Placement = App.Placement(
        App.Vector(-36.75, -20.5, MOTOR_Z_CENTER),
        App.Rotation(matrix),
    )

    placed = motor.BoundBox
    expected_placed = (-48.0, -1.5, -40.5, 0.4, 77.75, 106.25)
    actual_placed = (
        placed.XMin, placed.XMax, placed.YMin,
        placed.YMax, placed.ZMin, placed.ZMax,
    )
    if any(abs(actual - expected) > 0.02 for actual, expected in zip(actual_placed, expected_placed)):
        raise RuntimeError(
            "official motor placement failed: "
            f"actual={actual_placed} expected={expected_placed}"
        )
    return motor


def rotated(shape, angle_degrees):
    result = shape.copy()
    result.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), angle_degrees)
    return result


def moved_to_origin(shape):
    result = shape.copy()
    bounds = result.BoundBox
    result.translate(App.Vector(-bounds.XMin, -bounds.YMin, -bounds.ZMin))
    return result


def intersection_volume(a, b):
    common = a.common(b)
    return common.Volume if not common.isNull() else 0.0


def main():
    if not os.path.exists(SOURCE):
        raise RuntimeError(f"source file not found: {SOURCE}")
    if not os.path.exists(MOTOR_STEP):
        raise RuntimeError(f"official ROBOTIS motor STEP not found: {MOTOR_STEP}")
    if not os.path.isdir(EXPORT_DIR):
        raise RuntimeError(f"export directory not found: {EXPORT_DIR}")

    doc = App.openDocument(SOURCE)
    source_arm = doc.getObject("SwingArm_1")
    if source_arm is None:
        raise RuntimeError("SwingArm_1 is missing from PipeRobotV2.fcstd")

    mount = make_mount_frame()
    reinforcement = make_reinforcement()
    legacy_hole_closure = make_legacy_motor_hole_closure()
    rear_motor_clearance = make_rear_motor_clearance_pocket()
    capsule_boss_cutter = make_obsolete_capsule_boss_cutter()
    arm_before_capsule_trim = (
        source_arm.Shape
        .fuse(legacy_hole_closure)
        .fuse(reinforcement)
        .fuse(mount)
        .removeSplitter()
        .cut(rear_motor_clearance)
        .removeSplitter()
    )
    capsule_removed_volume = intersection_volume(
        arm_before_capsule_trim, capsule_boss_cutter
    )
    final_arm_1_shape = (
        arm_before_capsule_trim.cut(capsule_boss_cutter).removeSplitter()
    )
    if not final_arm_1_shape.isValid() or len(final_arm_1_shape.Solids) != 1:
        raise RuntimeError(
            "generated SwingArm is not one valid solid: "
            f"valid={final_arm_1_shape.isValid()} solids={len(final_arm_1_shape.Solids)}"
        )

    # The selected capsule must be removed without changing either endpoint.
    pivot_probe = Part.makeCylinder(
        12.0,
        9.0,
        App.Vector(36.0, -47.0, 62.0),
        App.Vector(0, 1, 0),
    )
    motor_mount_probe = box(35.0, 44.0, 38.0, -56.0, -47.0, 73.0)
    for label, probe in (
        ("pivot", pivot_probe),
        ("motor mount", motor_mount_probe),
    ):
        before = intersection_volume(arm_before_capsule_trim, probe)
        after = intersection_volume(final_arm_1_shape, probe)
        if abs(before - after) > 0.001:
            raise RuntimeError(
                f"capsule trim changed {label}: before={before:.6f} after={after:.6f}"
            )

    motor_1_shape = load_official_motor_reference()
    arm_motor_overlap = intersection_volume(final_arm_1_shape, motor_1_shape)
    mount_motor_overlap = intersection_volume(mount, motor_1_shape)
    if arm_motor_overlap > 0.01 or mount_motor_overlap > 0.01:
        raise RuntimeError(
            "motor clearance failed: "
            f"arm overlap={arm_motor_overlap:.6f}, mount overlap={mount_motor_overlap:.6f}"
        )

    # Prove that the screw axes match the blind pilot holes in the ROBOTIS
    # CAD.  The probe stays 0.1 mm clear of the nominal 2.1 mm pilot wall.
    screw_axis_overlap = 0.0
    for z in (
        MOTOR_Z_CENTER - HOLE_PITCH_Z / 2.0,
        MOTOR_Z_CENTER + HOLE_PITCH_Z / 2.0,
    ):
        pilot_probe = Part.makeCylinder(
            0.95,
            3.8,
            App.Vector(MOTOR_X_MIN - 0.01, TWO_HOLE_Y_CENTER, z),
            App.Vector(1, 0, 0),
        )
        screw_axis_overlap += intersection_volume(pilot_probe, motor_1_shape)
    if screw_axis_overlap > 0.001:
        raise RuntimeError(
            "two-hole screw axes do not match official motor CAD: "
            f"overlap={screw_axis_overlap:.6f}"
        )

    arm_objects = []
    motor_objects = []
    for index, angle in enumerate((0.0, 120.0, 240.0), start=1):
        arm_obj = add_shape(
            doc,
            f"SwingArm_XL430_{index}",
            f"SwingArm XL430 No Capsule Boss {index}",
            rotated(final_arm_1_shape, angle),
            (0.95, 0.65, 0.15),
        )
        motor_obj = add_shape(
            doc,
            f"REF_XL430_Official_{index}",
            f"REF XL430-W250-T Official ROBOTIS STEP {index}",
            rotated(motor_1_shape, angle),
            (0.18, 0.18, 0.20),
        )
        motor_obj.addProperty("App::PropertyString", "CADSource", "XL430 Motor")
        motor_obj.CADSource = "ROBOTIS XL430-W250 (New) official STEP, download no. 773"
        arm_objects.append(arm_obj)
        motor_objects.append(motor_obj)

    coupon_obj = add_shape(
        doc,
        "XL430_2HoleHeadMount_FitCoupon",
        "PRINT FIRST - XL430 Two-Hole Head Mount Fit Coupon",
        mount,
        (0.20, 0.75, 0.35),
    )
    coupon_obj.addProperty("App::PropertyString", "Purpose", "XL430 Mount")
    coupon_obj.Purpose = "Verify two M2.5 holes at 16 mm pitch and keyed case fit before printing three arms"

    spec = doc.addObject("App::FeaturePython", "XL430_Mount_Specification")
    spec.Label = "XL430 Mount - dimensions and assembly notes"
    properties = {
        "MotorEnvelope": "28.5 W x 46.5 H x 34 D mm",
        "MotorCAD": "Embedded official ROBOTIS XL430-W250 (New) STEP; 25 solids",
        "CorrectedAxisMapping": "Assembly X=46.5, Y(output axis)=34, Z=28.5 mm",
        "OutputDirection": "+Y for arm 1; rotated 120/240 deg about robot X for arms 2/3",
        "HeadTailOrientation": "Two-hole end at X=-48 near shaft; four-hole end points toward +X/pivot",
        "HeadHolePattern": "2 holes, 16 mm pitch; exact centers Y=-14.5, Z=84/100 from official STEP",
        "CasePilotHole": "2.1 mm diameter, 4.0 mm maximum depth",
        "LegacyRearHole": "Obsolete 24 mm through-hole is closed; blind pocket clears real rear cover/idler boss",
        "RearFeatureClearance": f"{REAR_FEATURE_CLEARANCE:.2f} mm around official STEP rear feature",
        "CapsuleBoss": (
            "Removed selected underside capsule boss flush to Y=-43; "
            f"removed {capsule_removed_volume:.2f} mm^3"
        ),
        "FrameClearance": f"{BODY_CLEARANCE:.2f} mm per locating side",
        "PrintOrientation": "Arm rear face and coupon outer plate face are pre-oriented onto Z=0",
        "AssemblyOrder": "Print coupon -> verify screws/fit -> print 3 identical complete arms",
    }
    for prop_name, value in properties.items():
        spec.addProperty("App::PropertyString", prop_name, "XL430 Mount")
        setattr(spec, prop_name, value)

    # Hide only the obsolete arm/motor/wheel references. Other assembly parts
    # remain untouched in the generated copy.
    for index in range(1, 4):
        for old_name in (f"SwingArm_{index}", f"REF_Motor_{index}", f"REF_Wheel_{index}"):
            old_obj = doc.getObject(old_name)
            if old_obj is not None:
                old_obj.Visibility = False

    doc.recompute()

    # Export copies are pre-oriented for FDM.  The complete arm's original
    # rear plane (Y=-47) lies on the bed; the fit coupon's outer plate face
    # (X=-53) lies on the bed.  Assembly-oriented objects above stay unchanged.
    print_arm_shape = final_arm_1_shape.copy()
    print_arm_shape.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 90.0)
    print_arm_shape = moved_to_origin(print_arm_shape)
    print_arm_obj = add_shape(
        doc,
        "PRINT_ORIENTED_SwingArm_XL430_NoCapsule",
        "PRINT - SwingArm XL430 No Capsule Boss (rear face on bed)",
        print_arm_shape,
        (0.35, 0.80, 0.95),
    )
    print_arm_obj.Visibility = False

    print_coupon_shape = mount.copy()
    print_coupon_shape.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), -90.0)
    print_coupon_shape = moved_to_origin(print_coupon_shape)
    print_coupon_obj = add_shape(
        doc,
        "PRINT_ORIENTED_XL430_FitCoupon",
        "PRINT FIRST - XL430 Fit Coupon (outer face on bed)",
        print_coupon_shape,
        (0.25, 0.90, 0.45),
    )
    print_coupon_obj.Visibility = False

    doc.recompute()
    doc.saveAs(OUTPUT)

    arm_stl = os.path.join(EXPORT_DIR, "SwingArm_XL430_NoCapsuleBoss_PRINT.stl")
    arm_step = os.path.join(EXPORT_DIR, "SwingArm_XL430_NoCapsuleBoss.step")
    coupon_stl = os.path.join(EXPORT_DIR, "XL430_RealMotorVerified_FitCoupon_PRINT_FIRST.stl")
    Mesh.export([print_arm_obj], arm_stl)
    Part.export([arm_objects[0]], arm_step)
    Mesh.export([print_coupon_obj], coupon_stl)

    print("XL430_MOUNT_BUILD_OK")
    print(f"  output={OUTPUT}")
    print(f"  arm_stl={arm_stl}")
    print(f"  arm_step={arm_step}")
    print(f"  coupon_stl={coupon_stl}")
    print(
        "  final_arm "
        f"valid={final_arm_1_shape.isValid()} solids={len(final_arm_1_shape.Solids)} "
        f"volume={final_arm_1_shape.Volume:.3f}"
    )
    print(
        "  print_bounds "
        f"arm=({print_arm_shape.BoundBox.XLength:.3f}, "
        f"{print_arm_shape.BoundBox.YLength:.3f}, {print_arm_shape.BoundBox.ZLength:.3f}) "
        f"coupon=({print_coupon_shape.BoundBox.XLength:.3f}, "
        f"{print_coupon_shape.BoundBox.YLength:.3f}, {print_coupon_shape.BoundBox.ZLength:.3f})"
    )
    print(
        "  clearance "
        f"arm_motor_overlap={arm_motor_overlap:.6f} "
        f"mount_motor_overlap={mount_motor_overlap:.6f} "
        f"screw_axis_overlap={screw_axis_overlap:.6f}"
    )
    print(f"  capsule_removed_volume={capsule_removed_volume:.6f}")
    print("  shaft_direction=(0,+1,0)")


main()
