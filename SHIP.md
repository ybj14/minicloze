# Ship: Traditional Mongolian (Hudum / bichig) dual display

**Branch:** `feat/mongolian-traditional-bichig`  
**Courses:** `mongolian_a1`, `mongolian_swadesh`  
**Display:** Cyrillic primary + Traditional secondary, **horizontal LTR** (not `vertical-lr`)

## PR

- **URL:** https://github.com/ybj14/minicloze/pull/24
- **Merge SHA:** `17414240d37d7fcfed83c3964c2253dd0ac52c5c` (squash)
- **Merged at:** 2026-10-02 19:16 CST (UTC+8)

## What shipped

1. **Build:** `scripts/mongolian_bichig.mjs` + `@gege-mn/gege-converter` (npm). Wired via `scripts/build_static_web_data.py` (`--mongolian-only` or full build).
2. **Data:** `mongolian_{a1,swadesh}_tokens.json` in `minicloze-lib/corpora/` and `minicloze-web/static/data/`; explanations enriched with `bichig`.
3. **UI:** `tokensPath` on mon courses; prompt secondary line (`#wylieLine` + `.bichig-line`); MC `.choice-bichig`; explanation `.word-explanations-bichig`.
4. **Font:** self-hosted `static/fonts/noto-sans-mongolian-400.woff2` (Noto Sans Mongolian).
5. **Cache:** `DATA_VERSION=static-data-20261002-1`, SW `minicloze-static-pwa-v40`, asset `?v=static-pwa-20261002-01`.

Cyrillic remains the cloze answer key and typed Latin normalize path (`CYRILLIC_LATIN`). Traditional is display-only (not in `tokenAnswerTransliterations`).

## Before / after examples

| Course | Cyrillic (primary) | Traditional (bichig) | Provenance |
|---|---|---|---|
| A1 | Хүү сансар руу харав. | ᠬᠦᠦ ᠰᠠᠨᠰᠠᠷ ᠤᠷᠤᠭᠤ ᠬᠠᠷᠠᠪᠠ | lexicon / harvested |
| Swadesh | Өглөө би цай уудаг. | ᠥᠷᠯᠦᠭᠡ ᠪᠢ ᠴᠠᠢ ᠤᠭᠤᠳᠠᠭ | lexicon / harvested |
| Vocab | од / нар / тэнгэр | ᠣᠳᠤ / ᠨᠠᠷᠠᠨ / ᠲᠩᠷᠢ | lexicon |

## Converter coverage / gaps

QA log: `scripts/data/mongolian_bichig_qa.json`

| Set | Notes |
|---|---|
| A1 explanation surfaces | 6580/6580 with bichig; **89** unique guess-tier lemmas (201 surface uses) |
| Swadesh | 2695/2695; **22** unique guesses (82 uses) |
| Combined unique guesses | **111** |

Guess-tier stems are mostly inflected verbs / productive morphology (e.g. `аваарай`, `амардаг`, `амьдарч`, `гаталж`). Converter is a candidate generator (~74% top-1 on held-out running text per upstream). Display still shows top-1; cloze scoring never uses bichig.

**Known limitations:** no curated override map yet; Todo/Clear script out of scope; vertical Traditional layout intentionally not used (user confirmed LTR horizontal).

## Rebuild

```bash
npm install
python3 scripts/build_static_web_data.py --mongolian-only
# or full: ./.venv-tibetan/bin/python scripts/build_static_web_data.py
```
