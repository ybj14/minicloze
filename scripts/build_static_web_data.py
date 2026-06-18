#!/usr/bin/env python3
"""Build static data extras used by the browser-only web app."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pyewts

from amharic_transliteration import romanize as romanize_amharic
from armenian_transliteration import romanize as romanize_armenian
from burmese_okell import romanize as romanize_burmese_okell
from khmer_romanization import transcribe as transcribe_khmer
from khmer_romanization import transliterate as transliterate_khmer
from thai_paiboon import romanize as romanize_thai_paiboon


ROOT = Path(__file__).resolve().parents[1]
STATIC_DATA = ROOT / "minicloze-web" / "static" / "data"
CORPORA = ROOT / "minicloze-lib" / "corpora"

TIBETAN_BREAKS = {"་", "༌", "།", "༎", "༏", "༐", "༑", "༔"}
COURSE_PREFIXES = [
    "mongolian_a1",
    "mongolian_swadesh",
    "tibetan_a1",
    "tibetan_swadesh",
    "tajik_a1",
    "tajik_swadesh",
    "thai_a1",
    "thai_swadesh",
    "burmese_a1",
    "burmese_swadesh",
    "khmer_a1",
    "khmer_swadesh",
    "amharic_a1",
    "amharic_swadesh",
    "armenian_a1",
    "armenian_swadesh",
]
SOURCE_FILES = [
    filename
    for prefix in COURSE_PREFIXES
    for filename in [f"{prefix}.json", f"{prefix}_explanations.json", f"{prefix}_vocab.json"]
]
TIBETAN_COURSES = ["tibetan_a1", "tibetan_swadesh"]
THAI_COURSES = ["thai_a1", "thai_swadesh"]
BURMESE_COURSES = ["burmese_a1", "burmese_swadesh"]
KHMER_COURSES = ["khmer_a1", "khmer_swadesh"]
AMHARIC_COURSES = ["amharic_a1", "amharic_swadesh"]
ARMENIAN_COURSES = ["armenian_a1", "armenian_swadesh"]


def tokenize_syllables(text: str) -> list[str]:
    tokens: list[str] = []
    current: list[str] = []

    for char in text.strip():
        current.append(char)
        if char in TIBETAN_BREAKS or char.isspace():
            push_token(tokens, current)

    push_token(tokens, current)
    return tokens


def push_token(tokens: list[str], current: list[str]) -> None:
    token = "".join(current)
    if token.strip():
        tokens.append(token)
    current.clear()


def tokenize_with_target(text: str, target: str | None) -> list[str]:
    if not target:
        return tokenize_syllables(text)

    index = text.find(target)
    if index < 0:
        return tokenize_syllables(text)

    before = text[:index]
    after = text[index + len(target) :]
    return [*tokenize_syllables(before), target, *tokenize_syllables(after)]


def convert_items(converter: pyewts.pyewts, items: list[str]) -> list[str]:
    return [converter.toWylie(item) for item in items]


def convert_items_to_thl(items: list[str]) -> list[str]:
    script = ROOT / "scripts" / "tibetan_thl.mjs"
    try:
        result = subprocess.run(
            ["node", str(script)],
            input=json.dumps(items, ensure_ascii=False),
            text=True,
            capture_output=True,
            check=True,
            cwd=ROOT,
        )
    except FileNotFoundError as err:
        raise RuntimeError("Tibetan THL generation requires Node.js") from err
    except subprocess.CalledProcessError as err:
        stderr = err.stderr.strip()
        raise RuntimeError(
            "Tibetan THL generation requires npm dependencies. "
            "Run `npm install` from the workspace root. "
            f"Details: {stderr}"
        ) from err

    converted = json.loads(result.stdout)
    if len(converted) != len(items):
        raise RuntimeError(
            f"THL converter returned {len(converted)} items for {len(items)} inputs"
        )
    return converted


def tibetan_token(text: str, wylie: str, thl: str) -> dict[str, str]:
    token = {"text": text}
    if wylie.strip():
        token["wylie"] = wylie
    if thl.strip():
        token["thl"] = thl
    return token


def build_tibetan_tokens(course: str) -> None:
    converter = pyewts.pyewts()
    corpus_path = STATIC_DATA / f"{course}.json"
    output_path = STATIC_DATA / f"{course}_tokens.json"

    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    tokenized: dict[str, list[dict[str, str]]] = {}
    sentence_token_texts: list[tuple[str, list[str]]] = []
    all_token_texts: list[str] = []

    for sentence in corpus["data"]:
        translation = sentence.get("translations", [{}])[0].get("text", "")
        token_texts = tokenize_with_target(translation, sentence.get("cloze_word"))
        sentence_token_texts.append((str(sentence["id"]), token_texts))
        all_token_texts.extend(token_texts)

    all_wylies = convert_items(converter, all_token_texts)
    all_thls = convert_items_to_thl(all_token_texts)
    offset = 0
    for sentence_id, token_texts in sentence_token_texts:
        length = len(token_texts)
        wylies = all_wylies[offset : offset + length]
        thls = all_thls[offset : offset + length]
        offset += length
        tokenized[sentence_id] = [
            tibetan_token(text, wylie, thl)
            for text, wylie, thl in zip(token_texts, wylies, thls, strict=True)
        ]

    output_path.write_text(
        json.dumps(tokenized, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def build_thai_tokens(course: str) -> None:
    explanations_path = STATIC_DATA / f"{course}_explanations.json"
    output_path = STATIC_DATA / f"{course}_tokens.json"
    explanations = json.loads(explanations_path.read_text(encoding="utf-8"))
    tokenized: dict[str, list[dict[str, str]]] = {}

    for sentence in explanations["data"]:
        tokens = []
        for word in sentence.get("words", []):
            text = word.get("word", "")
            paiboon = word.get("paiboon") or romanize_thai_paiboon(text)
            tokens.append({"text": text, "paiboon": paiboon})
        tokenized[str(sentence["id"])] = tokens

    output_path.write_text(
        json.dumps(tokenized, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def build_burmese_tokens(course: str) -> None:
    explanations_path = STATIC_DATA / f"{course}_explanations.json"
    output_path = STATIC_DATA / f"{course}_tokens.json"
    explanations = json.loads(explanations_path.read_text(encoding="utf-8"))
    tokenized: dict[str, list[dict[str, str]]] = {}

    for sentence in explanations["data"]:
        tokens = []
        words = sentence.get("words", [])
        for index, word in enumerate(words):
            text = word.get("word", "")
            if index + 1 < len(words):
                text = f"{text} "
            token = {"text": text}
            mlcts = word.get("mlcts")
            if mlcts:
                token["mlcts"] = mlcts
            okell = word.get("okell") or romanize_burmese_okell(word.get("word", ""), mlcts)
            if okell:
                token["okell"] = okell
            tokens.append(token)
        tokenized[str(sentence["id"])] = tokens

    output_path.write_text(
        json.dumps(tokenized, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def build_khmer_tokens(course: str) -> None:
    explanations_path = STATIC_DATA / f"{course}_explanations.json"
    output_path = STATIC_DATA / f"{course}_tokens.json"
    explanations = json.loads(explanations_path.read_text(encoding="utf-8"))
    tokenized: dict[str, list[dict[str, str]]] = {}

    for sentence in explanations["data"]:
        tokens = []
        for word in sentence.get("words", []):
            text = word.get("word", "")
            transliteration = word.get("transliteration") or transliterate_khmer(text)
            transcription = word.get("transcription") or transcribe_khmer(text)
            token = {"text": text}
            if transliteration:
                token["transliteration"] = transliteration
            if transcription:
                token["transcription"] = transcription
            tokens.append(token)
        tokenized[str(sentence["id"])] = tokens

    output_path.write_text(
        json.dumps(tokenized, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def build_amharic_tokens(course: str) -> None:
    explanations_path = STATIC_DATA / f"{course}_explanations.json"
    output_path = STATIC_DATA / f"{course}_tokens.json"
    explanations = json.loads(explanations_path.read_text(encoding="utf-8"))
    tokenized: dict[str, list[dict[str, str]]] = {}

    for sentence in explanations["data"]:
        tokens = []
        words = sentence.get("words", [])
        for index, word in enumerate(words):
            text = word.get("word", "")
            if index + 1 < len(words):
                text = f"{text} "
            token = {"text": text}
            transliteration = word.get("transliteration") or romanize_amharic(word.get("word", ""))
            if transliteration.strip():
                token["transliteration"] = transliteration
            tokens.append(token)
        tokenized[str(sentence["id"])] = tokens

    output_path.write_text(
        json.dumps(tokenized, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def build_armenian_tokens(course: str) -> None:
    explanations_path = STATIC_DATA / f"{course}_explanations.json"
    output_path = STATIC_DATA / f"{course}_tokens.json"
    explanations = json.loads(explanations_path.read_text(encoding="utf-8"))
    tokenized: dict[str, list[dict[str, str]]] = {}

    for sentence in explanations["data"]:
        tokens = []
        words = sentence.get("words", [])
        for index, word in enumerate(words):
            text = word.get("word", "")
            if index + 1 < len(words):
                text = f"{text} "
            token = {"text": text}
            transliteration = word.get("transliteration") or romanize_armenian(word.get("word", ""))
            if transliteration.strip():
                token["transliteration"] = transliteration
            tokens.append(token)
        tokenized[str(sentence["id"])] = tokens

    output_path.write_text(
        json.dumps(tokenized, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def copy_base_data() -> None:
    STATIC_DATA.mkdir(parents=True, exist_ok=True)
    for filename in SOURCE_FILES:
        shutil.copyfile(CORPORA / filename, STATIC_DATA / filename)


def enrich_tibetan_explanations(course: str) -> None:
    converter = pyewts.pyewts()
    path = STATIC_DATA / f"{course}_explanations.json"
    explanations = json.loads(path.read_text(encoding="utf-8"))
    all_words: list[str] = [
        word.get("word", "")
        for sentence in explanations["data"]
        for word in sentence.get("words", [])
    ]
    all_wylies = convert_items(converter, all_words)
    all_thls = convert_items_to_thl(all_words)
    offset = 0

    for sentence in explanations["data"]:
        words = sentence.get("words", [])
        length = len(words)
        wylies = all_wylies[offset : offset + length]
        thls = all_thls[offset : offset + length]
        offset += length
        for word, wylie, thl in zip(words, wylies, thls, strict=True):
            if wylie.strip():
                word["wylie"] = wylie
            if thl.strip():
                word["thl"] = thl

    path.write_text(
        json.dumps(explanations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def enrich_thai_explanations(course: str) -> None:
    path = STATIC_DATA / f"{course}_explanations.json"
    explanations = json.loads(path.read_text(encoding="utf-8"))

    for sentence in explanations["data"]:
        for word in sentence.get("words", []):
            paiboon = word.get("paiboon") or romanize_thai_paiboon(word.get("word", ""))
            if paiboon.strip():
                word["paiboon"] = paiboon

    path.write_text(
        json.dumps(explanations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def enrich_burmese_explanations(course: str) -> None:
    path = STATIC_DATA / f"{course}_explanations.json"
    explanations = json.loads(path.read_text(encoding="utf-8"))

    for sentence in explanations["data"]:
        for word in sentence.get("words", []):
            mlcts = word.get("mlcts", "")
            okell = word.get("okell") or romanize_burmese_okell(word.get("word", ""), mlcts)
            if okell.strip():
                word["okell"] = okell

    path.write_text(
        json.dumps(explanations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def enrich_khmer_explanations(course: str) -> None:
    path = STATIC_DATA / f"{course}_explanations.json"
    explanations = json.loads(path.read_text(encoding="utf-8"))

    for sentence in explanations["data"]:
        for word in sentence.get("words", []):
            text = word.get("word", "")
            transliteration = word.get("transliteration") or transliterate_khmer(text)
            transcription = word.get("transcription") or transcribe_khmer(text)
            if transliteration.strip():
                word["transliteration"] = transliteration
            if transcription.strip():
                word["transcription"] = transcription

    path.write_text(
        json.dumps(explanations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def enrich_amharic_explanations(course: str) -> None:
    path = STATIC_DATA / f"{course}_explanations.json"
    explanations = json.loads(path.read_text(encoding="utf-8"))

    for sentence in explanations["data"]:
        for word in sentence.get("words", []):
            transliteration = word.get("transliteration") or romanize_amharic(word.get("word", ""))
            if transliteration.strip():
                word["transliteration"] = transliteration

    path.write_text(
        json.dumps(explanations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def enrich_armenian_explanations(course: str) -> None:
    path = STATIC_DATA / f"{course}_explanations.json"
    explanations = json.loads(path.read_text(encoding="utf-8"))

    for sentence in explanations["data"]:
        for word in sentence.get("words", []):
            transliteration = word.get("transliteration") or romanize_armenian(word.get("word", ""))
            if transliteration.strip():
                word["transliteration"] = transliteration

    path.write_text(
        json.dumps(explanations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    copy_base_data()
    for course in TIBETAN_COURSES:
        build_tibetan_tokens(course)
        enrich_tibetan_explanations(course)
    for course in THAI_COURSES:
        enrich_thai_explanations(course)
        build_thai_tokens(course)
    for course in BURMESE_COURSES:
        enrich_burmese_explanations(course)
        build_burmese_tokens(course)
    for course in KHMER_COURSES:
        enrich_khmer_explanations(course)
        build_khmer_tokens(course)
    for course in AMHARIC_COURSES:
        enrich_amharic_explanations(course)
        build_amharic_tokens(course)
    for course in ARMENIAN_COURSES:
        enrich_armenian_explanations(course)
        build_armenian_tokens(course)


if __name__ == "__main__":
    main()
