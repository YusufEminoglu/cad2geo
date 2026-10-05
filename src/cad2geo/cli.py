"""Command-line interface for cad2geo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .geojson import write_geojson
from .reader import NetcadReader, parse_netcad


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cad2geo",
        description="Inspect and convert CAD/Netcad drawing data for geospatial workflows.",
    )
    parser.add_argument("--version", action="version", version=f"cad2geo {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="List NCZ/NCA layers and metadata.")
    inspect_parser.add_argument("source", type=Path)
    inspect_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    convert_parser = subparsers.add_parser("convert", help="Convert an NCZ/NCA file to GeoJSON.")
    convert_parser.add_argument("source", type=Path)
    convert_parser.add_argument("output", type=Path)
    convert_parser.add_argument(
        "--layers",
        help="Comma-separated layer codes to decode; defaults to all layers.",
    )

    dxf_parser = subparsers.add_parser("dxf", help="Convert an AutoCAD DXF file to GeoJSON.")
    dxf_parser.add_argument("source", type=Path)
    dxf_parser.add_argument("output", type=Path)

    clean_parser = subparsers.add_parser("clean", help="Perform geometric QA repair on CAD drawing and output clean GeoJSON.")
    clean_parser.add_argument("source", type=Path)
    clean_parser.add_argument("output", type=Path)
    clean_parser.add_argument("--snap-tolerance", type=float, default=0.05, help="Snap tolerance in map units.")
    clean_parser.add_argument("--min-area", type=float, default=0.1, help="Minimum polygon area to retain.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "inspect":
        return _inspect(args)
    if args.command == "convert":
        return _convert(args)
    if args.command == "dxf":
        return _dxf(args)
    if args.command == "clean":
        return _clean(args)
    parser.error(f"Unknown command: {args.command}")
    return 2


def _inspect(args: argparse.Namespace) -> int:
    reader = NetcadReader(args.source).index()
    summaries = reader.layer_summaries()
    if args.json:
        print(
            json.dumps(
                {
                    "source": str(args.source),
                    "backend": reader.backend,
                    "from_cache": reader.from_cache,
                    "version_name": reader.version_name,
                    "epsg": reader.epsg,
                    "projection_text": reader.projection_text,
                    "layers": [summary.to_dict() for summary in summaries],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    print(f"Source: {args.source}")
    print(f"Backend: {reader.backend}")
    if reader.version_name:
        print(f"Version: {reader.version_name}")
    if reader.epsg:
        print(f"CRS: {reader.epsg}")
    if not summaries:
        print("No supported geometry layers found.")
        return 0
    print("Layers:")
    for summary in summaries:
        families = ", ".join(sorted(summary.families)) or "-"
        print(
            f"  {summary.layer_code:>3}  {summary.layer_name or '(unnamed)'}  "
            f"{summary.record_count} record(s)  [{families}]"
        )
    return 0


def _convert(args: argparse.Namespace) -> int:
    if args.layers:
        layer_codes = [int(part.strip()) for part in args.layers.split(",") if part.strip()]
        reader = NetcadReader(args.source).index()
        entities = reader.decode_layers(layer_codes)
    else:
        entities = parse_netcad(args.source).entities
    collection = write_geojson(entities, args.output)
    print(f"Wrote {len(collection['features'])} feature(s) to {args.output}")
    return 0


def _dxf(args: argparse.Namespace) -> int:
    from .dxf import dxf_to_geojson

    collection = dxf_to_geojson(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(collection, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Parsed DXF: Wrote {len(collection['features'])} feature(s) to {args.output}")
    return 0


def _clean(args: argparse.Namespace) -> int:
    from .qa_cleaner import clean_cad_entities

    raw_entities = parse_netcad(args.source).entities
    cleaned, report = clean_cad_entities(
        raw_entities,
        snap_tolerance=args.snap_tolerance,
        min_polygon_area=args.min_area,
    )
    write_geojson(cleaned, args.output)
    print(f"Cleaned CAD: {report.total_input_entities} -> {report.total_output_entities} entities")
    print(f"  - Endpoints snapped: {report.endpoints_snapped}")
    print(f"  - Duplicate vertices removed: {report.duplicate_vertices_removed}")
    print(f"  - Slivers filtered: {report.slivers_filtered}")
    print(f"Wrote cleaned GeoJSON to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
