#!/usr/bin/env python3
"""Offline MLCTS-to-Okell helper for the local Burmese corpora.

The converter is intentionally scoped to the beginner Burmese corpus.  It uses
the Okell values in Wiktionary's Burmese transliteration table for the regular
onset/rhyme mapping, then applies a small override table for common A1 words
whose spoken form is not transparent from the spelling.
"""

from __future__ import annotations

import re


BURMESE_RE = re.compile(r"[\u1000-\u109f]")
SYLLABLE_DOT_RE = re.compile(r"(?<=[A-Za-z])\.(?=[A-Za-z])")

WORD_OVERRIDES = {
    "မင်္ဂလာပါ": "miñgălapa",
    "ကျွန်တော်": "cuñto",
    "ကျွန်တော်က": "cuñto ká",
    "ကျွန်မ": "cuñmá",
    "ကျွန်မက": "cuñmá ká",
    "ကျမ": "cămá",
    "ငါ": "nga",
    "သူ": "thu",
    "သူက": "thu ká",
    "ဒီ": "di",
    "ရေ": "yei",
    "ရေက": "yei ká",
    "ရေကို": "yei kou",
    "ထမင်း": "htămìñ",
    "ထမင်းကို": "htămìñ kou",
    "စား": "sà",
    "စားတယ်": "sà te",
    "သောက်": "thauʔ",
    "သောက်တယ်": "thauʔ te",
    "တယ်": "te",
    "ပါတယ်": "ba de",
    "မယ်": "me",
    "ပါ": "ba",
    "က": "ká",
    "ကို": "kou",
    "မှာ": "hma",
    "နဲ့": "ne",
    "လို့": "lo",
    "သည်": "thi",
    "ရှိ": "hyí",
    "ရှိတယ်": "hyí te",
    "နေ": "nei",
    "သွား": "thwà",
    "သွားတယ်": "thwà te",
    "လာ": "la",
    "လာတယ်": "la te",
    "ဝယ်": "we",
    "ဝယ်တယ်": "we te",
    "ပေး": "pei",
    "ပေးတယ်": "pei te",
    "ဖွင့်": "hpwíñ",
    "ဖွင့်တယ်": "hpwíñ te",
    "ကြည့်": "ci",
    "ကြည့်တယ်": "ci te",
    "ဆရာ": "hsăya",
    "ဆရာမ": "hsăyamá",
    "ကလေး": "hkăleì",
    "ကလေးက": "hkăleì ká",
    "ကျောင်း": "caùñ",
    "ကျောင်းက": "caùñ ká",
    "ကျောင်းသား": "caùñthà",
    "ကျောင်းသူ": "caùñthu",
    "စာ": "sa",
    "စာအုပ်": "sa ouʔ",
    "အိမ်": "eiñ",
    "အိမ်မှာ": "eiñ hma",
    "အမေ": "ămei",
    "အမေက": "ămei ká",
    "အဖေ": "ăhpei",
    "အဖေက": "ăhpei ká",
    "မေမေ": "meimei",
    "ဖေဖေ": "hpeihpei",
    "လမ်း": "làñ",
    "ကား": "kà",
    "မိုး": "moù",
    "မိုးရွာ": "moùywa",
    "ရွာ": "ywa",
    "ဆိုင်": "hsaiñ",
    "ဈေး": "zei",
    "ပန်း": "pàñ",
    "လက်": "leʔ",
    "နား": "nà",
    "ဆေး": "hseì",
    "အိတ်": "eiʔ",
    "ခွက်": "hkwet",
    "တံခါး": "dăgà",
    "ပေါ်": "po",
    "ပေါ်မှာ": "po hma",
    "ထဲ": "hte",
    "ထဲမှာ": "hte hma",
    "ညနေ": "nyănei",
    "ဒီနေ့": "dinei",
    "နည်းနည်း": "neìneì",
    "မုန့်": "moúñ",
    "ဖုန်း": "hpòuñ",
    "လူ": "lu",
    "သူငယ်ချင်း": "thăngejìñ",
}

ONSETS = {
    "hkyw": "hcw",
    "hkrw": "hcw",
    "hngw": "hngw",
    "hnyw": "hnyw",
    "hpr": "hpy",
    "hpy": "hpy",
    "hmr": "hmy",
    "hmy": "hmy",
    "hly": "hly",
    "hrw": "hyw",
    "hkw": "hkw",
    "hky": "hc",
    "hkr": "hc",
    "hng": "hng",
    "hny": "hny",
    "hcw": "hsw",
    "hc": "hs",
    "hk": "hk",
    "hpw": "hpw",
    "hmw": "hmw",
    "hlw": "hlw",
    "hsy": "hy",
    "kyw": "cw",
    "krw": "cw",
    "ngw": "ngw",
    "nyw": "nyw",
    "prw": "pw",
    "mrw": "mw",
    "gyw": "jw",
    "bhw": "bw",
    "ky": "c",
    "kr": "c",
    "kw": "kw",
    "kh": "hk",
    "gy": "j",
    "gw": "gw",
    "gh": "g",
    "ng": "ng",
    "gr": "j",
    "gy": "j",
    "ny": "ny",
    "ht": "ht",
    "dh": "d",
    "hn": "hn",
    "nw": "nw",
    "py": "py",
    "pr": "py",
    "pw": "pw",
    "hp": "hp",
    "by": "by",
    "br": "by",
    "bw": "bw",
    "bh": "b",
    "hm": "hm",
    "my": "my",
    "mr": "my",
    "mw": "mw",
    "hy": "hy",
    "yw": "yw",
    "hr": "hy",
    "rw": "yw",
    "hl": "hl",
    "ly": "ly",
    "lw": "lw",
    "hw": "hw",
    "c": "s",
    "j": "z",
    "t": "t",
    "d": "d",
    "n": "n",
    "p": "p",
    "b": "b",
    "m": "m",
    "y": "y",
    "r": "y",
    "l": "l",
    "w": "w",
    "s": "th",
    "h": "h",
    "k": "k",
    "g": "g",
}

RHYMES = {
    "a.": "á",
    "a": "a",
    "a:": "à",
    "ak": "eʔ",
    "ac": "iʔ",
    "at": "aʔ",
    "ap": "aʔ",
    "ang": "iñ",
    "añ": "iñ",
    "an": "añ",
    "am": "añ",
    "any": "i",
    "ai": "e",
    "ai.": "é",
    "ai:": "è",
    "i.": "í",
    "i": "i",
    "i:": "ì",
    "ik": "eiʔ",
    "ic": "eiʔ",
    "it": "eiʔ",
    "ip": "eiʔ",
    "ing": "eiñ",
    "in": "eiñ",
    "im": "eiñ",
    "u.": "ú",
    "u": "u",
    "u:": "ù",
    "uk": "ouʔ",
    "uc": "ouʔ",
    "ut": "ouʔ",
    "up": "ouʔ",
    "ung": "ouñ",
    "un": "ouñ",
    "um": "ouñ",
    "e": "ei",
    "e.": "eí",
    "e:": "eì",
    "au": "o",
    "au.": "ó",
    "au:": "ò",
    "auk": "auʔ",
    "auc": "auʔ",
    "aut": "auʔ",
    "aup": "auʔ",
    "aung": "auñ",
    "aung.": "aúñ",
    "aung:": "aùñ",
    "aun": "auñ",
    "aum": "auñ",
    "ui": "ou",
    "ui.": "óu",
    "ui:": "où",
    "uik": "aiʔ",
    "uic": "aiʔ",
    "uit": "aiʔ",
    "uip": "aiʔ",
    "uing": "aiñ",
    "uin": "aiñ",
    "uim": "aiñ",
    "o": "o",
    "o.": "ó",
    "o:": "ò",
}

ONSET_KEYS = sorted(ONSETS, key=len, reverse=True)


def romanize(word: str, mlcts: str | None = None) -> str:
    """Return an Okell transcription for a Burmese corpus token."""

    word = (word or "").strip()
    if word in WORD_OVERRIDES:
        return WORD_OVERRIDES[word]
    if not mlcts:
        return ""
    return romanize_mlcts(mlcts)


def romanize_mlcts(mlcts: str) -> str:
    mlcts = normalize_mlcts(mlcts)
    if not mlcts:
        return ""

    words = []
    for chunk in mlcts.split():
        syllables = [part for part in re.split(r"[-+]", chunk) if part]
        converted = [
            romanize_syllable(part, index + 1 < len(syllables))
            for index, part in enumerate(syllables)
        ]
        words.append("".join(part for part in converted if part))
    return " ".join(part for part in words if part).strip()


def normalize_mlcts(mlcts: str) -> str:
    text = str(mlcts).strip().lower()
    text = text.replace("’", "'").replace("`", "'")
    text = text.strip("/")
    text = SYLLABLE_DOT_RE.sub(" ", text)
    text = re.sub(r"[^a-zñ.:+\-'\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def romanize_syllable(syllable: str, followed_by_syllable: bool = False) -> str:
    raw = syllable.strip(" '")
    if not raw:
        return ""

    onset = ""
    rhyme = raw
    for candidate in ONSET_KEYS:
        if raw.startswith(candidate) and len(candidate) > len(onset):
            onset = candidate
            rhyme = raw[len(candidate) :]
            break

    okell_onset = ONSETS.get(onset, onset)
    okell_rhyme = RHYMES.get(rhyme)
    if okell_rhyme is None:
        okell_rhyme = fallback_rhyme(rhyme)

    if followed_by_syllable and okell_rhyme in {"a", "á"}:
        okell_rhyme = "ă"
    return f"{okell_onset}{okell_rhyme}"


def fallback_rhyme(rhyme: str) -> str:
    if not rhyme:
        return ""
    value = rhyme
    value = value.replace(":", "̀")
    value = value.replace(".", "́")
    value = value.replace("ng", "ñ")
    value = value.replace("ny", "ñ")
    return value


def has_burmese(text: str) -> bool:
    return bool(BURMESE_RE.search(text or ""))
