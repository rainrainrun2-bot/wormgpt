# HolyGPT

A small offline assistant written in pure Python.

- No external APIs.
- No large language models.
- No third-party dependencies (standard library only).

It combines three classical AI techniques:

1. **Intent handlers** — math, time, date, identity, help. Deterministic.
2. **ELIZA-style pattern matching** — regex + pronoun reflection for chat.
3. **Markov-chain text generator** — trained on a small built-in corpus,
   extendable with any UTF-8 text file you point it at.

## Run it

```bash
python -m holygpt
```

You'll get a prompt:

```
HolyGPT ready. Type /help for commands, /quit to exit.
you> what time is it?
holy> It's 14:32.
you> 12 * 7
holy> 84
you> i am tired
holy> How long have you been tired?
you> tell me about the stars
holy> The night is quiet, the stars are old, and the mind that wonders...
```

### Train on your own text

```bash
python -m holygpt --train path/to/book.txt --train path/to/notes.txt
```

Or at runtime:

```
you> /train path/to/book.txt
[trained on path/to/book.txt (102345 chars)]
```

## Use as a library

```python
from holygpt import HolyGPT

bot = HolyGPT(seed=42)
bot.train("Any string of text you want to add to the Markov chain.")
print(bot.reply("hello"))
```

## Project layout

```
holygpt/
  __init__.py    # public API
  __main__.py    # CLI entry point (python -m holygpt)
  bot.py         # HolyGPT class, ties the layers together
  intents.py     # math / time / date / identity handlers
  eliza.py       # regex pattern matcher with pronoun reflection
  markov.py      # n-gram word-level Markov chain
  corpus.txt     # small default training corpus
```

## How the layers fit together

For every user message, `HolyGPT.reply` tries:

1. `intents.resolve(message)` — if it looks like math or a time/date question,
   answer it directly.
2. `Eliza.respond(message)` — if it matches a conversational pattern,
   reflect it back.
3. `MarkovChain.generate(seed=words_from_message)` — otherwise, generate a
   sentence biased toward words the user just used.

Each layer is independent and replaceable.
