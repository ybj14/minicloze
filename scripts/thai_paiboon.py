#!/usr/bin/env python3
"""Small offline Thai-to-Paiboon transliterator for the local A1 corpus.

The implementation follows the Paiboon-style conventions used by Wiktionary:
aspirated consonants use h, Thai-specific unaspirated stops use g/dt/bp, long
vowels are doubled, and tone is marked on the first vowel of each syllable.
It is intentionally scoped to learner-friendly corpus text and includes a
curated override table for common A1 words whose spelling is not transparent.
"""

from __future__ import annotations

import re
import unicodedata


THAI_RE = re.compile(r"[\u0e00-\u0e7f]")
CONSONANTS = set("กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ")
PREPOSED = set("เแโใไ")
TONE_MARKS = {"่": 1, "้": 2, "๊": 3, "๋": 4}
LOW_CLASS = set("คฅฆงชซฌญฑฒณทธนพฟภมยรลวฬฮ")
MID_CLASS = set("กจฎฏดตบปอ")
HIGH_CLASS = set("ขฃฉฐถผฝศษสห")
SONORANTS = set("งญณนมยรลวฬ")
CLUSTER_SECONDS = set("รลว")
CLUSTER_FIRSTS = set("กขคตปผพฟบ")
DEAD_FINALS = set("กขฃคฅฆจฉชซฌฎฏฐฑฒดตถทธบปผพฟภศษส")
NASAL_FINALS = set("งญณนม")
GLIDE_FINALS = set("ยว")

INITIALS = {
    "ก": "g",
    "ข": "k",
    "ฃ": "k",
    "ค": "k",
    "ฅ": "k",
    "ฆ": "k",
    "ง": "ng",
    "จ": "j",
    "ฉ": "ch",
    "ช": "ch",
    "ซ": "s",
    "ฌ": "ch",
    "ญ": "y",
    "ฎ": "d",
    "ฏ": "dt",
    "ฐ": "t",
    "ฑ": "t",
    "ฒ": "t",
    "ณ": "n",
    "ด": "d",
    "ต": "dt",
    "ถ": "t",
    "ท": "t",
    "ธ": "t",
    "น": "n",
    "บ": "b",
    "ป": "bp",
    "ผ": "p",
    "ฝ": "f",
    "พ": "p",
    "ฟ": "f",
    "ภ": "p",
    "ม": "m",
    "ย": "y",
    "ร": "r",
    "ล": "l",
    "ว": "w",
    "ศ": "s",
    "ษ": "s",
    "ส": "s",
    "ห": "h",
    "ฬ": "l",
    "อ": "",
    "ฮ": "h",
}

FINALS = {
    "ก": "k",
    "ข": "k",
    "ฃ": "k",
    "ค": "k",
    "ฅ": "k",
    "ฆ": "k",
    "ง": "ng",
    "จ": "t",
    "ฉ": "t",
    "ช": "t",
    "ซ": "t",
    "ฌ": "t",
    "ญ": "n",
    "ฎ": "t",
    "ฏ": "t",
    "ฐ": "t",
    "ฑ": "t",
    "ฒ": "t",
    "ณ": "n",
    "ด": "t",
    "ต": "t",
    "ถ": "t",
    "ท": "t",
    "ธ": "t",
    "น": "n",
    "บ": "p",
    "ป": "p",
    "ผ": "p",
    "ฝ": "p",
    "พ": "p",
    "ฟ": "p",
    "ภ": "p",
    "ม": "m",
    "ย": "y",
    "ร": "n",
    "ล": "n",
    "ว": "w",
    "ศ": "t",
    "ษ": "t",
    "ส": "t",
    "ห": "",
    "ฬ": "n",
    "อ": "",
    "ฮ": "",
}

TONE_COMBINING = {
    "low": "\u0300",
    "falling": "\u0302",
    "high": "\u0301",
    "rising": "\u030c",
}
ROMAN_VOWELS = set("aeiouɛɔəʉ")


OVERRIDES = {
    "ก็": "gɔ̂",
    "กรุงเทพ": "grung-têep",
    "กรุณา": "gà-rú-naa",
    "กระจก": "grà-jòk",
    "กระดาน": "grà-daan",
    "กระดาษ": "grà-dàat",
    "กระหาย": "grà-hǎai",
    "กระเป๋า": "grà-bpǎo",
    "กุญแจ": "gun-jae",
    "ก๋วยเตี๋ยว": "gǔuay-dtǐao",
    "กิโลเมตร": "gì-loo-mét",
    "กีฬา": "gii-laa",
    "ขอบคุณ": "kɔ̀ɔp-kun",
    "ของคุณ": "kɔ̌ɔng-kun",
    "ขอโทษ": "kɔ̌ɔ-tôot",
    "ขอบใจ": "kɔ̀ɔp-jai",
    "ขนม": "kà-nǒm",
    "ขนมปัง": "kà-nǒm-bpang",
    "คนขับ": "kon-kàp",
    "ครอบครัว": "krɔ̂ɔp-krua",
    "ครับ": "kráp",
    "ครึ่ง": "krʉ̀ng",
    "ครู": "kruu",
    "ความ": "kwaam",
    "ความรัก": "kwaam-rák",
    "ความสุข": "kwaam-sùk",
    "คอมพิวเตอร์": "kɔm-piu-dtə̂ə",
    "คำ": "kam",
    "คำตอบ": "kam-dtɔ̀ɔp",
    "คำถาม": "kam-tǎam",
    "คำศัพท์": "kam-sàp",
    "คุณ": "kun",
    "ค่ะ": "kâ",
    "ค่า": "kâa",
    "คน": "kon",
    "จดหมาย": "jòt-mǎai",
    "จักรยาน": "jàk-grà-yaan",
    "จังหวัด": "jang-wàt",
    "จันทร์": "jan",
    "จริง": "jing",
    "ฉัน": "chǎn",
    "ใช่": "châi",
    "ชาวนา": "chaao-naa",
    "ช้าๆ": "cháa-cháa",
    "ซ้าย": "sáai",
    "ดอกไม้": "dɔ̀ɔk-máai",
    "ดวงตา": "duang-dtaa",
    "ดีใจ": "dii-jai",
    "ตลาด": "dtà-làat",
    "ตลก": "dtà-lòk",
    "ตำรวจ": "dtam-rùuat",
    "ตอน": "dtɔɔn",
    "ตอนนี้": "dtɔɔn-níi",
    "ตะวัน": "dtà-wan",
    "ตัวเลข": "dtua-lêek",
    "ข้อสอบ": "kɔ̂ɔ-sɔ̀ɔp",
    "ถนน": "tà-nǒn",
    "ถ่าย": "tàai",
    "ทำงาน": "tam-ngaan",
    "ทำการบ้าน": "tam-gaan-bâan",
    "ทำอาหาร": "tam-aa-hǎan",
    "ทำให้": "tam-hâi",
    "ทะเล": "tá-lee",
    "ทันที": "tan-tii",
    "ทราย": "saai",
    "ทุ่ง": "tûng",
    "ที่": "tîi",
    "ธนาคาร": "tá-naa-kaan",
    "นิดหน่อย": "nít-nɔ̀i",
    "นี่": "nîi",
    "นี้": "níi",
    "น้ำ": "náam",
    "น้ำเงิน": "nám-ngən",
    "น่าเบื่อ": "nâa-bʉ̀a",
    "นักเรียน": "nák-riian",
    "นักร้อง": "nák-rɔ́ɔng",
    "นักกีฬา": "nák-gii-laa",
    "นักท่องเที่ยว": "nák-tɔ̂ng-tîao",
    "นักท่องเที่ยว": "nák-tɔ̂ng-tîao",
    "น้อง": "nɔ́ɔng",
    "บ่าย": "bàai",
    "บาง": "baang",
    "บางที": "baang-tii",
    "บน": "bon",
    "บนฟ้า": "bon-fáa",
    "ปัญหา": "bpan-hǎa",
    "ประเทศไทย": "bprà-têet-tai",
    "ประโยค": "bprà-yòok",
    "ประชุม": "bprà-chum",
    "ประมาณ": "bprà-maan",
    "ปลอบ": "bplɔ̀ɔp",
    "ปลูก": "bplùuk",
    "ผ้าเช็ดตัว": "pâa-chét-dtua",
    "ผ้าห่ม": "pâa-hòm",
    "ผ่าน": "pàan",
    "พนักงาน": "pá-nák-ngaan",
    "พรุ่งนี้": "prûng-níi",
    "พร้อม": "prɔ́ɔm",
    "พี่ชาย": "pîi-chaai",
    "พี่": "pîi",
    "ฟัง": "fang",
    "ฟุตบอล": "fút-bɔɔn",
    "ผู้ชาย": "pûu-chaai",
    "ภาษาไทย": "paa-sǎa-tai",
    "ภาษาอังกฤษ": "paa-sǎa-ang-grìt",
    "ภูเขา": "puu-kǎo",
    "มะนาว": "má-naao",
    "มะม่วง": "má-mûang",
    "มะเขือเทศ": "má-kʉ̌a-têet",
    "มะพร้าว": "má-práao",
    "มะละกอ": "má-lá-gɔɔ",
    "มาก": "mâak",
    "มา": "maa",
    "มืด": "mʉ̂ʉt",
    "เมื่อ": "mʉ̂a",
    "เมืองไทย": "mʉang-tai",
    "แม่": "mâae",
    "แม่น้ำ": "mâae-náam",
    "ไม่ได้": "mâi-dâi",
    "ไม่": "mâi",
    "ไหม": "mǎi",
    "ใหม่": "mài",
    "ใหญ่": "yài",
    "รอรถเมล์": "rɔɔ-rót-mee",
    "รถเมล์": "rót-mee",
    "รถไฟ": "rót-fai",
    "รถไฟฟ้า": "rót-fai-fáa",
    "ร่างกาย": "râang-gaai",
    "ร้านอาหาร": "ráan-aa-hǎan",
    "ละคร": "lá-kɔɔn",
    "เรียก": "rîiak",
    "โรงเรียน": "roong-riian",
    "โรงพยาบาล": "roong-pá-yaa-baan",
    "โรงแรม": "roong-raem",
    "วันจันทร์": "wan-jan",
    "วันเสาร์": "wan-sǎo",
    "วันอาทิตย์": "wan-aa-tít",
    "ว่ายน้ำ": "wâai-náam",
    "สนุก": "sà-nùk",
    "สนามบิน": "sà-nǎam-bin",
    "สถานี": "sà-tǎa-nii",
    "สวน": "sǔan",
    "สวย": "sǔay",
    "สบาย": "sà-baai",
    "สวัสดี": "sà-wàt-dii",
    "สะอาด": "sà-àat",
    "สะพาน": "sà-paan",
    "สัตว์": "sàt",
    "สั้นๆ": "sân-sân",
    "สำหรับ": "sǎm-ràp",
    "สำคัญ": "sǎm-kan",
    "สว่าง": "sà-wàang",
    "สีเขียว": "sǐi-kǐao",
    "สีขาว": "sǐi-kǎao",
    "สีดำ": "sǐi-dam",
    "สีแดง": "sǐi-daeng",
    "สีเหลือง": "sǐi-lʉ̌ang",
    "สีน้ำตาล": "sǐi-nám-dtaan",
    "สีน้ำเงิน": "sǐi-nám-ngən",
    "สุดท้าย": "sùt-táai",
    "สุภาพ": "sù-pâap",
    "หนัง": "nǎng",
    "หนังสือ": "nǎng-sʉ̌ʉ",
    "หนังสือพิมพ์": "nǎng-sʉ̌ʉ-pim",
    "หน้า": "nâa",
    "หน้าต่าง": "nâa-dtàang",
    "หนึ่ง": "nʉ̀ng",
    "หมอน": "mɔ̌ɔn",
    "หมา": "mǎa",
    "หมด": "mòt",
    "หมู่บ้าน": "mùu-bâan",
    "หลังจาก": "lǎng-jàak",
    "ห้อง": "hɔ̂ɔng",
    "ห้องเรียน": "hɔ̂ɔng-riian",
    "ห้องน้ำ": "hɔ̂ɔng-náam",
    "อยาก": "yàak",
    "อยู่": "yùu",
    "อย่าง": "yàang",
    "อย่างไร": "yàang-rai",
    "อย่างระวัง": "yàang-rá-wang",
    "อย่างสุภาพ": "yàang-sù-pâap",
    "อย่างอ่อนโยน": "yàang-ɔ̀ɔn-yoon",
    "อาหาร": "aa-hǎan",
    "อากาศ": "aa-gàat",
    "อังกฤษ": "ang-grìt",
    "อาทิตย์": "aa-tít",
    "อินเทอร์เน็ต": "in-təə-nét",
    "อ่อนโยน": "ɔ̀ɔn-yoon",
    "อาคาร": "aa-kaan",
    "เก้า": "gâao",
    "เขียน": "kǐian",
    "เข้าใจ": "kâo-jai",
    "เข้า": "kâo",
    "เครื่องบิน": "krʉ̂ang-bin",
    "เครื่อง": "krʉ̂ang",
    "เงิน": "ngən",
    "เกษตรกร": "gà-sèet-dtrà-gɔɔn",
    "เจ็บ": "jèp",
    "เจอ": "jəə",
    "เฉยๆ": "chə̌əi-chə̌əi",
    "เดินทาง": "dəən-taang",
    "เด็ก": "dèk",
    "เตรียม": "dtriiam",
    "เพดาน": "pee-daan",
    "เท่านั้น": "tâo-nán",
    "เที่ยง": "tîiang",
    "เท้า": "táao",
    "เป็ด": "bpèt",
    "เป็น": "bpen",
    "เปิด": "bpə̀ət",
    "เพราะ": "prɔ́",
    "เพื่อน": "pʉ̂an",
    "เพื่อนบ้าน": "pʉ̂an-bâan",
    "เพื่อ": "pʉ̂a",
    "เมือง": "mʉang",
    "เมนู": "mee-nuu",
    "เมื่อวาน": "mʉ̂a-waan",
    "เลิกเรียน": "lə̂ək-riian",
    "เส้นผม": "sên-pǒm",
    "เสียใจ": "sǐia-jai",
    "เสื้อ": "sʉ̂a",
    "เห็น": "hěn",
    "แชมพู": "chaem-puu",
    "แก้ว": "gâaeo",
    "แก้": "gâae",
    "แข็งแรง": "kǎeng-raeng",
    "แขวน": "kwǎaen",
    "แปล": "bplaae",
    "แปรง": "bpraaeng",
    "แมว": "maaeo",
    "แยก": "yâaek",
    "แล้ว": "láaeo",
    "แห้ง": "hâaeng",
    "โต๊ะ": "dtó",
    "โทรศัพท์": "too-rá-sàp",
    "โทษ": "tôot",
    "โรง": "roong",
    "ใกล้": "glâi",
    "ใจดี": "jai-dii",
    "ใต้": "dtâi",
    "ใน": "nai",
    "ใบเสร็จ": "bai-sèt",
    "ให้": "hâi",
    "ไกล": "glai",
    "ไกลๆ": "glai-glai",
    "ได้": "dâi",
    "ไฟแดง": "fai-daeng",
    "ไป": "bpai",
    "ไปก่อน": "bpai-gɔ̀ɔn",
}


def is_thai(text: str) -> bool:
    return bool(THAI_RE.search(text))


def romanize(text: str) -> str:
    if not text:
        return ""
    parts: list[str] = []
    for chunk in re.split(r"(\s+)", text):
        if not chunk:
            continue
        if chunk.isspace():
            parts.append(chunk)
        elif is_thai(chunk):
            parts.append(romanize_word(chunk))
        else:
            parts.append(chunk)
    return "".join(parts)


def romanize_word(word: str) -> str:
    raw_word = word.strip()
    if not raw_word:
        return ""
    if raw_word in OVERRIDES:
        return OVERRIDES[raw_word]
    word = clean_silent_marks(raw_word)
    if not word:
        return ""
    if word.endswith("ๆ") and len(word) > 1:
        base = romanize_word(word[:-1])
        return f"{base}-{base}" if base else ""
    if word in OVERRIDES:
        return OVERRIDES[word]

    syllables = split_syllables(word)
    rendered = [romanize_syllable(syllable) for syllable in syllables]
    rendered = [item for item in rendered if item]
    if not rendered:
        return word
    return "-".join(rendered)


def clean_silent_marks(word: str) -> str:
    word = re.sub(r"[ก-ฮ]์", "", word)
    return word.replace("์", "")


def split_syllables(word: str) -> list[str]:
    if word in OVERRIDES:
        return [word]
    syllables: list[str] = []
    index = 0
    while index < len(word):
        next_index = next_syllable_end(word, index)
        if next_index <= index:
            next_index = index + 1
        syllables.append(word[index:next_index])
        index = next_index
    return syllables


def next_syllable_end(word: str, start: int) -> int:
    index = start
    if index < len(word) and word[index] in PREPOSED:
        index += 1

    consonant_positions = [
        pos for pos in range(index, len(word)) if word[pos] in CONSONANTS
    ]
    if not consonant_positions:
        return len(word)

    onset_start = consonant_positions[0]
    onset_end = onset_start + 1
    if onset_end < len(word) and word[onset_end] in CONSONANTS:
        first = word[onset_start]
        second = word[onset_end]
        if (first in {"ห", "อ"} and second in SONORANTS) or (
            first in CLUSTER_FIRSTS and second in CLUSTER_SECONDS
        ):
            onset_end += 1

    # A leading unclustered consonant before another consonant is usually an
    # implicit short-a syllable in this A1 corpus, e.g. ตลาด, ขนม, สนุก.
    if (
        start == onset_start
        and onset_end == onset_start + 1
        and onset_end < len(word)
        and word[onset_end] in CONSONANTS
        and word[onset_end] not in {"ร", "ล", "ว", "อ"}
        and len(word) - onset_end > 1
    ):
        return onset_end

    end = onset_end
    saw_final = False
    while end < len(word):
        char = word[end]
        if char in PREPOSED and end > start:
            break
        if char == "อ" and end >= onset_end:
            end += 1
            continue
        if (
            char == "ว"
            and end + 1 < len(word)
            and word[end + 1] in CONSONANTS
        ):
            end += 1
            continue
        if (
            char == "ย"
            and "ี" in word[start:end]
            and end + 1 < len(word)
            and word[end + 1] in CONSONANTS
        ):
            end += 1
            continue
        if char in CONSONANTS and end >= onset_end:
            if saw_final:
                break
            saw_final = True
            end += 1
            if end < len(word) and word[end] in {"ิ", "ี", "ึ", "ื", "ุ", "ู", "ั", "็"}:
                # The consonant likely starts the next syllable.
                end -= 1
                break
            continue
        end += 1
    return end


def romanize_syllable(syllable: str) -> str:
    if syllable in OVERRIDES:
        return OVERRIDES[syllable]
    if not syllable:
        return ""

    tone_mark = next((TONE_MARKS[ch] for ch in syllable if ch in TONE_MARKS), 0)
    clean = "".join(ch for ch in syllable if ch not in TONE_MARKS)
    preposed = "".join(ch for ch in clean if ch in PREPOSED)
    core = "".join(ch for ch in clean if ch not in PREPOSED)
    consonants = [ch for ch in core if ch in CONSONANTS]
    if not consonants:
        return clean

    onset, effective_class, consumed = parse_onset(core, consonants)
    remainder = core[consumed:]
    final = final_consonant(remainder)
    vowel = vowel_value(preposed, remainder, final)
    initial = "".join(INITIALS.get(ch, "") for ch in onset if ch not in {"ห", "อ"} or len(onset) == 1)
    if onset and onset[0] == "ห" and len(onset) > 1:
        initial = INITIALS.get(onset[1], "")
    if onset and onset[0] == "อ" and len(onset) > 1:
        initial = INITIALS.get(onset[1], "")
    ending = FINALS.get(final, "") if final else ""
    roman = f"{initial}{vowel}{ending}"
    tone = tone_name(effective_class, tone_mark, final, vowel_is_short(preposed, remainder, final))
    return apply_tone(roman, tone)


def parse_onset(core: str, consonants: list[str]) -> tuple[str, str, int]:
    first_index = next((i for i, ch in enumerate(core) if ch in CONSONANTS), 0)
    first = core[first_index]
    onset = first
    consumed = first_index + 1
    effective = consonant_class(first)
    if consumed < len(core) and core[consumed] in CONSONANTS:
        second = core[consumed]
        if first in {"ห", "อ"} and second in SONORANTS:
            onset += second
            consumed += 1
            effective = "high" if first == "ห" else "mid"
        elif first in CLUSTER_FIRSTS and second in CLUSTER_SECONDS:
            onset += second
            consumed += 1
            effective = consonant_class(first)
    return onset, effective, consumed


def consonant_class(char: str) -> str:
    if char in HIGH_CLASS:
        return "high"
    if char in MID_CLASS:
        return "mid"
    return "low"


def final_consonant(remainder: str) -> str | None:
    consonants = [ch for ch in remainder if ch in CONSONANTS]
    if not consonants:
        return None
    if len(consonants) == 1:
        return consonants[0]
    return consonants[-1]


def vowel_value(preposed: str, remainder: str, final: str | None) -> str:
    has = lambda text: text in remainder
    if "ำ" in remainder:
        return "am"
    if "รร" in remainder:
        return "an" if final else "an"
    if preposed == "ไ" or preposed == "ใ":
        return "ai"
    if "ัว" in remainder or ("ว" in remainder and not preposed and final != "ว"):
        return "ua"
    if preposed == "เ" and "ีย" in remainder:
        return "iia"
    if preposed == "เ" and "ือ" in remainder:
        return "ʉa"
    if preposed == "เ" and "า" in remainder:
        return "ao"
    if preposed == "เ" and "อะ" in remainder:
        return "ə"
    if preposed == "เ" and "อ" in remainder:
        return "əə"
    if preposed == "เ":
        return "e" if "็" in remainder or "ะ" in remainder else "ee"
    if preposed == "แ":
        return "ɛ" if "็" in remainder or "ะ" in remainder else "ɛɛ"
    if preposed == "โ":
        return "o" if "ะ" in remainder else "oo"
    if has("ึ"):
        return "ʉ"
    if has("ื"):
        return "ʉʉ"
    if has("ิ"):
        return "i"
    if has("ี"):
        return "ii"
    if has("ุ"):
        return "u"
    if has("ู"):
        return "uu"
    if has("ั"):
        return "a"
    if has("า"):
        return "aa"
    if has("อ"):
        return "ɔɔ"
    if has("ะ"):
        return "a"
    if final:
        return "o"
    return "a"


def vowel_is_short(preposed: str, remainder: str, final: str | None) -> bool:
    if any(mark in remainder for mark in ["ะ", "ั", "ิ", "ึ", "ุ", "็"]):
        return True
    if preposed in {"ไ", "ใ"}:
        return False
    if not preposed and final and "า" not in remainder and "ี" not in remainder and "ู" not in remainder and "ื" not in remainder and "อ" not in remainder:
        return True
    return False


def tone_name(consonant_class_name: str, mark: int, final: str | None, is_short: bool) -> str:
    dead = final in DEAD_FINALS or (final is None and is_short)
    if consonant_class_name == "mid":
        if mark == 1:
            return "low"
        if mark == 2:
            return "falling"
        if mark == 3:
            return "high"
        if mark == 4:
            return "rising"
        return "low" if dead else "mid"
    if consonant_class_name == "high":
        if mark == 1:
            return "low"
        if mark == 2:
            return "falling"
        return "low" if dead else "rising"

    if mark == 1:
        return "falling"
    if mark == 2:
        return "high"
    if dead:
        return "high" if is_short else "falling"
    return "mid"


def apply_tone(roman: str, tone: str) -> str:
    mark = TONE_COMBINING.get(tone)
    if not mark:
        return roman
    chars = list(roman)
    for index, char in enumerate(chars):
        if char in ROMAN_VOWELS:
            chars[index] = char + mark
            return unicodedata.normalize("NFC", "".join(chars))
    return roman


if __name__ == "__main__":
    import sys

    for item in sys.argv[1:]:
        print(f"{item}\t{romanize(item)}")
