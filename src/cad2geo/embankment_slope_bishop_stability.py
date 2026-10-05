# -*- coding: utf-8 -*-
"""Geotechnical Embankment Circular Slip Failure & Bishop's Simplified Safety Factor Engine for cad2geo."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class SlopeSliceProfile:
    cohesion_c_kpa: float = 15.0
    friction_angle_phi_deg: float = 28.0
    soil_unit_weight_gamma_kn_m3: float = 19.5
    pore_water_pressure_ratio_ru: float = 0.15
    embankment_height_h_m: float = 8.0
    slope_angle_beta_deg: float = 33.7  # 1V:1.5H slope


@dataclass
class BishopStabilityResult:
    factor_of_safety_bishop: float
    critical_slip_circle_radius_m: float
    is_slope_stable: bool
    pore_water_pressure_ratio: float
    iterations_to_convergence: int
    driving_moment_kn_m: float
    resisting_moment_kn_m: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "fs_bishop": round(self.factor_of_safety_bishop, 2),
            "radius_m": round(self.critical_slip_circle_radius_m, 1),
            "is_stable": self.is_slope_stable,
            "ru": round(self.pore_water_pressure_ratio, 2),
            "iterations": self.iterations_to_convergence,
        }


def evaluate_bishop_slope_stability(
    profile: SlopeSliceProfile | None = None,
    num_slices: int = 10,
    tolerance: float = 0.001,
) -> BishopStabilityResult:
    """Compute geotechnical circular arc slope stability using Bishop's Simplified Method of Slices.

    Bishop's Simplified Safety Factor FS:
    FS = [ sum( (c' * b + (W - u * b) * tan(phi')) / m_alpha ) ] / [ sum( W * sin(alpha) ) ]
    where m_alpha = cos(alpha) * (1 + tan(alpha) * tan(phi') / FS)
    """
    p = profile or SlopeSliceProfile()
    c = max(0.1, p.cohesion_c_kpa)
    phi_rad = math.radians(p.friction_angle_phi_deg)
    gamma = p.soil_unit_weight_gamma_kn_m3
    h = p.embankment_height_h_m
    beta_rad = math.radians(p.slope_angle_beta_deg)

    # Geometry of critical trial slip circle
    r = h * 1.65
    b_total = h / math.tan(beta_rad) + h * 0.8
    b_slice = b_total / float(num_slices)

    # Discretize slope into slices
    slice_weights: list[float] = []
    slice_alphas: list[float] = []
    slice_widths: list[float] = []

    for i in range(num_slices):
        # Normalized slice elevation above slip circle
        alpha_i = math.radians(-35.0 + (70.0 / num_slices) * (i + 0.5))
        h_i = max(0.5, h * math.sin((math.pi / num_slices) * (i + 0.5)))
        w_i = gamma * b_slice * h_i

        slice_weights.append(w_i)
        slice_alphas.append(alpha_i)
        slice_widths.append(b_slice)

    # Driving moment denominator: sum(W * sin(alpha))
    driving_moment_sum = sum(w * math.sin(a) for w, a in zip(slice_weights, slice_alphas))
    driving_moment_sum = max(10.0, driving_moment_sum)

    # Iterative solution for Bishop FS
    fs = 1.50
    iterations = 0

    for _it in range(30):
        iterations += 1
        resisting_sum = 0.0
        for w, a, b in zip(slice_weights, slice_alphas, slice_widths):
            # Pore water pressure u = ru * gamma * h
            u_i = p.pore_water_pressure_ratio_ru * w / b
            # m_alpha term
            m_alpha = math.cos(a) * (1.0 + (math.tan(a) * math.tan(phi_rad)) / fs)
            if abs(m_alpha) < 0.05:
                m_alpha = 0.05 if m_alpha >= 0 else -0.05

            numerator = c * b + (w - u_i * b) * math.tan(phi_rad)
            resisting_sum += numerator / m_alpha

        new_fs = resisting_sum / driving_moment_sum
        if abs(new_fs - fs) < tolerance:
            fs = new_fs
            break
        fs = new_fs

    is_stable = fs >= 1.30  # Standard geotechnical safety requirement for cut/fill slopes

    return BishopStabilityResult(
        factor_of_safety_bishop=max(0.5, fs),
        critical_slip_circle_radius_m=r,
        is_slope_stable=is_stable,
        pore_water_pressure_ratio=p.pore_water_pressure_ratio_ru,
        iterations_to_convergence=iterations,
        driving_moment_kn_m=driving_moment_sum * r,
        resisting_moment_kn_m=resisting_sum * r,
    )
