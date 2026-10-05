# -*- coding: utf-8 -*-
"""DWG/DXF Block Reference & Attribute Extractor for cad2geo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence


@dataclass
class CADBlockInstance:
    """A single placed block reference (INSERT entity) in CAD."""

    block_name: str
    insertion_point: tuple[float, float, float]
    scale_xyz: tuple[float, float, float]
    rotation_degrees: float
    layer: str
    attributes: dict[str, str] = field(default_factory=dict)

    def to_geojson_feature(self) -> dict[str, Any]:
        """Convert block instance into a GeoJSON Point feature with full attribute tags."""
        props = {
            "block_name": self.block_name,
            "rotation_deg": self.rotation_degrees,
            "layer": self.layer,
            **self.attributes,
        }
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": list(self.insertion_point),
            },
            "properties": props,
        }


@dataclass
class CADBlockLibrary:
    """Collection of extracted CAD blocks and summary statistics."""

    total_blocks_found: int
    unique_block_names: list[str]
    instances: list[CADBlockInstance]

    def to_geojson_feature_collection(self) -> dict[str, Any]:
        return {
            "type": "FeatureCollection",
            "features": [inst.to_geojson_feature() for inst in self.instances],
        }


def extract_cad_blocks(
    insert_entities: Sequence[dict[str, Any]],
) -> CADBlockLibrary:
    """Parse INSERT block references and ATTRIB attribute pairs into georeferenced features."""
    instances: list[CADBlockInstance] = []
    unique_names: set[str] = set()

    for ent in insert_entities:
        b_name = str(ent.get("block_name", ent.get("name", "ANONYMOUS_BLOCK")))
        pos = ent.get("insertion_point", ent.get("position", (0.0, 0.0, 0.0)))
        if len(pos) == 2:
            pos = (pos[0], pos[1], 0.0)

        scale = ent.get("scale", (1.0, 1.0, 1.0))
        if isinstance(scale, (int, float)):
            scale = (float(scale), float(scale), float(scale))

        rot = float(ent.get("rotation_degrees", ent.get("rotation", 0.0)))
        layer = str(ent.get("layer", "0"))
        attribs = ent.get("attributes", {})

        inst = CADBlockInstance(
            block_name=b_name,
            insertion_point=pos,
            scale_xyz=scale,
            rotation_degrees=rot,
            layer=layer,
            attributes={str(k): str(v) for k, v in attribs.items()},
        )
        instances.append(inst)
        unique_names.add(b_name)

    return CADBlockLibrary(
        total_blocks_found=len(instances),
        unique_block_names=sorted(unique_names),
        instances=instances,
    )
