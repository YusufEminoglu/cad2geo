# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-08-26
### Added (Full 02CadGis Core Tool Suite)
- **Smart Turkish & Global CRS Detector (`detect_crs`)**:
  - Automatic detection of Turkish survey datums: TUREF / TM, ED50 / TM (3° Gauss-Krüger, 6° UTM).
  - Easting magnitude analysis for false-easting vs zone-prefixed coordinates.
- **Smart Coordinate & Survey CSV Sniffer (`sniff_csv_coordinates`, `csv_to_geojson`)**:
  - Auto-detection of delimiters (`,`, `;`, `\t`, `|`, whitespace), headers, and Easting/Northing coordinate columns.
  - Direct conversion of delimited survey files into GeoJSON FeatureCollections.
- **MPYY & e-Plan Zoning Layer Classifier (`classify_cad_layer`)**:
  - Official Turkish Spatial Planning Code (MPYY) land-use categorization and hex styling.
- **CAD to GIS Topology & Conversion Engine (`polygonize_cad_lines`, `split_features_by_cad_layer`)**:
  - Automatic line-to-polygon loop closure and layer splitting.

## [0.1.0] - 2026-08-25
### Added
- Initial `cad2geo` SDK package.
- Pure-Python Netcad NCZ/NCA parser and lazy layer catalog.
- Stable public dataclasses for Netcad entities and parse results.
- GeoJSON export helpers.
- `cad2geo inspect` and `cad2geo convert` CLI commands.
