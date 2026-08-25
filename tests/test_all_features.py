# -*- coding: utf-8 -*-
"""Comprehensive test suite for cad2geo."""

import os
import tempfile
import unittest

import cad2geo


class TestCad2Geo(unittest.TestCase):
    def test_crs_detection(self) -> None:
        # Test TM30 TUREF
        crs1 = cad2geo.detect_crs(proj_text="TUREF / 3 / Zone 30")
        self.assertIsNotNone(crs1)
        self.assertEqual(crs1.epsg, 5254)

        # Test ED50 TM27
        crs2 = cad2geo.detect_crs(proj_text="ED50 / TM27")
        self.assertIsNotNone(crs2)
        self.assertEqual(crs2.epsg, 2319)

        # Test 3-Degree Gauss-Krüger with millionth easting
        gk_coords = [(10_500_000.0, 4_200_000.0), (10_500_100.0, 4_200_100.0)]
        crs3 = cad2geo.detect_crs(coords=gk_coords)
        self.assertIsNotNone(crs3)
        self.assertIn(crs3.epsg, [5270, 2207])

        # Test WGS84 decimal degrees
        wgs_coords = [(27.14, 38.42), (27.15, 38.43)]
        crs4 = cad2geo.detect_crs(coords=wgs_coords)
        self.assertIsNotNone(crs4)
        self.assertEqual(crs4.epsg, 4326)

    def test_csv_coordinate_sniffer(self) -> None:
        sample_csv = """Nokta_No,Saga,Yukari,Kot,Kod
P1,500120.50,4200350.20,125.40,POL
P2,500145.20,4200390.80,126.10,POL
P3,500180.00,4200340.00,124.80,POL
"""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
            tmp.write(sample_csv)
            tmp_path = tmp.name

        try:
            profile = cad2geo.sniff_csv_coordinates(tmp_path)
            self.assertEqual(profile.delimiter, ",")
            self.assertEqual(profile.x_field, "Saga")
            self.assertEqual(profile.y_field, "Yukari")
            self.assertEqual(profile.z_field, "Kot")
            self.assertEqual(profile.id_field, "Nokta_No")

            geojson = cad2geo.csv_to_geojson(tmp_path, profile)
            self.assertEqual(len(geojson["features"]), 3)
            self.assertEqual(geojson["features"][0]["geometry"]["coordinates"][0], 500120.50)
            self.assertEqual(geojson["features"][0]["properties"]["Kod"], "POL")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_mpyy_classification(self) -> None:
        # Residential
        c1 = cad2geo.classify_cad_layer("1_KONUT_ALANI")
        self.assertTrue(c1.is_matched)
        self.assertEqual(c1.code, "RESIDENTIAL")
        self.assertEqual(c1.color, "#FFD700")

        # Commercial
        c2 = cad2geo.classify_cad_layer("TICARET_MERKEZI")
        self.assertTrue(c2.is_matched)
        self.assertEqual(c2.code, "COMMERCIAL")

        # Green / Park
        c3 = cad2geo.classify_cad_layer("COCUK_BAHCESI_PARK")
        self.assertTrue(c3.is_matched)
        self.assertEqual(c3.code, "GREEN")

        # Unclassified
        c4 = cad2geo.classify_cad_layer("UNKNOWN_LAYER_XYZ")
        self.assertFalse(c4.is_matched)
        self.assertEqual(c4.code, "UNCLASSIFIED")

    def test_topology_and_polygonize(self) -> None:
        # Unclosed segments forming a rectangle: (0,0)->(10,0), (10,0)->(10,10), (10,10)->(0,10), (0,10)->(0,0)
        lines = [
            [(0.0, 0.0), (10.0, 0.0)],
            [(10.0, 0.0), (10.0, 10.0)],
            [(10.0, 10.0), (0.0, 10.0)],
            [(0.0, 10.0), (0.0, 0.0)],
        ]
        rings = cad2geo.polygonize_cad_lines(lines, tolerance=0.01)
        self.assertEqual(len(rings), 1)
        self.assertEqual(rings[0][0], rings[0][-1])  # Exact closure

        # Layer splitting
        features = [
            {"type": "Feature", "properties": {"layer": "YOL"}},
            {"type": "Feature", "properties": {"layer": "KONUT"}},
            {"type": "Feature", "properties": {"layer": "YOL"}},
        ]
        layers = cad2geo.split_features_by_cad_layer(features)
        self.assertEqual(len(layers["YOL"]), 2)
        self.assertEqual(len(layers["KONUT"]), 1)


if __name__ == "__main__":
    unittest.main()
