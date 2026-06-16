#!/usr/bin/env python3
"""Maintain the local Tajik A1 minicloze seed data.

The vocabulary is a compact, Codex-curated beginner seed list. Final sentence
batches are authored learning material; this script does not overwrite them
unless --write-template-batches is passed deliberately for scaffolding.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORPORA = ROOT / "minicloze-lib" / "corpora"
GENERATED = CORPORA / "generated"
SOURCE = "Codex curated Tajik A1 seed list"
ID_START = -300000
EXPECTED_COUNT = 500
BATCH_SIZE = 125


@dataclass(frozen=True)
class Entry:
    word: str
    gloss: str
    pos: str


RAW_ENTRIES = """
як|one|num
ду|two|num
се|three|num
чор|four|num
панҷ|five|num
шаш|six|num
ҳафт|seven|num
ҳашт|eight|num
нӯҳ|nine|num
даҳ|ten|num
ёздаҳ|eleven|num
дувоздаҳ|twelve|num
сездаҳ|thirteen|num
чордаҳ|fourteen|num
понздаҳ|fifteen|num
шонздаҳ|sixteen|num
ҳабдаҳ|seventeen|num
ҳаждаҳ|eighteen|num
нуздаҳ|nineteen|num
бист|twenty|num
сӣ|thirty|num
чил|forty|num
панҷоҳ|fifty|num
шаст|sixty|num
ҳафтод|seventy|num
ҳаштод|eighty|num
навад|ninety|num
сад|one hundred|num
ҳазор|one thousand|num
якум|first|ord
дуюм|second|ord
сеюм|third|ord
чорум|fourth|ord
панҷум|fifth|ord
шашум|sixth|ord
ҳафтум|seventh|ord
ҳаштум|eighth|ord
нӯҳум|ninth|ord
даҳум|tenth|ord
одам|person|noun
мард|man|noun
зан|woman|noun
кӯдак|child|noun
писар|boy|noun
духтар|girl|noun
падар|father|noun
модар|mother|noun
бародар|brother|noun
хоҳар|sister|noun
бобо|grandfather|noun
бибӣ|grandmother|noun
амак|uncle|noun
хола|aunt|noun
писарак|little boy|noun
духтарак|little girl|noun
дӯст|friend|noun
рафиқ|friend|noun
ҳамсоя|neighbor|noun
меҳмон|guest|noun
оила|family|noun
хеш|relative|noun
ном|name|noun
насаб|surname|noun
омӯзгор|teacher|noun
муаллим|teacher|noun
хонанда|pupil|noun
донишҷӯ|student|noun
табиб|doctor|noun
ҳамшира|nurse|noun
коргар|worker|noun
деҳқон|farmer|noun
ронанда|driver|noun
фурӯшанда|seller|noun
ошпаз|cook|noun
нозир|inspector|noun
муҳандис|engineer|noun
саркор|manager|noun
корманд|employee|noun
мусофир|passenger|noun
сайёҳ|tourist|noun
шогирд|apprentice|noun
устод|master; teacher|noun
ҳамкор|colleague|noun
навозанда|musician|noun
варзишгар|athlete|noun
ҳунарманд|artist|noun
полис|police officer|noun
пизишк|physician|noun
дандонпизишк|dentist|noun
шоир|poet|noun
нависанда|writer|noun
тарҷумон|translator|noun
роҳбалад|guide|noun
шахс|person|noun
ҷавон|youth|noun
пир|elder|noun
хона|house|noun
ҳуҷра|room|noun
ошхона|kitchen|noun
ҳаммом|bathroom|noun
дар|door|noun
тиреза|window|noun
девор|wall|noun
фарш|floor|noun
шифт|ceiling|noun
миз|table|noun
курсӣ|chair|noun
кат|bed|noun
ҷевон|cupboard|noun
раф|shelf|noun
чароғ|lamp|noun
коса|bowl|noun
табақ|plate|noun
пиёла|cup|noun
қошуқ|spoon|noun
чангак|fork|noun
корд|knife|noun
дег|pot|noun
чойник|teapot|noun
яхдон|refrigerator|noun
боғ|garden|noun
ҳавлӣ|yard|noun
кӯча|street|noun
роҳ|road|noun
гузар|passage|noun
майдон|square; field|noun
кӯпрук|bridge|noun
мактаб|school|noun
донишгоҳ|university|noun
беморхона|hospital|noun
дорухона|pharmacy|noun
бозор|market|noun
мағоза|shop|noun
идора|office|noun
корхона|factory|noun
истгоҳ|station|noun
фурудгоҳ|airport|noun
меҳмонхона|hotel|noun
тарабхона|restaurant|noun
қаҳвахона|cafe|noun
парк|park|noun
осорхона|museum|noun
театр|theater|noun
китобхона|library|noun
бино|building|noun
манзил|dwelling|noun
деҳа|village|noun
шаҳр|city|noun
кишвар|country|noun
пойтахт|capital city|noun
маҳалла|neighborhood|noun
ноҳия|district|noun
вилоят|region|noun
харита|map|noun
ҷазира|island|noun
соҳил|shore|noun
кӯҳистон|mountains|noun
водӣ|valley|noun
китоб|book|noun
дафтар|notebook|noun
қалам|pencil; pen|noun
ручка|pen|noun
коғаз|paper|noun
нома|letter|noun
мактуб|letter|noun
телефон|phone|noun
компютер|computer|noun
экран|screen|noun
клавиатура|keyboard|noun
калид|key|noun
қулф|lock|noun
сумка|bag|noun
халта|sack|noun
ҷузвдон|backpack|noun
соат|clock; watch|noun
айнак|glasses|noun
расм|picture|noun
радио|radio|noun
телевизор|television|noun
камера|camera|noun
сурат|photo|noun
туҳфа|gift|noun
чатр|umbrella|noun
бозича|toy|noun
тӯб|ball|noun
либос|clothes|noun
курта|shirt|noun
шим|pants|noun
доман|skirt|noun
пойафзол|shoes|noun
кулоҳ|hat|noun
ҷӯроб|sock|noun
дастпӯшак|glove|noun
рӯймол|scarf|noun
дастмол|towel|noun
камарбанд|belt|noun
ангуштарин|ring|noun
собун|soap|noun
шампун|shampoo|noun
оина|mirror|noun
шона|comb|noun
хамира|paste|noun
чӯтка|brush|noun
чипта|ticket|noun
шиноснома|passport|noun
ҳамён|wallet|noun
пул|money|noun
нарх|price|noun
ҳисоб|bill; account|noun
нон|bread|noun
об|water|noun
чой|tea|noun
қаҳва|coffee|noun
шир|milk|noun
шакар|sugar|noun
намак|salt|noun
равған|oil; butter|noun
биринҷ|rice|noun
гӯшт|meat|noun
моҳӣ|fish|noun
мурғ|chicken|noun
тухм|egg|noun
панир|cheese|noun
мева|fruit|noun
себ|apple|noun
нок|pear|noun
банан|banana|noun
афлесун|orange|noun
лимӯ|lemon|noun
ангур|grapes|noun
олу|plum|noun
зардолу|apricot|noun
шафтолу|peach|noun
гелос|cherry|noun
анор|pomegranate|noun
харбуза|melon|noun
тарбуз|watermelon|noun
сабзӣ|carrot|noun
картошка|potato|noun
пиёз|onion|noun
помидор|tomato|noun
бодиринг|cucumber|noun
карам|cabbage|noun
қаламфур|pepper|noun
сир|garlic|noun
лубиё|beans|noun
нахӯд|chickpea|noun
ҷуворимакка|corn|noun
салат|salad|noun
шӯрбо|soup|noun
ош|pilaf|noun
хӯрок|food|noun
таом|dish|noun
наҳорӣ|breakfast|noun
нисфирӯзӣ|lunch|noun
шом|dinner; evening|noun
ширинӣ|sweet|noun
кулча|cookie|noun
асал|honey|noun
мураббо|jam|noun
йогурт|yogurt|noun
шарбат|juice|noun
нӯшокӣ|drink|noun
пица|pizza|noun
макарон|pasta|noun
сэндвич|sandwich|noun
қанд|candy; sugar|noun
яхмос|ice cream|noun
чормағз|nut|noun
бодом|almond|noun
офтоб|sun|noun
моҳ|moon; month|noun
ситора|star|noun
осмон|sky|noun
абр|cloud|noun
борон|rain|noun
барф|snow|noun
шамол|wind|noun
ҳаво|air; weather|noun
замин|earth; ground|noun
кӯҳ|mountain|noun
дарё|river|noun
баҳр|sea|noun
кӯл|lake|noun
ҷангал|forest|noun
дарахт|tree|noun
барг|leaf|noun
гул|flower|noun
алаф|grass|noun
санг|stone|noun
хок|soil|noun
рег|sand|noun
оташ|fire|noun
дуд|smoke|noun
нур|light|noun
соя|shadow|noun
баҳор|spring|noun
тобистон|summer|noun
тирамоҳ|autumn|noun
зимистон|winter|noun
рӯз|day|noun
шаб|night|noun
субҳ|morning|noun
бегоҳ|evening|noun
вақт|time|noun
дақиқа|minute|noun
лаҳза|moment|noun
ҳафта|week|noun
сол|year|noun
имрӯз|today|adv
фардо|tomorrow|adv
дирӯз|yesterday|adv
саг|dog|noun
гурба|cat|noun
асп|horse|noun
гов|cow|noun
гӯсфанд|sheep|noun
буз|goat|noun
хар|donkey|noun
паранда|bird|noun
уқоб|eagle|noun
мурғобӣ|duck|noun
хурӯс|rooster|noun
харгӯш|rabbit|noun
рӯбоҳ|fox|noun
хирс|bear|noun
шер|lion|noun
паланг|tiger|noun
фил|elephant|noun
маймун|monkey|noun
муш|mouse|noun
мӯрча|ant|noun
занбӯр|bee|noun
мор|snake|noun
қурбоққа|frog|noun
гург|wolf|noun
шутур|camel|noun
ҳашарот|insect|noun
ҷонвар|animal|noun
бол|wing|noun
дум|tail|noun
лона|nest|noun
ранг|color|noun
садо|sound|noun
бӯй|smell|noun
гармӣ|heat|noun
хунукӣ|coldness|noun
бориш|precipitation|noun
қулла|peak|noun
теппа|hill|noun
саҳро|desert|noun
чаман|meadow|noun
чашма|spring|noun
обшор|waterfall|noun
ҷӯй|brook|noun
уфуқ|horizon|noun
дунё|world|noun
табиат|nature|noun
муҳит|environment|noun
фасл|season|noun
самт|direction|noun
шимол|north|noun
ҷануб|south|noun
шарқ|east|noun
ғарб|west|noun
сар|head|noun
рӯй|face|noun
чашм|eye|noun
гӯш|ear|noun
бинӣ|nose|noun
даҳон|mouth|noun
дандон|tooth|noun
забон|tongue; language|noun
гардан|neck|noun
китф|shoulder|noun
даст|hand|noun
пой|foot; leg|noun
ангушт|finger|noun
дил|heart|noun
шикам|stomach|noun
пушт|back|noun
мӯй|hair|noun
хун|blood|noun
устухон|bone|noun
бадан|body|noun
саломатӣ|health|noun
дору|medicine|noun
дард|pain|noun
таб|fever|noun
хоб|sleep|noun
орзу|dream; wish|noun
фикр|thought|noun
ақл|mind|noun
хотира|memory|noun
савол|question|noun
ҷавоб|answer|noun
дарс|lesson|noun
вазифа|task; homework|noun
кор|work|noun
бозӣ|game|noun
сафар|trip|noun
истироҳат|rest|noun
суруд|song|noun
мусиқӣ|music|noun
рақс|dance|noun
филм|film|noun
хабар|news|noun
маълумот|information|noun
дониш|knowledge|noun
илм|science|noun
ҳунар|art; skill|noun
қоида|rule|noun
иҷозат|permission|noun
нақша|plan|noun
мақсад|goal|noun
кӯмак|help|noun
ёрӣ|help|noun
шодмонӣ|joy|noun
ғам|sadness|noun
муҳаббат|love|noun
дӯстӣ|friendship|noun
сулҳ|peace|noun
умед|hope|noun
ростӣ|truth|noun
дурӯғ|lie|noun
хато|mistake|noun
сабаб|reason|noun
натиҷа|result|noun
мисол|example|noun
қисм|part|noun
оғоз|start|noun
анҷом|end|noun
ҷой|place|noun
навбат|turn; queue|noun
тартиб|order|noun
имконият|opportunity|noun
мушкил|problem|noun
масъала|issue|noun
ҳал|solution|noun
лоиҳа|project|noun
ҷадвал|schedule; table|noun
рӯйхат|list|noun
рақам|digit|noun
шумора|number|noun
андоза|size|noun
вазн|weight|noun
дарозӣ|length|noun
баландӣ|height|noun
паҳно|width|noun
масофа|distance|noun
суръат|speed|noun
оромӣ|calm|noun
хурсандӣ|happiness|noun
зиндагӣ|life|noun
таҷриба|experience|noun
одат|habit|noun
фарҳанг|culture|noun
гуфтор|speech|noun
навишт|writing|noun
хониш|reading|noun
таърих|history|noun
ҷуғрофия|geography|noun
варзиш|sport|noun
даста|team|noun
ғалаба|victory|noun
хуб|good|adj
бад|bad|adj
калон|big|adj
хурд|small|adj
баланд|high; tall|adj
паст|low|adj
дароз|long|adj
кӯтоҳ|short|adj
васеъ|wide|adj
танг|narrow|adj
нав|new|adj
кӯҳна|old|adj
тоза|clean|adj
ифлос|dirty|adj
гарм|hot; warm|adj
хунук|cold|adj
салқин|cool|adj
равшан|bright|adj
торик|dark|adj
осон|easy|adj
душвор|difficult|adj
тез|fast|adj
суст|slow|adj
вазнин|heavy|adj
сабук|light|adj
нарм|soft|adj
сахт|hard|adj
ширин|sweet|adj
талх|bitter|adj
турш|sour|adj
шӯр|salty|adj
болаззат|tasty|adj
қимат|expensive|adj
арзон|cheap|adj
наздик|near|adj
дур|far|adj
кушода|open|adj
баста|closed|adj
пур|full|adj
холӣ|empty|adj
дуруст|correct|adj
нодуруст|incorrect|adj
бехатар|safe|adj
хатарнок|dangerous|adj
муҳим|important|adj
лозим|necessary|adj
мумкин|possible|adj
зебо|beautiful|adj
зишт|ugly|adj
ҷолиб|interesting|adj
дилгиркунанда|boring|adj
хурсанд|happy|adj
ғамгин|sad|adj
хаста|tired|adj
тайёр|ready|adj
озод|free|adj
серкор|busy|adj
ором|calm|adj
пуровоз|loud|adj
қавӣ|strong|adj
заиф|weak|adj
солим|healthy|adj
бемор|sick|adj
бой|rich|adj
камбағал|poor|adj
меҳрубон|kind|adj
боадаб|polite|adj
доно|clever|adj
сода|simple|adj
мураккаб|complex|adj
ҳақиқӣ|true|adj
қалбакӣ|fake|adj
маҳаллӣ|local|adj
хориҷӣ|foreign|adj
аввал|first|adj
охирин|last|adj
ҳаррӯза|daily|adj
рангин|colorful|adj
хушк|dry|adj
тар|wet|adj
сабз|green|adj
сурх|red|adj
сафед|white|adj
сиёҳ|black|adj
зард|yellow|adj
кабуд|blue|adj
қаҳваранг|brown|adj
хокистарӣ|gray|adj
норанҷӣ|orange|adj
арғувон|purple|adj
зинда|alive|adj
омода|ready|adj
муносиб|suitable|adj
беҳтар|better|adj
бадтар|worse|adj
камёб|rare|adj
маъмул|common|adj
будан|be|verb
доштан|have|verb
кардан|do|verb
рафтан|go|verb
омадан|come|verb
дидан|see|verb
шунидан|hear|verb
гуфтан|say|verb
хондан|read|verb
навиштан|write|verb
хӯрдан|eat|verb
нӯшидан|drink|verb
хобидан|sleep|verb
нишастан|sit|verb
истодан|stand|verb
давидан|run|verb
омӯхтан|learn|verb
омӯзондан|teach|verb
пухтан|cook|verb
кушодан|open|verb
бастан|close|verb
гирифтан|take|get|verb
додан|give|verb
харидан|buy|verb
фурӯхтан|sell|verb
пардохтан|pay|verb
пурсидан|ask|verb
фаҳмидан|understand|verb
донистан|know|verb
шустан|wash|verb
бардоштан|lift|verb
гузоштан|put|verb
ёфтан|find|verb
сохтан|build|verb
буридан|cut|verb
кашидан|pull; draw|verb
шикастан|break|verb
кӯшидан|try|verb
хандидан|laugh|verb
рақсидан|dance|verb
пӯшидан|wear|verb
рондан|drive|verb
оҳиста|slowly|adv
зуд|quickly|adv
ҳамеша|always|adv
гоҳе|sometimes|adv
акнун|now|adv
пас|then|adv
пеш|before|adv
якҷоя|together|adv
танҳо|alone; only|adv
боз|again|adv
""".strip()


POS_NOTES = {
    "adj": "adjective",
    "adv": "adverb",
    "noun": "noun",
    "num": "number",
    "ord": "ordinal number",
    "verb": "infinitive",
}


def parse_entries() -> list[Entry]:
    entries: list[Entry] = []
    for line in RAW_ENTRIES.splitlines():
        word, gloss, pos = [part.strip() for part in line.split("|", 2)]
        if " " in word:
            raise ValueError(f"target word must be one token: {word!r}")
        entries.append(Entry(word, gloss, pos))

    words = [entry.word for entry in entries]
    duplicates = sorted({word for word in words if words.count(word) > 1})
    if duplicates:
        raise ValueError(f"duplicate words: {duplicates}")
    if len(entries) < EXPECTED_COUNT:
        raise ValueError(f"expected at least {EXPECTED_COUNT} entries, got {len(entries)}")
    return select_a1_entries(entries)


def select_a1_entries(entries: list[Entry]) -> list[Entry]:
    selected: list[Entry] = []
    selected_words: set[str] = set()

    def add_matching(pos: str, limit: int | None = None) -> None:
        added = 0
        for entry in entries:
            if entry.pos != pos or entry.word in selected_words:
                continue
            selected.append(entry)
            selected_words.add(entry.word)
            added += 1
            if limit is not None and added >= limit:
                return

    add_matching("num")
    add_matching("ord")
    add_matching("verb")
    add_matching("adv")
    add_matching("adj", 80)
    add_matching("noun")

    if len(selected) < EXPECTED_COUNT:
        for entry in entries:
            if entry.word not in selected_words:
                selected.append(entry)
                selected_words.add(entry.word)
            if len(selected) >= EXPECTED_COUNT:
                break

    return selected[:EXPECTED_COUNT]


def first_gloss(gloss: str) -> str:
    return gloss.split(";", 1)[0].split("|", 1)[0].strip()


def sentences_for(entry: Entry) -> list[dict[str, str]]:
    word = entry.word
    gloss = first_gloss(entry.gloss)

    if entry.pos == "adj":
        pairs = [
            (f"Ин чиз {word} аст.", f"This thing is {gloss}."),
            (f"Ҳолат {word} аст.", f"The situation is {gloss}."),
            (f"Ҷавоб {word} аст.", f"The answer is {gloss}."),
        ]
    elif entry.pos == "adv":
        pairs = [
            (f"Ман {word} меоям.", f"I come {gloss}."),
            (f"Вай {word} мехонад.", f"He or she reads {gloss}."),
            (f"Мо {word} кор мекунем.", f"We work {gloss}."),
        ]
    elif entry.pos == "num":
        pairs = [
            (f"Ман {word} китоб дорам.", f"I have {gloss} book(s)."),
            (f"Синф {word} хонанда дорад.", f"The class has {gloss} pupil(s)."),
            (f"Ӯ {word} қалам дорад.", f"He or she has {gloss} pen(s)."),
        ]
    elif entry.pos == "ord":
        pairs = [
            (f"Дарси {word} осон аст.", f"The {gloss} lesson is easy."),
            (f"Рӯзи {word} хуб аст.", f"The {gloss} day is good."),
            (f"Саволи {word} кӯтоҳ аст.", f"The {gloss} question is short."),
        ]
    elif entry.pos == "verb":
        pairs = [
            (f"{word} осон аст.", f"To {gloss} is easy."),
            (f"Имрӯз {word} лозим аст.", f"Today it is necessary to {gloss}."),
            (f"Ман {word} мехоҳам.", f"I want to {gloss}."),
        ]
    else:
        pairs = [
            (f"Ин {word} аст.", f"This is {gloss}."),
            (f"Ман дар бораи {word} фикр мекунам.", f"I think about {gloss}."),
            (f"Дар дарс {word} ҳаст.", f"There is {gloss} in the lesson."),
        ]

    return [{"target": target, "text": text} for target, text in pairs]


def build_batches(entries: list[Entry]) -> list[dict[str, object]]:
    return [
        {
            "vocab_index": index,
            "word": entry.word,
            "gloss": entry.gloss,
            "sentences": sentences_for(entry),
        }
        for index, entry in enumerate(entries, 1)
    ]


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_vocab(entries: list[Entry]) -> None:
    vocab = [
        {"word": entry.word, "gloss": entry.gloss, "source": SOURCE}
        for entry in entries
    ]
    write_json(CORPORA / "tajik_a1_vocab.json", vocab)


def write_batches(batches: list[dict[str, object]]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    for start in range(1, EXPECTED_COUNT + 1, BATCH_SIZE):
        end = start + BATCH_SIZE - 1
        batch_path = GENERATED / f"tajik_{start:03d}_{end:03d}.json"
        write_json(batch_path, batches[start - 1 : end])


def write_explanations(entries: list[Entry]) -> None:
    rows = []
    current_id = ID_START
    for entry in entries:
        for _ in range(3):
            rows.append(
                {
                    "id": current_id,
                    "words": [
                        {
                            "word": entry.word,
                            "gloss": entry.gloss,
                            "note": POS_NOTES[entry.pos],
                        }
                    ],
                }
            )
            current_id -= 1

    write_json(CORPORA / "tajik_a1_explanations.json", {"data": rows})


def validate(entries: list[Entry], batches: list[dict[str, object]]) -> None:
    if len(entries) != EXPECTED_COUNT:
        raise ValueError(f"expected {EXPECTED_COUNT} entries, got {len(entries)}")
    if len(batches) != EXPECTED_COUNT:
        raise ValueError(f"expected {EXPECTED_COUNT} batches, got {len(batches)}")

    for entry, item in zip(entries, batches, strict=True):
        sentences = item["sentences"]
        if not isinstance(sentences, list) or len(sentences) != 3:
            raise ValueError(f"{entry.word}: expected 3 sentences")
        for sentence in sentences:
            target = sentence["target"]
            if f" {entry.word} " not in f" {target} ":
                raise ValueError(f"{entry.word}: target word is not a standalone token")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write-template-batches",
        action="store_true",
        help="overwrite generated Tajik batches with mechanical scaffolding; do not use for final corpus quality",
    )
    args = parser.parse_args()

    entries = parse_entries()

    CORPORA.mkdir(parents=True, exist_ok=True)
    write_vocab(entries)
    write_explanations(entries)
    if args.write_template_batches:
        batches = build_batches(entries)
        validate(entries, batches)
        write_batches(batches)
        print(f"wrote Tajik A1 vocab, explanations, and template batches for {len(entries)} words")
    else:
        print(f"wrote Tajik A1 vocab and explanations for {len(entries)} words")


if __name__ == "__main__":
    main()
