"""Minimal PNG encoder using only the standard library.

Supports two color modes:
- 1-bit grayscale (true binary images, packed 8 pixels/byte)
- 8-bit grayscale

A PNG file is just: signature + chunks. Each chunk is
length(4) + type(4) + data + CRC32(type+data).
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path
from typing import Sequence

_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def write_binary_png(
    path: str | Path,
    bits: Sequence[int],
    width: int,
    height: int,
) -> None:
    """Write a 1-bit PNG. ``bits`` is a flat sequence of 0/1 values, row-major."""
    if len(bits) != width * height:
        raise ValueError(f"expected {width * height} bits, got {len(bits)}")

    bytes_per_row = (width + 7) // 8
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter type "None" for this scanline
        row_start = y * width
        for bx in range(bytes_per_row):
            byte = 0
            base = bx * 8
            for bit in range(8):
                x = base + bit
                if x < width and bits[row_start + x]:
                    byte |= 1 << (7 - bit)
            raw.append(byte)

    # IHDR: bit_depth=1, color_type=0 (grayscale)
    ihdr = struct.pack(">IIBBBBB", width, height, 1, 0, 0, 0, 0)
    idat = zlib.compress(bytes(raw), 9)
    Path(path).write_bytes(
        _SIGNATURE + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", b"")
    )


def write_grayscale_png(
    path: str | Path,
    pixels: Sequence[int],
    width: int,
    height: int,
) -> None:
    """Write an 8-bit grayscale PNG. ``pixels`` is a flat sequence of 0..255."""
    if len(pixels) != width * height:
        raise ValueError(f"expected {width * height} pixels, got {len(pixels)}")

    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw.extend(pixels[y * width : (y + 1) * width])

    # IHDR: bit_depth=8, color_type=0 (grayscale)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    idat = zlib.compress(bytes(raw), 9)
    Path(path).write_bytes(
        _SIGNATURE + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", b"")
    )
