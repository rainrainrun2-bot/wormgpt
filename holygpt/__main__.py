"""Interactive CLI for HolyGPT.

Run with:  python -m holygpt
"""

from __future__ import annotations

import argparse
import sys

from .bot import HolyGPT


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="holygpt", description="Offline AI assistant.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility.")
    parser.add_argument("--order", type=int, default=2, help="Markov chain order (default: 2).")
    parser.add_argument(
        "--train",
        action="append",
        default=[],
        metavar="PATH",
        help="Extra text file to train on. May be passed multiple times.",
    )
    args = parser.parse_args(argv)

    bot = HolyGPT(seed=args.seed, markov_order=args.order)
    for path in args.train:
        try:
            n = bot.train_from_file(path)
            print(f"[trained on {path} ({n} chars)]", file=sys.stderr)
        except OSError as exc:
            print(f"[could not read {path}: {exc}]", file=sys.stderr)

    print("HolyGPT ready. Type /help for commands, /quit to exit.")
    while True:
        try:
            user = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user:
            continue
        if user in {"/quit", "/exit"}:
            break
        if user == "/help":
            print(
                "Commands:\n"
                "  /train <path>   train on a text file\n"
                "  /quit           exit\n"
                "Otherwise, just chat."
            )
            continue
        if user.startswith("/train "):
            path = user[len("/train ") :].strip()
            try:
                n = bot.train_from_file(path)
                print(f"[trained on {path} ({n} chars)]")
            except OSError as exc:
                print(f"[could not read {path}: {exc}]")
            continue
        print(f"holy> {bot.reply(user)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
