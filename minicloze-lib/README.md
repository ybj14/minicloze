# minicloze-lib
Contains minicloze's backend logic which is shared across all frontends. Minicloze is a cloze-based language learning game written in Rust.

Tibetan sentence prompts are tokenized with Botok and transliterated to Wylie with pyewts through a Python helper. Install `botok` and `pyewts` in the Python interpreter used by `MINICLOZE_PYTHON`, or by `python3` when the environment variable is not set.
