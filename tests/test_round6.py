# -*- coding: utf-8 -*-
"""Unit tests for cad2geo Round 6 features (Cut & Fill Balancer & Spline Densifier)."""

from __future__ import annotations

import unittest

from cad2geo import (
    CutFillVolumeReport,
    SplineDensificationResult,
    calculate_earthwork_cut_fill,
    densify_cad_splines,
)


class TestCad2GeoRound6(unittest.TestCase):
    def test_cut_and_fill_volume_balancer(self) -> None:
        # Existing terrain (average 15m) vs Design flat surface (12m) -> net CUT
        terrain = [(0.0, 0.0, 15.0), (10.0, 0.0, 16.0), (10.0, 10.0, 14.0), (0.0, 10.0, 15.0)]
        design = [(0.0, 0.0, 12.0), (10.0, 0.0, 12.0), (10.0, 10.0, 12.0), (0.0, 10.0, 12.0)]

        rep = calculate_earthwork_cut_fill(terrain, design, cell_size_m=5.0)

        self.assertIsInstance(rep, CutFillVolumeReport)
        self.assertGreater(rep.total_cut_volume_m3, 0.0)
        self.assertEqual(rep.total_fill_volume_m3, 0.0)
        self.assertLess(rep.net_earthwork_balance_m3, 0.0)
        self.assertEqual(len(rep.cells), 4)

        d = rep.to_dict()
        self.assertIn("total_cut_m3", d)
        self.assertIn("net_balance_m3", d)

    def test_cad_spline_densifier(self) -> None:
        ctrl_pts = [(0.0, 0.0), (25.0, 50.0), (75.0, 50.0), (100.0, 0.0)]
        res = densify_cad_splines(ctrl_pts, samples_per_segment=8, max_segment_length_m=5.0)

        self.assertIsInstance(res, SplineDensificationResult)
        self.assertEqual(res.original_points_count, 4)
        self.assertGreater(res.densified_points_count, 4)
        self.assertGreater(res.total_curve_length_m, 100.0)

        geojson_feature = res.to_geojson_feature({"layer": "ROAD_ALIGNMENT"})
        self.assertEqual(geojson_feature["geometry"]["type"], "LineString")
        self.assertEqual(len(geojson_feature["geometry"]["coordinates"]), res.densified_points_count)
