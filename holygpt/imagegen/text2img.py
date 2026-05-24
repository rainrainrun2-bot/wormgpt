"""Text-to-image: parse a description and render a procedural sprite.

Pipeline:
    prompt --> tokens --> KEYWORDS lookup --> {template, palette, features}
    --> render template to a depth grid (silhouette)
    --> add features (horns, wings, sword, ...)
    --> apply shading + outline
    --> map cells to RGBA pixels using the chosen palette
    --> nearest-neighbor upscale to target size

No external APIs, no models. The "search" step is just a keyword table.
"""

from __future__ import annotations

import math
import random
import re
from typing import Dict, List, Optional, Sequence, Tuple

from . import palettes, templates
from .shapes import (
    CELL_ACCENT1,
    CELL_ACCENT2,
    CELL_BODY,
    CELL_HIGHLIGHT,
    CELL_OUTLINE,
    CELL_SHADOW,
    CELL_TRANSPARENT,
    Grid,
    add_outline,
    add_shading,
    fill_circle,
    fill_rect,
    fill_triangle,
)

RGBA = Tuple[int, int, int, int]


# --- Keyword "search" table ---------------------------------------------------

# Each keyword may set a template, a palette, add features, or add effects.
# Later keywords override earlier ones for template/palette, EXCEPT that an
# explicit color word (red, blue, ...) always wins over a character-type
# default palette (knight -> silver, demon -> red, ...). Keywords whose
# *only* job is setting a palette are tagged with "color": True.
KEYWORDS: Dict[str, Dict[str, object]] = {
    # body templates
    "human":    {"template": "humanoid"},
    "person":   {"template": "humanoid"},
    "man":      {"template": "humanoid"},
    "woman":    {"template": "humanoid"},
    "knight":   {"template": "humanoid", "features": ["sword"], "palette": "silver"},
    "warrior":  {"template": "humanoid", "features": ["sword"]},
    "mage":     {"template": "humanoid", "features": ["hat", "staff"], "palette": "purple"},
    "wizard":   {"template": "humanoid", "features": ["hat", "staff"], "palette": "blue"},
    "demon":    {"template": "humanoid", "features": ["horns", "wings"], "palette": "red"},
    "devil":    {"template": "humanoid", "features": ["horns"], "palette": "red"},
    "angel":    {"template": "humanoid", "features": ["halo", "wings"], "palette": "white"},
    "skeleton": {"template": "humanoid", "palette": "bone"},
    "zombie":   {"template": "humanoid", "palette": "green"},
    "king":     {"template": "humanoid", "features": ["crown"], "palette": "gold"},
    "queen":    {"template": "humanoid", "features": ["crown"], "palette": "purple"},
    "ghost":    {"template": "blob", "palette": "white"},
    "dragon":   {"template": "dragon"},
    "wyrm":     {"template": "dragon"},
    "serpent":  {"template": "dragon"},
    "lizard":   {"template": "dragon"},
    "slime":    {"template": "blob", "palette": "green"},
    "blob":     {"template": "blob"},
    "robot":    {"template": "robot", "palette": "silver"},
    "mech":     {"template": "robot", "palette": "silver"},
    "droid":    {"template": "robot", "palette": "silver"},

    # explicit colors / palettes (these win over type defaults)
    "red":      {"palette": "red", "color": True},
    "crimson":  {"palette": "red", "color": True},
    "blue":     {"palette": "blue", "color": True},
    "azure":    {"palette": "blue", "color": True},
    "green":    {"palette": "green", "color": True},
    "emerald":  {"palette": "green", "color": True},
    "purple":   {"palette": "purple", "color": True},
    "violet":   {"palette": "purple", "color": True},
    "gold":     {"palette": "gold", "color": True},
    "golden":   {"palette": "gold", "color": True},
    "silver":   {"palette": "silver", "color": True},
    "black":    {"palette": "shadow", "color": True},
    "dark":     {"palette": "shadow", "color": True},
    "white":    {"palette": "white", "color": True},
    "pink":     {"palette": "pink", "color": True},
    "orange":   {"palette": "orange", "color": True},
    "yellow":   {"palette": "yellow", "color": True},
    "fire":     {"palette": "fire", "color": True, "features": ["eyes"]},
    "fiery":    {"palette": "fire", "color": True},
    "flame":    {"palette": "fire", "color": True},
    "ice":      {"palette": "ice", "color": True},
    "frost":    {"palette": "ice", "color": True},
    "frozen":   {"palette": "ice", "color": True},
    "shadow":   {"palette": "shadow", "color": True},

    # features
    "wings":    {"features": ["wings"]},
    "winged":   {"features": ["wings"]},
    "horns":    {"features": ["horns"]},
    "horned":   {"features": ["horns"]},
    "sword":    {"features": ["sword"]},
    "shield":   {"features": ["shield"]},
    "crown":    {"features": ["crown"]},
    "staff":    {"features": ["staff"]},
    "hat":      {"features": ["hat"]},
    "halo":     {"features": ["halo"]},
    "eyes":     {"features": ["eyes"]},
    "evil":     {"features": ["horns", "eyes"]},
    "cute":     {"features": ["eyes"]},
    "glowing":  {"features": ["eyes"]},
}


def parse_prompt(prompt: str) -> Dict[str, object]:
    """Extract template / palette / features from a free-text prompt."""
    tokens = re.findall(r"[a-z]+", prompt.lower())
    template = "humanoid"
    default_palette: Optional[str] = None
    explicit_palette: Optional[str] = None
    features: List[str] = []
    seen_features = set()
    for token in tokens:
        attrs = KEYWORDS.get(token)
        if not attrs:
            continue
        if "template" in attrs:
            template = attrs["template"]  # type: ignore[assignment]
        if "palette" in attrs:
            if attrs.get("color"):
                explicit_palette = attrs["palette"]  # type: ignore[assignment]
            else:
                default_palette = attrs["palette"]  # type: ignore[assignment]
        for feat in attrs.get("features", []):  # type: ignore[union-attr]
            if feat not in seen_features:
                seen_features.add(feat)
                features.append(feat)
    palette = explicit_palette or default_palette or palettes.DEFAULT_PALETTE
    return {"template": template, "palette": palette, "features": features}


# --- Feature renderers --------------------------------------------------------


def _add_horns(g: Grid, size: int) -> None:
    cx = size // 2
    head_top = size // 8
    horn_h = max(2, size // 10)
    fill_triangle(
        g,
        [
            (cx - size // 5, head_top + 1),
            (cx - size // 7, head_top + 1),
            (cx - size // 4, max(0, head_top - horn_h)),
        ],
        CELL_ACCENT1,
    )
    fill_triangle(
        g,
        [
            (cx + size // 7, head_top + 1),
            (cx + size // 5, head_top + 1),
            (cx + size // 4, max(0, head_top - horn_h)),
        ],
        CELL_ACCENT1,
    )


def _add_wings(g: Grid, size: int) -> None:
    cx = size // 2
    mid = int(size * 0.45)
    fill_triangle(
        g,
        [
            (cx - size // 6, mid),
            (max(1, cx - size // 2 + 2), mid - size // 5),
            (max(1, cx - size // 2 + 2), mid + size // 6),
        ],
        CELL_HIGHLIGHT,
    )
    fill_triangle(
        g,
        [
            (cx + size // 6, mid),
            (min(size - 2, cx + size // 2 - 2), mid - size // 5),
            (min(size - 2, cx + size // 2 - 2), mid + size // 6),
        ],
        CELL_HIGHLIGHT,
    )


def _add_hat(g: Grid, size: int) -> None:
    cx = size // 2
    head_top = max(1, size // 8 - 1)
    fill_triangle(
        g,
        [
            (cx - size // 6, head_top),
            (cx + size // 6, head_top),
            (cx, max(0, head_top - size // 4)),
        ],
        CELL_ACCENT1,
    )


def _add_sword(g: Grid, size: int) -> None:
    cx = size // 2
    body_w = max(2, size // 7)
    sword_x = min(size - 2, cx + body_w + max(2, size // 12))
    sword_top = max(2, size // 10)
    sword_bot = int(size * 0.62)
    fill_rect(g, sword_x, sword_top, sword_x, sword_bot, CELL_HIGHLIGHT)
    fill_rect(g, sword_x - 1, sword_bot - 1, sword_x + 1, sword_bot - 1, CELL_HIGHLIGHT)


def _add_staff(g: Grid, size: int) -> None:
    cx = size // 2
    body_w = max(2, size // 7)
    staff_x = max(1, cx - body_w - max(2, size // 12))
    staff_top = max(1, size // 16)
    staff_bot = int(size * 0.85)
    fill_rect(g, staff_x, staff_top, staff_x, staff_bot, CELL_ACCENT1)
    fill_circle(g, staff_x, staff_top, max(1, size // 24), CELL_ACCENT2)


def _add_shield(g: Grid, size: int) -> None:
    cx = size // 2
    body_w = max(2, size // 7)
    sx = max(1, cx - body_w - max(2, size // 10))
    sy = int(size * 0.42)
    fill_circle(g, sx, sy, max(2, size // 12), CELL_ACCENT1)


def _add_crown(g: Grid, size: int) -> None:
    cx = size // 2
    head_top = max(1, size // 8)
    base_y = max(0, head_top - 1)
    top_y = max(0, head_top - max(2, size // 12))
    fill_rect(g, cx - size // 7, base_y, cx + size // 7, base_y, CELL_ACCENT1)
    for dx in (-size // 7, 0, size // 7):
        fill_triangle(
            g,
            [(cx + dx - 1, base_y), (cx + dx + 1, base_y), (cx + dx, top_y)],
            CELL_ACCENT1,
        )


def _add_halo(g: Grid, size: int) -> None:
    cx = size // 2
    head_top = max(1, size // 8)
    halo_y = max(0, head_top - max(2, size // 16))
    halo_rx = size // 6
    halo_ry = max(1, size // 24)
    for angle in range(0, 360, 6):
        rad = math.radians(angle)
        x = int(cx + halo_rx * math.cos(rad))
        y = int(halo_y + halo_ry * math.sin(rad))
        if 0 <= x < size and 0 <= y < size and g[y][x] == CELL_TRANSPARENT:
            g[y][x] = CELL_ACCENT1


def _add_eyes(g: Grid, size: int, template_name: str) -> None:
    if template_name == "humanoid":
        cx = size // 2
        head_r = max(2, size // 7)
        head_cy = size // 8 + head_r
        eye_off = max(1, size // 14)
        eye_r = max(1, size // 32)
        fill_circle(g, cx - eye_off, head_cy, eye_r, CELL_ACCENT2)
        fill_circle(g, cx + eye_off, head_cy, eye_r, CELL_ACCENT2)
    elif template_name == "robot":
        cx = size // 2
        head_top = size // 8
        head_h = size // 4
        eye_y = head_top + head_h // 2
        eye_off = max(1, size // 12)
        fill_circle(g, cx - eye_off, eye_y, max(1, size // 32), CELL_ACCENT2)
        fill_circle(g, cx + eye_off, eye_y, max(1, size // 32), CELL_ACCENT2)
    elif template_name == "dragon":
        head_cx = max(size // 6, 4)
        head_cy = int(size * 0.42)
        fill_circle(g, head_cx + 1, head_cy - 1, max(1, size // 40), CELL_ACCENT2)
    elif template_name == "blob":
        cx = size // 2
        cy = int(size * 0.55)
        fill_circle(g, cx - max(1, size // 12), cy - 1, max(1, size // 32), CELL_ACCENT2)
        fill_circle(g, cx + max(1, size // 12), cy - 1, max(1, size // 32), CELL_ACCENT2)


# --- Render -------------------------------------------------------------------


def _cell_color(cell: int, palette: Sequence[Tuple[int, int, int]]) -> RGBA:
    if cell == CELL_TRANSPARENT:
        return (0, 0, 0, 0)
    if cell == CELL_OUTLINE:
        r, g, b = palette[0]
        return (r // 3, g // 3, b // 3, 255)
    if cell == CELL_SHADOW:
        return (*palette[0], 255)
    if cell == CELL_BODY:
        return (*palette[2], 255)
    if cell == CELL_HIGHLIGHT:
        return (*palette[3], 255)
    if cell == CELL_ACCENT1:
        return (*palettes.ACCENT_GOLD, 255)
    if cell == CELL_ACCENT2:
        return (*palettes.ACCENT_RED, 255)
    return (0, 0, 0, 0)


def _upscale(grid: Grid, native: int, target_w: int, target_h: int, palette_name: str) -> List[RGBA]:
    palette = palettes.PALETTES[palette_name]
    pixels: List[RGBA] = [(0, 0, 0, 0)] * (target_w * target_h)
    for y in range(target_h):
        ny = min(native - 1, y * native // target_h)
        row = grid[ny]
        for x in range(target_w):
            nx = min(native - 1, x * native // target_w)
            pixels[y * target_w + x] = _cell_color(row[nx], palette)
    return pixels


def generate(
    prompt: str,
    width: int = 128,
    height: int = 128,
    seed: Optional[int] = None,
) -> Tuple[List[RGBA], Dict[str, object]]:
    """Generate an RGBA pixel buffer from a text prompt.

    Returns ``(pixels, parsed_params)``. ``pixels`` is a flat list of (r,g,b,a).
    """
    rng = random.Random(seed)
    params = parse_prompt(prompt)

    # Choose native sprite resolution. 32 px scales nicely up to 128 (4x).
    native = 32
    if max(width, height) >= 256:
        native = 48

    template_fn = templates.TEMPLATES[params["template"]]  # type: ignore[index]
    grid = template_fn(native, rng)

    feature_renderers = {
        "horns": lambda g: _add_horns(g, native),
        "wings": lambda g: _add_wings(g, native),
        "hat": lambda g: _add_hat(g, native),
        "sword": lambda g: _add_sword(g, native),
        "staff": lambda g: _add_staff(g, native),
        "shield": lambda g: _add_shield(g, native),
        "crown": lambda g: _add_crown(g, native),
        "halo": lambda g: _add_halo(g, native),
    }
    deferred_eyes = "eyes" in params["features"]  # type: ignore[operator]
    for feat in params["features"]:  # type: ignore[union-attr]
        if feat == "eyes":
            continue
        renderer = feature_renderers.get(feat)
        if renderer:
            renderer(grid)

    add_shading(grid)
    add_outline(grid)

    if deferred_eyes:
        # Eyes go on top of shading so they stay bright.
        _add_eyes(grid, native, params["template"])  # type: ignore[arg-type]

    pixels = _upscale(grid, native, width, height, params["palette"])  # type: ignore[arg-type]
    return pixels, params
