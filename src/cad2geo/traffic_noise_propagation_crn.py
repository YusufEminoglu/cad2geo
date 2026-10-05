# -*- coding: utf-8 -*-
"""Calculation of Road Traffic Noise (CRTN) Acoustic Decibel Propagation Engine for cad2geo."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class RoadAcousticProfile:
    traffic_flow_vehicles_per_hour: float = 2400.0  # q
    heavy_vehicles_percentage: float = 15.0  # p (%)
    average_traffic_speed_kmh: float = 85.0  # V
    road_gradient_pct: float = 2.5  # G
    road_surface_correction_db: float = -1.0  # Dense asphalt porous concrete
    facade_reflection_correction_db: float = 2.5  # Façade reflection +2.5 dB


@dataclass
class TrafficNoiseResult:
    basic_noise_level_l10_18h_db: float
    facade_noise_level_l10_db: float
    equivalent_day_evening_night_lden_db: float
    receiver_distance_m: float
    distance_attenuation_db: float
    is_exceeding_residential_threshold: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "l10_18h_db": round(self.basic_noise_level_l10_18h_db, 1),
            "facade_l10_db": round(self.facade_noise_level_l10_db, 1),
            "lden_db": round(self.equivalent_day_evening_night_lden_db, 1),
            "distance_m": round(self.receiver_distance_m, 1),
            "exceeds_threshold": self.is_exceeding_residential_threshold,
        }


def calculate_crtn_noise_propagation(
    receiver_distance_m: float = 35.0,  # Distance from road centerline to building facade
    receiver_height_m: float = 4.0,  # 1st floor window height
    profile: RoadAcousticProfile | None = None,
    ground_absorption_factor: float = 0.5,  # 0.0 hard ground, 1.0 soft grass
) -> TrafficNoiseResult:
    """Compute UK Department of Transport CRTN traffic acoustic decibel levels at receiver facades.

    CRTN Basic Noise Level at 10m:
    L10_10m = 42.2 + 10 * log10(q) + Delta_v_p + Delta_G
    where Delta_v_p = 33 * log10(V + 40 + 500/V) + 10 * log10(1 + 5p / V) - 68.8
    """
    p = profile or RoadAcousticProfile()
    q = max(100.0, p.traffic_flow_vehicles_per_hour)
    v = max(20.0, p.average_traffic_speed_kmh)
    p_heavy = max(0.0, min(100.0, p.heavy_vehicles_percentage))
    g = max(0.0, p.road_gradient_pct)
    d = max(4.0, receiver_distance_m)

    # 1. Base traffic volume emission
    base_l10 = 42.2 + 10.0 * math.log10(q)

    # 2. Speed and heavy vehicle correction
    speed_heavy_term = 33.0 * math.log10(v + 40.0 + 500.0 / v) + 10.0 * math.log10(1.0 + (5.0 * p_heavy) / v) - 68.8

    # 3. Gradient correction
    grad_term = 0.3 * g

    # Basic noise level at reference 10m
    l10_ref = base_l10 + speed_heavy_term + grad_term + p.road_surface_correction_db

    # 4. Distance attenuation (geometric spreading + ground absorption)
    slant_dist = math.hypot(d, receiver_height_m - 1.2)
    dist_attenuation = 10.0 * math.log10(slant_dist / 10.0) + (ground_absorption_factor * 5.2 * math.log10(slant_dist / 10.0))

    # Facade noise level
    facade_l10 = l10_ref - dist_attenuation + p.facade_reflection_correction_db

    # Conversion to Lden (EU Environmental Noise Directive standard: Lden ~= L10 - 2.5 dB)
    lden = facade_l10 - 2.5
    is_exceeds = lden >= 65.0  # WHO / EU daytime residential limit 65 dBA

    return TrafficNoiseResult(
        basic_noise_level_l10_18h_db=l10_ref,
        facade_noise_level_l10_db=facade_l10,
        equivalent_day_evening_night_lden_db=lden,
        receiver_distance_m=d,
        distance_attenuation_db=dist_attenuation,
        is_exceeding_residential_threshold=is_exceeds,
    )
