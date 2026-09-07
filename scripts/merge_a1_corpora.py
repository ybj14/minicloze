#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

from amharic_transliteration import transliterate as transliterate_amharic
from armenian_transliteration import romanize as romanize_armenian
from burmese_okell import romanize as romanize_burmese_okell
from georgian_transliteration import romanize as romanize_georgian
from khmer_romanization import transcribe as transcribe_khmer
from khmer_romanization import transliterate as transliterate_khmer


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
    "mongolian-swadesh": {
        "vocab": CORPORA / "mongolian_swadesh_vocab.json",
        "output": CORPORA / "mongolian_swadesh.json",
        "batches": [
            GENERATED / "mongolian_swadesh_001_104.json",
            GENERATED / "mongolian_swadesh_105_207.json",
        ],
        "id_start": -500000,
        "expected_count": 207,
        "expected_sentences": 621,
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
    "tibetan-swadesh": {
        "vocab": CORPORA / "tibetan_swadesh_vocab.json",
        "output": CORPORA / "tibetan_swadesh.json",
        "batches": [
            GENERATED / "tibetan_swadesh_001_104.json",
            GENERATED / "tibetan_swadesh_105_207.json",
        ],
        "id_start": -600000,
        "expected_count": 207,
        "expected_sentences": 621,
        "forbidden": ["ཞེས་པའི་ཚིག", "word “", "the word"],
    },
    "tajik": {
        "vocab": CORPORA / "tajik_a1_vocab.json",
        "output": CORPORA / "tajik_a1.json",
        "batches": [
            GENERATED / "tajik_001_125.json",
            GENERATED / "tajik_126_250.json",
            GENERATED / "tajik_251_375.json",
            GENERATED / "tajik_376_500.json",
        ],
        "id_start": -300000,
        "forbidden": ["калимаи", "маънои", "word “", "the word"],
        "standalone_target": True,
    },
    "tajik-swadesh": {
        "vocab": CORPORA / "tajik_swadesh_vocab.json",
        "output": CORPORA / "tajik_swadesh.json",
        "batches": [
            GENERATED / "tajik_swadesh_001_104.json",
            GENERATED / "tajik_swadesh_105_207.json",
        ],
        "id_start": -700000,
        "expected_count": 207,
        "expected_sentences": 621,
        "forbidden": ["калимаи", "маънои", "word “", "the word"],
        "standalone_target": True,
    },
    "thai": {
        "vocab": CORPORA / "thai_a1_vocab.json",
        "output": CORPORA / "thai_a1.json",
        "batches": [
            GENERATED / "thai_001_125.json",
            GENERATED / "thai_126_250.json",
            GENERATED / "thai_251_375.json",
            GENERATED / "thai_376_500.json",
        ],
        "id_start": -400000,
        "forbidden": ["คำว่า", "word “", "the word"],
    },
    "thai-swadesh": {
        "vocab": CORPORA / "thai_swadesh_vocab.json",
        "output": CORPORA / "thai_swadesh.json",
        "batches": [
            GENERATED / "thai_swadesh_001_104.json",
            GENERATED / "thai_swadesh_105_207.json",
        ],
        "id_start": -800000,
        "expected_count": 207,
        "expected_sentences": 621,
        "forbidden": ["คำว่า", "word “", "the word"],
    },
    "burmese": {
        "vocab": CORPORA / "burmese_a1_vocab.json",
        "output": CORPORA / "burmese_a1.json",
        "explanations": CORPORA / "burmese_a1_explanations.json",
        "batches": [
            GENERATED / "burmese_001_050.json",
            GENERATED / "burmese_051_100.json",
            GENERATED / "burmese_101_150.json",
            GENERATED / "burmese_151_200.json",
            GENERATED / "burmese_201_250.json",
            GENERATED / "burmese_251_300.json",
            GENERATED / "burmese_301_350.json",
            GENERATED / "burmese_351_400.json",
            GENERATED / "burmese_401_450.json",
            GENERATED / "burmese_451_500.json",
        ],
        "id_start": -900000,
        "forbidden": ["word “", "the word"],
        "vocab_from_batches": True,
        "explanations_from_batches": True,
        "max_frame_repeats": 8,
    },
    "burmese-swadesh": {
        "vocab": CORPORA / "burmese_swadesh_vocab.json",
        "output": CORPORA / "burmese_swadesh.json",
        "explanations": CORPORA / "burmese_swadesh_explanations.json",
        "batches": [
            GENERATED / "burmese_swadesh_001_041.json",
            GENERATED / "burmese_swadesh_042_083.json",
            GENERATED / "burmese_swadesh_084_124.json",
            GENERATED / "burmese_swadesh_125_165.json",
            GENERATED / "burmese_swadesh_166_207.json",
        ],
        "id_start": -1000000,
        "expected_count": 207,
        "expected_sentences": 621,
        "forbidden": ["word “", "the word"],
        "vocab_from_batches": True,
        "explanations_from_batches": True,
        "max_frame_repeats": 8,
    },
    "khmer": {
        "vocab": CORPORA / "khmer_a1_vocab.json",
        "output": CORPORA / "khmer_a1.json",
        "explanations": CORPORA / "khmer_a1_explanations.json",
        "batches": [
            GENERATED / "khmer_001_050.json",
            GENERATED / "khmer_051_100.json",
            GENERATED / "khmer_101_150.json",
            GENERATED / "khmer_151_200.json",
            GENERATED / "khmer_201_250.json",
            GENERATED / "khmer_251_300.json",
            GENERATED / "khmer_301_350.json",
            GENERATED / "khmer_351_400.json",
            GENERATED / "khmer_401_450.json",
            GENERATED / "khmer_451_500.json",
        ],
        "id_start": -1100000,
        "forbidden": ["មានន័យ", "word “", "the word"],
        "vocab_from_batches": True,
        "explanations_from_batches": True,
        "unspaced_explanations": True,
        "max_frame_repeats": 50,
    },
    "khmer-swadesh": {
        "vocab": CORPORA / "khmer_swadesh_vocab.json",
        "output": CORPORA / "khmer_swadesh.json",
        "explanations": CORPORA / "khmer_swadesh_explanations.json",
        "batches": [
            GENERATED / "khmer_swadesh_001_041.json",
            GENERATED / "khmer_swadesh_042_083.json",
            GENERATED / "khmer_swadesh_084_124.json",
            GENERATED / "khmer_swadesh_125_165.json",
            GENERATED / "khmer_swadesh_166_207.json",
        ],
        "id_start": -1200000,
        "expected_count": 207,
        "expected_sentences": 621,
        "forbidden": ["មានន័យ", "word “", "the word"],
        "vocab_from_batches": True,
        "explanations_from_batches": True,
        "unspaced_explanations": True,
        "max_frame_repeats": 50,
    },
    "amharic": {
        "vocab": CORPORA / "amharic_a1_vocab.json",
        "output": CORPORA / "amharic_a1.json",
        "explanations": CORPORA / "amharic_a1_explanations.json",
        "batches": [
            GENERATED / "amharic_001_050.json",
            GENERATED / "amharic_051_100.json",
            GENERATED / "amharic_101_150.json",
            GENERATED / "amharic_151_200.json",
            GENERATED / "amharic_201_250.json",
            GENERATED / "amharic_251_300.json",
            GENERATED / "amharic_301_350.json",
            GENERATED / "amharic_351_400.json",
            GENERATED / "amharic_401_450.json",
            GENERATED / "amharic_451_500.json",
        ],
        "id_start": -1300000,
        "forbidden": ["ቃል ማለት", "የሚለው", "word “", "the word"],
        "vocab_from_batches": True,
        "explanations_from_batches": True,
    },
    "amharic-swadesh": {
        "vocab": CORPORA / "amharic_swadesh_vocab.json",
        "output": CORPORA / "amharic_swadesh.json",
        "explanations": CORPORA / "amharic_swadesh_explanations.json",
        "batches": [
            GENERATED / "amharic_swadesh_001_041.json",
            GENERATED / "amharic_swadesh_042_083.json",
            GENERATED / "amharic_swadesh_084_124.json",
            GENERATED / "amharic_swadesh_125_165.json",
            GENERATED / "amharic_swadesh_166_207.json",
        ],
        "id_start": -1400000,
        "expected_count": 207,
        "expected_sentences": 621,
        "forbidden": ["ቃል ማለት", "የሚለው", "word “", "the word"],
        "vocab_from_batches": True,
        "explanations_from_batches": True,
    },
    "armenian": {
        "vocab": CORPORA / "armenian_a1_vocab.json",
        "output": CORPORA / "armenian_a1.json",
        "explanations": CORPORA / "armenian_a1_explanations.json",
        "batches": [
            GENERATED / "armenian_001_050.json",
            GENERATED / "armenian_051_100.json",
            GENERATED / "armenian_101_150.json",
            GENERATED / "armenian_151_200.json",
            GENERATED / "armenian_201_250.json",
            GENERATED / "armenian_251_300.json",
            GENERATED / "armenian_301_350.json",
            GENERATED / "armenian_351_400.json",
            GENERATED / "armenian_401_450.json",
            GENERATED / "armenian_451_500.json",
        ],
        "id_start": -1500000,
        "forbidden": ["բառը", "նշանակում է", "word “", "the word"],
        "vocab_from_batches": True,
        "explanations_from_batches": True,
    },
    "armenian-swadesh": {
        "vocab": CORPORA / "armenian_swadesh_vocab.json",
        "output": CORPORA / "armenian_swadesh.json",
        "explanations": CORPORA / "armenian_swadesh_explanations.json",
        "batches": [
            GENERATED / "armenian_swadesh_001_041.json",
            GENERATED / "armenian_swadesh_042_083.json",
            GENERATED / "armenian_swadesh_084_124.json",
            GENERATED / "armenian_swadesh_125_165.json",
            GENERATED / "armenian_swadesh_166_207.json",
        ],
        "id_start": -1600000,
        "expected_count": 207,
        "expected_sentences": 621,
        "forbidden": ["բառը", "նշանակում է", "word “", "the word"],
        "vocab_from_batches": True,
        "explanations_from_batches": True,
    },
    "georgian": {
        "vocab": CORPORA / "georgian_a1_vocab.json",
        "output": CORPORA / "georgian_a1.json",
        "explanations": CORPORA / "georgian_a1_explanations.json",
        "batches": [
            GENERATED / "georgian_001_050.json",
            GENERATED / "georgian_051_100.json",
            GENERATED / "georgian_101_150.json",
            GENERATED / "georgian_151_200.json",
            GENERATED / "georgian_201_250.json",
            GENERATED / "georgian_251_300.json",
            GENERATED / "georgian_301_350.json",
            GENERATED / "georgian_351_400.json",
            GENERATED / "georgian_401_450.json",
            GENERATED / "georgian_451_500.json",
        ],
        "id_start": -1700000,
        "forbidden": ["სიტყვა", "ნიშნავს", "word “", "the word"],
        "vocab_from_batches": True,
        "explanations_from_batches": True,
    },
    "georgian-swadesh": {
        "vocab": CORPORA / "georgian_swadesh_vocab.json",
        "output": CORPORA / "georgian_swadesh.json",
        "explanations": CORPORA / "georgian_swadesh_explanations.json",
        "batches": [
            GENERATED / "georgian_swadesh_001_041.json",
            GENERATED / "georgian_swadesh_042_083.json",
            GENERATED / "georgian_swadesh_084_124.json",
            GENERATED / "georgian_swadesh_125_165.json",
            GENERATED / "georgian_swadesh_166_207.json",
        ],
        "id_start": -1800000,
        "expected_count": 207,
        "expected_sentences": 621,
        "forbidden": ["სიტყვა", "ნიშნავს", "word “", "the word"],
        "vocab_from_batches": True,
        "explanations_from_batches": True,
    },
}

BAD_ENGLISH_PATTERNS = [
    re.compile(pattern, re.I)
    for pattern in [
        r"\bwho is the book\b",
        r"\bwhat is the book\b",
        r"\bwhere came\b",
        r"\bwhen is the book\b",
        r"\bhow came\b",
        r"\bi see the hello\b",
        r"\bthe thanks is\b",
    ]
]


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
            words = sentence.get("words")
            if word not in target:
                errors.append(
                    f"{batch_path}: index {index} sentence {sentence_index} lacks target word {word!r}"
                )
            if config.get("explanations_from_batches"):
                if not isinstance(words, list) or not words:
                    errors.append(
                        f"{batch_path}: index {index} sentence {sentence_index} must include words explanations"
                    )
                else:
                    separator = "" if config.get("unspaced_explanations") else " "
                    token_text = separator.join(
                        str(part.get("word", "")).strip()
                        for part in words
                        if str(part.get("word", "")).strip()
                    )
                    normalized_target = target.strip().rstrip("။.།។៕?!።፧፣፤፥፦։՞՜՛՝჻")
                    if config.get("unspaced_explanations"):
                        normalized_target = re.sub(r"\s+", "", normalized_target)
                    if token_text != normalized_target:
                        errors.append(
                            f"{batch_path}: index {index} sentence {sentence_index} words do not match target"
                        )
                    for part in words:
                        if not str(part.get("word", "")).strip() or not str(part.get("gloss", "")).strip():
                            errors.append(
                                f"{batch_path}: index {index} sentence {sentence_index} has empty explanation"
                            )
            if config.get("standalone_target") and not re.search(
                rf"(?<!\S){re.escape(word)}(?!\S)", target
            ):
                errors.append(
                    f"{batch_path}: index {index} sentence {sentence_index} does not use standalone target word {word!r}"
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


def load_vocab_from_batches(config):
    vocab_by_index = {}
    errors = []
    for batch_path in config["batches"]:
        data = load_json(batch_path)
        if not isinstance(data, list):
            raise ValueError(f"{batch_path}: expected a JSON array")
        for item in data:
            index = item.get("vocab_index")
            word = str(item.get("word", "")).strip()
            gloss = str(item.get("gloss", "")).strip()
            if not isinstance(index, int) or not word or not gloss:
                errors.append(f"{batch_path}: malformed vocabulary item {item!r}")
                continue
            source = str(item.get("source", "Codex-authored Burmese local corpus")).strip()
            if index in vocab_by_index:
                errors.append(f"{batch_path}: duplicate vocab_index {index}")
                continue
            vocab_by_index[index] = {"word": word, "gloss": gloss, "source": source}

    expected_count = config.get("expected_count", 500)
    expected_indices = set(range(1, expected_count + 1))
    missing = sorted(expected_indices - set(vocab_by_index))
    extra = sorted(set(vocab_by_index) - expected_indices)
    if missing:
        errors.append(f"missing vocab indices {missing[:20]}")
    if extra:
        errors.append(f"unexpected vocab indices {extra[:20]}")
    if errors:
        raise ValueError("\n".join(errors[:80]))
    return [vocab_by_index[index] for index in range(1, expected_count + 1)]


def normalize_english_frame(text, gloss):
    frame = str(text).lower().strip()
    frame = re.sub(r"\s+", " ", frame)
    candidates = {str(gloss).lower().strip()}
    candidates.add(re.sub(r"^to\s+", "", str(gloss).lower().strip()))
    for candidate in sorted(candidates, key=len, reverse=True):
        if not candidate:
            continue
        forms = {candidate}
        if not candidate.endswith("s"):
            forms.add(f"{candidate}s")
        if candidate.endswith("y"):
            forms.add(f"{candidate[:-1]}ies")
        for form in sorted(forms, key=len, reverse=True):
            frame = re.sub(rf"\b{re.escape(form)}\b", "{x}", frame)
    return frame


def validate_naturalness(lang, config, batches):
    max_repeats = config.get("max_frame_repeats")
    if not max_repeats:
        return

    frame_counts = {}
    frame_examples = {}
    errors = []
    for item in batches:
        gloss = item.get("gloss", "")
        for sentence in item.get("sentences", []):
            text = sentence.get("text", "")
            if any(pattern.search(text) for pattern in BAD_ENGLISH_PATTERNS):
                errors.append(
                    f"{lang}: suspicious English sentence at vocab_index {item.get('vocab_index')}: {text!r}"
                )
            frame = normalize_english_frame(text, gloss)
            frame_counts[frame] = frame_counts.get(frame, 0) + 1
            frame_examples.setdefault(frame, text)

    for frame, count in sorted(frame_counts.items(), key=lambda item: item[1], reverse=True):
        if count > max_repeats:
            errors.append(
                f"{lang}: repeated English frame {frame!r} appears {count} times; "
                f"example: {frame_examples[frame]!r}"
            )

    if errors:
        raise ValueError("\n".join(errors[:80]))


def enrich_burmese_words(words):
    for word in words:
        text = str(word.get("word", "")).strip()
        mlcts = str(word.get("mlcts", "")).strip()
        okell = str(word.get("okell", "")).strip() or romanize_burmese_okell(text, mlcts)
        if okell:
            word["okell"] = okell
    return words


def enrich_khmer_words(words):
    for word in words:
        text = str(word.get("word", "")).strip()
        transliteration = str(word.get("transliteration", "")).strip() or transliterate_khmer(text)
        transcription = str(word.get("transcription", "")).strip() or transcribe_khmer(text)
        if transliteration:
            word["transliteration"] = transliteration
        if transcription:
            word["transcription"] = transcription
    return words



def enrich_amharic_words(words):
    for word in words:
        text = str(word.get("word", "")).strip()
        # Always refresh from Ethi-translit (do not keep stale SERA values).
        transliteration = transliterate_amharic(text)
        if transliteration.strip():
            word["transliteration"] = transliteration
    return words


def enrich_armenian_words(words):
    for word in words:
        text = str(word.get("word", "")).strip()
        transliteration = str(word.get("transliteration", "")).strip() or romanize_armenian(text)
        if transliteration:
            word["transliteration"] = transliteration
    return words


def enrich_georgian_words(words):
    for word in words:
        text = str(word.get("word", "")).strip()
        transliteration = str(word.get("transliteration", "")).strip() or romanize_georgian(text)
        if transliteration:
            word["transliteration"] = transliteration
    return words


def expected_range(path):
    stem = path.stem
    start, end = stem.rsplit("_", 2)[1:]
    return int(start), int(end)


def merge_language(lang, config):
    vocab = load_vocab_from_batches(config) if config.get("vocab_from_batches") else load_json(config["vocab"])
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

    validate_naturalness(lang, config, all_batches)

    rows = []
    explanation_rows = []
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
            if config.get("explanations_from_batches"):
                words = sentence["words"]
                if lang.startswith("burmese"):
                    words = enrich_burmese_words(words)
                elif lang.startswith("khmer"):
                    words = enrich_khmer_words(words)
                elif lang.startswith("amharic"):
                    words = enrich_amharic_words(words)
                elif lang.startswith("armenian"):
                    words = enrich_armenian_words(words)
                elif lang.startswith("georgian"):
                    words = enrich_georgian_words(words)
                explanation_rows.append(
                    {
                        "id": current_id,
                        "words": words,
                    }
                )
            current_id -= 1

    expected_count = config.get("expected_count", 500)
    expected_sentences = config.get("expected_sentences", expected_count * 3)
    if len(seen) != expected_count or len(rows) != expected_sentences:
        raise ValueError(
            f"{lang}: expected {expected_count} words and {expected_sentences} sentences, "
            f"got {len(seen)} and {len(rows)}"
        )

    config["output"].write_text(
        json.dumps({"data": rows}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if config.get("vocab_from_batches"):
        config["vocab"].write_text(
            json.dumps(vocab, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"{lang}: wrote {config['vocab']} ({len(vocab)} words)")
    if config.get("explanations_from_batches"):
        config["explanations"].write_text(
            json.dumps({"data": explanation_rows}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"{lang}: wrote {config['explanations']} ({len(explanation_rows)} rows)")
    print(f"{lang}: wrote {config['output']} ({len(rows)} sentences)")


def main():
    requested = sys.argv[1:] or sorted(LANGS)
    for lang in requested:
        merge_language(lang, LANGS[lang])


if __name__ == "__main__":
    main()
