"""HolyGPT image generation: pure-Python, no dependencies.

Generators:
- ``automata.wolfram_1d``     -> binary patterns from elementary cellular automata
- ``automata.game_of_life``   -> binary snapshot of Conway's Game of Life
- ``automata.random_walk``    -> binary trace of a drunkard's walk
- ``noise.value_noise``       -> grayscale fractal-noise image

I/O:
- ``png.write_binary_png``    -> 1-bit PNG (truly binary; tiny files)
- ``png.write_grayscale_png`` -> 8-bit grayscale PNG
"""

from . import automata, noise, png

__all__ = ["automata", "noise", "png"]
