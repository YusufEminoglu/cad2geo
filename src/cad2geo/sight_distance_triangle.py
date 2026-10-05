# -*- coding: utf-8 -*-
"""Highway Intersection Sight Distance Triangle (AASHTO / Karayolları) Analyzer for cad2geo."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Sequence


@dataclass
class IntersectionLegProfile:
    leg_id: str
    design_speed_kmh: float
    grade_pct: float = 0.0  # + uphill, - downhill
    is_major_road: bool = True


@dataclass
class SightTriangleResult:
    is_clear_of_obstructions: bool
    approach_sight_distance_major_m: float
    departure_sight_distance_minor_m: float
    sight_triangle_polygon: list[tuple[float, float]]
    obstructing_features_count: int
    obstructing_feature_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "clear": self.is_clear_of_obstructions,
            "sight_dist_major_m": round(self.approach_sight_distance_major_m, 2),
            "sight_dist_minor_m": round(self.departure_sight_distance_minor_m, 2),
            "obstructions": self.obstructing_features_count,
        }


def _point_in_polygon(x: float, y: float, poly: Sequence[tuple[float, float]]) -> bool:
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def evaluate_intersection_sight_triangles(
    intersection_vertex_2d: tuple[float, float],
    major_road_direction_deg: float,
    minor_road_direction_deg: float,
    major_leg: IntersectionLegProfile,
    minor_leg: IntersectionLegProfile,
    cad_obstacles: Sequence[dict[str, Any]] | None = None,
) -> SightTriangleResult:
    """Compute AASHTO Case B (Stop-controlled intersection) Sight Triangles and detect line-of-sight obstructions."""
    ix, iy = intersection_vertex_2d

    # AASHTO Stopping Sight Distance / Departure Sight Distance formula:
    # d_major = 0.278 * V_major * t_gap (where t_gap = 7.5s for passenger car passenger turns)
    t_gap = 7.5
    d_major = 0.278 * major_leg.design_speed_kmh * t_gap

    # Decision setback distance along minor road (usually 4.4m from edge of major road traveled way)
    d_minor = 4.4 + 3.0  # ~7.4m from intersection vertex

    # Major road sight point (A)
    rad_maj = math.radians(major_road_direction_deg)
    ax = ix + d_major * math.cos(rad_maj)
    ay = iy + d_major * math.sin(rad_maj)

    # Minor road driver eye point (B)
    rad_min = math.radians(minor_road_direction_deg)
    bx = ix + d_minor * math.cos(rad_min)
    by = iy + d_minor * math.sin(rad_min)

    # Triangle vertices: B (driver eye), (ix, iy) (junction center), A (approaching vehicle)
    triangle = [(bx, by), (ix, iy), (ax, ay), (bx, by)]

    obstructing_ids: list[str] = []
    if cad_obstacles:
        for obs in cad_obstacles:
            oid = str(obs.get("id", "OBS"))
            pos = obs.get("position", (0.0, 0.0))
            if _point_in_polygon(pos[0], pos[1], triangle):
                obstructing_ids.append(oid)

    return SightTriangleResult(
        is_clear_of_obstructions=(len(obstructing_ids) == 0),
        approach_sight_distance_major_m=d_major,
        departure_sight_distance_minor_m=d_minor,
        sight_triangle_polygon=triangle,
        obstructing_features_count=len(obstructing_ids),
        obstructing_feature_ids=obstructing_ids,
    )
