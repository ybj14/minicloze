#!/usr/bin/env python3
"""Offline Khmer romanization helpers for minicloze.

Follows Wiktionary ``Module:km-pron``:
- Orthographic transliteration via the ``tl`` character map (with repha
  handling and the ``ʰ̥`` → ``̥ʰ`` fix).
- WT romanisation via ``export.convert(text, "tc")`` syllable analysis.

This is NOT Module:km-translit / UNGEGN.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

J = "្"
C = "កខគឃងចឆជឈញដឋឌឍណតថទធនបផពភមយរលវឝឞសហឡអ"
C_MOD = "៉៊"
V_INDEP = "ឣឤឥឦឧឨឩឪឫឬឭឮឯឰឱឲឳ"
V_DIAC = "ាិីឹឺុូួើឿៀេែៃោៅំះៈ័៏"
V_POST = "់"
APOS = "'"

KM_STRING_RE = re.compile(rf"[ក-៹'{re.escape(V_INDEP)}]+")
RECESSIVE_RE = re.compile(r"[ŋɲñnmjyrlʋv]")

CONSONANTS: dict[str, dict[str, Any]] = {
    "ក": {"class": 1, "ipa": ("k", "k"), "tc": ("k", "k")},
    "ខ": {"class": 1, "ipa": ("kʰ", "k"), "tc": ("kh", "k")},
    "គ": {"class": 2, "ipa": ("k", "k"), "tc": ("k", "k")},
    "ឃ": {"class": 2, "ipa": ("kʰ", "k"), "tc": ("kh", "k")},
    "ង": {"class": 2, "ipa": ("ŋ", "ŋ"), "tc": ("ng", "ng")},
    "ង៉": {"class": 1, "ipa": ("ŋ", "ŋ"), "tc": ("ng", "ng")},
    "ច": {"class": 1, "ipa": ("c", "c"), "tc": ("c", "c")},
    "ឆ": {"class": 1, "ipa": ("cʰ", "c"), "tc": ("ch", "c")},
    "ជ": {"class": 2, "ipa": ("c", "c"), "tc": ("c", "c")},
    "ឈ": {"class": 2, "ipa": ("cʰ", "c"), "tc": ("ch", "c")},
    "ញ": {"class": 2, "ipa": ("ɲ", "ɲ"), "tc": ("ñ", "ñ")},
    "ញ៉": {"class": 1, "ipa": ("ɲ", "ɲ"), "tc": ("ñ", "ñ")},
    "ដ": {"class": 1, "ipa": ("ɗ", "t"), "tc": ("d", "t")},
    "ឋ": {"class": 1, "ipa": ("tʰ", "t"), "tc": ("th", "t")},
    "ឌ": {"class": 2, "ipa": ("ɗ", "t"), "tc": ("d", "t")},
    "ឍ": {"class": 2, "ipa": ("tʰ", "t"), "tc": ("th", "t")},
    "ណ": {"class": 1, "ipa": ("n", "n"), "tc": ("n", "n")},
    "ត": {"class": 1, "ipa": ("t", "t"), "tc": ("t", "t")},
    "ថ": {"class": 1, "ipa": ("tʰ", "t"), "tc": ("th", "t")},
    "ទ": {"class": 2, "ipa": ("t", "t"), "tc": ("t", "t")},
    "ធ": {"class": 2, "ipa": ("tʰ", "t"), "tc": ("th", "t")},
    "ន": {"class": 2, "ipa": ("n", "n"), "tc": ("n", "n")},
    "ន៉": {"class": 1, "ipa": ("n", "n"), "tc": ("n", "n")},
    "ប": {"class": 1, "ipa": ("ɓ", "p"), "tc": ("b", "p")},
    "ប៉": {"class": 1, "ipa": ("p", "p"), "tc": ("p", "p")},
    "ប៊": {"class": 2, "ipa": ("ɓ", "p"), "tc": ("b", "p")},
    "ផ": {"class": 1, "ipa": ("pʰ", "p"), "tc": ("ph", "p")},
    "ព": {"class": 2, "ipa": ("p", "p"), "tc": ("p", "p")},
    "ភ": {"class": 2, "ipa": ("pʰ", "p"), "tc": ("ph", "p")},
    "ម": {"class": 2, "ipa": ("m", "m"), "tc": ("m", "m")},
    "ម៉": {"class": 1, "ipa": ("m", "m"), "tc": ("m", "m")},
    "យ": {"class": 2, "ipa": ("j", "j"), "tc": ("y", "y")},
    "យ៉": {"class": 1, "ipa": ("j", "j"), "tc": ("y", "y")},
    "រ": {"class": 2, "ipa": ("r", ""), "tc": ("r", "")},
    "រ៉": {"class": 1, "ipa": ("r", ""), "tc": ("r", "")},
    "ល": {"class": 2, "ipa": ("l", "l"), "tc": ("l", "l")},
    "ល៉": {"class": 1, "ipa": ("l", "l"), "tc": ("l", "l")},
    "វ": {"class": 2, "ipa": ("ʋ", "w"), "tc": ("v", "w")},
    "វ៉": {"class": 1, "ipa": ("ʋ", "w"), "tc": ("v", "w")},
    "ឝ": {"class": 1, "ipa": ("s", "h"), "tc": ("s", "h")},
    "ឞ": {"class": 1, "ipa": ("s", "h"), "tc": ("s", "h")},
    "ស": {"class": 1, "ipa": ("s", "h"), "tc": ("s", "h")},
    "ស៊": {"class": 2, "ipa": ("s", "h"), "tc": ("s", "h")},
    "ហ": {"class": 1, "ipa": ("h", "h"), "tc": ("h", "h")},
    "ហ៊": {"class": 2, "ipa": ("h", "h"), "tc": ("h", "h")},
    "ឡ": {"class": 1, "ipa": ("l", "l"), "tc": ("l", "l")},
    "អ": {"class": 1, "ipa": ("ʔ", ""), "tc": ("ʼ", "ʼ")},
    "អ៊": {"class": 2, "ipa": ("ʔ", ""), "tc": ("ʼ", "ʼ")},
    "ហក": {"class": 1, "ipa": ("ɡ", "k"), "tc": ("g", "k")},
    "ហគ": {"class": 2, "ipa": ("ɡ", "k"), "tc": ("g", "k")},
    "ហគ៊": {"class": 2, "ipa": ("ɡ", "k"), "tc": ("g", "k")},
    "ហន": {"class": 1, "ipa": ("n", ""), "tc": ("n", "n")},
    "ហម": {"class": 1, "ipa": ("m", ""), "tc": ("m", "m")},
    "ហល": {"class": 1, "ipa": ("l", ""), "tc": ("l", "l")},
    "ហវ": {"class": 1, "ipa": ("f", "f"), "tc": ("f", "f")},
    "ហវ៊": {"class": 2, "ipa": ("f", "f"), "tc": ("f", "f")},
    "ហស": {"class": 1, "ipa": ("z", "z"), "tc": ("z", "z")},
    "ហស៊": {"class": 2, "ipa": ("z", "z"), "tc": ("z", "z")},
    "": {"class": 1, "ipa": ("", ""), "tc": ("", "")},
}

VOWELS: dict[str, dict[str, tuple[str, str]]] = {
    "": {"ipa": ("ɑː", "ɔː"), "tc": ("ɑɑ", "ɔɔ")},
    "៏": {"ipa": ("ɑ", "ɔ"), "tc": ("ɑ", "ɔ")},
    "់": {"ipa": ("ɑ", "ŭə"), "tc": ("ɑ", "ŭə")},
    "់2": {"ipa": ("ɑ", "u"), "tc": ("ɑ", "u")},
    "័": {"ipa": ("a", "ŏə"), "tc": ("a", "ŏə")},
    "័2": {"ipa": ("a", "ĕə"), "tc": ("a", "ĕə")},
    "័យ": {"ipa": ("aj", "ɨj"), "tc": ("ay", "ɨy")},
    "័រ": {"ipa": ("aə", "ŏə"), "tc": ("", "ɔə")},
    "ា": {"ipa": ("aː", "iə"), "tc": ("aa", "iə")},
    "ា់": {"ipa": ("a", "ŏə"), "tc": ("a", "ŏə")},
    "ា់2": {"ipa": ("a", "ĕə"), "tc": ("a", "ĕə")},
    "ិ": {"ipa": ("eʔ", "iʔ"), "tc": ("eʼ", "iʼ")},
    "ិ2": {"ipa": ("ə", "ɨ"), "tc": ("ə", "ɨ")},
    "ិយ": {"ipa": ("əj", "iː"), "tc": ("əy", "ii")},
    "ិះ": {"ipa": ("eh", "ih"), "tc": ("eh", "ih")},
    "ី": {"ipa": ("əj", "iː"), "tc": ("əy", "ii")},
    "ឹ": {"ipa": ("ə", "ɨ"), "tc": ("ə", "ɨ")},
    "ឹះ": {"ipa": ("əh", "ɨh"), "tc": ("əh", "ɨh")},
    "ឺ": {"ipa": ("əɨ", "ɨː"), "tc": ("əɨ", "ɨɨ")},
    "ុ": {"ipa": ("oʔ", "uʔ"), "tc": ("oʼ", "uʼ")},
    "ុ2": {"ipa": ("o", "u"), "tc": ("o", "u")},
    "ុះ": {"ipa": ("oh", "uh"), "tc": ("oh", "uh")},
    "ូ": {"ipa": ("ou", "uː"), "tc": ("ou", "uu")},
    "ូវ": {"ipa": ("əw", "ɨw"), "tc": ("əw", "ɨw")},
    "ួ": {"ipa": ("uə", "uə"), "tc": ("uə", "uə")},
    "ើ": {"ipa": ("aə", "əː"), "tc": ("aə", "əə")},
    "ើះ": {"ipa": ("aəh", "əh"), "tc": ("əh", "")},
    "ឿ": {"ipa": ("ɨə", "ɨə"), "tc": ("ɨə", "ɨə")},
    "ៀ": {"ipa": ("iə", "iə"), "tc": ("iə", "iə")},
    "េ": {"ipa": ("eː", "ei"), "tc": ("ee", "ei")},
    "េ2": {"ipa": ("ə", "ɨ"), "tc": ("ə", "ɨ")},
    "េះ": {"ipa": ("eh", "ih"), "tc": ("eh", "ih")},
    "ែ": {"ipa": ("ae", "ɛː"), "tc": ("ae", "ɛɛ")},
    "ែះ": {"ipa": ("aeh", "ɛh"), "tc": ("eh", "")},
    "ៃ": {"ipa": ("aj", "ɨj"), "tc": ("ay", "ɨy")},
    "ោ": {"ipa": ("ao", "oː"), "tc": ("ao", "oo")},
    "ោះ": {"ipa": ("ɑh", "ŭəh"), "tc": ("ɑh", "ŭəh")},
    "ៅ": {"ipa": ("aw", "ɨw"), "tc": ("aw", "ɨw")},
    "ុំ": {"ipa": ("om", "um"), "tc": ("om", "um")},
    "ំ": {"ipa": ("ɑm", "um"), "tc": ("ɑm", "um")},
    "ាំ": {"ipa": ("am", "ŏəm"), "tc": ("am", "ŏəm")},
    "ាំង": {"ipa": ("aŋ", "ĕəŋ"), "tc": ("ang", "ĕəng")},
    "ះ": {"ipa": ("ah", "ĕəh"), "tc": ("ah", "ĕəh")},
    "ៈ": {"ipa": ("aʔ", "ĕəʔ"), "tc": ("aʼ", "ĕəʼ")},
    "'": {"ipa": ("ə", "ə"), "tc": ("ə", "ə")},
}

TL: dict[str, str] = {
    "ក": "k", "ខ": "kʰ", "គ": "g", "ឃ": "gʰ", "ង": "ṅ",
    "ច": "c", "ឆ": "cʰ", "ជ": "j", "ឈ": "jʰ", "ញ": "ñ",
    "ដ": "ṭ", "ឋ": "ṭʰ", "ឌ": "ḍ", "ឍ": "ḍʰ", "ណ": "ṇ",
    "ត": "t", "ថ": "tʰ", "ទ": "d", "ធ": "dʰ", "ន": "n",
    "ប": "p", "ផ": "pʰ", "ព": "b", "ភ": "bʰ", "ម": "m",
    "យ": "y", "រ": "r", "ល": "l", "វ": "v",
    "ឝ": "ś", "ឞ": "ṣ", "ស": "s",
    "ហ": "h", "ឡ": "ḷ", "អ": "ʼ",
    "ឣ": "a", "ឤ": "ā", "ឥ": "i", "ឦ": "ī",
    "ឧ": "u", "ឨ": "uk", "ឩ": "ū", "ឪ": "uv",
    "ឫ": "ṛ", "ឬ": "ṝ", "ឭ": "ḷ", "ឮ": "ḹ",
    "ឯ": "e", "ឰ": "ai", "ឱ": "o", "ឲ": "o", "ឳ": "au",
    "ា": "ā", "ិ": "i", "ី": "ī", "ឹ": "ẏ", "ឺ": "ȳ",
    "ុ": "u", "ូ": "ū", "ួ": "ua",
    "ើ": "oe", "ឿ": "ẏa", "ៀ": "ia",
    "េ": "e", "ែ": "ae", "ៃ": "ai", "ោ": "o", "ៅ": "au",
    "ំ": "ṃ", "ះ": "ḥ", "ៈ": "`",
    "៉": "″", "៊": "′", "់": "´", "៌": "ŕ", "៍": "̊",
    "៎": "⸗", "៏": "ʿ", "័": "˘", "៑": "̑", "្": "̥",
    "។": "ǂ", "៕": "ǁ", "ៗ": "«", "៙": "§", "៚": "»", "៛": "",
    "០": "0", "១": "1", "២": "2", "៣": "3", "៤": "4",
    "៥": "5", "៦": "6", "៧": "7", "៨": "8", "៩": "9",
}

# Approximate WT-style values for independent vowels (not in km-pron convert).
INDEP_TC: dict[str, str] = {
    "ឣ": "ʼɑɑ", "ឤ": "ʼaa", "ឥ": "ʼə", "ឦ": "ʼəy",
    "ឧ": "ʼo", "ឨ": "ʼok", "ឩ": "ʼuu", "ឪ": "ʼəw",
    "ឫ": "rɨ", "ឬ": "rɨɨ", "ឭ": "lɨ", "ឮ": "lɨɨ",
    "ឯ": "ʼae", "ឰ": "ʼay", "ឱ": "ʼao", "ឲ": "ʼao", "ឳ": "ʼaw",
    "ឱ្យ": "ʼaoy",
    "ឲ្យ": "ʼaoy",
}

GLOTTIFY = {"a", "aː", "ɑ", "ɑː", "ɔ", "ɔː", "ĕə", "ŭə", "iə", "ɨə", "uə"}

AMBIG = {
    "k%-h": "k\u200bh",
    "c%-h": "c\u200bh",
    "t%-h": "t\u200bh",
    "p%-h": "p\u200bh",
    "n%-g": "n\u200bg",
}

KNOWN_TRANSCRIPTIONS: dict[str, str] = {
    # Phonemic-respelling cases (orthography alone insufficient)
    "សួស្តី": "suəsdəy",
    "សួស្ដី": "suəsdəy",
    "ធំ": "thom",
    "អ្នក": "nĕək",
    "ស្រលាញ់": "srɑlañ",
    "ស្រឡាញ់": "srɑlañ",
    "ទំហំ": "tumhum",
    "វិហារ": "vihiə",
    "បារី": "baarəy",
    "កន្លែង": "kɑnlaeng",
    "ភ្នំពេញ": "phnum pɨñ",
    "កម្ពុជា": "kampuciə",
    "អម្ពិល": "ʼɑmpɨl",
    "ប្ដី": "pdəy",
    "ប្តី": "pdəy",
    "ពពក": "pɔpɔɔk",
    "ពណ៌": "pɔɔ",
    "រវល់": "rɔwŏəl",
    "ដកដង្ហើម": "dɑɑk dɑɑnghaəm",
    "បទចម្រៀង": "bɑɑt cɑɑmriəng",
    "ថ្ងៃព្រហស្បតិ៍": "thngay prɔhɔah",
}

_REPHA_RE = re.compile(r"([\u1780-\u17a2])៌")
_PIECE = f"[{C}][{C_MOD}]?"
POST_INIT = (
    f"([{V_DIAC}]*)"
    f"([{C}]?[{C_MOD}]?)"
    f"([{V_POST}]?)"
    f"({re.escape(APOS)}?)"
)


def _c_capt(n: int = 1) -> str:
    """One outer capturing group only (matches Lua cCaptClus / cUncapt)."""
    if n == 1:
        return f"({_PIECE})"
    return "(" + _PIECE + (J + _PIECE) * (n - 1) + ")"


_SYL_PATTERNS = [
    re.compile("^" + _c_capt(n) + POST_INIT + "$")
    for n in (4, 3, 2, 1)
]

_SEQ1 = re.compile(
    f"([{C}{C_MOD}{V_DIAC}])"
    f"([{C}][{C_MOD}]?)"
    f"([{V_DIAC}{J}])"
)

# Sesquisyllable: coeng-cluster then another consonant onset
_SESQUI = re.compile(
    rf"([{C}][{C_MOD}]?(?:{J}[{C}][{C_MOD}]?)+)([{C}])"
)

# After a closed syllable (vowel diacritics + coda C), before a new onset C
_AFTER_RIME = re.compile(
    rf"([{C}][{C_MOD}]?(?:{J}[{C}][{C_MOD}]?)*[{V_DIAC}]+[{C}][{C_MOD}]?)"
    rf"([{C}])"
)


def repha(text: str) -> str:
    return _REPHA_RE.sub(r"៌\1", text)


def transliterate(text: str) -> str:
    """Return Wiktionary Orthographic romanisation (``tl`` map)."""
    text = unicodedata.normalize("NFC", text)
    text = repha(text)
    out = [TL.get(ch, ch) for ch in text]
    return "".join(out).replace("ʰ̥", "̥ʰ")


def syllabify(text: str) -> str:
    text = re.sub(r"([%'់])([^,\- ])", r"\1-\2", text)
    while _SEQ1.search(text):
        text = _SEQ1.sub(r"\1-\2\3", text)
    return text


def _sesqui_syllabify(text: str) -> str:
    """Extra hyphenation for inherent-vowel sesquisyllables (e.g. ក្រហម → ក្រ-ហម)."""
    text = syllabify(text)
    prev = None
    while prev != text:
        prev = text
        text = _SESQUI.sub(r"\1-\2", text)
        text = _AFTER_RIME.sub(r"\1-\2", text)
    return text


def syl_analysis(syllable: str) -> tuple[str, str, str, str, str] | None:
    # Independent vowel as its own syllable
    if len(syllable) >= 1 and syllable[0] in V_INDEP:
        return None  # handled separately
    for pat in _SYL_PATTERNS:
        m = pat.match(syllable)
        if m:
            return m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
    return None


def _syl_redist(text: str, block: bool) -> str | None:
    word_re = re.compile(rf"[ក-៹'\-]+")

    def repl_word(match: re.Match[str]) -> str:
        word = match.group(0)
        syls = word.split("-")
        all_syl: list[list[str]] = []
        for syl_id, syl in enumerate(syls):
            if syl == "":
                all_syl.append([])
                continue
            # Pass independent-vowel syllables through unchanged
            if syl and (syl in INDEP_TC or syl[0] in V_INDEP):
                all_syl.append([syl, "", "", "", ""])
                continue
            parsed = syl_analysis(syl)
            if not parsed:
                raise ValueError("syl_analysis failed")
            all_syl.append(list(parsed))
            if (
                syl_id != 0
                and all_syl[syl_id - 1]
                and len(all_syl[syl_id - 1]) >= 3
                and all_syl[syl_id - 1][2] == ""
                and J in all_syl[syl_id][0]
                and not block
            ):
                c1 = all_syl[syl_id][0]
                before_j = re.match(rf"^([^{J}]+)", c1)
                after_j = re.match(rf"^[^{J}]+{J}(.+)", c1)
                if before_j and after_j:
                    all_syl[syl_id - 1][2] = before_j.group(1)
                    all_syl[syl_id][0] = after_j.group(1)
            if (
                len(syls) == 2
                and syl_id == 1
                and all_syl[syl_id - 1]
                and len(all_syl[syl_id - 1]) >= 4
                and all_syl[syl_id - 1][1] + all_syl[syl_id - 1][3] == ""
                # Don't attach bantak to independent-vowel minor syllables
                and not (all_syl[syl_id - 1][0] and all_syl[syl_id - 1][0][0] in V_INDEP)
            ):
                all_syl[syl_id - 1][3] = V_POST
        return "-".join("".join(parts) for parts in all_syl)

    try:
        return word_re.sub(lambda m: repl_word(m), text)
    except ValueError:
        return None


def _get_cons(c1_set: list[str]) -> list[str] | None:
    cons_set: list[str] = []
    i = 0
    n = len(c1_set)
    while i < n:
        found = False
        for length in (3, 2, 1):
            chunk = "".join(c1_set[i : i + length]) if i + length <= n else "a"
            if chunk in CONSONANTS:
                cons_set.append(chunk)
                i += length
                found = True
                break
            if length == 1:
                return None
        if not found:
            return None
    return cons_set


def _init_clus(c1: str, mode: str) -> tuple[str, int]:
    pos = 0
    c1 = c1.replace(J, "")
    if c1 in CONSONANTS:
        data = CONSONANTS[c1]
        return data[mode][pos], data["class"]

    cons_set = _get_cons(list(c1))
    if not cons_set:
        raise ValueError(f"Error handling initial {c1}")

    init: list[str] = []
    fittest_s: int | str = ""
    for seq, ch in enumerate(cons_set, start=1):
        data = CONSONANTS[ch]
        onset = data[mode][pos]
        use_class = (
            (not RECESSIVE_RE.search(onset) and "ng" not in onset)
            or (fittest_s == "" and seq == len(cons_set))
        )
        if use_class:
            fittest_s = data["class"]
        init.append(onset)
    c1_out = "".join(init)
    c1_out = re.sub(r"[ɓb](.)", r"p\1", c1_out)
    if mode == "ipa":
        c1_out = re.sub(r"p([knŋcɲdtnjls])", r"pʰ\1", c1_out)
        c1_out = re.sub(r"pʰ([^knŋcɲdtnjls])", r"p\1", c1_out)
        c1_out = re.sub(r"t([kŋnmjlʋ])", r"tʰ\1", c1_out)
        c1_out = re.sub(r"tʰ([^kŋnmjlʋ])", r"t\1", c1_out)
        c1_out = re.sub(r"k([ctnbmlʋs])", r"kʰ\1", c1_out)
        c1_out = re.sub(r"kʰ([^ctnbmlʋs])", r"k\1", c1_out)
        c1_out = re.sub(r"c([kŋnmlʋʔ])", r"cʰ\1", c1_out)
        c1_out = re.sub(r"cʰ([^kŋnmlʋʔ])", r"c\1", c1_out)
    return c1_out, int(fittest_s) if fittest_s != "" else 1


def _rime(v1: str, c2: str, fittest: int, red: str, mode: str) -> str | None:
    if red == APOS:
        v1 = red
    key = v1 + c2
    if key in VOWELS:
        return VOWELS[key][mode][fittest - 1]

    c2_val = CONSONANTS[c2][mode][1] if c2 in CONSONANTS else c2

    if (
        ((v1 in ("័", "ា់")) and (re.search(r"[kŋ]", c2_val) or c2_val == "ng"))
        or (v1 == "េ" and (re.search(r"[cɲ]", c2_val) or c2_val == "ñ"))
        or (v1 == "់" and re.search(r"[mp]", c2_val))
        or (v1 in ("ិ", "ុ") and c2_val != "")
    ):
        v1 = v1 + "2"

    v1_val = VOWELS[v1][mode][fittest - 1] if v1 in VOWELS else v1
    if v1_val in GLOTTIFY and mode == "ipa" and c2_val == "k":
        c2_val = "ʡ"
    return v1_val + c2_val


def _convert_core(text: str, mode: str, block: bool) -> str | None:
    text = _syl_redist(text, block)
    if text is None:
        return None

    for syllable in list(KM_STRING_RE.findall(text)):
        # Independent vowel syllable (pre-split in convert)
        if syllable in INDEP_TC:
            text = text.replace(syllable, INDEP_TC[syllable], 1)
            continue
        if syllable and all(ch in V_INDEP for ch in syllable):
            repl = "".join(INDEP_TC.get(ch, TL.get(ch, ch)) for ch in syllable)
            text = text.replace(syllable, repl, 1)
            continue
        if syllable and syllable[0] in V_INDEP:
            indep = syllable[0]
            rest = syllable[1:]
            repl = INDEP_TC.get(indep, TL.get(indep, indep))
            if rest:
                rest_parsed = syl_analysis(rest)
                if rest_parsed:
                    try:
                        c1_out, fittest = _init_clus(rest_parsed[0], mode)
                        v1c2 = _rime(
                            rest_parsed[1] + rest_parsed[3],
                            rest_parsed[2],
                            fittest,
                            rest_parsed[4],
                            mode,
                        )
                        repl = repl + c1_out + (v1c2 or "")
                    except ValueError:
                        return None
                else:
                    return None
            text = text.replace(syllable, repl, 1)
            continue

        parsed = syl_analysis(syllable)
        if not parsed:
            return None
        c1, v1, c2, bantak, red = parsed
        try:
            c1_out, fittest = _init_clus(c1, mode)
        except ValueError:
            return None
        v1c2 = _rime(v1 + bantak, c2, fittest, red, mode)
        if v1c2 is None:
            return None
        text = text.replace(syllable, c1_out + v1c2, 1)

    def ambig_sub(m: re.Match[str]) -> str:
        key = m.group(1)
        lookup = key[0] + "%-" + key[-1] if len(key) >= 3 else key
        return AMBIG.get(lookup, key)

    text = re.sub(r"(.%\-.)", ambig_sub, text)
    text = text.replace("%", "")
    text = text.replace("-", ".")
    text = text.replace("\u200b", "-")
    text = re.sub(r"ʔ([ptkhlɲŋmnjw])", r"\1", text)
    text = text.replace("ŭə.", "ɔ.")
    text = re.sub(r"([eiou])[ʔʼ]\.", r"\1.", text)
    text = text.replace("ʡ.s", "k.s")
    text = text.replace("ʡ", "ʔ")

    if mode == "tc":
        text = text.replace("...", "…")
        text = text.replace(".", "")
    else:
        text = text.replace("-", ".")
        readings = [
            re.sub(r"^([^.]+)\.([^.]+)$", r"\1.ˈ\2", reading)
            for reading in text.split(", ")
        ]
        text = ", ".join(readings)
        text = re.sub(r"^([^.\s]+) ([^.\s]+)$", r"\1 ˈ\2", text)
    return text


def convert(text: str, mode: str = "tc") -> str | None:
    """Port of Module:km-pron ``export.convert`` (mode ``tc`` or ``ipa``)."""
    text = unicodedata.normalize("NFC", text)
    if not text:
        return ""

    # Strip toandakhiat-marked silent letters roughly: C៍ → drop C
    # (Wiktionary usually respells these away)
    text_work = re.sub(rf"[{C}]៍", "", text)

    # Split independent vowels into their own hyphen-separated tokens so the
    # rest of the word can be analysed normally (km-pron expects respelling).
    # Keep independent vowel + coeng clusters (e.g. ឲ្យ) intact.
    text_work = re.sub(
        rf"([{V_INDEP}](?:{J}[{C}][{C_MOD}]?)*)",
        lambda mo: f"-{mo.group(1)}-",
        text_work,
    )
    text_work = re.sub(r"-{2,}", "-", text_work).strip("-")

    # Lua ``block`` is true only when the *caller* supplied hyphens (phonemic
    # respelling). Auto-hyphens from syllabify must still allow sylRedist.
    block = "-" in text
    for candidate in (
        syllabify(text_work),
        _sesqui_syllabify(text_work),
    ):
        result = _convert_core(candidate, mode, block)
        if result is not None:
            return result
    return None


def transcribe(text: str) -> str:
    """Return Wiktionary WT romanisation (``convert(..., 'tc')``)."""
    text = unicodedata.normalize("NFC", text.strip())
    if not text:
        return ""
    if text in KNOWN_TRANSCRIPTIONS:
        return KNOWN_TRANSCRIPTIONS[text]
    if ", " in text:
        return ", ".join(transcribe(part) for part in text.split(", "))
    if " " in text:
        return " ".join(transcribe(part) for part in text.split())

    # Compounds starting with អ្នក
    if text.startswith("អ្នក") and len(text) > len("អ្នក"):
        rest = transcribe(text[len("អ្នក"):])
        return ("nĕək " + rest).strip() if rest else "nĕək"

    result = convert(text, "tc")
    if result is not None:
        return result
    return KNOWN_TRANSCRIPTIONS.get(text, "")


def romanize(text: str) -> tuple[str, str]:
    return transliterate(text), transcribe(text)


if __name__ == "__main__":
    import json
    import sys

    items = json.load(sys.stdin)
    json.dump(
        [
            {
                "text": item,
                "transliteration": transliterate(str(item)),
                "transcription": transcribe(str(item)),
            }
            for item in items
        ],
        sys.stdout,
        ensure_ascii=False,
    )
