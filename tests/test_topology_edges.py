# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""Edge-case tests for the CAD topology helpers."""

from __future__ import annotations

import unittest

from cad2geo.topology import polygonize_cad_lines, split_features_by_cad_layer


class TestPolygonizeEdges(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(polygonize_cad_lines([]), [])

    def test_degenerate_segments_dropped(self) -> None:
        # A single-vertex "line" is invalid and cannot form a ring.
        self.assertEqual(polygonize_cad_lines([[(1.0, 1.0)]]), [])

    def test_already_closed_ring(self) -> None:
        ring = [(0.0, 0.0), (5.0, 0.0), (5.0, 5.0), (0.0, 5.0), (0.0, 0.0)]
        rings = polygonize_cad_lines([ring])
        self.assertEqual(len(rings), 1)
        self.assertEqual(rings[0][0], rings[0][-1])

    def test_reverse_chaining(self) -> None:
        # Segments are deliberately supplied with mixed orientations so the
        # head/tail and tail/tail matching branches are exercised.
        lines = [
            [(0.0, 0.0), (10.0, 0.0)],
            [(10.0, 10.0), (10.0, 0.0)],  # tail matches candidate tail
            [(0.0, 10.0), (10.0, 10.0)],
            [(0.0, 0.0), (0.0, 10.0)],  # head matches candidate head
        ]
        rings = polygonize_cad_lines(lines, tolerance=0.01)
        self.assertEqual(len(rings), 1)
        self.assertEqual(rings[0][0], rings[0][-1])
        self.assertGreaterEqual(len(rings[0]), 5)


class TestSplitFeaturesEdges(unittest.TestCase):
    def test_missing_layer_defaults_to_zero(self) -> None:
        features = [
            {"type": "Feature", "properties": {}},
            {"type": "Feature", "properties": {"layer_name": "YOL"}},
            {"type": "Feature", "properties": {"Layer": "PARK"}},
        ]
        layers = split_features_by_cad_layer(features)
        self.assertEqual(len(layers["0"]), 1)
        self.assertEqual(len(layers["YOL"]), 1)
        self.assertEqual(len(layers["PARK"]), 1)


if __name__ == "__main__":
    unittest.main()
