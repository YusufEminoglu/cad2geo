# -*- coding: utf-8 -*-
"""CAD Text & MText Spatial Annotation Linker for cad2geo."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Sequence

from .spatial_ops import point_in_polygon


@dataclass
class MatchedPolygonAnnotation:
    polygon_index: int
    polygon_layer: str
    matched_text: str
    text_position: tuple[float, float]
    match_type: str  # 'CONTAINS' (inside polygon) or 'NEAREST_CENTROID'
    distance_to_centroid: float


@dataclass
class AnnotationMatchResult:
    total_annotations_processed: int
    matched_count: int
    unmatched_count: int
    matches: list[MatchedPolygonAnnotation]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_annotations": self.total_annotations_processed,
            "matched_count": self.matched_count,
            "unmatched_count": self.unmatched_count,
            "match_rate_pct": round((self.matched_count / max(1, self.total_annotations_processed)) * 100.0, 1),
            "matches": [
                {
                    "poly_idx": m.polygon_index,
                    "layer": m.polygon_layer,
                    "text": m.matched_text,
                    "type": m.match_type,
                    "dist": round(m.distance_to_centroid, 2),
                }
                for m in self.matches
            ],
        }


def _calc_centroid(polygon: Sequence[tuple[float, float]]) -> tuple[float, float]:
    if not polygon:
        return (0.0, 0.0)
    sx = sum(p[0] for p in polygon)
    sy = sum(p[1] for p in polygon)
    return (sx / len(polygon), sy / len(polygon))


def link_annotations_to_polygons(
    polygons: list[dict[str, Any]],  # List of dicts with 'coordinates': list[tuple[float, float]], 'layer': str
    annotations: list[dict[str, Any]],  # List of dicts with 'text': str, 'position': tuple[float, float]
    max_search_radius: float = 50.0,
) -> AnnotationMatchResult:
    """Spatially associate floating CAD text/MText labels with their enclosing or nearest parcel boundaries."""
    matches: list[MatchedPolygonAnnotation] = []
    matched_cnt = 0
    unmatched_cnt = 0

    poly_centroids = [_calc_centroid(p.get("coordinates", [])) for p in polygons]

    for ann in annotations:
        txt = str(ann.get("text", "")).strip()
        pos = ann.get("position", (0.0, 0.0))
        if not txt:
            continue

        matched = False

        # 1. Point-in-Polygon check
        for p_idx, p_data in enumerate(polygons):
            coords = p_data.get("coordinates", [])
            if len(coords) >= 3 and point_in_polygon(pos[0], pos[1], coords):
                c_dist = math.hypot(pos[0] - poly_centroids[p_idx][0], pos[1] - poly_centroids[p_idx][1])
                matches.append(
                    MatchedPolygonAnnotation(
                        polygon_index=p_idx,
                        polygon_layer=str(p_data.get("layer", "0")),
                        matched_text=txt,
                        text_position=pos,
                        match_type="CONTAINS",
                        distance_to_centroid=c_dist,
                    )
                )
                matched = True
                break

        # 2. Nearest Centroid Fallback
        if not matched:
            min_dist = float("inf")
            best_idx = -1
            for p_idx, p_data in enumerate(polygons):
                c = poly_centroids[p_idx]
                d = math.hypot(pos[0] - c[0], pos[1] - c[1])
                if d < min_dist and d <= max_search_radius:
                    min_dist = d
                    best_idx = p_idx

            if best_idx != -1:
                matches.append(
                    MatchedPolygonAnnotation(
                        polygon_index=best_idx,
                        polygon_layer=str(polygons[best_idx].get("layer", "0")),
                        matched_text=txt,
                        text_position=pos,
                        match_type="NEAREST_CENTROID",
                        distance_to_centroid=min_dist,
                    )
                )
                matched = True

        if matched:
            matched_cnt += 1
        else:
            unmatched_cnt += 1

    return AnnotationMatchResult(
        total_annotations_processed=len(annotations),
        matched_count=matched_cnt,
        unmatched_count=unmatched_cnt,
        matches=matches,
    )
