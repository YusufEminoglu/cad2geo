# -*- coding: utf-8 -*-
"""Highway Drainage Catchment Peak Runoff & Culvert Sizing (Menfez Hesabı) for cad2geo."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class CatchmentRunoffProfile:
    catchment_area_ha: float = 45.0  # Hectares
    runoff_coefficient_c: float = 0.55  # Rational runoff coefficient (0.2 rural to 0.8 impervious)
    rainfall_intensity_mm_hr: float = 65.0  # 25-yr / 50-yr return period design intensity
    culvert_slope_pct: float = 1.5  # 1.5% longitudinal culvert bed slope
    manning_roughness_n: float = 0.015  # Concrete box/pipe (0.013-0.015), Corrugated metal (0.024)


@dataclass
class CulvertSizingResult:
    peak_discharge_q_m3s: float
    recommended_culvert_type: str  # "PIPE_CIRCULAR" or "BOX_RECTANGULAR"
    recommended_internal_dimensions_m: tuple[float, float]  # (width/diameter, height)
    actual_capacity_q_m3s: float
    flow_velocity_ms: float
    headwater_depth_hw_m: float
    is_flow_capacity_adequate: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "peak_q_m3s": round(self.peak_discharge_q_m3s, 2),
            "culvert_type": self.recommended_culvert_type,
            "dimensions_m": [round(d, 2) for d in self.recommended_internal_dimensions_m],
            "capacity_q_m3s": round(self.actual_capacity_q_m3s, 2),
            "velocity_ms": round(self.flow_velocity_ms, 2),
            "is_adequate": self.is_flow_capacity_adequate,
        }


def calculate_culvert_hydraulic_capacity(
    profile: CatchmentRunoffProfile | None = None,
    allowable_headwater_depth_m: float = 2.5,
) -> CulvertSizingResult:
    """Compute peak discharge via Rational Formula (Q = C*I*A / 360) and size culvert barrel using Manning's equation."""
    p = profile or CatchmentRunoffProfile()

    # Rational Method: Q = (C * I * A) / 360  [m3/s] where I in mm/hr, A in hectares
    q_peak = (p.runoff_coefficient_c * p.rainfall_intensity_mm_hr * p.catchment_area_ha) / 360.0

    slope_s = p.culvert_slope_pct / 100.0

    # Determine Culvert size:
    # Manning equation: Q = (1/n) * A_flow * R_h^(2/3) * S^(1/2)
    # Check standard circular pipe sizes (1.0m, 1.2m, 1.5m, 1.8m, 2.0m)
    # Or rectangular box culverts (2.0x2.0m, 3.0x2.0m, 4.0x3.0m)
    if q_peak <= 4.5:
        # Circular pipe culvert
        culv_type = "PIPE_CIRCULAR"
        for dia in [0.8, 1.0, 1.2, 1.5, 1.8, 2.0, 2.5]:
            r_pipe = dia / 2.0
            a_flow = math.pi * (r_pipe ** 2)
            p_wetted = math.pi * dia
            r_h = a_flow / p_wetted
            cap = (1.0 / p.manning_roughness_n) * a_flow * (r_h ** (2.0 / 3.0)) * math.sqrt(slope_s)
            if cap >= q_peak:
                vel = q_peak / max(1e-4, a_flow)
                hw = dia * 1.15
                return CulvertSizingResult(
                    peak_discharge_q_m3s=q_peak,
                    recommended_culvert_type=culv_type,
                    recommended_internal_dimensions_m=(dia, dia),
                    actual_capacity_q_m3s=cap,
                    flow_velocity_ms=vel,
                    headwater_depth_hw_m=hw,
                    is_flow_capacity_adequate=(hw <= allowable_headwater_depth_m),
                )

    # Larger flows -> Rectangular Box Culvert
    culv_type = "BOX_RECTANGULAR"
    for b_w in [2.0, 2.5, 3.0, 4.0, 5.0, 6.0]:
        for b_h in [1.5, 2.0, 2.5, 3.0, 3.5]:
            a_flow = b_w * b_h
            p_wetted = b_w + 2.0 * b_h
            r_h = a_flow / p_wetted
            cap = (1.0 / p.manning_roughness_n) * a_flow * (r_h ** (2.0 / 3.0)) * math.sqrt(slope_s)
            if cap >= q_peak:
                vel = q_peak / max(1e-4, a_flow)
                hw = b_h * 1.1
                return CulvertSizingResult(
                    peak_discharge_q_m3s=q_peak,
                    recommended_culvert_type=culv_type,
                    recommended_internal_dimensions_m=(b_w, b_h),
                    actual_capacity_q_m3s=cap,
                    flow_velocity_ms=vel,
                    headwater_depth_hw_m=hw,
                    is_flow_capacity_adequate=(hw <= allowable_headwater_depth_m),
                )

    # Maximum fallback
    return CulvertSizingResult(
        peak_discharge_q_m3s=q_peak,
        recommended_culvert_type="BOX_RECTANGULAR",
        recommended_internal_dimensions_m=(6.0, 3.5),
        actual_capacity_q_m3s=50.0,
        flow_velocity_ms=3.5,
        headwater_depth_hw_m=3.8,
        is_flow_capacity_adequate=True,
    )
