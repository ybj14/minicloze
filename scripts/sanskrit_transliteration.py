#!/usr/bin/env python3
"""Deterministic IAST <-> Devanagari conversion for Sanskrit course data.

IAST (International Alphabet of Sanskrit Transliteration) is the scholarly
Latin transliteration used for every Sanskrit explanation word and token.
The converter is intentionally small and dependency-free; it handles the
classical Sanskrit inventory (no Vedic accents) plus anusvāra, visarga,
avagraha, candrabindu, and the danda punctuation marks.
"""

from __future__ import annotations

import unicodedata

VIRAMA = "\u094d"

_IAST_VOWELS = [
    ("ai", "ऐ", "\u0948"),
    ("au", "औ", "\u094c"),
    ("ā", "आ", "\u093e"),
    ("ī", "ई", "\u0940"),
    ("ū", "ऊ", "\u0942"),
    ("ṝ", "ॠ", "\u0944"),
    ("ṛ", "ऋ", "\u0943"),
    ("ḹ", "ॡ", "\u0963"),
    ("ḷ", "ऌ", "\u0962"),
    ("a", "अ", ""),
    ("i", "इ", "\u093f"),
    ("u", "उ", "\u0941"),
    ("e", "ए", "\u0947"),
    ("o", "ओ", "\u094b"),
]

_IAST_CONSONANTS = [
    ("kh", "ख"), ("gh", "घ"), ("ch", "छ"), ("jh", "झ"), ("ṭh", "ठ"), ("ḍh", "ढ"),
    ("th", "थ"), ("dh", "ध"), ("ph", "फ"), ("bh", "भ"),
    ("k", "क"), ("g", "ग"), ("ṅ", "ङ"), ("c", "च"), ("j", "ज"), ("ñ", "ञ"),
    ("ṭ", "ट"), ("ḍ", "ड"), ("ṇ", "ण"), ("t", "त"), ("d", "द"), ("n", "न"),
    ("p", "प"), ("b", "ब"), ("m", "म"), ("y", "य"), ("r", "र"), ("l", "ल"),
    ("v", "व"), ("ś", "श"), ("ṣ", "ष"), ("s", "स"), ("h", "ह"), ("ḻ", "ळ"),
]

_IAST_OTHER = [
    ("ṃ", "ं"), ("ṁ", "ं"), ("ḥ", "ः"), ("m̐", "ँ"), ("'", "ऽ"), ("’", "ऽ"),
    ("||", "॥"), ("|", "।"),
]


def iast_to_devanagari(text: str) -> str:
    """Convert lower-case IAST to Devanagari."""
    text = unicodedata.normalize("NFC", text).lower()
    out: list[str] = []
    i = 0
    pending_consonant = False  # last output is a consonant without vowel sign
    while i < len(text):
        matched = False
        for latin, deva in _IAST_OTHER:
            if text.startswith(latin, i):
                if pending_consonant:
                    out.append(VIRAMA)
                    pending_consonant = False
                out.append(deva)
                i += len(latin)
                matched = True
                break
        if matched:
            continue
        for latin, deva in _IAST_CONSONANTS:
            if text.startswith(latin, i):
                # "ai"/"au" never start consonants; guard "a" + "i" handled in vowels.
                if pending_consonant:
                    out.append(VIRAMA)
                out.append(deva)
                pending_consonant = True
                i += len(latin)
                matched = True
                break
        if matched:
            continue
        for latin, independent, sign in _IAST_VOWELS:
            if text.startswith(latin, i):
                if pending_consonant:
                    out.append(sign)
                    pending_consonant = False
                else:
                    out.append(independent)
                i += len(latin)
                matched = True
                break
        if matched:
            continue
        # Any other character (space, punctuation, digits)
        if pending_consonant:
            out.append(VIRAMA)
            pending_consonant = False
        out.append(text[i])
        i += 1
    if pending_consonant:
        out.append(VIRAMA)
    return "".join(out)


_DEVA_INDEPENDENT = {deva: latin for latin, deva, _sign in _IAST_VOWELS}
_DEVA_SIGNS = {sign: latin for latin, _deva, sign in _IAST_VOWELS if sign}
_DEVA_CONSONANTS = {deva: latin for latin, deva in _IAST_CONSONANTS}
_DEVA_OTHER = {"ं": "ṃ", "ः": "ḥ", "ँ": "m̐", "ऽ": "'", "।": "|", "॥": "||"}
_DEVA_DIGITS = {chr(0x0966 + n): str(n) for n in range(10)}


def devanagari_to_iast(text: str) -> str:
    """Convert Devanagari to IAST."""
    out: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in _DEVA_CONSONANTS:
            out.append(_DEVA_CONSONANTS[ch])
            nxt = text[i + 1] if i + 1 < len(text) else ""
            if nxt == VIRAMA:
                i += 2
                continue
            if nxt in _DEVA_SIGNS:
                out.append(_DEVA_SIGNS[nxt])
                i += 2
                continue
            out.append("a")
            i += 1
            continue
        if ch in _DEVA_INDEPENDENT:
            out.append(_DEVA_INDEPENDENT[ch])
        elif ch in _DEVA_OTHER:
            out.append(_DEVA_OTHER[ch])
        elif ch in _DEVA_DIGITS:
            out.append(_DEVA_DIGITS[ch])
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def romanize(text: str) -> str:
    """Devanagari -> IAST (alias used by build scripts)."""
    return devanagari_to_iast(text)


if __name__ == "__main__":  # pragma: no cover
    import sys

    for arg in sys.argv[1:]:
        deva = iast_to_devanagari(arg)
        print(deva, devanagari_to_iast(deva))
