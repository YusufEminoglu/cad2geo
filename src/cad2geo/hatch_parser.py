# -*- coding: utf-8 -*-
"""CAD Hatch Pattern & Texture Extractor for cad2geo."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Sequence


@dataclass
class HatchLine:
    angle_degrees: float
    base_x: float
    base_y: float
    offset_x: float
    offset_y: float
    dash_pattern: list[float] = field(default_factory=list)


@dataclass
class HatchPattern:
    """Decoded CAD Hatch pattern specification."""

    pattern_name: str  # 'ANSI31', 'BRICK', 'CONC', 'EARTH', 'SOLID'
    scale: float = 1.0
    angle_degrees: float = 0.0
    lines: list[HatchLine] = field(default_factory=list)

    def to_svg_pattern(self, pattern_id: str, stroke_color: str = "#444444") -> str:
        """Generate SVG <pattern> definition."""
        if self.pattern_name.upper() == "SOLID":
            return f'<pattern id="{pattern_id}" width="10" height="10" patternUnits="userSpaceOnUse"><rect width="10" height="10" fill="{stroke_color}" /></pattern>'

        size = max(10, int(20 * self.scale))
        ang = self.angle_degrees
        rad = math.radians(ang)
        x2 = size * math.cos(rad)
        y2 = size * math.sin(rad)

        return f"""<pattern id="{pattern_id}" width="{size}" height="{size}" patternTransform="rotate({ang})" patternUnits="userSpaceOnUse">
  <line x1="0" y1="0" x2="{size}" y2="0" stroke="{stroke_color}" stroke-width="1" />
</pattern>"""


STANDARD_HATCHES: dict[str, HatchPattern] = {
    "ANSI31": HatchPattern(pattern_name="ANSI31", angle_degrees=45.0),
    "ANSI32": HatchPattern(pattern_name="ANSI32", angle_degrees=45.0),
    "ANSI33": HatchPattern(pattern_name="ANSI33", angle_degrees=45.0),
    "BRICK": HatchPattern(pattern_name="BRICK", angle_degrees=0.0),
    "CONC": HatchPattern(pattern_name="CONC", angle_degrees=0.0),
    "SOLID": HatchPattern(pattern_name="SOLID", angle_degrees=0.0),
}


def parse_cad_hatches(layer_name: str) -> HatchPattern:
    """Infer standard CAD hatch pattern from layer name or description."""
    upper = layer_name.upper()
    for name, pat in STANDARD_HATCHES.items():
        if name in upper:
            return pat
    return STANDARD_HATCHES["ANSI31"]
