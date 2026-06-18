"""Small SERA-style Ethiopic transliteration helper for Amharic course data."""

from __future__ import annotations

import re


VOWELS = ("e", "u", "i", "a", "E", "", "o")
SERIES = {
    "ሀ": "h",
    "ለ": "l",
    "ሐ": "H",
    "መ": "m",
    "ሠ": "S",
    "ረ": "r",
    "ሰ": "s",
    "ሸ": "sh",
    "ቀ": "q",
    "በ": "b",
    "ቨ": "v",
    "ተ": "t",
    "ቸ": "ch",
    "ኀ": "h",
    "ነ": "n",
    "ኘ": "ny",
    "አ": "",
    "ከ": "k",
    "ኸ": "x",
    "ወ": "w",
    "ዐ": "'",
    "ዘ": "z",
    "ዠ": "zh",
    "የ": "y",
    "ደ": "d",
    "ጀ": "j",
    "ገ": "g",
    "ጠ": "T",
    "ጨ": "ch'",
    "ጰ": "P",
    "ጸ": "ts",
    "ፀ": "Ts",
    "ፈ": "f",
    "ፐ": "p",
}

EXTRA = {
    "ቈ": "qwe",
    "ቊ": "qwi",
    "ቋ": "qwa",
    "ቌ": "qwe",
    "ቍ": "qwe",
    "ቧ": "bwa",
    "ኈ": "hwe",
    "ኊ": "hwi",
    "ኋ": "hwa",
    "ኌ": "hwe",
    "ኍ": "hwe",
    "ኳ": "kwa",
    "ዃ": "xwa",
    "ዟ": "zhwa",
    "ጓ": "gwa",
    "ጧ": "Twa",
    "ጯ": "chwa",
    "ጷ": "Pwa",
    "ጿ": "tswa",
    "ፏ": "fwa",
    "ፗ": "pwa",
    "ፘ": "rya",
    "ፙ": "mya",
    "ፚ": "fya",
}

TRANSLITERATION = dict(EXTRA)
for base, consonant in SERIES.items():
    start = ord(base)
    for offset, vowel in enumerate(VOWELS):
        char = chr(start + offset)
        if consonant:
            value = f"{consonant}{vowel}"
        else:
            value = vowel or "e"
        TRANSLITERATION[char] = value

PUNCTUATION = {
    "።": ".",
    "፣": ",",
    "፤": ";",
    "፥": ":",
    "፦": ":",
    "፧": "?",
    "?": "?",
    ".": ".",
    ",": ",",
    ";": ";",
    ":": ":",
    "!": "!",
}


def romanize(text: str) -> str:
    parts: list[str] = []
    for char in text:
        if char.isspace():
            parts.append(" ")
        elif char in TRANSLITERATION:
            parts.append(TRANSLITERATION[char])
        elif char in PUNCTUATION:
            parts.append(PUNCTUATION[char])
        else:
            parts.append(char)

    value = "".join(parts)
    value = re.sub(r"\s+", " ", value).strip()
    return value
