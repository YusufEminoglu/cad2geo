# -*- coding: utf-8 -*-
"""
MPYY (Mekânsal Planlar Yapım Yönetmeliği) & e-Plan Symbology Classifier.
Maps CAD layer names and block definitions to official spatial zoning categories and RGB styles.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

MPYY_CATALOG = {
    "RESIDENTIAL": {
        "patterns": [r"KONUT", r"MESKUN", r"GELISME", r"KONUT_ALANI", r"GECEKONDU", r"TOPLU_KONUT"],
        "category": "Konut Alanı (Residential)",
        "color": "#FFD700",
        "fill_opacity": 0.5,
    },
    "COMMERCIAL": {
        "patterns": [r"TICARET", r"MIA", r"OFIS", r"CARSI", r"AVM", r"KDKT", r"TICARI"],
        "category": "Ticaret & İş Alanı (Commercial)",
        "color": "#EF4444",
        "fill_opacity": 0.6,
    },
    "EDUCATION": {
        "patterns": [
            r"EGITIM",
            r"OKUL",
            r"ILKOKUL",
            r"ORTAOKUL",
            r"LISE",
            r"ANAOKULU",
            r"UNIVERSITE",
        ],
        "category": "Eğitim Tesisleri (Education)",
        "color": "#3B82F6",
        "fill_opacity": 0.6,
    },
    "GREEN": {
        "patterns": [
            r"PARK",
            r"YESIL",
            r"REKREASYON",
            r"COCUK",
            r"MEYDAN",
            r"ORMAN",
            r"KORULUK",
            r"PASIF_YESIL",
        ],
        "category": "Açık ve Yeşil Alanlar (Parks & Greenery)",
        "color": "#10B981",
        "fill_opacity": 0.6,
    },
    "HEALTH": {
        "patterns": [r"SAGLIK", r"HASTANE", r"DISP", r"SAGLIK_OCAGI", r"ASM"],
        "category": "Sağlık Tesisleri (Health & Hospital)",
        "color": "#06B6D4",
        "fill_opacity": 0.6,
    },
    "RELIGIOUS": {
        "patterns": [r"IBADET", r"CAMI", r"MESCIT", r"KILISE", r"DINI"],
        "category": "İbadet Alanları (Religious Facilities)",
        "color": "#8B5CF6",
        "fill_opacity": 0.6,
    },
    "INDUSTRY": {
        "patterns": [r"SANAYI", r"DEPOLAMA", r"KSS", r"OSB", r"FABRIKA", r"IMAR_SANAYI"],
        "category": "Sanayi & Depolama Alanı (Industrial)",
        "color": "#6B21A8",
        "fill_opacity": 0.6,
    },
    "TRANSPORTATION": {
        "patterns": [
            r"YOL",
            r"CADDE",
            r"SOKAK",
            r"OTOPARK",
            r"KAVSAK",
            r"TERMINAL",
            r"GARAJ",
            r"TRAMVAY",
            r"RAYLI",
        ],
        "category": "Ulaşım & Yol Ağı (Transportation)",
        "color": "#64748B",
        "fill_opacity": 0.4,
    },
    "ADMINISTRATIVE": {
        "patterns": [r"RESMI", r"KAMU", r"BELEDIYE", r"HUKUMET", r"IDARI", r"KARAKOL", r"ITFAIYE"],
        "category": "Resmi Kurum & İdari Tesisler (Administrative)",
        "color": "#3B82F6",
        "fill_opacity": 0.6,
    },
    "TECHNICAL_INFRASTRUCTURE": {
        "patterns": [r"TEKNIK", r"ALTYAPI", r"TRAFO", r"SU_DEPOSU", r"ARITMA", r"POMPA", r"ENERJI"],
        "category": "Teknik Altyapı (Infrastructure)",
        "color": "#F59E0B",
        "fill_opacity": 0.6,
    },
}


@dataclass
class LayerClassification:
    """Classified MPYY / e-Plan zoning metadata for a CAD layer."""

    layer_name: str
    code: str
    category: str
    color: str
    fill_opacity: float
    is_matched: bool


def classify_cad_layer(layer_name: str) -> LayerClassification:
    """Match a CAD layer name to official Turkish MPYY spatial zoning standards."""
    clean_name = (
        layer_name.upper()
        .replace(" ", "_")
        .replace("İ", "I")
        .replace("Ş", "S")
        .replace("Ğ", "G")
        .replace("Ü", "U")
        .replace("Ö", "O")
        .replace("Ç", "C")
    )

    for code, info in MPYY_CATALOG.items():
        for pat in info["patterns"]:
            if re.search(pat, clean_name):
                return LayerClassification(
                    layer_name=layer_name,
                    code=code,
                    category=info["category"],
                    color=info["color"],
                    fill_opacity=info["fill_opacity"],
                    is_matched=True,
                )

    # Unmatched fallback
    return LayerClassification(
        layer_name=layer_name,
        code="UNCLASSIFIED",
        category="Diğer / Belirtilmemiş (Other CAD Layer)",
        color="#94A3B8",
        fill_opacity=0.3,
        is_matched=False,
    )
