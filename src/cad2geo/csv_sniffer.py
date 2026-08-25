# -*- coding: utf-8 -*-
"""
Smart Delimited Text & Survey Coordinate Sniffer:
Auto-detects delimiter, header, coordinate column pairs (X/Y/Z), and outputs GeoJSON points.
"""

from __future__ import annotations

import csv
import os
import re
from dataclasses import dataclass, field
from typing import Any

CANDIDATE_DELIMITERS = [",", ";", "\t", "|", " "]

X_NAMES = (
    "x",
    "lon",
    "long",
    "longitude",
    "easting",
    "east",
    "x_coord",
    "coord_x",
    "boylam",
    "saga",
    "saga_deger",
    "point_x",
)
Y_NAMES = (
    "y",
    "lat",
    "latitude",
    "northing",
    "north",
    "y_coord",
    "coord_y",
    "enlem",
    "yukari",
    "yukari_deger",
    "point_y",
)
Z_NAMES = ("z", "elev", "elevation", "height", "kot", "z_coord", "point_z")
ID_NAMES = ("id", "pnt", "point", "nokta", "nokta_no", "pnt_id", "name", "label")


@dataclass
class CsvProfile:
    """Detected structure and geometry columns of a delimited coordinate file."""

    delimiter: str = ","
    fields: list[str] = field(default_factory=list)
    x_field: str = ""
    y_field: str = ""
    z_field: str = ""
    id_field: str = ""
    row_count: int = 0
    sample_points: list[tuple[float, float]] = field(default_factory=list)


def sniff_csv_coordinates(filepath_or_content: str) -> CsvProfile:
    """Analyze a delimited text/CSV file to detect delimiter, columns, and coordinate fields."""
    if os.path.isfile(filepath_or_content):
        with open(filepath_or_content, "r", encoding="utf-8", errors="replace") as f:
            sample_text = f.read(64 * 1024)
    else:
        sample_text = filepath_or_content[: 64 * 1024]

    lines = [ln.strip() for ln in sample_text.splitlines() if ln.strip()]
    if not lines:
        return CsvProfile()

    # Determine best delimiter
    best_delim = ","
    max_cols = 0
    for d in CANDIDATE_DELIMITERS:
        if d == " ":
            cols = len(re.split(r"\s+", lines[0]))
        else:
            cols = len(lines[0].split(d))
        if cols > max_cols:
            max_cols = cols
            best_delim = d

    # Parse headers
    if best_delim == " ":
        header_row = re.split(r"\s+", lines[0])
    else:
        reader = csv.reader(lines[:1], delimiter=best_delim)
        header_row = next(reader, [])

    # Check if first row is actually a header or data
    has_header = False
    for h in header_row:
        if not re.match(r"^-?\d+(\.\d+)?$", h.strip()):
            has_header = True
            break

    if has_header:
        fields_list = [h.strip() for h in header_row]
        data_lines = lines[1:]
    else:
        fields_list = [f"Col_{i + 1}" for i in range(len(header_row))]
        data_lines = lines

    # Find X, Y, Z, ID fields
    x_col, y_col, z_col, id_col = "", "", "", ""

    for fld in fields_list:
        low = fld.lower().replace(" ", "_")
        if low in X_NAMES and not x_col:
            x_col = fld
        elif low in Y_NAMES and not y_col:
            y_col = fld
        elif low in Z_NAMES and not z_col:
            z_col = fld
        elif low in ID_NAMES and not id_col:
            id_col = fld

    # Fallback to positional columns if unnamed
    if not x_col and len(fields_list) >= 2:
        # Check column 0/1 or 1/2
        if len(fields_list) >= 3 and not has_header:
            id_col = fields_list[0]
            y_col = fields_list[1]  # In Turkey, often N (Yukarı) is 1st, E (Sağa) is 2nd
            x_col = fields_list[2]
            if len(fields_list) >= 4:
                z_col = fields_list[3]
        else:
            x_col = fields_list[0]
            y_col = fields_list[1]

    # Sample points extraction
    sample_pts: list[tuple[float, float]] = []
    x_idx = fields_list.index(x_col) if x_col in fields_list else 0
    y_idx = fields_list.index(y_col) if y_col in fields_list else 1

    for row_str in data_lines[:100]:
        if best_delim == " ":
            parts = re.split(r"\s+", row_str)
        else:
            parts = row_str.split(best_delim)
        if len(parts) > max(x_idx, y_idx):
            try:
                vx = float(parts[x_idx].replace(",", "."))
                vy = float(parts[y_idx].replace(",", "."))
                sample_pts.append((vx, vy))
            except ValueError:
                pass

    return CsvProfile(
        delimiter=best_delim,
        fields=fields_list,
        x_field=x_col,
        y_field=y_col,
        z_field=z_col,
        id_field=id_col,
        row_count=len(data_lines),
        sample_points=sample_pts,
    )


def csv_to_geojson(filepath: str, profile: CsvProfile | None = None) -> dict[str, Any]:
    """Convert delimited survey coordinate file directly to a GeoJSON FeatureCollection."""
    if profile is None:
        profile = sniff_csv_coordinates(filepath)

    features: list[dict[str, Any]] = []

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    header_offset = 1 if profile.fields and profile.fields[0] in lines[0] else 0
    x_idx = profile.fields.index(profile.x_field) if profile.x_field in profile.fields else 0
    y_idx = profile.fields.index(profile.y_field) if profile.y_field in profile.fields else 1
    z_idx = profile.fields.index(profile.z_field) if profile.z_field in profile.fields else -1

    for line in lines[header_offset:]:
        if profile.delimiter == " ":
            parts = re.split(r"\s+", line)
        else:
            parts = line.split(profile.delimiter)

        if len(parts) > max(x_idx, y_idx):
            try:
                x = float(parts[x_idx].replace(",", "."))
                y = float(parts[y_idx].replace(",", "."))
                coords = [x, y]
                if z_idx != -1 and len(parts) > z_idx:
                    try:
                        coords.append(float(parts[z_idx].replace(",", ".")))
                    except ValueError:
                        pass

                props: dict[str, Any] = {}
                for idx, val in enumerate(parts):
                    f_name = profile.fields[idx] if idx < len(profile.fields) else f"Col_{idx + 1}"
                    props[f_name] = val.strip()

                features.append(
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": coords},
                        "properties": props,
                    }
                )
            except ValueError:
                continue

    return {"type": "FeatureCollection", "features": features}
