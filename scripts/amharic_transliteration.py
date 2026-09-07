#!/usr/bin/env python3
"""Amharic / Ethiopic romanization for minicloze.

Faithful port of Wiktionary ``Module:Ethi-translit`` (WT:ETHI TR):
https://en.wiktionary.org/wiki/Module:Ethi-translit

Display field is scholarly transliteration (ä/ə/ʾ/š/…), not SERA ASCII.
Optional ``KNOWN_GEMINATES`` covers frequent entry-level gemination that the
orthography-only module cannot recover (e.g. ቡና → bunna).
"""

from __future__ import annotations

import re
import unicodedata

GEM = "\u135F"  # ETHIOPIC COMBINING GEMINATION MARK

# Character map from Module:Ethi-translit ``tt``
TT: dict[str, str] = {
    "ሀ": "hä", "ሁ": "hu", "ሂ": "hi", "ሃ": "ha", "ሄ": "he", "ህ": "hə", "ሆ": "ho",
    "ለ": "lä", "ሉ": "lu", "ሊ": "li", "ላ": "la", "ሌ": "le", "ል": "lə", "ሎ": "lo",
    "ሏ": "lʷa",
    "ሐ": "ḥä", "ሑ": "ḥu", "ሒ": "ḥi", "ሓ": "ḥa", "ሔ": "ḥe", "ሕ": "ḥə", "ሖ": "ḥo",
    "ሗ": "ḥʷa",
    "መ": "mä", "ሙ": "mu", "ሚ": "mi", "ማ": "ma", "ሜ": "me", "ም": "mə", "ሞ": "mo",
    "ሟ": "mʷa", "ፙ": "mʲä",
    "ሠ": "śä", "ሡ": "śu", "ሢ": "śi", "ሣ": "śa", "ሤ": "śe", "ሥ": "śə", "ሦ": "śo",
    "ሧ": "śʷa",
    "ረ": "rä", "ሩ": "ru", "ሪ": "ri", "ራ": "ra", "ሬ": "re", "ር": "rə", "ሮ": "ro",
    "ሯ": "rʷa", "ፘ": "rʲä",
    "ሰ": "sä", "ሱ": "su", "ሲ": "si", "ሳ": "sa", "ሴ": "se", "ስ": "sə", "ሶ": "so",
    "ሷ": "sʷa",
    "ሸ": "šä", "ሹ": "šu", "ሺ": "ši", "ሻ": "ša", "ሼ": "še", "ሽ": "šə", "ሾ": "šo",
    "ሿ": "šʷa",
    "ቀ": "ḳä", "ቁ": "ḳu", "ቂ": "ḳi", "ቃ": "ḳa", "ቄ": "ḳe", "ቅ": "ḳə", "ቆ": "ḳo",
    "ቈ": "ḳʷä", "ቊ": "ḳʷi", "ቋ": "ḳʷa", "ቌ": "ḳʷe", "ቍ": "ḳʷə",
    "ቐ": "x̣ä", "ቑ": "x̣u", "ቒ": "x̣i", "ቓ": "x̣a", "ቔ": "x̣e", "ቕ": "x̣ə", "ቖ": "x̣o",
    "ቘ": "x̣ʷä", "ቚ": "x̣ʷi", "ቛ": "x̣ʷa", "ቜ": "x̣ʷe", "ቝ": "x̣ʷə",
    "በ": "bä", "ቡ": "bu", "ቢ": "bi", "ባ": "ba", "ቤ": "be", "ብ": "bə", "ቦ": "bo",
    "ቧ": "bʷa",
    "ቨ": "vä", "ቩ": "vu", "ቪ": "vi", "ቫ": "va", "ቬ": "ve", "ቭ": "və", "ቮ": "vo",
    "ቯ": "vʷa",
    "ተ": "tä", "ቱ": "tu", "ቲ": "ti", "ታ": "ta", "ቴ": "te", "ት": "tə", "ቶ": "to",
    "ቷ": "tʷa",
    "ቸ": "čä", "ቹ": "ču", "ቺ": "či", "ቻ": "ča", "ቼ": "če", "ች": "čə", "ቾ": "čo",
    "ቿ": "čʷa",
    "ኀ": "ḫä", "ኁ": "ḫu", "ኂ": "ḫi", "ኃ": "ḫa", "ኄ": "ḫe", "ኅ": "ḫə", "ኆ": "ḫo",
    "ኈ": "ḫʷä", "ኊ": "ḫʷi", "ኋ": "ḫʷa", "ኌ": "ḫʷe", "ኍ": "ḫʷə",
    "ነ": "nä", "ኑ": "nu", "ኒ": "ni", "ና": "na", "ኔ": "ne", "ን": "nə", "ኖ": "no",
    "ኗ": "nʷa",
    "ኘ": "ñä", "ኙ": "ñu", "ኚ": "ñi", "ኛ": "ña", "ኜ": "ñe", "ኝ": "ñə", "ኞ": "ño",
    "ኟ": "ñʷa",
    "አ": "ʾä", "ኡ": "ʾu", "ኢ": "ʾi", "ኣ": "ʾa", "ኤ": "ʾe", "እ": "ʾə", "ኦ": "ʾo",
    "ኧ": "ʾʷa",
    "ከ": "kä", "ኩ": "ku", "ኪ": "ki", "ካ": "ka", "ኬ": "ke", "ክ": "kə", "ኮ": "ko",
    "ኰ": "kʷä", "ኲ": "kʷi", "ኳ": "kʷa", "ኴ": "kʷe", "ኵ": "kʷə",
    "ኸ": "xä", "ኹ": "xu", "ኺ": "xi", "ኻ": "xa", "ኼ": "xe", "ኽ": "xə", "ኾ": "xo",
    "ዅ": "xʷə", "ዀ": "xʷä", "ዂ": "xʷi", "ዃ": "xʷa", "ዄ": "xʷe",
    "ወ": "wä", "ዉ": "wu", "ዊ": "wi", "ዋ": "wa", "ዌ": "we", "ው": "wə", "ዎ": "wo",
    "ዐ": "ʿä", "ዑ": "ʿu", "ዒ": "ʿi", "ዓ": "ʿa", "ዔ": "ʿe", "ዕ": "ʿə", "ዖ": "ʿo",
    "ዘ": "zä", "ዙ": "zu", "ዚ": "zi", "ዛ": "za", "ዜ": "ze", "ዝ": "zə", "ዞ": "zo",
    "ዟ": "zʷa",
    "ዠ": "žä", "ዡ": "žu", "ዢ": "ži", "ዣ": "ža", "ዤ": "že", "ዥ": "žə", "ዦ": "žo",
    "ዧ": "žʷa",
    "የ": "yä", "ዩ": "yu", "ዪ": "yi", "ያ": "ya", "ዬ": "ye", "ይ": "yə", "ዮ": "yo",
    "ደ": "dä", "ዱ": "du", "ዲ": "di", "ዳ": "da", "ዴ": "de", "ድ": "də", "ዶ": "do",
    "ዷ": "dʷa",
    "ጀ": "ǧä", "ጁ": "ǧu", "ጂ": "ǧi", "ጃ": "ǧa", "ጄ": "ǧe", "ጅ": "ǧə", "ጆ": "ǧo",
    "ጇ": "ǧʷa",
    "ገ": "gä", "ጉ": "gu", "ጊ": "gi", "ጋ": "ga", "ጌ": "ge", "ግ": "gə", "ጎ": "go",
    "ጐ": "gʷä", "ጒ": "gʷi", "ጓ": "gʷa", "ጔ": "gʷe", "ጕ": "gʷə",
    "ጘ": "ŋä", "ጙ": "ŋu", "ጚ": "ŋi", "ጛ": "ŋa", "ጜ": "ŋe", "ጝ": "ŋə", "ጞ": "ŋo",
    "ⶓ": "ŋʷä", "ⶔ": "ŋʷi", "ጟ": "ŋʷa", "ⶕ": "ŋʷe", "ⶖ": "ŋʷə",
    "ጠ": "ṭä", "ጡ": "ṭu", "ጢ": "ṭi", "ጣ": "ṭa", "ጤ": "ṭe", "ጥ": "ṭə", "ጦ": "ṭo",
    "ጧ": "ṭʷa",
    "ጨ": "č̣ä", "ጩ": "č̣u", "ጪ": "č̣i", "ጫ": "č̣a", "ጬ": "č̣e", "ጭ": "č̣ə", "ጮ": "č̣o",
    "ጯ": "č̣ʷa",
    "ጰ": "p̣ä", "ጱ": "p̣u", "ጲ": "p̣i", "ጳ": "p̣a", "ጴ": "p̣e", "ጵ": "p̣ə", "ጶ": "p̣o",
    "ጷ": "p̣ʷa",
    "ጸ": "ṣä", "ጹ": "ṣu", "ጺ": "ṣi", "ጻ": "ṣa", "ጼ": "ṣe", "ጽ": "ṣə", "ጾ": "ṣo",
    "ጿ": "ṣʷa",
    "ፀ": "ṣ́ä", "ፁ": "ṣ́u", "ፂ": "ṣ́i", "ፃ": "ṣ́a", "ፄ": "ṣ́e", "ፅ": "ṣ́ə", "ፆ": "ṣ́o",
    "ፈ": "fä", "ፉ": "fu", "ፊ": "fi", "ፋ": "fa", "ፌ": "fe", "ፍ": "fə", "ፎ": "fo",
    "ፏ": "fʷa", "ፚ": "fʲä",
    "ፐ": "pä", "ፑ": "pu", "ፒ": "pi", "ፓ": "pa", "ፔ": "pe", "ፕ": "pə", "ፖ": "po",
    "ፗ": "pʷa",
    # punctuation
    "፠": "§", "፡": " ", "።": ".", "፣": ",", "፤": ";", "፥": ":", "፦": ":-", "፧": "?", "፨": "¶",
}

NUMBER_MAP: dict[str, int] = {
    "፩": 1, "፪": 2, "፫": 3, "፬": 4, "፭": 5, "፮": 6, "፯": 7, "፰": 8, "፱": 9,
    "፲": 10, "፳": 20, "፴": 30, "፵": 40, "፶": 50, "፷": 60, "፸": 70, "፹": 80, "፺": 90,
}

# Entry-level gemination / WT lemma overrides (orthography alone under-geminates).
# Values match common Wiktionary Amharic headword transliterations.
KNOWN_GEMINATES: dict[str, str] = {
    "ቡና": "bunna",
    "እሱ": "ʾəssu",
    "እሷ": "ʾəsswa",
    "አንተ": "ʾantä",
    "አንቺ": "ʾanči",
    "እነሱ": "ʾənnässu",
    "እኛ": "ʾəñña",
    "እናንተ": "ʾənnantä",
}

# Consonant + optional labialization / underdot / acute / palatalization, then ə
_SCHWA_SYL = re.compile(
    r"([bdfghklmnprstvwxyzñčŋśšžǧʾʿḥḫḳṣṭ][ʲʷ̣́]*)ə"
)

_NUM_RUN = re.compile(r"[፩-፼]+")
_SPACE_PUNCT = re.compile(r"^[\s\W]", re.UNICODE)


def ethiopic_number(geez: str) -> int:
    """Port of Module:Ethi-translit ``export.number``."""
    val = 0
    if re.match(r"^[፻፼]", geez):
        geez = "፩" + geez
    geez = geez.replace("፼፻", "፼፩፻")
    geez = re.sub(r"፼([^፻፼]*)$", r"፼፻\1", geez)
    geez = re.sub(r"፼([^፻፼]*፼)", r"፼፻\1", geez)
    geez = re.sub(r"፼([^፻፼]*፼)", r"፼፻\1", geez)

    for digit in geez:
        if digit in NUMBER_MAP:
            val += NUMBER_MAP[digit]
        elif digit in ("፻", "፼"):
            val *= 100
    return val


def _apply_tt(text: str) -> str:
    return "".join(TT.get(ch, ch) for ch in text)


def _remove_non_initial_schwa(text: str) -> str:
    """Port of the Module:Ethi-translit ə-dropping pass."""
    prev_end_pos: int | None = None
    prev_schwa_removed = False
    text_len = len(text)
    out: list[str] = []
    pos = 0

    for match in _SCHWA_SYL.finditer(text):
        start_pos = match.start()
        end_pos = match.end()
        syllable = match.group(0)
        consonant = match.group(1)

        out.append(text[pos:start_pos])

        at_boundary = start_pos == 0 or bool(_SPACE_PUNCT.match(text[start_pos - 1]))
        keep_after_drop = (
            prev_end_pos == start_pos
            and prev_schwa_removed
            and not (
                end_pos == text_len
                or bool(_SPACE_PUNCT.match(text[end_pos : end_pos + 1] or ""))
            )
        )

        if at_boundary or keep_after_drop:
            ret = syllable
        else:
            ret = consonant

        prev_schwa_removed = ret == consonant
        prev_end_pos = end_pos
        out.append(ret)
        pos = end_pos

    out.append(text[pos:])
    return "".join(out)


def tr(text: str, lang: str | None = None, sc: str | None = None) -> str:
    """Port of Module:Ethi-translit ``export.tr`` (without known-lemma overrides)."""
    del lang, sc  # module signature compatibility
    text = unicodedata.normalize("NFC", text)

    # Remove gemination marks → internal Q…W markers (Lua: (.)GEM → Q%1W)
    text = re.sub(r"(.)" + GEM, r"Q\1W", text)

    text = _apply_tt(text)

    # Geminate consonants (keep ə before/after geminates via Ə)
    text = text.replace("Qx̣", "Vx̣x̣")
    text = text.replace("Qč̣", "Vč̣č̣")
    text = text.replace("Qp̣", "Vp̣p̣")
    text = text.replace("Qṣ́", "Vṣ́ṣ́")
    text = re.sub(r"Q(.)", r"V\1\1", text)
    text = re.sub(r"əW?V", "Ə", text)
    text = re.sub(
        r"əW([hlḥmśrsšḳxbvtčḫnñʾkxwʿzžydǧgṭṣfp])",
        r"Ə\1",
        text,
    )

    text = _remove_non_initial_schwa(text)
    text = _NUM_RUN.sub(lambda m: str(ethiopic_number(m.group(0))), text)
    text = text.replace("-ʾ", "-")
    text = text.replace("Ə", "ə")
    text = re.sub(r"[VW]", "", text)
    return text


def transliterate(text: str) -> str:
    """Wiktionary Ethi-translit string for display (with known geminate overrides)."""
    text = unicodedata.normalize("NFC", text.strip())
    if not text:
        return ""
    if text in KNOWN_GEMINATES:
        return KNOWN_GEMINATES[text]
    if ", " in text:
        return ", ".join(transliterate(part) for part in text.split(", "))
    if " " in text:
        return " ".join(transliterate(part) for part in text.split())
    return tr(text)


def romanize(text: str) -> str:
    """Alias used by course generators / build_static_web_data."""
    return transliterate(text)


_SELF_CHECK: list[tuple[str, str]] = [
    ("እኔ", "ʾəne"),
    ("ቤት", "bet"),
    ("መጽሐፍ", "mäṣḥäf"),
    ("ቡና", "bunna"),
    ("ሰላም", "sälam"),
    ("እንጀራ", "ʾənǧära"),
    ("ተማሪ", "tämari"),
    ("ጓደኛ", "gʷadäña"),
    ("ልጅ", "ləǧ"),
    ("ውሻ", "wəša"),
    ("ጥቁር", "ṭəḳur"),
    ("ፀሐይ", "ṣ́äḥäy"),
    ("እሱ", "ʾəssu"),
    ("አንተ", "ʾantä"),
    # gemination mark support (ብ + GEM + ና-style on ቡ)
    ("ቡ" + GEM + "ና", "bbuna"),
]


def self_check() -> None:
    failures: list[str] = []
    for geez, expected in _SELF_CHECK:
        got = transliterate(geez)
        if got != expected:
            failures.append(f"{geez!r}: expected {expected!r}, got {got!r}")
    if failures:
        raise SystemExit("self-check failed:\n  " + "\n  ".join(failures))
    print(f"ok: {len(_SELF_CHECK)} Ethi-translit cases")


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--self-check":
        self_check()
    elif not sys.stdin.isatty():
        items = json.load(sys.stdin)
        json.dump(
            [{"text": item, "transliteration": transliterate(str(item))} for item in items],
            sys.stdout,
            ensure_ascii=False,
        )
    else:
        self_check()
