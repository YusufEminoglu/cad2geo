# -*- coding: utf-8 -*-
"""Unit tests for cad2geo Round 8 features (Spiral Curve Transition & Culvert Sizing)."""

from __future__ import annotations

import unittest

from cad2geo import (
    CatchmentRunoffProfile,
    ClothoidTransitionResult,
    CulvertSizingResult,
    SpiralCurveParams,
    calculate_clothoid_spiral_curve,
    calculate_culvert_hydraulic_capacity,
)


class TestCad2GeoRound8(unittest.TestCase):
    def test_euler_clothoid_spiral_curve(self) -> None:
        params = SpiralCurveParams(
            spiral_parameter_a=150.0,
            circular_curve_radius_r=400.0,
            origin_point=(1000.0, 2000.0),
            initial_bearing_degrees=45.0,
        )

        res = calculate_clothoid_spiral_curve(params, num_sample_points=25)

        self.assertIsInstance(res, ClothoidTransitionResult)
        self.assertEqual(res.spiral_parameter_a, 150.0)
        self.assertGreater(res.spiral_length_l, 0.0)
        self.assertGreater(res.total_spiral_angle_deg, 0.0)
        self.assertGreater(res.shift_p_m, 0.0)
        self.assertEqual(len(res.spiral_points), 26)

        d = res.to_dict()
        self.assertIn("parameter_a", d)
        self.assertIn("shift_p_m", d)

    def test_hydrological_culvert_sizing(self) -> None:
        profile = CatchmentRunoffProfile(
            catchment_area_ha=30.0,
            runoff_coefficient_c=0.60,
            rainfall_intensity_mm_hr=70.0,
            culvert_slope_pct=2.0,
        )

        res = calculate_culvert_hydraulic_capacity(profile, allowable_headwater_depth_m=3.0)

        self.assertIsInstance(res, CulvertSizingResult)
        self.assertGreater(res.peak_discharge_q_m3s, 0.0)
        self.assertGreater(res.actual_capacity_q_m3s, res.peak_discharge_q_m3s)
        self.assertIn(res.recommended_culvert_type, ["PIPE_CIRCULAR", "BOX_RECTANGULAR"])
        self.assertTrue(res.is_flow_capacity_adequate)

        d = res.to_dict()
        self.assertIn("peak_q_m3s", d)
        self.assertIn("dimensions_m", d)
