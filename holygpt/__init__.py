"""HolyGPT: a pure-Python local assistant.

No external APIs. No large language models. Just classical AI techniques:
- intent handlers (math, time, date, greetings)
- ELIZA-style pattern matching for conversation
- Markov-chain text generation for free-form replies
"""

from .bot import HolyGPT

__all__ = ["HolyGPT"]
__version__ = "0.1.0"
