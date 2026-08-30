# -*- coding: utf-8 -*-
"""Multi-Scale CAD Quadtree Tile Slicer for cad2geo."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable

from .ncz_engine.model import NetcadEntity


@dataclass(frozen=True)
class CADTileBounds:
    """Represents a quadtree tile coordinate (Z/X/Y) with spatial bounds."""

    zoom: int
    x: int
    y: int
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "zoom": self.zoom,
            "x": self.x,
            "y": self.y,
            "bbox": [round(self.min_x, 2), round(self.min_y, 2), round(self.max_x, 2), round(self.max_y, 2)],
        }


@dataclass
class CADTilePyramid:
    """Collection of multi-scale quadtree tiles covering a CAD drawing."""

    min_zoom: int
    max_zoom: int
    total_tiles: int
    tiles: list[CADTileBounds]
    drawing_bbox: tuple[float, float, float, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "min_zoom": self.min_zoom,
            "max_zoom": self.max_zoom,
            "total_tiles": self.total_tiles,
            "drawing_bbox": [round(v, 2) for v in self.drawing_bbox],
            "tiles_count": len(self.tiles),
        }


def slice_cad_to_tile_pyramid(
    entities: Iterable[NetcadEntity],
    min_zoom: int = 0,
    max_zoom: int = 3,
) -> CADTilePyramid:
    """Compute multi-scale quadtree tile bounds covering the entire CAD drawing."""
    min_x, min_y = float("inf"), float("inf")
    max_x, max_y = float("-inf"), float("-inf")

    for e in entities:
        for pt in e.coordinates:
            min_x = min(min_x, pt.x)
            max_x = max(max_x, pt.x)
            min_y = min(min_y, pt.y)
            max_y = max(max_y, pt.y)

    if min_x == float("inf"):
        min_x, min_y, max_x, max_y = 0.0, 0.0, 1000.0, 1000.0

    # Ensure square root domain
    span = max(max_x - min_x, max_y - min_y) * 1.05
    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0
    root_min_x = cx - span / 2.0
    root_min_y = cy - span / 2.0

    tiles: list[CADTileBounds] = []

    for z in range(min_zoom, max_zoom + 1):
        num_tiles_axis = 1 << z  # 2^z
        tile_size = span / num_tiles_axis

        for tx in range(num_tiles_axis):
            t_min_x = root_min_x + tx * tile_size
            t_max_x = t_min_x + tile_size

            for ty in range(num_tiles_axis):
                t_min_y = root_min_y + ty * tile_size
                t_max_y = t_min_y + tile_size

                # Check if tile intersects drawing bounds
                if not (t_max_x < min_x or t_min_x > max_x or t_max_y < min_y or t_min_y > max_y):
                    tiles.append(
                        CADTileBounds(
                            zoom=z,
                            x=tx,
                            y=ty,
                            min_x=t_min_x,
                            min_y=t_min_y,
                            max_x=t_max_x,
                            max_y=t_max_y,
                        )
                    )

    return CADTilePyramid(
        min_zoom=min_zoom,
        max_zoom=max_zoom,
        total_tiles=len(tiles),
        tiles=tiles,
        drawing_bbox=(min_x, min_y, max_x, max_y),
    )
