"""Locate candidate circular edge clusters on the two XL430 end faces."""

import math

import Mesh


MESH_PATH = "/tmp/XL430_New.stl"
PLANES = (0.0, 46.5)
PLANE_TOLERANCE = 0.002
NEIGHBOR_DISTANCE = 0.55


def components(points):
    remaining = set(range(len(points)))
    result = []
    limit_squared = NEIGHBOR_DISTANCE**2
    while remaining:
        seed = remaining.pop()
        group = {seed}
        queue = [seed]
        while queue:
            current = queue.pop()
            x1, y1 = points[current]
            neighbors = []
            for candidate in remaining:
                x2, y2 = points[candidate]
                if (x1 - x2) ** 2 + (y1 - y2) ** 2 <= limit_squared:
                    neighbors.append(candidate)
            for candidate in neighbors:
                remaining.remove(candidate)
                group.add(candidate)
                queue.append(candidate)
        result.append([points[index] for index in group])
    return result


mesh = Mesh.Mesh(MESH_PATH)
for plane_z in PLANES:
    points = sorted(
        {
            (round(point.x, 4), round(point.y, 4))
            for point in mesh.Points
            if abs(point.z - plane_z) <= PLANE_TOLERANCE
        }
    )
    print(f"END_FACE z={plane_z:.1f} unique_points={len(points)}")
    candidates = []
    for group in components(points):
        if len(group) < 5:
            continue
        xs = [point[0] for point in group]
        ys = [point[1] for point in group]
        x_span = max(xs) - min(xs)
        y_span = max(ys) - min(ys)
        if 1.2 <= x_span <= 8.0 and 1.2 <= y_span <= 8.0:
            center_x = (min(xs) + max(xs)) / 2.0
            center_y = (min(ys) + max(ys)) / 2.0
            candidates.append(
                (center_x, center_y, x_span, y_span, len(group))
            )
    for center_x, center_y, x_span, y_span, count in sorted(candidates):
        print(
            "  candidate "
            f"center=({center_x:.4f}, {center_y:.4f}) "
            f"span=({x_span:.4f}, {y_span:.4f}) points={count}"
        )
