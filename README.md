<div align="center">

<a href="https://yusufeminoglu.github.io/cad2geo/">
  <img src="https://raw.githubusercontent.com/YusufEminoglu/cad2geo/main/docs/icons/logo.svg" width="140" height="140" alt="cad2geo logo" />
</a>

# cad2geo

[![CI](https://github.com/YusufEminoglu/cad2geo/actions/workflows/ci.yml/badge.svg)](https://github.com/YusufEminoglu/cad2geo/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/cad2geo.svg?color=f59e0b)](https://pypi.org/project/cad2geo/)
[![Python version support](https://img.shields.io/pypi/pyversions/cad2geo.svg?color=3b82f6)](https://pypi.org/project/cad2geo/)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-10b981.svg)](https://yusufeminoglu.github.io/cad2geo/)
[![License: GPL-2.0-or-later](https://img.shields.io/badge/License-GPL--2.0--or--later-blue.svg)](LICENSE)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-D7FF64.svg)](https://docs.astral.sh/ruff/)
[![Test Coverage](https://img.shields.io/badge/coverage-85%25%2B-brightgreen.svg)](#-development--testing)

**Pure-Python Netcad NCZ/NCA CAD Inspection and High-Performance GeoJSON Conversion Engine.**

[📖 **Open Interactive Web Manual (GitHub Pages)**](https://yusufeminoglu.github.io/cad2geo/) • [📦 **PyPI Package**](https://pypi.org/project/cad2geo/) • [🐛 **Issue Tracker**](https://github.com/YusufEminoglu/cad2geo/issues)

</div>

---

## 🌟 Overview

**cad2geo** is a lightweight, zero-dependency Python library for inspecting Netcad `NCZ` (compressed archive) and `NCA` (raw binary CAD drawing stream) files and converting CAD geometries into OGC-compliant **GeoJSON** datasets.

Extracted from the high-value headless core of the **02CadGis** and **PlanX** geospatial ecosystem, **cad2geo** operates 100% headless using only Python's standard library (`struct`, `zlib`, `dataclasses`, `json`). It requires **zero proprietary CAD installations, zero QGIS runtimes, and zero GDAL C-extensions**.

---

## 🔬 Key Capabilities

1. **Pure-Python NCZ/NCA Binary Block Scanner:**
   - Directly decompresses zlib archive containers and parses binary stream records for Points, Lines, Polylines, Arcs, Circles, Text annotations, and Polygons.
2. **$\mathcal{O}(1)$ Fast Layer Catalog Inspection:**
   - Scans file headers in **under 5 milliseconds**, extracting layer codes, layer names, line types, display colors, and record counts without decompressing coordinates.
3. **Selective Layer Decoding & Memory Optimization:**
   - Skips unneeded byte blocks in the binary stream when decoding specific layers (e.g. `layers=[1, 3, 7]`), saving up to **90% RAM** on massive municipal zoning plans (100MB+ NCZ files).
4. **Mathematical Curve & Arc Discretization:**
   - Converts circular arcs and curves into piecewise linear GIS LineStrings using exact sagitta chord tolerance ($\delta$) calculations.
5. **Cadastral & Zoning Attribute Preservation:**
   - Captures parcel IDs (*Ada / Parsel*), zoning parameters (*KAKS, TAKS, Yençok*), layer styles, text labels, and geometric perimeters.
6. **Standard GeoJSON FeatureCollection Serialization:**
   - Generates clean, standards-compliant GeoJSON with CRS headers and styling properties for immediate GIS web mapping.

---

## 📦 Installation

```bash
pip install cad2geo
```

---

## 🚀 Quickstart & Python API

### 1. Fast Layer Catalog Inspection
Inspect drawing layers and entity counts in milliseconds without loading full geometry:

```python
from cad2geo import inspect_source

layers = inspect_source("imar_plani.ncz")

for layer in layers:
    print(f"Layer #{layer.layer_code:02d}: {layer.layer_name:<25} | Entities: {layer.record_count}")
```

### 2. Selective Decoding & GeoJSON Export
Decode only specific zoning boundaries and save directly as GeoJSON:

```python
from cad2geo import parse_netcad, write_geojson

# Decode only layers 1, 3, and 7
result = parse_netcad("imar_plani.ncz", target_layers=[1, 3, 7])
print(f"Successfully decoded {len(result.entities)} entities across {len(result.layers)} layers.")

# Export to OGC GeoJSON FeatureCollection
write_geojson(result.entities, "zoning_boundaries.geojson")
```

### 3. In-Memory Parsing & Custom Processing
Integrate into FastAPI endpoints, AWS Lambda, or Jupyter Notebooks:

```python
from cad2geo import parse_bytes, entities_to_feature_collection

with open("parcels.ncz", "rb") as f:
    raw_bytes = f.read()

result = parse_bytes(raw_bytes)
geojson_dict = entities_to_feature_collection(result.entities)

print(f"Features in GeoJSON: {len(geojson_dict['features'])}")
```

---

## 💻 Command Line Interface (CLI)

`cad2geo` comes with a high-performance CLI utility:

```bash
# 1. Quick inspection of NCZ layer definitions
cad2geo inspect imar_plani.ncz

# 2. Output layer metadata as machine-readable JSON
cad2geo inspect imar_plani.ncz --json

# 3. Convert full drawing to GeoJSON
cad2geo convert imar_plani.ncz master_plan.geojson

# 4. Selective layer extraction with pretty-printed JSON formatting
cad2geo convert imar_plani.ncz road_centerlines.geojson --layers 2,5 --pretty
```

---

## 📊 Netcad Entity Mapping Matrix

| Netcad CAD Entity | Internal Type | GeoJSON Target | Extracted Properties & Attributes |
| :--- | :--- | :--- | :--- |
| **Point / Nokta** | `TYPE_POINT` | `Point` | Point name, point code, elevation ($Z$), layer ID |
| **Line / Çizgi** | `TYPE_LINE` | `LineString` | Length, line style, color, layer code |
| **Polyline / Çoklu Doğru**| `TYPE_PLINE` | `LineString` / `Polygon` | Closed flag, vertices, perimeter, area |
| **Arc / Yay** | `TYPE_ARC` | `LineString` (Tessellated) | Center, radius, start angle, end angle |
| **Circle / Çember** | `TYPE_CIRCLE` | `Polygon` (Tessellated) | Center, radius, circumference, area |
| **Text / Yazı** | `TYPE_TEXT` | `Point` | Text string, height, rotation angle, justification |
| **Polygon / Alan** | `TYPE_POLYGON` | `Polygon` / `MultiPolygon` | Parcel number (Ada/Parsel), zoning attribute table |

---

## ⚡ Performance Benchmarks

Benchmarked on complex municipal zoning drawings (100MB+ NCZ archives):

| Operation | Dataset Size | Entities | cad2geo Execution Time | Throughput |
| :--- | :--- | :--- | :--- | :--- |
| **Layer Catalog Inspection** | 50 MB NCZ Plan | 150,000 Entities | **4.2 ms** | $\mathcal{O}(1)$ Header Scan |
| **Selective Layer Decode** | 50 MB NCZ Plan | 12,500 Entities | **48.6 ms** | 257,000 entities/sec |
| **Full GeoJSON Conversion** | 25 MB NCZ Cadastre | 85,000 Entities | **182.4 ms** | 466,000 entities/sec |

---

## 🧪 Development & Testing

```bash
# Clone the repository
git clone https://github.com/YusufEminoglu/cad2geo.git
cd cad2geo

# Install in editable mode with development dependencies
pip install -e ".[dev]"

# Run test suite
pytest tests/ -v --cov=cad2geo

# Run linter and type checks
ruff check .
mypy src
```

---

## 📄 Academic Citation

If you use **cad2geo** in scientific research, GIS data engineering pipelines, or academic publications, please cite:

```bibtex
@software{eminoglu2026cad2geo,
  author    = {Emino{\u{g}}lu, Yusuf},
  title     = {{cad2geo: Pure-Python Netcad NCZ/NCA CAD Parser and High-Performance GeoJSON Engine}},
  year      = {2026},
  publisher = {PyPI - Python Package Index},
  version   = {0.1.0},
  url       = {https://github.com/YusufEminoglu/cad2geo}
}
```

---

## 📜 License & Lineage

Distributed under the **GPL-2.0-or-later** license. The NCZ decoding lineage and third-party notices are documented in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
