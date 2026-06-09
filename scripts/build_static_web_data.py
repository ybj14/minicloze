#!/usr/bin/env python3
"""Build static data extras used by the browser-only web app."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pyewts


ROOT = Path(__file__).resolve().parents[1]
STATIC_DATA = ROOT / "minicloze-web" / "static" / "data"
CORPORA = ROOT / "minicloze-lib" / "corpora"

TIBETAN_BREAKS = {"་", "༌", "།", "༎", "༏", "༐", "༑", "༔"}
SOURCE_FILES = [
    "mongolian_a1.json",
    "mongolian_a1_explanations.json",
    "mongolian_a1_vocab.json",
    "tibetan_a1.json",
    "tibetan_a1_explanations.json",
    "tibetan_a1_vocab.json",
]


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


def build_tibetan_tokens() -> None:
    converter = pyewts.pyewts()
    corpus_path = STATIC_DATA / "tibetan_a1.json"
    output_path = STATIC_DATA / "tibetan_a1_tokens.json"

    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    tokenized: dict[str, list[dict[str, str]]] = {}

    for sentence in corpus["data"]:
        translation = sentence.get("translations", [{}])[0].get("text", "")
        token_texts = tokenize_with_target(translation, sentence.get("cloze_word"))
        wylies = convert_items(converter, token_texts)
        tokenized[str(sentence["id"])] = [
            {"text": text, "wylie": wylie}
            for text, wylie in zip(token_texts, wylies, strict=True)
        ]

    output_path.write_text(
        json.dumps(tokenized, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def copy_base_data() -> None:
    STATIC_DATA.mkdir(parents=True, exist_ok=True)
    for filename in SOURCE_FILES:
        shutil.copyfile(CORPORA / filename, STATIC_DATA / filename)


def enrich_tibetan_explanations() -> None:
    converter = pyewts.pyewts()
    path = STATIC_DATA / "tibetan_a1_explanations.json"
    explanations = json.loads(path.read_text(encoding="utf-8"))

    for sentence in explanations["data"]:
        words = sentence.get("words", [])
        wylies = convert_items(converter, [word.get("word", "") for word in words])
        for word, wylie in zip(words, wylies, strict=True):
            if wylie.strip():
                word["wylie"] = wylie

    path.write_text(
        json.dumps(explanations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    copy_base_data()
    build_tibetan_tokens()
    enrich_tibetan_explanations()


if __name__ == "__main__":
    main()
