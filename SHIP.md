# Ship: Poppe romanization (鲍培转写) third line for Mongolian

> **Review status (updated 2026-11-13, after #32): the Traditional Mongolian (bichig) and Poppe lines are NOT human-reviewed.**
> They are machine output of `@gege-mn/gege-converter` 0.5.0, which describes itself as a candidate generator (~74% top-1 per word), plus a mechanical Poppe clean-up and 34 source-cited overrides. Nobody who reads Traditional Mongolian has reviewed them.
>
> Every Mongolian token and explanation word now carries `verified: true|false`:
> * **`verified: true`** (5973 / 9275 tokens, 64.4%) means *dictionary-checked*, not human-reviewed: either a sourced row in `scripts/data/mongolian_bichig_overrides.json`, or the bichig equals the headword string recorded from mongoltoli.mn (Academy of Sciences dictionary) or English Wiktionary in `scripts/data/mongolian_dictionary_evidence.json` **and** the Poppe equals the rule-based transliteration of that bichig. The source is in `verified_by`; the per-word list is `scripts/data/mongolian_verified_words.json`.
> * **`verified: false`** (3302 tokens) means awaiting review; reason codes are in `review` (explanations only). Known-unresolved categories are always flagged, even when a dictionary string matches: past tense -лаа/-лоо/-лээ/-лөө (`past-laa`), detached -тай/-тэй adjectives (`tai-detached`), -du-ban dative-reflexives (`du-ban`), guess-tier forms (`guess-tier`), homographs (`homograph`), and the wrong gloss of хүнд in sentence -100859 (`gloss-error`). See `scripts/data/mongolian_review_flags.json`.
> * The app shows a small `*` and a tooltip on the bichig/Poppe line, multiple-choice option and word list entry when a word is unverified.
> * Review queue, ranked by token frequency: `scripts/data/mongolian_review_queue.md` (and `.json`). Resolve a word by adding a sourced override row and rebuilding; do not edit generated data.
>
> An earlier version of this file said the romanization "matches Poppe conventions". That was false: the raw `classical` field leaked FVS digits (`mašin1`), `kh`, and q/γ in front-vowel words (`deγer-e`, `qeüqed`) in ~19% of tokens. See the correction note below.

**Branch:** `feat/mongolian-poppe-romanization`  
**Courses:** `mongolian_a1`, `mongolian_swadesh`  
**Display order:** **Cyrillic → Traditional bichig → Poppe** (mirrors Tibetan native → zwpy → Wylie)

## PR

- **URL:** https://github.com/ybj14/minicloze/pull/25
- **Merge SHA:** `15d13909693ad92d163d68026152025faf740ba1` (squash)
- **Merged at:** 2026-10-02 19:21 CST (UTC+8)

## Conversion choice

**Source:** top candidate `classical` from `@gege-mn/gege-converter` (same path that builds bichig).  
> **Correction (2026-10-29 audit; summary in the `fix/mongolian-poppe-review` PR):** neither the bichig nor the Poppe line is expert-reviewed. `@gege-mn/gege-converter` describes itself as a candidate generator (~74% top-1). Its raw `classical` field is not Poppe: it leaked FVS digits (`mašin1`), `kh`, and q/γ in front-vowel words (`deγer-e`, `qeüqed`) for ~19% of tokens. The build now runs `normalizePoppe()` (mechanical harmony/artefact fix) and applies `scripts/data/mongolian_bichig_overrides.json` (34 source-cited rows). Remaining lexical errors (verb past -лаа, -du-ban forms, detached -тай, guess-tier words, homographs) still need a bichig reader and are flagged `verified: false` (see the review status above).

**Why Classical from the converter (not a fresh Cyrillic→Latin table):**

1. Deterministic at build time and already aligned with the bichig top-1 candidate.
2. Closer to Written Mongolian than a letter-by-letter Cyrillic mapping (it restores unstable -n and classical stems like `tngri` / `naran` / `odu`), but it is still unreviewed machine output; see the review status above.
3. Fallback if `classical` is missing: `fromScript(bichig)` via `@gege-mn/mongol-bichig`.

**Field name:** `poppe` on tokens and explanation words.

Poppe is display-only (not in `tokenAnswerTransliterations`); cloze keys stay Cyrillic.

## What shipped

1. **Build:** `scripts/mongolian_bichig.mjs` now emits `bichig` + `poppe`.
2. **Data:** regenerated `mongolian_{a1,swadesh}_{tokens,explanations}.json` (static + corpora).
3. **UI:** third line via existing `#wylieOrthographyLine` / MC tertiary / explanation span; CSS `.poppe-line`, `.choice-poppe`, `.word-explanations-poppe`.
4. **Cache:** `DATA_VERSION=static-data-20261002-2`, SW `minicloze-static-pwa-v41`, asset `?v=static-pwa-20261002-02`.

## Examples (Cyrillic / bichig / Poppe)

Current data after the 2026-10-30 rebuild. "Status" is the `verified` marker; dictionary-checked is not the same as reviewed by a reader.

| Course | Cyrillic | Traditional (bichig) | Poppe | Status |
|---|---|---|---|---|
| A1 | Хүү | ᠬᠦᠦ | küü (was `qüü`) | dictionary-checked (mongoltoli.mn, Wiktionary) |
| A1 | сансар | ᠰᠠᠨᠰᠠᠷ | sansar | dictionary-checked (Wiktionary) |
| A1 | харав | ᠬᠠᠷᠠᠪᠠ | qaraba | unverified |
| Swadesh | Өглөө 'morning' | ᠥᠷᠯᠦᠭᠡ | örlüge | dictionary-checked (Wiktionary) |
| Swadesh | цай | ᠴᠠᠢ | čai | dictionary-checked (mongoltoli.mn, Wiktionary) |
| Swadesh | уудаг | ᠤᠭᠤᠳᠠᠭ | uγudaγ | unverified |
| Vocab | од / нар / тэнгэр | ᠣᠳᠤ / ᠨᠠᠷᠠᠨ / ᠲᠩᠷᠢ | odu / naran / tngri | checked / unverified / checked |

Coverage: A1 6580/6580 poppe; Swadesh 2695/2695 poppe (same surfaces as bichig).

## Rebuild

```bash
npm install
python3 scripts/build_static_web_data.py --mongolian-only
npm run test:mongolian
```

The build also regenerates `scripts/data/mongolian_review_queue.{json,md}`, `scripts/data/mongolian_verified_words.json` and `scripts/data/mongolian_bichig_qa.json`.

Cache for the 2026-10-30 review build: `DATA_VERSION=static-data-20261030-1`, SW `minicloze-static-pwa-v45`, asset `?v=static-pwa-20261031-01`.

Cache after #32 (2026-11-13, then on production): `DATA_VERSION=static-data-20261103-1`, SW `minicloze-static-pwa-v46`, asset `?v=static-pwa-20261103-01`.

Current cache in this tree: `DATA_VERSION=static-data-20261113-1`, SW `minicloze-static-pwa-v47`, asset `?v=static-pwa-20261113-01`.
