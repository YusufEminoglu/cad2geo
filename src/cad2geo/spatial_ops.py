# -*- coding: utf-8 -*-
"""Geometric Buffers, Point-in-Polygon & Spatial Index for cad2geo."""

from __future__ import annotations

import math
from typing import Any, Sequence

from .ncz_engine.model import NetcadCoordinate, NetcadEntity


def point_in_polygon(x: float, y: float, polygon: Sequence[tuple[float, float]]) -> bool:
    """Ray casting algorithm for 2D point-in-polygon containment test."""
    n = len(polygon)
    if n < 3:
        return False
    inside = False
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def buffer_point(x: float, y: float, radius: float, num_segments: int = 16) -> list[NetcadCoordinate]:
    """Generate a circular polygon buffer around a point."""
    ring: list[NetcadCoordinate] = []
    for i in range(num_segments):
        ang = i * (2.0 * math.pi / num_segments)
        px = x + radius * math.cos(ang)
        py = y + radius * math.sin(ang)
        ring.append(NetcadCoordinate(x=px, y=py, z=0.0))
    # Close ring
    ring.append(ring[0])
    return ring


def _get_xy(pt: Any) -> tuple[float, float]:
    if hasattr(pt, "x") and hasattr(pt, "y"):
        return float(pt.x), float(pt.y)
    return float(pt[0]), float(pt[1])


def buffer_polyline(
    coords: Sequence[Any],
    distance: float,
    num_segments: int = 8,
) -> list[NetcadCoordinate]:
    """Generate parallel offset corridor polygon buffer around a 2D polyline."""
    n = len(coords)
    if n < 2:
        if n == 1:
            x0, y0 = _get_xy(coords[0])
            return buffer_point(x0, y0, distance, num_segments)
        return []

    left_offset: list[tuple[float, float]] = []
    right_offset: list[tuple[float, float]] = []

    for i in range(n - 1):
        x1, y1 = _get_xy(coords[i])
        x2, y2 = _get_xy(coords[i + 1])
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)
        if length <= 1e-6:
            continue

        # Unit normal vector (-dy/L, dx/L)
        nx = -dy / length
        ny = dx / length

        left_offset.append((x1 + nx * distance, y1 + ny * distance))
        left_offset.append((x2 + nx * distance, y2 + ny * distance))

        right_offset.append((x2 - nx * distance, y2 - ny * distance))
        right_offset.append((x1 - nx * distance, y1 - ny * distance))

    # Combine into closed polygon corridor (left forward + right backward)
    full_ring_pts = left_offset + right_offset
    if not full_ring_pts:
        return []

    res = [NetcadCoordinate(x=x, y=y, z=0.0) for x, y in full_ring_pts]
    res.append(res[0])
    return res


class CADSpatialIndex:
    """Fast grid-based 2D spatial index for CAD entities."""

    def __init__(self, cell_size: float = 100.0) -> None:
        self.cell_size = cell_size
        self.grid: dict[tuple[int, int], list[NetcadEntity]] = {}
        self.entities: list[NetcadEntity] = []

    def insert(self, entity: NetcadEntity) -> None:
        self.entities.append(entity)
        if not entity.coordinates:
            return
        min_x = min(p.x for p in entity.coordinates)
        max_x = max(p.x for p in entity.coordinates)
        min_y = min(p.y for p in entity.coordinates)
        max_y = max(p.y for p in entity.coordinates)

        c1 = int(math.floor(min_x / self.cell_size))
        c2 = int(math.floor(max_x / self.cell_size))
        r1 = int(math.floor(min_y / self.cell_size))
        r2 = int(math.floor(max_y / self.cell_size))

        for c in range(c1, c2 + 1):
            for r in range(r1, r2 + 1):
                key = (c, r)
                if key not in self.grid:
                    self.grid[key] = []
                self.grid[key].append(entity)

    def query_bbox(self, min_x: float, min_y: float, max_x: float, max_y: float) -> list[NetcadEntity]:
        """Find candidate entities intersecting query bounding box."""
        c1 = int(math.floor(min_x / self.cell_size))
        c2 = int(math.floor(max_x / self.cell_size))
        r1 = int(math.floor(min_y / self.cell_size))
        r2 = int(math.floor(max_y / self.cell_size))

        seen = set()
        candidates: list[NetcadEntity] = []
        for c in range(c1, c2 + 1):
            for r in range(r1, r2 + 1):
                for e in self.grid.get((c, r), []):
                    e_id = id(e)
                    if e_id not in seen:
                        seen.add(e_id)
                        candidates.append(e)
        return candidates
