# -*- coding: utf-8 -*-
"""Road Corridor Parametric Cross-Section Profile (Enkesit) Generator for cad2geo."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


@dataclass
class CrossSectionProfile:
    station_chainage_m: float
    centerline_x: float
    centerline_y: float
    centerline_ground_z: float
    centerline_design_z: float
    roadway_width_m: float
    cross_slope_pct: float  # e.g. -2.0%
    cut_slope_ratio: float  # e.g. 1:1.5
    fill_slope_ratio: float  # e.g. 1:2.0
    profile_points_offset_z: list[tuple[float, float]]  # (lateral_offset_m, elevation_z)


@dataclass
class StationCrossSectionSet:
    total_sections_count: int
    station_interval_m: float
    sections: list[CrossSectionProfile]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_sections": self.total_sections_count,
            "station_interval_m": self.station_interval_m,
            "first_station": self.sections[0].station_chainage_m if self.sections else 0.0,
            "last_station": self.sections[-1].station_chainage_m if self.sections else 0.0,
        }

    def export_dxf(self, output_path: str | Path) -> Path:
        """Export parametric cross sections as CAD 2D DXF drawing sheet."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "0", "SECTION",
            "2", "ENTITIES",
        ]

        sheet_x = 0.0
        sheet_y = 0.0

        for sec in self.sections:
            # Draw baseline
            pts = sec.profile_points_offset_z
            for i in range(len(pts) - 1):
                p1 = pts[i]
                p2 = pts[i + 1]
                x1 = sheet_x + p1[0]
                y1 = sheet_y + p1[1]
                x2 = sheet_x + p2[0]
                y2 = sheet_y + p2[1]

                lines.extend([
                    "0", "LINE",
                    "8", "ROAD_PROFILE",
                    "10", f"{x1:.3f}", "20", f"{y1:.3f}", "30", "0.0",
                    "11", f"{x2:.3f}", "21", f"{y2:.3f}", "31", "0.0",
                ])

            # Text label: Station Km 0+xxx
            km_str = f"Km {sec.station_chainage_m/1000.0:.3f}"
            lines.extend([
                "0", "TEXT",
                "8", "STATION_LABEL",
                "10", f"{sheet_x:.3f}", "20", f"{sheet_y - 5.0:.3f}", "30", "0.0",
                "40", "1.5",  # Text height
                "1", km_str,
            ])

            sheet_y += 40.0  # Stack sections vertically

        lines.extend([
            "0", "ENDSEC",
            "0", "EOF",
        ])

        out.write_text("\n".join(lines), encoding="utf-8")
        return out


def generate_road_cross_sections(
    centerline_3d: Sequence[tuple[float, float, float]],
    station_interval_m: float = 20.0,
    roadway_half_width_m: float = 4.0,
    cross_slope_pct: float = -2.0,
    cut_slope_ratio: float = 1.5,
    fill_slope_ratio: float = 2.0,
) -> StationCrossSectionSet:
    """Generate engineering cross-sections with ditch slopes and daylight intersection lines at station intervals."""
    pts = list(centerline_3d)
    if len(pts) < 2:
        return StationCrossSectionSet(0, station_interval_m, [])

    # Interpolate stations
    sections: list[CrossSectionProfile] = []
    tot_chainage = 0.0

    for i in range(len(pts) - 1):
        p1 = pts[i]
        p2 = pts[i + 1]
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        dz = p2[2] - p1[2]
        seg_len = math.hypot(dx, dy)

        step = 0.0
        while step < seg_len:
            t = step / max(1e-4, seg_len)
            cx = p1[0] + t * dx
            cy = p1[1] + t * dy
            cz = p1[2] + t * dz

            chainage = tot_chainage + step

            # Design road elevation points: Left edge, Center, Right edge
            edge_drop = roadway_half_width_m * (cross_slope_pct / 100.0)
            z_center = cz
            z_left_edge = cz + edge_drop
            z_right_edge = cz + edge_drop

            # Daylight batter slope points
            z_left_daylight = z_left_edge + (2.0 * cut_slope_ratio)
            z_right_daylight = z_right_edge + (2.0 * cut_slope_ratio)

            sec_pts = [
                (-roadway_half_width_m - 3.0, z_left_daylight),
                (-roadway_half_width_m, z_left_edge),
                (0.0, z_center),
                (roadway_half_width_m, z_right_edge),
                (roadway_half_width_m + 3.0, z_right_daylight),
            ]

            sections.append(
                CrossSectionProfile(
                    station_chainage_m=chainage,
                    centerline_x=cx,
                    centerline_y=cy,
                    centerline_ground_z=cz,
                    centerline_design_z=cz,
                    roadway_width_m=roadway_half_width_m * 2.0,
                    cross_slope_pct=cross_slope_pct,
                    cut_slope_ratio=cut_slope_ratio,
                    fill_slope_ratio=fill_slope_ratio,
                    profile_points_offset_z=sec_pts,
                )
            )

            step += station_interval_m

        tot_chainage += seg_len

    return StationCrossSectionSet(
        total_sections_count=len(sections),
        station_interval_m=station_interval_m,
        sections=sections,
    )
