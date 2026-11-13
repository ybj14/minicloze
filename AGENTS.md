# Repository Guidelines

## Project Shape

`minicloze` is a Rust workspace for a cloze-style language-learning game.

- `minicloze-lib/`: shared Rust logic for sentence loading, prompts, answer checking, SRS, Tibetan helpers, and local corpora embedded with `include_str!`.
- `minicloze-cli/`: terminal frontend (binary `minicloze`); `cargo run --bin minicloze -- <language-or-corpus> [inverse]`. The workspace has two binaries (`minicloze`, `minicloze-web`), so a bare `cargo run` fails.
- `minicloze-web/`: Axum local web server plus a browser-only static PWA in `minicloze-web/static`.
- `minicloze-lib/corpora/`: source local course JSON, vocabulary JSON, explanation JSON, and generated batch inputs.
- `scripts/`: corpus merge/build/enrichment utilities.

The local course codes (see `COURSES` in `minicloze-web/static/app.js`) are `mon-a1`, `mon-swadesh`, `bod-a1`, `bod-swadesh`, `tgk-a1`, `tgk-swadesh`, `tha-a1`, `tha-swadesh`, `mya-a1`, `mya-swadesh`, `khm-a1`, `khm-swadesh`, `amh-a1`, `amh-swadesh`, `hye-a1`, `hye-swadesh`, `kat-a1`, `kat-swadesh`, `mlt-a1`, `mlt-swadesh`, `san-a1`, `san-swadesh`, and `san-a1-classical`. User-facing aliases such as `mongolian-a1`, `tibetan-swadesh`, `burmese-a1`, `khmer-a1`, `maltese-a1`, and `sanskrit-a1-classical` are normalized in `minicloze-lib/src/langs.rs`.

## Development Commands

Run commands from the repository root unless noted otherwise. Contributor workflow, PR rules, and Vercel deploy notes are in `README.md` ("How to contribute", "Deploying to Vercel").

- Format Rust: `cargo fmt` (needs the rustfmt component: `rustup component add rustfmt`)
- Run all Rust tests: `cargo test` (recent stable toolchain; without `pkg-config`, set `OPENSSL_LIB_DIR` / `OPENSSL_INCLUDE_DIR`, e.g. `/usr/lib/x86_64-linux-gnu` and `/usr/include`)
- Run CLI locally: `cargo run --bin minicloze -- mongolian-a1` or `cargo run --bin minicloze -- tibetan-a1 inverse`
- Run launcher with Tibetan dependencies bootstrapped: `./learn.sh tibetan-a1`
- Run local web server with Tibetan helpers: `./web.sh`
- Static PWA preview: `python3 -m http.server 4173 --directory minicloze-web/static`
- Rebuild static web data after corpus changes: `./.venv-tibetan/bin/python scripts/build_static_web_data.py` (same as `npm run build:static-data`; `.venv-tibetan` is created by `./learn.sh tibetan-a1` or `./web.sh`). Single-language refreshes: `--khmer-only`, `--amharic-only`, `--mongolian-only`, `--sanskrit-only`.
- Mongolian bichig/Poppe: `npm install`, then `npm run build:static-data:mongolian` and `npm run test:mongolian`
- Background web server: `./webctl.sh start`, `./webctl.sh status`, `./webctl.sh stop`, `./webctl.sh logs`

Tibetan learner phonetics use `scripts/tibetan_zwpy.py` (藏文拼音 / ZWPY). The launcher scripts create/reuse `.venv-tibetan` and install Botok/pyewts when needed.

## Corpus Workflow

Treat `minicloze-lib/corpora` as the source of truth. The browser app loads mirrored files from `minicloze-web/static/data`, so any corpus, vocabulary, or explanation change usually needs:

1. Update source files under `minicloze-lib/corpora`.
2. Run the relevant generator/merge script if the source is a generated batch.
3. Run `./.venv-tibetan/bin/python scripts/build_static_web_data.py`.
4. Run `cargo test`.

Useful corpus scripts:

- `scripts/merge_a1_corpora.py [language...]` validates generated batches and writes the main A1/Swadesh corpus JSON files. Language keys are the `LANGS` entries, e.g. `maltese`, `maltese-swadesh`, `sanskrit`, `sanskrit-swadesh`, `sanskrit-classical`.
- `scripts/generate_full_sentence_explanations.py [language...]` builds explanation files for `mongolian`, `tibetan`, `tajik`, `thai` and their `-swadesh` variants, and fails on unknown/alignment issues by default (`--allow-unknown` to override). Newer merge configs (Maltese, Sanskrit) build vocab/explanations from the batches instead (`vocab_from_batches` / `explanations_from_batches`).
- `scripts/generate_swadesh_courses.py` fetches Wiktionary Swadesh seed data and writes local Swadesh vocabulary/course material.
- `scripts/build_static_web_data.py` copies corpus/vocab/explanation files into the static web directory, adds Tibetan Wylie + ZWPY (藏文拼音) data, Thai Paiboon data, Burmese MLCTS/Okell token data, Khmer Wiktionary transliteration/transcription token data, Amharic/Armenian/Georgian/Maltese/Sanskrit transliteration tokens, and Mongolian Traditional (Hudum/bichig) via `scripts/mongolian_bichig.mjs` (`@gege-mn/gege-converter`; requires `npm install`). On `master` the Mongolian step runs only with `--mongolian-only` (or `npm run build:static-data:mongolian`), not in the full build; draft PR #27 proposes adding it. The Mongolian bichig/Poppe output is unreviewed machine output: each word carries `verified: true|false` (true = sourced override or dictionary-checked, not human-reviewed). Fix forms only via sourced rows in `scripts/data/mongolian_bichig_overrides.json`, never by hand-editing data or from unsourced knowledge; the review queue is `scripts/data/mongolian_review_queue.md`. Run `npm run test:mongolian` after rebuilding.

Before authoring or rewriting any local cloze corpus, read `minicloze-lib/corpora/GENERATION_RULES.md`. Those rules are binding: production sentences must be authored from the meaning and natural usage of each word, not generated by rotating templates or inserting words into generic frames. Scripts may validate, split, merge, enrich explanations/transliteration, and detect repetition, but they must not be the author of final sentence content.

When adding or renaming a local course, update all relevant places together: `minicloze-lib/src/langs.rs`, `minicloze-lib/src/local_corpora.rs`, `minicloze-web/static/app.js`, corpus source files, static data, and tests.

## Data Conventions

- Local corpus files use the Tatoeba v1-style shape: `{ "data": [...] }`, with `translations[0].text` as the target-language sentence and `text` as the English side for local courses.
- Local corpus rows may include `cloze_word`; keep it aligned with the actual target sentence.
- A1 courses have 500 vocabulary items and 1,500 sentences. Swadesh courses have 207 vocabulary items and 621 sentences.
- Existing local IDs are negative and language-specific; preserve each script's `id_start` range.
- Keep non-ASCII language text intact. Do not normalize away Tibetan tseks, Thai spelling, Cyrillic letters, or transliteration fields. Burmese explanations and tokens must preserve both `mlcts` and `okell`. Khmer explanations and tokens must preserve both Wiktionary-style `transliteration` and `transcription`.
- For Tajik generated sentences, target words should be standalone words where the merge script enforces that.
- Avoid meta-language in generated target sentences, such as sentences that talk about "the word ..." instead of using the word naturally.
- Treat sentence naturalness as a hard corpus requirement, not polish. Do not build production corpora by rotating generic templates such as "I saw X", "X is here", "The child drew X", or by inserting any question word into a noun frame. Sentences like "Who is the book?", "Where came?", "The liver is here", or other semantically odd examples are failures even when JSON shape and target-word checks pass.
- Generate cloze sentences as authored A1 learning material. Pick contexts that fit the specific concept: question words need real questions, body parts need ordinary body/health/gesture scenes, nature words need weather/place scenes, verbs need plausible actions, and function words need natural connectors. If a word is hard, write fewer but better simple contexts first, then adapt them to the target language.
- Reuse the successful A1 workflow for new Swadesh or derived courses: treat `minicloze-lib/corpora/generated/*` batch JSON as the reviewed source of truth, author/rewrite those batches first, then merge final corpus JSON and regenerate explanations/static web data from that reviewed corpus. Do not treat a scaffold generator's candidate sentences as production material.
- For large corpus rewrites, split by language or batch across agents when useful, but keep ownership disjoint and run local QA after merging. Subagent output is a draft until it passes naturalness, repetition, schema, explanation, and web-data validation.

## Static Web Notes

The static PWA in `minicloze-web/static` is deployable as-is. `vercel.json` serves that directory without an install/build step.

When changing `app.js`, `app.css`, `index.html`, service-worker behavior, or static data, keep cache busting in sync:

- `DATA_VERSION` in `minicloze-web/static/app.js`
- `CACHE_NAME` and shell asset query strings in `minicloze-web/static/service-worker.js`
- CSS/JS query strings in `minicloze-web/static/index.html`

The Axum server in `minicloze-web/src/main.rs` still embeds the app shell (`index.html`, `app.js`, CSS, manifest, service worker, icons) with `include_str!` / `include_bytes!`, and exposes API endpoints for local server mode. `/data/:file` now serves every `*.json` file from `minicloze-web/static/data` on disk (including `mongolian_*_tokens.json` and the Amharic, Armenian, Georgian, Maltese and Sanskrit courses), so `./web.sh` can load all 23 courses. Set `MINICLOZE_STATIC_DIR` to the `static` directory if the binary is not run from the crate.

## Testing Guidance

Run `cargo test` for normal changes. It covers answer normalization, local corpus/explanation alignment, SRS behavior, language aliases, Tibetan helpers, CLI answer handling, and web option generation.

For corpus-only changes, still run `cargo test` after rebuilding static data. If you change Python/Node generation scripts, run the specific script on the affected language and inspect the resulting JSON diff.

For frontend/UI changes, preview with either `./web.sh` or the static HTTP server. Check both multiple-choice and text-input modes, inverse mode, and at least one Tibetan or Thai course if transliteration/token rendering changed.

## Code Style

- Follow existing Rust 2021 style and keep shared behavior in `minicloze-lib` rather than duplicating it in frontends.
- Prefer small, focused tests near the module they exercise.
- Keep JavaScript in the static app framework-free and consistent with the existing DOM/state style.
- Keep Python scripts deterministic where possible and use UTF-8 JSON reads/writes with `ensure_ascii=False`.
- Do not hand-edit `minicloze-web/static/data` as the only copy of a corpus change; regenerate it from `minicloze-lib/corpora`.

## Git Hygiene

Work on a feature branch and open a PR to `master`. PRs are squash-merged by the owner. Agents must not merge PRs or push to `master`.

This repository may be nested inside a broader workspace. The project repository root is this directory, not its parent. Avoid committing local runtime artifacts such as `target/`, `node_modules/`, `.venv-tibetan/`, `.minicloze-web.log`, `.minicloze-web.pid`, `__pycache__/`, and `.DS_Store`.
