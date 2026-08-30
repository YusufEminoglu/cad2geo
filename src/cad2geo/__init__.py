__version__ = "0.11.0"
__author__ = "Yusuf Eminoğlu"

from . import cli
from .annotation_matcher import (
    AnnotationMatchResult,
    MatchedPolygonAnnotation,
    link_annotations_to_polygons,
)
from .block_extractor import (
    CADBlockInstance,
    CADBlockLibrary,
    extract_cad_blocks,
)
from .contour_interpolator import (
    ContourIsoline,
    TINSurfaceMesh,
    generate_tin_contours,
)
from .cross_section_generator import (
    CrossSectionProfile,
    StationCrossSectionSet,
    generate_road_cross_sections,
)
from .crs import DetectedCRS, detect_crs
from .csv_sniffer import CsvProfile, csv_to_geojson, sniff_csv_coordinates
from .cut_and_fill_calc import (
    CutFillVolumeReport,
    PrismoidCell,
    calculate_earthwork_cut_fill,
)
from .hydrological_culvert_sizing import (
    CatchmentRunoffProfile,
    CulvertSizingResult,
    calculate_culvert_hydraulic_capacity,
)
from .pavement_structural_number_sn import (
    PavementLayerConfig,
    PavementStructuralDesignResult,
    calculate_flexible_pavement_structural_number,
)
from .retaining_wall_earth_pressure import (
    RetainingWallStabilityResult,
    SoilWallParameters,
    evaluate_retaining_wall_stability,
)
from .sight_distance_triangle import (
    IntersectionLegProfile,
    SightTriangleResult,
    evaluate_intersection_sight_triangles,
)
from .spiral_curve_transition import (
    ClothoidTransitionResult,
    SpiralCurveParams,
    calculate_clothoid_spiral_curve,
)
from .stormwater_curb_inlet_hydraulics import (
    CurbGutterFlowResult,
    CurbGutterProfile,
    calculate_curb_inlet_hydraulic_capacity,
)
from .superelevation_runoff_designer import (
    StationSuperelevationCrossSection,
    SuperelevationConfig,
    SuperelevationDesignResult,
    calculate_superelevation_runoff,
)
from .dimension_parser import (
    DimensionEntity,
    DimensionSummary,
    extract_cad_dimensions,
)
from .dxf import (
    DXFEntity,
    DXFReader,
    dxf_to_geojson,
    parse_dxf,
)
from .geojson import entities_to_feature_collection, write_geojson
from .hatch_parser import (
    HatchLine,
    HatchPattern,
    parse_cad_hatches,
)
from .mpyy import MPYY_CATALOG, LayerClassification, classify_cad_layer
from .qa_cleaner import (
    QARepairReport,
    clean_cad_entities,
    remove_duplicate_vertices,
    snap_endpoints,
)
from .reader import (
    Cad2GeoError,
    LayerSummary,
    NetcadReader,
    inspect_source,
    is_ncz,
    parse_netcad,
)
from .spatial_ops import (
    CADSpatialIndex,
    buffer_point,
    buffer_polyline,
    point_in_polygon,
)
from .spline_densifier import (
    SplineDensificationResult,
    densify_cad_splines,
)
from .tile_slicer import (
    CADTileBounds,
    CADTilePyramid,
    slice_cad_to_tile_pyramid,
)
from .topology import (
    polygonize_cad_lines,
    split_features_by_cad_layer,
)
from .vector_export import (
    export_flat_geobuf_schema,
    export_geoparquet_metadata,
    export_to_esri_shapefile_asc,
)

__all__ = [
    "__version__",
    # Netcad Reader
    "NetcadReader",
    "Cad2GeoError",
    "LayerSummary",
    "inspect_source",
    "parse_netcad",
    "is_ncz",
    # DXF Reader & Converter
    "DXFReader",
    "DXFEntity",
    "parse_dxf",
    "dxf_to_geojson",
    # QA & Geometry Cleaner
    "clean_cad_entities",
    "snap_endpoints",
    "remove_duplicate_vertices",
    "QARepairReport",
    # Spatial Operations & Buffer
    "point_in_polygon",
    "buffer_point",
    "buffer_polyline",
    "CADSpatialIndex",
    # Vector Exporters
    "export_to_esri_shapefile_asc",
    "export_geoparquet_metadata",
    "export_flat_geobuf_schema",
    # Hatches & Tiles
    "parse_cad_hatches",
    "HatchPattern",
    "HatchLine",
    "slice_cad_to_tile_pyramid",
    "CADTilePyramid",
    "CADTileBounds",
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
    # Spatial Annotation Matcher
    "link_annotations_to_polygons",
    "AnnotationMatchResult",
    "MatchedPolygonAnnotation",
    # CAD Block Extractor
    "extract_cad_blocks",
    "CADBlockLibrary",
    "CADBlockInstance",
    # TIN Surface & Elevation Contours
    "generate_tin_contours",
    "TINSurfaceMesh",
    "ContourIsoline",
    # CAD Dimension Parser
    "extract_cad_dimensions",
    "DimensionSummary",
    "DimensionEntity",
    # Earthwork Cut and Fill Volumetric Balancer
    "calculate_earthwork_cut_fill",
    "CutFillVolumeReport",
    "PrismoidCell",
    # CAD Spline & Curve Adaptive Densifier
    "densify_cad_splines",
    "SplineDensificationResult",
    # Intersection Sight Distance Triangle
    "evaluate_intersection_sight_triangles",
    "SightTriangleResult",
    "IntersectionLegProfile",
    # Road Corridor Cross-Section Profiles
    "generate_road_cross_sections",
    "CrossSectionProfile",
    "StationCrossSectionSet",
    # Euler Clothoid Spiral Transition Curves
    "calculate_clothoid_spiral_curve",
    "ClothoidTransitionResult",
    "SpiralCurveParams",
    # Highway Culvert Hydrology & Barrel Sizing
    "calculate_culvert_hydraulic_capacity",
    "CulvertSizingResult",
    "CatchmentRunoffProfile",
    # Highway Superelevation & Runoff Transition
    "calculate_superelevation_runoff",
    "SuperelevationDesignResult",
    "SuperelevationConfig",
    "StationSuperelevationCrossSection",
    # Retaining Wall Earth Pressure & Stability
    "evaluate_retaining_wall_stability",
    "RetainingWallStabilityResult",
    "SoilWallParameters",
    # AASHTO Flexible Pavement Structural Number (SN)
    "calculate_flexible_pavement_structural_number",
    "PavementStructuralDesignResult",
    "PavementLayerConfig",
    # Highway Curb Gutter Flow & Grate Hydraulics (HEC-22)
    "calculate_curb_inlet_hydraulic_capacity",
    "CurbGutterFlowResult",
    "CurbGutterProfile",
]
