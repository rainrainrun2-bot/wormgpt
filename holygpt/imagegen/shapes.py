"""Drawing primitives for procedural sprite templates.

Operate on a 2D grid of integer "depth" codes (see CELL_* constants).
Each helper writes ``value`` into the grid wherever a shape covers a cell.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

# Cell codes used in the depth grid.
CELL_TRANSPARENT = 0
CELL_OUTLINE = 1
CELL_SHADOW = 2
CELL_BODY = 3
CELL_HIGHLIGHT = 4
CELL_ACCENT1 = 5  # warm/glow accent (gold)
CELL_ACCENT2 = 6  # eyes / danger accent (red)

Grid = List[List[int]]


def make_grid(size: int, fill: int = CELL_TRANSPARENT) -> Grid:
    return [[fill] * size for _ in range(size)]


def fill_circle(grid: Grid, cx: int, cy: int, r: int, value: int) -> None:
    size = len(grid)
    r2 = r * r
    for y in range(max(0, cy - r), min(size, cy + r + 1)):
        for x in range(max(0, cx - r), min(size, cx + r + 1)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r2:
                grid[y][x] = value


def fill_ellipse(grid: Grid, cx: int, cy: int, rx: int, ry: int, value: int) -> None:
    if rx <= 0 or ry <= 0:
        return
    size = len(grid)
    for y in range(max(0, cy - ry), min(size, cy + ry + 1)):
        for x in range(max(0, cx - rx), min(size, cx + rx + 1)):
            dx = (x - cx) / rx
            dy = (y - cy) / ry
            if dx * dx + dy * dy <= 1.0:
                grid[y][x] = value


def fill_rect(grid: Grid, x0: int, y0: int, x1: int, y1: int, value: int) -> None:
    size = len(grid)
    for y in range(max(0, y0), min(size, y1 + 1)):
        for x in range(max(0, x0), min(size, x1 + 1)):
            grid[y][x] = value


def fill_triangle(grid: Grid, points: Sequence[Tuple[int, int]], value: int) -> None:
    size = len(grid)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0 = max(0, min(xs))
    x1 = min(size - 1, max(xs))
    y0 = max(0, min(ys))
    y1 = min(size - 1, max(ys))

    p0, p1, p2 = points

    def edge(ax, ay, bx, by, cx, cy) -> int:
        return (cx - ax) * (by - ay) - (cy - ay) * (bx - ax)

    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d0 = edge(p0[0], p0[1], p1[0], p1[1], x, y)
            d1 = edge(p1[0], p1[1], p2[0], p2[1], x, y)
            d2 = edge(p2[0], p2[1], p0[0], p0[1], x, y)
            if (d0 >= 0 and d1 >= 0 and d2 >= 0) or (d0 <= 0 and d1 <= 0 and d2 <= 0):
                grid[y][x] = value


def add_shading(grid: Grid) -> None:
    """Convert solid body cells to highlight (top/left edge) or shadow (bottom)."""
    size = len(grid)
    new_grid = [row[:] for row in grid]
    for y in range(size):
        for x in range(size):
            if grid[y][x] != CELL_BODY:
                continue
            top = grid[y - 1][x] if y > 0 else CELL_TRANSPARENT
            left = grid[y][x - 1] if x > 0 else CELL_TRANSPARENT
            bot = grid[y + 1][x] if y < size - 1 else CELL_TRANSPARENT
            if top == CELL_TRANSPARENT or left == CELL_TRANSPARENT:
                new_grid[y][x] = CELL_HIGHLIGHT
            elif bot == CELL_TRANSPARENT:
                new_grid[y][x] = CELL_SHADOW
    for y in range(size):
        grid[y][:] = new_grid[y]


def add_outline(grid: Grid) -> None:
    """Surround any non-transparent region with a 1-pixel CELL_OUTLINE border."""
    size = len(grid)
    to_outline: List[Tuple[int, int]] = []
    for y in range(size):
        for x in range(size):
            if grid[y][x] != CELL_TRANSPARENT:
                continue
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < size and 0 <= nx < size:
                    if grid[ny][nx] not in (CELL_TRANSPARENT, CELL_OUTLINE):
                        to_outline.append((y, x))
                        break
    for y, x in to_outline:
        grid[y][x] = CELL_OUTLINE
