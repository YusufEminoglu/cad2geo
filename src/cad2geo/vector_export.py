# -*- coding: utf-8 -*-
"""Vector Exporters & GeoParquet / FlatGeobuf Metadata Generators for cad2geo."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .ncz_engine.model import NetcadEntity


def export_to_esri_shapefile_asc(
    entities: Iterable[NetcadEntity],
    output_path: str | Path,
) -> Path:
    """Export CAD entities to standard ESRI ASCII Polygon/Line text format (.ASC / .GEN)."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    for idx, e in enumerate(entities):
        if not e.coordinates:
            continue
        lines.append(f"{idx+1} {e.layer_name}")
        for pt in e.coordinates:
            lines.append(f"  {pt.x:.4f} {pt.y:.4f} {pt.z:.4f}")
        lines.append("END")
    lines.append("END")

    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def export_geoparquet_metadata(
    entities: Iterable[NetcadEntity],
    crs_auth: str = "EPSG:5254",
    geometry_column: str = "geometry",
) -> dict[str, Any]:
    """Generate GeoParquet 1.0 compliant JSON metadata block for columnar CAD storage."""
    layer_names = set()
    geom_types = set()
    min_x, min_y = float("inf"), float("inf")
    max_x, max_y = float("-inf"), float("-inf")
    total_count = 0

    for e in entities:
        total_count += 1
        layer_names.add(e.layer_name)
        geom_types.add(e.geometry_kind)
        for pt in e.coordinates:
            min_x = min(min_x, pt.x)
            max_x = max(max_x, pt.x)
            min_y = min(min_y, pt.y)
            max_y = max(max_y, pt.y)

    bbox = [min_x, min_y, max_x, max_y] if min_x != float("inf") else [0.0, 0.0, 0.0, 0.0]

    return {
        "version": "1.0.0",
        "primary_column": geometry_column,
        "columns": {
            geometry_column: {
                "encoding": "WKB",
                "geometry_types": sorted(geom_types),
                "crs": {
                    "type": "Name",
                    "properties": {"name": crs_auth},
                },
                "bbox": [round(v, 4) for v in bbox],
            }
        },
        "cad2geo_metadata": {
            "total_entities": total_count,
            "layers": sorted(layer_names),
        },
    }


def export_flat_geobuf_schema(
    entities: Iterable[NetcadEntity],
    name: str = "cad2geo_layer",
) -> dict[str, Any]:
    """Generate FlatGeobuf header schema description for binary streaming."""
    return {
        "name": name,
        "geometry_type": "GeometryCollection",
        "has_z": True,
        "has_m": False,
        "has_t": False,
        "has_tm": False,
        "columns": [
            {"name": "layer_name", "type": "String"},
            {"name": "layer_code", "type": "Int"},
            {"name": "color_argb", "type": "Int"},
            {"name": "label_text", "type": "String"},
            {"name": "is_closed", "type": "Bool"},
        ],
    }
