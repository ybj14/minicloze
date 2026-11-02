# Local corpora

These corpora use the same JSON shape as the Tatoeba v1 sentence API, with one extra optional field:

- `cloze_word`: the preferred target word to hide in the prompt.

The vocabulary selection is based on larger beginner/frequency lists, then the example sentences are original minicloze content. The source lists are used only for selecting target words and English glosses; the local corpora do not copy source example sentences, audio, or images. The exception is Sanskrit A1 Classical, whose sentences are simplified adaptations of cited lines from classical texts (see Sources).

Files:

Every course has three files: `<course>.json` (cloze sentences), `<course>_vocab.json` (target words) and `<course>_explanations.json` (full-sentence word explanations). Mongolian also has `<course>_tokens.json` (Traditional script / Poppe tokens written by `scripts/mongolian_bichig.mjs`). A1 courses have 500 target words and 1,500 sentences. Swadesh courses have 207 target words and 621 sentences. Reviewed batch inputs live in `generated/`.

| Course | Files (`<course>`) | Script / helper fields (explanation words) |
| --- | --- | --- |
| Mongolian A1 | `mongolian_a1` (+ `_tokens`) | Cyrillic; `bichig` (Traditional Mongolian) + `poppe`, machine-generated, with `verified` / `verified_by` (see `SHIP.md`) |
| Mongolian Swadesh | `mongolian_swadesh` (+ `_tokens`) | same as Mongolian A1 |
| Tibetan A1 | `tibetan_a1` | Tibetan; `wylie` + `zwpy` (藏文拼音) are added only to the static web copy by `scripts/build_static_web_data.py` |
| Tibetan Swadesh | `tibetan_swadesh` | same as Tibetan A1 |
| Tajik A1 | `tajik_a1` | Tajik Cyrillic |
| Tajik Swadesh | `tajik_swadesh` | Tajik Cyrillic |
| Thai A1 | `thai_a1` | Thai; `paiboon` |
| Thai Swadesh | `thai_swadesh` | same as Thai A1 |
| Burmese A1 | `burmese_a1` | Burmese; `mlcts` and `okell` |
| Burmese Swadesh | `burmese_swadesh` | MLCTS and Okell |
| Khmer A1 | `khmer_a1` | Khmer; Wiktionary-style `transliteration` and `transcription` |
| Khmer Swadesh | `khmer_swadesh` | Wiktionary transliteration and transcription |
| Amharic A1 | `amharic_a1` | Ge'ez script; `transliteration` = port of Wiktionary `Module:Ethi-translit` (`scripts/amharic_transliteration.py`; earlier docs said SERA-style) |
| Amharic Swadesh | `amharic_swadesh` | same as Amharic A1 |
| Armenian A1 | `armenian_a1` | Armenian; apostrophe-marked ASCII transliteration |
| Armenian Swadesh | `armenian_swadesh` | apostrophe-marked ASCII transliteration |
| Georgian A1 | `georgian_a1` | Georgian; apostrophe-marked ASCII transliteration |
| Georgian Swadesh | `georgian_swadesh` | apostrophe-marked ASCII transliteration |
| Maltese A1 | `maltese_a1` | Maltese orthography (ċ ġ ħ ż); ASCII learner transliteration (`scripts/maltese_transliteration.py`) |
| Maltese Swadesh | `maltese_swadesh` | same as Maltese A1 |
| Sanskrit A1 | `sanskrit_a1` | Devanagari; IAST |
| Sanskrit Swadesh | `sanskrit_swadesh` | Devanagari; IAST |
| Sanskrit A1 Classical | `sanskrit_a1_classical` | Devanagari; IAST; each sentence row carries `citation` and `source_text` |

Sources:

- Mongolian: Multi Linguis, English-Mongolian Learner's Dictionary, Elementary Level, CC BY-SA 3.0, used as the first quality-checked A1 seed list.
- Mongolian: https://1000mostcommonwords.com/1000-most-common-mongolian-words/, used to fill the remaining high-frequency beginner vocabulary.
- Tibetan: https://www.small-steps-tibetan.com/first-1000-words-basic, used as the source for the 500-word Tibetan beginner vocabulary selection.
- Tajik: Codex-curated beginner A1 seed list, used for selecting target words and English glosses.
- Thai: Codex-curated beginner A1 seed list, used for selecting target words and English glosses.
- Burmese: Codex-authored beginner A1 course material, split into reviewed batch files before merge.
- Khmer: Codex-curated beginner A1 seed list, used for selecting target words and English glosses.
- Amharic: Codex-curated beginner A1 seed list, combined with Amharic Swadesh seed items, used for selecting target words and English glosses.
- Armenian: Codex-curated beginner A1 seed list, combined with Eastern Armenian Swadesh seed items, used for selecting target words and English glosses.
- Georgian: Codex-curated beginner A1 seed list, combined with Georgian Swadesh seed items, used for selecting target words and English glosses.
- Maltese: LLM-curated Maltese A1 seed list (`A1_SOURCE` in `scripts/maltese_vocab.py`); A1 vocabulary and sentences are labelled `LLM-authored Maltese A1 2026-10-06` and were authored in `scripts/generate_maltese_courses.py` (PR #28).
- Maltese Swadesh: the 207 standard Swadesh concepts with preferred modern Maltese forms in `SWADESH_WORDS` (`scripts/maltese_vocab.py`, `SWADESH_SOURCE = "Wiktionary Maltese Swadesh seed"`), with per-item notes where the chosen form differs from Wiktionary; rows are labelled `LLM-authored Maltese Swadesh 2026-10-06` (PR #28).
- Sanskrit A1: hand-authored IAST source `scripts/data/sanskrit/a1.txt` with lexicons `lexicon.tsv` / `lexicon_swadesh.tsv`, converted by `scripts/build_sanskrit_batches.py`; vocabulary rows are labelled `LLM-authored Sanskrit A1 2026-10-06` (PR #29).
- Sanskrit Swadesh: lemmas from Wiktionary [Module:Swadesh/data/sa](https://en.wiktionary.org/wiki/Module:Swadesh/data/sa); where Wiktionary gives a Vedic/archaic or rare term a common textbook word is used, and every such override is listed in `scripts/data/sanskrit/README.md`; sentences are LLM-authored (`scripts/data/sanskrit/swadesh.txt`, PR #29).
- Sanskrit A1 Classical: every sentence is adapted from a specific line of a GRETIL plain-text edition (Hitopadeśa, Pañcatantra, Vetālapañcaviṃśatikā, Rāmāyaṇa, Bhagavadgītā, Manusmṛti, Bhartṛhari's Śatakatraya); each row's `citation` gives the GRETIL URL and line, and `source_text` the original clause. GRETIL e-texts are CC BY-NC-SA 4.0. Details and lemma swaps: `scripts/data/sanskrit/README.md` (PR #29).
- Swadesh: Wiktionary Swadesh data for English, Mongolian, Tibetan, Tajik, Thai, Burmese, Khmer, Amharic, Eastern Armenian, and Georgian, used for selecting the 207 core target concepts and seed target words; all cloze sentences are original minicloze A1 material.
