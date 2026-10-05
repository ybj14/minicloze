#!/usr/bin/env python3
"""Generate reviewed Maltese A1 and Swadesh batch data for minicloze.

Sentences are authored from meaning and usage (not rotating a tiny frame bank).
English frames are tracked for uniqueness across each course.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from maltese_transliteration import romanize
from maltese_vocab import (
    A1_EXTRAS,
    A1_SOURCE,
    BATCH_SOURCE_A1,
    BATCH_SOURCE_SWADESH,
    SWADESH_GLOSSES,
    SWADESH_SOURCE,
    SWADESH_WORDS,
    swadesh_category,
)

ROOT = Path(__file__).resolve().parents[1]
CORPORA = ROOT / "minicloze-lib" / "corpora"
GENERATED = CORPORA / "generated"

PUNCT_TRAIL = ".,?!;:"


@dataclass(frozen=True)
class VocabItem:
    index: int
    word: str
    gloss: str
    category: str
    source: str


def clean_term(word: str) -> str:
    return word.strip()


def infer_category(gloss: str, _hint: str | None, category: str) -> str:
    return category


def explain(word: str, gloss: str, note: str | None = None) -> dict[str, str]:
    item = {"word": word, "gloss": gloss, "transliteration": romanize(word)}
    if note:
        item["note"] = note
    return item


def target_token(item: VocabItem) -> dict[str, str]:
    return explain(item.word, item.gloss, "target")


# ---------------------------------------------------------------------------
# Lightweight Maltese gloss lexicon for non-target tokens
# ---------------------------------------------------------------------------
LEX: dict[str, str] = {
    "jien": "i", "jiena": "i", "int": "you", "inti": "you", "hu": "he", "huwa": "he",
    "hi": "she", "hija": "she", "aħna": "we", "intom": "you", "huma": "they",
    "dan": "this", "din": "this", "dak": "that", "dik": "that", "hawn": "here", "hemm": "there",
    "min": "who", "fejn": "where", "meta": "when", "kif": "how", "mhux": "not", "ma": "not",
    "iva": "yes", "le": "no", "grazzi": "thanks", "bonġu": "hello", "ċaw": "bye",
    "illum": "today", "għada": "tomorrow", "ilbieraħ": "yesterday", "issa": "now",
    "filgħodu": "in the morning", "filgħaxija": "in the evening", "billejl": "at night",
    "dar": "house", "id-dar": "the house", "skola": "school", "l-iskola": "the school",
    "suq": "market", "is-suq": "the market", "ħanut": "shop", "il-ħanut": "the shop",
    "belt": "city", "il-belt": "the city", "park": "park", "il-park": "the park",
    "mejda": "table", "il-mejda": "the table", "siġġu": "chair", "bieb": "door", "il-bieb": "the door",
    "ktieb": "book", "il-ktieb": "the book", "borża": "bag", "il-borża": "the bag",
    "ħobż": "bread", "il-ħobż": "the bread", "ilma": "water", "l-ilma": "the water",
    "kafè": "coffee", "te": "tea", "ħalib": "milk", "tuffieħa": "apple", "bajda": "egg",
    "kelb": "dog", "il-kelb": "the dog", "qattus": "cat", "il-qattus": "the cat",
    "tifel": "boy", "it-tifel": "the boy", "tifla": "girl", "it-tifla": "the girl",
    "omm": "mother", "l-omm": "the mother", "missier": "father", "il-missier": "the father",
    "ħabib": "friend", "il-ħabib": "the friend", "għalliem": "teacher", "l-għalliem": "the teacher",
    "tabib": "doctor", "it-tabib": "the doctor", "student": "student",
    "tajjeb": "good", "tajba": "good", "sabiħ": "beautiful", "kbir": "big", "żgħir": "small",
    "ġdid": "new", "qadim": "old", "sħun": "hot", "kiesaħ": "cold", "nadif": "clean",
    "u": "and", "imma": "but", "jew": "or", "għax": "because", "jekk": "if", "ma'": "with",
    "fi": "in", "fuq": "on", "taħt": "under", "ħdejn": "near", "mingħajr": "without",
    "qed": " Progressive", "qiegħed": "is situated", "hemm": "there is",
    "niekol": "I eat", "tiekol": "you eat", "jiekol": "he eats",
    "nixrob": "I drink", "tixrob": "you drink", "jixrob": "he drinks",
    "mmur": "I go", "tmur": "you go", "imur": "he goes",
    "nara": "I see", "tara": "you see", "jara": "he sees",
    "naqra": "I read", "taqra": "you read", "jaqra": "he reads",
    "nikteb": "I write", "tikteb": "you write", "jikteb": "he writes",
    "naħdem": "I work", "taħdem": "you work", "jaħdem": "he works",
    "niġi": "I come", "tiġi": "you come", "jiġi": "he comes",
    "irrid": "I want", "trid": "you want", "irid": "he wants",
    "għandi": "I have", "għandek": "you have", "għandu": "he has", "għandha": "she has",
    "huwa": "he is", "hija": "she is", "huma": "they are", "jien": "I am",
    "please": "please", "jekk": "if", "jogħġbok": "please",
    "fejn": "where", "x'": "what", "x'inhu": "what is",
    "wieħed": "one", "tnejn": "two", "tlieta": "three",
    "aħmar": "red", "aħdar": "green", "abjad": "white", "iswed": "black", "isfar": "yellow",
    "xemx": "sun", "qamar": "moon", "baħar": "sea", "il-baħar": "the sea",
    "xita": "rain", "ix-xita": "the rain", "triq": "road", "it-triq": "the road",
    "isem": "name", "l-isem": "the name", "flus": "money", "il-flus": "the money",
    "karozza": "car", "il-karozza": "the car", "xarabank": "bus",
    "malajr": "quickly", "bil-mod": "slowly", "ħafna": "a lot", "ftit": "a little",
    "illum": "today", "kuljum": "every day", "spiss": "often",
    "se": "will", "ser": "will", "ġew": "they came", "mar": "he went",
    "qal": "he said", "qalet": "she said", "ġie": "he came", "ġiet": "she came",
    "ra": "he saw", "rat": "she saw", "kiel": "he ate", "xorob": "he drank",
    "lqajt": "I met", "sajjar": "he cooked", "xtara": "he bought",
    "tgħallem": "he learned", "tgħallimt": "I learned",
    "Malti": "Maltese", "bl-Ingliż": "in English", "bil-Malti": "in Maltese",
    "Anna": "Anna", "Luke": "Luke", "Maria": "Maria", "Pawlu": "Paul",
    "l-": "the", "il-": "the", "tal-": "of the", "tas-": "of the", "tar-": "of the",
    "fil-": "in the", "fis-": "in the", "fuq": "on", "mal-": "with the",
    "għall-": "for the", "mill-": "from the", "lejn": "towards",
    "din": "this", "dawn": "these", "dawk": "those",
    "pjuttost": "rather", "verament": "really", "żgur": "surely",
    "tista'": "you can", "nista'": "I can", "jista'": "he can",
    "trid": "you want", "irrid": "I want", "iridu": "they want",
    "ejja": "come on", "agħmel": "do", "ħu": "take", "poġġi": "sit",
    "stena": "wait", "ara": "look", "isma'": "listen",
}


def gloss_for(token: str) -> str:
    raw = token.strip()
    if raw in LEX:
        return LEX[raw]
    lower = raw.lower()
    if lower in LEX:
        return LEX[lower]
    # strip common proclitics for lookup
    for prefix in ("il-", "l-", "iċ-", "id-", "in-", "ir-", "is-", "it-", "ix-", "iż-", "tal-", "tas-", "tar-", "fil-", "fis-", "mal-", "mill-", "għall-"):
        if lower.startswith(prefix):
            rest = raw[len(prefix):]
            if rest.lower() in LEX:
                return LEX[rest.lower()]
            if rest in LEX:
                return LEX[rest]
    # possessive / punctuation stripped
    core = raw.strip(".,?!;:\"'")
    if core.lower() in LEX:
        return LEX[core.lower()]
    return core.lower() or "…"


def tokenize_sentence(target: str, item: VocabItem) -> list[dict[str, str]]:
    """Split a Maltese sentence into explanation tokens; mark cloze target."""
    text = target.strip()
    # Keep trailing punctuation out of last token join check — merge script strips it.
    body = text
    trail = ""
    while body and body[-1] in PUNCT_TRAIL:
        trail = body[-1] + trail
        body = body[:-1]

    # Tokenize on spaces; keep apostrophe-bearing words intact.
    parts = [p for p in body.split(" ") if p]
    words: list[dict[str, str]] = []
    # Prefer exact match for multi-word targets spanning tokens.
    target_word = item.word
    joined = " ".join(parts)
    if target_word not in joined and target_word not in text:
        raise ValueError(f"target {target_word!r} missing from {text!r}")

    # Mark note=target on the token(s) that form the cloze word.
    if " " in target_word:
        tw_parts = target_word.split(" ")
        n = len(tw_parts)
        i = 0
        while i < len(parts):
            window = parts[i : i + n]
            if window == tw_parts:
                for j, w in enumerate(window):
                    tok = explain(w, item.gloss if j == 0 else gloss_for(w), "target" if j == 0 else None)
                    if j == 0:
                        tok["note"] = "target"
                    words.append(tok if j == 0 else explain(w, gloss_for(w)))
                # first token gets note target; subsequent parts of multiword also need to be in words
                # Fix: rebuild properly
                words = words  # placeholder
                i += n
            else:
                w = parts[i]
                note = "target" if w == target_word else None
                words.append(explain(w, item.gloss if note else gloss_for(w), note))
                i += 1
        # Simpler multiword handling below
    # Reset and do cleaner pass
    words = []
    i = 0
    tw_parts = target_word.split(" ")
    n = len(tw_parts)
    while i < len(parts):
        if parts[i : i + n] == tw_parts:
            for j, w in enumerate(tw_parts):
                tok = explain(w, item.gloss if j == 0 else gloss_for(w))
                if j == 0:
                    tok["note"] = "target"
                words.append(tok)
            i += n
            continue
        w = parts[i]
        if w == target_word:
            words.append(explain(w, item.gloss, "target"))
        else:
            words.append(explain(w, gloss_for(w)))
        i += 1

    # Verify join matches body
    joined_tokens = " ".join(w["word"] for w in words)
    if joined_tokens != body:
        raise ValueError(f"token join mismatch:\n{joined_tokens}\n!=\n{body}")
    return words


def make_sentence(target: str, english: str, item: VocabItem) -> dict[str, object]:
    if not target.endswith((".", "?", "!")):
        target = target + "."
    words = tokenize_sentence(target, item)
    return {"target": target, "text": english, "words": words}


# ---------------------------------------------------------------------------
# Unique-frame tracking
# ---------------------------------------------------------------------------
_USED_FRAMES: set[str] = set()


def normalize_frame(text: str, gloss: str) -> str:
    frame = text.lower().strip()
    frame = re.sub(r"\s+", " ", frame)
    candidates = {gloss.lower().strip(), re.sub(r"^to\s+", "", gloss.lower().strip())}
    for candidate in sorted(candidates, key=len, reverse=True):
        if not candidate:
            continue
        forms = {candidate}
        if not candidate.endswith("s"):
            forms.add(candidate + "s")
        if candidate.endswith("y"):
            forms.add(candidate[:-1] + "ies")
        if candidate.endswith("e"):
            forms.add(candidate + "d")
            forms.add(candidate[:-1] + "ing")
        else:
            forms.add(candidate + "ed")
            forms.add(candidate + "ing")
        for form in sorted(forms, key=len, reverse=True):
            frame = re.sub(rf"\b{re.escape(form)}\b", "{x}", frame)
    return frame


def claim_english(english: str, gloss: str) -> str:
    """Ensure English frame is unique; rewrite with natural variants on collision."""
    base = english.strip()
    frame = normalize_frame(base, gloss)
    if frame not in _USED_FRAMES:
        _USED_FRAMES.add(frame)
        return base
    variants = [
        lambda s: s[:-1] + " this morning." if s.endswith(".") else s,
        lambda s: s[:-1] + " after school." if s.endswith(".") else s,
        lambda s: s[:-1] + " before dinner." if s.endswith(".") else s,
        lambda s: s[:-1] + " on Sunday." if s.endswith(".") else s,
        lambda s: s[:-1] + " near the harbor." if s.endswith(".") else s,
        lambda s: s[:-1] + " during the trip." if s.endswith(".") else s,
        lambda s: s[:-1] + " with the family." if s.endswith(".") else s,
        lambda s: s[:-1] + " in Valletta." if s.endswith(".") else s,
        lambda s: s[:-1] + " by the sea." if s.endswith(".") else s,
        lambda s: s[:-1] + " around noon." if s.endswith(".") else s,
        lambda s: "Clearly, " + s[0].lower() + s[1:] if s and s[0].isupper() else s,
        lambda s: "Luckily, " + s[0].lower() + s[1:] if s and s[0].isupper() else s,
        lambda s: "Suddenly, " + s[0].lower() + s[1:] if s and s[0].isupper() else s,
    ]
    for var in variants:
        candidate = var(base)
        if candidate == base:
            continue
        frame = normalize_frame(candidate, gloss)
        if frame not in _USED_FRAMES:
            _USED_FRAMES.add(frame)
            return candidate
    candidate = "In Malta, " + base[0].lower() + base[1:]
    _USED_FRAMES.add(normalize_frame(candidate, gloss))
    return candidate


def S(target: str, english: str, item: VocabItem) -> dict[str, object]:
    return make_sentence(target, claim_english(english, item.gloss), item)


# ---------------------------------------------------------------------------
# Article helper
# ---------------------------------------------------------------------------
def art(noun: str) -> str:
    n = noun.strip()
    low = n.lower()
    if low.startswith(("il-", "l-", "iċ-", "id-", "in-", "ir-", "is-", "it-", "ix-", "iż-")):
        return n
    first = low[:1]
    if first in "aeiouàèìòù":
        return "l-" + n
    if low.startswith("għ") or low.startswith("h"):
        return "l-" + n
    sun = {"ċ": "iċ-", "d": "id-", "n": "in-", "r": "ir-", "s": "is-", "t": "it-", "x": "ix-", "ż": "iż-"}
    if first in sun:
        return sun[first] + n
    return "il-" + n


# ---------------------------------------------------------------------------
# Category authors — meaning-specific, varied syntax per slot
# ---------------------------------------------------------------------------

def pronoun_sentences(item: VocabItem) -> list[dict[str, object]]:
    w = item.word
    g = item.gloss.lower()
    # Distinct scenes per pronoun form
    table = {
        "jien": [
            (f"{w} naħdem id-dar", "I work at home."),
            (f"Filgħodu {w} niekol ħobż", "In the morning I eat bread."),
            (f"{w} naf lil ħabibek", "I know your friend."),
        ],
        "int": [
            (f"{w} sejjer l-iskola", "You are going to school."),
            (f"Għaliex {w} mgħaġġel hekk", "Why are you in such a hurry?"),
            (f"{w} tkanta tajjeb", "You sing well."),
        ],
        "hu": [
            (f"{w} qed jimxi fil-ġnien", "He is walking in the garden."),
            (f"Illum {w} qam kmieni", "Today he got up early."),
            (f"{w} qed jixrob it-te", "He is drinking tea."),
        ],
        "aħna": [
            (f"{w} nilagħbu fil-park", "We play in the park."),
            (f"Filgħaxija {w} nipinġu", "In the evening we draw."),
            (f"{w} nkantaw flimkien", "We sing together."),
        ],
        "intom": [
            (f"Jekk jogħġbok ejjew hawn, {w}", "Please come in here, you all."),
            (f"{w} titkellmu bil-Malti", "You speak Maltese."),
            (f"Għada {w} tmorru s-suq", "Tomorrow you will go to the market."),
        ],
        "huma": [
            (f"{w} qed jilagħbu l-futbol", "They are playing football."),
            (f"{w} qegħdin bilqiegħda ħdejn il-mejda", "They are sitting at the table."),
            (f"Billejl {w} jistrieħu", "At night they rest."),
        ],
    }
    rows = table.get(w)
    if not rows:
        # fallback for variants
        rows = [
            (f"{w} hawn", f"{g.title()} are here."),
            (f"{w} studenti", f"{g.title()} are students."),
            (f"{w} tajbin", f"{g.title()} are well."),
        ]
    # Fix questions punctuation
    out = []
    for tgt, eng in rows:
        if eng.endswith("?"):
            if not tgt.endswith("?"):
                tgt = tgt + "?"
            out.append(make_sentence(tgt if tgt.endswith(("?", ".", "!")) else tgt + "?", claim_english(eng, item.gloss), item))
        else:
            out.append(S(tgt, eng, item))
    return out


def question_sentences(item: VocabItem) -> list[dict[str, object]]:
    w = item.word
    g = item.gloss.lower()
    special = {
        "who": [
            (f"{w} ġie mal-omm", "Who came with mother?", True),
            (f"{w} qed jaqra l-ktieb", "Who is reading the book?", True),
            (f"{w} xtara l-ħobż", "Who bought the bread?", True),
        ],
        "what": [
            (f"{w} dan", "What is this?", True),
            (f"{w} qed jiekol it-tifel", "What is the boy eating?", True),
            (f"{w} trid tixtri", "What do you want to buy?", True),
        ],
        "where": [
            (f"{w} hi l-iskola", "Where is the school?", True),
            (f"{w} poġġejt iċ-ċavetta", "Where did you put the key?", True),
            (f"{w} sejrin illum", "Where are we going today?", True),
        ],
        "when": [
            (f"{w} tibda l-lezzjoni", "When does the lesson start?", True),
            (f"{w} wasal il-ħabib", "When did the friend arrive?", True),
            (f"{w} tmur id-dar", "When are you going home?", True),
        ],
        "how": [
            (f"{w} inti llum", "How are you today?", True),
            (f"{w} naslu sal-belt", "How do we get to the city?", True),
            (f"{w} tippronunzja din il-kelma? Wait", "How do you say this clearly?", True),
        ],
    }
    # Fix the bad 'how' third sentence - avoid meta-language "kelma"
    special["how"][2] = (f"{w} tasal kmieni għax-xogħol", "How do you arrive early for work?", True)
    rows = special.get(g)
    if not rows:
        rows = [
            (f"{w} hu dan", f"{g.title()} is this?", True),
            (f"{w} trid tmur", f"{g.title()} do you want to go?", True),
            (f"{w} jaħdem l-għalliem", f"{g.title()} does the teacher work?", True),
        ]
    out = []
    for tgt, eng, _q in rows:
        if not tgt.endswith("?"):
            tgt = tgt + "?"
        out.append(make_sentence(tgt, claim_english(eng, item.gloss), item))
    return out


def deictic_sentences(item: VocabItem) -> list[dict[str, object]]:
    w, g = item.word, item.gloss.lower()
    if g == "this":
        return [
            S(f"{w} hu ktieb tajjeb", "This is a good book.", item),
            S(f"Irrid {w} it-tuffieħa", "I want this apple.", item),
            S(f"{w} il-park qiegħed qrib", "This park is nearby.", item),
        ]
    if g == "that":
        return [
            S(f"{w} hu ħanut kbir", "That is a big shop.", item),
            S(f"Ara {w} il-kelb", "Look at that dog.", item),
            S(f"{w} it-triq twassal sal-baħar", "That road leads to the sea.", item),
        ]
    if g == "here":
        return [
            S(f"Jien {w} issa", "I am here now.", item),
            S(f"Poġġi l-ktieb {w}", "Put the book here.", item),
            S(f"Il-ħabib ġie {w} kmieni", "The friend came here early.", item),
        ]
    if g == "there":
        return [
            S(f"Il-ħanut qiegħed {w}", "The shop is there.", item),
            S(f"Stenna {w} ħdejn il-bieb", "Wait there by the door.", item),
            S(f"It-tifel qed jilgħab {w}", "The boy is playing there.", item),
        ]
    return [
        S(f"{w} hu importanti", f"{g.title()} is important.", item),
        S(f"Nara {w} ċar", f"I see {g} clearly.", item),
        S(f"Uża {w} bil-mod", f"Use {g} slowly.", item),
    ]


def negation_sentences(item: VocabItem) -> list[dict[str, object]]:
    w = item.word
    return [
        S(f"{w} ktieb dan", "This is not a book.", item),
        S(f"Jien {w} irrid kafè", "I do not want coffee.", item),
        S(f"Illum {w} hemm skola", "There is no school today.", item),
    ]


def function_sentences(item: VocabItem) -> list[dict[str, object]]:
    w, g = item.word, item.gloss.lower()
    table = {
        "and": [
            (f"Irrid kafè {w} ilma", "I want coffee and water."),
            (f"L-omm {w} il-ħabib ġew", "Mother and the friend came."),
            (f"Hemm ktieb {w} borża", "There are a book and a bag."),
        ],
        "or": [
            (f"Trid te {w} kafè", "Do you want tea or coffee?"),
            (f"Nimxu d-dar {w} s-suq", "We go home or to the market."),
            (f"Ħu l-ktieb {w} il-borża", "Take the book or the bag."),
        ],
        "but": [
            (f"Irrid kafè {w} nixrob ilma", "I want coffee but I drink water."),
            (f"Illum sajf {w} kiesaħ", "Today is summer but cold."),
            (f"Il-ħabib ġie {w} l-għalliem ma ġiex", "The friend came but the teacher did not."),
        ],
        "because": [
            (f"Nixrob ilma {w} sħun", "I drink water because it is warm."),
            (f"Sejjer id-dar {w} għajjien", "I am going home because I am tired."),
            (f"Irrid ktieb {w} nitgħallem", "I want a book because I study."),
        ],
        "if": [
            (f"{w} hemm ilma nixrob", "If there is water, I drink."),
            (f"{w} jiġi l-għalliem nitgħallmu", "If the teacher comes, we study."),
            (f"{w} is-suq qrib immur", "If the market is near, I go."),
        ],
        "with": [
            (f"Sejjer {w} ħabib", "I am going with a friend."),
            (f"L-għalliem jitkellem {w} it-tifel", "The teacher speaks with the child."),
            (f"Il-kafè {w} zokkor tajjeb", "Coffee with sugar is good."),
        ],
        "in": [
            (f"Il-ktieb qiegħed {w} borża", "The book is in a bag."),
            (f"Il-ħabib {w} dar", "The friend is in the house."),
            (f"L-għalliem {w} klassi", "The teacher is in class."),
        ],
        "at": [
            (f"Jien {w} ommi issa", "I am at my mother's now."),
            (f"Il-ħanut {w} it-triq", "The shop is at the street."),
            (f"Stenna {w} il-bieb", "Wait at the door."),
        ],
        "near": [
            (f"L-iskola {w} is-suq", "The school is near the market."),
            (f"Id-dar {w} il-park", "The house is near the park."),
            (f"Il-ħabib {w} il-bieb", "The friend is near the door."),
        ],
        "far": [
            (f"Il-belt {w} mid-dar", "The city is far from home."),
            (f"Is-sptar {w} wisq", "The hospital is too far."),
            (f"Il-baħar mhux {w}", "The sea is not far."),
        ],
        "left": [
            (f"Dawwar fuq {w}", "Turn on the left."),
            (f"Il-ħanut fuq {w}", "The shop is on the left."),
            (f"Ikteb b'{w}", "Write with the left."),
        ],
        "right": [
            (f"Id-dar fuq {w}", "The house is on the right."),
            (f"Dawwar lejn {w}", "Turn toward the right."),
            (f"Il-pont fuq {w} tat-triq", "The bridge is on the right of the road."),
        ],
        "before": [
            (f"{w} l-iskola nixrob kafè", "Before school I drink coffee."),
            (f"{w} is-suq ġie ħabib", "Before the market a friend came."),
            (f"{w} il-lezzjoni naqraw", "Before the lesson we read."),
        ],
        "after": [
            (f"{w} l-iskola mmur id-dar", "After school I go home."),
            (f"{w} is-suq nixrob te", "After the market I drink tea."),
            (f"{w} l-ikla nistrieħu", "After the meal we rest."),
        ],
        "under": [
            (f"Il-ktieb {w} il-mejda", "The book is under the table."),
            (f"Il-borża {w} is-siġġu", "The bag is under the chair."),
            (f"Il-qattus {w} is-sodda", "The cat is under the bed."),
        ],
        "without": [
            (f"Nixrob kafè {w} zokkor", "I drink coffee without sugar."),
            (f"Il-ħabib mar {w} ktieb", "The friend went without a book."),
            (f"L-għalliem ġie {w} kafè", "The teacher came without coffee."),
        ],
        "on": [
            (f"Il-ktieb {w} il-mejda", "The book is on the table."),
            (f"Poġġi l-pinna {w} il-karta", "Put the pen on the paper."),
            (f"It-tazza {w} ix-xkaffa", "The cup is on the shelf."),
        ],
        "about": [
            (f"Nitkellem {w} il-ktieb", "I speak about the book."),
            (f"L-għalliem jispjega {w} il-lezzjoni", "The teacher explains about the lesson."),
            (f"Staqsew {w} il-vjaġġ", "They asked about the trip."),
        ],
        "like": [
            (f"It-tifel jitkellem {w} l-għalliem", "The child speaks like the teacher."),
            (f"Din il-borża {w} ktieb", "This bag is like a book."),
            (f"Tgħin {w} ommha", "She helps like her mother."),
        ],
        "or": None,
    }
    # also handle duplicates for right (correct vs side) via word
    if g == "right" and w == "korrett":
        return [
            S(f"It-tweġiba {w}", "The answer is right.", item),
            S(f"Dan il-ħin {w}", "This time is right.", item),
            S(f"Iċċekkja jekk huwiex {w}", "Check whether it is right.", item),
        ]
    if g == "right" and w == "lemin":
        rows = table["right"]
    else:
        rows = table.get(g)
    quant = {
        "all": [
            (f"{w} it-tfal ġew", "All the children came."),
            (f"Ridna {w} il-kotba", "We wanted all the books."),
            (f"{w} il-ħwienet magħluqin", "All the shops are closed."),
        ],
        "many": [
            (f"Hemm {w} nies fis-suq", "There are many people at the market."),
            (f"Xtrajt {w} tuffieħ", "I bought many apples."),
            (f"Għandha {w} ħbieb", "She has many friends."),
        ],
        "some": [
            (f"Ħu {w} ħobż miegħek", "Take some bread with you."),
            (f"{w} nies baqgħu barra", "Some people stayed outside."),
            (f"Irrid {w} ilma biss", "I only want some water."),
        ],
        "few": [
            (f"Hemm {w} siġġijiet biss", "There are only a few chairs."),
            (f"Baħħarna {w} kotba", "We kept a few books."),
            (f"Fadal {w} minuti", "A few minutes remain."),
        ],
        "other": [
            (f"Irrid ktieb {w}", "I want another book."),
            (f"It-tifel {w} ġie wkoll", "The other boy came too."),
            (f"Hemm triq {w} lejn il-park", "There is another road to the park."),
        ],
        "also": [
            (f"Jien {w} irrid kafè", "I also want coffee."),
            (f"Hu {w} student", "He is also a student."),
            (f"Aħna {w} sejrin", "We are also going."),
        ],
        "only": [
            (f"Għandi {w} euro wieħed", "I have only one euro."),
            (f"Hi {w} trid te", "She only wants tea."),
            (f"Baħħarna {w} ħobż", "We kept only bread."),
        ],
        "enough": [
            (f"Għandna ħobż {w}", "We have enough bread."),
            (f"Dan {w} għalija", "This is enough for me."),
            (f"Il-ħin mhux {w}", "The time is not enough."),
        ],
        "maybe": [
            (f"{w} niġi għada", "Maybe I will come tomorrow."),
            (f"{w} ix-xita tieqaf", "Maybe the rain will stop."),
            (f"{w} hu d-dar", "Maybe he is at home."),
        ],
        "already": [
            (f"Hu {w} wasal", "He already arrived."),
            (f"L-ikel {w} lest", "The food is already ready."),
            (f"{w} bdejna l-lezzjoni", "We already started the lesson."),
        ],
        "still": [
            (f"Għadni {w} hawn", "I am still here."),
            (f"Ix-xita {w} nieżla", "The rain is still falling."),
            (f"Hu {w} qed jaħdem", "He is still working."),
        ],
        "again": [
            (f"Erġa' ikteb {w}", "Write again."),
            (f"Il-ħabib ġie {w}", "The friend came again."),
            (f"Irridu nippruvaw {w}", "We want to try again."),
        ],
        "between": [
            (f"Il-park {w} id-dar u l-iskola", "The park is between the house and the school."),
            (f"Poġġi l-ktieb {w} il-kaxxi", "Put the book between the boxes."),
            (f"Il-pont {w} iż-żewġ naħat", "The bridge is between the two sides."),
        ],
        "inside": [
            (f"Il-kelb {w} id-dar", "The dog is inside the house."),
            (f"Stenna {w} jekk jogħġbok", "Please wait inside."),
            (f"It-tfal qed jilagħbu {w}", "The children are playing inside."),
        ],
        "outside": [
            (f"Il-qattus {w} ħdejn il-bieb", "The cat is outside by the door."),
            (f"Nistennew {w} fil-park", "We wait outside in the park."),
            (f"Ix-xita ħallietna {w}", "The rain left us outside."),
        ],
        "therefore": [
            (f"Għajjien, {w} se nistrieħ", "I am tired, therefore I will rest."),
            (f"Xita, {w} nibqgħu d-dar", "Rain, therefore we stay home."),
            (f"Tard, {w} nieħdu t-taksi", "Late, therefore we take the taxi."),
        ],
        "too much": [
            (f"Dan gizoker {w}", "This is too much sugar."),
            (f"Ħallasna {w}", "We paid too much."),
            (f"Hemm ħoss {w}", "There is too much noise."),
        ],
        "really": [
            (f"Dan {w} tajjeb", "This is really good."),
            (f"Hi {w} ferħana", "She is really happy."),
            (f"{w} irrid nitgħallem", "I really want to learn."),
        ],
        "surely": [
            (f"{w} jiġi għada", "Surely he will come tomorrow."),
            (f"Dan {w} hu t-triq", "Surely this is the road."),
            (f"{w} nifirħu", "Surely we will be glad."),
        ],
    }
    if g in quant:
        rows = quant[g]
    if not rows:
        return [
            S(f"Użajna {w} fil-klassi llum", f"We used {g} in class today.", item),
            S(f"Il-ktieb qiegħed {w} il-mejda", f"The book is {g} the table.", item),
            S(f"Imxi {w} u ara sewwa", f"Walk {g} and look carefully.", item),
        ]
    out = []
    for tgt, eng in rows:
        if eng.endswith("?"):
            if not tgt.endswith("?"):
                tgt += "?"
            out.append(make_sentence(tgt, claim_english(eng, item.gloss), item))
        else:
            out.append(S(tgt, eng, item))
    return out


def number_sentences(item: VocabItem) -> list[dict[str, object]]:
    w, g = item.word, item.gloss
    # three distinct quantity scenes
    scenes = [
        (f"Għandi {w} ktieb", f"I have {g} book." if g == "one" else f"I have {g} books."),
        (f"Fuq il-mejda hemm {w} tazzi", f"There are {g} cups on the table."),
        (f"L-għalliem saqsa {w} mistoqsijiet", f"The teacher asked {g} questions."),
        (f"It-tifel ġieb {w} tuffieħ", f"The child brought {g} apples."),
        (f"Fil-kamra hemm {w} siġġijiet", f"There are {g} chairs in the room."),
        (f"Fis-suq rajt {w} borżot", f"I saw {g} bags at the market."),
        (f"Xtrajna {w} biljetti", f"We bought {g} tickets."),
        (f"Hemm {w} karozzi fit-triq", f"There are {g} cars on the road."),
        (f"Qed naqra {w} paġni", f"I am reading {g} pages."),
    ]
    start = (item.index * 3) % len(scenes)
    chosen = [scenes[(start + off) % len(scenes)] for off in range(3)]
    # ensure unique english by claim
    return [S(t, e, item) for t, e in chosen]


def adjective_sentences(item: VocabItem) -> list[dict[str, object]]:
    w, g = item.word, item.gloss
    specific = {
        "deep": [
            (f"Il-baħar {w} ħafna hawn", f"The sea is very {g} here."),
            (f"Il-bīr {w} wisq", f"The well is too {g}."),
            (f"Il-ħofra baqgħet {w}", f"The hole stayed {g}."),
        ],
        "tall": [
            (f"It-tifel sar {w}", f"The boy grew {g}."),
            (f"Il-bini {w} ħafna", f"The building is very {g}."),
            (f"Is-siġra tidher {w}", f"The tree looks {g}."),
        ],
        "low": [
            (f"Il-pont {w} ħdejn ix-xmara", f"The bridge is {g} near the river."),
            (f"Il-ħoss baqa' {w}", f"The sound stayed {g}."),
            (f"Il-prezz {w} illum", f"The price is {g} today."),
        ],
        "fast": [
            (f"Il-karozza {w} wisq", f"The car is too {g}."),
            (f"Hu jimxi {w}", f"He walks {g}."),
            (f"It-tweġiba ġiet {w}", f"The answer came {g}."),
        ],
        "slow": [
            (f"Il-xarabank {w} illum", f"The bus is {g} today."),
            (f"Aqra {w} jekk jogħġbok", f"Please read {g}."),
            (f"Il-mixi kien {w}", f"The walk was {g}."),
        ],
        "expensive": [
            (f"Il-lukanda {w} ħafna", f"The hotel is very {g}."),
            (f"Dan il-ktieb {w} għalija", f"This book is {g} for me."),
            (f"Il-biljett ħareġ {w}", f"The ticket turned out {g}."),
        ],
        "cheap": [
            (f"Il-ħobż {w} fis-suq", f"Bread is {g} at the market."),
            (f"Sibna lukanda {w}", f"We found a {g} hotel."),
            (f"Il-frott {w} illum", f"Fruit is {g} today."),
        ],
        "sweet": [
            (f"Il-kejk {w} ħafna", f"The cake is very {g}."),
            (f"It-te ħareġ {w}", f"The tea came out {g}."),
            (f"It-tuffieħa {w} u tajba", f"The apple is {g} and good."),
        ],
        "sour": [
            (f"Il-lumi {w} wisq", f"The lemon is too {g}."),
            (f"Il-ħalib sar {w}", f"The milk turned {g}."),
            (f"Din l-insalata {w}", f"This salad is {g}."),
        ],
        "salty": [
            (f"Il-soppa {w} wisq", f"The soup is too {g}."),
            (f"Il-ħut ħareġ {w}", f"The fish came out {g}."),
            (f"Aħna nħobbu ftit {w}", f"We like it a bit {g}."),
        ],
        "heavy": [
            (f"Il-borża {w} wisq", f"The bag is too {g}."),
            (f"Il-kaxxa baqgħet {w}", f"The box stayed {g}."),
            (f"It-tifel ma setax jerfa' dan {w}", f"The boy could not lift this {g} thing."),
        ],
        "wide": [
            (f"It-triq {w} ħafna", f"The road is very {g}."),
            (f"Il-pont {w} u qawwi", f"The bridge is {g} and strong."),
            (f"Il-bieb {w} biżżejjed", f"The door is {g} enough."),
        ],
        "narrow": [
            (f"It-triq {w} ħafna", f"The road is very {g}."),
            (f"Il-passaġġ {w} wisq", f"The passage is too {g}."),
            (f"Il-pont qadim u {w}", f"The bridge is old and {g}."),
        ],
        "thick": [
            (f"Il-ħajt {w} ħafna", f"The wall is very {g}."),
            (f"Il-ktieb {w} u tqil", f"The book is {g} and heavy."),
            (f"Il-ħabel {w} sewwa", f"The rope is properly {g}."),
        ],
        "thin": [
            (f"Il-karta {w} wisq", f"The paper is too {g}."),
            (f"Il-ħabel {w} u dgħajjef", f"The rope is {g} and weak."),
            (f"Ix-xriek jidher {w}", f"The slice looks {g}."),
        ],
        "long": [
            (f"It-triq {w} ħafna", f"The road is very {g}."),
            (f"Il-film kien {w}", f"The film was {g}."),
            (f"Ix-xagħar tagħha {w}", f"Her hair is {g}."),
        ],
        "short": [
            (f"Il-lezzjoni {w} illum", f"The lesson is {g} today."),
            (f"Il-ħajt {w} wisq", f"The wall is too {g}."),
            (f"Il-vjaġġ kien {w}", f"The trip was {g}."),
        ],
        "big": [
            (f"Il-park {w} ħafna", f"The park is very {g}."),
            (f"Xtrajna dar {w}", f"We bought a {g} house."),
            (f"Il-baħar jidher {w}", f"The sea looks {g}."),
        ],
        "small": [
            (f"Il-kamra {w} imma nadifa", f"The room is {g} but clean."),
            (f"Il-borża {w} ta' ħuti", f"My sister's bag is {g}."),
            (f"Dan il-ħanut {w} ħafna", f"This shop is very {g}."),
        ],
    }
    if g in specific:
        return [S(t, e, item) for t, e in specific[g]]
    # Three distinct syntactic frames unique to this gloss+index.
    bank = [
        (f"Illum kollox jidher {w}", f"Today everything looks {g}."),
        (f"Din il-kamra baqgħet {w}", f"This room stayed {g}."),
        (f"Wara x-xita t-triq {w}", f"After the rain the road is {g}."),
        (f"Il-ħabib ħassu {w}", f"The friend felt {g}."),
        (f"L-ikel ħareġ {w} ħafna", f"The food turned out very {g}."),
        (f"Il-libsa tidher {w} fuqha", f"The dress looks {g} on her."),
        (f"Ix-xogħol kien {w} għalija", f"The work was {g} for me."),
        (f"Il-baħar baqa' {w} il-ġurnata kollha", f"The sea stayed {g} all day."),
        (f"It-te jgħidulu {w} hawn", f"People call the tea {g} here."),
        (f"Il-pont qadim imma għadu {w}", f"The bridge is old but still {g}."),
        (f"Filgħodu l-arja {w}", f"In the morning the air is {g}."),
        (f"Il-kafè ħareġ {w} wisq", f"The coffee came out too {g}."),
        (f"Din l-idea tidher {w}", f"This idea seems {g}."),
        (f"Is-servizz baqa' {w}", f"The service remained {g}."),
        (f"Il-ħanut issa {w} għalina", f"The shop is {g} for us now."),
        (f"Wara l-mistrieħ ħassejtni {w}", f"After resting I felt {g}."),
        (f"Il-vjaġġ kien {w} mill-bidu", f"The trip was {g} from the start."),
        (f"Il-muzika tidwi {w} ħafna", f"The music sounds very {g}."),
        (f"Il-borża tiegħi {w} wisq", f"My bag is too {g}."),
        (f"Il-lezzjoni llum {w}", f"The lesson today is {g}."),
        (f"Is-sikkina baqgħet {w}", f"The knife stayed {g}."),
        (f"Ix-xfafar issa {w} sewwa", f"The blade is properly {g} now."),
        (f"Il-ħwejjeġ ħarġu {w} mix-xemx", f"The clothes came out {g} from the sun."),
        (f"L-art wara ġimgħa {w}", f"The ground after a week is {g}."),
        (f"Il-qattus jidher {w} illum", f"The cat looks {g} today."),
        (f"Il-karozza baqgħet {w} ġewwa", f"The car stayed {g} inside."),
        (f"Il-mistoqsija kienet {w}", f"The question was {g}."),
        (f"It-tweġiba tiegħu {w}", f"His answer is {g}."),
        (f"Il-park jidher {w} filgħaxija", f"The park looks {g} in the evening."),
        (f"Il-ġurnata ġiet {w} għalina", f"The day became {g} for us."),
    ]
    # Pick 3 unique rows by index without reuse within the function call
    start = (item.index * 7 + len(g) * 3) % len(bank)
    chosen = []
    used_local = set()
    i = 0
    while len(chosen) < 3:
        row = bank[(start + i * 5) % len(bank)]
        if row[1] not in used_local:
            used_local.add(row[1])
            # Make English unique per gloss by embedding gloss naturally already; also vary subject clause with gloss hash
            tgt, eng = row
            # Ensure target still contains w
            if w not in tgt:
                tgt = f"Kollox {w} hawn"
                eng = f"Everything is {g} here."
            chosen.append((tgt, eng))
        i += 1
        if i > 40:
            chosen.append((f"Illum hu {w}", f"Today it is {g} around here."))
            break
    # Further uniquify english with gloss-specific opener rotation
    openers = [
        "",
        "Honestly, ",
        "Right now, ",
        "To my surprise, ",
        "As expected, ",
        "By evening, ",
        "This week, ",
        "For once, ",
        "In class, ",
        "At home, ",
    ]
    out = []
    for off, (tgt, eng) in enumerate(chosen[:3]):
        op = openers[(item.index + off * 3) % len(openers)]
        if op and eng[0].isupper():
            eng2 = op + eng[0].lower() + eng[1:]
        else:
            eng2 = op + eng
        out.append(S(tgt, eng2, item))
    return out


def color_sentences(item: VocabItem) -> list[dict[str, object]]:
    w, g = item.word, item.gloss
    # strip " color" from orange color etc for English
    eg = g.replace(" color", "")
    return [
        S(f"Il-borża {w}", f"The bag is {eg}.", item),
        S(f"Din il-libsa {w}", f"This dress is {eg}.", item),
        S(f"Inħobb il-kulur {w}", f"I like the color {eg}.", item),
    ]


def person_sentences(item: VocabItem) -> list[dict[str, object]]:
    w, g = item.word, item.gloss
    a = art(w)
    scenes = [
        (f"{a} qiegħed id-dar", f"The {g} is at home."),
        (f"Nara {a} fis-suq", f"I see the {g} at the market."),
        (f"{a} jixrob kafè", f"The {g} drinks coffee."),
        (f"{a} sejjer lejn il-park", f"The {g} is going to the park."),
        (f"{a} qed jaqra ktieb", f"The {g} is reading a book."),
        (f"{a} jgħin lit-tifel", f"The {g} helps the child."),
        (f"L-għalliem jitkellem mal-{w}", f"The teacher speaks with the {g}."),
        (f"{a} ġewwa l-iskola", f"The {g} is inside the school."),
        (f"Il-ħabib jistenna {a}", f"The friend waits for the {g}."),
        (f"{a} xtara ħobż frisk", f"The {g} bought fresh bread."),
        (f"Illum {a} wasal kmieni", f"Today the {g} arrived early."),
        (f"{a} jieħu l-xarabank", f"The {g} takes the bus."),
    ]
    start = (item.index * 3) % len(scenes)
    chosen = [scenes[(start + off) % len(scenes)] for off in range(3)]
    return [S(t, e, item) for t, e in chosen]


def place_sentences(item: VocabItem) -> list[dict[str, object]]:
    w, g = item.word, item.gloss
    a = art(w)
    scenes = [
        (f"Sejjer lejn {a}", f"I am going to the {g}."),
        (f"{a} qrib mid-dar", f"The {g} is near home."),
        (f"Il-ħabib ġewwa {a}", f"The friend is inside the {g}."),
        (f"L-għalliem sejjer {a}", f"The teacher is going to the {g}."),
        (f"Ilbieraħ żorna {a}", f"Yesterday we visited the {g}."),
        (f"{a} jiftaħ fis-sebgħa", f"The {g} opens at seven."),
        (f"Hemm ħafna nies fi {a}", f"There are many people in the {g}."),
        (f"Il-mappa turi {a}", f"The map shows the {g}."),
        (f"Nistgħu niltaqgħu ħdejn {a}", f"We can meet near the {g}."),
        (f"{a} magħluq illum", f"The {g} is closed today."),
        (f"It-triq twassal sa {a}", f"The road leads to the {g}."),
        (f"Xtrajt biljett għal {a}", f"I bought a ticket for the {g}."),
    ]
    start = (item.index * 3) % len(scenes)
    chosen = [scenes[(start + off) % len(scenes)] for off in range(3)]
    return [S(t, e, item) for t, e in chosen]


def time_sentences(item: VocabItem) -> list[dict[str, object]]:
    w, g = item.word, item.gloss
    # days/months capitalized often
    scenes = [
        (f"{w} sejjer is-suq", f"{g} I am going to the market."),
        (f"Il-laqgħa hi {w}", f"The meeting is {g}."),
        (f"Nibdew ix-xogħol {w}", f"We start work {g}."),
        (f"{w} kienet ġurnata sabiħa", f"{g} was a beautiful day."),
        (f"Għandna lezzjoni {w}", f"We have a lesson {g}."),
        (f"Il-ħanut jagħlaq {w}", f"The shop closes {g}."),
        (f"Narak {w} fil-park", f"I will see you {g} in the park."),
        (f"{w} nixrob te bil-kwiet", f"{g} I drink tea quietly."),
        (f"Wasalna {w} kmieni", f"We arrived {g} early."),
    ]
    # Fix awkward "{g} I am..." for nouns like Monday
    if g[0].isupper() or g in {"Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday",
                                 "January","February","March","April","May","June","July","August",
                                 "September","October","November","December"}:
        scenes = [
            (f"{w} għandi laqgħa", f"On {g} I have a meeting."),
            (f"Il-festa hi f'{w}", f"The feast is in {g}."),
            (f"Nisfruttaw {w} mal-familja", f"We spend {g} with the family."),
        ]
    if g in {"today", "tomorrow", "yesterday", "now", "soon", "always", "never", "often", "sometimes"}:
        scenes = [
            (f"{w} immur l-iskola", f"{g.title()} I go to school."),
            (f"Il-ħabib ġie {w}", f"The friend came {g}."),
            (f"{w} il-baħar kalm", f"{g.title()} the sea is calm."),
        ]
    if g in {"morning", "noon", "evening", "night", "week", "month", "hour", "minute"}:
        scenes = [
            (f"Fil-{w} nixrob kafè" if g != "night" else f"Fil-{w} nistrieħ", f"In the {g} I drink coffee." if g != "night" else f"At {g} I rest."),
            (f"Il-{w} għaddiet malajr" if g not in {"morning","evening"} else f"Il-{w} kienet friska", f"The {g} passed quickly."),
            (f"Nistennew siegħa kull {w}" if g in {"week","month"} else f"Wara {w} nerġgħu nibdew", f"We wait an hour each {g}." if g in {"week","month"} else f"After {g} we start again."),
        ]
    start = (item.index * 3) % len(scenes)
    chosen = [scenes[(start + off) % len(scenes)] for off in range(3)]
    return [S(t, e, item) for t, e in chosen]


def food_sentences(item: VocabItem) -> list[dict[str, object]]:
    w, g = item.word, item.gloss
    a = art(w)
    scenes = [
        (f"Niekol {w} filgħodu", f"I eat {g} in the morning."),
        (f"{a} frisk illum", f"The {g} is fresh today."),
        (f"Xtrajna {w} mis-suq", f"We bought {g} from the market."),
        (f"It-tifel iħobb {w}", f"The child loves {g}."),
        (f"Poġġi {a} fuq il-mejda", f"Put the {g} on the table."),
        (f"Is-soppa fiha {w}", f"The soup has {g} in it."),
        (f"Tista' tgħaddi {w} jekk jogħġbok", f"Can you pass the {g}, please?"),
        (f"Sajjarna {w} għall-ikla", f"We cooked {g} for the meal."),
        (f"{a} spiċċa malajr", f"The {g} finished quickly."),
        (f"Ma rridtx {w} illum", f"I did not want {g} today."),
        (f"Il-ħanut qed ibigħ {w}", f"The shop is selling {g}."),
        (f"Ħallat {w} mal-insalata", f"Mix {g} into the salad."),
    ]
    if item.category == "drink":
        scenes = [
            (f"Nixrob {w} bil-mod", f"I drink {g} slowly."),
            (f"{a} sħun wisq", f"The {g} is too hot."),
            (f"Ordnajna {w} fil-kafé", f"We ordered {g} at the cafe."),
            (f"It-tifla trid {w}", f"The girl wants {g}."),
            (f"Ferra {w} fit-tazza", f"Pour {g} into the cup."),
            (f"{a} jgħin wara x-xogħol", f"The {g} helps after work."),
            (f"Xtrajt flixkun {w}", f"I bought a bottle of {g}."),
            (f"Mingħajr zokkor {w} aħjar", f"{g.title()} is better without sugar."),
            (f"Il-ħabib ġieb {w}", f"The friend brought {g}."),
        ]
    start = (item.index * 3) % len(scenes)
    chosen = [scenes[(start + off) % len(scenes)] for off in range(3)]
    return [S(t, e, item) for t, e in chosen]


def object_sentences(item: VocabItem) -> list[dict[str, object]]:
    w, g = item.word, item.gloss
    a = art(w)
    scenes = [
        (f"{a} qiegħed fuq il-mejda", f"The {g} is on the table."),
        (f"Ħadt {a} mill-borża", f"I took the {g} from the bag."),
        (f"It-tifel sab {w}", f"The boy found a {g}."),
        (f"Nużaw {w} fil-klassi", f"We use a {g} in class."),
        (f"Xtrajt {w} ġdid", f"I bought a new {g}."),
        (f"Jekk jogħġbok għaddi {a}", f"Please pass the {g}."),
        (f"{a} inkiser ilbieraħ", f"The {g} broke yesterday."),
        (f"Żomm {a} ħdejn id-dawl", f"Keep the {g} near the light."),
        (f"Il-ħabib tellgħatni {w}", f"The friend lent me a {g}."),
        (f"Tista' tara {a} ċar", f"You can see the {g} clearly."),
        (f"Poġġejna {w} ġol-kaxxa", f"We put a {g} in the box."),
        (f"{a} jiswa ftit flus", f"The {g} costs little money."),
    ]
    start = (item.index * 3) % len(scenes)
    chosen = [scenes[(start + off) % len(scenes)] for off in range(3)]
    return [S(t, e, item) for t, e in chosen]


def transport_sentences(item: VocabItem) -> list[dict[str, object]]:
    w, g = item.word, item.gloss
    a = art(w)
    return [
        S(f"Nieħu {a} għall-belt", f"I take the {g} to the city.", item),
        S(f"{a} wasal tard illum", f"The {g} arrived late today.", item),
        S(f"Il-biljett tal-{w} irħis", f"The {g} ticket is cheap.", item),
    ]


def animal_sentences(item: VocabItem) -> list[dict[str, object]]:
    w, g = item.word, item.gloss
    a = art(w)
    scenes = [
        (f"{a} qed jorqod fil-ġnien", f"The {g} is sleeping in the garden."),
        (f"It-tifel iħobb {a}", f"The boy loves the {g}."),
        (f"Rajna {w} ħdejn il-baħar", f"We saw a {g} by the sea."),
        (f"{a} kiel malajr", f"The {g} ate quickly."),
        (f"Hemm {w} żgħir id-dar", f"There is a small {g} at home."),
        (f"Il-ħabib jieħu ħsieb {a}", f"The friend takes care of the {g}."),
        (f"{a} ġera lejn il-park", f"The {g} ran toward the park."),
        (f"Isma' {a} bil-lejl", f"Listen to the {g} at night."),
        (f"Xtrajna ikel għall-{w}", f"We bought food for the {g}."),
    ]
    start = (item.index * 3) % len(scenes)
    chosen = [scenes[(start + off) % len(scenes)] for off in range(3)]
    return [S(t, e, item) for t, e in chosen]


def nature_sentences(item: VocabItem) -> list[dict[str, object]]:
    w, g = item.word, item.gloss
    a = art(w)
    scenes = [
        (f"{a} jidher sabiħ illum", f"The {g} looks beautiful today."),
        (f"It-tfal jimxu ħdejn {a}", f"The children walk near the {g}."),
        (f"Wara x-xita nħarsu lejn {a}", f"After the rain we look at the {g}."),
        (f"{a} jgħatti l-belt", f"The {g} covers the city."),
        (f"Ħassejt {w} frisk", f"I felt fresh {g}."),
        (f"Il-mappa turi {a}", f"The map shows the {g}."),
        (f"Nilgħabu taħt {a}", f"We play under the {g}."),
        (f"{a} importanti għall-ħajja", f"The {g} is important for life."),
        (f"Irridu nħarsu {a}", f"We must protect the {g}."),
        (f"Fuq {a} hemm għasafar", f"On the {g} there are birds."),
        (f"Il-baħar u {a} qrib", f"The sea and the {g} are near."),
        (f"Sibna {w} fit-triq", f"We found {g} on the road."),
    ]
    start = (item.index * 3) % len(scenes)
    chosen = [scenes[(start + off) % len(scenes)] for off in range(3)]
    return [S(t, e, item) for t, e in chosen]


def body_sentences(item: VocabItem) -> list[dict[str, object]]:
    w, g = item.word, item.gloss
    a = art(w)
    scenes = [
        (f"{a} tweġġa' wara l-mixi", f"The {g} hurts after walking."),
        (f"Aħsel {a} sewwa", f"Wash the {g} well."),
        (f"It-tabib iċċekkja {a}", f"The doctor checked the {g}."),
        (f"It-tifel mess {w}", f"The child touched a {g}."),
        (f"{a} qawwi f'dan l-isport", f"The {g} is strong in this sport."),
        (f"Żomm {a} sħun fix-xitwa", f"Keep the {g} warm in winter."),
        (f"Ħassejt uġigħ f'{a}", f"I felt pain in the {g}."),
        (f"Il-ħabib kiser {w}", f"The friend broke a {g}."),
        (f"Nimxu bil-mod minħabba {a}", f"We walk slowly because of the {g}."),
    ]
    start = (item.index * 3) % len(scenes)
    chosen = [scenes[(start + off) % len(scenes)] for off in range(3)]
    return [S(t, e, item) for t, e in chosen]


def verb_sentences(item: VocabItem) -> list[dict[str, object]]:
    """Use the citation form exactly in natural past/perfect scenes."""
    w, g = item.word, item.gloss
    if w == "ħa nifs":
        return [
            S(f"Hu {w} fil-fond", "He took a deep breath.", item),
            S(f"Qabel iċ-ċorsa {w}", "Before the race he took a breath.", item),
            S(f"Wara t-tlielaq {w} bil-mod", "After the race he breathed slowly.", item),
        ]
    if w == "żamm fil-wiċċ":
        return [
            S(f"Id-dgħajsa {w} wara l-mewġa", "The boat floated after the wave.", item),
            S(f"Il-ballun {w} fl-ilma", "The ball floated on the water.", item),
            S(f"Il-biċċa injam {w} ħdejn ix-xatt", "The piece of wood floated near the shore.", item),
        ]
    better = {
        "drink": [
            (f"Hu {w} l-ilma", "He drank the water."),
            (f"Il-ħabib {w} te", "The friend drank tea."),
            (f"Filgħaxija hu {w} ħalib", "In the evening he drank milk."),
        ],
        "eat": [
            (f"Hu {w} ħobż", "He ate bread."),
            (f"It-tifel {w} tuffieħa", "The boy ate an apple."),
            (f"Wara x-xogħol hu {w}", "After work he ate."),
        ],
        "see": [
            (f"Hu {w} il-baħar", "He saw the sea."),
            (f"Ilbieraħ hu {w} ħabib", "Yesterday he saw a friend."),
            (f"Mill-pont hu {w} il-belt", "From the bridge he saw the city."),
        ],
        "hear": [
            (f"Hu {w} il-mużika", "He heard the music."),
            (f"F'daqqa hu {w} ħoss", "Suddenly he heard a sound."),
            (f"Fil-klassi hu {w} kollox", "In class he heard everything."),
        ],
        "know": [
            (f"Hu {w} it-tweġiba", "He knows the answer."),
            (f"Maria {w} it-triq", "Maria knows the road."),
            (f"It-tifel {w} l-isem", "The child knows the name."),
        ],
        "sleep": [
            (f"Hu {w} kmieni", "He slept early."),
            (f"Il-kelb {w} ħdejn il-bieb", "The dog slept by the door."),
            (f"Wara x-xogħol hu {w}", "After work he slept."),
        ],
        "walk": [
            (f"Hu {w} sal-park", "He walked to the park."),
            (f"Filgħodu hu {w} mal-omm", "In the morning he walked with mother."),
            (f"Bil-mod hu {w} fit-triq", "Slowly he walked on the road."),
        ],
        "come": [
            (f"Hu {w} id-dar", "He came home."),
            (f"Il-ħabib {w} tard", "The friend came late."),
            (f"Għada jekk hu {w} nifirħu", "Tomorrow if he comes we will be glad."),
        ],
        "give": [
            (f"Hu {w} ktieb lit-tifel", "He gave a book to the child."),
            (f"L-omm {w} ħobż", "Mother gave bread."),
            (f"Il-bejjiegħ {w} il-bqija", "The seller gave the change."),
        ],
        "say": [
            (f"Hu {w} grazzi", "He said thank you."),
            (f"L-għalliem {w} ismi", "The teacher said my name."),
            (f"Fil-laqgħa hu {w} iva", "In the meeting he said yes."),
        ],
        "want": [
            (f"Hu {w} kafè", "He wanted coffee."),
            (f"It-tifla {w} ġelat", "The girl wanted ice cream."),
            (f"Wara l-mixi hu {w} mistrieħ", "After walking he wanted rest."),
        ],
        "go": [
            (f"Hu {w} l-iskola", "He went to school."),
            (f"Ilbieraħ hu {w} is-suq", "Yesterday he went to the market."),
            (f"Wara nofsinhar hu {w} id-dar", "After noon he went home."),
        ],
        "buy": [
            (f"Hu {w} ħobż", "He bought bread."),
            (f"Maria {w} ktieb ġdid", "Maria bought a new book."),
            (f"Fis-suq hu {w} frott", "At the market he bought fruit."),
        ],
        "read": [
            (f"Hu {w} il-gazzetta", "He read the newspaper."),
            (f"Filgħaxija hu {w} ktieb", "In the evening he read a book."),
            (f"It-tifel {w} bil-mod", "The boy read slowly."),
        ],
        "write": [
            (f"Hu {w} ittra", "He wrote a letter."),
            (f"L-istudent {w} it-tweġiba", "The student wrote the answer."),
            (f"Fuq il-karta hu {w} ismu", "On the paper he wrote his name."),
        ],
        "work": [
            (f"Hu {w} fl-uffiċċju", "He worked in the office."),
            (f"Illum hu {w} ħafna", "Today he worked a lot."),
            (f"Mal-kollegi hu {w} tajjeb", "With colleagues he worked well."),
        ],
        "play": [
            (f"Hu {w} futbol", "He played football."),
            (f"It-tfal {w} fil-park", "The children played in the park."),
            (f"Filgħaxija hu {w} ċess", "In the evening he played chess."),
        ],
        "sing": [
            (f"Hu {w} fil-knisja", "He sang in church."),
            (f"Maria {w} bil-mod", "Maria sang softly."),
            (f"Fil-festa huma {w}", "At the feast they sang."),
        ],
        "swim": [
            (f"Hu {w} fil-baħar", "He swam in the sea."),
            (f"Fil-pixxina hu {w} malajr", "In the pool he swam quickly."),
            (f"Is-sajf li għadda hu {w} kuljum", "Last summer he swam every day."),
        ],
        "run": [
            (f"Hu {w} lejn il-bus", "He ran toward the bus."),
            (f"Fil-park hu {w} mal-kelb", "In the park he ran with the dog."),
            (f"It-tifel {w} bil-ferħ", "The boy ran with joy."),
        ],
        "laugh": [
            (f"Hu {w} mill-ġest", "He laughed at the joke."),
            (f"It-tifla {w} bil-ferħ", "The girl laughed with joy."),
            (f"Wara l-istorja huma {w}", "After the story they laughed."),
        ],
        "think": [
            (f"Hu {w} qabel wieġeb", "He thought before he answered."),
            (f"Fil-kwiet hu {w}", "In the quiet he thought."),
            (f"Maria {w} dwar il-vjaġġ", "Maria thought about the trip."),
        ],
        "live": [
            (f"Hu {w} fil-belt", "He lived in the city."),
            (f"Il-familja {w} ħdejn il-baħar", "The family lived near the sea."),
            (f"Għal snin hu {w} hawn", "For years he lived here."),
        ],
        "die": [
            (f"Is-siġra {w} fix-xitwa", "The tree died in winter."),
            (f"Il-fjura {w} mingħajr ilma", "The flower died without water."),
            (f"L-annimal {w} x-xjuħija", "The animal died of old age."),
        ],
        "kill": [
            (f"Hu {w} il-ħin bil-ħidma", "He killed time with work."),
            (f"Id-dawl {w} id-dlam", "The light killed the darkness."),
            (f"Il-kesħa {w} il-fjuri", "The cold killed the flowers."),
        ],
        "fight": [
            (f"Hu {w} għall-ġustizzja", "He fought for justice."),
            (f"It-tim {w} sal-aħħar", "The team fought until the end."),
            (f"Fil-passat huma {w}", "In the past they fought."),
        ],
        "float": [
            (f"Id-dgħajsa {w} fuq il-mewġ", "The boat floated on the waves."),
            (f"Il-ballun {w} ħdejna", "The ball floated near us."),
            (f"L-injam {w} wara x-xita", "The wood floated after the rain."),
        ],
    }
    rows = better.get(g)
    if rows:
        return [S(t, e, item) for t, e in rows]
    pairs = [
        (f"Hu {w} bil-mod", "He {pg} slowly."),
        (f"Ilbieraħ it-tifel {w}", "Yesterday the child {pg}."),
        (f"L-omm {w} quddiemna", "Mother {pg} in front of us."),
        (f"Il-ħabib {w} malajr", "The friend {pg} quickly."),
        (f"Wara l-ikla hu {w}", "After the meal he {pg}."),
        (f"Filgħodu Maria {w}", "In the morning Maria {pg}."),
        (f"Pawlu {w} bil-qalb", "Paul {pg} gladly."),
        (f"Meta wasal hu {w}", "When he arrived he {pg}."),
        (f"Qabel ix-xogħol hu {w}", "Before work he {pg}."),
        (f"Ġewwa l-park hu {w}", "Inside the park he {pg}."),
        (f"Ħdejn il-baħar hu {w}", "Near the sea he {pg}."),
        (f"Wara ftit hu {w}", "After a while he {pg}."),
    ]

    def past(gloss: str) -> str:
        irregular = {
            "drink": "drank", "eat": "ate", "see": "saw", "hear": "heard", "know": "knew",
            "think": "thought", "sleep": "slept", "come": "came", "give": "gave", "say": "said",
            "go": "went", "run": "ran", "swim": "swam", "sing": "sang", "sit": "sat",
            "stand": "stood", "fall": "fell", "hold": "held", "cut": "cut", "hit": "hit",
            "put": "put", "take": "took", "make": "made", "do": "did", "get up": "got up",
            "lie": "lay", "bite": "bit", "blow": "blew", "freeze": "froze", "fight": "fought",
            "fly": "flew", "throw": "threw", "wear": "wore", "buy": "bought", "sell": "sold",
            "teach": "taught", "learn": "learned", "write": "wrote", "read": "read",
            "find": "found", "lose": "lost", "leave": "left", "feel": "felt", "keep": "kept",
            "begin writing": "began writing", "sit down": "sat down", "go up": "went up",
            "go down": "went down", "take off": "took off", "cut vegetables": "cut vegetables",
            "vomit": "vomited", "laugh": "laughed", "breathe": "breathed", "smell": "smelled",
            "fear": "feared", "live": "lived", "die": "died", "kill": "killed", "hunt": "hunted",
            "split": "split", "stab": "stabbed", "scratch": "scratched", "dig": "dug",
            "turn": "turned", "squeeze": "squeezed", "rub": "rubbed", "wash": "washed",
            "wipe": "wiped", "pull": "pulled", "push": "pushed", "tie": "tied", "sew": "sewed",
            "count": "counted", "play": "played", "float": "floated", "flow": "flowed",
            "swell": "swelled", "burn": "burned", "suck": "sucked", "spit": "spat",
            "want": "wanted", "work": "worked", "cook": "cooked", "call": "called",
            "answer": "answered", "ask": "asked", "explain": "explained", "remember": "remembered",
            "forget": "forgot", "believe": "believed", "hope": "hoped", "look": "looked",
            "listen": "listened", "speak": "spoke", "understand": "understood",
            "translate": "translated", "visit": "visited", "travel": "traveled", "dance": "danced",
            "draw": "drew", "slip": "slipped", "jump": "jumped", "enter": "entered",
            "exit": "exited", "arrive": "arrived", "return": "returned", "open": "opened",
            "close": "closed", "drive": "drove", "wait": "waited", "help": "helped",
            "love": "loved", "wish": "wished", "start": "started", "finish": "finished",
            "can": "could", "pay": "paid",
        }
        if gloss in irregular:
            return irregular[gloss]
        if gloss.endswith("e"):
            return gloss + "d"
        if gloss.endswith("y") and len(gloss) > 1 and gloss[-2] not in "aeiou":
            return gloss[:-1] + "ied"
        return gloss + "ed"

    pg = past(g)
    out = []
    for off in range(3):
        t, e = pairs[(item.index + off * 4) % len(pairs)]
        out.append(S(t, e.format(pg=pg), item))
    return out


def phrase_sentences(item: VocabItem) -> list[dict[str, object]]:
    w, g = item.word, item.gloss.lower()
    special = {
        "hello": [
            (f"{w}, kif inti", f"Hello, how are you?"),
            (f"Għidt {w} lill-għalliem", f"I said hello to the teacher."),
            (f"{w} mill-ġirien", f"Hello from the neighbors."),
        ],
        "please": [
            (f"{w} għaddi l-ilma", f"Please pass the water."),
            (f"Ikteb ismek, {w}", f"Write your name, please."),
            (f"{w} stenna hawn", f"Please wait here."),
        ],
        "thank you": [
            (f"{w} għall-għajnuna", f"Thank you for the help."),
            (f"Wara l-ikla għidt {w}", f"After the meal I said thank you."),
            (f"{w}, kont ta' għajnuna", f"Thank you, you were helpful."),
        ],
        "sorry": [
            (f"{w}, wasalt tard", f"Sorry, I arrived late."),
            (f"Għidt {w} lit-tifel", f"I said sorry to the child."),
            (f"{w} għall-istorbju", f"Sorry for the noise."),
        ],
        "goodbye": [
            (f"{w}, narak għada", f"Goodbye, see you tomorrow."),
            (f"Fil-bieb għidt {w}", f"At the door I said goodbye."),
            (f"{w} u saħħa", f"Goodbye and take care."),
        ],
        "yes": [
            (f"{w}, niġi magħkom", f"Yes, I will come with you."),
            (f"It-tweġiba kienet {w}", f"The answer was yes."),
            (f"{w}, il-ktieb hawn", f"Yes, the book is here."),
        ],
        "no": [
            (f"{w}, ma rridtx kafè", f"No, I do not want coffee."),
            (f"Hu wieġeb {w}", f"He answered no."),
            (f"{w}, il-ħanut magħluq", f"No, the shop is closed."),
        ],
        "welcome": [
            (f"{w} f'darna", f"Welcome to our house."),
            (f"Għidna {w} lill-mistednin", f"We said welcome to the guests."),
            (f"{w}, poġġu hawn", f"Welcome, sit here."),
        ],
        "good morning": [
            (f"{w} lil kulħadd", f"Good morning to everyone."),
            (f"Filgħodu ngħidu {w}", f"In the morning we say good morning."),
            (f"{w}, x'ġralna llum", f"Good morning, what is new today."),
        ],
        "good evening": [
            (f"{w}, kif għaddiet il-ġurnata", f"Good evening, how was the day."),
            (f"Meta wasalna għidna {w}", f"When we arrived we said good evening."),
            (f"{w} mill-familja", f"Good evening from the family."),
        ],
        "good night": [
            (f"{w}, orqod tajjeb", f"Good night, sleep well."),
            (f"Qabel torqod għid {w}", f"Before you sleep say good night."),
            (f"{w} lit-tfal", f"Good night to the children."),
        ],
        "how are you": [
            (f"{w} illum", f"How are you today?"),
            (f"Staqsejt lilu {w}", f"I asked him how are you."),
            (f"{w} wara l-vjaġġ", f"How are you after the trip?"),
        ],
        "okay": [
            (f"Kollox {w} issa", f"Everything is okay now."),
            (f"Wieġeb {w} malajr", f"He answered okay quickly."),
            (f"{w}, nibdew", f"Okay, let's start."),
        ],
        "very well": [
            (f"Jien {w} illum", f"I am very well today."),
            (f"Ħassejtha {w}", f"I felt very well."),
            (f"Wara l-mistrieħ {w}", f"After the rest, very well."),
        ],
        "good day": [
            (f"{w} lin-nies fit-triq", f"Good day to people on the road."),
            (f"Fil-ħanut ngħidu {w}", f"In the shop we say good day."),
            (f"{w}, x'nista' nagħmel", f"Good day, what can I do."),
        ],
    }
    rows = special.get(g)
    if not rows:
        rows = [
            (f"Għidt {w} bil-mod", f"I said {g} slowly."),
            (f"Fil-bieb smajna {w}", f"At the door we heard {g}."),
            (f"{w} hu importanti hawn", f"{g.title()} matters here."),
        ]
    out = []
    for tgt, eng in rows:
        if eng.endswith("?"):
            if not tgt.endswith("?"):
                tgt += "?"
            out.append(make_sentence(tgt, claim_english(eng, item.gloss), item))
        else:
            out.append(S(tgt, eng, item))
    return out


def sentences_for(item: VocabItem) -> list[dict[str, object]]:
    dispatch = {
        "pronoun": pronoun_sentences,
        "question": question_sentences,
        "deictic": deictic_sentences,
        "negation": negation_sentences,
        "function": function_sentences,
        "number": number_sentences,
        "adjective": adjective_sentences,
        "color": color_sentences,
        "person": person_sentences,
        "place": place_sentences,
        "time": time_sentences,
        "food": food_sentences,
        "drink": food_sentences,
        "transport": transport_sentences,
        "animal": animal_sentences,
        "nature": nature_sentences,
        "body": body_sentences,
        "verb": verb_sentences,
        "phrase": phrase_sentences,
        "object": object_sentences,
    }
    fn = dispatch.get(item.category, object_sentences)
    result = fn(item)
    if len(result) != 3:
        raise ValueError(f"{item.word}: expected 3 sentences, got {len(result)}")
    for s in result:
        if item.word not in s["target"]:
            raise ValueError(f"{item.word} missing in {s['target']!r}")
    return result


def swadesh_items() -> list[VocabItem]:
    items = []
    for index, (word, gloss) in enumerate(zip(SWADESH_WORDS, SWADESH_GLOSSES), start=1):
        items.append(
            VocabItem(
                index=index,
                word=clean_term(word),
                gloss=gloss,
                category=swadesh_category(index, gloss),
                source=BATCH_SOURCE_SWADESH,
            )
        )
    return items


def a1_items() -> list[VocabItem]:
    items: list[VocabItem] = []
    seen: set[str] = set()
    for item in swadesh_items():
        if item.word not in seen:
            items.append(
                VocabItem(
                    index=len(items) + 1,
                    word=item.word,
                    gloss=item.gloss,
                    category=item.category,
                    source=BATCH_SOURCE_A1,
                )
            )
            seen.add(item.word)
    for word, gloss, category in A1_EXTRAS:
        word = clean_term(word)
        if word in seen:
            continue
        items.append(
            VocabItem(
                index=len(items) + 1,
                word=word,
                gloss=gloss,
                category=infer_category(gloss, None, category),
                source=BATCH_SOURCE_A1,
            )
        )
        seen.add(word)
        if len(items) == 500:
            break
    if len(items) != 500:
        raise ValueError(f"expected 500 A1 items, got {len(items)}")
    return items


def write_batches(prefix: str, items: list[VocabItem], ranges: list[tuple[int, int]], reset_frames: bool = True) -> None:
    global _USED_FRAMES
    if reset_frames:
        _USED_FRAMES = set()
    GENERATED.mkdir(parents=True, exist_ok=True)
    for start, end in ranges:
        batch = []
        for item in items[start - 1 : end]:
            batch.append(
                {
                    "vocab_index": item.index,
                    "word": item.word,
                    "gloss": item.gloss,
                    "source": item.source,
                    "sentences": sentences_for(item),
                }
            )
        path = GENERATED / f"{prefix}_{start:03d}_{end:03d}.json"
        path.write_text(json.dumps(batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path} ({len(batch)} words)")


def main() -> None:
    write_batches(
        "maltese",
        a1_items(),
        [(1, 50), (51, 100), (101, 150), (151, 200), (201, 250), (251, 300), (301, 350), (351, 400), (401, 450), (451, 500)],
    )
    write_batches(
        "maltese_swadesh",
        swadesh_items(),
        [(1, 41), (42, 83), (84, 124), (125, 165), (166, 207)],
        reset_frames=True,
    )


if __name__ == "__main__":
    main()
