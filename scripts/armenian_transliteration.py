"""ASCII Armenian transliteration helper for local course data.

The mapping is intentionally close to common WT:HY/ISO-style values, while
remaining ASCII so learners can type answers without special characters.
"""

from __future__ import annotations

import re


DIGRAPHS = {
    "ու": "u",
}

LETTERS = {
    "ա": "a",
    "բ": "b",
    "գ": "g",
    "դ": "d",
    "ե": "e",
    "զ": "z",
    "է": "e",
    "ը": "y",
    "թ": "t",
    "ժ": "zh",
    "ի": "i",
    "լ": "l",
    "խ": "kh",
    "ծ": "ts",
    "կ": "k",
    "հ": "h",
    "ձ": "dz",
    "ղ": "gh",
    "ճ": "ch",
    "մ": "m",
    "յ": "y",
    "ն": "n",
    "շ": "sh",
    "ո": "o",
    "չ": "ch",
    "պ": "p",
    "ջ": "j",
    "ռ": "rr",
    "ս": "s",
    "վ": "v",
    "տ": "t",
    "ր": "r",
    "ց": "ts",
    "ւ": "v",
    "փ": "p",
    "ք": "k",
    "օ": "o",
    "ֆ": "f",
    "և": "ev",
}

PUNCTUATION = {
    "։": ".",
    "՞": "?",
    "՜": "!",
    "՛": "",
    "՝": ",",
    ",": ",",
    ".": ".",
    "?": "?",
    "!": "!",
    ";": ";",
    ":": ":",
}


def romanize(text: str) -> str:
    source = text.lower()
    parts: list[str] = []
    index = 0
    while index < len(source):
        pair = source[index : index + 2]
        if pair in DIGRAPHS:
            parts.append(DIGRAPHS[pair])
            index += 2
            continue

        char = source[index]
        if char.isspace():
            parts.append(" ")
        elif char in LETTERS:
            parts.append(LETTERS[char])
        elif char in PUNCTUATION:
            parts.append(PUNCTUATION[char])
        else:
            parts.append(char)
        index += 1

    return re.sub(r"\s+", " ", "".join(parts)).strip()
