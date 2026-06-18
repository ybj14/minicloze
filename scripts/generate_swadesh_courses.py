#!/usr/bin/env python3
"""Generate local Swadesh courses for the bundled minicloze languages.

The vocabulary seed comes from Wiktionary Swadesh data. Sentences are original
local course material generated from varied A1 frames, not copied examples.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

from thai_paiboon import romanize as romanize_thai_paiboon


ROOT = Path(__file__).resolve().parents[1]
CORPORA = ROOT / "minicloze-lib" / "corpora"
GENERATED = CORPORA / "generated"
USER_AGENT = {"User-Agent": "minicloze-swadesh-course-builder/1.0"}

LANGS = {
    "mongolian": {"code": "mn", "id_start": -500000, "base": "mon"},
    "tibetan": {"code": "bo", "id_start": -600000, "base": "bod"},
    "tajik": {"code": "tg", "id_start": -700000, "base": "tgk"},
    "thai": {"code": "th", "id_start": -800000, "base": "tha"},
}


@dataclass(frozen=True)
class Concept:
    index: int
    gloss: str


@dataclass(frozen=True)
class VocabItem:
    index: int
    word: str
    gloss: str
    source: str


def fetch_text(url: str) -> str:
    with urlopen(Request(url, headers=USER_AGENT), timeout=30) as response:
        return response.read().decode("utf-8")


def parse_swadesh_module(code: str) -> dict[int, list[str]]:
    text = fetch_text(f"https://en.wiktionary.org/wiki/Module:Swadesh/data/{code}?action=raw")
    rows: dict[int, list[str]] = {}
    for match in re.finditer(r"m\[(\d+)\]\s*=\s*(.*)", text):
        index = int(match.group(1))
        terms = re.findall(r'term\s*=\s*"([^"]+)"', match.group(2))
        if terms:
            rows[index] = terms
    return rows


def parse_thai_swadesh() -> dict[int, list[str]]:
    text = fetch_text(
        "https://en.wiktionary.org/w/index.php?title=Appendix:Thai_Swadesh_list&action=raw"
    )
    rows: dict[int, list[str]] = {}
    for block in text.split("|-"):
        number_match = re.search(r"\|i=No\|\s*(\d+)", block)
        if not number_match:
            continue
        target_match = re.search(r"\|c=01\|\s*(.*?)(?=\n\|c=02\||\n\|-|\Z)", block, re.S)
        if not target_match:
            continue
        links = re.findall(r"\[\[([^|\]#]+)(?:#[^|\]]+)?(?:\|[^\]]*)?\]\]", target_match.group(1))
        if links:
            rows[int(number_match.group(1))] = [clean_term(link) for link in links]
    return rows


def clean_term(term: str) -> str:
    return re.sub(r"\s+", " ", term).strip().strip("་།")


MONGOLIAN_OVERRIDES = {
    6: "тэд",
    16: "биш",
    36: "эмэгтэй",
    37: "эрэгтэй",
    99: "амьсгалах",
    184: "хуучин",
    192: "мохоо",
    201: "дээр",
    203: "хамт",
    204: "болон",
    206: "яагаад гэвэл",
}

TAJIK_OVERRIDES = {
    16: "не",
    204: "ва",
}

THAI_OVERRIDES = {
    2: "คุณ",
    7: "นี่",
    8: "นั่น",
    20: "น้อย",
    36: "ผู้หญิง",
    37: "ผู้ชาย",
    38: "คน",
    47: "สุนัข",
    66: "ไขมัน",
    201: "ที่",
    202: "ใน",
    203: "กับ",
    204: "และ",
    205: "ถ้า",
    206: "เพราะ",
}

TIBETAN_OVERRIDES = {
    6: "ཁོང་ཚོ",
    9: "འདིར",
    10: "དེར",
    15: "ག་འདྲ",
    16: "མ",
    20: "ཉུང་ཉུང",
    21: "གཞན",
    27: "ཆེན་པོ",
    32: "ཆུང་ཆུང",
    33: "ཐུང་ཐུང",
    34: "དོག་པོ",
    35: "སྲབ་མོ",
    36: "བུད་མེད",
    37: "སྐྱེས་པ",
    39: "ཕྲུ་གུ",
    43: "པ་ཕ",
    46: "བྱ",
    50: "འབུ",
    51: "ཤིང",
    53: "དབྱུག་པ",
    55: "ས་བོན",
    56: "ལོ་མ",
    57: "རྩ་བ",
    58: "ཤུན་པ",
    62: "པགས་པ",
    64: "ཁྲག",
    65: "རུས་པ",
    66: "ཚིལ",
    69: "མཇུག་མ",
    70: "སྒྲོ",
    73: "རྣ་བ",
    75: "སྣ",
    78: "ལྕེ",
    82: "པུས་མོ",
    84: "གཤོག་པ",
    85: "གྲོད་པ",
    89: "བྲང",
    90: "སྙིང",
    95: "འཇིབ",
    96: "མཆིལ་མ་གཏོར",
    108: "སྡོད",
    111: "འཐབ",
    112: "རྔོན",
    114: "གཏུབ",
    115: "གཤག",
    116: "བཙུག",
    117: "འབྲད",
    118: "བརྐོ",
    119: "ཆུ་རྐྱལ་རྒྱག",
    123: "ཉལ",
    126: "འཁོར",
    127: "ལྷུང",
    129: "འཛིན",
    130: "བཙིར",
    131: "བརྡར",
    132: "བཀྲུ",
    133: "ཕྱི",
    134: "འཐེན",
    135: "འདེད",
    139: "རྩི",
    140: "ཟེར",
    141: "གླུ་ལེན",
    143: "འཕྱོ",
    144: "འབབ",
    145: "འཁྱག",
    146: "སྐྲང",
    161: "སྨུག་པ",
    163: "རླུང",
    165: "འཁྱགས་པ",
    168: "ཐལ་བ",
    169: "འབར",
    173: "ལྗང་ཁུ",
    178: "ཉིན",
    182: "ཁེངས་པ",
    189: "དྲང་པོ",
    192: "རྟུལ་པོ",
    193: "འཇམ་པོ",
    196: "འགྲིག",
}

OVERRIDES = {
    "mongolian": MONGOLIAN_OVERRIDES,
    "tibetan": TIBETAN_OVERRIDES,
    "tajik": TAJIK_OVERRIDES,
    "thai": THAI_OVERRIDES,
}


HELPERS = {
    "mongolian": {
        "i": ("Би", "I"),
        "i_erg": ("Би", "I"),
        "you": ("Та", "you"),
        "child": ("Хүүхэд", "child"),
        "teacher": ("Багш", "teacher"),
        "mother": ("Ээж", "mother"),
        "friend": ("Найз", "friend"),
        "today": ("Өнөөдөр", "today"),
        "here": ("энд", "here"),
        "there": ("тэнд", "there"),
        "this": ("Энэ", "this"),
        "that": ("Тэр", "that"),
        "see": ("харлаа", "saw"),
        "is": ("байна", "is"),
        "draw": ("зурлаа", "drew"),
        "bag": ("цүнх", "bag"),
        "road": ("зам", "road"),
        "room": ("өрөөн", "room"),
        "home": ("гэрт", "at home"),
        "tea": ("цай", "tea"),
        "food": ("хоол", "food"),
        "cup": ("аяга", "cup"),
        "table": ("ширээн", "table"),
        "on": ("дээр", "on"),
        "in": ("дотор", "inside"),
        "like": ("дуртай", "like"),
        "no": ("болохгүй", "not allowed"),
        "learn": ("сурч", "learning"),
        "came": ("ирсэн", "came"),
        "book": ("Ном", "book"),
        "go": ("явах", "go"),
        "water": ("ус", "water"),
        "drink": ("ууж", "drinking"),
        "hot": ("халуун", "hot"),
    },
    "tajik": {
        "i": ("Ман", "I"),
        "you": ("Шумо", "you"),
        "child": ("Кӯдак", "child"),
        "teacher": ("Омӯзгор", "teacher"),
        "mother": ("Модар", "mother"),
        "friend": ("Дӯст", "friend"),
        "today": ("Имрӯз", "today"),
        "here": ("инҷо", "here"),
        "there": ("онҷо", "there"),
        "this": ("Ин", "this"),
        "that": ("Он", "that"),
        "see": ("дид", "saw"),
        "i_saw": ("дидам", "I saw"),
        "is": ("аст", "is"),
        "draw": ("кашид", "drew"),
        "bag": ("халта", "bag"),
        "road": ("роҳ", "road"),
        "room": ("хона", "room"),
        "home": ("хона", "home"),
        "tea": ("чой", "tea"),
        "food": ("хӯрок", "food"),
        "cup": ("пиёла", "cup"),
        "table": ("миз", "table"),
        "on": ("дар", "in; at"),
        "in": ("дар", "in"),
        "like": ("дӯст", "like"),
        "have": ("дорам", "I have"),
        "no": ("мумкин", "possible"),
        "not": ("нест", "is not"),
        "learn": ("меомӯзад", "learns"),
        "came": ("омад", "came"),
        "book": ("Китоб", "book"),
        "go": ("меравад", "goes"),
        "go_i": ("меравам", "I go"),
        "water": ("об", "water"),
        "drink": ("менӯшад", "drinks"),
        "drink_i": ("менӯшам", "I drink"),
        "hot": ("гарм", "hot"),
    },
    "thai": {
        "i": ("ฉัน", "I"),
        "you": ("คุณ", "you"),
        "child": ("เด็ก", "child"),
        "teacher": ("ครู", "teacher"),
        "mother": ("แม่", "mother"),
        "friend": ("เพื่อน", "friend"),
        "today": ("วันนี้", "today"),
        "here": ("ที่นี่", "here"),
        "there": ("ที่นั่น", "there"),
        "this": ("นี่", "this"),
        "that": ("นั่น", "that"),
        "see": ("เห็น", "see"),
        "is": ("อยู่", "be; stay"),
        "draw": ("วาด", "draw"),
        "bag": ("กระเป๋า", "bag"),
        "road": ("ถนน", "road"),
        "room": ("ห้อง", "room"),
        "home": ("บ้าน", "home"),
        "tea": ("ชา", "tea"),
        "food": ("อาหาร", "food"),
        "cup": ("แก้ว", "cup"),
        "table": ("โต๊ะ", "table"),
        "on": ("บน", "on"),
        "in": ("ใน", "in"),
        "like": ("ชอบ", "like"),
        "no": ("ห้าม", "must not"),
        "learn": ("เรียน", "learn"),
        "came": ("มา", "come"),
        "book": ("หนังสือ", "book"),
        "go": ("ไป", "go"),
        "water": ("น้ำ", "water"),
        "drink": ("ดื่ม", "drink"),
        "hot": ("ร้อน", "hot"),
    },
    "tibetan": {
        "i": ("ང", "I"),
        "i_erg": ("ངས", "I (ergative)"),
        "you": ("ཁྱེད", "you"),
        "child": ("ཕྲུ་གུ", "child"),
        "child_erg": ("ཕྲུ་གུས", "child (ergative)"),
        "teacher": ("དགེ་རྒན", "teacher"),
        "mother": ("ཨ་མ", "mother"),
        "friend": ("གྲོགས་པོ", "friend"),
        "today": ("དེ་རིང", "today"),
        "here": ("འདིར", "here"),
        "there": ("དེར", "there"),
        "this": ("འདི", "this"),
        "that": ("དེ", "that"),
        "see": ("མཐོང", "see"),
        "is": ("རེད", "is"),
        "exists": ("ཡོད", "is; exists"),
        "draw": ("བྲིས", "drew"),
        "bag": ("ཁུག་མ", "bag"),
        "road": ("ལམ", "road"),
        "room": ("ཁང་པ", "room"),
        "home": ("ནང", "home"),
        "tea": ("ཇ", "tea"),
        "food": ("ཟས", "food"),
        "cup": ("ཕོར་པ", "cup"),
        "table": ("ཅོག་ཙེ", "table"),
        "on": ("སྒང་ལ", "on"),
        "in": ("ནང་ལ", "in"),
        "like": ("དགའ", "like"),
        "no": ("མི་ཆོག", "not allowed"),
        "learn": ("སྦྱོང", "learn"),
        "came": ("ཡོང", "came"),
        "book": ("དེབ", "book"),
        "go": ("འགྲོ", "go"),
        "water": ("ཆུ", "water"),
        "drink": ("འཐུང", "drink"),
        "hot": ("ཚ་པོ", "hot"),
    },
}


def load_concepts() -> list[Concept]:
    english = parse_swadesh_module("en")
    return [Concept(index=i, gloss=english[i][0].lower()) for i in range(1, 208)]


def load_seed_terms() -> dict[str, dict[int, list[str]]]:
    return {
        "mongolian": parse_swadesh_module("mn"),
        "tibetan": parse_swadesh_module("bo"),
        "tajik": parse_swadesh_module("tg"),
        "thai": parse_thai_swadesh(),
    }


def choose_word(language: str, index: int, seed_terms: dict[int, list[str]]) -> tuple[str, str]:
    override = OVERRIDES.get(language, {}).get(index)
    if override:
        return override, "Wiktionary Swadesh 207; local A1 correction"
    terms = seed_terms.get(index, [])
    if not terms:
        raise ValueError(f"{language}: missing Swadesh item {index}")
    return clean_term(terms[0]), "Wiktionary Swadesh 207"


def classify(index: int) -> str:
    if index in range(1, 7):
        return "pronoun"
    if index in range(11, 16):
        return "question"
    if index in {7, 8, 9, 10}:
        return "deictic"
    if index == 16:
        return "negative"
    if index in range(17, 27):
        return "quantity"
    if index in set(range(27, 36)) | set(range(172, 199)):
        return "adjective"
    if index in set(range(92, 147)) | {169}:
        return "verb"
    if index in range(201, 207):
        return "function"
    return "noun"


def h(language: str, key: str) -> dict[str, str]:
    word, gloss = HELPERS[language][key]
    return explain(word, gloss, language)


def explain(word: str, gloss: str, language: str, note: str | None = None) -> dict[str, str]:
    item = {"word": word, "gloss": gloss}
    if note:
        item["note"] = note
    if language == "thai":
        paiboon = romanize_thai_paiboon(word)
        if paiboon.strip():
            item["paiboon"] = paiboon
    return item


def target(vocab: VocabItem, language: str) -> dict[str, str]:
    return explain(vocab.word, vocab.gloss, language, "Swadesh target")


def sentence(language: str, tokens: list[dict[str, str]], english: str) -> dict[str, object]:
    if language == "thai":
        target_text = "".join(token["word"] for token in tokens)
    elif language == "tibetan":
        target_text = "".join(tibetan_piece(token["word"]) for token in tokens).rstrip("་") + "།"
    else:
        target_text = " ".join(token["word"] for token in tokens) + "."
    return {
        "target": target_text,
        "text": english,
        "words": tokens,
    }


def tibetan_piece(word: str) -> str:
    return word if word.endswith(("།", "་")) else f"{word}་"


def choose_three(frames: list[dict[str, object]], index: int) -> list[dict[str, object]]:
    offset = (index - 1) % len(frames)
    chosen = []
    for step in range(3):
        chosen.append(frames[(offset + step) % len(frames)])
    return chosen


def noun_sentences(language: str, vocab: VocabItem) -> list[dict[str, object]]:
    g = vocab.gloss
    if language == "tajik":
        frames = [
            sentence(language, [h(language, "i"), target(vocab, language), h(language, "i_saw")], f"I saw the {g}."),
            sentence(language, [target(vocab, language), h(language, "here"), h(language, "is")], f"The {g} is here."),
            sentence(language, [h(language, "child"), target(vocab, language), h(language, "draw")], f"The child drew the {g}."),
            sentence(language, [h(language, "teacher"), target(vocab, language), h(language, "there"), h(language, "see")], f"The teacher saw the {g} there."),
            sentence(language, [h(language, "today"), target(vocab, language), h(language, "here"), h(language, "is")], f"The {g} is here today."),
            sentence(language, [h(language, "mother"), target(vocab, language), h(language, "see")], f"Mother sees the {g}."),
        ]
        return choose_three(frames, vocab.index)
    if language == "thai":
        frames = [
            sentence(language, [h(language, "i"), h(language, "see"), target(vocab, language)], f"I saw the {g}."),
            sentence(language, [target(vocab, language), h(language, "is"), h(language, "here")], f"The {g} is here."),
            sentence(language, [h(language, "child"), h(language, "draw"), target(vocab, language)], f"The child drew the {g}."),
            sentence(language, [h(language, "teacher"), h(language, "see"), target(vocab, language), h(language, "there")], f"The teacher saw the {g} there."),
            sentence(language, [h(language, "today"), target(vocab, language), h(language, "is"), h(language, "here")], f"The {g} is here today."),
            sentence(language, [h(language, "mother"), h(language, "see"), target(vocab, language)], f"Mother sees the {g}."),
        ]
        return choose_three(frames, vocab.index)
    frames = [
        sentence(language, [h(language, "i_erg") if language == "tibetan" else h(language, "i"), target(vocab, language), h(language, "see")], f"I saw the {g}."),
        sentence(language, [target(vocab, language), h(language, "here"), h(language, "is" if language != "tibetan" else "exists")], f"The {g} is here."),
        sentence(language, [h(language, "child_erg") if language == "tibetan" else h(language, "child"), target(vocab, language), h(language, "draw")], f"The child drew the {g}."),
        sentence(language, [h(language, "teacher"), target(vocab, language), h(language, "there"), h(language, "see")], f"The teacher saw the {g} there."),
        sentence(language, [h(language, "today"), target(vocab, language), h(language, "here"), h(language, "is" if language != "tibetan" else "exists")], f"The {g} is here today."),
        sentence(language, [h(language, "mother"), target(vocab, language), h(language, "see")], f"Mother sees the {g}."),
    ]
    return choose_three(frames, vocab.index)


def adjective_sentences(language: str, vocab: VocabItem) -> list[dict[str, object]]:
    g = vocab.gloss
    if language == "tajik":
        frames = [
            sentence(language, [h(language, "this"), h(language, "bag"), target(vocab, language), h(language, "is")], f"This bag is {g}."),
            sentence(language, [h(language, "today"), h(language, "road"), target(vocab, language), h(language, "is")], f"The road is {g} today."),
            sentence(language, [h(language, "cup"), target(vocab, language), h(language, "on"), h(language, "table"), h(language, "is")], f"The {g} cup is on the table."),
            sentence(language, [h(language, "that"), h(language, "room"), target(vocab, language), h(language, "is")], f"That room is {g}."),
            sentence(language, [h(language, "tea"), target(vocab, language), h(language, "in"), h(language, "cup"), h(language, "is")], f"The {g} tea is in the cup."),
            sentence(language, [h(language, "this"), h(language, "food"), target(vocab, language), h(language, "is")], f"This food is {g}."),
        ]
        return choose_three(frames, vocab.index)
    if language == "thai":
        frames = [
            sentence(language, [h(language, "bag"), h(language, "this"), target(vocab, language)], f"This bag is {g}."),
            sentence(language, [h(language, "today"), h(language, "road"), target(vocab, language)], f"The road is {g} today."),
            sentence(language, [h(language, "cup"), target(vocab, language), h(language, "is"), h(language, "on"), h(language, "table")], f"The {g} cup is on the table."),
            sentence(language, [h(language, "room"), h(language, "that"), target(vocab, language)], f"That room is {g}."),
            sentence(language, [h(language, "tea"), target(vocab, language), h(language, "is"), h(language, "in"), h(language, "cup")], f"The {g} tea is in the cup."),
            sentence(language, [h(language, "food"), h(language, "this"), target(vocab, language)], f"This food is {g}."),
        ]
        return choose_three(frames, vocab.index)
    frames = [
        sentence(language, [h(language, "this"), h(language, "bag"), target(vocab, language), h(language, "is")], f"This bag is {g}."),
        sentence(language, [h(language, "today"), h(language, "road"), target(vocab, language), h(language, "is")], f"The road is {g} today."),
        sentence(language, [target(vocab, language), h(language, "cup"), h(language, "table"), h(language, "on"), h(language, "is" if language != "tibetan" else "exists")], f"The {g} cup is on the table."),
        sentence(language, [h(language, "that"), h(language, "room"), target(vocab, language), h(language, "is")], f"That room is {g}."),
        sentence(language, [target(vocab, language), h(language, "tea"), h(language, "cup"), h(language, "in"), h(language, "is" if language != "tibetan" else "exists")], f"The {g} tea is in the cup."),
        sentence(language, [h(language, "this"), h(language, "food"), target(vocab, language), h(language, "is")], f"This food is {g}."),
    ]
    return choose_three(frames, vocab.index)


def verb_sentences(language: str, vocab: VocabItem) -> list[dict[str, object]]:
    g = vocab.gloss
    if language == "tajik":
        frames = [
            sentence(language, [h(language, "i"), target(vocab, language), h(language, "like"), h(language, "have")], f"I like to {g}."),
            sentence(language, [h(language, "here"), target(vocab, language), h(language, "no"), h(language, "not")], f"It is not allowed to {g} here."),
            sentence(language, [h(language, "child"), target(vocab, language), h(language, "learn")], f"The child is learning to {g}."),
            sentence(language, [h(language, "friend"), target(vocab, language), h(language, "learn")], f"My friend is learning to {g}."),
            sentence(language, [h(language, "today"), h(language, "i"), target(vocab, language), h(language, "like"), h(language, "have")], f"Today I like to {g}."),
            sentence(language, [h(language, "home"), target(vocab, language), h(language, "no"), h(language, "not")], f"It is not allowed to {g} at home."),
        ]
        return choose_three(frames, vocab.index)
    if language == "thai":
        frames = [
            sentence(language, [h(language, "i"), h(language, "like"), target(vocab, language)], f"I like to {g}."),
            sentence(language, [h(language, "here"), h(language, "no"), target(vocab, language)], f"Do not {g} here."),
            sentence(language, [h(language, "child"), h(language, "learn"), target(vocab, language)], f"The child is learning to {g}."),
            sentence(language, [h(language, "friend"), h(language, "learn"), target(vocab, language)], f"My friend is learning to {g}."),
            sentence(language, [h(language, "today"), h(language, "i"), h(language, "like"), target(vocab, language)], f"Today I like to {g}."),
            sentence(language, [h(language, "home"), h(language, "no"), target(vocab, language)], f"Do not {g} at home."),
        ]
        return choose_three(frames, vocab.index)
    frames = [
        sentence(language, [h(language, "i"), target(vocab, language), h(language, "like")], f"I like to {g}."),
        sentence(language, [h(language, "here"), target(vocab, language), h(language, "no")], f"Do not {g} here."),
        sentence(language, [h(language, "child"), target(vocab, language), h(language, "learn"), h(language, "is" if language != "tibetan" else "exists")], f"The child is learning to {g}."),
        sentence(language, [h(language, "friend"), target(vocab, language), h(language, "learn"), h(language, "is" if language != "tibetan" else "exists")], f"My friend is learning to {g}."),
        sentence(language, [h(language, "today"), h(language, "i"), target(vocab, language), h(language, "like")], f"Today I like to {g}."),
        sentence(language, [h(language, "home"), target(vocab, language), h(language, "no")], f"Do not {g} at home."),
    ]
    return choose_three(frames, vocab.index)


def pronoun_sentences(language: str, vocab: VocabItem) -> list[dict[str, object]]:
    subjects = {
        1: ("I", "me", "I am"),
        2: ("You", "you", "You are"),
        3: ("He", "him", "He is"),
        4: ("We", "us", "We are"),
        5: ("You all", "you all", "You all are"),
        6: ("They", "them", "They are"),
    }
    subject, obj, be = subjects.get(vocab.index, (vocab.gloss.title(), vocab.gloss, f"{vocab.gloss.title()} is"))
    if language == "thai":
        return [
            sentence(language, [target(vocab, language), h(language, "is"), h(language, "here")], f"{be} here."),
            sentence(language, [h(language, "teacher"), h(language, "see"), target(vocab, language)], f"The teacher saw {obj}."),
            sentence(language, [target(vocab, language), h(language, "drink"), h(language, "water")], f"{be} drinking water."),
        ]
    if language == "tajik":
        drink = h(language, "drink_i") if vocab.index == 1 else h(language, "drink")
        return [
            sentence(language, [target(vocab, language), h(language, "here"), h(language, "is")], f"{be} here."),
            sentence(language, [h(language, "teacher"), target(vocab, language), h(language, "see")], f"The teacher saw {obj}."),
            sentence(language, [target(vocab, language), h(language, "water"), drink], f"{be} drinking water."),
        ]
    return [
        sentence(language, [target(vocab, language), h(language, "here"), h(language, "is" if language != "tibetan" else "exists")], f"{be} here."),
        sentence(language, [h(language, "teacher"), target(vocab, language), h(language, "see")], f"The teacher saw {obj}."),
        sentence(language, [target(vocab, language), h(language, "water"), h(language, "drink"), h(language, "is" if language != "tibetan" else "exists")], f"{be} drinking water."),
    ]


def question_sentences(language: str, vocab: VocabItem) -> list[dict[str, object]]:
    g = vocab.gloss
    if language == "thai":
        return [
            sentence(language, [target(vocab, language), h(language, "came")], f"{g.title()} came?"),
            sentence(language, [h(language, "book"), h(language, "is"), target(vocab, language)], f"{g.title()} is the book?"),
            sentence(language, [h(language, "you"), h(language, "go"), target(vocab, language)], f"{g.title()} will you go?"),
        ]
    return [
        sentence(language, [target(vocab, language), h(language, "came")], f"{g.title()} came?"),
        sentence(language, [h(language, "book"), target(vocab, language), h(language, "is" if language != "tibetan" else "exists")], f"{g.title()} is the book?"),
        sentence(language, [h(language, "you"), target(vocab, language), h(language, "go")], f"{g.title()} will you go?"),
    ]


def deictic_sentences(language: str, vocab: VocabItem) -> list[dict[str, object]]:
    g = vocab.gloss
    if language == "thai":
        return [
            sentence(language, [h(language, "book"), h(language, "is"), target(vocab, language)], f"The book is {g}."),
            sentence(language, [h(language, "mother"), h(language, "came"), target(vocab, language)], f"Mother came {g}."),
            sentence(language, [h(language, "child"), h(language, "see"), target(vocab, language)], f"The child sees {g}."),
        ]
    return [
        sentence(language, [target(vocab, language), h(language, "book"), h(language, "is" if language != "tibetan" else "exists")], f"The book is {g}."),
        sentence(language, [h(language, "mother"), target(vocab, language), h(language, "came")], f"Mother came {g}."),
        sentence(language, [h(language, "child"), target(vocab, language), h(language, "see")], f"The child sees {g}."),
    ]


def negative_sentences(language: str, vocab: VocabItem) -> list[dict[str, object]]:
    if language == "thai":
        return [
            sentence(language, [h(language, "water"), target(vocab, language), h(language, "hot")], "This water is not hot."),
            sentence(language, [h(language, "child"), target(vocab, language), h(language, "came")], "The child did not come."),
            sentence(language, [h(language, "i"), target(vocab, language), h(language, "go")], "I will not go."),
        ]
    return [
        sentence(language, [h(language, "this"), h(language, "water"), target(vocab, language), h(language, "hot")], "This water is not hot."),
        sentence(language, [h(language, "child"), target(vocab, language), h(language, "came")], "The child did not come."),
        sentence(language, [h(language, "i"), target(vocab, language), h(language, "go")], "I will not go."),
    ]


def quantity_sentences(language: str, vocab: VocabItem) -> list[dict[str, object]]:
    g = vocab.gloss
    if language == "thai":
        return [
            sentence(language, [h(language, "teacher"), h(language, "see"), target(vocab, language), h(language, "book")], f"The teacher saw {g} book(s)."),
            sentence(language, [target(vocab, language), h(language, "cup"), h(language, "is"), h(language, "on"), h(language, "table")], f"{g.title()} cup(s) are on the table."),
            sentence(language, [h(language, "child"), h(language, "drink"), target(vocab, language), h(language, "water")], f"The child drinks {g} water."),
        ]
    return [
        sentence(language, [h(language, "teacher"), target(vocab, language), h(language, "book"), h(language, "see")], f"The teacher saw {g} book(s)."),
        sentence(language, [target(vocab, language), h(language, "cup"), h(language, "table"), h(language, "on"), h(language, "is" if language != "tibetan" else "exists")], f"{g.title()} cup(s) are on the table."),
        sentence(language, [h(language, "child"), target(vocab, language), h(language, "water"), h(language, "drink")], f"The child drinks {g} water."),
    ]


def function_sentences(language: str, vocab: VocabItem) -> list[dict[str, object]]:
    i = vocab.index
    if language == "tajik":
        if i == 201:
            return [
                sentence(language, [h(language, "i"), target(vocab, language), h(language, "home"), h(language, "go_i")], "I go to the house."),
                sentence(language, [h(language, "teacher"), target(vocab, language), h(language, "room"), h(language, "came")], "The teacher came to the room."),
                sentence(language, [h(language, "friend"), target(vocab, language), h(language, "table"), h(language, "came")], "My friend came to the table."),
            ]
        if i == 202:
            return [
                sentence(language, [h(language, "water"), target(vocab, language), h(language, "cup"), h(language, "is")], "The water is in the cup."),
                sentence(language, [h(language, "book"), target(vocab, language), h(language, "bag"), h(language, "is")], "The book is in the bag."),
                sentence(language, [h(language, "child"), target(vocab, language), h(language, "room"), h(language, "is")], "The child is in the room."),
            ]
        if i == 203:
            return [
                sentence(language, [h(language, "i"), target(vocab, language), h(language, "mother"), h(language, "go_i")], "I go with mother."),
                sentence(language, [h(language, "teacher"), target(vocab, language), h(language, "child"), h(language, "came")], "The teacher came with the child."),
                sentence(language, [h(language, "friend"), target(vocab, language), h(language, "i"), h(language, "tea"), h(language, "drink")], "My friend drinks tea with me."),
            ]
        if i == 204:
            return [
                sentence(language, [h(language, "water"), target(vocab, language), h(language, "cup"), h(language, "here"), h(language, "is")], "Water and a cup are here."),
                sentence(language, [h(language, "mother"), target(vocab, language), h(language, "child"), h(language, "came")], "Mother and the child came."),
                sentence(language, [h(language, "tea"), target(vocab, language), h(language, "food"), h(language, "on"), h(language, "table"), h(language, "is")], "Tea and food are on the table."),
            ]
        if i == 205:
            return [
                sentence(language, [target(vocab, language), h(language, "water"), h(language, "hot"), h(language, "i"), h(language, "drink_i")], "If the water is hot, I drink."),
                sentence(language, [target(vocab, language), h(language, "teacher"), h(language, "came"), h(language, "child"), h(language, "learn")], "If the teacher comes, the child learns."),
                sentence(language, [target(vocab, language), h(language, "book"), h(language, "here"), h(language, "i"), h(language, "i_saw")], "If the book is here, I see it."),
            ]
        return [
            sentence(language, [h(language, "i"), h(language, "water"), h(language, "drink_i"), target(vocab, language), h(language, "hot"), h(language, "is")], "I drink water because it is hot."),
            sentence(language, [h(language, "child"), h(language, "home"), h(language, "came"), target(vocab, language), h(language, "mother"), h(language, "there"), h(language, "is")], "The child came home because mother is there."),
            sentence(language, [h(language, "teacher"), h(language, "book"), h(language, "see"), target(vocab, language), h(language, "book"), h(language, "on"), h(language, "table"), h(language, "is")], "The teacher sees the book because it is on the table."),
        ]
    if language == "thai":
        if i == 201:
            return [
                sentence(language, [h(language, "book"), h(language, "is"), target(vocab, language), h(language, "table")], "The book is at the table."),
                sentence(language, [h(language, "cup"), h(language, "is"), target(vocab, language), h(language, "table")], "The cup is at the table."),
                sentence(language, [h(language, "child"), h(language, "is"), target(vocab, language), h(language, "room")], "The child is at the room."),
            ]
        if i == 202:
            return [
                sentence(language, [h(language, "water"), h(language, "is"), target(vocab, language), h(language, "cup")], "The water is in the cup."),
                sentence(language, [h(language, "book"), h(language, "is"), target(vocab, language), h(language, "bag")], "The book is in the bag."),
                sentence(language, [h(language, "child"), h(language, "is"), target(vocab, language), h(language, "room")], "The child is in the room."),
            ]
        if i == 203:
            return [
                sentence(language, [h(language, "i"), h(language, "go"), target(vocab, language), h(language, "mother")], "I go with mother."),
                sentence(language, [h(language, "teacher"), h(language, "came"), target(vocab, language), h(language, "child")], "The teacher came with the child."),
                sentence(language, [h(language, "friend"), h(language, "drink"), h(language, "tea"), target(vocab, language), h(language, "i")], "My friend drinks tea with me."),
            ]
        if i == 204:
            return [
                sentence(language, [h(language, "water"), target(vocab, language), h(language, "cup"), h(language, "is"), h(language, "here")], "Water and a cup are here."),
                sentence(language, [h(language, "mother"), target(vocab, language), h(language, "child"), h(language, "came")], "Mother and the child came."),
                sentence(language, [h(language, "tea"), target(vocab, language), h(language, "food"), h(language, "is"), h(language, "on"), h(language, "table")], "Tea and food are on the table."),
            ]
        if i == 205:
            return [
                sentence(language, [target(vocab, language), h(language, "water"), h(language, "hot"), h(language, "i"), h(language, "drink")], "If the water is hot, I drink."),
                sentence(language, [target(vocab, language), h(language, "teacher"), h(language, "came"), h(language, "child"), h(language, "learn")], "If the teacher comes, the child learns."),
                sentence(language, [target(vocab, language), h(language, "book"), h(language, "is"), h(language, "here"), h(language, "i"), h(language, "see")], "If the book is here, I see it."),
            ]
        return [
            sentence(language, [h(language, "i"), h(language, "drink"), h(language, "water"), target(vocab, language), h(language, "hot")], "I drink water because it is hot."),
            sentence(language, [h(language, "child"), h(language, "came"), h(language, "home"), target(vocab, language), h(language, "mother"), h(language, "is"), h(language, "there")], "The child came home because mother is there."),
            sentence(language, [h(language, "teacher"), h(language, "see"), h(language, "book"), target(vocab, language), h(language, "book"), h(language, "is"), h(language, "on"), h(language, "table")], "The teacher sees the book because it is on the table."),
        ]
    if i == 201:
        return [
            sentence(language, [h(language, "book"), h(language, "table"), target(vocab, language), h(language, "is" if language != "tibetan" else "exists")], "The book is at the table."),
            sentence(language, [h(language, "cup"), h(language, "table"), target(vocab, language), h(language, "is" if language != "tibetan" else "exists")], "The cup is on the table."),
            sentence(language, [h(language, "child"), h(language, "room"), target(vocab, language), h(language, "is" if language != "tibetan" else "exists")], "The child is at the room."),
        ]
    if i == 202:
        return [
            sentence(language, [h(language, "water"), target(vocab, language), h(language, "cup"), h(language, "is" if language != "tibetan" else "exists")], "The water is in the cup."),
            sentence(language, [h(language, "book"), target(vocab, language), h(language, "bag"), h(language, "is" if language != "tibetan" else "exists")], "The book is in the bag."),
            sentence(language, [h(language, "child"), target(vocab, language), h(language, "room"), h(language, "is" if language != "tibetan" else "exists")], "The child is in the room."),
        ]
    if i == 203:
        return [
            sentence(language, [h(language, "i"), target(vocab, language), h(language, "mother"), h(language, "go")], "I go with mother."),
            sentence(language, [h(language, "teacher"), target(vocab, language), h(language, "child"), h(language, "came")], "The teacher came with the child."),
            sentence(language, [h(language, "friend"), target(vocab, language), h(language, "tea"), h(language, "drink")], "My friend drinks tea with me."),
        ]
    if i == 204:
        return [
            sentence(language, [h(language, "water"), target(vocab, language), h(language, "cup"), h(language, "here"), h(language, "is" if language != "tibetan" else "exists")], "Water and a cup are here."),
            sentence(language, [h(language, "mother"), target(vocab, language), h(language, "child"), h(language, "came")], "Mother and the child came."),
            sentence(language, [h(language, "tea"), target(vocab, language), h(language, "food"), h(language, "table"), h(language, "on"), h(language, "is" if language != "tibetan" else "exists")], "Tea and food are on the table."),
        ]
    if i == 205:
        return [
            sentence(language, [target(vocab, language), h(language, "water"), h(language, "hot"), h(language, "i"), h(language, "drink")], "If the water is hot, I drink."),
            sentence(language, [target(vocab, language), h(language, "teacher"), h(language, "came"), h(language, "child"), h(language, "learn"), h(language, "is")], "If the teacher comes, the child learns."),
            sentence(language, [target(vocab, language), h(language, "book"), h(language, "here"), h(language, "i"), h(language, "see")], "If the book is here, I see it."),
        ]
    return [
        sentence(language, [h(language, "i"), h(language, "water"), h(language, "drink"), target(vocab, language), h(language, "hot"), h(language, "is")], "I drink water because it is hot."),
        sentence(language, [h(language, "child"), h(language, "home"), h(language, "came"), target(vocab, language), h(language, "mother"), h(language, "there"), h(language, "is" if language != "tibetan" else "exists")], "The child came home because mother is there."),
        sentence(language, [h(language, "teacher"), h(language, "book"), h(language, "see"), target(vocab, language), h(language, "book"), h(language, "table"), h(language, "on"), h(language, "is" if language != "tibetan" else "exists")], "The teacher sees the book because it is on the table."),
    ]


DISPATCH = {
    "pronoun": pronoun_sentences,
    "question": question_sentences,
    "deictic": deictic_sentences,
    "negative": negative_sentences,
    "quantity": quantity_sentences,
    "adjective": adjective_sentences,
    "verb": verb_sentences,
    "function": function_sentences,
    "noun": noun_sentences,
}


def generate_language(language: str, concepts: list[Concept], seed_terms: dict[int, list[str]]) -> None:
    vocab: list[VocabItem] = []
    for concept in concepts:
        word, source = choose_word(language, concept.index, seed_terms)
        vocab.append(VocabItem(concept.index, word, concept.gloss, source))

    batches: list[dict[str, object]] = []
    corpus_rows: list[dict[str, object]] = []
    explanation_rows: list[dict[str, object]] = []
    current_id = LANGS[language]["id_start"]

    for item in vocab:
        rows = DISPATCH[classify(item.index)](language, item)
        if len(rows) != 3:
            raise ValueError(f"{language} {item.index}: expected 3 sentences")
        for row in rows:
            if item.word not in str(row["target"]):
                raise ValueError(f"{language} {item.index}: target {item.word!r} missing from {row['target']!r}")
            corpus_rows.append(
                {
                    "id": current_id,
                    "text": row["text"],
                    "cloze_word": item.word,
                    "translations": [{"id": current_id, "text": row["target"]}],
                }
            )
            explanation_rows.append({"id": current_id, "words": row["words"]})
            current_id -= 1
        batches.append(
            {
                "vocab_index": item.index,
                "word": item.word,
                "gloss": item.gloss,
                "sentences": [{"target": row["target"], "text": row["text"]} for row in rows],
            }
        )

    write_json(
        CORPORA / f"{language}_swadesh_vocab.json",
        [{"word": item.word, "gloss": item.gloss, "source": item.source} for item in vocab],
    )
    write_json(CORPORA / f"{language}_swadesh.json", {"data": corpus_rows})
    write_json(CORPORA / f"{language}_swadesh_explanations.json", {"data": explanation_rows})
    write_batches(language, batches)
    print(f"{language}: {len(vocab)} words, {len(corpus_rows)} sentences")


def write_batches(language: str, batches: list[dict[str, object]]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    splits = [(1, 104), (105, 207)]
    by_index = {item["vocab_index"]: item for item in batches}
    for start, end in splits:
        data = [by_index[index] for index in range(start, end + 1)]
        write_json(GENERATED / f"{language}_swadesh_{start:03d}_{end:03d}.json", data)


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    concepts = load_concepts()
    seeds = load_seed_terms()
    for language in LANGS:
        generate_language(language, concepts, seeds[language])


if __name__ == "__main__":
    main()
