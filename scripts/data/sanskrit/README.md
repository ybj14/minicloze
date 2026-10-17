# Sanskrit course sources

This directory holds the hand-authored sources for three Sanskrit courses. `scripts/build_sanskrit_batches.py` turns them into batch JSON under `minicloze-lib/corpora/generated/`, and `scripts/merge_a1_corpora.py` merges those batches into the shipped corpora.

| Course | Code | Source | Size | Stems | id_start |
| --- | --- | --- | --- | --- | --- |
| Sanskrit A1 | `san-a1` | `a1.txt` | 500 × 3 = 1500 | `sanskrit_a1*`, batches `sanskrit_NNN_NNN.json` | -2100000 |
| Sanskrit Swadesh | `san-swadesh` | `swadesh.txt` | 207 × 3 = 621 | `sanskrit_swadesh*` | -2200000 |
| Sanskrit A1 Classical | `san-a1-classical` | `classical.txt` | 500 × 3 = 1500 | `sanskrit_a1_classical*` | -2300000 |

## Source format

```
@ index | lemma (IAST) | English gloss
sentence in IAST with the *cloze word marked = English translation [## key]
```

- Each item has exactly three sentences.
- The cloze word is the token marked with `*`. It is stored exactly as it appears in the sentence (inflected form), so it always matches a standalone token of the target.
- A `token{gloss}` suffix overrides the gloss for one token.
- Per-token English glosses come from `lexicon.tsv` and `lexicon_swadesh.tsv`, which are shared by A1 and Swadesh. The classical course uses `lexicon_classical.tsv` first, then the shared lexicons. Entries look like `form=gloss`, separated by ` | `. Word-final `m`/`ṃ` variants match automatically.
- The build refuses to write batches if any token is missing from the lexicon (`--check` lists the missing forms).

## Spelling convention (all courses)

- Targets are Devanagari. Transliteration and explanation fields use IAST.
- The style is pedagogical pausa, as in NCERT *Ruchira* and Samskrita Bharati primers:
  - words are kept separate, with no external sandhi;
  - word-final `m` before a consonant is written as anusvāra (`ṃ`);
  - final `ḥ` is kept.
- Classical lines are therefore printed un-sandhied. For example, Hitopadeśa `nahi suptasya siṃhasya praviśanti mukhe mṛgāḥ` becomes `suptasya siṃhasya mukhe mṛgāḥ na praviśanti`.

## Sanskrit Swadesh lemma source

The 207 Swadesh lemmas come from Wiktionary [Module:Swadesh/data/sa](https://en.wiktionary.org/wiki/Module:Swadesh/data/sa).

Where Wiktionary gives a Vedic/archaic or rare term, the course uses the common textbook word instead, so learners meet vocabulary used in modern primers and classical prose. The overrides, in the form index: Wiktionary → course, are:

29 uru → viśālaḥ · 30 ghana → sthūlaḥ · 32 alpa → laghuḥ · 34 aṃhu → saṅkīrṇaḥ · 70 parṇa → piccham · 95 dhayati → cūṣati · 99 aniti → śvasiti · 112 veti → mṛgayate · 117 likhati → kaṇḍūyati · 119 plavate → tarati · 120 patati → uḍḍīyate · 121 eti/gacchati/carati → calati · 124 sīdati → upaviśati · 126 vartate → parivartate · 127 padyate → patati · 129 dharati → dhārayati · 130 mṛdnāti → pīḍayati · 133 mārṣṭi → mārjayati · 140 vakti → vadati · 142 dīvyati → krīḍati · 144 sarati/kṣarati → vahati · 145 śīyate → ghanībhavati · 151 varṣa → vṛṣṭiḥ · 156 aśman → pāṣāṇaḥ · 161 mih → nīhāraḥ · 165 hima → tuṣāraḥ · 168 āsa → bhasma · 180 tapta → uṣṇaḥ · 197 neda/prati → samīpe · 200 savya → vāmaḥ · 201/202 (locative case) → antike / antaḥ.

All other lemmas follow Wiktionary, given in the nominative or 3rd-person-singular citation form.

## Sanskrit A1 Classical: citation approach

Every classical sentence is adapted from a specific line of a classical text, and every row in `sanskrit_a1_classical.json` carries that line's citation.

- **Texts used:** GRETIL plain-text editions, cited by URL. They live under `https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/plaintext/`:
  - `hit` Nārāyaṇa, *Hitopadeśa*: `sa_nArAyaNa-hitopadeza.txt`
  - `pt` Viṣṇuśarman, *Pañcatantra*: `sa_viSNuzarman-paJcatantra.txt`
  - `vet` Somadeva, *Kathāsaritsāgara: Vetālapañcaviṃśatikā*: `sa_somadeva-kathAsaritsAgaravetAlapaJcaviMzatikA.txt`
  - `ram` Vālmīki, *Rāmāyaṇa*: `sa_rAmAyaNa.txt`
  - `bhg` *Bhagavadgītā* (mūla verses only): `sa_bhagavadgItA-comm.txt`
  - `manu` *Manusmṛti*: `sa_manusmRti.txt`
  - `bhartr` Bhartṛhari, *Śatakatraya*: `sa_bhatRhari-zatakatraya.txt`
- **Keys:** each sentence line ends in `## code@LINE.CLAUSE`.
  - `LINE` is the 1-based line number in that GRETIL file.
  - `CLAUSE` is the daṇḍa/clause segment on that line.
  - `code:substring` is also accepted.
- **Resolution:** the builder opens the file and resolves the key. It aborts if the key doesn't exist. It then writes two fields:
  - `citation`: `Adapted from <work>, <verse X | prose passage preceding verse X> — <GRETIL URL> (line N)`. The verse number comes from the nearest GRETIL verse marker.
  - `source_text`: the original clause, in GRETIL's IAST.

  A reviewer can open the URL, go to line N, and compare. `merge_a1_corpora.py sanskrit-classical` rejects any row without a citation.
- **Adaptation rules:**
  - Lines are simplified to A1 level by:
    - undoing sandhi and compounds;
    - putting words in plain order;
    - dropping clauses;
    - replacing a rare synonym with the course lemma where necessary, e.g. `atilaulyād` → `atilobhāt`.
  - Meaning stays faithful to the source.
  - All rows are labelled "Adapted from" because none are verbatim (the un-sandhied spelling alone changes the text).
  - No citation is invented. Every one is generated from a key that resolves in the file.
- **Lemma list:** the starting point was a 500-lemma beginner list of common nouns, verbs, adjectives and particles from the narrative texts.
  - Lemmas that are rare in these texts were swapped for common classical words, so that each item has three independent attestations.
  - The header line of each item in `classical.txt` is authoritative.
  - Notable swaps, written as original → used:
    - mārayati → vyāpādayati
    - likhati → bhāṣate
    - namati → praṇamati
    - pratyāgacchati → nivartate
    - anusarati → anugacchati
    - bṛhat → kṛśaḥ
    - duḥkhī → duḥkhitaḥ
    - dhanī → īśvaraḥ
    - kṣudhitaḥ → bubhukṣitaḥ
    - antaḥ → madhye
    - vipattiḥ → vipad
    - vivekaḥ → matiḥ
    - puram → jīvitam
    - tīrtham → vyasanam
    - kṣīram → payaḥ
    - madhu → daṇḍaḥ
    - bījam → vairam
    - śilā → dhairyam
    - patram → kṣaṇaḥ
    - cañcuḥ → maraṇam
    - rudhiram → māsaḥ
    - upakaroti → jayati
    - prārthayate → nivedayati
    - pariharati → sahate
    - vismarati → nirūpayati
    - kṛśaḥ (duplicate) → sthiraḥ
    - sthūlaḥ → guṇavān
    - pīnaḥ → samarthaḥ
    - kṛṣṇaḥ → śreṣṭhaḥ
    - śvetaḥ → dhanyaḥ
    - raktaḥ → durjanaḥ
    - śītalaḥ → duṣkaraḥ
    - kaṭhinaḥ → nirbhayaḥ
    - uccaḥ → nirguṇaḥ
    - pakvaḥ → vacaḥ
- **Licence:** the GRETIL e-texts are distributed under CC BY-NC-SA 4.0. Only short, adapted clauses are quoted here (in `source_text`), each with attribution to its file.

## Rebuilding

```bash
# Classical keys need the GRETIL files listed above in this directory (default /workspace/sa_corpus):
export SANSKRIT_CORPUS_DIR=/path/to/gretil/plaintext
cd scripts
python3 build_sanskrit_batches.py classical --check   # list unknown forms / bad keys, write nothing
python3 build_sanskrit_batches.py                     # all courses (or: a1 | swadesh | classical)
cd ..
python3 scripts/merge_a1_corpora.py sanskrit
python3 scripts/merge_a1_corpora.py sanskrit-swadesh
python3 scripts/merge_a1_corpora.py sanskrit-classical
python3 scripts/data/sanskrit/qa_dupes.py scripts/data/sanskrit/classical.txt  # duplicate sentences / translations
cd scripts && python3 build_static_web_data.py --sanskrit-only
```

`find_classical.py` is the search helper used while authoring. It prints short GRETIL clauses that attest a candidate lemma, as ready-to-use `code@LINE.CLAUSE` keys.
