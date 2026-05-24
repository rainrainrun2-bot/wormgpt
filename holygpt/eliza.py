"""ELIZA-style pattern matcher.

Maps user inputs to responses using regex patterns and pronoun "reflection"
(e.g. swapping "I am" for "you are"). This is the same trick Joseph Weizenbaum
used in 1966; it produces surprisingly conversational replies with zero ML.
"""

from __future__ import annotations

import random
import re
from typing import List, Tuple

# Words to swap when echoing the user's phrasing back at them.
REFLECTIONS = {
    "i": "you",
    "me": "you",
    "my": "your",
    "mine": "yours",
    "am": "are",
    "i'm": "you are",
    "i am": "you are",
    "you": "i",
    "your": "my",
    "yours": "mine",
    "you are": "i am",
    "you're": "i am",
    "are": "am",
    "was": "were",
    "were": "was",
}

# Each entry is (regex, [response templates]). {0}, {1}, ... refer to the
# reflected capture groups from the regex.
PATTERNS: List[Tuple[str, List[str]]] = [
    (
        r"i need (.+)",
        [
            "Why do you need {0}?",
            "Would it really help to get {0}?",
            "What would having {0} change for you?",
        ],
    ),
    (
        r"why don'?t you (.+)\??",
        [
            "Do you really think I don't {0}?",
            "Perhaps eventually I will {0}.",
            "Do you really want me to {0}?",
        ],
    ),
    (
        r"why can'?t i (.+)\??",
        [
            "Do you think you should be able to {0}?",
            "What would it mean if you could {0}?",
            "What is stopping you from {0}?",
        ],
    ),
    (
        r"i can'?t (.+)",
        [
            "How do you know you can't {0}?",
            "What would it take for you to {0}?",
            "Have you really tried to {0}?",
        ],
    ),
    (
        r"i am (.+)",
        [
            "How long have you been {0}?",
            "Why do you say you are {0}?",
            "How does being {0} make you feel?",
        ],
    ),
    (
        r"i'?m (.+)",
        [
            "How does being {0} make you feel?",
            "Why do you tell me you're {0}?",
            "Are you {0} often?",
        ],
    ),
    (
        r"are you (.+)\??",
        [
            "Why does it matter whether I am {0}?",
            "Would you prefer if I were not {0}?",
            "Maybe I am {0} in your view.",
        ],
    ),
    (
        r"what (.+)\??",
        [
            "Why do you ask?",
            "What do you think?",
            "What comes to mind when you ask that?",
        ],
    ),
    (
        r"how (.+)\??",
        [
            "How do you suppose?",
            "What answer would please you most?",
            "What does this question mean to you?",
        ],
    ),
    (
        r"because (.+)",
        [
            "Is that the real reason?",
            "What other reasons come to mind?",
            "Does that reason apply to anything else?",
        ],
    ),
    (
        r"(.+)\?$",
        [
            "Why do you ask that?",
            "What do you think?",
            "How would an answer to that help you?",
        ],
    ),
    (
        r"sorry (.*)",
        [
            "No need to apologise.",
            "Apologies aren't necessary.",
            "What feelings do you have when you apologise?",
        ],
    ),
    (
        r"hello(.*)",
        [
            "Hello. How are you feeling today?",
            "Hi there. What's on your mind?",
            "Hello. How can I help?",
        ],
    ),
    (
        r"i think (.+)",
        [
            "Do you doubt {0}?",
            "Do you really think so?",
            "But you're not sure {0}?",
        ],
    ),
    (
        r"(.*) friend(.*)",
        [
            "Tell me more about your friends.",
            "Why do you bring up the topic of friends?",
            "Do your friends worry you?",
        ],
    ),
    (
        r"yes",
        [
            "You seem quite sure.",
            "I see.",
            "Go on.",
        ],
    ),
    (
        r"no",
        [
            "Why not?",
            "Are you sure?",
            "Why no?",
        ],
    ),
]


def _reflect(fragment: str) -> str:
    """Swap first/second-person words so a quote can be echoed naturally."""
    tokens = re.findall(r"\w+'?\w*|[^\w\s]", fragment.lower())
    reflected = [REFLECTIONS.get(tok, tok) for tok in tokens]
    out = ""
    for tok in reflected:
        if re.match(r"[^\w\s]", tok):
            out = out.rstrip() + tok + " "
        else:
            out += tok + " "
    return out.strip()


class Eliza:
    """Tiny rule-based responder."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self._compiled = [
            (re.compile(pat, re.IGNORECASE), responses)
            for pat, responses in PATTERNS
        ]

    def respond(self, text: str) -> str | None:
        """Return a response for ``text`` or ``None`` if no pattern matches."""
        cleaned = text.strip().rstrip(".!?")
        for pattern, responses in self._compiled:
            match = pattern.match(cleaned)
            if match:
                template = self.rng.choice(responses)
                groups = [_reflect(g) for g in match.groups()]
                try:
                    return template.format(*groups)
                except IndexError:
                    return template
        return None
