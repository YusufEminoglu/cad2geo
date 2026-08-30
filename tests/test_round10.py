# -*- coding: utf-8 -*-
"""Unit tests for cad2geo Round 10 features (Pavement Structural Number & Curb Inlet Hydraulics)."""

from __future__ import annotations

import unittest

from cad2geo import (
    CurbGutterFlowResult,
    CurbGutterProfile,
    PavementLayerConfig,
    PavementStructuralDesignResult,
    calculate_curb_inlet_hydraulic_capacity,
    calculate_flexible_pavement_structural_number,
)


class TestCad2GeoRound10(unittest.TestCase):
    def test_flexible_pavement_structural_number(self) -> None:
        layers = PavementLayerConfig(
            asphalt_surface_thickness_d1_inches=4.0,
            crushed_stone_base_thickness_d2_inches=8.0,
            subbase_thickness_d3_inches=10.0,
        )

        res = calculate_flexible_pavement_structural_number(
            design_traffic_esal_millions=4.0,
            subgrade_resilient_modulus_psi=7000.0,
            layers=layers,
        )

        self.assertIsInstance(res, PavementStructuralDesignResult)
        self.assertGreater(res.provided_structural_number_sn, 2.5)
        self.assertGreater(res.required_structural_number_sn, 1.5)
        self.assertGreater(res.total_pavement_thickness_cm, 30.0)

        d = res.to_dict()
        self.assertIn("required_sn", d)
        self.assertIn("provided_sn", d)
        self.assertIn("thickness_cm", d)

    def test_stormwater_curb_inlet_hydraulics(self) -> None:
        profile = CurbGutterProfile(
            longitudinal_slope_s0_pct=2.0,
            cross_slope_sx_pct=2.0,
            allowable_spread_width_t_m=2.5,
        )

        res = calculate_curb_inlet_hydraulic_capacity(gutter_discharge_q_m3s=0.050, profile=profile)

        self.assertIsInstance(res, CurbGutterFlowResult)
        self.assertGreater(res.gutter_flow_spread_t_m, 0.5)
        self.assertGreater(res.gutter_flow_depth_d_m, 0.01)
        self.assertGreater(res.grate_interception_efficiency_pct, 50.0)

        d = res.to_dict()
        self.assertIn("discharge_q_m3s", d)
        self.assertIn("spread_t_m", d)
        self.assertIn("efficiency_pct", d)
