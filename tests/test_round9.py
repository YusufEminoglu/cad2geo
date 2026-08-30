# -*- coding: utf-8 -*-
"""Unit tests for cad2geo Round 9 features (Superelevation Runoff & Retaining Wall Stability)."""

from __future__ import annotations

import unittest

from cad2geo import (
    RetainingWallStabilityResult,
    SoilWallParameters,
    StationSuperelevationCrossSection,
    SuperelevationConfig,
    SuperelevationDesignResult,
    calculate_superelevation_runoff,
    evaluate_retaining_wall_stability,
)


class TestCad2GeoRound9(unittest.TestCase):
    def test_superelevation_runoff_designer(self) -> None:
        cfg = SuperelevationConfig(
            design_speed_kmh=80.0,
            curve_radius_r_m=400.0,
            lane_width_m=3.75,
            max_superelevation_rate_pct=8.0,
        )

        res = calculate_superelevation_runoff(cfg, station_sampling_interval_m=10.0)

        self.assertIsInstance(res, SuperelevationDesignResult)
        self.assertGreater(res.design_superelevation_rate_pct, 2.0)
        self.assertGreater(res.superelevation_runoff_length_m, 0.0)
        self.assertGreater(len(res.station_cross_sections), 3)

        d = res.to_dict()
        self.assertIn("design_e_pct", d)
        self.assertIn("superelevation_runoff_m", d)

    def test_retaining_wall_stability(self) -> None:
        params = SoilWallParameters(
            wall_height_h_m=4.5,
            wall_base_width_b_m=2.5,
            soil_unit_weight_kn_m3=18.5,
            internal_friction_angle_phi_deg=30.0,
        )

        res = evaluate_retaining_wall_stability(params)

        self.assertIsInstance(res, RetainingWallStabilityResult)
        self.assertGreater(res.active_earth_pressure_coeff_ka, 0.2)
        self.assertGreater(res.total_active_thrust_pa_kn_m, 0.0)
        self.assertGreater(res.safety_factor_overturning, 1.0)
        self.assertGreater(res.safety_factor_sliding, 1.0)

        d = res.to_dict()
        self.assertIn("ka", d)
        self.assertIn("fs_overturning", d)
        self.assertIn("fs_sliding", d)
