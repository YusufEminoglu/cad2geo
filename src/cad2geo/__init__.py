# -*- coding: utf-8 -*-
"""
cad2geo — Pure-Python CAD to GIS Converter & Reader Suite (02CadGis Engine).
"""

from __future__ import annotations

__version__ = "0.2.0"
__author__ = "Yusuf Eminoğlu"

from .crs import DetectedCRS, detect_crs
from .csv_sniffer import CsvProfile, csv_to_geojson, sniff_csv_coordinates
from .geojson import entities_to_feature_collection, write_geojson
from .mpyy import MPYY_CATALOG, LayerClassification, classify_cad_layer
from .reader import (
    Cad2GeoError,
    LayerSummary,
    NetcadReader,
    inspect_source,
    is_ncz,
    parse_netcad,
)
from .topology import polygonize_cad_lines, split_features_by_cad_layer

__all__ = [
    "__version__",
    # Netcad Reader
    "NetcadReader",
    "Cad2GeoError",
    "LayerSummary",
    "inspect_source",
    "parse_netcad",
    "is_ncz",
    # GeoJSON
    "entities_to_feature_collection",
    "write_geojson",
    # Smart CRS Detector
    "detect_crs",
    "DetectedCRS",
    # Smart CSV Coordinate Sniffer
    "sniff_csv_coordinates",
    "csv_to_geojson",
    "CsvProfile",
    # MPYY & e-Plan Symbology
    "classify_cad_layer",
    "LayerClassification",
    "MPYY_CATALOG",
    # Topology & Layer Split
    "polygonize_cad_lines",
    "split_features_by_cad_layer",
]
