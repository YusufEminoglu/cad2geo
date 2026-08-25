# -*- coding: utf-8 -*-
"""
CAD to GIS Topology & Conversion Engine:
Automatic line-to-polygon closure, topological snapping, and layer separation.
"""

from __future__ import annotations

import math
from typing import Any


def polygonize_cad_lines(
    linestrings: list[list[tuple[float, float]]],
    tolerance: float = 0.01,
) -> list[list[tuple[float, float]]]:
    """Chain connected CAD line segments into closed polygon rings."""
    if not linestrings:
        return []

    # Filter out empty or degenerate lines
    valid_lines = [list(ls) for ls in linestrings if len(ls) >= 2]
    if not valid_lines:
        return []

    # Check already closed linestrings
    closed_rings: list[list[tuple[float, float]]] = []
    unclosed_segments: list[list[tuple[float, float]]] = []

    for ls in valid_lines:
        dx = ls[0][0] - ls[-1][0]
        dy = ls[0][1] - ls[-1][1]
        if math.hypot(dx, dy) <= tolerance:
            ring = list(ls)
            ring[-1] = ring[0]  # Force exact closure
            closed_rings.append(ring)
        else:
            unclosed_segments.append(list(ls))

    # Greedy segment chaining for unclosed lines
    while unclosed_segments:
        curr_chain = unclosed_segments.pop(0)
        extended = True

        while extended:
            extended = False
            head = curr_chain[0]
            tail = curr_chain[-1]

            # Check if current chain is closed
            if (
                math.hypot(head[0] - tail[0], head[1] - tail[1]) <= tolerance
                and len(curr_chain) >= 4
            ):
                curr_chain[-1] = curr_chain[0]
                closed_rings.append(curr_chain)
                break

            # Search matching segment in remaining
            for idx, cand in enumerate(unclosed_segments):
                c_head = cand[0]
                c_tail = cand[-1]

                # Match tail with candidate head
                if math.hypot(tail[0] - c_head[0], tail[1] - c_head[1]) <= tolerance:
                    curr_chain.extend(cand[1:])
                    unclosed_segments.pop(idx)
                    extended = True
                    break
                # Match tail with candidate tail (reverse candidate)
                elif math.hypot(tail[0] - c_tail[0], tail[1] - c_tail[1]) <= tolerance:
                    curr_chain.extend(reversed(cand[:-1]))
                    unclosed_segments.pop(idx)
                    extended = True
                    break
                # Match head with candidate tail
                elif math.hypot(head[0] - c_tail[0], head[1] - c_tail[1]) <= tolerance:
                    curr_chain = cand[:-1] + curr_chain
                    unclosed_segments.pop(idx)
                    extended = True
                    break
                # Match head with candidate head (reverse candidate)
                elif math.hypot(head[0] - c_head[0], head[1] - c_head[1]) <= tolerance:
                    curr_chain = list(reversed(cand[1:])) + curr_chain
                    unclosed_segments.pop(idx)
                    extended = True
                    break

    return closed_rings


def split_features_by_cad_layer(
    features: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group a flat list of CAD GeoJSON features into distinct layer dictionaries."""
    layers: dict[str, list[dict[str, Any]]] = {}

    for feat in features:
        props = feat.get("properties", {})
        layer_name = props.get("layer") or props.get("Layer") or props.get("layer_name") or "0"
        if layer_name not in layers:
            layers[layer_name] = []
        layers[layer_name].append(feat)

    return layers
