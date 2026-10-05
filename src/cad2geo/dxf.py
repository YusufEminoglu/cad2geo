# -*- coding: utf-8 -*-
"""Pure-Python DXF (AutoCAD Drawing Exchange Format) reader & GeoJSON converter."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .ncz_engine.model import NetcadCoordinate, NetcadEntity

# Standard AutoCAD Color Index (ACI 1-7 primary mapping)
ACI_PALETTE: dict[int, str] = {
    1: "#FF0000",  # Red
    2: "#FFFF00",  # Yellow
    3: "#00FF00",  # Green
    4: "#00FFFF",  # Cyan
    5: "#0000FF",  # Blue
    6: "#FF00FF",  # Magenta
    7: "#FFFFFF",  # White / Black
    8: "#808080",  # Dark Gray
    9: "#C0C0C0",  # Light Gray
}


@dataclass
class DXFEntity:
    """Represents a decoded geometric entity from a DXF file."""

    kind: str  # LINE, LWPOLYLINE, POLYLINE, POINT, CIRCLE, ARC, 3DFACE, TEXT, MTEXT
    layer: str
    color_aci: int = 7
    color_hex: str = "#FFFFFF"
    is_closed: bool = False
    text: str = ""
    text_height: float = 0.0
    radius: float = 0.0
    start_angle: float = 0.0
    end_angle: float = 0.0
    coordinates: list[NetcadCoordinate] = field(default_factory=list)

    def to_netcad_entity(self, layer_code: int = 0) -> NetcadEntity:
        """Convert DXFEntity into a standard NetcadEntity representation."""
        geom_kind = self.kind.upper()
        if geom_kind in ("LWPOLYLINE", "POLYLINE"):
            geom_kind = "POLYGON" if self.is_closed else "LINE"
        elif geom_kind in ("LINE", "3DFACE"):
            geom_kind = "LINE"
        elif geom_kind in ("POINT", "CIRCLE", "ARC"):
            geom_kind = "POINT" if geom_kind == "POINT" else "LINE"
        elif geom_kind in ("TEXT", "MTEXT"):
            geom_kind = "POINT"

        return NetcadEntity(
            geometry_kind=geom_kind,
            layer_code=layer_code,
            layer_name=self.layer,
            name=self.layer,
            label_text=self.text,
            text_height=self.text_height,
            radius=self.radius,
            start_angle=self.start_angle,
            end_angle=self.end_angle,
            is_closed=self.is_closed,
            coordinates=self.coordinates,
        )

    def to_geojson_feature(self) -> dict[str, Any]:
        """Convert to GeoJSON Feature."""
        coords = [[c.x, c.y] for c in self.coordinates]
        geom: dict[str, Any] | None = None

        if self.kind in ("LWPOLYLINE", "POLYLINE") and self.is_closed:
            if coords and coords[0] != coords[-1]:
                coords.append(coords[0])
            geom = {"type": "Polygon", "coordinates": [coords]}
        elif self.kind in ("LINE", "LWPOLYLINE", "POLYLINE", "3DFACE"):
            geom = {"type": "LineString", "coordinates": coords}
        elif self.kind in ("POINT", "TEXT", "MTEXT") and coords:
            geom = {"type": "Point", "coordinates": coords[0]}
        elif coords:
            geom = {"type": "LineString", "coordinates": coords}
        else:
            geom = None

        return {
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "dxf_kind": self.kind,
                "layer_name": self.layer,
                "color_aci": self.color_aci,
                "color_hex": self.color_hex,
                "text": self.text,
                "is_closed": self.is_closed,
            },
        }


class DXFReader:
    """Pure-Python streaming reader for ASCII DXF files."""

    def __init__(self, filepath_or_text: str | Path) -> None:
        if isinstance(filepath_or_text, Path) or (
            isinstance(filepath_or_text, str) and "\n" not in filepath_or_text and Path(filepath_or_text).exists()
        ):
            self.raw_text = Path(filepath_or_text).read_text(encoding="utf-8", errors="replace")
        else:
            self.raw_text = str(filepath_or_text)

        self.entities: list[DXFEntity] = []
        self.layers: set[str] = set()

    def parse(self) -> list[DXFEntity]:
        """Parse the DXF content and extract entities."""
        lines = [line.strip() for line in self.raw_text.splitlines()]
        num_lines = len(lines)
        idx = 0

        # Scan for ENTITIES section
        in_entities = False
        while idx + 1 < num_lines:
            code_str = lines[idx]
            val = lines[idx + 1]
            idx += 2

            try:
                code = int(code_str)
            except ValueError:
                continue

            if code == 0 and val == "SECTION":
                continue
            if code == 2 and val == "ENTITIES":
                in_entities = True
                break

        if not in_entities:
            # Try parsing from start if no explicit ENTITIES section header found
            idx = 0

        current_kind: str | None = None
        current_layer = "0"
        current_aci = 7
        current_coords: list[NetcadCoordinate] = []
        current_x = 0.0
        current_y = 0.0
        current_z = 0.0
        current_text = ""
        current_text_height = 0.0
        current_radius = 0.0
        current_is_closed = False

        def flush_entity() -> None:
            nonlocal current_kind, current_layer, current_aci, current_coords
            nonlocal current_text, current_text_height, current_radius, current_is_closed
            if current_kind:
                coords = list(current_coords) if current_coords else []
                hex_col = ACI_PALETTE.get(current_aci, "#FFFFFF")
                entity = DXFEntity(
                    kind=current_kind,
                    layer=current_layer,
                    color_aci=current_aci,
                    color_hex=hex_col,
                    is_closed=current_is_closed,
                    text=current_text,
                    text_height=current_text_height,
                    radius=current_radius,
                    coordinates=coords,
                )
                self.entities.append(entity)
                self.layers.add(current_layer)

            current_kind = None
            current_layer = "0"
            current_aci = 7
            current_coords = []
            current_text = ""
            current_text_height = 0.0
            current_radius = 0.0
            current_is_closed = False

        while idx + 1 < num_lines:
            code_str = lines[idx]
            val = lines[idx + 1]
            idx += 2

            try:
                code = int(code_str)
            except ValueError:
                continue

            if code == 0:
                if val == "ENDSEC" or val == "EOF":
                    flush_entity()
                    break

                # New entity encountered
                flush_entity()
                current_kind = val.upper()
                continue

            if current_kind is None:
                continue

            if code == 8:
                current_layer = val
            elif code == 62:
                try:
                    current_aci = int(val)
                except ValueError:
                    pass
            elif code == 1:
                current_text = val
            elif code == 40:
                try:
                    current_radius = float(val)
                    current_text_height = float(val)
                except ValueError:
                    pass
            elif code == 70:
                try:
                    flags = int(val)
                    if flags & 1:
                        current_is_closed = True
                except ValueError:
                    pass
            elif code == 10:
                try:
                    current_x = float(val)
                except ValueError:
                    pass
            elif code == 20:
                try:
                    current_y = float(val)
                except ValueError:
                    pass
            elif code == 30:
                try:
                    current_z = float(val)
                except ValueError:
                    pass
                current_coords.append(NetcadCoordinate(x=current_x, y=current_y, z=current_z))
            elif code == 11 and current_kind == "LINE":
                try:
                    end_x = float(val)
                except ValueError:
                    end_x = current_x
            elif code == 21 and current_kind == "LINE":
                try:
                    end_y = float(val)
                except ValueError:
                    end_y = current_y
            elif code == 31 and current_kind == "LINE":
                try:
                    end_z = float(val)
                except ValueError:
                    end_z = 0.0
                current_coords.append(NetcadCoordinate(x=end_x, y=end_y, z=end_z))

        flush_entity()
        return self.entities


def parse_dxf(filepath_or_text: str | Path) -> list[DXFEntity]:
    """Parse a DXF file into a list of DXFEntity objects."""
    return DXFReader(filepath_or_text).parse()


def dxf_to_geojson(filepath_or_text: str | Path) -> dict[str, Any]:
    """Parse a DXF file and convert it directly to a GeoJSON FeatureCollection."""
    entities = parse_dxf(filepath_or_text)
    features = [e.to_geojson_feature() for e in entities if e.coordinates]
    return {
        "type": "FeatureCollection",
        "features": features,
    }
