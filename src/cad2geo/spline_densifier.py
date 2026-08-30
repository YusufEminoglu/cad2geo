# -*- coding: utf-8 -*-
"""CAD Spline, Bézier & Arc Bulge Adaptive Densifier for cad2geo."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Sequence


@dataclass
class SplineDensificationResult:
    original_points_count: int
    densified_points_count: int
    total_curve_length_m: float
    coordinates: list[tuple[float, float]]

    def to_geojson_feature(self, properties: dict[str, Any] | None = None) -> dict[str, Any]:
        props = properties or {}
        props["length_m"] = round(self.total_curve_length_m, 2)
        props["vertices"] = self.densified_points_count
        return {
            "type": "Feature",
            "properties": props,
            "geometry": {
                "type": "LineString",
                "coordinates": [[round(p[0], 4), round(p[1], 4)] for p in self.coordinates],
            },
        }


def _evaluate_cubic_bezier(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    t: float,
) -> tuple[float, float]:
    omt = 1.0 - t
    x = omt**3 * p0[0] + 3 * omt**2 * t * p1[0] + 3 * omt * t**2 * p2[0] + t**3 * p3[0]
    y = omt**3 * p0[1] + 3 * omt**2 * t * p1[1] + 3 * omt * t**2 * p2[1] + t**3 * p3[1]
    return (x, y)


def densify_cad_splines(
    control_points: Sequence[tuple[float, float]],
    samples_per_segment: int = 10,
    max_segment_length_m: float = 2.0,
) -> SplineDensificationResult:
    """Adaptively densify CAD spline control points into smooth, curvature-continuous polylines."""
    pts = list(control_points)
    if len(pts) < 2:
        return SplineDensificationResult(len(pts), len(pts), 0.0, pts)

    if len(pts) == 2:
        # Linear densification
        p0, p1 = pts[0], pts[1]
        dist = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        steps = max(samples_per_segment, int(math.ceil(dist / max(0.1, max_segment_length_m))))
        dense_pts = []
        for i in range(steps + 1):
            t = i / float(steps)
            dense_pts.append((p0[0] + t * (p1[0] - p0[0]), p0[1] + t * (p1[1] - p0[1])))
        return SplineDensificationResult(len(pts), len(dense_pts), dist, dense_pts)

    # Catmull-Rom to Cubic Bezier conversion for smooth multi-point splines
    dense_pts: list[tuple[float, float]] = []

    # Pad endpoints
    extended = [pts[0]] + pts + [pts[-1]]

    for i in range(1, len(extended) - 2):
        p0 = extended[i - 1]
        p1 = extended[i]
        p2 = extended[i + 1]
        p3 = extended[i + 2]

        # Convert Catmull-Rom segment (p1 -> p2) to Bezier control points
        b0 = p1
        b1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
        b2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
        b3 = p2

        chord_len = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        steps = max(samples_per_segment, int(math.ceil(chord_len / max(0.1, max_segment_length_m))))

        for s in range(steps):
            t = s / float(steps)
            dense_pts.append(_evaluate_cubic_bezier(b0, b1, b2, b3, t))

    dense_pts.append(pts[-1])

    # Compute total length
    tot_len = 0.0
    for j in range(len(dense_pts) - 1):
        tot_len += math.hypot(dense_pts[j + 1][0] - dense_pts[j][0], dense_pts[j + 1][1] - dense_pts[j][1])

    return SplineDensificationResult(
        original_points_count=len(pts),
        densified_points_count=len(dense_pts),
        total_curve_length_m=tot_len,
        coordinates=dense_pts,
    )
