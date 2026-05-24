"""Color palettes for text-to-image sprite generation.

Each palette is a list of 4 RGB tuples ordered dark -> light:
    [shadow, mid_dark, body, highlight]
The renderer picks colors from these slots when shading.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

RGB = Tuple[int, int, int]

PALETTES: Dict[str, List[RGB]] = {
    "red":     [(60, 10, 10),  (130, 30, 30),   (200, 60, 60),   (255, 130, 100)],
    "blue":    [(10, 20, 60),  (30, 60, 130),   (60, 120, 200),  (130, 180, 255)],
    "green":   [(10, 50, 20),  (40, 110, 50),   (80, 180, 90),   (150, 240, 150)],
    "purple":  [(40, 10, 60),  (90, 30, 120),   (150, 70, 200),  (220, 150, 255)],
    "gold":    [(60, 40, 10),  (130, 100, 30),  (210, 170, 60),  (255, 230, 130)],
    "silver":  [(50, 50, 60),  (110, 110, 130), (170, 170, 190), (230, 230, 240)],
    "shadow":  [(5, 5, 10),    (25, 25, 40),    (60, 60, 80),    (100, 100, 130)],
    "white":   [(120, 120, 130),(180, 180, 200),(220, 220, 235), (255, 255, 255)],
    "fire":    [(60, 10, 0),   (180, 50, 0),    (250, 130, 20),  (255, 220, 80)],
    "ice":     [(20, 40, 80),  (80, 130, 200),  (160, 210, 250), (230, 245, 255)],
    "bone":    [(60, 50, 40),  (140, 130, 110), (210, 200, 180), (250, 245, 230)],
    "pink":    [(80, 30, 60),  (180, 80, 130),  (240, 140, 190), (255, 200, 230)],
    "orange":  [(80, 30, 0),   (180, 80, 0),    (240, 140, 30),  (255, 200, 100)],
    "yellow":  [(80, 70, 0),   (180, 160, 30),  (240, 220, 60),  (255, 250, 130)],
}

DEFAULT_PALETTE = "silver"

# Accent colors used for features (eyes, fire, etc.) regardless of palette.
ACCENT_GOLD: RGB = (255, 220, 80)
ACCENT_RED: RGB = (220, 40, 40)
