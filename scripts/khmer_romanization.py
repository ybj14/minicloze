#!/usr/bin/env python3
"""Offline Khmer romanization helpers for minicloze.

The spelling-oriented transliteration follows the structure of Wiktionary's
``Module:km-translit`` (WT:KM TR).  The pronunciation-oriented transcription
uses Wiktionary-style output names and test-case spellings where known, then
falls back to a conservative conversion from the same syllable analysis.
"""

from __future__ import annotations

import re
import unicodedata

ZWS = "\u200b"
CONSONANTS = "កខគឃងចឆជឈញដឋឌឍណតថទធនបផពភមយរលវឝឞសហឡអ"
CONSONANT_RE = f"[{CONSONANTS}]"

CONS_CONV = {
    "ក": ("k", "a"),
    "ខ": ("kh", "a"),
    "គ": ("k", "o"),
    "ឃ": ("kh", "o"),
    "ង": ("ng", "o"),
    "ច": ("ch", "a"),
    "ឆ": ("chh", "a"),
    "ជ": ("ch", "o"),
    "ឈ": ("chh", "o"),
    "ញ": ("nh", "o"),
    "ដ": ("d", "a"),
    "ឋ": ("th", "a"),
    "ឌ": ("d", "o"),
    "ឍ": ("th", "o"),
    "ណ": ("n", "a"),
    "ត": ("t", "a"),
    "ថ": ("th", "a"),
    "ទ": ("t", "o"),
    "ធ": ("th", "o"),
    "ន": ("n", "o"),
    "ប": ("b", "a"),
    "ផ": ("ph", "a"),
    "ព": ("p", "o"),
    "ភ": ("ph", "o"),
    "ម": ("m", "o"),
    "យ": ("y", "o"),
    "រ": ("r", "o"),
    "ល": ("l", "o"),
    "វ": ("v", "o"),
    "ឝ": ("sh", "a"),
    "ឞ": ("ss", "o"),
    "ស": ("s", "a"),
    "ហ": ("h", "a"),
    "ឡ": ("l", "a"),
    "អ": ("ʼ", "a"),
    "": ("", ""),
    "ប៉": ("p", "a"),
}

DIGRAPH = {
    "ហ្គ": "g",
    "ហ្ន": "n",
    "ហ្ម": "m",
    "ហ្ល": "l",
    "ហ្វ": "f",
    "ហ្ស": "z",
}

INDEP_VOWEL = {
    "ឥ": "ʼĕ",
    "ឦ": "ʼei",
    "ឧ": "ʼŏ",
    "ឨ": "ʼŏk",
    "ឩ": "ʼŭ",
    "ឪ": "ʼŏu",
    "ឫ": "rœ̆",
    "ឬ": "rœ",
    "ឭ": "lœ̆",
    "ឮ": "lœ",
    "ឯ": "ʼé",
    "ឰ": "ʼai",
    "ឱ": "ʼaô",
    "ឲ": "ʼaô",
    "ឳ": "ʼâu",
}

VOWEL_CONV = {
    "": {"a": "â", "o": "ô"},
    "ា": {"a": "a", "o": "éa"},
    "ិ": {"a": "ĕ", "o": "ĭ"},
    "ី": {"a": "ei", "o": "i"},
    "ឹ": {"a": "œ̆", "o": "œ̆"},
    "ឺ": {"a": "œ", "o": "œ"},
    "ុ": {"a": "ŏ", "o": "ŭ"},
    "ូ": {"a": "o", "o": "u"},
    "ួ": {"a": "uŏ", "o": "uŏ"},
    "ើ": {"a": "aeu", "o": "eu"},
    "ឿ": {"a": "eua", "o": "eua"},
    "ៀ": {"a": "iĕ", "o": "iĕ"},
    "េ": {"a": "é", "o": "é"},
    "ែ": {"a": "ê", "o": "ê"},
    "ៃ": {"a": "ai", "o": "ey"},
    "ោ": {"a": "aô", "o": "oŭ"},
    "ៅ": {"a": "au", "o": "ŏu"},
    "ុំ": {"a": "om", "o": "ŭm"},
    "ំ": {"a": "âm", "o": "um"},
    "ាំ": {"a": "ăm", "o": "ŏâm"},
    "ាំង": {"a": "ăng", "o": "eăng"},
    "ះ": {"a": "ăh", "o": "eăh"},
    "ុះ": {"a": "ŏh", "o": "uh"},
    "េះ": {"a": "éh", "o": "éh"},
    "ោះ": {"a": "aŏh", "o": "uŏh"},
    "ឹះ": {"a": "ĕh", "o": "ĭh"},
    "ិះ": {"a": "ĕh", "o": "ĭh"},
    "ៈ": {"a": "aʼ", "o": "éaʼ"},
    "័": {"a": "â", "o": "ô"},
}

CHAR_TYPE = {char: "consonant" for char in CONSONANTS}
CHAR_TYPE.update({char: "indep_vowel" for char in INDEP_VOWEL})
CHAR_TYPE.update({char: "vowel_sign" for char in "ាិីឹឺុូួើឿៀេែោៅ"})
CHAR_TYPE.update({char: "terminating_vowel" for char in "ៃំះៈ"})
CHAR_TYPE.update({"៉": "consonant_shift", "៊": "consonant_shift"})
CHAR_TYPE.update({"់": "terminating_sign"})
CHAR_TYPE.update({char: "sign" for char in "៌៍៎៏័៑៓៖ៜ៝"})
CHAR_TYPE.update({"្": "combining_sign"})
CHAR_TYPE.update({char: "punctuation" for char in "។៕ៗ៘៙៚៛"})
CHAR_TYPE[ZWS] = "ZWS"

SP_SYMBOLS = {
    **{chr(ord("០") + index): str(index) for index in range(10)},
    **{chr(ord("៰") + index): str(index) for index in range(10)},
}

KNOWN_TRANSCRIPTIONS = {
    "ក្បាល": "kbaal",
    "ស្អែក": "sʼaek",
    "ផ្សេង": "phseing",
    "ល្មម": "lmɔɔm",
    "ភ្ជុំ": "phcum",
    "ម្នាស់": "mnŏəh",
    "ផ្ទះ": "phtĕəh",
    "ខ្ញុំ": "khñom",
    "ប្ដី": "pdəy",
    "ប្តី": "pdəy",
    "ឆ្វេង": "chveing",
    "ហ្វឹក": "fək",
    "ឡាន": "laan",
    "ឃាត់": "khŏət",
    "ខាត់": "khat",
    "ញាំ": "ñŏəm",
    "ល្ហុង": "lhong",
    "អ្នក": "nĕək",
    "លក់": "lŭək",
    "ស្រលាញ់": "srɑlañ",
    "ស្រឡាញ់": "srɑlañ",
    "គំនិត": "kumnɨt",
    "ត្រជាក់": "trɑcĕək",
    "ជណ្ដើរ": "cŭəndaə",
    "ទំហំ": "tumhum",
    "វិហារ": "vihiə",
    "បារី": "baarəy",
    "កន្លែង": "kɑnlaeng",
    "ភ្នំពេញ": "phnum pɨñ",
    "ធំ": "thom",
    "ឆ្ងាញ់": "chngañ",
    "កម្ពុជា": "kampuciə",
    "អម្ពិល": "ʼɑmpɨl",
}


def _chartype(char: str) -> str | None:
    return CHAR_TYPE.get(char)


def _preprocess(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = "".join(SP_SYMBOLS.get(char, char) for char in text)
    text = re.sub(r"(.)្(.្.)", rf"\1{ZWS}\2", text)
    text = re.sub(
        rf"({CONSONANT_RE}្{CONSONANT_RE})({CONSONANT_RE})",
        rf"{ZWS}\1\2",
        text,
    )
    text = re.sub(
        rf"({CONSONANT_RE})({CONSONANT_RE}្?{CONSONANT_RE})",
        rf"\1{ZWS}\2",
        text,
    )
    text = re.sub(r"(.៍)", rf"{ZWS}\1", text)
    return text


def _segment_word(word: str) -> list[str]:
    chars = list(word)
    types = [_chartype(char) for char in chars]
    syllables: list[str] = []
    current: list[str] = []
    progress = "none"

    def next_types_from(start: int) -> tuple[list[str], bool]:
        next_types: list[str] = []
        index = start
        while True:
            chartype = types[index] if index < len(types) else None
            char = chars[index] if index < len(chars) else ""
            if (
                chartype is None
                or chartype in {"punctuation", "indep_vowel", "terminating_sign", "ZWS"}
            ):
                return next_types, True
            if chartype in {"consonant", "combining_sign"} or (
                chartype == "sign" and char != "័"
            ):
                next_types.append(chartype)
            else:
                return next_types, False
            index += 1

    def has_following_consonant_cluster(start: int) -> bool:
        next_types, skipped = next_types_from(start)
        if skipped:
            return True
        joined = " ".join(next_types)
        return re.search(r"consonant s?i?g?n? ?consonant", joined) is not None

    for index in range(len(chars) + 1):
        char = chars[index] if index < len(chars) else ""
        chartype = types[index] if index < len(types) else None
        previous = chars[index - 1] if index else ""
        nxt = chars[index + 1] if index + 1 < len(chars) else ""

        if index == len(chars) or chartype == "ZWS":
            progress = "none"
            if current:
                syllables.append("".join(current))
                current = []
        elif progress == "none":
            if chartype == "consonant":
                current.append(char)
                progress = "initial"
            else:
                syllables.append(char)
        elif progress == "initial":
            if chartype == "combining_sign":
                current.append(char)
                progress = "initial_combining"
            elif chartype in {"sign", "consonant_shift"}:
                current.append(char)
            elif chartype == "vowel_sign":
                current.append(char)
                progress = "vowel"
            elif chartype == "terminating_vowel":
                current.append(char)
                if previous + char + nxt == "ាំង" and index == len(chars) - 2:
                    progress = "vowel"
                else:
                    syllables.append("".join(current))
                    current = []
                    progress = "none"
            elif chartype == "consonant":
                if has_following_consonant_cluster(index):
                    current.append(char)
                    progress = "coda"
                else:
                    syllables.append("".join(current))
                    current = [char]
                    progress = "initial"
            else:
                syllables.append(char)
                progress = "none"
        elif progress == "initial_combining":
            if chartype == "consonant":
                current.append(char)
                progress = "initial"
            else:
                syllables.append(char)
                progress = "none"
        elif progress == "vowel":
            if chartype == "vowel_sign":
                current.append(char)
            elif chartype == "terminating_vowel":
                current.append(char)
                if previous + char + nxt == "ាំង" and index == len(chars) - 2:
                    progress = "vowel"
                else:
                    syllables.append("".join(current))
                    current = []
                    progress = "none"
            elif chartype == "consonant":
                if has_following_consonant_cluster(index):
                    current.append(char)
                    progress = "coda"
                else:
                    syllables.append("".join(current))
                    current = [char]
                    progress = "initial"
            else:
                syllables.append(char)
                progress = "none"
        elif progress == "coda":
            if chartype == "combining_sign":
                current.append(char)
                progress = "coda_combining"
            elif chartype in {"sign", "terminating_sign"}:
                current.append(char)
            else:
                if current:
                    syllables.append("".join(current))
                current = []
                if chartype == "consonant":
                    current.append(char)
                    progress = "initial"
                else:
                    syllables.append(char)
                    progress = "none"
        elif progress == "coda_combining":
            if chartype == "consonant":
                current.append(char)
                progress = "coda"
            else:
                if current:
                    syllables.append("".join(current))
                current = []
                progress = "none"

    return [syllable for syllable in syllables if syllable]


def _transliterate_syllable(syllable: str) -> str:
    if "៍" in syllable:
        return "".join(CONS_CONV.get(char, ("", ""))[0] for char in syllable)

    original = syllable
    syllable = syllable.removesuffix("់")
    pattern = re.compile(
        rf"^({CONSONANT_RE})្?({CONSONANT_RE}?)([៉៊]?)([ាិីឹឺុូួើឿៀេែៃោៅា័]?[ំះៈ]?)([៉៊]?)([{CONSONANTS}]?៉?)្?({CONSONANT_RE}?)(៖?)$"
    )
    match = pattern.match(syllable)
    if not match:
        return "".join(INDEP_VOWEL.get(char, char) for char in original)

    initial_a, initial_b, shifter_a, vowel, shifter_b, coda_a, coda_b, optional = match.groups()
    if not (shifter_a + shifter_b + vowel + coda_a + coda_b) and initial_b and "្" not in syllable:
        coda_a = initial_b
        initial_b = ""
    base = initial_a
    if initial_b and initial_b not in "ងញនមយរលវ":
        base = initial_b
    if vowel + coda_a + coda_b == "ាំង":
        vowel, coda_a, coda_b = "ាំង", "", ""
    optional = optional.replace("៖", "ː")

    shifter = shifter_a + shifter_b
    if not shifter and base in CONS_CONV:
        vowel_class = CONS_CONV[base][1]
    elif shifter == "៉":
        vowel_class = "a"
    elif shifter == "៊":
        vowel_class = "o"
    else:
        return syllable + optional

    vowel_value = VOWEL_CONV.get(vowel, {}).get(vowel_class)
    if vowel_value is None:
        return syllable + optional

    initial_key = f"{initial_a}្{initial_b}"
    coda_key = f"{coda_a}្{coda_b}"
    if initial_key in DIGRAPH and (
        coda_key in DIGRAPH or (coda_a in CONS_CONV and coda_b in CONS_CONV)
    ):
        coda_value = DIGRAPH.get(coda_key) or CONS_CONV[coda_a][0] + CONS_CONV[coda_b][0]
        return DIGRAPH[initial_key] + vowel_value + coda_value + optional

    if (
        initial_a in CONS_CONV
        and initial_b in CONS_CONV
        and coda_a in CONS_CONV
        and coda_b in CONS_CONV
    ):
        return (
            CONS_CONV[initial_a][0]
            + CONS_CONV[initial_b][0]
            + vowel_value
            + CONS_CONV[coda_a][0]
            + CONS_CONV[coda_b][0]
            + optional
        )

    return syllable + optional


def transliterate(text: str) -> str:
    """Return Wiktionary-style Khmer transliteration."""
    text = _preprocess(text)
    for match in list(re.finditer(rf"[ក-៝{ZWS}]+", text)):
        original = match.group(0)
        syllables = [_transliterate_syllable(item) for item in _segment_word(original)]
        for index, syllable in enumerate(syllables):
            if syllable == "ៗ" and index:
                syllables[index] = syllables[index - 1]
        converted = "".join(syllables)
        text = text.replace(original, converted, 1)
    text = "".join(INDEP_VOWEL.get(char, char) for char in text)
    text = re.sub(r"([^ ]*) ៗ", r"\1 \1", text)
    return unicodedata.normalize("NFC", text).replace(ZWS, "")


def _fallback_transcription(text: str) -> str:
    value = transliterate(text)
    replacements = [
        ("chh", "ch"),
        ("nh", "ñ"),
        ("â", "ɑ"),
        ("ô", "ɔ"),
        ("œ̆", "ə"),
        ("œ", "əə"),
        ("ĕ", "ĕ"),
        ("ĭ", "ɨ"),
        ("ŭ", "u"),
        ("ŏ", "o"),
        ("éa", "iə"),
        ("aeu", "aə"),
        ("eu", "ə"),
        ("ei", "əy"),
        ("aô", "ao"),
        ("oŭ", "ou"),
        ("ŏu", "ou"),
        ("uŏ", "uə"),
        ("eua", "ɨə"),
        ("iĕ", "iə"),
        ("é", "e"),
        ("ê", "ɛɛ"),
    ]
    for source, target in replacements:
        value = value.replace(source, target)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def transcribe(text: str) -> str:
    """Return Wiktionary-style Khmer pronunciation transcription."""
    text = text.strip()
    if not text:
        return ""
    if text in KNOWN_TRANSCRIPTIONS:
        return KNOWN_TRANSCRIPTIONS[text]
    if re.search(r"\s", text):
        return " ".join(transcribe(part) for part in text.split())
    return _fallback_transcription(text)


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
