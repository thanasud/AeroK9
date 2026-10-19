#!/usr/bin/env python3
"""Report placement, bounds, and cylindrical geometry for FreeCAD parts.

Run with FreeCADCmd, for example:
  freecadcmd model/inspect_freecad_geometry.py model/PipeRobotV2.fcstd SwingArm_1
"""

import math
import os
import sys

import FreeCAD as App


def vector_text(vector):
    return f"({vector.x:.4f}, {vector.y:.4f}, {vector.z:.4f})"


def bounds_text(bounds):
    return (
        f"min=({bounds.XMin:.4f}, {bounds.YMin:.4f}, {bounds.ZMin:.4f}) "
        f"max=({bounds.XMax:.4f}, {bounds.YMax:.4f}, {bounds.ZMax:.4f}) "
        f"size=({bounds.XLength:.4f}, {bounds.YLength:.4f}, {bounds.ZLength:.4f})"
    )


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: inspect_freecad_geometry.py FILE [OBJECT ...]")

    path = os.path.abspath(sys.argv[1])
    requested = set(sys.argv[2:])
    doc = App.openDocument(path)
    try:
        objects = [obj for obj in doc.Objects if hasattr(obj, "Shape")]
        if requested:
            objects = [
                obj
                for obj in objects
                if obj.Name in requested or obj.Label in requested
            ]

        for obj in objects:
            shape = obj.Shape
            placed = shape.copy()
            placed.Placement = obj.getGlobalPlacement()
            placement = obj.getGlobalPlacement()
            print(f"OBJECT {obj.Name} label={obj.Label!r}")
            print(
                "  placement "
                f"base={vector_text(placement.Base)} "
                f"axis={vector_text(placement.Rotation.Axis)} "
                f"angle={math.degrees(placement.Rotation.Angle):.4f}deg"
            )
            print(f"  local_bounds  {bounds_text(shape.BoundBox)}")
            print(f"  global_bounds {bounds_text(placed.BoundBox)}")
            print(
                f"  solids={len(shape.Solids)} faces={len(shape.Faces)} "
                f"edges={len(shape.Edges)} volume={shape.Volume:.4f}"
            )

            cylinders = []
            for index, face in enumerate(shape.Faces, start=1):
                surface = face.Surface
                if hasattr(surface, "Radius") and hasattr(surface, "Axis"):
                    radius = float(surface.Radius)
                    if radius <= 20.0:
                        center = getattr(surface, "Center", App.Vector())
                        cylinders.append((index, radius, center, surface.Axis))

            for index, radius, center, axis in sorted(
                cylinders, key=lambda row: (round(row[1], 5), row[0])
            ):
                print(
                    f"  cylinder face={index} radius={radius:.4f} "
                    f"center={vector_text(center)} axis={vector_text(axis)}"
                )
    finally:
        App.closeDocument(doc.Name)


# FreeCAD executes a .py startup file with a tool-specific module name rather
# than ``__main__``, so invoke the entry point unconditionally.
main()
