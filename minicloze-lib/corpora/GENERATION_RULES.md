# Cloze Corpus Generation Rules

These rules are mandatory for production local corpora. They exist because a
JSON file can pass schema checks while still being bad learning material.

## Core Rule

Generate sentences with language-model authorship, not template substitution.
For every vocabulary item, first think about what the word means, how it is
used by real speakers, what an A1 learner can understand, and which simple
scene naturally calls for that word. Then write original target-language
sentences and natural English translations for that specific word.

## Forbidden Production Methods

Do not build production sentences by rotating frames such as:

- `I see X.`
- `X is here.`
- `The child drew X.`
- `The teacher sees X.`
- `X is on the table.`
- `The X is beautiful today.`

Do not write code that loops through a vocabulary list and creates sentences by
inserting `word` or `gloss` into generic frames. Do not normalize bad examples
by calling them "candidate" material if they are being written into source
corpora. Scaffold scripts may create empty batch files, assign IDs, split
batches, validate JSON, merge reviewed batches, enrich transliteration, or
check repetition. They must not be the author of final sentence content.

## Required Authorship Workflow

For each word, author three independent A1 sentences by hand or by an LLM
acting as a language author. Use the word in three plausible contexts. Avoid
making the three sentences tiny variations of the same scene.

Before accepting a sentence, check:

- The target-language sentence is natural, grammatical, and idiomatic enough for beginner course material.
- The English translation is natural English, not a gloss-filled placeholder.
- The target word is used with its actual meaning and part of speech.
- Question words appear in real questions, not noun frames.
- Function words and particles appear in natural constructions.
- Greetings, replies, time words, pronouns, body parts, abstract phrases, and place words get category-specific contexts.
- The sentence does not discuss "the word ..." or otherwise use meta-language.
- The sentence is A1: short, concrete, and built from beginner vocabulary unless the target word itself is the challenge.
- The cloze target appears exactly in the target sentence and is not hidden inside an unrelated longer word unless the language requires it and QA explicitly accepts it.

## Repetition Limits

Repetition is a quality bug. In a single reviewed batch, the same English frame
after replacing the target gloss should usually appear no more than three
times. In a full 500-word course, any frame appearing more than eight times
needs a manual justification or rewrite. The goal is not to dodge a regex; the
goal is that learners do not feel they are reading a spreadsheet.

Natural exceptions are allowed for small closed classes, such as pronouns,
numbers, or core particles, but even there the contexts must be semantically
appropriate and grammatically correct.

## Batch Review

Work in small batches, normally 20-50 vocabulary items. For each batch:

1. Author sentences for each word from meaning and usage, not from a global frame bank.
2. Read the batch as a learner would and mark unnatural or repetitive lines.
3. Rewrite bad lines before merging.
4. Run mechanical QA only after the human/LLM naturalness pass.
5. Treat generated explanations and static web data as derived artifacts.

If generating vocabulary, sentences, or full-sentence explanations is too large
for one pass, call subagents and split the work. Give each subagent these rules
and a disjoint vocabulary range, course, or artifact type. Ask subagents to
author language content from meaning and usage, not templates, and to return
reviewable batch JSON or explanation rows only for their assigned scope.
Subagent output is draft material until the main agent has inspected
representative samples, checked full coverage, and run QA.

## Scripts

Scripts are allowed for:

- vocabulary normalization and source metadata;
- assigning stable negative IDs;
- splitting and merging reviewed batch JSON;
- validating target-word presence and schema shape;
- generating full-sentence word explanations from reviewed sentences;
- adding standard transliteration fields such as Wylie, THL, Paiboon, MLCTS, or Okell;
- detecting repeated frames, meta-language, missing explanations, and web-data drift.

Scripts are not allowed to generate final target-language sentences through
generic frame substitution.

## Transliteration And Explanations

For non-Latin or non-Cyrillic writing systems, provide a standard academic or
well-established learner transliteration for sentence tokens and vocabulary
explanations when practical. Explanations must cover the whole target-language
sentence, not only the cloze word.

For Burmese, include both `mlcts` and `okell` on every explanation word and
sentence token. Treat MLCTS as the spelling-oriented scholarly transliteration
and Okell as the learner pronunciation transcription, analogous to Tibetan
Wylie plus THL.
