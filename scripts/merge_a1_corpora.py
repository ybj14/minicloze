#!/usr/bin/env python3
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORPORA = ROOT / "minicloze-lib" / "corpora"
GENERATED = CORPORA / "generated"

LANGS = {
    "mongolian": {
        "vocab": CORPORA / "mongolian_a1_vocab.json",
        "output": CORPORA / "mongolian_a1.json",
        "batches": [
            GENERATED / "mongolian_001_125.json",
            GENERATED / "mongolian_126_250.json",
            GENERATED / "mongolian_251_375.json",
            GENERATED / "mongolian_376_500.json",
        ],
        "id_start": -100000,
        "forbidden": [" гэдэг үг", "гэдэг үгийг", "word “", "the word"],
    },
    "tibetan": {
        "vocab": CORPORA / "tibetan_a1_vocab.json",
        "output": CORPORA / "tibetan_a1.json",
        "batches": [
            GENERATED / "tibetan_001_125.json",
            GENERATED / "tibetan_126_250.json",
            GENERATED / "tibetan_251_375.json",
            GENERATED / "tibetan_376_500.json",
        ],
        "id_start": -200000,
        "forbidden": ["ཞེས་པའི་ཚིག", "word “", "the word"],
    },
}


def load_json(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def validate_batch(lang, config, expected_vocab, batch_path):
    data = load_json(batch_path)
    if not isinstance(data, list):
        raise ValueError(f"{batch_path}: expected a JSON array")

    by_index = {item["vocab_index"]: item for item in data}
    errors = []

    for index, vocab_item in expected_vocab.items():
        item = by_index.get(index)
        if item is None:
            errors.append(f"{batch_path}: missing vocab_index {index}")
            continue

        word = vocab_item["word"].strip("།")
        if item.get("word", "").strip("།") != word:
            errors.append(f"{batch_path}: index {index} word mismatch")

        sentences = item.get("sentences")
        if not isinstance(sentences, list) or len(sentences) != 3:
            errors.append(f"{batch_path}: index {index} must have exactly 3 sentences")
            continue

        for sentence_index, sentence in enumerate(sentences, 1):
            target = sentence.get("target", "")
            text = sentence.get("text", "")
            if word not in target:
                errors.append(
                    f"{batch_path}: index {index} sentence {sentence_index} lacks target word {word!r}"
                )
            lower_text = text.lower()
            if any(marker in target or marker in lower_text for marker in config["forbidden"]):
                errors.append(
                    f"{batch_path}: index {index} sentence {sentence_index} has meta-language"
                )

    extra = sorted(set(by_index) - set(expected_vocab))
    if extra:
        errors.append(f"{batch_path}: unexpected indices {extra[:10]}")

    if errors:
        raise ValueError("\n".join(errors[:80]))

    return data


def expected_range(path):
    stem = path.stem
    start, end = stem.rsplit("_", 2)[1:]
    return int(start), int(end)


def merge_language(lang, config):
    vocab = load_json(config["vocab"])
    all_batches = []

    for batch_path in config["batches"]:
        if not batch_path.exists():
            raise FileNotFoundError(batch_path)
        start, end = expected_range(batch_path)
        expected_vocab = {
            index: vocab[index - 1]
            for index in range(start, end + 1)
        }
        all_batches.extend(validate_batch(lang, config, expected_vocab, batch_path))

    rows = []
    current_id = config["id_start"]
    seen = set()

    for item in sorted(all_batches, key=lambda entry: entry["vocab_index"]):
        index = item["vocab_index"]
        if index in seen:
            raise ValueError(f"{lang}: duplicate vocab_index {index}")
        seen.add(index)

        word = item["word"].strip("།")
        for sentence in item["sentences"]:
            rows.append(
                {
                    "id": current_id,
                    "text": sentence["text"],
                    "cloze_word": word,
                    "translations": [
                        {
                            "id": current_id,
                            "text": sentence["target"],
                        }
                    ],
                }
            )
            current_id -= 1

    if len(seen) != 500 or len(rows) != 1500:
        raise ValueError(f"{lang}: expected 500 words and 1500 sentences, got {len(seen)} and {len(rows)}")

    config["output"].write_text(
        json.dumps({"data": rows}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"{lang}: wrote {config['output']} ({len(rows)} sentences)")


def main():
    requested = sys.argv[1:] or sorted(LANGS)
    for lang in requested:
        merge_language(lang, LANGS[lang])


if __name__ == "__main__":
    main()
