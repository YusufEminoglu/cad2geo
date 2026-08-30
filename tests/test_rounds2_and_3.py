# -*- coding: utf-8 -*-
"""Unit tests for cad2geo Rounds 2 and 3 features (Vector Exporters, Spatial Ops, Hatches, Tile Slicer)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cad2geo import (
    CADSpatialIndex,
    CADTilePyramid,
    buffer_point,
    buffer_polyline,
    export_flat_geobuf_schema,
    export_geoparquet_metadata,
    export_to_esri_shapefile_asc,
    parse_cad_hatches,
    parse_netcad,
    point_in_polygon,
    slice_cad_to_tile_pyramid,
)
from cad2geo.ncz_engine.model import NetcadCoordinate, NetcadEntity
from tests import ncz_fixtures as fx


class TestCad2GeoRounds2And3(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.temp_dir.name)
        self.ncz_file = self.tmp / "sample.ncz"
        self.ncz_file.write_bytes(fx.full_drawing())

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_point_in_polygon_and_buffers(self) -> None:
        poly = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        self.assertTrue(point_in_polygon(5.0, 5.0, poly))
        self.assertFalse(point_in_polygon(15.0, 5.0, poly))

        pt_buf = buffer_point(5.0, 5.0, radius=2.0)
        self.assertGreater(len(pt_buf), 4)

        line_coords = [NetcadCoordinate(x=0.0, y=0.0), NetcadCoordinate(x=50.0, y=0.0)]
        line_buf = buffer_polyline(line_coords, distance=5.0)
        self.assertGreater(len(line_buf), 4)

    def test_spatial_index(self) -> None:
        idx = CADSpatialIndex(cell_size=50.0)
        e1 = NetcadEntity(geometry_kind="POINT", layer_code=0, layer_name="P1", coordinates=[NetcadCoordinate(x=10.0, y=10.0)])
        e2 = NetcadEntity(geometry_kind="POINT", layer_code=0, layer_name="P2", coordinates=[NetcadCoordinate(x=200.0, y=200.0)])

        idx.insert(e1)
        idx.insert(e2)

        hits = idx.query_bbox(0.0, 0.0, 50.0, 50.0)
        self.assertIn(e1, hits)
        self.assertNotIn(e2, hits)

    def test_vector_exporters(self) -> None:
        res = parse_netcad(self.ncz_file)
        asc_path = self.tmp / "out.asc"
        export_to_esri_shapefile_asc(res.entities, asc_path)
        self.assertTrue(asc_path.exists())

        gp_meta = export_geoparquet_metadata(res.entities)
        self.assertEqual(gp_meta["version"], "1.0.0")

        fgb_schema = export_flat_geobuf_schema(res.entities)
        self.assertEqual(fgb_schema["geometry_type"], "GeometryCollection")

    def test_hatches_and_tile_pyramid(self) -> None:
        hatch = parse_cad_hatches("LAYER_ANSI31_WALLS")
        self.assertEqual(hatch.pattern_name, "ANSI31")

        res = parse_netcad(self.ncz_file)
        pyramid = slice_cad_to_tile_pyramid(res.entities, min_zoom=0, max_zoom=2)
        self.assertIsInstance(pyramid, CADTilePyramid)
        self.assertGreater(pyramid.total_tiles, 0)
        d = pyramid.to_dict()
        self.assertIn("total_tiles", d)
