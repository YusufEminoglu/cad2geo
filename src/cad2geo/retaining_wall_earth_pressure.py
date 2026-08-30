# -*- coding: utf-8 -*-
"""Roadside Retaining Wall Lateral Earth Pressure & Stability Engine (Rankine/Coulomb) for cad2geo."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Sequence


@dataclass
class SoilWallParameters:
    wall_height_h_m: float = 5.0
    wall_base_width_b_m: float = 2.8
    soil_unit_weight_kn_m3: float = 19.0  # gamma
    internal_friction_angle_phi_deg: float = 32.0  # phi
    cohesion_c_kpa: float = 0.0
    soil_friction_delta_deg: float = 20.0  # delta
    concrete_unit_weight_kn_m3: float = 24.0
    backfill_slope_beta_deg: float = 0.0
    surcharge_load_q_kpa: float = 10.0  # Highway traffic surcharge (q)


@dataclass
class RetainingWallStabilityResult:
    active_earth_pressure_coeff_ka: float
    total_active_thrust_pa_kn_m: float
    resisting_moment_knm_m: float
    overturning_moment_knm_m: float
    safety_factor_overturning: float
    safety_factor_sliding: float
    is_wall_stable: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "ka": round(self.active_earth_pressure_coeff_ka, 3),
            "thrust_pa_kn_m": round(self.total_active_thrust_pa_kn_m, 2),
            "fs_overturning": round(self.safety_factor_overturning, 2),
            "fs_sliding": round(self.safety_factor_sliding, 2),
            "is_stable": self.is_wall_stable,
        }


def evaluate_retaining_wall_stability(
    params: SoilWallParameters | None = None,
    min_fs_overturning: float = 2.0,
    min_fs_sliding: float = 1.5,
) -> RetainingWallStabilityResult:
    """Compute lateral active earth thrust (Rankine) and factors of safety against overturning and sliding."""
    p = params or SoilWallParameters()

    phi_rad = math.radians(p.internal_friction_angle_phi_deg)
    # Rankine Ka = (1 - sin(phi)) / (1 + sin(phi)) = tan^2(45 - phi/2)
    ka = (1.0 - math.sin(phi_rad)) / (1.0 + math.sin(phi_rad))

    h = p.wall_height_h_m
    b = p.wall_base_width_b_m

    # Active thrust components:
    # 1. Soil triangular pressure: P_a1 = 0.5 * gamma * H^2 * Ka
    p_a1 = 0.5 * p.soil_unit_weight_kn_m3 * (h ** 2) * ka
    # 2. Surcharge rectangular pressure: P_a2 = q * H * Ka
    p_a2 = p.surcharge_load_q_kpa * h * ka
    tot_thrust = p_a1 + p_a2

    # Overturning moment about toe (point O):
    # M_ov = P_a1 * (H/3) + P_a2 * (H/2)
    m_ov = p_a1 * (h / 3.0) + p_a2 * (h / 2.0)

    # Weight of cantilever stem, base slab, and soil block on heel:
    w_wall_concrete = (0.45 * h + b * 0.6) * p.concrete_unit_weight_kn_m3
    w_soil_heel = (b * 0.65) * (h * 0.9) * p.soil_unit_weight_kn_m3
    tot_vertical_w = w_wall_concrete + w_soil_heel

    # Resisting moment about toe:
    lever_arm = b * 0.50
    m_res = tot_vertical_w * lever_arm

    fs_ov = m_res / max(1e-4, m_ov)

    # Sliding safety factor: FS_slide = (W * tan(phi_base) + B * c_base) / P_active
    phi_base_rad = math.radians(p.internal_friction_angle_phi_deg)
    resisting_sliding_force = tot_vertical_w * math.tan(phi_base_rad) * 0.95
    fs_slide = resisting_sliding_force / max(1e-4, tot_thrust)

    is_stable = (fs_ov >= min_fs_overturning) and (fs_slide >= min_fs_sliding)

    return RetainingWallStabilityResult(
        active_earth_pressure_coeff_ka=ka,
        total_active_thrust_pa_kn_m=tot_thrust,
        resisting_moment_knm_m=m_res,
        overturning_moment_knm_m=m_ov,
        safety_factor_overturning=fs_ov,
        safety_factor_sliding=fs_slide,
        is_wall_stable=is_stable,
    )
