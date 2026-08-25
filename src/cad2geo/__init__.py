"""cad2geo - CAD/Netcad drawing data for Python geospatial workflows."""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "Yusuf Eminoğlu"
__email__ = "yusufeminoglu@gmail.com"

from .geojson import entities_to_feature_collection, write_geojson
from .ncz_engine.model import (
    NetcadAttributeRow,
    NetcadAttributeTable,
    NetcadCoordinate,
    NetcadEntity,
    NetcadParseResult,
)
from .reader import (
    Cad2GeoError,
    LayerSummary,
    NetcadReader,
    inspect_source,
    parse_netcad,
)

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "Cad2GeoError",
    "LayerSummary",
    "NetcadReader",
    "NetcadCoordinate",
    "NetcadEntity",
    "NetcadAttributeRow",
    "NetcadAttributeTable",
    "NetcadParseResult",
    "inspect_source",
    "parse_netcad",
    "entities_to_feature_collection",
    "write_geojson",
]
