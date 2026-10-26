# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""Regressions and edge cases for the DXF, CSV, QA, topology and engineering helpers."""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import cad2geo
from cad2geo.cli import main as cli_main
from cad2geo.csv_sniffer import csv_to_geojson, sniff_csv_coordinates
from cad2geo.cut_and_fill_calc import calculate_earthwork_cut_fill
from cad2geo.dxf import DXFEntity, dxf_to_geojson, parse_dxf
from cad2geo.hatch_parser import STANDARD_HATCHES, parse_cad_hatches
from cad2geo.hydrological_culvert_sizing import (
    CatchmentRunoffProfile,
    calculate_culvert_hydraulic_capacity,
)
from cad2geo.ncz_engine.model import NetcadCoordinate, NetcadEntity
from cad2geo.ncz_engine.v2 import cache as ncz_cache
from cad2geo.qa_cleaner import clean_cad_entities
from cad2geo.reader import NetcadReader, is_ncz
from cad2geo.spline_densifier import densify_cad_splines
from cad2geo.topology import polygonize_cad_lines, split_features_by_cad_layer
from tests import ncz_fixtures as fx


def _dxf(*pairs: tuple[int, object]) -> str:
    """Build DXF text (inside an ENTITIES section) from group-code/value pairs."""
    body = [(0, "SECTION"), (2, "ENTITIES"), *pairs, (0, "ENDSEC"), (0, "EOF")]
    return "".join(f"{code}\n{value}\n" for code, value in body)


class TestDxfReader(unittest.TestCase):
    def test_lwpolyline_without_z_codes_keeps_its_vertices(self) -> None:
        # Regression: vertices were only emitted on group 30, which a real
        # LWPOLYLINE never writes, so every LWPOLYLINE came back empty.
        text = _dxf(
            (0, "LWPOLYLINE"),
            (8, "P"),
            (90, 4),
            (70, 1),
            (10, 0.0),
            (20, 0.0),
            (10, 5.0),
            (20, 0.0),
            (10, 5.0),
            (20, 5.0),
            (10, 0.0),
            (20, 5.0),
        )
        entity = parse_dxf(text)[0]
        self.assertEqual([(c.x, c.y) for c in entity.coordinates], [(0, 0), (5, 0), (5, 5), (0, 5)])
        geometry = dxf_to_geojson(text)["features"][0]["geometry"]
        self.assertEqual(geometry["type"], "Polygon")
        self.assertEqual(len(geometry["coordinates"][0]), 5)

    def test_2d_line_keeps_both_endpoints(self) -> None:
        # Regression: a LINE without 30/31 codes produced no coordinates.
        text = _dxf((0, "LINE"), (8, "L"), (10, 1), (20, 2), (11, 3), (21, 4))
        entity = parse_dxf(text)[0]
        self.assertEqual([(c.x, c.y) for c in entity.coordinates], [(1, 2), (3, 4)])

    def test_3d_line_keeps_elevations(self) -> None:
        text = _dxf((0, "LINE"), (10, 1), (20, 2), (30, 7), (11, 3), (21, 4), (31, 9))
        coords = parse_dxf(text)[0].coordinates
        self.assertEqual([(c.x, c.y, c.z) for c in coords], [(1, 2, 7), (3, 4, 9)])

    def test_line_z_without_end_point_does_not_crash(self) -> None:
        # Regression: a stray group 31 raised UnboundLocalError (end_x).
        text = _dxf((0, "LINE"), (10, 0), (20, 0), (30, 0), (31, 0))
        self.assertEqual(len(parse_dxf(text)[0].coordinates), 1)

    def test_old_style_polyline_collects_its_vertices(self) -> None:
        # Regression: each VERTEX became its own one-point entity and the
        # POLYLINE itself kept only its dummy (0, 0) header point.
        text = _dxf(
            (0, "POLYLINE"),
            (8, "P"),
            (66, 1),
            (10, 0),
            (20, 0),
            (30, 0),
            (70, 1),
            (0, "VERTEX"),
            (8, "OTHER"),
            (70, 0),
            (10, 1),
            (20, 1),
            (30, 2),
            (0, "VERTEX"),
            (10, 2),
            (20, 1),
            (30, 2),
            (0, "VERTEX"),
            (10, 2),
            (20, 2),
            (30, 2),
            (0, "SEQEND"),
            (0, "POINT"),
            (10, 9),
            (20, 9),
        )
        entities = parse_dxf(text)
        self.assertEqual([entity.kind for entity in entities], ["POLYLINE", "POINT"])
        polyline = entities[0]
        self.assertEqual(polyline.layer, "P")
        self.assertTrue(polyline.is_closed)
        self.assertEqual(
            [(c.x, c.y, c.z) for c in polyline.coordinates], [(1, 1, 2), (2, 1, 2), (2, 2, 2)]
        )

    def test_geojson_output_is_always_valid(self) -> None:
        # Regression: a CIRCLE (centre only) became a one-position
        # LineString and a two-vertex closed polyline a 3-position Polygon.
        circle = _dxf((0, "CIRCLE"), (10, 1), (20, 1), (30, 0), (40, 2))
        self.assertEqual(
            dxf_to_geojson(circle)["features"][0]["geometry"],
            {"type": "Point", "coordinates": [1.0, 1.0]},
        )
        sliver = DXFEntity(
            kind="LWPOLYLINE",
            layer="0",
            is_closed=True,
            coordinates=[NetcadCoordinate(0, 0), NetcadCoordinate(1, 0)],
        )
        self.assertEqual(sliver.to_geojson_feature()["geometry"]["type"], "LineString")
        self.assertIsNone(DXFEntity(kind="LINE", layer="0").to_geojson_feature()["geometry"])

    def test_to_netcad_entity_kinds(self) -> None:
        expected = {
            "LWPOLYLINE": "LINE",
            "3DFACE": "LINE",
            "CIRCLE": "LINE",
            "POINT": "POINT",
            "MTEXT": "POINT",
            "INSERT": "INSERT",
        }
        for kind, mapped in expected.items():
            with self.subTest(kind=kind):
                entity = DXFEntity(kind=kind, layer="L").to_netcad_entity(layer_code=3)
                self.assertEqual(entity.geometry_kind, mapped)
                self.assertEqual(entity.layer_code, 3)
        closed = DXFEntity(kind="POLYLINE", layer="L", is_closed=True).to_netcad_entity()
        self.assertEqual(closed.geometry_kind, "POLYGON")

    def test_text_without_entities_section_and_bad_values(self) -> None:
        text = "0\nPOINT\n8\nX\n62\nbad\n10\nnope\n20\n1\n0\nEOF\n"
        entity = parse_dxf(text)[0]
        self.assertEqual((entity.layer, entity.color_aci), ("X", 7))
        self.assertEqual([(c.x, c.y) for c in entity.coordinates], [(0.0, 1.0)])


class TestCsvSniffer(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "points.csv"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_quoted_csv_rows_are_parsed(self) -> None:
        # Regression: rows were split on the raw delimiter, so quoted values
        # ('"500000.5"') never parsed and no point was produced.
        self.path.write_text(
            '"id","x","y"\n"1","500000.5","4500000.25"\n"A, B","500001","4500001"\n',
            encoding="utf-8",
        )
        profile = sniff_csv_coordinates(str(self.path))
        self.assertEqual(profile.sample_points, [(500000.5, 4500000.25), (500001.0, 4500001.0)])
        features = csv_to_geojson(str(self.path))["features"]
        self.assertEqual(len(features), 2)
        self.assertEqual(features[1]["properties"]["id"], "A, B")

    def test_semicolon_file_with_decimal_commas(self) -> None:
        # Regression: ',' tied with ';' on column count and won, splitting
        # every decimal value in half; the first row was also taken as a header.
        self.path.write_text("1;4500000,5;500000,25\n2;4500001,5;500001,25\n", encoding="utf-8")
        profile = sniff_csv_coordinates(str(self.path))
        self.assertEqual(profile.delimiter, ";")
        self.assertEqual(profile.row_count, 2)
        self.assertEqual(profile.sample_points[0], (500000.25, 4500000.5))
        coords = [f["geometry"]["coordinates"] for f in csv_to_geojson(str(self.path))["features"]]
        self.assertEqual(coords[0], [500000.25, 4500000.5])

    def test_empty_file_with_explicit_profile(self) -> None:
        self.path.write_text("", encoding="utf-8")
        profile = sniff_csv_coordinates("id,x,y\n1,2,3\n")
        self.assertEqual(csv_to_geojson(str(self.path), profile)["features"], [])
        self.assertEqual(sniff_csv_coordinates(str(self.path)).fields, [])

    def test_space_delimited_with_z_column(self) -> None:
        self.path.write_text("x y z\n1 2 3\n4 5 bad\n", encoding="utf-8")
        features = csv_to_geojson(str(self.path))["features"]
        self.assertEqual([f["geometry"]["coordinates"] for f in features], [[1, 2, 3], [4, 5]])


class TestQaCleaner(unittest.TestCase):
    def test_engine_title_case_kinds_are_cleaned(self) -> None:
        # Regression: the NCZ engine emits "Line"/"Polyline"/"Polygon" but
        # the cleaner only matched upper case, so no NCZ line was ever
        # length-checked and open "Polygon" rings were never snapped.
        tiny = NetcadEntity(
            "Line", 0, coordinates=[NetcadCoordinate(0, 0), NetcadCoordinate(0.001, 0)]
        )
        ring = NetcadEntity(
            "Polygon",
            0,
            coordinates=[
                NetcadCoordinate(0, 0),
                NetcadCoordinate(10, 0),
                NetcadCoordinate(10, 10),
                NetcadCoordinate(0, 10),
                NetcadCoordinate(0, 0.02),
            ],
        )
        lone = NetcadEntity("Polyline", 0, coordinates=[NetcadCoordinate(1, 1)])
        cleaned, report = clean_cad_entities([tiny, ring, lone])
        self.assertEqual(report.degenerate_lines_dropped, 2)
        self.assertEqual(report.endpoints_snapped, 1)
        self.assertEqual(len(cleaned), 1)
        self.assertTrue(cleaned[0].is_closed)

    def test_slivers_and_empty_entities(self) -> None:
        sliver = NetcadEntity(
            "POLYGON",
            0,
            coordinates=[NetcadCoordinate(0, 0), NetcadCoordinate(1, 0), NetcadCoordinate(0, 0.01)],
        )
        cleaned, report = clean_cad_entities([sliver, NetcadEntity("POINT", 0)])
        self.assertEqual(cleaned, [])
        self.assertEqual(report.slivers_filtered, 1)
        self.assertEqual(report.to_dict()["total_input_entities"], 2)


class TestTopology(unittest.TestCase):
    def test_degenerate_closed_lines_are_not_rings(self) -> None:
        # Regression: A-B-A and A-A "closed" lines were returned as polygon
        # rings with fewer than the four positions a ring requires.
        self.assertEqual(polygonize_cad_lines([[(0, 0), (1, 0), (0, 0)]]), [])
        self.assertEqual(polygonize_cad_lines([[(0, 0), (0, 0.001)]]), [])

    def test_null_properties_are_allowed(self) -> None:
        # Regression: GeoJSON "properties": null raised AttributeError.
        feature = {"type": "Feature", "properties": None, "geometry": None}
        self.assertEqual(split_features_by_cad_layer([feature]), {"0": [feature]})


class TestEngineeringHelpers(unittest.TestCase):
    def test_culvert_beyond_largest_box_is_flagged_inadequate(self) -> None:
        # Regression: when no barrel was large enough the result claimed a
        # fixed 50 m3/s capacity and is_flow_capacity_adequate=True.
        for profile in (
            CatchmentRunoffProfile(catchment_area_ha=5000.0),
            CatchmentRunoffProfile(culvert_slope_pct=0.0),
        ):
            with self.subTest(profile=profile):
                result = calculate_culvert_hydraulic_capacity(profile)
                self.assertFalse(result.is_flow_capacity_adequate)
                self.assertLess(result.actual_capacity_q_m3s, result.peak_discharge_q_m3s)
                self.assertEqual(result.recommended_internal_dimensions_m, (6.0, 3.5))

    def test_culvert_box_branch(self) -> None:
        result = calculate_culvert_hydraulic_capacity(
            CatchmentRunoffProfile(catchment_area_ha=400.0), allowable_headwater_depth_m=5.0
        )
        self.assertEqual(result.recommended_culvert_type, "BOX_RECTANGULAR")
        self.assertGreaterEqual(result.actual_capacity_q_m3s, result.peak_discharge_q_m3s)
        self.assertTrue(result.is_flow_capacity_adequate)
        self.assertEqual(result.to_dict()["culvert_type"], "BOX_RECTANGULAR")

    def test_cut_fill_falls_back_to_pairwise_matching(self) -> None:
        existing = [(0.0, 0.0, 10.0), (5.0, 0.0, 10.0)]
        design = [(1000.0, 0.0, 12.0), (1005.0, 0.0, 9.0)]
        report = calculate_earthwork_cut_fill(existing, design, cell_size_m=5.0)
        self.assertAlmostEqual(report.total_fill_volume_m3, 2.0 * 25.0 * 1.15)
        self.assertAlmostEqual(report.total_cut_volume_m3, 25.0)
        self.assertEqual(len(report.cells), 2)
        self.assertAlmostEqual(report.cut_fill_ratio, 25.0 / 57.5)

    def test_hatch_lookup_returns_independent_copies(self) -> None:
        # Regression: the shared STANDARD_HATCHES instance was returned, so
        # mutating one result changed every later lookup.
        pattern = parse_cad_hatches("unknown layer")
        pattern.scale = 3.0
        pattern.lines.append(mock.sentinel.line)
        self.assertEqual(STANDARD_HATCHES["ANSI31"].scale, 1.0)
        self.assertEqual(STANDARD_HATCHES["ANSI31"].lines, [])
        self.assertEqual(parse_cad_hatches("x").scale, 1.0)
        self.assertEqual(parse_cad_hatches("site_brick").pattern_name, "BRICK")
        self.assertIn("<rect", parse_cad_hatches("SOLID fill").to_svg_pattern("p1"))
        self.assertIn(
            'patternTransform="rotate(45.0)"', parse_cad_hatches("x").to_svg_pattern("p2")
        )

    def test_spline_zero_length_segment_without_samples(self) -> None:
        # Regression: two coincident points with samples_per_segment=0
        # raised ZeroDivisionError.
        result = densify_cad_splines([(1.0, 1.0), (1.0, 1.0)], samples_per_segment=0)
        self.assertEqual(result.coordinates, [(1.0, 1.0), (1.0, 1.0)])
        self.assertEqual(result.total_curve_length_m, 0.0)

    def test_spline_feature_does_not_mutate_caller_properties(self) -> None:
        props = {"name": "a"}
        feature = densify_cad_splines([(0, 0), (3, 4)]).to_geojson_feature(props)
        self.assertEqual(props, {"name": "a"})
        self.assertEqual(feature["properties"]["length_m"], 5.0)

    def test_spline_short_inputs_and_catmull_rom(self) -> None:
        self.assertEqual(densify_cad_splines([(0, 0)]).densified_points_count, 1)
        result = densify_cad_splines([(0, 0), (10, 0), (10, 10)], samples_per_segment=4)
        self.assertEqual(result.coordinates[0], (0, 0))
        self.assertEqual(result.coordinates[-1], (10, 10))
        self.assertGreater(result.total_curve_length_m, 19.0)


class TestReaderAndCli(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.ncz = self.tmp / "drawing.ncz"
        self.ncz.write_bytes(fx.full_drawing())
        self._cache = mock.patch.object(ncz_cache, "_cache_root", return_value=self.tmp / "cache")
        self._cache.start()
        self._env = mock.patch.dict(os.environ)
        self._env.start()
        os.environ.pop("CAD2GEO_NCZ_CACHE_DISABLE", None)

    def tearDown(self) -> None:
        self._env.stop()
        self._cache.stop()
        self._tmp.cleanup()

    def _run(self, argv: list[str]) -> tuple[int, str]:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = cli_main(argv)
        return code, buffer.getvalue()

    def test_is_ncz(self) -> None:
        self.assertTrue(is_ncz(self.ncz))
        self.assertFalse(is_ncz(self.tmp / "missing.ncz"))
        self.assertFalse(is_ncz(self.tmp))

    def test_index_served_from_cache_then_decodes_lazily(self) -> None:
        first = NetcadReader(self.ncz).index()
        self.assertFalse(first.from_cache)
        again = NetcadReader(self.ncz)
        self.assertEqual(again.version_name, "NCZ-TEST-1.0")  # lazy index via cache
        self.assertTrue(again.from_cache)
        self.assertEqual(again.epsg, "EPSG:5254")
        self.assertTrue(again.attribute_tables())
        self.assertEqual(again.decode_layers([]), [])
        self.assertTrue(again.decode_layers([1]))
        with self.assertRaises(FileNotFoundError):
            NetcadReader(self.tmp / "missing.ncz").index()

    def test_cli_inspect_text_and_json(self) -> None:
        code, out = self._run(["inspect", str(self.ncz)])
        self.assertEqual(code, 0)
        self.assertIn("Version: NCZ-TEST-1.0", out)
        self.assertIn("CRS: EPSG:5254", out)
        self.assertIn("Layers:", out)
        code, out = self._run(["inspect", str(self.ncz), "--json"])
        self.assertEqual(json.loads(out)["epsg"], "EPSG:5254")

    def test_cli_inspect_empty_drawing(self) -> None:
        empty = self.tmp / "empty.ncz"
        empty.write_bytes(b"")
        code, out = self._run(["inspect", str(empty)])
        self.assertEqual(code, 0)
        self.assertIn("No supported geometry layers found.", out)

    def test_cli_output_to_a_narrow_encoding_does_not_crash(self) -> None:
        # Regression: redirected stdout on Windows uses the ANSI code page; a
        # layer name decoded to U+0081 (CP857 "u-umlaut") raised
        # UnicodeEncodeError instead of printing the layer list.
        odd = self.tmp / "odd.ncz"
        odd.write_bytes(fx.layer_table_block([b"R\x81AD"]) + fx.point_block(layer=0))
        src = str(Path(cad2geo.__file__).resolve().parents[1])
        env = dict(
            os.environ,
            CAD2GEO_NCZ_CACHE_DISABLE="1",
            PYTHONIOENCODING="cp1254",
            PYTHONPATH=os.pathsep.join([src, os.environ.get("PYTHONPATH", "")]),
        )
        script = "import sys; from cad2geo.cli import main; sys.exit(main(sys.argv[1:]))"
        done = subprocess.run(
            [sys.executable, "-c", script, "inspect", str(odd)],
            env=env,
            capture_output=True,
            timeout=120,
        )
        self.assertEqual(done.returncode, 0, done.stderr.decode("cp1254", "replace"))
        self.assertIn(b"R?AD", done.stdout)

    def test_cli_convert_selected_layers(self) -> None:
        output = self.tmp / "out" / "layers.geojson"
        code, out = self._run(["convert", str(self.ncz), str(output), "--layers", "1, 3"])
        self.assertEqual(code, 0)
        collection = json.loads(output.read_text(encoding="utf-8"))
        self.assertTrue(collection["features"])
        self.assertIn(f"{len(collection['features'])} feature(s)", out)


if __name__ == "__main__":
    unittest.main()
