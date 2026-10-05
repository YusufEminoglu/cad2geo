# -*- coding: utf-8 -*-
"""Highway Horizontal Curve Superelevation (Deve Kurpu) & Runoff Transition Designer for cad2geo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SuperelevationConfig:
    design_speed_kmh: float = 90.0
    curve_radius_r_m: float = 450.0
    normal_cross_slope_pct: float = 2.0  # Normal crown (-2.0%)
    lane_width_m: float = 3.65
    num_lanes_each_direction: int = 1
    max_superelevation_rate_pct: float = 8.0  # e_max = 8% standard
    transition_spiral_length_m: float = 60.0


@dataclass
class StationSuperelevationCrossSection:
    station_chainage_m: float
    left_edge_elevation_delta_m: float
    right_edge_elevation_delta_m: float
    cross_slope_pct: float


@dataclass
class SuperelevationDesignResult:
    design_superelevation_rate_pct: float
    tangent_runoff_length_m: float
    superelevation_runoff_length_m: float
    total_transition_length_m: float
    station_cross_sections: list[StationSuperelevationCrossSection]

    def to_dict(self) -> dict[str, Any]:
        return {
            "design_e_pct": round(self.design_superelevation_rate_pct, 2),
            "tangent_runoff_m": round(self.tangent_runoff_length_m, 1),
            "superelevation_runoff_m": round(self.superelevation_runoff_length_m, 1),
            "total_transition_m": round(self.total_transition_length_m, 1),
            "stations_count": len(self.station_cross_sections),
        }


def calculate_superelevation_runoff(
    config: SuperelevationConfig | None = None,
    station_sampling_interval_m: float = 10.0,
) -> SuperelevationDesignResult:
    """Compute AASHTO design superelevation rate (e), tangent runoff (Lt), and superelevation runoff (Lr).

    Formulae:
    e_design = (V^2) / (127 * R) - f_s
    L_r = (w * n_1 * e_d) / delta_relative_gradient
    L_t = (e_normal / e_d) * L_r
    """
    cfg = config or SuperelevationConfig()

    v = cfg.design_speed_kmh
    r = cfg.curve_radius_r_m

    # AASHTO Method 5 Superelevation distribution
    e_theoretical = ((v ** 2) / (127.0 * r)) * 100.0
    e_design = min(cfg.max_superelevation_rate_pct, max(cfg.normal_cross_slope_pct, e_theoretical * 0.45))

    # Relative maximum gradient (Delta)
    delta_grad = max(0.004, 0.0075 - 0.00004 * v)

    w = cfg.lane_width_m * cfg.num_lanes_each_direction
    l_r = (w * (e_design / 100.0)) / delta_grad
    l_t = (cfg.normal_cross_slope_pct / max(0.1, e_design)) * l_r
    tot_trans = l_t + l_r

    stations: list[StationSuperelevationCrossSection] = []
    num_steps = int(tot_trans // station_sampling_interval_m) + 1

    for i in range(num_steps):
        s_m = min(tot_trans, i * station_sampling_interval_m)

        if s_m <= l_t:
            # Transition from normal crown to flat outside lane
            frac = s_m / max(1.0, l_t)
            curr_e = -cfg.normal_cross_slope_pct + frac * cfg.normal_cross_slope_pct
        else:
            # Transition from flat to full superelevation e_design
            frac = (s_m - l_t) / max(1.0, l_r)
            curr_e = frac * e_design

        dz_left = -(w * (curr_e / 100.0))
        dz_right = w * (curr_e / 100.0)

        stations.append(
            StationSuperelevationCrossSection(
                station_chainage_m=s_m,
                left_edge_elevation_delta_m=round(dz_left, 3),
                right_edge_elevation_delta_m=round(dz_right, 3),
                cross_slope_pct=round(curr_e, 2),
            )
        )

    return SuperelevationDesignResult(
        design_superelevation_rate_pct=e_design,
        tangent_runoff_length_m=l_t,
        superelevation_runoff_length_m=l_r,
        total_transition_length_m=tot_trans,
        station_cross_sections=stations,
    )
