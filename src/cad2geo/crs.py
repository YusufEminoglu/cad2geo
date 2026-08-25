# -*- coding: utf-8 -*-
"""
Smart Automatic Coordinate Reference System (CRS) & Projection Detector.
Accurately identifies Turkish survey / planning datums (TUREF, ED50, WGS84, 3° Gauss-Krüger, 6° UTM).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

# Central meridians of the Turkish 3-degree zones. Zone index = cm // 3.
TURKISH_CENTRAL_MERIDIANS = (27, 30, 33, 36, 39, 42, 45)

# cm -> EPSG, false easting 500000 (no zone prefix in the easting)
TUREF_TM = {27: 5253, 30: 5254, 33: 5255, 36: 5256, 39: 5257, 42: 5258, 45: 5259}
ED50_TM = {27: 2319, 30: 2320, 33: 2321, 36: 2322, 39: 2323, 42: 2324, 45: 2325}

# cm -> EPSG, false easting zone*1_000_000 + 500000 (zone prefixed easting)
TUREF_GK = {27: 5269, 30: 5270, 33: 5271, 36: 5272, 39: 5273, 42: 5274, 45: 5275}
ED50_GK = {27: 2206, 30: 2207, 33: 2208, 36: 2209, 39: 2210, 42: 2211, 45: 2212}

# UTM zone -> EPSG, for the four zones that cover Turkey
WGS84_UTM = {35: 32635, 36: 32636, 37: 32637, 38: 32638}
ED50_UTM = {35: 23035, 36: 23036, 37: 23037, 38: 23038}

LABELS = {
    **{v: f"TUREF / TM{k}" for k, v in TUREF_TM.items()},
    **{v: f"ED50 / TM{k}" for k, v in ED50_TM.items()},
    **{v: f"TUREF / 3-degree Gauss-Kruger zone {k // 3}" for k, v in TUREF_GK.items()},
    **{v: f"ED50 / 3-degree Gauss-Kruger zone {k // 3}" for k, v in ED50_GK.items()},
    **{v: f"WGS 84 / UTM zone {k}N" for k, v in WGS84_UTM.items()},
    **{v: f"ED50 / UTM zone {k}N" for k, v in ED50_UTM.items()},
    4326: "WGS 84",
}

TURKEY_NORTHING = (3_800_000.0, 4_800_000.0)
GK_EASTING_FLOOR = 1_000_000.0


@dataclass(frozen=True)
class DetectedCRS:
    """Result of CRS auto-detection."""

    epsg: int
    authid: str
    description: str
    confidence: float
    reason: str

    def __str__(self) -> str:
        return f"{self.authid} ({self.description}, {int(self.confidence * 100)}% confidence: {self.reason})"


def detect_crs(
    proj_text: str = "",
    coords: Sequence[tuple[float, float]] | None = None,
    srs_id: int | None = None,
) -> DetectedCRS | None:
    """Analyze projection metadata string and sample coordinates to detect the exact EPSG CRS."""
    t = (proj_text or "").upper().strip()
    is_ed50 = bool(re.search(r"\bED\s*50\b|\bED-50\b|\bEUROPEAN\b", t))

    # Look for explicit central meridian or zone number
    cm_match = re.search(r"\b(DOM|CM|DILIM|MERIDIAN|TM)\s*[:=]?\s*(\d{2})\b", t)
    zone_match = re.search(r"\b(ZONE|ZON)\s*[:=]?\s*(\d{1,2})\b", t)

    detected_cm = None
    if cm_match:
        cm_cand = int(cm_match.group(2))
        if cm_cand in TURKISH_CENTRAL_MERIDIANS:
            detected_cm = cm_cand
    elif zone_match:
        z_cand = int(zone_match.group(2))
        if 9 <= z_cand <= 15:
            detected_cm = z_cand * 3

    # Sample coordinate inspection
    has_gk_easting = False
    if coords and len(coords) > 0:
        sample_x = [pt[0] for pt in coords[:100]]
        avg_x = sum(sample_x) / len(sample_x)
        if avg_x >= GK_EASTING_FLOOR:
            has_gk_easting = True
            # Extract zone from the millionth digit
            z_from_coord = int(avg_x // 1_000_000)
            if 9 <= z_from_coord <= 15 and not detected_cm:
                detected_cm = z_from_coord * 3

    # 1. 3-Degree Gauss-Krüger / TM
    if detected_cm in TURKISH_CENTRAL_MERIDIANS:
        if has_gk_easting:
            epsg = ED50_GK[detected_cm] if is_ed50 else TUREF_GK[detected_cm]
            label = LABELS.get(epsg, f"EPSG:{epsg}")
            return DetectedCRS(
                epsg,
                f"EPSG:{epsg}",
                label,
                0.95,
                f"3° GK zone {detected_cm // 3} with zone-prefixed easting",
            )
        else:
            epsg = ED50_TM[detected_cm] if is_ed50 else TUREF_TM[detected_cm]
            label = LABELS.get(epsg, f"EPSG:{epsg}")
            return DetectedCRS(
                epsg, f"EPSG:{epsg}", label, 0.90, f"3° TM central meridian {detected_cm}°"
            )

    # 2. 6-Degree UTM
    if zone_match:
        z_utm = int(zone_match.group(2))
        if 35 <= z_utm <= 38:
            epsg = ED50_UTM[z_utm] if is_ed50 else WGS84_UTM[z_utm]
            label = LABELS.get(epsg, f"EPSG:{epsg}")
            return DetectedCRS(epsg, f"EPSG:{epsg}", label, 0.90, f"6° UTM zone {z_utm}N")

    # 3. Geographic WGS84 fallback if degrees
    if coords and len(coords) > 0:
        sample_x = [pt[0] for pt in coords[:10]]
        sample_y = [pt[1] for pt in coords[:10]]
        if all(25 <= x <= 46 for x in sample_x) and all(35 <= y <= 43 for y in sample_y):
            return DetectedCRS(
                4326,
                "EPSG:4326",
                "WGS 84 (Geographic Lat/Lon)",
                0.99,
                "Coordinates fall within Turkey decimal degree bounds",
            )

    # Default fallback: TUREF / TM30 (Izmir/Istanbul/Ankara common survey datum)
    return DetectedCRS(
        5254, "EPSG:5254", "TUREF / TM30", 0.60, "Default Turkish national survey grid fallback"
    )
