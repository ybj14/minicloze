#!/usr/bin/env python3
"""Generate full-sentence word explanations for local A1 corpora."""

from __future__ import annotations

import argparse
from pathlib import Path

from explanation_utils import (
    PUNCTUATION,
    build_explanations_from_corpus,
    collect_unknowns,
    read_json,
    write_json,
)


ROOT = Path(__file__).resolve().parents[1]
CORPORA = ROOT / "minicloze-lib" / "corpora"

LANGS = {
    "tajik": {
        "language": "tajik",
        "corpus": CORPORA / "tajik_a1.json",
        "vocab": CORPORA / "tajik_a1_vocab.json",
        "output": CORPORA / "tajik_a1_explanations.json",
    },
    "thai": {
        "language": "thai",
        "corpus": CORPORA / "thai_a1.json",
        "vocab": CORPORA / "thai_a1_vocab.json",
        "output": CORPORA / "thai_a1_explanations.json",
    },
}


def stripped_token(value: str) -> str:
    return value.strip(PUNCTUATION).lower()


def compact_target(value: str) -> str:
    return "".join(char for char in value if not char.isspace() and char not in PUNCTUATION)


def collect_alignment_issues(
    corpus_path: Path,
    explanations: dict[str, list[dict[str, object]]],
    language: str,
) -> list[str]:
    corpus_rows = read_json(corpus_path)["data"]
    explanation_rows = explanations["data"]
    issues: list[str] = []
    if len(corpus_rows) != len(explanation_rows):
        issues.append(f"row count mismatch: corpus={len(corpus_rows)} explanations={len(explanation_rows)}")
        return issues

    for corpus_row, explanation_row in zip(corpus_rows, explanation_rows, strict=True):
        row_id = corpus_row["id"]
        if explanation_row["id"] != row_id:
            issues.append(f"{row_id}: explanation id is {explanation_row['id']}")
            continue
        words = explanation_row["words"]
        cloze = stripped_token(str(corpus_row.get("cloze_word") or ""))
        if cloze and not any(stripped_token(str(word["word"])) == cloze for word in words):
            issues.append(f"{row_id}: missing cloze {cloze}")
        if language == "thai":
            target = compact_target(corpus_row["translations"][0]["text"])
            rebuilt = "".join(str(word["word"]) for word in words)
            if rebuilt != target:
                issues.append(f"{row_id}: Thai token rebuild mismatch")
    return issues


def generate(lang: str, fail_on_unknown: bool) -> None:
    config = LANGS[lang]
    explanations = build_explanations_from_corpus(
        config["corpus"],
        config["vocab"],
        config["language"],
    )
    unknowns = collect_unknowns(explanations)
    alignment_issues = collect_alignment_issues(config["corpus"], explanations, config["language"])
    if fail_on_unknown:
        failures = []
        if unknowns:
            top = ", ".join(f"{word}={count}" for word, count in list(unknowns.items())[:30])
            failures.append(f"unexplained tokens remain: {top}")
        if alignment_issues:
            failures.append("alignment issues: " + "; ".join(alignment_issues[:30]))
        if failures:
            raise ValueError(f"{lang}: {'; '.join(failures)}")

    write_json(config["output"], explanations)
    rows = explanations["data"]
    word_count = sum(len(row["words"]) for row in rows)
    print(
        f"{lang}: wrote {config['output']} "
        f"({len(rows)} rows, {word_count} word explanations, {len(unknowns)} unknown tokens)"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("languages", nargs="*", choices=sorted(LANGS))
    parser.add_argument("--allow-unknown", action="store_true")
    args = parser.parse_args()

    requested = args.languages or sorted(LANGS)
    for lang in requested:
        generate(lang, fail_on_unknown=not args.allow_unknown)


if __name__ == "__main__":
    main()
