# Changelog

All notable changes to this project will be documented in this file.

## [0.9.0] - 2026-08-30
### Added
- **Euler Clothoid Spiral Transition Curve Engine (`spiral_curve_transition.py`)**: Added `calculate_clothoid_spiral_curve` using Fresnel integrals for smooth highway/railway transition curves.
- **Highway Drainage Catchment Peak Runoff & Culvert Sizing (`hydrological_culvert_sizing.py`)**: Added `calculate_culvert_hydraulic_capacity` computing Rational Method discharges and Manning pipe/box culvert dimensions.

## [0.8.0] - 2026-08-30
### Added
- **Intersection Sight Distance Triangle Analyzer (`sight_distance_triangle.py`)**: Added `evaluate_intersection_sight_triangles` computing AASHTO Case B stopping and departure sight triangles.
- **Road Corridor Cross-Section Profiles (Enkesit) (`cross_section_generator.py`)**: Added `generate_road_cross_sections` computing daylight batter slopes and exporting multi-station DXF sheets.

## [0.7.0] - 2026-08-30
### Added
- **Earthwork Cut & Fill Volumetric Balancer (`cut_and_fill_calc.py`)**: Added `calculate_earthwork_cut_fill` computing prismoidal grid volumes and net excavation/fill balance.
- **CAD Spline & Bézier Adaptive Densifier (`spline_densifier.py`)**: Added `densify_cad_splines` generating curvature-continuous polylines from control points.

## [0.6.0] - 2026-08-30
### Added
- **Delaunay TIN Surface & Contour Isoline Generator (`contour_interpolator.py`)**: Added `generate_tin_contours` extracting continuous elevation isolines and index contours from 3D spot height points.
- **CAD DIMENSION Entity Parser & Geometric Distance QA (`dimension_parser.py`)**: Added `extract_cad_dimensions` cross-validating annotated dimension text against computed geometric segment lengths.

## [0.5.0] - 2026-08-30
### Added
- **CAD Text & Spatial Annotation Linker (`annotation_matcher.py`)**: Added `link_annotations_to_polygons` matching floating CAD text/MText labels with enclosing/nearest parcel polygons.
- **DWG/DXF Block & Dynamic Attribute Extractor (`block_extractor.py`)**: Added `extract_cad_blocks` converting INSERT block references and ATTRIB tags to georeferenced GeoJSON point features.

## [0.4.0] - 2026-08-30
### Added
- **Geometric Buffers & Spatial Index (`spatial_ops.py`)**: Added `buffer_point`, `buffer_polyline`, `point_in_polygon` (ray casting) and fast grid-based `CADSpatialIndex`.
- **Vector Exporters & GeoParquet Schema (`vector_export.py`)**: Added `export_to_esri_shapefile_asc`, `export_geoparquet_metadata`, and `export_flat_geobuf_schema`.
- **Hatch Pattern & Texture Parser (`hatch_parser.py`)**: Decodes standard CAD hatch styles into SVG fill pattern definitions (`parse_cad_hatches`).
- **Multi-Scale CAD Tile Pyramid (`tile_slicer.py`)**: Slices drawings into quadtree tile bounds (`slice_cad_to_tile_pyramid`).

## [0.3.0] - 2026-08-30
### Added
- **Pure-Python DXF Reader & Converter (`dxf.py`)**:
  - Full support for AutoCAD ASCII DXF (R12-R2018) entity extraction (LINE, POLYLINE, LWPOLYLINE, 3DFACE, CIRCLE, ARC, POINT, TEXT, MTEXT).
  - ACI color palette mapping to hex and direct GeoJSON conversion (`parse_dxf`, `dxf_to_geojson`).
- **CAD QA & Geometry Repair Engine (`qa_cleaner.py`)**:
  - Endpoint snapping (`snap_endpoints`), consecutive duplicate vertex removal (`remove_duplicate_vertices`), degenerate line removal, and micro-sliver polygon filtering.
  - Generates comprehensive `QARepairReport` metrics.
- **CLI Subcommands**:
  - Added `cad2geo dxf <source.dxf> <out.geojson>` and `cad2geo clean <source.ncz> <out.geojson>`.

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
