# -*- coding: utf-8 -*-
"""Unit tests for cad2geo Round 5 features (TIN Contours & Dimension Parser)."""

from __future__ import annotations

import unittest

from cad2geo import (
    ContourIsoline,
    DimensionEntity,
    DimensionSummary,
    TINSurfaceMesh,
    extract_cad_dimensions,
    generate_tin_contours,
)


class TestCad2GeoRound5(unittest.TestCase):
    def test_tin_contour_generator(self) -> None:
        pts = [
            (0.0, 0.0, 10.0),
            (100.0, 0.0, 15.0),
            (100.0, 100.0, 25.0),
            (0.0, 100.0, 20.0),
            (50.0, 50.0, 30.0),
        ]

        mesh = generate_tin_contours(pts, contour_interval_m=5.0, index_interval_m=10.0)
        self.assertIsInstance(mesh, TINSurfaceMesh)
        self.assertEqual(mesh.total_vertices, 5)
        self.assertGreater(mesh.total_triangles, 0)
        self.assertEqual(mesh.min_elevation_z, 10.0)
        self.assertEqual(mesh.max_elevation_z, 30.0)
        self.assertGreater(len(mesh.contours), 0)

        geojson = mesh.to_geojson()
        self.assertEqual(geojson["type"], "FeatureCollection")
        self.assertGreater(len(geojson["features"]), 0)

    def test_dimension_parser_qa(self) -> None:
        raw_dims = [
            # Accurate dimension (50.0m)
            {"dim_type": "ALIGNED", "p1": (0.0, 0.0), "p2": (50.0, 0.0), "measurement": "50.00", "layer": "DIM"},
            # Discrepancy (drawn 100m, labeled 120m)
            {"dim_type": "LINEAR", "p1": (0.0, 0.0), "p2": (100.0, 0.0), "measurement": "120.00", "layer": "DIM"},
        ]

        summary = extract_cad_dimensions(raw_dims, tolerance_m=0.05)
        self.assertIsInstance(summary, DimensionSummary)
        self.assertEqual(summary.total_dimensions, 2)
        self.assertEqual(summary.accurate_count, 1)
        self.assertEqual(summary.discrepancies_count, 1)
        self.assertGreater(summary.max_deviation_m, 10.0)

        d = summary.to_dict()
        self.assertIn("accurate_count", d)
        self.assertIn("discrepancies_count", d)
