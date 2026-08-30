# -*- coding: utf-8 -*-
"""CAD DIMENSION Entity Parser and Linear/Angular Distance Verification QA for cad2geo."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Sequence


@dataclass
class DimensionEntity:
    dimension_type: str  # 'ALIGNED', 'LINEAR', 'ANGULAR', 'RADIAL'
    measurement_value: float  # Value annotated in text
    computed_geometry_length: float  # Actual distance between defining points
    deviation_m: float
    is_accurate: bool
    point_definition_1: tuple[float, float]
    point_definition_2: tuple[float, float]
    text_override: str = ""
    layer: str = "DIMENSIONS"


@dataclass
class DimensionSummary:
    total_dimensions: int
    mean_measured_distance: float
    max_deviation_m: float
    accurate_count: int
    discrepancies_count: int
    dimensions: list[DimensionEntity]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_dimensions": self.total_dimensions,
            "mean_measured_distance": round(self.mean_measured_distance, 2),
            "max_deviation_m": round(self.max_deviation_m, 4),
            "accurate_count": self.accurate_count,
            "discrepancies_count": self.discrepancies_count,
        }


def extract_cad_dimensions(
    raw_dimension_entities: Sequence[dict[str, Any]],
    tolerance_m: float = 0.05,
) -> DimensionSummary:
    """Extract and cross-validate CAD dimensions against geometric endpoints."""
    dims: list[DimensionEntity] = []
    tot_dist = 0.0
    max_dev = 0.0
    acc_count = 0
    disc_count = 0

    for raw in raw_dimension_entities:
        dim_type = str(raw.get("dim_type", "ALIGNED")).upper()
        p1 = tuple(raw.get("p1", (0.0, 0.0)))
        p2 = tuple(raw.get("p2", (0.0, 0.0)))
        text_val = raw.get("measurement", None)
        layer = str(raw.get("layer", "DIMENSIONS"))

        geom_len = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        if text_val is None or text_val == "":
            meas_val = geom_len
        else:
            try:
                meas_val = float(text_val)
            except ValueError:
                meas_val = geom_len

        dev = abs(meas_val - geom_len)
        max_dev = max(max_dev, dev)
        tot_dist += meas_val

        is_acc = dev <= tolerance_m
        if is_acc:
            acc_count += 1
        else:
            disc_count += 1

        dims.append(
            DimensionEntity(
                dimension_type=dim_type,
                measurement_value=meas_val,
                computed_geometry_length=geom_len,
                deviation_m=dev,
                is_accurate=is_acc,
                point_definition_1=p1,
                point_definition_2=p2,
                text_override=str(text_val or ""),
                layer=layer,
            )
        )

    mean_dist = (tot_dist / max(1, len(dims))) if dims else 0.0

    return DimensionSummary(
        total_dimensions=len(dims),
        mean_measured_distance=mean_dist,
        max_deviation_m=max_dev,
        accurate_count=acc_count,
        discrepancies_count=disc_count,
        dimensions=dims,
    )
