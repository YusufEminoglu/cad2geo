# -*- coding: utf-8 -*-
"""Unit tests for cad2geo DXF parsing and QA cleaner modules."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cad2geo import (
    DXFEntity,
    DXFReader,
    QARepairReport,
    clean_cad_entities,
    dxf_to_geojson,
    parse_dxf,
    parse_netcad,
    remove_duplicate_vertices,
    snap_endpoints,
)
from cad2geo.cli import main as cli_main
from cad2geo.ncz_engine.model import NetcadCoordinate, NetcadEntity
from tests import ncz_fixtures as fx

SAMPLE_DXF = """0
SECTION
2
ENTITIES
0
LINE
8
WALLS
62
1
10
0.0
20
0.0
30
0.0
11
100.0
21
50.0
31
0.0
0
LWPOLYLINE
8
PARCELS
62
3
70
1
10
0.0
20
0.0
30
0.0
10
50.0
20
0.0
30
0.0
10
50.0
20
50.0
30
0.0
10
0.0
20
50.0
30
0.0
0
TEXT
8
ANNOTATIONS
62
7
1
BUILDING_A
40
2.5
10
25.0
20
25.0
30
0.0
0
ENDSEC
0
EOF
"""


class TestDxfAndQaCleaner(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.temp_dir.name)
        self.dxf_file = self.tmp / "sample.dxf"
        self.dxf_file.write_text(SAMPLE_DXF, encoding="utf-8")

        self.ncz_file = self.tmp / "sample.ncz"
        self.ncz_file.write_bytes(fx.full_drawing())

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_dxf_reader_parses_entities(self) -> None:
        entities = parse_dxf(self.dxf_file)
        self.assertEqual(len(entities), 3)

        line_ent = entities[0]
        self.assertEqual(line_ent.kind, "LINE")
        self.assertEqual(line_ent.layer, "WALLS")
        self.assertEqual(line_ent.color_hex, "#FF0000")
        self.assertEqual(len(line_ent.coordinates), 2)

        poly_ent = entities[1]
        self.assertEqual(poly_ent.kind, "LWPOLYLINE")
        self.assertEqual(poly_ent.layer, "PARCELS")
        self.assertTrue(poly_ent.is_closed)
        self.assertEqual(len(poly_ent.coordinates), 4)

        text_ent = entities[2]
        self.assertEqual(text_ent.kind, "TEXT")
        self.assertEqual(text_ent.text, "BUILDING_A")

    def test_dxf_to_geojson_conversion(self) -> None:
        fc = dxf_to_geojson(self.dxf_file)
        self.assertEqual(fc["type"], "FeatureCollection")
        self.assertEqual(len(fc["features"]), 3)

        types = [f["geometry"]["type"] for f in fc["features"]]
        self.assertIn("LineString", types)
        self.assertIn("Polygon", types)
        self.assertIn("Point", types)

    def test_snap_endpoints(self) -> None:
        coords = [
            NetcadCoordinate(x=0.0, y=0.0),
            NetcadCoordinate(x=10.0, y=0.0),
            NetcadCoordinate(x=10.0, y=10.0),
            NetcadCoordinate(x=0.0, y=0.02),  # gap of 0.02
        ]
        snapped, did_snap = snap_endpoints(coords, tolerance=0.05)
        self.assertTrue(did_snap)
        self.assertEqual(snapped[0].x, snapped[-1].x)
        self.assertEqual(snapped[0].y, snapped[-1].y)

    def test_remove_duplicate_vertices(self) -> None:
        coords = [
            NetcadCoordinate(x=0.0, y=0.0),
            NetcadCoordinate(x=0.0, y=0.00001),  # duplicate
            NetcadCoordinate(x=10.0, y=0.0),
            NetcadCoordinate(x=10.0, y=0.0),  # duplicate
            NetcadCoordinate(x=20.0, y=0.0),
        ]
        cleaned, removed = remove_duplicate_vertices(coords, min_dist=1e-3)
        self.assertEqual(removed, 2)
        self.assertEqual(len(cleaned), 3)

    def test_clean_cad_entities_pipeline(self) -> None:
        raw_res = parse_netcad(self.ncz_file)
        cleaned, report = clean_cad_entities(raw_res.entities, snap_tolerance=0.1)

        self.assertIsInstance(report, QARepairReport)
        self.assertGreater(report.total_input_entities, 0)
        self.assertGreater(report.total_output_entities, 0)
        d = report.to_dict()
        self.assertIn("total_input_entities", d)

    def test_cli_dxf_and_clean(self) -> None:
        out_dxf_geo = self.tmp / "dxf_out.geojson"
        ret_dxf = cli_main(["dxf", str(self.dxf_file), str(out_dxf_geo)])
        self.assertEqual(ret_dxf, 0)
        self.assertTrue(out_dxf_geo.exists())

        out_clean_geo = self.tmp / "clean_out.geojson"
        ret_clean = cli_main(["clean", str(self.ncz_file), str(out_clean_geo)])
        self.assertEqual(ret_clean, 0)
        self.assertTrue(out_clean_geo.exists())
