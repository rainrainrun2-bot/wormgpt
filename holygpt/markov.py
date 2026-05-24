"""Word-level Markov chain text generator.

Given a corpus, builds a table of "what word(s) tend to follow this state?"
and samples from it to generate new sentences. Order = how many previous
words form the state (2 is usually a good balance of coherence and novelty).
"""

from __future__ import annotations

import random
import re
from collections import defaultdict
from typing import Dict, List, Sequence, Tuple

WORD_RE = re.compile(r"[A-Za-z']+|[.!?]")
SENTENCE_END = {".", "!", "?"}


def tokenize(text: str) -> List[str]:
    """Split text into words and sentence-ending punctuation."""
    return WORD_RE.findall(text)


class MarkovChain:
    """Simple n-gram Markov chain over tokens."""

    def __init__(self, order: int = 2, rng: random.Random | None = None) -> None:
        if order < 1:
            raise ValueError("order must be >= 1")
        self.order = order
        self.rng = rng or random.Random()
        self.table: Dict[Tuple[str, ...], List[str]] = defaultdict(list)
        self.starts: List[Tuple[str, ...]] = []

    def train(self, text: str) -> None:
        """Add ``text`` to the model. Can be called many times."""
        tokens = tokenize(text)
        if len(tokens) <= self.order:
            return
        # Track sentence-start states so generated text starts naturally.
        is_start = True
        for i in range(len(tokens) - self.order):
            state = tuple(tokens[i : i + self.order])
            nxt = tokens[i + self.order]
            self.table[state].append(nxt)
            if is_start:
                self.starts.append(state)
                is_start = False
            if nxt in SENTENCE_END:
                is_start = True

    def _pick_start(self, seed_tokens: Sequence[str] | None) -> Tuple[str, ...]:
        """Choose an initial state, biased toward any seed words the user gave."""
        if seed_tokens:
            lowered = {t.lower() for t in seed_tokens}
            candidates = [
                state
                for state in self.table
                if any(tok.lower() in lowered for tok in state)
            ]
            if candidates:
                return self.rng.choice(candidates)
        if self.starts:
            return self.rng.choice(self.starts)
        if self.table:
            return self.rng.choice(list(self.table.keys()))
        raise RuntimeError("Markov chain has no training data")

    def generate(
        self,
        max_tokens: int = 40,
        seed: Sequence[str] | None = None,
    ) -> str:
        """Generate up to ``max_tokens`` tokens, optionally biased by ``seed``."""
        if not self.table:
            return ""
        state = self._pick_start(seed)
        output = list(state)
        for _ in range(max_tokens - self.order):
            choices = self.table.get(state)
            if not choices:
                break
            nxt = self.rng.choice(choices)
            output.append(nxt)
            if nxt in SENTENCE_END and len(output) >= 6:
                break
            state = tuple(output[-self.order :])
        return self._detokenize(output)

    @staticmethod
    def _detokenize(tokens: List[str]) -> str:
        out = ""
        for tok in tokens:
            if tok in SENTENCE_END:
                out = out.rstrip() + tok + " "
            else:
                out += tok + " "
        out = out.strip()
        return out[:1].upper() + out[1:] if out else out
