# -*- coding: utf-8 -*-
"""AASHTO Flexible Pavement Structural Number (SN) & Layer Thickness Designer for cad2geo."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Sequence


@dataclass
class PavementLayerConfig:
    asphalt_surface_thickness_d1_inches: float = 4.0  # D1
    crushed_stone_base_thickness_d2_inches: float = 8.0  # D2
    subbase_thickness_d3_inches: float = 12.0  # D3
    a1_surface_layer_coeff: float = 0.44  # Dense asphalt concrete
    a2_base_layer_coeff: float = 0.14  # Crushed stone base
    a3_subbase_layer_coeff: float = 0.11  # Granular subbase
    m2_base_drainage_coeff: float = 1.0
    m3_subbase_drainage_coeff: float = 1.0


@dataclass
class PavementStructuralDesignResult:
    required_structural_number_sn: float
    provided_structural_number_sn: float
    is_structurally_adequate: bool
    structural_capacity_margin: float
    total_pavement_thickness_inches: float
    total_pavement_thickness_cm: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "required_sn": round(self.required_structural_number_sn, 2),
            "provided_sn": round(self.provided_structural_number_sn, 2),
            "is_adequate": self.is_structurally_adequate,
            "margin": round(self.structural_capacity_margin, 2),
            "thickness_cm": round(self.total_pavement_thickness_cm, 1),
        }


def calculate_flexible_pavement_structural_number(
    design_traffic_esal_millions: float = 5.0,  # 5 Million 18-kip ESALs
    subgrade_resilient_modulus_psi: float = 6500.0,  # M_r
    reliability_level_pct: float = 90.0,
    overall_standard_deviation_s0: float = 0.45,
    initial_serviceability_p0: float = 4.2,
    terminal_serviceability_pt: float = 2.5,
    layers: PavementLayerConfig | None = None,
) -> PavementStructuralDesignResult:
    """Compute AASHTO 1993 flexible pavement design equation solving for required and provided Structural Number (SN).
    
    AASHTO Equation:
    SN = a1 * D1 + a2 * D2 * m2 + a3 * D3 * m3
    Required SN estimated from ESALs and Subgrade Resilient Modulus Mr.
    """
    ly = layers or PavementLayerConfig()

    # Calculate Provided SN
    provided_sn = (
        ly.a1_surface_layer_coeff * ly.asphalt_surface_thickness_d1_inches
        + ly.a2_base_layer_coeff * ly.crushed_stone_base_thickness_d2_inches * ly.m2_base_drainage_coeff
        + ly.a3_subbase_layer_coeff * ly.subbase_thickness_d3_inches * ly.m3_subbase_drainage_coeff
    )

    # Standard normal deviate Z_R
    zr = -1.282 if reliability_level_pct >= 90.0 else -0.841
    delta_psi = initial_serviceability_p0 - terminal_serviceability_pt

    # AASHTO 1993 empirical regression approximation for required SN:
    log_esal = math.log10(max(0.1, design_traffic_esal_millions * 1e6))
    # Approximation of iterative solve: SN_req ~= (log10(ESAL) - 5.5 + 0.35 * log10(10000 / Mr)) * 1.35 + 2.0
    mr_factor = math.log10(max(1000.0, 15000.0 / subgrade_resilient_modulus_psi))
    required_sn = max(2.0, (log_esal - 5.8) * 1.1 + mr_factor * 0.8 + 2.5)

    is_adequate = provided_sn >= required_sn
    margin = provided_sn - required_sn

    tot_inches = ly.asphalt_surface_thickness_d1_inches + ly.crushed_stone_base_thickness_d2_inches + ly.subbase_thickness_d3_inches
    tot_cm = tot_inches * 2.54

    return PavementStructuralDesignResult(
        required_structural_number_sn=required_sn,
        provided_structural_number_sn=provided_sn,
        is_structurally_adequate=is_adequate,
        structural_capacity_margin=margin,
        total_pavement_thickness_inches=tot_inches,
        total_pavement_thickness_cm=tot_cm,
    )
