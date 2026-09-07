#!/usr/bin/env python3
"""Tibetan pinyin (ZWPY / 藏文拼音) transcription for minicloze.

Scheme
------
Official SASM/GNC/SRC romanization of Standard Tibetan, commonly called
Tibetan pinyin or ZWPY (藏文拼音). Based on Lhasa pronunciation as used by
China National Radio Tibetan Radio; regulated via《少数民族语地名汉语拼音字母音译转写法》
(1976) and related PRC standards for geographic/personal names.

This is a *phonetic transcription* (actual Lhasa reading), not an orthographic
transliteration. Wylie/EWTS remains the orthographic layer (like Khmer ``tl``);
ZWPY is the learner pronunciation layer (like Khmer ``tc`` / Thai Paiboon).

Diacritics follow the official tables and common gazetteer spellings:
``ê ô ä ö ü`` (prefer umlauts over digraphs ``ai/oi/ain/oin``).

Conversion pipeline
-------------------
1. Tibetan Unicode → EWTS via ``pyewts`` (when available), or accept EWTS input.
2. Split into tsheg-syllables.
3. Longest-match Wylie onset + rime lookup from Wikipedia / national tables.
4. Light sandhi: non-initial bare ``ba`` / ``bo`` → ``wa`` / ``wo``.

Tone is not marked. Automatic phonetics cannot be 100% accurate for every
sandhi / word-boundary case; tables cover standard single-syllable Lhasa forms
plus the ba/bo particle rule.

References
----------
- https://en.wikipedia.org/wiki/Tibetan_pinyin
- 《少数民族语地名汉语拼音字母音译转写法》
- IETF tag ``bo-Latn-pinyin``
"""

from __future__ import annotations

import re
from typing import Iterable

try:
    import pyewts
except ImportError:  # pragma: no cover
    pyewts = None  # type: ignore

# Wylie onset cluster → Tibetan pinyin initial (longest keys matched first).
# Compiled from the English Wikipedia "Tibetan pinyin" onset table.
_ONSET_PAIRS: list[tuple[str, str]] = [
    # retroflex / r-subscript stacks (must beat shorter labial/velar keys)
    ("bsgr", "zh"),
    ("bskr", "zh"),
    ("mkhr", "ch"),
    ("'khr", "ch"),
    ("'phr", "ch"),
    ("mgr", "zh"),
    ("'gr", "zh"),
    ("'dr", "zh"),
    ("'br", "zh"),
    ("rkr", "zh"),
    ("lkr", "zh"),
    ("skr", "zh"),
    ("dkr", "zh"),
    ("bkr", "zh"),
    ("rgr", "zh"),
    ("lgr", "zh"),
    ("sgr", "zh"),
    ("dgr", "zh"),
    ("dpr", "zh"),
    ("dbr", "zh"),
    ("lpr", "zh"),
    ("spr", "zh"),
    ("rbr", "zh"),
    ("lbr", "zh"),
    ("sbr", "zh"),
    ("bsr", "zh"),
    ("khr", "ch"),
    ("thr", "ch"),
    ("phr", "ch"),
    ("grw", "ch"),
    ("kr", "zh"),
    ("tr", "zh"),
    ("pr", "zh"),
    ("gr", "ch"),
    ("dr", "ch"),
    ("br", "ch"),
    ("hr", "sh"),
    ("rh", "rh"),
    # ky / gy series
    ("brky", "gy"),
    ("bsky", "gy"),
    ("brgy", "gy"),
    ("bsgy", "gy"),
    ("rky", "gy"),
    ("lky", "gy"),
    ("sky", "gy"),
    ("dky", "gy"),
    ("bky", "gy"),
    ("rgy", "gy"),
    ("lgy", "gy"),
    ("sgy", "gy"),
    ("dgy", "gy"),
    ("bgy", "gy"),
    ("mgy", "gy"),
    ("'gy", "gy"),
    ("mkhy", "ky"),
    ("'khy", "ky"),
    ("khy", "ky"),
    ("ky", "gy"),
    ("gy", "ky"),
    ("hy", "hy"),
    # alveolo-palatal / y-subscript
    ("brny", "ny"),
    ("bsny", "ny"),
    ("rny", "ny"),
    ("sny", "ny"),
    ("gny", "ny"),
    ("mny", "ny"),
    ("nyw", "ny"),
    ("rmy", "ny"),
    ("smy", "ny"),
    ("dpy", "j"),
    ("lpy", "j"),
    ("spy", "j"),
    ("rby", "j"),
    ("lby", "j"),
    ("sby", "j"),
    ("brj", "j"),
    ("'by", "j"),
    ("'phy", "q"),
    ("phy", "q"),
    ("g.y", "y"),
    ("dby", "y"),
    ("py", "j"),
    ("by", "q"),
    ("my", "ny"),
    # affricates
    ("brts", "z"),
    ("bsts", "z"),
    ("brdz", "z"),
    ("rtsw", "z"),
    ("stsw", "z"),
    ("rts", "z"),
    ("sts", "z"),
    ("gts", "z"),
    ("bts", "z"),
    ("rdz", "z"),
    ("gdz", "z"),
    ("mdz", "z"),
    ("'dz", "z"),
    ("tshw", "c"),
    ("mtsh", "c"),
    ("'tsh", "c"),
    ("tsh", "c"),
    ("ts", "z"),
    ("dz", "c"),
    # velars
    ("brng", "ng"),
    ("bsng", "ng"),
    ("rng", "ng"),
    ("lng", "ng"),
    ("sng", "ng"),
    ("dng", "ng"),
    ("mng", "ng"),
    ("brk", "g"),
    ("bsk", "g"),
    ("brg", "g"),
    ("bsg", "g"),
    ("rk", "g"),
    ("lk", "g"),
    ("sk", "g"),
    ("kw", "g"),
    ("dk", "g"),
    ("bk", "g"),
    ("rg", "g"),
    ("lg", "g"),
    ("sg", "g"),
    ("dg", "g"),
    ("bg", "g"),
    ("mg", "g"),
    ("'g", "g"),
    ("khw", "k"),
    ("mkh", "k"),
    ("'kh", "k"),
    ("gw", "k"),
    ("kh", "k"),
    ("k", "g"),
    ("g", "k"),
    ("ng", "ng"),
    # dentals
    ("brt", "d"),
    ("blt", "d"),
    ("bst", "d"),
    ("bld", "d"),
    ("brd", "d"),
    ("bsd", "d"),
    ("bzl", "d"),
    ("rt", "d"),
    ("lt", "d"),
    ("st", "d"),
    ("tw", "d"),
    ("gt", "d"),
    ("bt", "d"),
    ("rd", "d"),
    ("sd", "d"),
    ("gd", "d"),
    ("bd", "d"),
    ("lth", "d"),
    ("zl", "d"),
    ("ld", "d"),
    ("md", "d"),
    ("'d", "d"),
    ("mth", "t"),
    ("'th", "t"),
    ("dw", "t"),
    ("th", "t"),
    ("t", "d"),
    ("d", "t"),
    # labials
    ("smr", "m"),
    ("sp", "b"),
    ("dp", "b"),
    ("lp", "b"),
    ("rb", "b"),
    ("sb", "b"),
    ("lb", "b"),
    ("'b", "b"),
    ("'ph", "p"),
    ("ph", "p"),
    ("bh", "bh"),
    ("rm", "m"),
    ("sm", "m"),
    ("dm", "m"),
    ("mr", "m"),
    ("db", "w"),
    ("p", "b"),
    ("b", "p"),
    ("m", "m"),
    ("w", "w"),
    # palatal affricates / fricatives
    ("gsh", "x"),
    ("bsh", "x"),
    ("shw", "x"),
    ("gzh", "x"),
    ("bzh", "x"),
    ("zhw", "x"),
    ("mch", "q"),
    ("'ch", "q"),
    ("gc", "j"),
    ("bc", "j"),
    ("lc", "j"),
    ("cw", "j"),
    ("rj", "j"),
    ("gj", "j"),
    ("lj", "j"),
    ("mj", "j"),
    ("'j", "j"),
    ("sh", "x"),
    ("zh", "x"),
    ("ch", "q"),
    ("c", "j"),
    ("j", "q"),
    # sibilants / liquids / glides
    ("brl", "l"),
    ("bsl", "l"),
    ("bsr", "s"),
    ("sr", "s"),
    ("sw", "s"),
    ("gs", "s"),
    ("bs", "s"),
    ("zw", "s"),
    ("gz", "s"),
    ("bz", "s"),
    ("brn", "n"),
    ("bsn", "n"),
    ("rn", "n"),
    ("sn", "n"),
    ("gn", "n"),
    ("mn", "n"),
    ("lh", "lh"),
    ("lw", "l"),
    ("kl", "l"),
    ("gl", "l"),
    ("bl", "l"),
    ("rl", "l"),
    ("sl", "l"),
    ("rw", "r"),
    ("hw", "h"),
    ("s", "s"),
    ("z", "s"),
    ("l", "l"),
    ("r", "r"),
    ("h", "h"),
    ("y", "y"),
    ("ny", "ny"),
    ("n", "n"),
]

_ONSET: dict[str, str] = {}
for _k, _v in _ONSET_PAIRS:
    _ONSET.setdefault(_k, _v)

_ONSET_KEYS = sorted(_ONSET.keys(), key=len, reverse=True)

_RIME: dict[str, str] = {
    "a": "a", "a'u": "au", "ar": "ar", "al": "ä", "a'i": "ä", "ad": "ä", "as": "ä",
    "ag": "ag", "ags": "ag", "ab": "ab", "abs": "ab", "ang": "ang", "angs": "ang",
    "am": "am", "ams": "am", "an": "än",
    "i": "i", "i'u": "iu", "e'u": "iu", "ir": "ir", "il": "i", "id": "i", "is": "i",
    "ig": "ig", "igs": "ig", "ib": "ib", "ibs": "ib", "ing": "ing", "ings": "ing",
    "im": "im", "ims": "im", "in": "in",
    "u": "u", "ur": "ur", "ul": "ü", "u'i": "ü", "ud": "ü", "us": "ü",
    "ug": "ug", "ugs": "ug", "ub": "ub", "ubs": "ub", "ung": "ung", "ungs": "ung",
    "um": "um", "ums": "um", "un": "ün",
    "e": "ê", "er": "êr", "el": "ê", "e'i": "ê", "ed": "ê", "es": "ê",
    "eg": "êg", "egs": "êg", "eb": "êb", "ebs": "êb", "eng": "êng", "engs": "êng",
    "em": "êm", "ems": "êm", "en": "ên",
    "o": "o", "o'u": "ou", "or": "or", "ol": "ö", "o'i": "ö", "od": "ö", "os": "ö",
    "og": "og", "ogs": "og", "ob": "ob", "obs": "ob", "ong": "ong", "ongs": "ong",
    "om": "om", "oms": "om", "on": "ön",
}

_RIME_KEYS = sorted(_RIME.keys(), key=len, reverse=True)
_VOWELS = set("aeiou")
_TIBETAN_RE = re.compile(r"[\u0f00-\u0fff]+")
_SPACE_RE = re.compile(r"\s+")


def _converter():
    if pyewts is None:
        raise RuntimeError("pyewts is required for Tibetan Unicode → Wylie")
    return pyewts.pyewts()


def to_wylie(text: str) -> str:
    raw = str(text or "")
    if not raw.strip():
        return ""
    if _TIBETAN_RE.search(raw):
        return _converter().toWylie(raw)
    return raw


def _normalize_wylie_syllable(syllable: str) -> str:
    s = syllable.strip().lower()
    s = s.replace("+", "")
    s = re.sub(r"^\[+|\]+$", "", s)
    return s


def _split_onset_rime(syllable: str) -> tuple[str, str]:
    s = _normalize_wylie_syllable(syllable)
    if not s:
        return "", ""

    if s[0] in _VOWELS:
        return "", s
    if s.startswith("'") and len(s) > 1 and s[1] in _VOWELS:
        return "", s[1:]

    for onset in _ONSET_KEYS:
        if s.startswith(onset):
            rest = s[len(onset):]
            if rest == "" or rest[0] in _VOWELS or rest.startswith("'"):
                return onset, rest if rest else "a"

    for i, ch in enumerate(s):
        if ch in _VOWELS:
            return s[:i], s[i:]
        if ch == "'" and i + 1 < len(s) and s[i + 1] in _VOWELS and i > 0:
            return s[:i], s[i:]
    return s, "a"


def _rime_to_zwpy(rime: str) -> str:
    r = rime.strip().lower()
    if not r:
        return "a"
    if r in _RIME:
        return _RIME[r]
    if r.endswith("'") and r[:-1] in _RIME:
        return _RIME[r[:-1]]
    for key in _RIME_KEYS:
        if r.startswith(key):
            return _RIME[key]
    return r


def _onset_to_zwpy(onset: str) -> str:
    if not onset:
        return ""
    return _ONSET.get(onset, onset)


def syllable_zwpy(wylie_syllable: str, *, word_initial: bool = True) -> str:
    s = _normalize_wylie_syllable(wylie_syllable)
    if not s or s in {"/", "|", "//"}:
        return ""

    if not word_initial:
        if s == "ba":
            return "wa"
        if s == "bo":
            return "wo"

    onset, rime = _split_onset_rime(s)
    return f"{_onset_to_zwpy(onset)}{_rime_to_zwpy(rime)}"


def _wylie_syllables(wylie: str) -> list[str]:
    text = wylie.strip()
    if not text:
        return []
    return [p for p in _SPACE_RE.split(text) if p]


def romanize_wylie(wylie: str) -> str:
    syllables = _wylie_syllables(wylie)
    out: list[str] = []
    for i, syl in enumerate(syllables):
        zw = syllable_zwpy(syl, word_initial=(i == 0))
        if zw:
            out.append(zw)
    return " ".join(out)


def romanize(text: str) -> str:
    raw = str(text or "").strip()
    if not raw:
        return ""
    if not _TIBETAN_RE.search(raw) and not re.search(r"[A-Za-z']", raw):
        return ""
    return romanize_wylie(to_wylie(raw))


def romanize_many(items: Iterable[str]) -> list[str]:
    return [romanize(item) for item in items]


def self_check() -> None:
    cases = [
        ("བོད་", "pö"),
        ("བོད་སྐད", "pö gä"),
        ("ཁ་བ་", "ka wa"),
        ("སློབ་ཕྲུག", "lob chug"),
        ("བཀྲ་ཤིས", "zha xi"),
        ("བདེ་ལེགས", "dê lêg"),
        ("གཞིས་ཀ་རྩེ་", "xi ga zê"),
        ("བཀྲ་ཤིས་ལྷུན་པོ་", "zha xi lhün bo"),
        ("འབྲས་སྤུང་", "zhä bung"),
        ("ཆོས་ཀྱི་རྒྱལ་མཚན་", "qö gyi gyä cän"),
        ("ཐུབ་བསྟན་རྒྱ་མཚོ་", "tub dän gya co"),
        ("ལྷ་ས་", "lha sa"),
        ("ང", "nga"),
    ]
    print("Tibetan → ZWPY self-check")
    ok = 0
    for tib, expected in cases:
        got = romanize(tib)
        mark = "OK" if got == expected else "DIFF"
        if got == expected:
            ok += 1
        print(f"  [{mark}] {tib} => {got!r} (expected {expected!r})")
    print(f"{ok}/{len(cases)} exact matches")


if __name__ == "__main__":
    self_check()
