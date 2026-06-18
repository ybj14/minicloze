"""ASCII Georgian transliteration helper for local course data.

The mapping follows common Georgian romanization values. It uses apostrophes
for ejective stops and affricates while remaining ASCII so learners can type
pronunciation helpers without special characters.
"""

from __future__ import annotations

import re


LETTERS = {
    "ა": "a",
    "ბ": "b",
    "გ": "g",
    "დ": "d",
    "ე": "e",
    "ვ": "v",
    "ზ": "z",
    "თ": "t",
    "ი": "i",
    "კ": "k'",
    "ლ": "l",
    "მ": "m",
    "ნ": "n",
    "ო": "o",
    "პ": "p'",
    "ჟ": "zh",
    "რ": "r",
    "ს": "s",
    "ტ": "t'",
    "უ": "u",
    "ფ": "p",
    "ქ": "k",
    "ღ": "gh",
    "ყ": "q'",
    "შ": "sh",
    "ჩ": "ch",
    "ც": "ts",
    "ძ": "dz",
    "წ": "ts'",
    "ჭ": "ch'",
    "ხ": "kh",
    "ჯ": "j",
    "ჰ": "h",
}

PUNCTUATION = {
    ".": ".",
    "?": "?",
    "!": "!",
    ",": ",",
    ";": ";",
    ":": ":",
    "(": "(",
    ")": ")",
}


def romanize(text: str) -> str:
    parts: list[str] = []
    for char in text.lower():
        if char.isspace():
            parts.append(" ")
        elif char in LETTERS:
            parts.append(LETTERS[char])
        elif char in PUNCTUATION:
            parts.append(PUNCTUATION[char])
        else:
            parts.append(char)

    return re.sub(r"\s+", " ", "".join(parts)).strip()
