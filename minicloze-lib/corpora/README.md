# Local A1 corpora

These corpora use the same JSON shape as the Tatoeba v1 sentence API, with one extra optional field:

- `cloze_word`: the preferred target word to hide in the prompt.

The vocabulary selection is based on larger beginner/frequency lists, then the example sentences are original minicloze content. The source lists are used only for selecting target words and English glosses; the local corpora do not copy source example sentences, audio, or images.

Files:

- `mongolian_a1_vocab.json`: 500 Mongolian Cyrillic target words.
- `mongolian_a1.json`: 1,500 Mongolian cloze sentences.
- `tibetan_a1_vocab.json`: 500 Tibetan target words.
- `tibetan_a1.json`: 1,500 Tibetan cloze sentences.

Sources:

- Mongolian: Multi Linguis, English-Mongolian Learner's Dictionary, Elementary Level, CC BY-SA 3.0, used as the first quality-checked A1 seed list.
- Mongolian: https://1000mostcommonwords.com/1000-most-common-mongolian-words/, used to fill the remaining high-frequency beginner vocabulary.
- Tibetan: https://www.small-steps-tibetan.com/first-1000-words-basic, used as the source for the 500-word Tibetan beginner vocabulary selection.
