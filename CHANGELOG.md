# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
### Changed
- Completed type hints and docstrings across the NCZ Engine v2 (binary cursor, geometry decoders, block metadata, attribute tables, cache) and the civil-engineering result objects.
- Applied `ruff format` to `src/` and `tests/`, and re-verified `ruff check`.
- Rewrote README quickstart/CLI examples so every snippet matches the real public API, and documented the full public API and engineering engines.

### Added
- Edge-case tests for `polygonize_cad_lines` (reverse chaining, pre-closed rings, degenerate input) and `split_features_by_cad_layer` (layer fallbacks).

### Fixed
- NCZ Engine v2 decoders no longer leak `NaN`/`inf` from corrupt or unexpected field values
  into decoded entities. A non-finite box rotation used to turn every ring corner into `NaN`
  (written as invalid JSON by the GeoJSON exporters), and smart-object sizes, circle/arc
  radii and angles, and text/symbol/block rotations could carry `NaN`/`Infinity`. Such
  scalars now fall back to `0`, smart objects use their corner-point size, and polyline
  vertices with non-finite coordinates are skipped.
- NCZ Engine v2: an `@TAB` not followed by digits (for example the text `@TABLE`) is no longer
  taken as an attribute-table marker; it used to create a bogus table and truncate the
  preceding real record.
- NCZ Engine v2: a geometry record nested in a container block is now indexed when it ends
  exactly at the container's last byte (an off-by-one bound skipped it).
- NCZ Engine v2: an unterminated `SRS:"EPSG:..."` value in a `TILED_XML` block is read only to
  the end of its block and stops at NUL padding, instead of running on through the rest of the
  file and returning padding and the next blocks' bytes as the EPSG code.
- NCZ Engine v2: open polylines no longer report rectangle `box_width`/`box_height`/rotation
  when their cyclic vertex list happens to reduce to four corners; only closed rings do.
- NCZ index cache: a cache file holding well-formed JSON of the wrong shape (non-object
  document, non-object metadata, non-object summaries or tables) is now a cache miss instead
  of an `AttributeError` or a crash later in the reader, and a failed save no longer leaves an
  orphaned `*.json.tmp` file behind.
- `cad2geo inspect`/`convert`/`clean`: output redirected to a file on Windows (ANSI code page)
  no longer aborts with `UnicodeEncodeError` on characters the encoding cannot represent;
  they are replaced instead.
- DXF reader: vertices are emitted on their group-20 value (group 30 only refines z), so
  `LWPOLYLINE` entities and 2D `LINE`/`POINT` entities keep their coordinates (they used to
  come back empty); a stray group 31 no longer raises `UnboundLocalError`; old-style
  `POLYLINE`/`VERTEX`/`SEQEND` sequences are collected into one polyline instead of one
  bogus entity per vertex plus a dummy `(0, 0)` point.
- DXF GeoJSON export always emits valid geometry: single-vertex entities (e.g. `CIRCLE`
  centres) become a `Point` instead of a one-position `LineString`, and a closed polyline
  with fewer than three vertices becomes a `LineString` instead of an invalid `Polygon` ring.
- CSV sniffer: rows are split with CSV quoting rules, so quoted files (`"1","500000.5",...`)
  yield points (they produced none); `;`-delimited files with decimal commas are detected
  as `;` (a tie with `,` used to win) and their first data row is no longer taken as a
  header; `csv_to_geojson` no longer fails on an empty file with an explicit profile.
- `clean_cad_entities` matches geometry kinds case-insensitively, so NCZ engine entities
  (`"Line"`, `"Polyline"`, `"Polygon"`) are length-checked and snapped like DXF ones.
- `polygonize_cad_lines` no longer returns degenerate "closed" inputs with fewer than four
  positions (`A-B-A`, `A-A`) as polygon rings; `split_features_by_cad_layer` accepts GeoJSON
  features with `"properties": null`.
- `calculate_culvert_hydraulic_capacity`: when no standard barrel carries the peak flow the
  result now reports the largest box's real capacity and `is_flow_capacity_adequate=False`
  (it claimed a fixed 50 m3/s and `True`).
- `parse_cad_hatches` returns a copy, so changing the returned pattern no longer corrupts the
  shared `STANDARD_HATCHES` table.
- `densify_cad_splines` no longer divides by zero for two coincident points with
  `samples_per_segment=0`, and `to_geojson_feature` no longer mutates the caller's
  `properties` dict.

## [0.12.0] - 2026-08-30
### Added
- **Geotechnical Embankment Bishop Circular Slope Stability Engine (`embankment_slope_bishop_stability.py`)**: Added `evaluate_bishop_slope_stability` solving Bishop's simplified method of slices and pore water ratio $r_u$.
- **Calculation of Road Traffic Noise (CRTN) Acoustic Propagation Engine (`traffic_noise_propagation_crn.py`)**: Added `calculate_crtn_noise_propagation` calculating $L_{10,18h}$ and $L_{den}$ façade noise attenuation.

## [0.11.0] - 2026-08-30
### Added
- **AASHTO Flexible Pavement Structural Number (SN) Designer (`pavement_structural_number_sn.py`)**: Added `calculate_flexible_pavement_structural_number` solving AASHTO 1993 equations for ESAL loads and subgrade $M_r$.
- **Highway Curb Gutter Flow & Grate Hydraulics (HEC-22) (`stormwater_curb_inlet_hydraulics.py`)**: Added `calculate_curb_inlet_hydraulic_capacity` computing modified Manning triangular spread and interception efficiency.

## [0.10.0] - 2026-08-30
### Added
- **Highway Superelevation (Deve Kurpu) & Transition Runoff Designer (`superelevation_runoff_designer.py`)**: Added `calculate_superelevation_runoff` computing AASHTO $e_{max}$, tangent runoff ($L_t$), and cross-section edge profiles.
- **Roadside Retaining Wall Lateral Earth Pressure & Stability Engine (`retaining_wall_earth_pressure.py`)**: Added `evaluate_retaining_wall_stability` computing Rankine active thrust, overturning moments, and sliding factors of safety.

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
