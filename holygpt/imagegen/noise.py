"""Grayscale value-noise generator.

Real Perlin noise involves gradient vectors; "value noise" is the toy
cousin: random values at lattice points, smoothly interpolated. Summing
several octaves at increasing frequencies produces fractal/cloud-like
images. Pure stdlib, no numpy.
"""

from __future__ import annotations

import random
from typing import List, Optional


def _smoothstep(t: float) -> float:
    # Hermite smoothing: 3t^2 - 2t^3, gives C1-continuous interpolation.
    return t * t * (3 - 2 * t)


def _lattice(rng: random.Random, lw: int, lh: int) -> List[float]:
    return [rng.random() for _ in range(lw * lh)]


def _sample_octave(
    lattice: List[float],
    lw: int,
    lh: int,
    width: int,
    height: int,
) -> List[float]:
    """Bilinearly sample a ``lw x lh`` lattice over a ``width x height`` image."""
    out = [0.0] * (width * height)
    sx = (lw - 1) / max(width - 1, 1)
    sy = (lh - 1) / max(height - 1, 1)
    for y in range(height):
        fy = y * sy
        y0 = int(fy)
        y1 = min(y0 + 1, lh - 1)
        ty = _smoothstep(fy - y0)
        for x in range(width):
            fx = x * sx
            x0 = int(fx)
            x1 = min(x0 + 1, lw - 1)
            tx = _smoothstep(fx - x0)
            v00 = lattice[y0 * lw + x0]
            v10 = lattice[y0 * lw + x1]
            v01 = lattice[y1 * lw + x0]
            v11 = lattice[y1 * lw + x1]
            top = v00 * (1 - tx) + v10 * tx
            bot = v01 * (1 - tx) + v11 * tx
            out[y * width + x] = top * (1 - ty) + bot * ty
    return out


def value_noise(
    width: int = 256,
    height: int = 256,
    octaves: int = 4,
    base_lattice: int = 4,
    persistence: float = 0.5,
    seed: Optional[int] = None,
) -> List[int]:
    """Generate a grayscale value-noise image.

    Each octave doubles the lattice resolution and halves its amplitude
    (controlled by ``persistence``). Returns flat 0..255 grayscale pixels.
    """
    if octaves < 1:
        raise ValueError("octaves must be >= 1")
    rng = random.Random(seed)

    accum = [0.0] * (width * height)
    amplitude = 1.0
    total_amp = 0.0
    lw = lh = base_lattice
    for _ in range(octaves):
        lattice = _lattice(rng, lw, lh)
        sampled = _sample_octave(lattice, lw, lh, width, height)
        for i, v in enumerate(sampled):
            accum[i] += v * amplitude
        total_amp += amplitude
        amplitude *= persistence
        lw = lw * 2 - 1  # finer lattice next octave
        lh = lh * 2 - 1

    # Normalize to 0..255.
    if total_amp == 0:
        return [0] * (width * height)
    pixels = [int(max(0.0, min(1.0, v / total_amp)) * 255) for v in accum]
    return pixels
