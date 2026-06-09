# minicloze
A command-line cloze-based language-learning game using the Tatoeba database of sentences. Written in Rust. The name is a reference to the Clozemaster app. This repository contains the Cargo workspace for minicloze.

# Features
- Support for over 400 languages
- Lookup unfamiliar words on Wiktionary
- Support for MacOS, Linux and Windows
- Lean implementation, written in Rust
- High-quality Tibetan word segmentation through Botok

# Targets
- **Long-term**
- Build a FOSS version of Clozemaster
- **Short-term**
- Learn 100, 1000 etc. most common words of various languages
- Play between two non-English languages

# Installation
To install `minicloze-cli`, the only currently supported frontend, use `cargo install minicloze` (more likely to be up-to-date) or just download a release.

# Tibetan tokenization
Tibetan (`minicloze tibetan`) uses [Botok](https://pypi.org/project/botok/) for word segmentation and [pyewts](https://pypi.org/project/pyewts/) for Wylie transliteration, so cloze prompts hide words rather than whole sentences and show a transliterated helper line. Install the Python dependencies before playing Tibetan:

```bash
python3 -m pip install botok
python3 -m pip install "setuptools<81" wheel
python3 -m pip install --no-build-isolation pyewts
```

If Botok is installed in a non-default Python, set `MINICLOZE_PYTHON` to that interpreter. For example:

```bash
MINICLOZE_PYTHON=/path/to/python minicloze tibetan
```

For debugging only, `MINICLOZE_TIBETAN_FALLBACK=syllable` falls back to syllable-level splitting when Botok cannot run.

The local `tibetan-a1` corpus can run without Botok by using a built-in target-word fallback. Install Botok and pyewts if you want Wylie helper text.

You can also use the one-step launcher, which runs any language or local corpus. For Tibetan targets such as `tibetan`, `tibetan-a1`, or a future `tibetan-a2`, it creates a local Python environment and installs Botok/pyewts if needed:

```bash
./learn.sh mongolian
./learn.sh tibetan-a1
./learn.sh tibetan-a1 inverse
```

The older Tibetan-only launcher is still available as a shortcut for `./learn.sh tibetan`:

```bash
./learn-tibetan.sh
```

# Usage
For `minicloze-cli`, just pass in the language (from www.tatoeba.org) you want to use, e.g. `minicloze french`. Add `inverse` for inverse mode (`minicloze french inverse`).

There are also local A1 corpora with original beginner sentences:

```bash
minicloze mongolian-a1
minicloze tibetan-a1
```

Answers can be typed either in the target script or as a Latin transliteration without diacritics. For example, Mongolian `дөрөв` can be answered as `dorov`, and Tibetan `བཀྲ་ཤིས` can be answered as `bkra shis`.

![Example of use with French](french.gif)

# Contributing
Any help is very welcome, just open a PR or an issue and I'll probably be able to reply quickly. Right now the focus is on expanding from the basic idea into a more fully-fledged and user friendly experience.

# Licensing
Remote sentence data comes from Tatoeba (www.tatoeba.org), released under the CC-BY 2.0 FR license.

The local `mongolian-a1` and `tibetan-a1` corpora are original minicloze sentences generated for this project. Their vocabulary selection is inspired by beginner language-learning resources listed in `minicloze-lib/corpora/README.md`.
