# Ship: Poppe romanization (鲍培转写) third line for Mongolian

**Branch:** `feat/mongolian-poppe-romanization`  
**Courses:** `mongolian_a1`, `mongolian_swadesh`  
**Display order:** **Cyrillic → Traditional bichig → Poppe** (mirrors Tibetan native → zwpy → Wylie)

## PR

- **URL:** https://github.com/ybj14/minicloze/pull/25
- **Merge SHA:** `15d13909693ad92d163d68026152025faf740ba1` (squash)
- **Merged at:** 2026-10-02 19:21 CST (UTC+8)

## Conversion choice

**Source:** top candidate `classical` from `@gege-mn/gege-converter` (same path that builds bichig).  
This Classical romanization is the scholarly / VPMC-style Latin used in Mongolian studies and matches **Poppe** (鲍培转写) conventions: `č š ǰ γ ö ü`, harmony-conditioned `q`/`k` and `γ`/`g`.

**Why Classical from the converter (not a fresh Cyrillic→Latin table):**

1. Deterministic at build time and already aligned with the bichig top-1 candidate.
2. More accurate than letter-by-letter Cyrillic mapping (Written Mongolian restores unstable -n, classical stems like `tngri` / `naran` / `odu`).
3. Fallback if `classical` is missing: `fromScript(bichig)` via `@gege-mn/mongol-bichig`.

**Field name:** `poppe` on tokens and explanation words.

Poppe is display-only (not in `tokenAnswerTransliterations`); cloze keys stay Cyrillic.

## What shipped

1. **Build:** `scripts/mongolian_bichig.mjs` now emits `bichig` + `poppe`.
2. **Data:** regenerated `mongolian_{a1,swadesh}_{tokens,explanations}.json` (static + corpora).
3. **UI:** third line via existing `#wylieOrthographyLine` / MC tertiary / explanation span; CSS `.poppe-line`, `.choice-poppe`, `.word-explanations-poppe`.
4. **Cache:** `DATA_VERSION=static-data-20261002-2`, SW `minicloze-static-pwa-v41`, asset `?v=static-pwa-20261002-02`.

## Examples (Cyrillic / bichig / Poppe)

| Course | Cyrillic | Traditional (bichig) | Poppe |
|---|---|---|---|
| A1 | Хүү | ᠬᠦᠦ | qüü |
| A1 | сансар | ᠰᠠᠨᠰᠠᠷ | sansar |
| A1 | харав | ᠬᠠᠷᠠᠪᠠ | qaraba |
| Swadesh | Өглөө | ᠥᠷᠯᠦᠭᠡ | örlüge |
| Swadesh | цай | ᠴᠠᠢ | čai |
| Swadesh | уудаг | ᠤᠭᠤᠳᠠᠭ | uγudaγ |
| Vocab | од / нар / тэнгэр | ᠣᠳᠤ / ᠨᠠᠷᠠᠨ / ᠲᠩᠷᠢ | odu / naran / tngri |

Coverage: A1 6580/6580 poppe; Swadesh 2695/2695 poppe (same surfaces as bichig).

## Rebuild

```bash
npm install
python3 scripts/build_static_web_data.py --mongolian-only
```
