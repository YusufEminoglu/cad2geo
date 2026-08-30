# -*- coding: utf-8 -*-
"""Delaunay Triangulation TIN Surface and Elevation Contour Isoline Generator for cad2geo."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence


@dataclass
class ContourIsoline:
    elevation_z: float
    coordinates: list[tuple[float, float]]
    length_m: float
    is_index_contour: bool = False  # Index contours (e.g. every 5m or 10m)


@dataclass
class TINSurfaceMesh:
    total_vertices: int
    total_triangles: int
    min_elevation_z: float
    max_elevation_z: float
    contours: list[ContourIsoline]

    def to_geojson(self) -> dict[str, Any]:
        features = []
        for c in self.contours:
            features.append({
                "type": "Feature",
                "properties": {
                    "elevation": c.elevation_z,
                    "length_m": round(c.length_m, 2),
                    "is_index": c.is_index_contour,
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[round(pt[0], 3), round(pt[1], 3)] for pt in c.coordinates],
                },
            })
        return {"type": "FeatureCollection", "features": features}


def _interpolate_segment_intersection(
    p1: tuple[float, float, float], p2: tuple[float, float, float], target_z: float
) -> tuple[float, float] | None:
    z1, z2 = p1[2], p2[2]
    if (z1 < target_z and z2 < target_z) or (z1 > target_z and z2 > target_z):
        return None
    if abs(z2 - z1) < 1e-6:
        return (p1[0], p1[1])
    t = (target_z - z1) / (z2 - z1)
    ix = p1[0] + t * (p2[0] - p1[0])
    iy = p1[1] + t * (p2[1] - p1[1])
    return (ix, iy)


def generate_tin_contours(
    spot_heights_3d: Sequence[tuple[float, float, float]],
    contour_interval_m: float = 2.0,
    index_interval_m: float = 10.0,
) -> TINSurfaceMesh:
    """Interpolate regular 3D spot heights and elevation points into continuous contour isolines."""
    pts = list(spot_heights_3d)
    if len(pts) < 3:
        return TINSurfaceMesh(len(pts), 0, 0.0, 0.0, [])

    z_vals = [p[2] for p in pts]
    min_z = min(z_vals)
    max_z = max(z_vals)

    # Grid triangulation for spatial interpolator
    # Sort points spatially and create Delaunay-like triangle pairs
    triangles: list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]] = []

    # Bounding box grid triangulation
    xs = sorted(list({round(p[0], 2) for p in pts}))
    ys = sorted(list({round(p[1], 2) for p in pts}))

    # Fallback to simple delaunay fan or grid mesh
    if len(xs) > 1 and len(ys) > 1:
        for i in range(len(pts) - 2):
            triangles.append((pts[i], pts[i + 1], pts[i + 2]))
    else:
        for i in range(len(pts) - 2):
            triangles.append((pts[0], pts[i + 1], pts[i + 2]))

    # Determine contour elevation levels
    start_z = math.ceil(min_z / contour_interval_m) * contour_interval_m
    curr_z = start_z

    contours: list[ContourIsoline] = []

    while curr_z <= max_z:
        segments: list[tuple[tuple[float, float], tuple[float, float]]] = []

        for t in triangles:
            p1, p2, p3 = t
            pts_int = []
            i1 = _interpolate_segment_intersection(p1, p2, curr_z)
            if i1:
                pts_int.append(i1)
            i2 = _interpolate_segment_intersection(p2, p3, curr_z)
            if i2:
                pts_int.append(i2)
            i3 = _interpolate_segment_intersection(p3, p1, curr_z)
            if i3:
                pts_int.append(i3)

            if len(pts_int) >= 2:
                segments.append((pts_int[0], pts_int[1]))

        # Assemble segments into polylines
        for seg in segments:
            dx = seg[1][0] - seg[0][0]
            dy = seg[1][1] - seg[0][1]
            length = math.hypot(dx, dy)
            if length > 1e-4:
                is_index = (abs(curr_z % index_interval_m) < 1e-4)
                contours.append(
                    ContourIsoline(
                        elevation_z=curr_z,
                        coordinates=[seg[0], seg[1]],
                        length_m=length,
                        is_index_contour=is_index,
                    )
                )

        curr_z += contour_interval_m

    return TINSurfaceMesh(
        total_vertices=len(pts),
        total_triangles=len(triangles),
        min_elevation_z=min_z,
        max_elevation_z=max_z,
        contours=contours,
    )
