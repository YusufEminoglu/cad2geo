<div align="center">

<a href="https://geophilo.com/">
  <img src="https://geophilo.com/assets/sdk_icons/cad2geo_sdk.svg" width="140" height="140" alt="cad2geo logo" />
</a>

# cad2geo


[![PyPI version](https://img.shields.io/pypi/v/cad2geo.svg?color=f59e0b)](https://pypi.org/project/cad2geo/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23677239.svg)](https://doi.org/10.5281/zenodo.23677239)
[![Python version support](https://img.shields.io/pypi/pyversions/cad2geo.svg?color=3b82f6)](https://pypi.org/project/cad2geo/)
[![Documentation](https://img.shields.io/badge/docs-GEOPHILO-10b981.svg)](https://geophilo.com/cad2geo/)
[![License: GPL-2.0-or-later](https://img.shields.io/badge/License-GPL--2.0--or--later-blue.svg)](https://github.com/YusufEminoglu/cad2geo/blob/main/LICENSE)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-D7FF64.svg)](https://docs.astral.sh/ruff/)
[![Test Coverage](https://img.shields.io/badge/coverage-91%25-brightgreen.svg)](#-development--testing)

**Convert Netcad NCZ/NCA and DXF CAD drawings to GeoJSON in pure Python — no GDAL, no QGIS — plus civil-engineering calculators.**

[📖 **Open Interactive Web Manual**](https://geophilo.com/cad2geo/) • [📦 **PyPI Package**](https://pypi.org/project/cad2geo/) • [🐙 **GitHub**](https://github.com/YusufEminoglu/cad2geo) • [🐛 **Issue Tracker**](https://github.com/YusufEminoglu/cad2geo/issues)

</div>

---

## 📦 Installation

```bash
pip install cad2geo
```

**Requirements:** Python 3.9+ and the standard library only. No runtime third-party dependencies. Optional development tooling (tests, linting, build): `pip install -e ".[dev]"`.

## ⚡ Quickstart

```python
from cad2geo import inspect_source, parse_netcad, write_geojson

# 1. List the layers in a Netcad drawing (fast header scan)
for layer in inspect_source("plan.ncz"):
    print(layer.layer_code, layer.layer_name, layer.record_count)

# 2. Decode everything and write GeoJSON
result = parse_netcad("plan.ncz")
collection = write_geojson(result.entities, "plan.geojson")
print(len(collection["features"]), "features ->", "plan.geojson")

# 0 ROADS 2
# 1 PARCELS 5
# ...
# 15 features -> plan.geojson
```

Same from the shell: `cad2geo convert plan.ncz plan.geojson`. AutoCAD drawings: `dxf_to_geojson("survey.dxf")`.

## 🇹🇷 Türkçe Özet

**cad2geo**, Netcad `.ncz` / `.nca` çizimlerini ve AutoCAD `.dxf` dosyalarını saf Python ile GeoJSON'a dönüştürür. Netcad, QGIS ya da GDAL kurulumu gerekmez; yalnızca Python yeterlidir.
Katman listesini hızla okuyabilir, yalnızca ihtiyaç duyduğunuz katmanları çözebilir ve şev stabilitesi, üstyapı, menfez gibi inşaat mühendisliği hesaplarını da aynı paketle yapabilirsiniz.

```bash
pip install cad2geo
```

Ayrıntılı kullanım kılavuzu: [geophilo.com/cad2geo](https://geophilo.com/cad2geo/)

---

## 🌟 Overview

**cad2geo** is a lightweight, zero-dependency Python library for inspecting Netcad `NCZ` (compressed archive) and `NCA` (raw binary CAD drawing stream) files and converting CAD geometries into OGC-compliant **GeoJSON** datasets.

Extracted from the high-value headless core of the **02CadGis** and **PlanX** geospatial ecosystem, **cad2geo** operates 100% headless using only Python's standard library (`struct`, `zlib`, `dataclasses`, `json`). It requires **zero proprietary CAD installations, zero QGIS runtimes, and zero GDAL C-extensions**.

Beyond raw conversion, the library ships a growing suite of turnkey **civil-engineering, cadastral and cartographic** engines (Bishop slope stability, CRTN road-noise, AASHTO pavement design, superelevation, culvert hydrology, retaining walls, sight-distance triangles, earthwork cut/fill, TIN contours, quadtree tiles and more), all callable with plain Python tuples.

---

## 🔬 Key Capabilities

1. **Pure-Python NCZ/NCA Binary Block Scanner:**
   - Directly decompresses zlib archive containers and parses binary stream records for Points, Lines, Polylines, Arcs, Circles, Text annotations, and Polygons.
2. **O(1) Fast Layer Catalog Inspection:**
   - Scans file headers in **under 5 milliseconds**, extracting layer codes, layer names, line types, display colors, and record counts without decompressing coordinates.
3. **Selective Layer Decoding & Memory Optimization:**
   - Skips unneeded byte blocks in the binary stream when decoding specific layers (e.g. `layer_codes=[1, 3, 7]`), saving up to **90% RAM** on massive municipal zoning plans (100MB+ NCZ files).
4. **Fingerprinted On-disk Index Cache:**
   - Reopening an unchanged drawing shows its layer tree instantly via a `(size, mtime_ns)`-keyed JSON cache; disable it with `CAD2GEO_NCZ_CACHE_DISABLE=1`.
5. **Mathematical Curve & Arc Discretization:**
   - Converts circular arcs and curves into piecewise linear GIS LineStrings using exact sagitta chord tolerance (δ) calculations.
6. **Cadastral & Zoning Attribute Preservation:**
   - Captures parcel IDs (*Ada / Parsel*), zoning parameters (*KAKS, TAKS, Yençok*), layer styles, text labels, and geometric perimeters.
7. **Standard GeoJSON FeatureCollection Serialization:**
   - Generates clean, standards-compliant GeoJSON with CRS headers and styling properties for immediate GIS web mapping.
8. **Civil-Engineering & Cartography Engines:**
   - Bishop slope stability, CRTN traffic noise, AASHTO `SN`, HEC-22 curb inlets, culvert sizing, superelevation runoff, retaining-wall earth pressure, road cross-sections, clothoid spirals, TIN contours, block extraction, dimension parsing, tile pyramids and QA repair — all pure Python.

---

## 🧰 Compatibility & Troubleshooting

### Compatibility matrix

| Component | Supported |
| :--- | :--- |
| Python | 3.9, 3.10, 3.11, 3.12, 3.13 |
| Operating systems | Windows, macOS, Linux (pure Python, no compiled extensions) |
| Input formats | Netcad `.ncz` / `.nca`, AutoCAD `.dxf`, delimited text via `csv_to_geojson` |
| Output formats | GeoJSON (files, strings, streams), ESRI ASCII GEN text, and GeoParquet / FlatGeobuf *metadata* dictionaries. For binary Shapefile, GeoPackage, FlatGeobuf, GeoParquet, DXF and KML output use the sister package [NCZ2Geo](https://pypi.org/project/NCZ2Geo/). |
| Runtime dependencies | None (the `[dev]` extra adds pytest, coverage, ruff, mypy, build and twine) |
| Typing | Fully annotated public API with a bundled `py.typed` marker |

### Troubleshooting

| Symptom | Likely cause and fix |
| :--- | :--- |
| `FileNotFoundError` from `NetcadReader` / `parse_netcad` | The path is relative to the current working directory. Resolve it with `Path(...).resolve()` before calling the API. |
| Layer list looks stale after replacing a file | Delete the sidecar JSON cache next to the drawing, or set `CAD2GEO_NCZ_CACHE_DISABLE=1` for the session. |
| `UnicodeEncodeError` in a Windows terminal | The CLI prints Turkish characters and emoji. Run `set PYTHONUTF8=1` (PowerShell: `$env:PYTHONUTF8=1`) or use Windows Terminal. |
| High memory use on 100 MB+ plans | Call `inspect_source()` first and decode only the required layers with `reader.decode_layers([...])`. |
| CRS confidence is low | Pass both `proj_text=` and representative `coords=` to `detect_crs()`; inspect `DetectedCRS.authid` before exporting. |
| DXF entities are missing | Only model-space `POINT`, `LINE`, `LWPOLYLINE`, `POLYLINE`, `ARC`, `CIRCLE`, `TEXT`/`MTEXT` and `INSERT` are converted; explode unsupported proxy objects in CAD first. |

---

## 🚀 Python API Examples

### 1. Fast Layer Catalog Inspection

Inspect drawing layers and entity counts in milliseconds without loading full geometry:

```python
from cad2geo import inspect_source

layers = inspect_source("imar_plani.ncz")

for layer in layers:
    families = ", ".join(sorted(layer.families)) or "-"
    print(f"Layer #{layer.layer_code:02d}: {layer.layer_name:<25} | "
          f"Entities: {layer.record_count} | [{families}]")
```

### 2. Selective Decoding & GeoJSON Export

Use `NetcadReader` to index once, then decode only the layers you need:

```python
from cad2geo import NetcadReader, write_geojson

reader = NetcadReader("imar_plani.ncz").index()
print(f"Backend: {reader.backend} | Version: {reader.version_name} | CRS: {reader.epsg}")

# Decode only layers 1, 3 and 7
entities = reader.decode_layers([1, 3, 7])

# Export to an OGC GeoJSON FeatureCollection
collection = write_geojson(entities, "zoning_boundaries.geojson")
print(f"Wrote {len(collection['features'])} feature(s).")
```

### 3. Full Parse & Custom Processing

`parse_netcad` decodes the whole drawing into stable dataclasses suitable for pipelines:

```python
from cad2geo import parse_netcad, entities_to_feature_collection

result = parse_netcad("parcels.ncz")
print(f"Parsed {len(result.entities)} entities "
      f"across {len(result.layer_names)} layers using {result.parser_backend}.")

geojson_dict = entities_to_feature_collection(result.entities)
print(f"Features in GeoJSON: {len(geojson_dict['features'])}")
```

### 4. DXF Conversion

```python
from cad2geo import dxf_to_geojson

collection = dxf_to_geojson("survey.dxf")
print(f"Converted {len(collection['features'])} DXF feature(s).")
```

### 5. Smart CRS Detection

```python
from cad2geo import detect_crs

crs = detect_crs(proj_text="ED50 / 3 DOM 33", coords=[(11556000.0, 4280000.0)])
print(crs.authid, "->", crs.description, f"({crs.confidence:.0%})")
# EPSG:2208 -> ED50 / 3-degree Gauss-Kruger zone 11 (95%)
```

### 6. Civil-Engineering Calculators

All engineering engines accept plain tuples/dataclasses and return rich result objects with a `.to_dict()` serialiser:

```python
from cad2geo import (
    SlopeSliceProfile,
    calculate_flexible_pavement_structural_number,
    evaluate_bishop_slope_stability,
)

# Bishop simplified method of slices
stability = evaluate_bishop_slope_stability(
    SlopeSliceProfile(
        cohesion_c_kpa=15.0,
        friction_angle_phi_deg=25.0,
        soil_unit_weight_gamma_kn_m3=19.0,
        embankment_height_h_m=10.0,
        slope_angle_beta_deg=30.0,
    )
)
print(f"Bishop FoS: {stability.factor_of_safety_bishop:.2f}")

# AASHTO 1993 flexible pavement structural number
sn = calculate_flexible_pavement_structural_number(
    design_traffic_esal_millions=10.0, subgrade_resilient_modulus_psi=6500.0
)
print(sn.to_dict())
```

### 7. Geometric QA Repair

```python
from cad2geo import clean_cad_entities, parse_netcad, write_geojson

entities = parse_netcad("dirty_plan.ncz").entities
cleaned, report = clean_cad_entities(entities, snap_tolerance=0.05, min_polygon_area=0.1)
write_geojson(cleaned, "clean_plan.geojson")

print(f"{report.endpoints_snapped} endpoints snapped, "
      f"{report.slivers_filtered} slivers removed.")
```

---

## 💻 Command Line Interface (CLI)

`cad2geo` ships a high-performance CLI with `inspect`, `convert`, `dxf` and `clean` subcommands:

```bash
# 1. Quick inspection of NCZ layer definitions
cad2geo inspect imar_plani.ncz

# 2. Output layer metadata as machine-readable JSON
cad2geo inspect imar_plani.ncz --json

# 3. Convert a full drawing to GeoJSON
cad2geo convert imar_plani.ncz master_plan.geojson

# 4. Selective layer extraction (only layers 2 and 5)
cad2geo convert imar_plani.ncz road_centerlines.geojson --layers 2,5

# 5. Convert an AutoCAD DXF file
cad2geo dxf survey.dxf survey.geojson

# 6. Geometric QA repair with snapping and sliver removal
cad2geo clean dirty_plan.ncz clean_plan.geojson --snap-tolerance 0.05 --min-area 0.1
```

Run `cad2geo --help` or `cad2geo <command> --help` for the full option list.

---

## 🧩 Public API Reference

Everything below is importable directly from the top-level `cad2geo` package.

### Readers & Conversion

| Symbol | Description |
| :--- | :--- |
| `NetcadReader(path)` | Catalog-backed reader supporting selective, layer-by-layer decoding. |
| `inspect_source(path)` | Lightweight NCZ/NCA layer catalog (`list[LayerSummary]`). |
| `parse_netcad(path)` | Full parse into a `NetcadParseResult` of stable dataclasses. |
| `is_ncz(path)` | `True` when `path` points at an `.ncz`/`.nca` file. |
| `DXFReader`, `parse_dxf`, `dxf_to_geojson` | Pure-Python ASCII DXF reader and GeoJSON converter. |
| `entities_to_feature_collection`, `write_geojson` | GeoJSON serialisation helpers. |

### Cartography, CRS & Utility Engines

| Symbol | Description |
| :--- | :--- |
| `detect_crs(proj_text, coords, srs_id)` | Turkish datum / Gauss-Krüger / UTM EPSG auto-detection. |
| `sniff_csv_coordinates`, `csv_to_geojson` | Header heuristics for CSV → GeoJSON point conversion. |
| `classify_cad_layer`, `MPYY_CATALOG` | MPYY / e-Plan layer symbology classification. |
| `polygonize_cad_lines`, `split_features_by_cad_layer` | Topology building and per-layer feature splitting. |
| `link_annotations_to_polygons` | Spatial text/MText ↔ parcel annotation matcher. |
| `extract_cad_blocks` | INSERT block-reference and ATTRIB attribute extractor. |
| `extract_cad_dimensions` | CAD dimension entity parser and summariser. |
| `parse_cad_hatches` | Hatch pattern decoder. |
| `slice_cad_to_tile_pyramid` | Multi-scale quadtree tile pyramid generator. |
| `clean_cad_entities`, `snap_endpoints`, `remove_duplicate_vertices` | Geometric QA repair suite. |
| `point_in_polygon`, `buffer_point`, `buffer_polyline`, `CADSpatialIndex` | Spatial operations and a grid index. |
| `export_to_esri_shapefile_asc`, `export_geoparquet_metadata`, `export_flat_geobuf_schema` | Lightweight vector-export metadata helpers. |

### Civil-Engineering Engines

| Symbol | Description |
| :--- | :--- |
| `calculate_flexible_pavement_structural_number` | AASHTO 1993 flexible pavement structural number (SN). |
| `calculate_curb_inlet_hydraulic_capacity` | HEC-22 curb/gutter flow and grate interception. |
| `calculate_culvert_hydraulic_capacity` | Rational-method catchment runoff and barrel sizing. |
| `calculate_superelevation_runoff` | AASHTO superelevation and tangent runoff transition. |
| `evaluate_retaining_wall_stability` | Rankine earth pressure, overturning and sliding FoS. |
| `evaluate_bishop_slope_stability` | Bishop simplified method of slices slope stability. |
| `calculate_crtn_noise_propagation` | UK CRTN L10,18h / Lden façade propagation. |
| `evaluate_intersection_sight_triangles` | AASHTO intersection sight-distance triangles. |
| `calculate_clothoid_spiral_curve` | Euler clothoid spiral transition curve. |
| `generate_road_cross_sections` | Road corridor station cross-section profiles. |
| `calculate_earthwork_cut_fill` | Prismoid earthwork cut/fill volumetric balance. |
| `densify_cad_splines` | Adaptive Bézier spline densification. |
| `generate_tin_contours` | Delaunay TIN surface and contour isolines. |

---

## 📊 Netcad Entity Mapping Matrix

| Netcad CAD Entity | Internal Type | GeoJSON Target | Extracted Properties & Attributes |
| :--- | :--- | :--- | :--- |
| **Point / Nokta** | `TYPE_POINT` | `Point` | Point name, point code, elevation (Z), layer ID |
| **Line / Çizgi** | `TYPE_LINE` | `LineString` | Length, line style, color, layer code |
| **Polyline / Çoklu Doğru**| `TYPE_PLINE` | `LineString` / `Polygon` | Closed flag, vertices, perimeter, area |
| **Arc / Yay** | `TYPE_ARC` | `LineString` (Tessellated) | Center, radius, start angle, end angle |
| **Circle / Çember** | `TYPE_CIRCLE` | `Polygon` (Tessellated) | Center, radius, circumference, area |
| **Text / Yazı** | `TYPE_TEXT` | `Point` | Text string, height, rotation angle, justification |
| **Polygon / Alan** | `TYPE_POLYGON` | `Polygon` / `MultiPolygon` | Parcel number (Ada/Parsel), zoning attribute table |

---

## ⚡ Performance Benchmarks

Indicative single-threaded CPython timings on complex municipal zoning drawings (100MB+ NCZ archives):

| Operation | Dataset Size | Entities | cad2geo Execution Time | Throughput |
| :--- | :--- | :--- | :--- | :--- |
| **Layer Catalog Inspection** | 50 MB NCZ Plan | 150,000 Entities | **4.2 ms** | O(1) Header Scan |
| **Selective Layer Decode** | 50 MB NCZ Plan | 12,500 Entities | **48.6 ms** | 257,000 entities/sec |
| **Full GeoJSON Conversion** | 25 MB NCZ Cadastre | 85,000 Entities | **182.4 ms** | 466,000 entities/sec |

> Timings are illustrative and depend on hardware, drawing complexity and the number of decoded layers.

---

## 🧪 Development & Testing

```bash
# Clone the repository
git clone https://github.com/YusufEminoglu/cad2geo.git
cd cad2geo

# Install in editable mode with development dependencies
pip install -e ".[dev]"

# Run the test suite with coverage (fails under 70%)
pytest tests/ -v --cov=cad2geo

# Lint and auto-format
ruff check .
ruff format .

# Type-check the public API
mypy src
```

The suite lives in `tests/` and is `pytest`-compatible out of the box (`pythonpath = ["src"]` is configured, so no install step is required to run it).

---

## 📄 Academic Citation

If you use **cad2geo** in scientific research, GIS data engineering pipelines, or academic publications, please cite:

```bibtex
@software{eminoglu2026cad2geo,
  author    = {Emino{\u{g}}lu, Yusuf},
  title     = {{cad2geo: Pure-Python Netcad NCZ/NCA CAD Parser and High-Performance GeoJSON Engine}},
  year      = {2026},
  publisher = {Zenodo},
  version   = {0.12.3},
  doi       = {10.5281/zenodo.23677239},
  url       = {https://github.com/YusufEminoglu/cad2geo}
}
```

---

## 📜 License & Lineage

Distributed under the **GPL-2.0-or-later** license. The NCZ decoding lineage and third-party notices are documented in [`THIRD_PARTY_NOTICES.md`](https://github.com/YusufEminoglu/cad2geo/blob/main/THIRD_PARTY_NOTICES.md).
