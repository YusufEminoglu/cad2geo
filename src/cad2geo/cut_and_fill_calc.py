# -*- coding: utf-8 -*-
"""Earthwork Cut & Fill Volumetric Balancer & Prismoidal Grid Engine for cad2geo."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Sequence


@dataclass
class PrismoidCell:
    grid_x: float
    grid_y: float
    existing_elevation_z: float
    design_elevation_z: float
    delta_z: float  # design - existing: >0 is Fill, <0 is Cut
    cell_area_m2: float
    cut_volume_m3: float
    fill_volume_m3: float


@dataclass
class CutFillVolumeReport:
    total_cut_volume_m3: float
    total_fill_volume_m3: float
    net_earthwork_balance_m3: float  # fill - cut (positive means net import required)
    cut_fill_ratio: float
    total_grading_area_m2: float
    cells: list[PrismoidCell]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_cut_m3": round(self.total_cut_volume_m3, 2),
            "total_fill_m3": round(self.total_fill_volume_m3, 2),
            "net_balance_m3": round(self.net_earthwork_balance_m3, 2),
            "cut_fill_ratio": round(self.cut_fill_ratio, 2),
            "grading_area_m2": round(self.total_grading_area_m2, 2),
        }


def calculate_earthwork_cut_fill(
    existing_terrain_grid: Sequence[tuple[float, float, float]],  # (x, y, existing_z)
    design_surface_grid: Sequence[tuple[float, float, float]],   # (x, y, design_z)
    cell_size_m: float = 5.0,
    compaction_shrinkage_factor: float = 1.15,
) -> CutFillVolumeReport:
    """Compute precision cut and fill earthwork volume between terrain and proposed grading surface."""
    # Map points by grid index (round to nearest grid step)
    exist_map = {
        (round(p[0] / cell_size_m), round(p[1] / cell_size_m)): p[2]
        for p in existing_terrain_grid
    }
    design_map = {
        (round(p[0] / cell_size_m), round(p[1] / cell_size_m)): p[2]
        for p in design_surface_grid
    }

    common_keys = set(exist_map.keys()).intersection(set(design_map.keys()))
    if not common_keys:
        # Fallback to direct pair matching if lengths match
        n = min(len(existing_terrain_grid), len(design_surface_grid))
        cells = []
        tot_cut = 0.0
        tot_fill = 0.0
        c_area = cell_size_m * cell_size_m
        for i in range(n):
            ex_pt = existing_terrain_grid[i]
            ds_pt = design_surface_grid[i]
            dz = ds_pt[2] - ex_pt[2]
            cut_vol = abs(dz) * c_area if dz < 0 else 0.0
            fill_vol = (dz * c_area * compaction_shrinkage_factor) if dz > 0 else 0.0
            tot_cut += cut_vol
            tot_fill += fill_vol
            cells.append(
                PrismoidCell(
                    grid_x=ex_pt[0],
                    grid_y=ex_pt[1],
                    existing_elevation_z=ex_pt[2],
                    design_elevation_z=ds_pt[2],
                    delta_z=dz,
                    cell_area_m2=c_area,
                    cut_volume_m3=cut_vol,
                    fill_volume_m3=fill_vol,
                )
            )
        net_bal = tot_fill - tot_cut
        ratio = (tot_cut / max(1e-4, tot_fill)) if tot_fill > 0 else 0.0
        return CutFillVolumeReport(
            total_cut_volume_m3=tot_cut,
            total_fill_volume_m3=tot_fill,
            net_earthwork_balance_m3=net_bal,
            cut_fill_ratio=ratio,
            total_grading_area_m2=len(cells) * c_area,
            cells=cells,
        )

    cells = []
    tot_cut = 0.0
    tot_fill = 0.0
    c_area = cell_size_m * cell_size_m

    for k in common_keys:
        ez = exist_map[k]
        dz_val = design_map[k]
        diff_z = dz_val - ez

        cut_v = abs(diff_z) * c_area if diff_z < 0 else 0.0
        fill_v = (diff_z * c_area * compaction_shrinkage_factor) if diff_z > 0 else 0.0

        tot_cut += cut_v
        tot_fill += fill_v

        cells.append(
            PrismoidCell(
                grid_x=k[0] * cell_size_m,
                grid_y=k[1] * cell_size_m,
                existing_elevation_z=ez,
                design_elevation_z=dz_val,
                delta_z=diff_z,
                cell_area_m2=c_area,
                cut_volume_m3=cut_v,
                fill_volume_m3=fill_v,
            )
        )

    net_bal = tot_fill - tot_cut
    ratio = (tot_cut / max(1e-4, tot_fill)) if tot_fill > 0 else 0.0

    return CutFillVolumeReport(
        total_cut_volume_m3=tot_cut,
        total_fill_volume_m3=tot_fill,
        net_earthwork_balance_m3=net_bal,
        cut_fill_ratio=ratio,
        total_grading_area_m2=len(cells) * c_area,
        cells=cells,
    )
