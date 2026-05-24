"""HolyGPT orchestration: combines intents, ELIZA, and Markov layers."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Optional

from . import intents
from .eliza import Eliza
from .markov import MarkovChain, tokenize

_DEFAULT_CORPUS = Path(__file__).with_name("corpus.txt")


class HolyGPT:
    """A tiny offline assistant.

    Order of resolution for each user message:

    1. Intent handlers (math, time, date, identity, help) -> deterministic.
    2. ELIZA pattern match -> conversational reflection.
    3. Markov chain -> free-form fallback, biased by user's words.
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        markov_order: int = 2,
        load_default_corpus: bool = True,
    ) -> None:
        self.rng = random.Random(seed)
        self.eliza = Eliza(rng=self.rng)
        self.markov = MarkovChain(order=markov_order, rng=self.rng)
        if load_default_corpus and _DEFAULT_CORPUS.exists():
            self.train_from_file(_DEFAULT_CORPUS)

    # -- training ----------------------------------------------------------

    def train(self, text: str) -> None:
        self.markov.train(text)

    def train_from_file(self, path: str | Path) -> int:
        """Train on a UTF-8 text file. Returns its character length."""
        data = Path(path).read_text(encoding="utf-8", errors="ignore")
        self.markov.train(data)
        return len(data)

    # -- inference ---------------------------------------------------------

    def reply(self, message: str) -> str:
        message = message.strip()
        if not message:
            return "..."

        deterministic = intents.resolve(message)
        if deterministic is not None:
            return deterministic

        eliza_reply = self.eliza.respond(message)
        if eliza_reply is not None:
            return eliza_reply

        seed_words = [t for t in tokenize(message) if t.isalpha()]
        generated = self.markov.generate(max_tokens=30, seed=seed_words)
        if generated:
            return generated

        return "Tell me more."
