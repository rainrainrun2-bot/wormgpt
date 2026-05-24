"""Binary image generators based on cellular automata and random walks.

These are the most "from scratch" generators you can write: every output
pixel is computed by a deterministic (or pseudo-random) local rule.
"""

from __future__ import annotations

import random
from typing import List, Optional


# --- Wolfram 1D elementary cellular automaton --------------------------------


def wolfram_1d(
    rule: int,
    width: int = 256,
    height: int = 128,
    seed_position: Optional[int] = None,
) -> List[int]:
    """Generate a binary image from a Wolfram elementary CA.

    Famous rules:
      - 30  -> chaotic noise
      - 90  -> Sierpinski triangle
      - 110 -> Turing-complete, complex structure
      - 184 -> traffic flow

    Returns a flat list of 0/1 values (length ``width * height``), top-down.
    """
    if not 0 <= rule <= 255:
        raise ValueError("rule must be 0..255")
    row = [0] * width
    row[seed_position if seed_position is not None else width // 2] = 1
    out: List[int] = list(row)
    for _ in range(height - 1):
        new_row = [0] * width
        for i in range(width):
            left = row[i - 1] if i > 0 else 0
            center = row[i]
            right = row[i + 1] if i < width - 1 else 0
            pattern = (left << 2) | (center << 1) | right
            new_row[i] = (rule >> pattern) & 1
        out.extend(new_row)
        row = new_row
    return out


# --- Conway's Game of Life ----------------------------------------------------


def game_of_life(
    width: int = 128,
    height: int = 128,
    steps: int = 100,
    density: float = 0.3,
    seed: Optional[int] = None,
) -> List[int]:
    """Run Conway's Game of Life and return the final-frame binary image.

    ``density`` is the initial fraction of live cells.
    """
    if not 0.0 <= density <= 1.0:
        raise ValueError("density must be in [0, 1]")
    rng = random.Random(seed)
    grid = [1 if rng.random() < density else 0 for _ in range(width * height)]

    def at(x: int, y: int) -> int:
        if 0 <= x < width and 0 <= y < height:
            return grid[y * width + x]
        return 0

    for _ in range(steps):
        nxt = [0] * (width * height)
        for y in range(height):
            for x in range(width):
                n = (
                    at(x - 1, y - 1) + at(x, y - 1) + at(x + 1, y - 1)
                    + at(x - 1, y)                  + at(x + 1, y)
                    + at(x - 1, y + 1) + at(x, y + 1) + at(x + 1, y + 1)
                )
                alive = grid[y * width + x]
                if alive and n in (2, 3):
                    nxt[y * width + x] = 1
                elif not alive and n == 3:
                    nxt[y * width + x] = 1
        grid = nxt
    return grid


# --- Random walk --------------------------------------------------------------


def random_walk(
    width: int = 256,
    height: int = 256,
    steps: int = 50_000,
    seed: Optional[int] = None,
) -> List[int]:
    """A drunkard's walk: start in the center, step to a random neighbor each
    iteration, mark every visited pixel. Produces organic dendritic shapes.
    """
    rng = random.Random(seed)
    grid = [0] * (width * height)
    x, y = width // 2, height // 2
    grid[y * width + x] = 1
    for _ in range(steps):
        dx, dy = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
        x = max(0, min(width - 1, x + dx))
        y = max(0, min(height - 1, y + dy))
        grid[y * width + x] = 1
    return grid
