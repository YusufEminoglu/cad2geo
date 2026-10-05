# -*- coding: utf-8 -*-
"""Highway Curb Gutter Flow Spread & Inflow Grate Hydraulic Capacity (HEC-22) for cad2geo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CurbGutterProfile:
    longitudinal_slope_s0_pct: float = 1.5  # S0
    cross_slope_sx_pct: float = 2.0  # Sx
    manning_roughness_n: float = 0.016  # Asphalt / concrete gutter
    allowable_spread_width_t_m: float = 2.5  # Max shoulder flood spread
    grate_length_m: float = 1.0
    grate_width_m: float = 0.60


@dataclass
class CurbGutterFlowResult:
    design_discharge_q_m3s: float
    gutter_flow_spread_t_m: float
    gutter_flow_depth_d_m: float
    is_within_allowable_spread: bool
    grate_interception_efficiency_pct: float
    bypass_discharge_q_m3s: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "discharge_q_m3s": round(self.design_discharge_q_m3s, 3),
            "spread_t_m": round(self.gutter_flow_spread_t_m, 2),
            "depth_d_m": round(self.gutter_flow_depth_d_m, 3),
            "is_spread_ok": self.is_within_allowable_spread,
            "efficiency_pct": round(self.grate_interception_efficiency_pct, 1),
            "bypass_q_m3s": round(self.bypass_discharge_q_m3s, 3),
        }


def calculate_curb_inlet_hydraulic_capacity(
    gutter_discharge_q_m3s: float = 0.065,  # 65 L/s peak runoff
    profile: CurbGutterProfile | None = None,
) -> CurbGutterFlowResult:
    """Compute FHWA HEC-22 Manning modified triangular gutter flow spread and grate inlet interception capacity.

    Modified Manning's Equation for Triangular Gutter Flow:
    Q = (K_m / n) * S_x^(5/3) * S_0^(1/2) * T^(8/3)  where K_m = 0.376 (SI)
    T = ( (Q * n) / (0.376 * S_x^(5/3) * S_0^(1/2)) )^(3/8)
    Depth at curb: d = T * S_x
    """
    p = profile or CurbGutterProfile()
    s0 = max(0.001, p.longitudinal_slope_s0_pct / 100.0)
    sx = max(0.005, p.cross_slope_sx_pct / 100.0)
    q = max(0.001, gutter_discharge_q_m3s)

    # Solve for spread T (m)
    km = 0.376
    numerator = q * p.manning_roughness_n
    denominator = km * (sx ** (5.0 / 3.0)) * (s0 ** 0.5)
    spread_t = (numerator / max(1e-6, denominator)) ** (3.0 / 8.0)

    depth_d = spread_t * sx

    # FHWA HEC-22 Frontal Flow Ratio for Triangular Gutters:
    # E_o = 1 - (1 - W/T)^2.67
    w_ratio = min(1.0, max(0.0, p.grate_width_m / max(0.01, spread_t)))
    frontal_flow_ratio = 1.0 - ((1.0 - w_ratio) ** 2.67)

    # Grate efficiency E = R_f * E_o
    interception_eff = min(100.0, max(10.0, frontal_flow_ratio * 100.0 * 0.95))
    intercepted_q = q * (interception_eff / 100.0)
    bypass_q = q - intercepted_q

    is_ok = spread_t <= p.allowable_spread_width_t_m

    return CurbGutterFlowResult(
        design_discharge_q_m3s=q,
        gutter_flow_spread_t_m=spread_t,
        gutter_flow_depth_d_m=depth_d,
        is_within_allowable_spread=is_ok,
        grate_interception_efficiency_pct=interception_eff,
        bypass_discharge_q_m3s=bypass_q,
    )
