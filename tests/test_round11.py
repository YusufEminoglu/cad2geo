# -*- coding: utf-8 -*-
"""Unit tests for cad2geo Round 11 features (Bishop Slope Stability & CRTN Traffic Noise)."""

from __future__ import annotations

import unittest

from cad2geo import (
    BishopStabilityResult,
    RoadAcousticProfile,
    SlopeSliceProfile,
    TrafficNoiseResult,
    calculate_crtn_noise_propagation,
    evaluate_bishop_slope_stability,
)


class TestCad2GeoRound11(unittest.TestCase):
    def test_bishop_slope_stability(self) -> None:
        prof = SlopeSliceProfile(
            cohesion_c_kpa=18.0,
            friction_angle_phi_deg=30.0,
            soil_unit_weight_gamma_kn_m3=19.0,
            pore_water_pressure_ratio_ru=0.10,
            embankment_height_h_m=7.5,
        )

        res = evaluate_bishop_slope_stability(profile=prof, num_slices=12)

        self.assertIsInstance(res, BishopStabilityResult)
        self.assertGreater(res.factor_of_safety_bishop, 0.8)
        self.assertGreater(res.critical_slip_circle_radius_m, 5.0)
        self.assertGreater(res.iterations_to_convergence, 0)

        d = res.to_dict()
        self.assertIn("fs_bishop", d)
        self.assertIn("is_stable", d)
        self.assertIn("radius_m", d)

    def test_crtn_traffic_noise_propagation(self) -> None:
        prof = RoadAcousticProfile(
            traffic_flow_vehicles_per_hour=3000.0,
            heavy_vehicles_percentage=12.0,
            average_traffic_speed_kmh=90.0,
            road_gradient_pct=2.0,
        )

        res = calculate_crtn_noise_propagation(receiver_distance_m=40.0, profile=prof)

        self.assertIsInstance(res, TrafficNoiseResult)
        self.assertGreater(res.basic_noise_level_l10_18h_db, 60.0)
        self.assertGreater(res.facade_noise_level_l10_db, 40.0)
        self.assertGreater(res.equivalent_day_evening_night_lden_db, 40.0)

        d = res.to_dict()
        self.assertIn("l10_18h_db", d)
        self.assertIn("facade_l10_db", d)
        self.assertIn("lden_db", d)
