#!/usr/bin/env python3
"""ASCII-friendly Maltese learner transliteration."""

from __future__ import annotations

_FOLD = str.maketrans(
    {
        "ċ": "c",
        "Ċ": "C",
        "ġ": "g",
        "Ġ": "G",
        "ħ": "h",
        "Ħ": "H",
        "ż": "z",
        "Ż": "Z",
        "à": "a",
        "á": "a",
        "è": "e",
        "é": "e",
        "ì": "i",
        "í": "i",
        "ò": "o",
        "ó": "o",
        "ù": "u",
        "ú": "u",
        "â": "a",
        "ê": "e",
        "î": "i",
        "ô": "o",
        "û": "u",
    }
)


def romanize(text: str) -> str:
    """Fold Maltese diacritics to ASCII for learner helpers (ċ→c, ġ→g, ħ→h, ż→z)."""
    return (text or "").translate(_FOLD)
