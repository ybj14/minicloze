#!/usr/bin/env python3
"""Refresh local Swadesh vocabulary and QA course drafts.

The vocabulary seed comes from Wiktionary Swadesh data. Sentences are original
local course material generated from varied A1 frames, not copied examples.

By default this script refreshes vocabulary and runs QA only. It does not
overwrite final ``*_swadesh.json`` corpora, generated batch scaffold files, or
production explanation sidecars. Build production explanations from the merged
reviewed corpus with ``generate_full_sentence_explanations.py *-swadesh``.
Use ``--write-template-batches`` only to create draft scaffolds for human
rewrites; those template batches are not acceptable as final course material.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
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


@dataclass(frozen=True)
class CourseArtifacts:
    language: str
    vocab: list[VocabItem]
    corpus_rows: list[dict[str, object]]
    explanation_rows: list[dict[str, object]]
    batches: list[dict[str, object]]


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

A1_FILE_PREFIX = {
    "mongolian": "mongolian_a1",
    "tibetan": "tibetan_a1",
    "tajik": "tajik_a1",
    "thai": "thai_a1",
}


HELPERS = {
    "mongolian": {
        "i": ("Би", "I"),
        "i_erg": ("Би", "I"),
        "you": ("Та", "you"),
        "child": ("Хүүхэд", "child"),
        "teacher": ("Багш", "teacher"),
        "doctor": ("Эмч", "doctor"),
        "mother": ("Ээж", "mother"),
        "friend": ("Найз", "friend"),
        "my": ("Миний", "my"),
        "today": ("Өнөөдөр", "today"),
        "morning": ("Өглөө", "morning"),
        "evening": ("Орой", "evening"),
        "here": ("энд", "here"),
        "there": ("тэнд", "there"),
        "this": ("Энэ", "this"),
        "that": ("Тэр", "that"),
        "please": ("Та", "please"),
        "want": ("хүсэж", "want"),
        "can": ("чадна", "can"),
        "see": ("харлаа", "saw"),
        "is": ("байна", "is"),
        "draw": ("зурлаа", "drew"),
        "bag": ("цүнх", "bag"),
        "door": ("хаалга", "door"),
        "outside": ("гадаа", "outside"),
        "school": ("сургуульд", "at school"),
        "bread": ("талх", "bread"),
        "body": ("биед", "in the body"),
        "picture": ("зураг", "picture"),
        "check": ("шалгалаа", "checked"),
        "show": ("харуулж байна", "shows"),
        "clean": ("цэвэр", "clean"),
        "hurts": ("өвдөж", "hurts"),
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
        "doctor": ("Табиб", "doctor"),
        "mother": ("Модар", "mother"),
        "friend": ("Дӯст", "friend"),
        "my": ("Ман", "my"),
        "today": ("Имрӯз", "today"),
        "morning": ("Субҳ", "morning"),
        "evening": ("Бегоҳ", "evening"),
        "here": ("инҷо", "here"),
        "there": ("онҷо", "there"),
        "this": ("Ин", "this"),
        "that": ("Он", "that"),
        "please": ("Лутфан", "please"),
        "want": ("мехоҳад", "wants"),
        "can": ("метавонад", "can"),
        "see": ("дид", "saw"),
        "i_saw": ("дидам", "I saw"),
        "is": ("аст", "is"),
        "draw": ("кашид", "drew"),
        "bag": ("халта", "bag"),
        "door": ("дар", "door"),
        "outside": ("берун", "outside"),
        "school": ("мактаб", "school"),
        "bread": ("нон", "bread"),
        "body": ("бадан", "body"),
        "picture": ("расм", "picture"),
        "check": ("тафтиш кард", "checked"),
        "show": ("нишон медиҳад", "shows"),
        "clean": ("тоза", "clean"),
        "hurts": ("дард мекунад", "hurts"),
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
        "doctor": ("หมอ", "doctor"),
        "mother": ("แม่", "mother"),
        "friend": ("เพื่อน", "friend"),
        "my": ("ของฉัน", "my"),
        "today": ("วันนี้", "today"),
        "morning": ("ตอนเช้า", "morning"),
        "evening": ("ตอนเย็น", "evening"),
        "here": ("ที่นี่", "here"),
        "there": ("ที่นั่น", "there"),
        "this": ("นี่", "this"),
        "that": ("นั่น", "that"),
        "please": ("กรุณา", "please"),
        "want": ("อยาก", "want"),
        "can": ("ได้", "can"),
        "see": ("เห็น", "see"),
        "is": ("อยู่", "be; stay"),
        "draw": ("วาด", "draw"),
        "bag": ("กระเป๋า", "bag"),
        "door": ("ประตู", "door"),
        "outside": ("ข้างนอก", "outside"),
        "school": ("โรงเรียน", "school"),
        "bread": ("ขนมปัง", "bread"),
        "body": ("ร่างกาย", "body"),
        "picture": ("รูป", "picture"),
        "check": ("ตรวจ", "check"),
        "show": ("แสดง", "shows"),
        "clean": ("สะอาด", "clean"),
        "hurts": ("เจ็บ", "hurts"),
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
        "doctor": ("སྨན་པ", "doctor"),
        "mother": ("ཨ་མ", "mother"),
        "friend": ("གྲོགས་པོ", "friend"),
        "my": ("ངའི", "my"),
        "today": ("དེ་རིང", "today"),
        "morning": ("ཞོགས་པ", "morning"),
        "evening": ("དགོང་མོ", "evening"),
        "here": ("འདིར", "here"),
        "there": ("དེར", "there"),
        "this": ("འདི", "this"),
        "that": ("དེ", "that"),
        "please": ("རོགས་གནང", "please"),
        "want": ("འདོད", "want"),
        "can": ("ཐུབ", "can"),
        "see": ("མཐོང", "see"),
        "is": ("རེད", "is"),
        "exists": ("ཡོད", "is; exists"),
        "draw": ("བྲིས", "drew"),
        "bag": ("ཁུག་མ", "bag"),
        "door": ("སྒོ", "door"),
        "outside": ("ཕྱི་ལ", "outside"),
        "school": ("སློབ་གྲྭ", "school"),
        "bread": ("བག་ལེབ", "bread"),
        "body": ("ལུས", "body"),
        "picture": ("པར", "picture"),
        "check": ("བརྟག", "check"),
        "show": ("སྟོན", "shows"),
        "clean": ("གཙང་མ", "clean"),
        "hurts": ("ན", "hurts"),
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


def ctx(lexicon: dict[int, VocabItem], index: int, language: str) -> dict[str, str]:
    item = lexicon[index]
    return explain(item.word, item.gloss, language)


def be(language: str) -> dict[str, str]:
    return h(language, "exists" if language == "tibetan" else "is")


def lang_sentence(language: str, tokens: list[dict[str, str]], english: str) -> dict[str, object]:
    return sentence(language, tokens, english)


def semantic_sentences(
    language: str, vocab: VocabItem, lexicon: dict[int, VocabItem]
) -> list[dict[str, object]]:
    index = vocab.index
    if index in range(1, 7):
        return semantic_pronoun_sentences(language, vocab, lexicon)
    if index in range(11, 16):
        return semantic_question_sentences(language, vocab, lexicon)
    if index in {7, 8, 9, 10}:
        return semantic_deictic_sentences(language, vocab, lexicon)
    if index == 16:
        return semantic_negative_sentences(language, vocab, lexicon)
    if index in range(17, 27):
        return semantic_quantity_sentences(language, vocab, lexicon)
    if index in set(range(27, 36)) | set(range(172, 199)):
        return semantic_adjective_sentences(language, vocab, lexicon)
    if index in set(range(92, 147)) | {169}:
        return semantic_verb_sentences(language, vocab, lexicon)
    if index in range(201, 207):
        return semantic_function_sentences(language, vocab, lexicon)
    return semantic_noun_sentences(language, vocab, lexicon)


def semantic_pronoun_sentences(
    language: str, vocab: VocabItem, lexicon: dict[int, VocabItem]
) -> list[dict[str, object]]:
    forms = {
        1: ("I am here.", "The teacher sees me.", "I drink water."),
        2: ("You are here.", "Mother sees you.", "You drink water."),
        3: ("He is there.", "The child sees him.", "He drinks water."),
        4: ("We are at school.", "The teacher sees us.", "We drink water."),
        5: ("You all are here.", "Mother sees you all.", "You all drink water."),
        6: ("They are outside.", "The child sees them.", "They drink water."),
    }
    target_word = target(vocab, language)
    first, second, third = forms[vocab.index]
    place = h(language, "school") if vocab.index == 4 else h(language, "outside" if vocab.index in {3, 6} else "here")
    return [
        lang_sentence(language, [target_word, place, be(language)], first),
        lang_sentence(language, [h(language, "teacher" if vocab.index in {1, 4} else "mother" if vocab.index in {2, 5} else "child"), target_word, h(language, "see")], second),
        lang_sentence(language, [target_word, ctx(lexicon, 150, language), h(language, "drink")], third),
    ]


def semantic_question_sentences(
    language: str, vocab: VocabItem, lexicon: dict[int, VocabItem]
) -> list[dict[str, object]]:
    q = target(vocab, language)
    if vocab.index == 11:
        if language == "thai":
            rows = [
                [q, h(language, "came"), h(language, "today")],
                [q, h(language, "see"), h(language, "teacher")],
                [h(language, "you"), h(language, "go"), ctx(lexicon, 203, language), q],
            ]
        else:
            rows = [
                [q, h(language, "today"), h(language, "came")],
                [q, h(language, "teacher"), h(language, "see")],
                [h(language, "you"), q, ctx(lexicon, 203, language), h(language, "go")],
            ]
        texts = ["Who came today?", "Who saw the teacher?", "Who are you going with?"]
    elif vocab.index == 12:
        if language == "thai":
            rows = [
                [h(language, "bag"), h(language, "in"), q, be(language)],
                [h(language, "you"), h(language, "drink"), q],
                [h(language, "child"), h(language, "see"), q],
            ]
        else:
            rows = [
                [h(language, "bag"), h(language, "in"), q, be(language)],
                [h(language, "you"), q, h(language, "drink")],
                [h(language, "child"), q, h(language, "see")],
            ]
        texts = ["What is in the bag?", "What are you drinking?", "What does the child see?"]
    elif vocab.index == 13:
        rows = [
            [h(language, "you"), q, h(language, "go")],
            [h(language, "book"), q, be(language)],
            [h(language, "mother"), q, h(language, "came")],
        ]
        texts = ["Where are you going?", "Where is the book?", "Where did mother come?"]
    elif vocab.index == 14:
        rows = [
            [h(language, "you"), q, h(language, "came")],
            [h(language, "teacher"), q, h(language, "came")],
            [q, ctx(lexicon, 178, language), h(language, "go")],
        ]
        texts = ["When did you come?", "When did the teacher come?", "When is the trip?"]
    else:
        if language == "thai":
            rows = [
                [h(language, "you"), h(language, "go"), q],
                [h(language, "child"), h(language, "learn"), q],
                [h(language, "mother"), h(language, "drink"), ctx(lexicon, 150, language), q],
            ]
        else:
            rows = [
                [h(language, "you"), q, h(language, "go")],
                [h(language, "child"), q, h(language, "learn")],
                [h(language, "mother"), ctx(lexicon, 150, language), q, h(language, "drink")],
            ]
        texts = ["How will you go?", "How does the child learn?", "How does mother drink the water?"]
    return [lang_sentence(language, row, text) for row, text in zip(rows, texts, strict=True)]


def semantic_deictic_sentences(
    language: str, vocab: VocabItem, lexicon: dict[int, VocabItem]
) -> list[dict[str, object]]:
    d = target(vocab, language)
    if vocab.index in {7, 8}:
        rows = [
            [d, h(language, "book"), ctx(lexicon, 183 if vocab.index == 7 else 184, language), h(language, "is")],
            [h(language, "mother"), d, h(language, "see")],
            [d, h(language, "cup"), ctx(lexicon, 150, language), be(language)],
        ]
        texts = [
            f"{vocab.gloss.title()} book is {'new' if vocab.index == 7 else 'old'}.",
            f"Mother sees {vocab.gloss}.",
            f"{vocab.gloss.title()} cup has water.",
        ]
    else:
        place_text = "here" if vocab.index == 9 else "there"
        rows = [
            [h(language, "book"), d, be(language)],
            [h(language, "mother"), d, h(language, "came")],
            [h(language, "child"), d, h(language, "play") if "play" in HELPERS[language] else ctx(lexicon, 142, language)],
        ]
        texts = [f"The book is {place_text}.", f"Mother came {place_text}.", f"The child plays {place_text}."]
    return [lang_sentence(language, row, text) for row, text in zip(rows, texts, strict=True)]


def semantic_negative_sentences(
    language: str, vocab: VocabItem, lexicon: dict[int, VocabItem]
) -> list[dict[str, object]]:
    n = target(vocab, language)
    return [
        lang_sentence(language, [ctx(lexicon, 150, language), n, ctx(lexicon, 180, language), h(language, "is")], "The water is not warm."),
        lang_sentence(language, [h(language, "child"), n, h(language, "came")], "The child did not come."),
        lang_sentence(language, [h(language, "teacher"), n, h(language, "there"), be(language)], "The teacher is not there."),
    ]


def semantic_quantity_sentences(
    language: str, vocab: VocabItem, lexicon: dict[int, VocabItem]
) -> list[dict[str, object]]:
    q = target(vocab, language)
    number_text = {
        17: "all", 18: "many", 19: "some", 20: "few", 21: "other",
        22: "one", 23: "two", 24: "three", 25: "four", 26: "five",
    }[vocab.index]
    rows = [
        [h(language, "teacher"), q, h(language, "book"), h(language, "see")],
        [q, h(language, "cup"), h(language, "table"), h(language, "on"), be(language)],
        [h(language, "child"), q, ctx(lexicon, 54, language), h(language, "eat") if "eat" in HELPERS[language] else ctx(lexicon, 93, language)],
    ]
    texts = [
        f"The teacher sees {number_text} books.",
        f"{number_text.title()} cups are on the table.",
        f"The child eats {number_text} fruit.",
    ]
    return [lang_sentence(language, row, text) for row, text in zip(rows, texts, strict=True)]


PEOPLE = set(range(36, 44))
ANIMALS = set(range(44, 51))
PLANTS = set(range(51, 61))
BODY = set(range(71, 92)) | {62, 64, 65, 66}
NATURE = set(range(147, 172))


def semantic_noun_sentences(
    language: str, vocab: VocabItem, lexicon: dict[int, VocabItem]
) -> list[dict[str, object]]:
    x = target(vocab, language)
    g = vocab.gloss
    if vocab.index in PEOPLE:
        frames = [
            ([x, h(language, "home"), be(language)], f"The {g} is at home."),
            ([x, h(language, "tea"), h(language, "drink")], f"The {g} drinks tea."),
            ([h(language, "teacher"), x, h(language, "see")], f"The teacher sees the {g}."),
            ([x, h(language, "school"), h(language, "came")], f"The {g} came to school."),
            ([x, h(language, "child"), ctx(lexicon, 203, language), ctx(lexicon, 142, language)], f"The {g} plays with the child."),
        ]
    elif vocab.index in ANIMALS:
        frames = [
            ([x, h(language, "outside"), be(language)], f"The {g} is outside."),
            ([h(language, "child"), x, h(language, "see")], f"The child sees the {g}."),
            ([x, ctx(lexicon, 150, language), h(language, "drink")], f"The {g} drinks water."),
            ([x, ctx(lexicon, 51, language), ctx(lexicon, 197, language), be(language)], f"The {g} is near the tree."),
            ([x, ctx(lexicon, 107, language)], f"The {g} sleeps."),
        ]
    elif vocab.index in PLANTS:
        frames = [
            ([x, ctx(lexicon, 173, language), h(language, "is")], f"The {g} is green."),
            ([h(language, "child"), x, h(language, "see")], f"The child sees the {g}."),
            ([x, ctx(lexicon, 150, language), h(language, "in"), be(language)], f"The {g} is in water."),
            ([x, h(language, "road"), ctx(lexicon, 197, language), be(language)], f"The {g} is near the road."),
            ([h(language, "mother"), x, h(language, "table"), h(language, "on"), be(language)], f"Mother puts the {g} on the table."),
        ]
    elif vocab.index in BODY:
        frames = [
            ([h(language, "my"), x, h(language, "hurts")], f"My {g} hurts."),
            ([x, h(language, "clean"), h(language, "is")], f"The {g} is clean."),
            ([h(language, "i"), x, ctx(lexicon, 132, language)], f"I wash the {g}."),
            ([h(language, "child"), x, h(language, "see")], f"The child sees the {g}."),
            ([h(language, "my"), x, ctx(lexicon, 181, language), h(language, "is")], f"My {g} is cold."),
        ]
    elif vocab.index in NATURE:
        frames = [
            ([x, h(language, "today"), be(language)], f"The {g} is here today."),
            ([h(language, "child"), x, h(language, "see")], f"The child sees the {g}."),
            ([x, h(language, "road"), ctx(lexicon, 197, language), be(language)], f"The {g} is near the road."),
            ([x, ctx(lexicon, 162, language), h(language, "in"), be(language)], f"The {g} is in the sky."),
            ([x, ctx(lexicon, 181, language), h(language, "is")], f"The {g} is cold."),
        ]
    else:
        frames = [
            ([x, h(language, "table"), h(language, "on"), be(language)], f"The {g} is on the table."),
            ([h(language, "child"), x, h(language, "hold") if "hold" in HELPERS[language] else ctx(lexicon, 129, language)], f"The child holds the {g}."),
            ([x, h(language, "bag"), h(language, "in"), be(language)], f"The {g} is in the bag."),
            ([h(language, "mother"), x, h(language, "see")], f"Mother sees the {g}."),
            ([x, h(language, "clean"), h(language, "is")], f"The {g} is clean."),
        ]
    return [lang_sentence(language, row, text) for row, text in choose_three(frames, vocab.index)]


def semantic_adjective_sentences(
    language: str, vocab: VocabItem, lexicon: dict[int, VocabItem]
) -> list[dict[str, object]]:
    x = target(vocab, language)
    pair = {
        27: (h(language, "room"), "room"), 28: (h(language, "road"), "road"),
        29: (ctx(lexicon, 152, language), "river"), 30: (h(language, "book"), "book"),
        31: (h(language, "bag"), "bag"), 32: (h(language, "cup"), "cup"),
        33: (ctx(lexicon, 178, language), "day"), 34: (h(language, "road"), "road"),
        35: (ctx(lexicon, 56, language), "leaf"), 172: (h(language, "cup"), "cup"),
        173: (ctx(lexicon, 56, language), "leaf"), 174: (ctx(lexicon, 59, language), "flower"),
        175: (ctx(lexicon, 164, language), "snow"), 176: (ctx(lexicon, 177, language), "night"),
        180: (ctx(lexicon, 150, language), "water"), 181: (ctx(lexicon, 150, language), "water"),
        182: (h(language, "cup"), "cup"), 183: (h(language, "book"), "book"),
        184: (h(language, "road"), "road"), 185: (h(language, "food"), "food"),
        186: (ctx(lexicon, 160, language), "weather"), 187: (ctx(lexicon, 54, language), "fruit"),
        188: (ctx(lexicon, 83, language), "hand"), 189: (h(language, "road"), "road"),
        190: (ctx(lexicon, 156, language), "stone"), 191: (h(language, "stick"), "stick") if "stick" in HELPERS[language] else (ctx(lexicon, 53, language), "stick"),
        192: (ctx(lexicon, 53, language), "stick"), 193: (ctx(lexicon, 156, language), "stone"),
        194: (h(language, "road"), "road"), 195: (h(language, "road"), "road"),
        196: (h(language, "answer"), "answer") if "answer" in HELPERS[language] else (h(language, "book"), "answer"),
        197: (h(language, "home"), "home"), 198: (ctx(lexicon, 171, language), "mountain"),
    }.get(vocab.index, (h(language, "bag"), "bag"))
    noun, noun_text = pair
    return [
        lang_sentence(language, [noun, x, h(language, "is")], f"The {noun_text} is {vocab.gloss}."),
        lang_sentence(language, [h(language, "today"), noun, x, h(language, "is")], f"The {noun_text} is {vocab.gloss} today."),
        lang_sentence(language, [x, noun, h(language, "here"), be(language)], f"The {vocab.gloss} {noun_text} is here."),
    ]


VERB_OBJECT = {
    92: (ctx, 150, "water"), 93: (h, "bread", "bread"), 94: (ctx, 54, "fruit"),
    95: (ctx, 150, "water"), 96: (h, "outside", "outside"), 97: (h, "home", "at home"),
    98: (ctx, 163, "wind"), 99: (h, "morning", "in the morning"), 100: (h, "friend", "with a friend"),
    101: (h, "book", "the book"), 102: (ctx, 46, "a bird"), 103: (ctx, 207, "the name"),
    104: (h, "mother", "about mother"), 105: (ctx, 59, "the flower"), 106: (ctx, 49, "the snake"),
    107: (h, "home", "at home"), 108: (h, "home", "at home"), 109: (ctx, 51, "the tree"),
    110: (ctx, 48, "the louse"), 111: (h, "school", "at school"), 112: (ctx, 45, "fish"),
    113: (ctx, 53, "the stick"), 114: (h, "bread", "bread"), 115: (ctx, 54, "fruit"),
    116: (ctx, 53, "the stick"), 117: (ctx, 83, "the hand"), 118: (ctx, 159, "earth"),
    119: (ctx, 153, "in the lake"), 120: (ctx, 46, "like a bird"), 121: (h, "road", "on the road"),
    122: (h, "school", "to school"), 123: (h, "home", "at home"), 124: (h, "room", "in the room"),
    125: (h, "door", "by the door"), 126: (h, "road", "on the road"), 127: (h, "outside", "outside"),
    128: (h, "book", "the book"), 129: (h, "cup", "the cup"), 130: (ctx, 54, "fruit"),
    131: (ctx, 83, "the hand"), 132: (ctx, 83, "the hand"), 133: (h, "table", "the table"),
    134: (h, "door", "the door"), 135: (h, "door", "the door"), 136: (ctx, 156, "the stone"),
    137: (ctx, 61, "the rope"), 138: (h, "bag", "the bag"), 139: (h, "book", "books"),
    140: (ctx, 207, "the name"), 141: (h, "evening", "in the evening"), 142: (h, "outside", "outside"),
    143: (ctx, 150, "on water"), 144: (ctx, 152, "in the river"), 145: (ctx, 150, "water"),
    146: (ctx, 83, "the hand"), 169: (ctx, 167, "fire"),
}


def object_token(language: str, lexicon: dict[int, VocabItem], spec: tuple) -> dict[str, str]:
    getter, value, _ = spec
    if getter is ctx:
        return ctx(lexicon, value, language)
    return h(language, value)


def semantic_verb_sentences(
    language: str, vocab: VocabItem, lexicon: dict[int, VocabItem]
) -> list[dict[str, object]]:
    x = target(vocab, language)
    spec = VERB_OBJECT.get(vocab.index, (h, "here", "here"))
    obj = object_token(language, lexicon, spec)
    obj_text = spec[2]
    frames = [
        ([h(language, "i"), obj, x, h(language, "want")], f"I want to {vocab.gloss} {obj_text}."),
        ([h(language, "child"), obj, x, h(language, "can")], f"The child can {vocab.gloss} {obj_text}."),
        ([h(language, "today"), obj, x, h(language, "good") if "good" in HELPERS[language] else ctx(lexicon, 185, language)], f"Today it is good to {vocab.gloss} {obj_text}."),
        ([h(language, "please"), obj, x], f"Please {vocab.gloss} {obj_text}."),
        ([h(language, "school"), obj, x, h(language, "no")], f"Do not {vocab.gloss} {obj_text} at school."),
    ]
    if vocab.index in {109, 110, 111, 116}:
        frames[0] = ([h(language, "school"), obj, x, h(language, "no")], f"Do not {vocab.gloss} {obj_text} at school.")
        frames[1] = ([h(language, "book"), obj, x, h(language, "say") if "say" in HELPERS[language] else ctx(lexicon, 140, language)], f"The book says not to {vocab.gloss} {obj_text}.")
    return [lang_sentence(language, row, text) for row, text in choose_three(frames, vocab.index)]


def semantic_function_sentences(
    language: str, vocab: VocabItem, lexicon: dict[int, VocabItem]
) -> list[dict[str, object]]:
    return function_sentences(language, vocab)


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


def generate_language(
    language: str, concepts: list[Concept], seed_terms: dict[int, list[str]]
) -> CourseArtifacts:
    vocab: list[VocabItem] = []
    for concept in concepts:
        word, source = choose_word(language, concept.index, seed_terms)
        vocab.append(VocabItem(concept.index, word, concept.gloss, source))
    lexicon = {item.index: item for item in vocab}
    a1_bank = load_a1_sentence_bank(language, vocab)

    batches: list[dict[str, object]] = []
    corpus_rows: list[dict[str, object]] = []
    explanation_rows: list[dict[str, object]] = []
    current_id = LANGS[language]["id_start"]

    for item in vocab:
        rows = a1_bank.get(item.index) or semantic_sentences(language, item, lexicon)
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

    return CourseArtifacts(
        language=language,
        vocab=vocab,
        corpus_rows=corpus_rows,
        explanation_rows=explanation_rows,
        batches=batches,
    )


BAD_ENGLISH_PATTERNS = [
    re.compile(pattern, re.I)
    for pattern in [
        r"\bwho is the book\b",
        r"\bwhat is the book\b",
        r"\bwhere came\b",
        r"\bwhen is the book\b",
        r"\bhow came\b",
        r"\bwhere will you go\?$",
        r"\bwho will you go\?$",
        r"\bwhat will you go\?$",
        r"\bthe liver is here\b",
        r"\bthe child drew the name\b",
    ]
]


QUESTION_GLOSSES = {"who", "what", "where", "when", "how"}
DEFAULT_MAX_FRAME_REPEATS = 8


def normalize_english_frame(english: str, gloss: str | None) -> str:
    frame = english.lower().strip()
    frame = re.sub(r"\s+", " ", frame)
    if gloss:
        candidates = {gloss.lower().strip()}
        if candidates:
            candidates.add(re.sub(r"^to\s+", "", next(iter(candidates))))
        for candidate in sorted(candidates, key=len, reverse=True):
            if not candidate:
                continue
            forms = [candidate]
            if not candidate.endswith("s"):
                forms.append(f"{candidate}s")
            if candidate.endswith("y"):
                forms.append(f"{candidate[:-1]}ies")
            for form in forms:
                frame = re.sub(rf"\b{re.escape(form)}\b", "{x}", frame)
    return frame


def batch_sentence_rows(artifacts: CourseArtifacts) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for batch in artifacts.batches:
        for sentence_row in batch["sentences"]:
            rows.append(
                {
                    "text": sentence_row["text"],
                    "target": sentence_row["target"],
                    "vocab_index": batch["vocab_index"],
                    "word": batch["word"],
                    "gloss": batch["gloss"],
                }
            )
    return rows


def collect_naturalness_issues(
    language: str, rows: list[dict[str, object]], max_frame_repeats: int
) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    frame_counts: Counter[str] = Counter()
    frame_examples: dict[str, list[str]] = defaultdict(list)

    for row in rows:
        english = str(row.get("text", "")).strip()
        gloss = str(row.get("gloss", "")).strip()
        index = row.get("vocab_index", "?")
        if any(pattern.search(english) for pattern in BAD_ENGLISH_PATTERNS):
            issues.append(
                ("error", f"{language} {index}: unnatural template sentence: {english!r}")
            )
        if gloss.lower() in QUESTION_GLOSSES and english.lower().startswith(
            ("who is the ", "what is the ")
        ):
            issues.append(
                ("error", f"{language} {index}: question word forced into noun frame: {english!r}")
            )

        frame = normalize_english_frame(english, gloss)
        frame_counts[frame] += 1
        if len(frame_examples[frame]) < 3:
            frame_examples[frame].append(english)

    for frame, count in frame_counts.most_common():
        if count <= max_frame_repeats:
            continue
        examples = "; ".join(repr(example) for example in frame_examples[frame])
        issues.append(
            (
                "warning",
                f"{language}: repeated English frame {frame!r} appears {count} times; examples: {examples}",
            )
        )
    return issues


def report_naturalness_issues(
    issues: list[tuple[str, str]], *, strict_frame_qa: bool
) -> bool:
    for severity, message in issues:
        print(f"{severity.upper()}: {message}")
    has_errors = any(severity == "error" for severity, _ in issues)
    has_strict_warnings = strict_frame_qa and any(severity == "warning" for severity, _ in issues)
    return has_errors or has_strict_warnings


def validate_generated_artifacts(artifacts: CourseArtifacts, max_frame_repeats: int) -> list[tuple[str, str]]:
    return collect_naturalness_issues(
        artifacts.language, batch_sentence_rows(artifacts), max_frame_repeats
    )


def validate_existing_language(language: str, max_frame_repeats: int) -> list[tuple[str, str]]:
    corpus_path = CORPORA / f"{language}_swadesh.json"
    vocab_path = CORPORA / f"{language}_swadesh_vocab.json"
    corpus = read_json(corpus_path)
    vocab = read_json(vocab_path)
    gloss_by_word = {
        str(item.get("word")): str(item.get("gloss", ""))
        for item in vocab
        if isinstance(item, dict)
    }
    rows = []
    for row in corpus.get("data", []):
        if not isinstance(row, dict):
            continue
        word = str(row.get("cloze_word", ""))
        rows.append(
            {
                "text": row.get("text", ""),
                "word": word,
                "gloss": gloss_by_word.get(word, ""),
                "vocab_index": row.get("id", "?"),
            }
        )
    return collect_naturalness_issues(language, rows, max_frame_repeats)


def write_batches(language: str, batches: list[dict[str, object]]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    splits = [(1, 104), (105, 207)]
    by_index = {item["vocab_index"]: item for item in batches}
    for start, end in splits:
        data = [by_index[index] for index in range(start, end + 1)]
        write_json(GENERATED / f"{language}_swadesh_{start:03d}_{end:03d}.json", data)


def write_vocab(artifacts: CourseArtifacts) -> None:
    write_json(
        CORPORA / f"{artifacts.language}_swadesh_vocab.json",
        [
            {"word": item.word, "gloss": item.gloss, "source": item.source}
            for item in artifacts.vocab
        ],
    )


def write_explanations(artifacts: CourseArtifacts) -> None:
    write_json(
        CORPORA / f"{artifacts.language}_swadesh_explanations.json",
        {"data": artifacts.explanation_rows},
    )


def write_final_corpus(artifacts: CourseArtifacts) -> None:
    write_json(CORPORA / f"{artifacts.language}_swadesh.json", {"data": artifacts.corpus_rows})


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def duplicate_words(vocab: list[VocabItem]) -> set[str]:
    seen: set[str] = set()
    duplicated: set[str] = set()
    for item in vocab:
        if item.word in seen:
            duplicated.add(item.word)
        seen.add(item.word)
    return duplicated


def add_swadesh_note(words: list[dict[str, str]], item: VocabItem) -> list[dict[str, str]]:
    updated = [dict(word) for word in words]
    for word in updated:
        if clean_term(str(word.get("word", ""))) == clean_term(item.word):
            word["gloss"] = item.gloss
            word["note"] = "Swadesh target"
            break
    return updated


def load_a1_sentence_bank(language: str, vocab: list[VocabItem]) -> dict[int, list[dict[str, object]]]:
    """Reuse authored A1 sentences for exact, unambiguous Swadesh overlap."""
    prefix = A1_FILE_PREFIX[language]
    corpus_path = CORPORA / f"{prefix}.json"
    explanations_path = CORPORA / f"{prefix}_explanations.json"
    if not corpus_path.exists() or not explanations_path.exists():
        return {}

    duplicated = duplicate_words(vocab)
    item_by_word = {
        item.word: item
        for item in vocab
        if item.word not in duplicated
    }
    corpus = read_json(corpus_path)["data"]  # type: ignore[index]
    explanations = read_json(explanations_path)["data"]  # type: ignore[index]
    explanations_by_id = {row["id"]: row["words"] for row in explanations}
    by_index: dict[int, list[dict[str, object]]] = {}

    for row in corpus:
        word = str(row.get("cloze_word") or "")
        item = item_by_word.get(word)
        if item is None:
            continue
        target_text = row["translations"][0]["text"]
        if item.word not in target_text:
            continue
        words = explanations_by_id.get(row["id"], [])
        if not any(clean_term(str(part.get("word", ""))) == clean_term(item.word) for part in words):
            continue
        by_index.setdefault(item.index, []).append(
            {
                "target": target_text,
                "text": row["text"],
                "words": add_swadesh_note(words, item),
            }
        )

    return {
        index: rows[:3]
        for index, rows in by_index.items()
        if len(rows) >= 3
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Refresh Swadesh vocab sidecars and run naturalness QA. "
            "By default this does not overwrite final *_swadesh.json corpora or "
            "generated/*_swadesh_*.json sentence scaffolds, and it does not "
            "write production explanations."
        )
    )
    parser.add_argument(
        "languages",
        nargs="*",
        choices=[*LANGS.keys(), "all"],
        help="Languages to process. Defaults to all.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Read existing *_swadesh.json files and run naturalness QA without fetching or writing.",
    )
    parser.add_argument(
        "--no-write-vocab",
        action="store_true",
        help="Do not refresh *_swadesh_vocab.json. Ignored with --validate-only.",
    )
    parser.add_argument(
        "--no-write-explanations",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--write-candidate-explanations",
        action="store_true",
        help=(
            "Write candidate *_swadesh_explanations.json from scaffold output. "
            "Not for production; production explanations must be regenerated from merged final corpus."
        ),
    )
    parser.add_argument(
        "--write-template-batches",
        action="store_true",
        help=(
            "Write generated/*_swadesh_*.json draft scaffold batches. These template "
            "batches are for human rewriting only and must not be used as final corpus material."
        ),
    )
    parser.add_argument(
        "--write-final-corpus",
        action="store_true",
        help=(
            "Compatibility escape hatch: overwrite *_swadesh.json final corpus files. "
            "Use only after human-authored review; template/scaffold output is not final material."
        ),
    )
    parser.add_argument(
        "--max-frame-repeats",
        type=int,
        default=DEFAULT_MAX_FRAME_REPEATS,
        help=(
            "Report an English sentence frame when it appears more than this many times. "
            f"Default: {DEFAULT_MAX_FRAME_REPEATS}."
        ),
    )
    parser.add_argument(
        "--strict-frame-qa",
        action="store_true",
        help="Treat repeated-frame QA warnings as failures.",
    )
    return parser.parse_args()


def selected_languages(args: argparse.Namespace) -> list[str]:
    if not args.languages or "all" in args.languages:
        return list(LANGS)
    return args.languages


def main() -> None:
    args = parse_args()
    languages = selected_languages(args)

    if args.validate_only:
        failed = False
        for language in languages:
            issues = validate_existing_language(language, args.max_frame_repeats)
            failed = report_naturalness_issues(
                issues, strict_frame_qa=args.strict_frame_qa
            ) or failed
            print(f"{language}: validated existing final corpus")
        if failed:
            raise SystemExit(1)
        return

    concepts = load_concepts()
    seeds = load_seed_terms()
    failed = False
    for language in languages:
        artifacts = generate_language(language, concepts, seeds[language])
        issues = validate_generated_artifacts(artifacts, args.max_frame_repeats)
        failed = report_naturalness_issues(
            issues, strict_frame_qa=args.strict_frame_qa
        ) or failed
        if not args.no_write_vocab:
            write_vocab(artifacts)
        if args.write_candidate_explanations and not args.no_write_explanations:
            write_explanations(artifacts)
        if args.write_template_batches:
            write_batches(language, artifacts.batches)
        if args.write_final_corpus:
            write_final_corpus(artifacts)
        print(
            f"{language}: {len(artifacts.vocab)} words, "
            f"{len(artifacts.corpus_rows)} candidate sentences"
        )
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
