# cad2geo

**cad2geo** is a small Python SDK for inspecting Netcad `NCZ`/`NCA` drawings and converting supported geometry into GeoJSON without QGIS.

The first release focuses on the high-value headless core extracted from 02CadGis:

- pure-Python NCZ/NCA block scanning and geometry decoding
- cheap layer catalog inspection before full decode
- selective layer decoding
- stable dataclasses for coordinates, entities, attribute tables, and parse results
- GeoJSON FeatureCollection export
- CLI commands for inspection and conversion

## Installation

```bash
pip install cad2geo
```

## Python API

```python
from cad2geo import inspect_source, parse_netcad, write_geojson

layers = inspect_source("imar_plani.ncz")
for layer in layers:
    print(layer.layer_code, layer.layer_name, layer.record_count)

result = parse_netcad("imar_plani.ncz")
write_geojson(result.entities, "imar_plani.geojson")
```

## CLI

```bash
cad2geo inspect imar_plani.ncz
cad2geo inspect imar_plani.ncz --json
cad2geo convert imar_plani.ncz imar_plani.geojson
cad2geo convert imar_plani.ncz roads.geojson --layers 1,3,7
```

## Scope

`cad2geo` 0.1.0 intentionally does not wrap QGIS, GDAL/OGR, DWG, DXF, FileGDB, or GeoPackage workflows. Those remain in the 02CadGis QGIS plugin. The SDK starts with a dependency-free Netcad reader so it can run in scripts, notebooks, CI, and server-side processing.

## License

GPL-2.0-or-later. The NCZ decoding lineage is documented in `THIRD_PARTY_NOTICES.md`.
