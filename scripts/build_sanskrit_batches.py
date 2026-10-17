#!/usr/bin/env python3
"""Convert reviewed Sanskrit authoring files into generated batch JSON.

The authoring files under scripts/data/sanskrit/*.txt hold hand-authored
(LLM-as-language-author) Sanskrit sentences in IAST with natural English
translations. This script does NOT author content: it only

* converts IAST to Devanagari (scripts/sanskrit_transliteration.py),
* attaches per-token English glosses from the reviewed lexicon
  (scripts/data/sanskrit/lexicon.tsv, or inline ``token{gloss}`` overrides),
* records the per-sentence cloze form (the token marked with ``*``),
* for the classical course, resolves each ``## key`` against the downloaded
  GRETIL plain-text corpora and attaches the verifiable citation + original
  line, failing loudly when a key is not found,
* splits items into the standard batch files under corpora/generated/.

Authoring format::

    @ <index> | <lemma in IAST> | <english gloss>
    <iast sentence with *cloze token> = <English sentence> [## <corpus key>]

Conventions: pedagogical pausa spelling (no external vowel/visarga sandhi,
word-final m before a consonant written as anusvāra ṃ), as in NCERT Ruchira
and Samskrita Bharati primers.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

from sanskrit_transliteration import iast_to_devanagari

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "scripts" / "data" / "sanskrit"
GENERATED = ROOT / "minicloze-lib" / "corpora" / "generated"
CORPUS_DIR = Path(
    __import__("os").environ.get("SANSKRIT_CORPUS_DIR", "/workspace/sa_corpus")
)

COURSES = {
    "a1": {
        "source": DATA / "a1.txt",
        "stem": "sanskrit",
        "count": 500,
        "batch_size": 50,
        "label": "LLM-authored Sanskrit A1 2026-10-06",
    },
    "swadesh": {
        "source": DATA / "swadesh.txt",
        "stem": "sanskrit_swadesh",
        "count": 207,
        "ranges": [(1, 41), (42, 83), (84, 124), (125, 165), (166, 207)],
        "label": "Wiktionary Module:Swadesh/data/sa (overrides documented in scripts/data/sanskrit/README.md); LLM-authored sentences 2026-10-06",
    },
    "classical": {
        "source": DATA / "classical.txt",
        "stem": "sanskrit_a1_classical",
        "count": 500,
        "batch_size": 50,
        "label": "Sanskrit A1 Classical: sentences adapted from cited GRETIL texts 2026-10-06",
    },
}

GRETIL_BASE = "https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/plaintext/"
CORPORA_FILES = {
    "hit": ("Nārāyaṇa, Hitopadeśa (GRETIL e-text, J. Brzezinski / U. Stiehl)", "sa_nArAyaNa-hitopadeza.txt"),
    "pt": ("Viṣṇuśarman, Pañcatantra (GRETIL e-text)", "sa_viSNuzarman-paJcatantra.txt"),
    "bhg": ("Bhagavadgītā (GRETIL e-text, with commentaries file; mūla verses cited)", "sa_bhagavadgItA-comm.txt"),
    "ram": ("Vālmīki, Rāmāyaṇa (GRETIL e-text, critical edition)", "sa_rAmAyaNa.txt"),
    "manu": ("Manusmṛti (GRETIL e-text)", "sa_manusmRti.txt"),
    "bhartr": ("Bhartṛhari, Śatakatraya (GRETIL e-text)", "sa_bhatRhari-zatakatraya.txt"),
    "vet": ("Somadeva, Kathāsaritsāgara: Vetālapañcaviṃśatikā (GRETIL e-text)", "sa_somadeva-kathAsaritsAgaravetAlapaJcaviMzatikA.txt"),
}

TRAIL = ".?!"
INNER_PUNCT = ",;:"


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def load_lexicon(course: str) -> dict[str, str]:
    """Merge the shared lexicons; lexicon_classical.tsv is used only by the classical course.

    The classical lexicon is consulted first there because its glosses follow the
    classical contexts (e.g. pātre = "to a worthy person", not "in the pot").
    """
    lexicon: dict[str, str] = {}
    paths = [path for path in sorted(DATA.glob("lexicon*.tsv")) if path.name != "lexicon_classical.tsv"]
    if course == "classical":
        paths.insert(0, DATA / "lexicon_classical.tsv")
    for path in paths:
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = nfc(line.strip())
            if not line or line.startswith("#"):
                continue
            for entry in line.split(" | "):
                if "\t" in entry:
                    form, gloss = entry.split("\t", 1)
                elif "=" in entry:
                    form, gloss = entry.split("=", 1)
                else:
                    raise ValueError(f"{path}:{line_no}: malformed lexicon entry {entry!r}")
                form, gloss = form.strip(), gloss.strip()
                if not form or not gloss:
                    raise ValueError(f"{path}:{line_no}: malformed lexicon entry {entry!r}")
                if form in lexicon and lexicon[form] != gloss:
                    print(f"lexicon: duplicate {form!r} ({lexicon[form]!r} kept, {gloss!r} ignored)")
                lexicon.setdefault(form, gloss)
    return lexicon


def parse_source(path: Path) -> list[dict]:
    items: list[dict] = []
    current: dict | None = None
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = nfc(raw.strip())
        if not line or line.startswith("#"):
            continue
        if line.startswith("@"):
            parts = [part.strip() for part in line[1:].split("|")]
            if len(parts) < 3:
                raise ValueError(f"{path}:{line_no}: header needs index | lemma | gloss")
            current = {
                "index": int(parts[0]),
                "lemma": parts[1],
                "gloss": parts[2],
                "line": line_no,
                "sentences": [],
            }
            items.append(current)
            continue
        if current is None:
            raise ValueError(f"{path}:{line_no}: sentence before header")
        key = None
        if "##" in line:
            line, key = [part.strip() for part in line.split("##", 1)]
        if " = " not in line:
            raise ValueError(f"{path}:{line_no}: sentence needs ' = English'")
        sa, en = [part.strip() for part in line.split(" = ", 1)]
        current["sentences"].append({"sa": sa, "en": en, "key": key, "line": line_no})
    return items


REF_RE = re.compile(r"(?://|\|\|)\s*([A-Za-z]+_\d+(?:[.,]\d+)+)|\b(R_\d+,\d+\.\d+)\s*$")


def split_segments(text: str) -> list[str]:
    """Split a corpus line into daṇḍa-delimited clauses (single "|"), keeping
    verse-final markers out."""
    text = REF_RE.sub("", text)
    text = re.sub(r"\[=[^\]]*\]", "", text)
    parts = re.split(r"(?<!\|)\|(?!\|)|//", text)
    return [part.strip(" |-/") for part in parts if part.strip(" |-/")]


class CorpusIndex:
    """Index of the GRETIL plain-text files.

    Keys in the authoring file are either ``code@LINE.SEG`` (line number in the
    GRETIL file and 1-based daṇḍa clause index, as printed by
    ``scripts/data/sanskrit/find_classical.py``) or ``[code:]substring``.
    """

    def __init__(self) -> None:
        self.files: dict[str, list[str]] = {}
        self.locations: dict[str, list[str]] = {}
        for code, (_title, filename) in CORPORA_FILES.items():
            path = CORPUS_DIR / filename
            if not path.exists():
                continue
            raw_lines = [nfc(line) for line in path.read_text(encoding="utf-8").splitlines()]
            refs = [None] * len(raw_lines)
            for i, line in enumerate(raw_lines):
                match = REF_RE.search(line)
                if match:
                    refs[i] = match.group(1) or match.group(2)
            locations = [""] * len(raw_lines)
            next_ref = ""
            for i in range(len(raw_lines) - 1, -1, -1):
                line = raw_lines[i].strip()
                if refs[i]:
                    next_ref = refs[i]
                    locations[i] = f"verse {refs[i]}"
                elif not line:
                    continue
                else:
                    nxt = next((j for j in range(i + 1, min(i + 3, len(raw_lines))) if raw_lines[j].strip()), None)
                    is_half_verse = (
                        nxt is not None and refs[nxt] and len(line) < 120
                        and re.search(r"(\||/)\s*$|[a-zāīūṛṃḥ]\s*$", line)
                    )
                    if is_half_verse:
                        locations[i] = f"verse {refs[nxt]}"
                    elif next_ref:
                        locations[i] = f"prose passage preceding verse {next_ref}"
                    else:
                        locations[i] = f"line {i + 1}"
            self.files[code] = raw_lines
            self.locations[code] = locations

    @staticmethod
    def squash(text: str) -> str:
        return re.sub(r"[\s\-|/']+", "", text.lower())

    def find(self, key: str) -> tuple[str, int, str, str]:
        match = re.fullmatch(r"(\w+)@(\d+)(?:\.(\d+))?", key.strip())
        if match:
            code, line_no, seg = match.group(1), int(match.group(2)), match.group(3)
            if code not in self.files or not (1 <= line_no <= len(self.files[code])):
                raise KeyError(key)
            line = self.files[code][line_no - 1]
            segments = split_segments(line)
            if seg is not None:
                index = int(seg) - 1
                if not (0 <= index < len(segments)):
                    raise KeyError(key)
                text = segments[index]
            else:
                text = " | ".join(segments)
            return code, line_no, text, self.locations[code][line_no - 1]
        code = None
        if ":" in key and key.split(":", 1)[0] in CORPORA_FILES:
            code, key = key.split(":", 1)
        needle = self.squash(nfc(key))
        for file_code, lines in self.files.items():
            if code is not None and file_code != code:
                continue
            for i, line in enumerate(lines):
                if needle in self.squash(line):
                    segment = next((seg for seg in split_segments(line) if needle in self.squash(seg)), line.strip())
                    return file_code, i + 1, segment, self.locations[file_code][i]
        raise KeyError(key)


def lookup(lexicon: dict[str, str], form: str) -> str | None:
    if form in lexicon:
        return lexicon[form]
    if form.endswith("ṃ") and form[:-1] + "m" in lexicon:
        return lexicon[form[:-1] + "m"]
    if form.endswith("m") and form[:-1] + "ṃ" in lexicon:
        return lexicon[form[:-1] + "ṃ"]
    return None


VOWELS = tuple("aāiīuūṛṝḷeo")


def normalize_final_m(tokens: list[str]) -> list[str]:
    """Orthographic rule: word-final m is written ṃ (anusvāra) before a consonant
    and m before a vowel, before punctuation, or at the end of the sentence."""
    out = []
    for i, token in enumerate(tokens):
        m = re.match(r"^(.*?)([mṃ])((?:\{[^}]*\})?)([.?!,;:]*)$", token)
        if m and m.group(1).lstrip("*"):
            stem, _final, gloss, punct = m.groups()
            nxt = tokens[i + 1].lstrip("*") if i + 1 < len(tokens) else ""
            if punct or not nxt or nxt.startswith(VOWELS):
                final = "m"
            else:
                final = "ṃ"
            token = f"{stem}{final}{gloss}{punct}"
        out.append(token)
    return out


def clean_token(token: str) -> str:
    return token.strip(TRAIL + INNER_PUNCT + "*")


def build_item(item: dict, lexicon: dict[str, str], unknown: dict[str, int], label: str,
               corpus: CorpusIndex | None, errors: list[str]) -> dict:
    lemma_deva = iast_to_devanagari(item["lemma"])
    sentences = []
    for sentence in item["sentences"]:
        sa = sentence["sa"]
        tokens = normalize_final_m(sa.split())
        words = []
        cloze = None
        rendered_tokens = []
        for position, token in enumerate(tokens):
            inline_gloss = None
            match = re.search(r"\{([^}]*)\}", token)
            if match:
                inline_gloss = match.group(1).strip()
                token = token[: match.start()] + token[match.end():]
            is_target = token.startswith("*")
            token = token.lstrip("*")
            rendered_tokens.append(token)
            bare = token.strip(TRAIL + INNER_PUNCT)
            word_iast = token
            if position == len(tokens) - 1:
                word_iast = token.rstrip(TRAIL)
            gloss = inline_gloss or lookup(lexicon, bare)
            if is_target:
                cloze = bare
                gloss = gloss or item["gloss"]
            if not gloss:
                unknown[bare] = unknown.get(bare, 0) + 1
                gloss = "?"
            word = {
                "word": iast_to_devanagari(word_iast),
                "gloss": gloss,
                "transliteration": word_iast,
            }
            if is_target:
                word["note"] = "target"
            words.append(word)
        if cloze is None:
            errors.append(f"line {sentence['line']}: no *cloze token in {sa!r}")
            cloze = item["lemma"]
        iast_sentence = " ".join(rendered_tokens)
        target = iast_to_devanagari(iast_sentence)
        target = re.sub(r"\.$", "।", target)
        if not re.search(r"[।?!]$", target):
            errors.append(f"line {sentence['line']}: sentence must end with . ? or !")
        row = {
            "target": target,
            "text": sentence["en"],
            "cloze_word": iast_to_devanagari(cloze),
            "transliteration": iast_sentence,
            "words": words,
        }
        if sentence.get("key"):
            if corpus is None:
                errors.append(f"line {sentence['line']}: key given but no corpus loaded")
            else:
                try:
                    code, line_no, text, ref = corpus.find(sentence["key"])
                    title, filename = CORPORA_FILES[code]
                    row["citation"] = (
                        f"Adapted from {title}, {ref} — {GRETIL_BASE}{filename} (line {line_no})"
                    )
                    row["source_text"] = text
                except KeyError:
                    errors.append(
                        f"line {sentence['line']}: corpus key not found: {sentence['key']!r}"
                    )
        sentences.append(row)
    out = {
        "vocab_index": item["index"],
        "word": lemma_deva,
        "gloss": item["gloss"],
        "transliteration": item["lemma"],
        "source": label,
        "sentences": sentences,
    }
    return out


def batch_ranges(config: dict) -> list[tuple[int, int]]:
    if "ranges" in config:
        return config["ranges"]
    size = config["batch_size"]
    return [(start, min(start + size - 1, config["count"])) for start in range(1, config["count"] + 1, size)]


def build(course: str, write: bool = True) -> int:
    config = COURSES[course]
    lexicon = load_lexicon(course)
    items = parse_source(config["source"])
    corpus = CorpusIndex() if course == "classical" else None
    unknown: dict[str, int] = {}
    errors: list[str] = []
    built = []
    seen = set()
    for item in items:
        if item["index"] in seen:
            errors.append(f"duplicate index {item['index']}")
        seen.add(item["index"])
        if len(item["sentences"]) != 3:
            errors.append(f"index {item['index']} ({item['lemma']}) has {len(item['sentences'])} sentences")
        built.append(build_item(item, lexicon, unknown, config["label"], corpus, errors))
    if unknown:
        print(f"{course}: {len(unknown)} unknown forms (add to lexicon):")
        for form, count in sorted(unknown.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  {form}\t{count}")
    for error in errors[:200]:
        print("ERROR", error)
    present = sorted(seen)
    print(f"{course}: {len(built)} items parsed (max index {present[-1] if present else 0})")
    if write and not unknown and not errors:
        by_index = {entry["vocab_index"]: entry for entry in built}
        for start, end in batch_ranges(config):
            chunk = [by_index[i] for i in range(start, end + 1) if i in by_index]
            if len(chunk) != end - start + 1:
                print(f"{course}: skipping incomplete batch {start}-{end} ({len(chunk)} items)")
                continue
            path = GENERATED / f"{config['stem']}_{start:03d}_{end:03d}.json"
            path.write_text(json.dumps(chunk, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}")
    return 1 if (unknown or errors) else 0


if __name__ == "__main__":
    courses = [arg for arg in sys.argv[1:] if not arg.startswith("-")] or list(COURSES)
    status = 0
    for name in courses:
        status |= build(name, write="--check" not in sys.argv)
    sys.exit(status)
