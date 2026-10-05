# -*- coding: utf-8 -*-
"""Unit tests for cad2geo Round 4 features (Annotation Matcher & Block Extractor)."""

from __future__ import annotations

import unittest

from cad2geo import (
    AnnotationMatchResult,
    CADBlockLibrary,
    extract_cad_blocks,
    link_annotations_to_polygons,
)


class TestCad2GeoRound4(unittest.TestCase):
    def test_spatial_annotation_matching(self) -> None:
        polygons = [
            {"layer": "PARCEL", "coordinates": [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]},
            {"layer": "PARCEL", "coordinates": [(20.0, 0.0), (30.0, 0.0), (30.0, 10.0), (20.0, 10.0), (20.0, 0.0)]},
        ]
        annotations = [
            {"text": "Ada 101 / Parsel 1", "position": (5.0, 5.0)},  # Inside poly 0
            {"text": "Ada 101 / Parsel 2", "position": (25.0, 5.0)}, # Inside poly 1
            {"text": "Street Label", "position": (15.0, 5.0)},       # Outside but near
        ]

        res = link_annotations_to_polygons(polygons, annotations, max_search_radius=20.0)
        self.assertIsInstance(res, AnnotationMatchResult)
        self.assertEqual(res.total_annotations_processed, 3)
        self.assertEqual(res.matched_count, 3)
        self.assertEqual(res.matches[0].match_type, "CONTAINS")
        self.assertEqual(res.matches[0].matched_text, "Ada 101 / Parsel 1")

        d = res.to_dict()
        self.assertIn("match_rate_pct", d)

    def test_cad_block_extractor(self) -> None:
        inserts = [
            {
                "block_name": "TREE_OAK",
                "position": (100.0, 200.0, 5.0),
                "rotation": 45.0,
                "layer": "LANDSCAPE",
                "attributes": {"HEIGHT": "8.5", "SPECIES": "Quercus robur"},
            },
            {
                "block_name": "MANHOLE",
                "position": (150.0, 220.0),
                "layer": "UTILITY",
                "attributes": {"DEPTH": "2.4", "TYPE": "STORM"},
            },
        ]

        library = extract_cad_blocks(inserts)
        self.assertIsInstance(library, CADBlockLibrary)
        self.assertEqual(library.total_blocks_found, 2)
        self.assertEqual(len(library.unique_block_names), 2)
        self.assertEqual(library.instances[0].attributes["SPECIES"], "Quercus robur")

        fc = library.to_geojson_feature_collection()
        self.assertEqual(fc["type"], "FeatureCollection")
        self.assertEqual(len(fc["features"]), 2)
        self.assertEqual(fc["features"][0]["geometry"]["type"], "Point")
