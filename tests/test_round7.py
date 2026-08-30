# -*- coding: utf-8 -*-
"""Unit tests for cad2geo Round 7 features (Sight Triangle & Cross Section Generator)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cad2geo import (
    CrossSectionProfile,
    IntersectionLegProfile,
    SightTriangleResult,
    StationCrossSectionSet,
    evaluate_intersection_sight_triangles,
    generate_road_cross_sections,
)


class TestCad2GeoRound7(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_intersection_sight_distance_triangle(self) -> None:
        major = IntersectionLegProfile(leg_id="Major_East", design_speed_kmh=50.0)
        minor = IntersectionLegProfile(leg_id="Minor_North", design_speed_kmh=30.0, is_major_road=False)

        # Clear case
        res_clear = evaluate_intersection_sight_triangles(
            intersection_vertex_2d=(0.0, 0.0),
            major_road_direction_deg=0.0,
            minor_road_direction_deg=90.0,
            major_leg=major,
            minor_leg=minor,
            cad_obstacles=[{"id": "Far_Tree", "position": (500.0, 500.0)}],
        )

        self.assertIsInstance(res_clear, SightTriangleResult)
        self.assertTrue(res_clear.is_clear_of_obstructions)
        self.assertGreater(res_clear.approach_sight_distance_major_m, 50.0)

        # Obstructed case (obstacle inside triangle)
        res_obs = evaluate_intersection_sight_triangles(
            intersection_vertex_2d=(0.0, 0.0),
            major_road_direction_deg=0.0,
            minor_road_direction_deg=90.0,
            major_leg=major,
            minor_leg=minor,
            cad_obstacles=[{"id": "Corner_Billboard", "position": (10.0, 2.0)}],
        )

        self.assertFalse(res_obs.is_clear_of_obstructions)
        self.assertEqual(res_obs.obstructing_features_count, 1)

    def test_road_cross_section_generator(self) -> None:
        centerline = [(0.0, 0.0, 10.0), (100.0, 0.0, 12.0), (200.0, 0.0, 15.0)]
        xsections = generate_road_cross_sections(centerline, station_interval_m=25.0)

        self.assertIsInstance(xsections, StationCrossSectionSet)
        self.assertGreater(xsections.total_sections_count, 4)
        self.assertEqual(len(xsections.sections[0].profile_points_offset_z), 5)

        dxf_path = self.tmp / "cross_sections.dxf"
        xsections.export_dxf(dxf_path)
        self.assertTrue(dxf_path.exists())
        self.assertIn("ROAD_PROFILE", dxf_path.read_text(encoding="utf-8"))
