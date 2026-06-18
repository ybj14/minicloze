# Local corpora

These corpora use the same JSON shape as the Tatoeba v1 sentence API, with one extra optional field:

- `cloze_word`: the preferred target word to hide in the prompt.

The vocabulary selection is based on larger beginner/frequency lists, then the example sentences are original minicloze content. The source lists are used only for selecting target words and English glosses; the local corpora do not copy source example sentences, audio, or images.

Files:

- `mongolian_a1_vocab.json`: 500 Mongolian Cyrillic target words.
- `mongolian_a1.json`: 1,500 Mongolian cloze sentences.
- `mongolian_swadesh_vocab.json`: 207 Mongolian Cyrillic Swadesh target words.
- `mongolian_swadesh.json`: 621 Mongolian Swadesh cloze sentences.
- `tibetan_a1_vocab.json`: 500 Tibetan target words.
- `tibetan_a1.json`: 1,500 Tibetan cloze sentences.
- `tibetan_swadesh_vocab.json`: 207 Tibetan Swadesh target words.
- `tibetan_swadesh.json`: 621 Tibetan Swadesh cloze sentences.
- `tajik_a1_vocab.json`: 500 Tajik Cyrillic target words.
- `tajik_a1.json`: 1,500 Tajik cloze sentences.
- `tajik_swadesh_vocab.json`: 207 Tajik Cyrillic Swadesh target words.
- `tajik_swadesh.json`: 621 Tajik Swadesh cloze sentences.
- `thai_a1_vocab.json`: 500 Thai target words.
- `thai_a1.json`: 1,500 Thai cloze sentences.
- `thai_swadesh_vocab.json`: 207 Thai Swadesh target words.
- `thai_swadesh.json`: 621 Thai Swadesh cloze sentences.
- `burmese_a1_vocab.json`: 500 Burmese target words.
- `burmese_a1.json`: 1,500 Burmese cloze sentences.
- `burmese_a1_explanations.json`: full-sentence Burmese word explanations with MLCTS and Okell.
- `burmese_swadesh_vocab.json`: 207 Burmese Swadesh target words.
- `burmese_swadesh.json`: 621 Burmese Swadesh cloze sentences.
- `burmese_swadesh_explanations.json`: full-sentence Burmese Swadesh word explanations with MLCTS and Okell.
- `khmer_a1_vocab.json`: 500 Khmer target words.
- `khmer_a1.json`: 1,500 Khmer cloze sentences.
- `khmer_a1_explanations.json`: full-sentence Khmer word explanations with Wiktionary transliteration and transcription.
- `khmer_swadesh_vocab.json`: 207 Khmer Swadesh target words.
- `khmer_swadesh.json`: 621 Khmer Swadesh cloze sentences.
- `khmer_swadesh_explanations.json`: full-sentence Khmer Swadesh word explanations with Wiktionary transliteration and transcription.
- `amharic_a1_vocab.json`: 500 Amharic target words.
- `amharic_a1.json`: 1,500 Amharic cloze sentences.
- `amharic_a1_explanations.json`: full-sentence Amharic word explanations with SERA-style transliteration.
- `amharic_swadesh_vocab.json`: 207 Amharic Swadesh target words.
- `amharic_swadesh.json`: 621 Amharic Swadesh cloze sentences.
- `amharic_swadesh_explanations.json`: full-sentence Amharic Swadesh word explanations with SERA-style transliteration.

Sources:

- Mongolian: Multi Linguis, English-Mongolian Learner's Dictionary, Elementary Level, CC BY-SA 3.0, used as the first quality-checked A1 seed list.
- Mongolian: https://1000mostcommonwords.com/1000-most-common-mongolian-words/, used to fill the remaining high-frequency beginner vocabulary.
- Tibetan: https://www.small-steps-tibetan.com/first-1000-words-basic, used as the source for the 500-word Tibetan beginner vocabulary selection.
- Tajik: Codex-curated beginner A1 seed list, used for selecting target words and English glosses.
- Thai: Codex-curated beginner A1 seed list, used for selecting target words and English glosses.
- Burmese: Codex-authored beginner A1 course material, split into reviewed batch files before merge.
- Khmer: Codex-curated beginner A1 seed list, used for selecting target words and English glosses.
- Amharic: Codex-curated beginner A1 seed list, combined with Amharic Swadesh seed items, used for selecting target words and English glosses.
- Swadesh: Wiktionary Swadesh data for English, Mongolian, Tibetan, Tajik, Thai, Burmese, Khmer, and Amharic, used for selecting the 207 core target concepts and seed target words; all cloze sentences are original minicloze A1 material.
