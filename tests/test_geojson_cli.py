# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""GeoJSON and CLI behavior tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cad2geo.cli import main
from cad2geo.geojson import entities_to_feature_collection, write_geojson
from cad2geo.reader import parse_netcad
from tests import ncz_fixtures as fx


class TestGeoJsonAndCli(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="cad2geo-", dir=Path(__file__).resolve().parent))
        self.addCleanup(lambda: _rmtree(self.tmp))
        self.source = self.tmp / "fixture.ncz"
        self.source.write_bytes(fx.full_drawing())

    def test_entities_to_feature_collection(self) -> None:
        result = parse_netcad(self.source)
        collection = entities_to_feature_collection(result.entities)

        self.assertEqual(collection["type"], "FeatureCollection")
        self.assertGreaterEqual(len(collection["features"]), 8)
        self.assertIn(
            collection["features"][0]["geometry"]["type"],
            {"Point", "LineString", "Polygon"},
        )

    def test_write_geojson_round_trip(self) -> None:
        out = self.tmp / "out.geojson"
        result = parse_netcad(self.source)
        collection = write_geojson(result.entities, out)

        self.assertTrue(out.exists())
        self.assertEqual(json.loads(out.read_text(encoding="utf-8")), collection)

    def test_cli_inspect_json(self) -> None:
        self.assertEqual(main(["inspect", str(self.source), "--json"]), 0)

    def test_cli_convert(self) -> None:
        out = self.tmp / "selected.geojson"
        self.assertEqual(main(["convert", str(self.source), str(out), "--layers", "1"]), 0)
        payload = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(payload["type"], "FeatureCollection")
        self.assertTrue(payload["features"])
        self.assertTrue(
            all(feature["properties"]["layer_code"] == 1 for feature in payload["features"])
        )


def _rmtree(path: Path) -> None:
    import shutil

    shutil.rmtree(path, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
