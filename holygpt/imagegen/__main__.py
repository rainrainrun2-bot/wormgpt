"""CLI for HolyGPT image generators.

Usage examples:
  python -m holygpt.imagegen wolfram --rule 30 --width 257 --height 128 -o rule30.png
  python -m holygpt.imagegen life --width 128 --height 128 --steps 60 -o life.png
  python -m holygpt.imagegen walk --width 256 --height 256 --steps 80000 -o walk.png
  python -m holygpt.imagegen noise --width 256 --height 256 --octaves 5 -o noise.png
  python -m holygpt.imagegen text2img "blue dragon with wings" -o dragon.png
"""

from __future__ import annotations

import argparse
import sys

from . import automata, noise as noise_mod, png, text2img


def _add_size(p: argparse.ArgumentParser, default_w: int, default_h: int) -> None:
    p.add_argument("--width", type=int, default=default_w)
    p.add_argument("--height", type=int, default=default_h)
    p.add_argument("-o", "--out", required=True, help="output PNG path")
    p.add_argument("--seed", type=int, default=None)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="holygpt.imagegen")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_wolf = sub.add_parser("wolfram", help="Wolfram 1D elementary CA")
    p_wolf.add_argument("--rule", type=int, default=30)
    _add_size(p_wolf, 257, 128)

    p_life = sub.add_parser("life", help="Conway's Game of Life snapshot")
    p_life.add_argument("--steps", type=int, default=60)
    p_life.add_argument("--density", type=float, default=0.3)
    _add_size(p_life, 128, 128)

    p_walk = sub.add_parser("walk", help="Random walk trace")
    p_walk.add_argument("--steps", type=int, default=80_000)
    _add_size(p_walk, 256, 256)

    p_noise = sub.add_parser("noise", help="Grayscale value noise")
    p_noise.add_argument("--octaves", type=int, default=4)
    p_noise.add_argument("--base-lattice", type=int, default=4)
    p_noise.add_argument("--persistence", type=float, default=0.5)
    _add_size(p_noise, 256, 256)

    p_t2i = sub.add_parser(
        "text2img",
        help="Procedural sprite from a text prompt (RGBA PNG)",
    )
    p_t2i.add_argument("prompt", help='e.g. "blue dragon with red eyes"')
    _add_size(p_t2i, 128, 128)

    args = parser.parse_args(argv)

    if args.cmd == "wolfram":
        bits = automata.wolfram_1d(args.rule, args.width, args.height)
        png.write_binary_png(args.out, bits, args.width, args.height)
    elif args.cmd == "life":
        bits = automata.game_of_life(
            args.width, args.height, args.steps, args.density, args.seed
        )
        png.write_binary_png(args.out, bits, args.width, args.height)
    elif args.cmd == "walk":
        bits = automata.random_walk(args.width, args.height, args.steps, args.seed)
        png.write_binary_png(args.out, bits, args.width, args.height)
    elif args.cmd == "noise":
        pixels = noise_mod.value_noise(
            args.width,
            args.height,
            args.octaves,
            args.base_lattice,
            args.persistence,
            args.seed,
        )
        png.write_grayscale_png(args.out, pixels, args.width, args.height)
    elif args.cmd == "text2img":
        pixels, params = text2img.generate(
            args.prompt, args.width, args.height, args.seed
        )
        png.write_rgba_png(args.out, pixels, args.width, args.height)
        print(
            f"  prompt: {args.prompt!r}\n"
            f"  parsed: template={params['template']}, "
            f"palette={params['palette']}, features={params['features']}",
            file=sys.stderr,
        )
    else:  # pragma: no cover
        parser.error(f"unknown command {args.cmd!r}")

    print(f"wrote {args.out} ({args.width}x{args.height})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
