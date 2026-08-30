# -*- coding: utf-8 -*-
"""CAD Quality Assurance, Geometry Repair & Sliver Cleaner for cad2geo."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable

from .ncz_engine.model import NetcadCoordinate, NetcadEntity


@dataclass
class QARepairReport:
    """Detailed summary of geometric QA repairs performed on CAD entities."""

    total_input_entities: int = 0
    total_output_entities: int = 0
    endpoints_snapped: int = 0
    duplicate_vertices_removed: int = 0
    degenerate_lines_dropped: int = 0
    slivers_filtered: int = 0
    unclosed_polygons_fixed: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_input_entities": self.total_input_entities,
            "total_output_entities": self.total_output_entities,
            "endpoints_snapped": self.endpoints_snapped,
            "duplicate_vertices_removed": self.duplicate_vertices_removed,
            "degenerate_lines_dropped": self.degenerate_lines_dropped,
            "slivers_filtered": self.slivers_filtered,
            "unclosed_polygons_fixed": self.unclosed_polygons_fixed,
        }


def snap_endpoints(
    coords: list[NetcadCoordinate],
    tolerance: float = 0.05,
) -> tuple[list[NetcadCoordinate], bool]:
    """Snap start and end point together if distance is within tolerance."""
    if len(coords) < 3:
        return coords, False

    start = coords[0]
    end = coords[-1]
    dist = math.hypot(start.x - end.x, start.y - end.y)

    if 0.0 < dist <= tolerance:
        new_coords = list(coords)
        new_coords[-1] = NetcadCoordinate(x=start.x, y=start.y, z=start.z)
        return new_coords, True

    return coords, False


def remove_duplicate_vertices(
    coords: list[NetcadCoordinate],
    min_dist: float = 1e-4,
) -> tuple[list[NetcadCoordinate], int]:
    """Remove consecutive duplicate or near-duplicate vertices."""
    if len(coords) <= 1:
        return coords, 0

    cleaned: list[NetcadCoordinate] = [coords[0]]
    removed_count = 0

    for i in range(1, len(coords)):
        curr = coords[i]
        prev = cleaned[-1]
        dist = math.hypot(curr.x - prev.x, curr.y - prev.y)
        if dist >= min_dist:
            cleaned.append(curr)
        else:
            removed_count += 1

    return cleaned, removed_count


def calculate_polygon_area(coords: list[NetcadCoordinate]) -> float:
    """Compute polygon area using Shoelace formula."""
    if len(coords) < 3:
        return 0.0
    area = 0.0
    n = len(coords)
    for i in range(n):
        j = (i + 1) % n
        area += coords[i].x * coords[j].y
        area -= coords[j].x * coords[i].y
    return abs(area) / 2.0


def clean_cad_entities(
    entities: Iterable[NetcadEntity],
    snap_tolerance: float = 0.05,
    min_vertex_dist: float = 1e-4,
    min_polygon_area: float = 0.1,
    min_line_length: float = 0.01,
) -> tuple[list[NetcadEntity], QARepairReport]:
    """Clean and repair a list of NetcadEntity objects.

    Args:
        entities: List of CAD entities.
        snap_tolerance: Max gap in coordinate units to auto-close polylines/polygons.
        min_vertex_dist: Minimum distance between consecutive vertices.
        min_polygon_area: Minimum area below which polygon slivers are filtered out.
        min_line_length: Minimum total length for lines.

    Returns:
        Tuple of (cleaned_entities, QARepairReport).
    """
    report = QARepairReport()
    cleaned_entities: list[NetcadEntity] = []

    for entity in entities:
        report.total_input_entities += 1
        coords = entity.coordinates

        if not coords:
            continue

        # Step 1: Remove consecutive duplicate vertices
        coords, dup_count = remove_duplicate_vertices(coords, min_dist=min_vertex_dist)
        report.duplicate_vertices_removed += dup_count

        if len(coords) < 2 and entity.geometry_kind in ("LINE", "POLYLINE", "POLYGON"):
            report.degenerate_lines_dropped += 1
            continue

        # Step 2: Line length check
        if entity.geometry_kind in ("LINE", "POLYLINE") and not entity.is_closed:
            total_len = sum(
                math.hypot(coords[i + 1].x - coords[i].x, coords[i + 1].y - coords[i].y)
                for i in range(len(coords) - 1)
            )
            if total_len < min_line_length:
                report.degenerate_lines_dropped += 1
                continue

        # Step 3: Snap endpoints if closed polygon or intended closed ring
        snapped = False
        if entity.geometry_kind == "POLYGON" or entity.is_closed:
            coords, snapped = snap_endpoints(coords, tolerance=snap_tolerance)
            if snapped:
                report.endpoints_snapped += 1
                report.unclosed_polygons_fixed += 1

            area = calculate_polygon_area(coords)
            if area < min_polygon_area and len(coords) >= 3:
                report.slivers_filtered += 1
                continue

        # Create updated entity
        cleaned_entity = NetcadEntity(
            geometry_kind=entity.geometry_kind,
            layer_code=entity.layer_code,
            layer_name=entity.layer_name,
            color_argb=entity.color_argb,
            name=entity.name,
            label_text=entity.label_text,
            text_height=entity.text_height,
            rotation_degrees=entity.rotation_degrees,
            box_width=entity.box_width,
            box_height=entity.box_height,
            scale=entity.scale,
            grid_x=entity.grid_x,
            grid_y=entity.grid_y,
            radius=entity.radius,
            start_angle=entity.start_angle,
            end_angle=entity.end_angle,
            is_closed=entity.is_closed or snapped,
            coordinates=coords,
        )
        cleaned_entities.append(cleaned_entity)
        report.total_output_entities += 1

    return cleaned_entities, report
