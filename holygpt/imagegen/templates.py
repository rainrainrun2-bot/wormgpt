"""Procedural body templates for sprite generation.

Each template function returns a ``size x size`` depth grid filled with
CELL_BODY where the silhouette lives. Shading and outline are applied later.
"""

from __future__ import annotations

import random
from typing import Callable, Dict

from .shapes import (
    CELL_BODY,
    CELL_TRANSPARENT,
    Grid,
    fill_circle,
    fill_ellipse,
    fill_rect,
    fill_triangle,
    make_grid,
)


# --- Humanoid -----------------------------------------------------------------


def humanoid(size: int, rng: random.Random) -> Grid:
    g = make_grid(size)
    cx = size // 2
    head_r = max(2, size // 7)
    head_cy = size // 8 + head_r
    fill_circle(g, cx, head_cy, head_r, CELL_BODY)

    body_top = head_cy + head_r + 1
    body_bot = body_top + size // 3
    body_w = max(2, size // 7)
    fill_rect(g, cx - body_w, body_top, cx + body_w, body_bot, CELL_BODY)

    arm_w = max(1, size // 16)
    arm_top = body_top + 1
    arm_bot = body_top + size // 4
    fill_rect(g, cx - body_w - arm_w - 1, arm_top, cx - body_w - 1, arm_bot, CELL_BODY)
    fill_rect(g, cx + body_w + 1, arm_top, cx + body_w + arm_w + 1, arm_bot, CELL_BODY)

    leg_w = max(1, size // 14)
    leg_top = body_bot + 1
    leg_bot = size - max(2, size // 16)
    fill_rect(g, cx - body_w + 1, leg_top, cx - body_w + leg_w, leg_bot, CELL_BODY)
    fill_rect(g, cx + body_w - leg_w, leg_top, cx + body_w - 1, leg_bot, CELL_BODY)

    return g


# --- Dragon -------------------------------------------------------------------


def dragon(size: int, rng: random.Random) -> Grid:
    g = make_grid(size)
    body_cx = size // 2
    body_cy = int(size * 0.55)
    fill_ellipse(g, body_cx, body_cy, size // 3, size // 6, CELL_BODY)

    head_cx = max(size // 6, 4)
    head_cy = int(size * 0.42)
    fill_ellipse(g, head_cx, head_cy, max(3, size // 9), max(3, size // 10), CELL_BODY)

    # Neck: connect head to body with a thick line.
    neck_w = max(2, size // 12)
    fill_rect(
        g,
        head_cx,
        head_cy - neck_w // 2,
        body_cx - size // 5,
        head_cy + neck_w,
        CELL_BODY,
    )

    # Tail: tapering on right.
    tail_len = size // 3
    for i in range(tail_len):
        tx = body_cx + size // 3 + i
        ty = body_cy + i // 3
        if 0 <= tx < size and 0 <= ty < size:
            radius = max(1, size // 12 - i // 3)
            fill_circle(g, tx, ty, radius, CELL_BODY)

    # Wings: triangles flaring above the body.
    wing_top = max(1, body_cy - size // 3)
    fill_triangle(
        g,
        [
            (body_cx - 1, body_cy - size // 12),
            (max(2, body_cx - size // 3), wing_top),
            (body_cx, wing_top),
        ],
        CELL_BODY,
    )
    fill_triangle(
        g,
        [
            (body_cx + 1, body_cy - size // 12),
            (min(size - 3, body_cx + size // 3), wing_top),
            (body_cx, wing_top),
        ],
        CELL_BODY,
    )

    # Legs.
    leg_y = body_cy + size // 6
    fill_circle(g, body_cx - size // 6, leg_y, max(1, size // 16), CELL_BODY)
    fill_circle(g, body_cx + size // 6, leg_y, max(1, size // 16), CELL_BODY)

    return g


# --- Blob ---------------------------------------------------------------------


def blob(size: int, rng: random.Random) -> Grid:
    """Organic shape via biased random walk + cellular automata smoothing."""
    g = make_grid(size)
    cx, cy = size // 2, int(size * 0.55)
    x, y = cx, cy
    steps = max(200, size * size // 2)
    radius = max(3, size // 3)
    for _ in range(steps):
        g[y][x] = CELL_BODY
        dx, dy = rng.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        if x - cx > radius:
            dx = -1
        elif cx - x > radius:
            dx = 1
        if y - cy > radius:
            dy = -1
        elif cy - y > radius:
            dy = 1
        x = max(2, min(size - 3, x + dx))
        y = max(2, min(size - 3, y + dy))

    # Cellular automata smoothing: any cell with >=5 live neighbors lives.
    for _ in range(3):
        new_g = [row[:] for row in g]
        for yy in range(1, size - 1):
            for xx in range(1, size - 1):
                count = 0
                for ddy in (-1, 0, 1):
                    for ddx in (-1, 0, 1):
                        if g[yy + ddy][xx + ddx] != CELL_TRANSPARENT:
                            count += 1
                new_g[yy][xx] = CELL_BODY if count >= 5 else CELL_TRANSPARENT
        g = new_g
    return g


# --- Robot --------------------------------------------------------------------


def robot(size: int, rng: random.Random) -> Grid:
    g = make_grid(size)
    cx = size // 2

    head_top = size // 8
    head_h = size // 4
    head_w = size // 4
    fill_rect(g, cx - head_w, head_top, cx + head_w, head_top + head_h, CELL_BODY)

    # Antenna.
    fill_rect(g, cx, max(0, head_top - size // 8), cx + 1, head_top, CELL_BODY)

    body_top = head_top + head_h + 1
    body_h = size // 3
    body_w = int(size * 0.3)
    fill_rect(g, cx - body_w, body_top, cx + body_w, body_top + body_h, CELL_BODY)

    arm_w = max(1, size // 12)
    fill_rect(
        g,
        cx - body_w - arm_w - 1,
        body_top + 1,
        cx - body_w - 1,
        body_top + body_h - 1,
        CELL_BODY,
    )
    fill_rect(
        g,
        cx + body_w + 1,
        body_top + 1,
        cx + body_w + arm_w + 1,
        body_top + body_h - 1,
        CELL_BODY,
    )

    leg_top = body_top + body_h + 1
    leg_w = max(1, size // 10)
    fill_rect(g, cx - body_w + 1, leg_top, cx - body_w + leg_w, size - 2, CELL_BODY)
    fill_rect(g, cx + body_w - leg_w, leg_top, cx + body_w - 1, size - 2, CELL_BODY)

    return g


TEMPLATES: Dict[str, Callable[[int, random.Random], Grid]] = {
    "humanoid": humanoid,
    "dragon": dragon,
    "blob": blob,
    "robot": robot,
}
