# -*- coding: utf-8 -*-
"""Euler Clothoid Spiral Transition Curve Engine for cad2geo (Highway & Railway Alignment)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Sequence


@dataclass
class SpiralCurveParams:
    spiral_parameter_a: float = 120.0  # Clothoid parameter A: A^2 = R * L
    circular_curve_radius_r: float = 300.0  # Radius of circular curve in meters
    spiral_length_l: float | None = None  # Length of spiral (computed if None)
    origin_point: tuple[float, float] = (0.0, 0.0)
    initial_bearing_degrees: float = 0.0


@dataclass
class ClothoidTransitionResult:
    spiral_parameter_a: float
    spiral_length_l: float
    circular_radius_r: float
    total_spiral_angle_rad: float
    total_spiral_angle_deg: float
    shift_p_m: float  # Shift (P) of the circular curve
    spiral_points: list[tuple[float, float]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter_a": round(self.spiral_parameter_a, 2),
            "spiral_length_m": round(self.spiral_length_l, 2),
            "radius_m": round(self.circular_radius_r, 2),
            "spiral_angle_deg": round(self.total_spiral_angle_deg, 3),
            "shift_p_m": round(self.shift_p_m, 3),
            "points_count": len(self.spiral_points),
        }


def calculate_clothoid_spiral_curve(
    params: SpiralCurveParams | None = None,
    num_sample_points: int = 20,
) -> ClothoidTransitionResult:
    """Compute Euler spiral (clothoid) transition points using Fresnel integral Taylor series expansions.
    
    Formulae:
    L = A^2 / R
    tau = L / (2 * R) = L^2 / (2 * A^2)
    X(l) = l * (1 - tau^2 / 10 + tau^4 / 216 - ...)
    Y(l) = l * (tau / 3 - tau^3 / 42 + tau^5 / 1320 - ...)
    p (shift) = Y - R * (1 - cos(tau)) ~= L^2 / (24 * R)
    """
    p = params or SpiralCurveParams()

    if p.spiral_length_l is not None:
        l_len = p.spiral_length_l
        a_param = math.sqrt(p.circular_curve_radius_r * l_len)
    else:
        a_param = p.spiral_parameter_a
        l_len = (a_param ** 2) / max(1e-4, p.circular_curve_radius_r)

    total_tau = l_len / (2.0 * max(1e-4, p.circular_curve_radius_r))
    shift_p = (l_len ** 2) / (24.0 * max(1e-4, p.circular_curve_radius_r))

    rad_bearing = math.radians(p.initial_bearing_degrees)
    cos_b = math.cos(rad_bearing)
    sin_b = math.sin(rad_bearing)

    points: list[tuple[float, float]] = []

    for i in range(num_sample_points + 1):
        s = (l_len * i) / float(num_sample_points)
        tau = (s ** 2) / (2.0 * max(1e-4, a_param ** 2))

        # Taylor series approximation of Fresnel integrals
        x_local = s * (1.0 - (tau ** 2) / 10.0 + (tau ** 4) / 216.0)
        y_local = s * (tau / 3.0 - (tau ** 3) / 42.0 + (tau ** 5) / 1320.0)

        # Rotate and translate to global coordinate system
        x_glob = p.origin_point[0] + (x_local * cos_b - y_local * sin_b)
        y_glob = p.origin_point[1] + (x_local * sin_b + y_local * cos_b)
        points.append((round(x_glob, 3), round(y_glob, 3)))

    return ClothoidTransitionResult(
        spiral_parameter_a=a_param,
        spiral_length_l=l_len,
        circular_radius_r=p.circular_curve_radius_r,
        total_spiral_angle_rad=total_tau,
        total_spiral_angle_deg=math.degrees(total_tau),
        shift_p_m=shift_p,
        spiral_points=points,
    )
