# -*- coding: utf-8 -*-
"""cad2geo Cookbook — Spatial Annotations, Block Extraction & Buffers."""

import cad2geo

# 1. Text Annotation Matcher
polys = [{"layer": "PARCEL", "coordinates": [(0, 0), (50, 0), (50, 50), (0, 50), (0, 0)]}]
annots = [{"text": "Ada 102 / Parsel 8", "position": (25.0, 25.0)}]
match_res = cad2geo.link_annotations_to_polygons(polys, annots)
print(f"Matched Annotations: {match_res.matched_count}")

# 2. Block Extraction
blocks = cad2geo.extract_cad_blocks([
    {"block_name": "VALVE_HYDRANT", "position": (10.0, 10.0), "attributes": {"DIAMETER": "150mm"}}
])
print(f"Extracted CAD Blocks: {blocks.total_blocks_found}")

# 3. Spatial Index & Buffer
buf = cad2geo.buffer_polyline([(0, 0), (100, 0)], distance=5.0)
print(f"Buffered Polygon vertices: {len(buf)}")
