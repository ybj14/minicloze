#!/usr/bin/env python3
"""Generate reviewed Armenian A1 and Swadesh batch data for minicloze."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

from armenian_transliteration import romanize


ROOT = Path(__file__).resolve().parents[1]
CORPORA = ROOT / "minicloze-lib" / "corpora"
GENERATED = CORPORA / "generated"
USER_AGENT = {"User-Agent": "minicloze-armenian-course-builder/1.0"}

SWADESH_SOURCE = "Wiktionary Eastern Armenian Swadesh seed"
A1_SOURCE = "Codex-curated Armenian A1 seed list"

SWADESH_OVERRIDES = {
    16: "ոչ",
    40: "կնիկ",
    81: "սրունք",
    97: "փսխել",
    103: "իմանալ",
    134: "քաշել",
    143: "ջրի վրա լողալ",
    201: "վրա",
    202: "մեջ",
}


@dataclass(frozen=True)
class VocabItem:
    index: int
    word: str
    gloss: str
    category: str
    source: str


A1_EXTRAS: list[tuple[str, str, str]] = [
    ("բարև", "hello", "phrase"),
    ("խնդրում եմ", "please", "phrase"),
    ("շնորհակալություն", "thank you", "phrase"),
    ("ներողություն", "sorry", "phrase"),
    ("ցտեսություն", "goodbye", "phrase"),
    ("այո", "yes", "phrase"),
    ("չէ", "no", "phrase"),
    ("լավ", "okay", "adjective"),
    ("բարի գալուստ", "welcome", "phrase"),
    ("ընկեր", "friend", "person"),
    ("ընտանիք", "family", "person"),
    ("տատիկ", "grandmother", "person"),
    ("պապիկ", "grandfather", "person"),
    ("քույր", "sister", "person"),
    ("եղբայր", "brother", "person"),
    ("հորեղբայր", "uncle", "person"),
    ("մորաքույր", "aunt", "person"),
    ("հարևան", "neighbor", "person"),
    ("ուսուցիչ", "teacher", "person"),
    ("ուսանող", "student", "person"),
    ("աշակերտ", "pupil", "person"),
    ("բժիշկ", "doctor", "person"),
    ("բուժքույր", "nurse", "person"),
    ("ոստիկան", "police officer", "person"),
    ("վարորդ", "driver", "person"),
    ("աշխատող", "worker", "person"),
    ("վաճառող", "seller", "person"),
    ("հաճախորդ", "customer", "person"),
    ("հյուր", "guest", "person"),
    ("տուն", "house", "place"),
    ("դպրոց", "school", "place"),
    ("շուկա", "market", "place"),
    ("խանութ", "shop", "place"),
    ("փողոց", "street", "place"),
    ("քաղաք", "city", "place"),
    ("գյուղ", "village", "place"),
    ("հյուրանոց", "hotel", "place"),
    ("բանկ", "bank", "place"),
    ("հիվանդանոց", "hospital", "place"),
    ("դեղատուն", "pharmacy", "place"),
    ("այգի", "park", "place"),
    ("կանգառ", "stop", "place"),
    ("կայարան", "station", "place"),
    ("գրասենյակ", "office", "place"),
    ("ռեստորան", "restaurant", "place"),
    ("սրճարան", "cafe", "place"),
    ("թանգարան", "museum", "place"),
    ("գրադարան", "library", "place"),
    ("սենյակ", "room", "place"),
    ("ննջասենյակ", "bedroom", "place"),
    ("խոհանոց", "kitchen", "place"),
    ("լոգարան", "bathroom", "place"),
    ("բակ", "yard", "place"),
    ("կամուրջ", "bridge", "place"),
    ("եկեղեցի", "church", "place"),
    ("համալսարան", "university", "place"),
    ("գործարան", "factory", "place"),
    ("հրապարակ", "square", "place"),
    ("այսօր", "today", "time"),
    ("վաղը", "tomorrow", "time"),
    ("երեկ", "yesterday", "time"),
    ("հիմա", "now", "time"),
    ("առավոտ", "morning", "time"),
    ("կեսօր", "noon", "time"),
    ("երեկո", "evening", "time"),
    ("գիշեր", "night", "time"),
    ("շաբաթ", "week", "time"),
    ("ամիս", "month", "time"),
    ("ժամ", "hour", "time"),
    ("րոպե", "minute", "time"),
    ("երկուշաբթի", "Monday", "time"),
    ("երեքշաբթի", "Tuesday", "time"),
    ("չորեքշաբթի", "Wednesday", "time"),
    ("հինգշաբթի", "Thursday", "time"),
    ("ուրբաթ", "Friday", "time"),
    ("շաբաթ օր", "Saturday", "time"),
    ("կիրակի", "Sunday", "time"),
    ("հունվար", "January", "time"),
    ("փետրվար", "February", "time"),
    ("մարտ", "March", "time"),
    ("ապրիլ", "April", "time"),
    ("մայիս", "May", "time"),
    ("հունիս", "June", "time"),
    ("հուլիս", "July", "time"),
    ("օգոստոս", "August", "time"),
    ("սեպտեմբեր", "September", "time"),
    ("հոկտեմբեր", "October", "time"),
    ("նոյեմբեր", "November", "time"),
    ("դեկտեմբեր", "December", "time"),
    ("հաց", "bread", "food"),
    ("սուրճ", "coffee", "drink"),
    ("թեյ", "tea", "drink"),
    ("կաթ", "milk", "drink"),
    ("շաքար", "sugar", "food"),
    ("բրինձ", "rice", "food"),
    ("մակարոն", "pasta", "food"),
    ("ապուր", "soup", "food"),
    ("ձու", "egg", "food"),
    ("բանջարեղեն", "vegetables", "food"),
    ("միրգ", "fruit", "food"),
    ("բանան", "banana", "food"),
    ("նարինջ", "orange", "food"),
    ("խնձոր", "apple", "food"),
    ("կարտոֆիլ", "potato", "food"),
    ("լոլիկ", "tomato", "food"),
    ("սոխ", "onion", "food"),
    ("կարագ", "butter", "food"),
    ("մեղր", "honey", "food"),
    ("պանիր", "cheese", "food"),
    ("աղցան", "salad", "food"),
    ("նախաճաշ", "breakfast", "food"),
    ("ճաշ", "lunch", "food"),
    ("ընթրիք", "dinner", "food"),
    ("գիրք", "book", "object"),
    ("տետր", "notebook", "object"),
    ("գրիչ", "pen", "object"),
    ("մատիտ", "pencil", "object"),
    ("սեղան", "table", "object"),
    ("աթոռ", "chair", "object"),
    ("մահճակալ", "bed", "object"),
    ("դուռ", "door", "object"),
    ("պատուհան", "window", "object"),
    ("բանալի", "key", "object"),
    ("հեռախոս", "phone", "object"),
    ("համակարգիչ", "computer", "object"),
    ("հեռուստացույց", "television", "object"),
    ("ռադիո", "radio", "object"),
    ("պայուսակ", "bag", "object"),
    ("հագուստ", "clothes", "object"),
    ("կոշիկ", "shoes", "object"),
    ("գլխարկ", "hat", "object"),
    ("վերնաշապիկ", "shirt", "object"),
    ("տաբատ", "pants", "object"),
    ("զգեստ", "dress", "object"),
    ("բաճկոն", "jacket", "object"),
    ("փող", "money", "object"),
    ("դրամ", "dram", "object"),
    ("տոմս", "ticket", "object"),
    ("քարտեզ", "map", "object"),
    ("նվեր", "gift", "object"),
    ("արկղ", "box", "object"),
    ("օճառ", "soap", "object"),
    ("սրբիչ", "towel", "object"),
    ("հայելի", "mirror", "object"),
    ("բաժակ", "cup", "object"),
    ("ափսե", "plate", "object"),
    ("գդալ", "spoon", "object"),
    ("դանակ", "knife", "object"),
    ("պատառաքաղ", "fork", "object"),
    ("դաս", "lesson", "object"),
    ("աշխատանք", "work", "object"),
    ("տնային աշխատանք", "homework", "object"),
    ("քննություն", "exam", "object"),
    ("հարց", "question", "object"),
    ("պատասխան", "answer", "object"),
    ("թիվ", "number", "object"),
    ("տառ", "letter", "object"),
    ("լեզու", "language", "object"),
    ("հայերեն", "Armenian", "object"),
    ("անգլերեն", "English", "object"),
    ("պատմություն", "history", "object"),
    ("մաթեմատիկա", "math", "object"),
    ("երաժշտություն", "music", "object"),
    ("նկար", "picture", "object"),
    ("լուսանկար", "photo", "object"),
    ("խաղ", "game", "object"),
    ("նամակ", "letter", "object"),
    ("հաղորդագրություն", "message", "object"),
    ("նորություն", "news", "object"),
    ("փաստաթուղթ", "document", "object"),
    ("թուղթ", "paper", "object"),
    ("էջ", "page", "object"),
    ("գին", "price", "object"),
    ("հասցե", "address", "object"),
    ("մեքենա", "car", "transport"),
    ("ավտոբուս", "bus", "transport"),
    ("գնացք", "train", "transport"),
    ("տաքսի", "taxi", "transport"),
    ("հեծանիվ", "bicycle", "transport"),
    ("ինքնաթիռ", "airplane", "transport"),
    ("նավ", "boat", "transport"),
    ("ճամփորդություն", "trip", "transport"),
    ("արև", "sun", "nature"),
    ("լուսին", "moon", "nature"),
    ("աստղ", "star", "nature"),
    ("երկինք", "sky", "nature"),
    ("անձրև", "rain", "nature"),
    ("քամի", "wind", "nature"),
    ("ամպ", "cloud", "nature"),
    ("ձյուն", "snow", "nature"),
    ("սառույց", "ice", "nature"),
    ("ջերմություն", "heat", "nature"),
    ("ցուրտ", "cold", "nature"),
    ("գետ", "river", "nature"),
    ("սար", "mountain", "nature"),
    ("լիճ", "lake", "nature"),
    ("ծով", "sea", "nature"),
    ("ծաղիկ", "flower", "nature"),
    ("խոտ", "grass", "nature"),
    ("քար", "stone", "nature"),
    ("հող", "soil", "nature"),
    ("օդ", "air", "nature"),
    ("կատու", "cat", "animal"),
    ("ձի", "horse", "animal"),
    ("կով", "cow", "animal"),
    ("ոչխար", "sheep", "animal"),
    ("այծ", "goat", "animal"),
    ("հավ", "chicken", "animal"),
    ("խոզ", "pig", "animal"),
    ("առյուծ", "lion", "animal"),
    ("փիղ", "elephant", "animal"),
    ("երես", "face", "body"),
    ("մեջք", "back", "body"),
    ("ատամ", "tooth", "body"),
    ("ուս", "shoulder", "body"),
    ("մատ", "finger", "body"),
    ("թև", "arm", "body"),
    ("քիթ", "nose", "body"),
    ("առողջություն", "health", "body"),
    ("ցավ", "pain", "body"),
    ("դեղ", "medicine", "body"),
    ("հոգնածություն", "tiredness", "body"),
    ("կապույտ", "blue", "color"),
    ("կանաչ", "green", "color"),
    ("դեղին", "yellow", "color"),
    ("սպիտակ", "white", "color"),
    ("սև", "black", "color"),
    ("շագանակագույն", "brown", "color"),
    ("մոխրագույն", "gray", "color"),
    ("լավ", "good", "adjective"),
    ("վատ", "bad", "adjective"),
    ("նոր", "new", "adjective"),
    ("հին", "old", "adjective"),
    ("գեղեցիկ", "beautiful", "adjective"),
    ("հեշտ", "easy", "adjective"),
    ("արագ", "fast", "adjective"),
    ("դանդաղ", "slow", "adjective"),
    ("տաք", "warm", "adjective"),
    ("սառը", "cold", "adjective"),
    ("թանկ", "expensive", "adjective"),
    ("էժան", "cheap", "adjective"),
    ("մաքուր", "clean", "adjective"),
    ("կեղտոտ", "dirty", "adjective"),
    ("ուրախ", "happy", "adjective"),
    ("տխուր", "sad", "adjective"),
    ("պատրաստ", "ready", "adjective"),
    ("հիվանդ", "sick", "adjective"),
    ("ուժեղ", "strong", "adjective"),
    ("թույլ", "weak", "adjective"),
    ("կարևոր", "important", "adjective"),
    ("օգտակար", "useful", "adjective"),
    ("լուռ", "quiet", "adjective"),
    ("բարձր", "loud", "adjective"),
    ("գնալ", "go", "verb"),
    ("գալ", "come", "verb"),
    ("կարդալ", "read", "verb"),
    ("գրել", "write", "verb"),
    ("սովորել", "learn", "verb"),
    ("սովորեցնել", "teach", "verb"),
    ("աշխատել", "work", "verb"),
    ("գնել", "buy", "verb"),
    ("վաճառել", "sell", "verb"),
    ("բացել", "open", "verb"),
    ("փակել", "close", "verb"),
    ("վեր կենալ", "get up", "verb"),
    ("վազել", "run", "verb"),
    ("օգնել", "help", "verb"),
    ("հարցնել", "ask", "verb"),
    ("պատասխանել", "answer", "verb"),
    ("ուզել", "want", "verb"),
    ("սիրել", "like", "verb"),
    ("կարողանալ", "can", "verb"),
    ("վերցնել", "take", "verb"),
    ("բերել", "bring", "verb"),
    ("ուղարկել", "send", "verb"),
    ("սպասել", "wait", "verb"),
    ("սկսել", "start", "verb"),
    ("ավարտել", "finish", "verb"),
    ("լողանալ", "wash oneself", "verb"),
    ("պատրաստել", "prepare", "verb"),
    ("եփել", "cook", "verb"),
    ("թարգմանել", "translate", "verb"),
    ("ընտրել", "choose", "verb"),
    ("փոխել", "change", "verb"),
    ("ստորագրել", "sign", "verb"),
    ("վճարել", "pay", "verb"),
    ("օգտագործել", "use", "verb"),
    ("ստուգել", "check", "verb"),
    ("զանգել", "call", "verb"),
    ("նորոգել", "fix", "verb"),
    ("մաքրել", "clean", "verb"),
    ("անել", "do", "verb"),
    ("հիշել", "remember", "verb"),
    ("մոռանալ", "forget", "verb"),
    ("ստանալ", "receive", "verb"),
    ("կրել", "carry", "verb"),
    ("մնալ", "stay", "verb"),
    ("զգուշանալ", "be careful", "verb"),
    ("գտնել", "find", "verb"),
    ("կորցնել", "lose", "verb"),
    ("չափել", "measure", "verb"),
    ("միացնել", "turn on", "verb"),
    ("անջատել", "turn off", "verb"),
    ("կամ", "or", "function"),
    ("բայց", "but", "function"),
    ("դեպի", "to", "function"),
    ("համար", "for", "function"),
    ("մասին", "about", "function"),
    ("նման", "like", "function"),
    ("առաջ", "before", "function"),
    ("հետո", "after", "function"),
    ("տակ", "under", "function"),
    ("առանց", "without", "function"),
    ("օդանավակայան", "airport", "place"),
    ("փոստ", "post office", "place"),
    ("դասարան", "classroom", "place"),
    ("մարզադաշտ", "stadium", "place"),
    ("լողավազան", "pool", "place"),
    ("ուղեբեռ", "luggage", "object"),
    ("անձնագիր", "passport", "object"),
    ("վիզա", "visa", "object"),
    ("ժամացույց", "clock", "object"),
    ("ակնոց", "glasses", "object"),
    ("հովանոց", "umbrella", "object"),
    ("մետրո", "metro", "transport"),
    ("տրամվայ", "tram", "transport"),
    ("մոտոցիկլ", "motorcycle", "transport"),
    ("ելակ", "strawberry", "food"),
    ("վարունգ", "cucumber", "food"),
    ("գազար", "carrot", "food"),
    ("մածուն", "yogurt", "food"),
    ("հյութ", "juice", "drink"),
    ("սենդվիչ", "sandwich", "food"),
    ("ժպտալ", "smile", "verb"),
    ("խաղալ", "play", "verb"),
    ("լսել", "listen", "verb"),
    ("նայել", "look", "verb"),
    ("հասկանալ", "understand", "verb"),
    ("կրկնել", "repeat", "verb"),
    ("ծիծաղել", "laugh", "verb"),
    ("հանդիպել", "meet", "verb"),
    ("ձախ", "left", "adjective"),
    ("աջ", "right", "adjective"),
    ("ուղիղ", "straight", "adjective"),
    ("քաղցած", "hungry", "adjective"),
    ("ծարավ", "thirsty", "adjective"),
    ("զբաղված", "busy", "adjective"),
    ("ազատ", "free", "adjective"),
    ("միջին", "medium", "adjective"),
]

COMMON = {
    "i": ("ես", "I"),
    "you": ("դու", "you"),
    "we": ("մենք", "we"),
    "child": ("երեխա", "child"),
    "teacher": ("ուսուցիչ", "teacher"),
    "doctor": ("բժիշկ", "doctor"),
    "mother": ("մայր", "mother"),
    "friend": ("ընկեր", "friend"),
    "today": ("այսօր", "today"),
    "tomorrow": ("վաղը", "tomorrow"),
    "now": ("հիմա", "now"),
    "morning": ("առավոտ", "morning"),
    "evening": ("երեկո", "evening"),
    "here": ("այստեղ", "here"),
    "there": ("այնտեղ", "there"),
    "this": ("սա", "this"),
    "that": ("դա", "that"),
    "home": ("տուն", "home"),
    "school": ("դպրոց", "school"),
    "market": ("շուկա", "market"),
    "room": ("սենյակ", "room"),
    "yard": ("բակ", "yard"),
    "outside": ("դրսում", "outside"),
    "coffee": ("սուրճ", "coffee"),
    "tea": ("թեյ", "tea"),
    "water": ("ջուր", "water"),
    "book": ("գիրք", "book"),
    "bag": ("պայուսակ", "bag"),
    "bag_gen": ("պայուսակի", "bag"),
    "table": ("սեղան", "table"),
    "table_gen": ("սեղանի", "table"),
    "chair": ("աթոռ", "chair"),
    "chair_gen": ("աթոռի", "chair"),
    "bed": ("մահճակալ", "bed"),
    "bed_gen": ("մահճակալի", "bed"),
    "cup": ("բաժակ", "cup"),
    "picture": ("նկար", "picture"),
    "door": ("դուռ", "door"),
    "road": ("ճանապարհ", "road"),
    "road_gen": ("ճանապարհի", "road"),
    "cat": ("կատու", "cat"),
    "gift": ("նվեր", "gift"),
    "lesson": ("դաս", "lesson"),
    "school_gen": ("դպրոցի", "school"),
    "trip": ("ճամփորդություն", "trip"),
    "sugar": ("շաքար", "sugar"),
    "apple": ("խնձոր", "apple"),
    "sound": ("ձայն", "sound"),
    "music": ("երաժշտություն", "music"),
    "work": ("աշխատանք", "work"),
    "question": ("հարց", "question"),
    "is": ("է", "is"),
    "are": ("են", "are"),
    "have": ("ունեմ", "I have"),
    "there_is": ("կա", "there is"),
    "want": ("եմ ուզում", "I want"),
    "like": ("եմ սիրում", "I like"),
    "see": ("տեսնում եմ", "I see"),
    "bring": ("բերեց", "brought"),
    "drink": ("խմում եմ", "I drink"),
    "eat": ("ուտում եմ", "I eat"),
    "go": ("գնում եմ", "I go"),
    "come": ("գալիս եմ", "I come"),
    "learn": ("սովորում ենք", "we learn"),
    "say": ("ասում եմ", "I say"),
    "can": ("կարող ես", "you can"),
    "good": ("լավ", "good"),
    "clean": ("մաքուր", "clean"),
    "near": ("մոտ", "near"),
    "inside": ("մեջ", "inside"),
    "on": ("վրա", "on"),
    "to": ("դեպի", "to"),
    "with": ("հետ", "with"),
    "and": ("և", "and"),
    "before": ("առաջ", "before"),
    "after": ("հետո", "after"),
}

QUESTION_SENTENCES = {
    "who": [
        (["x", "came"], "Who came?"),
        (["x", "here", "is"], "Who is here?"),
        (["teacher_def", "x", "sees"], "Whom does the teacher see?"),
    ],
    "what": [
        (["you", "x", "you_want"], "What do you want?"),
        (["x", "table_gen", "on", "there_is"], "What is on the table?"),
        (["friend_def", "x", "bring"], "What did the friend bring?"),
    ],
    "where": [
        (["you", "x", "you_go"], "Where are you going?"),
        (["book_def", "x", "there_is"], "Where is the book?"),
        (["teacher_def", "x", "will_come"], "Where will the teacher come?"),
    ],
    "when": [
        (["you", "x", "you_come"], "When will you come?"),
        (["we", "x", "learn"], "When do we study?"),
        (["market_def", "x", "is"], "When is the market?"),
    ],
    "how": [
        (["you", "x", "you_go"], "How do you go?"),
        (["we", "x", "learn"], "How do we study?"),
        (["x", "water", "i_drink"], "How do I drink water?"),
    ],
}

PRONOUN_FORMS = {
    "ես": ("եմ", "am", "I"),
    "դու": ("ես", "are", "you"),
    "նա": ("է", "is", "he"),
    "մենք": ("ենք", "are", "we"),
    "դուք": ("եք", "are", "you all"),
    "նրանք": ("են", "are", "they"),
}

MONTHS = {
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
}
COLORS = {"white", "black", "red", "blue", "green", "yellow", "brown", "gray"}
DRINKS = {"water", "coffee", "tea", "milk"}
FOOD_GLOSSES = {
    "bread",
    "rice",
    "pasta",
    "soup",
    "meat",
    "fish",
    "egg",
    "vegetables",
    "fruit",
    "banana",
    "orange",
    "apple",
    "potato",
    "tomato",
    "onion",
    "butter",
    "honey",
    "cheese",
    "salad",
    "lunch",
    "breakfast",
    "dinner",
    "salt",
    "sugar",
    "fat",
}
QUESTION_GLOSSES = {"who", "what", "where", "when", "how"}
FUNCTION_GLOSSES = {
    "and",
    "or",
    "but",
    "because",
    "if",
    "with",
    "in",
    "on",
    "at",
    "to",
    "for",
    "about",
    "like",
    "before",
    "after",
    "under",
    "near",
    "without",
}
SENSITIVE_VERBS = {
    "bite",
    "spit",
    "vomit",
    "fear",
    "die",
    "kill",
    "fight",
    "hunt",
    "hit",
    "cut",
    "split",
    "stab",
}
INVOLUNTARY_VERBS = {"die", "vomit", "fear"}


def fetch_text(url: str) -> str:
    with urlopen(Request(url, headers=USER_AGENT), timeout=30) as response:
        return response.read().decode("utf-8")


def parse_swadesh_module(code: str) -> dict[int, list[str]]:
    text = fetch_text(f"https://en.wiktionary.org/wiki/Module:Swadesh/data/{code}?action=raw")
    rows: dict[int, list[str]] = {}
    for match in re.finditer(r"m\[(\d+)\]\s*=\s*(.*)", text):
        terms = [clean_term(term) for term in re.findall(r'term\s*=\s*"([^"]+)"', match.group(2))]
        terms = [term for term in terms if term and not term.startswith("-")]
        if terms:
            rows[int(match.group(1))] = terms
    return rows


def clean_term(term: str) -> str:
    term = re.sub(r"<notes:[^>]+>", "", term)
    term = re.sub(r"\(.*?\)", "", term)
    term = term.replace("...", " ").replace("…", " ")
    term = re.sub(r"\s+", " ", term)
    return term.strip().strip("։՞՜՛՝,.;:?!")


def infer_category(gloss: str, index: int | None, fallback: str = "object") -> str:
    gloss = gloss.lower()
    if gloss in QUESTION_GLOSSES:
        return "question"
    if index is not None and index in {1, 2, 3, 4, 5, 6}:
        return "pronoun"
    if index is not None and index in {7, 8, 9, 10}:
        return "deictic"
    if gloss in {"not", "no"}:
        return "negation"
    if gloss in FUNCTION_GLOSSES:
        return "function"
    if index is not None and 17 <= index <= 26:
        return "number"
    if index is not None and (27 <= index <= 35 or 180 <= index <= 201):
        return "adjective"
    if gloss in COLORS:
        return "color"
    if index is not None and 36 <= index <= 43:
        return "person"
    if index is not None and 44 <= index <= 50:
        return "animal"
    if index is not None and 51 <= index <= 60:
        return "nature"
    if index is not None and 62 <= index <= 91:
        if gloss in FOOD_GLOSSES:
            return "drink" if gloss in DRINKS else "food"
        return "body"
    if index is not None and 92 <= index <= 146:
        return "verb"
    if index is not None and 147 <= index <= 179:
        return "nature"
    if gloss in FOOD_GLOSSES:
        return "drink" if gloss in DRINKS else "food"
    return fallback


def swadesh_items() -> list[VocabItem]:
    try:
        english = parse_swadesh_module("en")
        armenian = parse_swadesh_module("hy/Eastern")
    except Exception:
        cached = CORPORA / "armenian_swadesh_vocab.json"
        if not cached.exists():
            raise
        data = json.loads(cached.read_text(encoding="utf-8"))
        return [
            VocabItem(
                index=index,
                word=clean_term(item["word"]),
                gloss=str(item["gloss"]).lower(),
                category=infer_category(str(item["gloss"]).lower(), index),
                source=str(item.get("source") or SWADESH_SOURCE),
            )
            for index, item in enumerate(data, 1)
        ]

    items = []
    for index in range(1, 208):
        word = SWADESH_OVERRIDES.get(index) or armenian[index][0]
        gloss = english[index][0].lower()
        items.append(
            VocabItem(
                index=index,
                word=clean_term(word),
                gloss=gloss,
                category=infer_category(gloss, index),
                source=SWADESH_SOURCE,
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
                    source=item.source,
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
                source=A1_SOURCE,
            )
        )
        seen.add(word)
        if len(items) == 500:
            break
    if len(items) != 500:
        raise ValueError(f"expected 500 A1 items, got {len(items)}")
    return items


def explain(word: str, gloss: str, note: str | None = None) -> dict[str, str]:
    item = {"word": word, "gloss": gloss, "transliteration": romanize(word)}
    if note:
        item["note"] = note
    return item


def h(key: str) -> dict[str, str]:
    word, gloss = COMMON[key]
    return explain(word, gloss)


def target(item: VocabItem) -> dict[str, str]:
    return explain(item.word, item.gloss, "target")


def sentence(tokens: Iterable[dict[str, str]], english: str, question: bool = False) -> dict[str, object]:
    words = list(tokens)
    target_text = " ".join(word["word"] for word in words)
    return {
        "target": f"{target_text}{'?' if question else '։'}",
        "text": english,
        "words": words,
    }


def token_from_key(key: str, item: VocabItem) -> dict[str, str]:
    if key == "x":
        return target(item)
    fixed = {
        "came": ("եկավ", "came"),
        "sees": ("տեսնում է", "sees"),
        "you_want": ("ես ուզում", "you want"),
        "you_go": ("ես գնում", "you go"),
        "will_come": ("կգա", "will come"),
        "you_come": ("ես գալիս", "you come"),
        "i_drink": ("խմում եմ", "I drink"),
        "teacher_def": ("ուսուցիչը", "the teacher"),
        "friend_def": ("ընկերը", "the friend"),
        "book_def": ("գիրքը", "the book"),
        "market_def": ("շուկան", "the market"),
        "table_gen": ("սեղանի", "table", "genitive"),
        "chair_gen": ("աթոռի", "chair", "genitive"),
        "bed_gen": ("մահճակալի", "bed", "genitive"),
        "bag_gen": ("պայուսակի", "bag", "genitive"),
        "road_gen": ("ճանապարհի", "road", "genitive"),
        "school_gen": ("դպրոցի", "school", "genitive"),
    }
    if key in fixed:
        values = fixed[key]
        return explain(values[0], values[1], values[2] if len(values) > 2 else None)
    return h(key)


def from_keys(keys: list[str], item: VocabItem, english: str, question: bool = False) -> dict[str, object]:
    return sentence([token_from_key(key, item) for key in keys], english, question)


def choose_sentences(item: VocabItem, frames: list[tuple[list[dict[str, str]], str] | tuple[list[dict[str, str]], str, bool]]) -> list[dict[str, object]]:
    start = (item.index * 3) % len(frames)
    chosen = [frames[(start + offset) % len(frames)] for offset in range(3)]
    return [sentence(frame[0], frame[1], frame[2] if len(frame) > 2 else False) for frame in chosen]


def pronoun_sentences(item: VocabItem) -> list[dict[str, object]]:
    verb, verb_gloss, english_subject = PRONOUN_FORMS.get(item.word, ("է", "is", item.gloss))
    subject = english_subject[0].upper() + english_subject[1:]
    return [
        sentence([target(item), h("here"), explain(verb, verb_gloss)], f"{subject} {verb_gloss} here."),
        sentence([target(item), explain("ուսանող", "student"), explain(verb, verb_gloss)], f"{subject} {verb_gloss} a student."),
        sentence([target(item), h("good"), explain(verb, verb_gloss)], f"{subject} {verb_gloss} well."),
    ]


def question_sentences(item: VocabItem) -> list[dict[str, object]]:
    frames = QUESTION_SENTENCES.get(item.gloss.lower())
    if frames:
        return [from_keys(keys, item, english, True) for keys, english in frames]
    return [
        sentence([target(item), h("here"), h("is")], f"{item.gloss.title()} is here?", True),
        sentence([h("you"), target(item), explain("ես ուզում", "you want")], f"Do you want {item.gloss}?", True),
        sentence([h("teacher"), target(item), explain("տեսնում է", "sees")], f"Does the teacher see {item.gloss}?", True),
    ]


def deictic_sentences(item: VocabItem) -> list[dict[str, object]]:
    if item.gloss in {"here", "there"}:
        return [
            sentence([h("i"), target(item), h("go")], f"I go {item.gloss}."),
            sentence([h("book"), target(item), h("there_is")], f"The book is {item.gloss}."),
            sentence([h("friend"), target(item), h("come")], f"A friend comes {item.gloss}."),
        ]
    return [
        sentence([target(item), h("book"), h("is")], f"{item.gloss.title()} is a book."),
        sentence([h("i"), target(item), h("see")], f"I see {item.gloss}."),
        sentence([target(item), h("bag"), h("good"), h("is")], f"{item.gloss.title()} bag is good."),
    ]


def negation_sentences(item: VocabItem) -> list[dict[str, object]]:
    return [
        sentence([target(item), h("this"), h("book"), explain("չէ", "is not")], "No, this is not a book."),
        sentence([h("i"), h("coffee"), target(item), explain("չեմ ուզում", "do not want")], "I do not want coffee."),
        sentence([h("today"), h("school"), target(item), explain("չկա", "there is no")], "There is no school today."),
    ]


def function_sentences(item: VocabItem) -> list[dict[str, object]]:
    g = item.gloss.lower()
    if g == "and":
        frames = [
            ([h("coffee"), target(item), h("water"), explain("եմ ուզում", "I want")], "I want coffee and water."),
            ([h("mother"), target(item), h("friend"), explain("եկան", "came")], "Mother and a friend came."),
            ([h("book"), target(item), h("bag"), h("there_is")], "There are a book and a bag."),
        ]
    elif g == "or":
        frames = [
            ([h("coffee"), target(item), h("tea"), explain("եմ ուզում", "I want")], "I want coffee or tea."),
            ([h("home"), target(item), h("market"), h("go")], "I go home or to the market."),
            ([h("book"), target(item), h("bag"), h("bring")], "Bring the book or the bag."),
        ]
    elif g == "but":
        frames = [
            ([h("coffee"), explain("եմ ուզում", "I want"), target(item), h("water"), h("drink")], "I want coffee but drink water."),
            ([h("today"), h("good"), h("is"), target(item), explain("սառը", "cold"), h("is")], "Today is good but cold."),
            ([h("friend"), explain("եկավ", "came"), target(item), h("teacher"), explain("չեկավ", "did not come")], "A friend came, but the teacher did not come."),
        ]
    elif g == "because":
        frames = [
            ([h("water"), h("drink"), target(item), explain("տաք", "hot"), h("is")], "I drink water because it is hot."),
            ([h("home"), h("go"), target(item), explain("հոգնած եմ", "I am tired")], "I go home because I am tired."),
            ([h("book"), explain("եմ ուզում", "I want"), target(item), h("learn")], "I want a book because we study."),
        ]
    elif g == "if":
        frames = [
            ([target(item), h("water"), h("there_is"), h("coffee"), h("drink")], "If there is water, I drink coffee."),
            ([target(item), h("teacher"), explain("գա", "comes"), h("we"), h("learn")], "If the teacher comes, we study."),
            ([target(item), h("market"), h("near"), h("is"), h("i"), h("go")], "If the market is near, I go."),
        ]
    elif g in {"in", "at"}:
        frames = [
            ([h("book"), h("bag_gen"), target(item), h("there_is")], "The book is in the bag."),
            ([h("friend"), h("home"), target(item), h("there_is")], "A friend is at home."),
            ([h("teacher"), h("school"), target(item), h("there_is")], "The teacher is at school."),
        ]
    elif g == "with":
        frames = [
            ([h("i"), h("friend"), target(item), h("go")], "I go with a friend."),
            ([h("teacher"), h("child"), target(item), explain("սովորում է", "studies")], "The teacher studies with the child."),
            ([h("coffee"), h("sugar"), target(item), h("is")], "The coffee is with sugar."),
        ]
    elif g == "to":
        frames = [
            ([h("i"), target(item), h("home"), h("go")], "I go home."),
            ([h("friend"), target(item), h("market"), explain("գնում է", "goes")], "A friend goes to the market."),
            ([h("teacher"), target(item), h("school"), explain("գնում է", "goes")], "The teacher goes to school."),
        ]
    elif g == "for":
        frames = [
            ([h("this"), h("book"), target(item), h("friend"), h("is")], "This book is for a friend."),
            ([h("coffee"), target(item), h("teacher"), h("is")], "The coffee is for the teacher."),
            ([h("gift"), target(item), h("mother"), h("is")], "The gift is for mother."),
        ]
    elif g == "about":
        frames = [
            ([h("i"), h("book"), target(item), explain("խոսում եմ", "I speak")], "I speak about the book."),
            ([h("teacher"), h("lesson"), target(item), explain("խոսում է", "speaks")], "The teacher speaks about the lesson."),
            ([h("friend"), h("trip"), target(item), explain("հարցնում է", "asks")], "A friend asks about the trip."),
        ]
    elif g == "like":
        frames = [
            ([h("child"), h("teacher"), target(item), explain("խոսում է", "speaks")], "The child speaks like the teacher."),
            ([h("this"), h("bag"), h("book"), target(item), h("is")], "This bag is like a book."),
            ([h("friend"), h("mother"), target(item), explain("օգնում է", "helps")], "A friend helps like mother."),
        ]
    elif g == "before":
        frames = [
            ([h("school"), target(item), h("i"), h("coffee"), h("drink")], "Before school, I drink coffee."),
            ([h("market"), target(item), h("friend"), explain("գալիս է", "comes")], "Before the market, a friend comes."),
            ([h("lesson"), target(item), h("we"), h("book"), explain("կարդում ենք", "we read")], "Before the lesson, we read a book."),
        ]
    elif g == "after":
        frames = [
            ([h("school"), target(item), h("i"), h("home"), h("go")], "After school, I go home."),
            ([h("market"), target(item), h("friend"), h("coffee"), explain("խմում է", "drinks")], "After the market, a friend drinks coffee."),
            ([h("lesson"), target(item), h("we"), h("book"), explain("կարդում ենք", "we read")], "After the lesson, we read a book."),
        ]
    elif g == "on":
        frames = [
            ([h("book"), h("table_gen"), target(item), h("there_is")], "The book is on the table."),
            ([h("cup"), h("table_gen"), target(item), h("there_is")], "The cup is on the table."),
            ([h("bag"), h("chair_gen"), target(item), h("there_is")], "The bag is on the chair."),
        ]
    elif g == "under":
        frames = [
            ([h("book"), h("table_gen"), target(item), h("there_is")], "The book is under the table."),
            ([h("bag"), h("chair_gen"), target(item), h("there_is")], "The bag is under the chair."),
            ([h("cat"), h("bed_gen"), target(item), h("there_is")], "The cat is under the bed."),
        ]
    elif g == "near":
        frames = [
            ([h("school"), h("market"), target(item), h("there_is")], "The school is near the market."),
            ([h("home"), h("road_gen"), target(item), h("there_is")], "The house is near the road."),
            ([h("friend"), h("door"), target(item), h("there_is")], "A friend is near the door."),
        ]
    elif g == "without":
        frames = [
            ([h("i"), h("sugar"), target(item), h("coffee"), h("drink")], "I drink coffee without sugar."),
            ([h("friend"), h("book"), target(item), h("school"), explain("գնում է", "goes")], "A friend goes to school without a book."),
            ([h("teacher"), h("coffee"), target(item), explain("գալիս է", "comes")], "The teacher comes without coffee."),
        ]
    else:
        frames = [
            ([h("i"), h("book"), target(item), h("there_is")], f"I use {item.gloss} with the book."),
            ([h("friend"), target(item), h("home"), h("go")], f"A friend goes {item.gloss} home."),
            ([h("teacher"), target(item), h("school"), h("there_is")], f"The teacher is {item.gloss} school."),
        ]
    return [sentence(tokens, english) for tokens, english in frames]


def number_sentences(item: VocabItem) -> list[dict[str, object]]:
    book = "book" if item.gloss == "one" else "books"
    question = "question" if item.gloss == "one" else "questions"
    frames = [
        ([h("i"), target(item), h("book"), h("have")], f"I have {item.gloss} {book}."),
        ([h("table_gen"), h("on"), target(item), h("cup"), h("there_is")], f"There are {item.gloss} cups on the table."),
        ([h("teacher"), target(item), h("question"), explain("հարցրեց", "asked")], f"The teacher asked {item.gloss} {question}."),
        ([h("child"), target(item), h("apple"), explain("բերեց", "brought")], f"The child brought {item.gloss} apples."),
        ([h("room"), h("inside"), target(item), h("chair"), h("there_is")], f"There are {item.gloss} chairs in the room."),
        ([h("market"), target(item), h("bag"), h("there_is")], f"There are {item.gloss} bags at the market."),
    ]
    return choose_sentences(item, frames)


def adjective_sentences(item: VocabItem) -> list[dict[str, object]]:
    if item.gloss == "loud":
        return [
            sentence([h("sound"), target(item), h("is")], "The sound is loud."),
            sentence([h("music"), target(item), h("is")], "The music is loud."),
            sentence([h("this"), h("room"), target(item), h("is")], "This room is loud."),
        ]
    if item.gloss == "quiet":
        return [
            sentence([h("room"), target(item), h("is")], "The room is quiet."),
            sentence([h("child"), target(item), h("is")], "The child is quiet."),
            sentence([h("this"), h("home"), target(item), h("is")], "This house is quiet."),
        ]
    frames = [
        ([h("bag"), target(item), h("is")], f"The bag is {item.gloss}."),
        ([h("this"), h("lesson"), target(item), h("is")], f"This lesson is {item.gloss}."),
        ([h("this"), h("book"), target(item), h("is")], f"This book is {item.gloss}."),
        ([h("room"), target(item), h("is")], f"The room is {item.gloss}."),
        ([h("coffee"), target(item), h("is")], f"The coffee is {item.gloss}."),
        ([h("market"), target(item), h("is")], f"The market is {item.gloss}."),
        ([h("this"), h("work"), target(item), h("is")], f"This work is {item.gloss}."),
        ([h("today"), h("trip"), target(item), h("is")], f"The trip is {item.gloss} today."),
        ([h("friend"), target(item), h("is")], f"The friend is {item.gloss}."),
    ]
    return choose_sentences(item, frames)


def color_sentences(item: VocabItem) -> list[dict[str, object]]:
    return [
        sentence([h("bag"), target(item), h("is")], f"The bag is {item.gloss}."),
        sentence([h("this"), explain("զգեստ", "dress"), target(item), h("is")], f"This dress is {item.gloss}."),
        sentence([target(item), explain("գույն", "color"), h("like")], f"I like the color {item.gloss}."),
    ]


def person_sentences(item: VocabItem) -> list[dict[str, object]]:
    frames = [
        ([target(item), h("home"), h("there_is")], f"The {item.gloss} is at home."),
        ([h("i"), target(item), h("see")], f"I see the {item.gloss}."),
        ([target(item), h("coffee"), explain("խմում է", "drinks")], f"The {item.gloss} drinks coffee."),
        ([target(item), h("market"), explain("գնում է", "goes")], f"The {item.gloss} goes to the market."),
        ([target(item), h("book"), explain("կարդում է", "reads")], f"The {item.gloss} reads a book."),
        ([target(item), h("child"), explain("օգնում է", "helps")], f"The {item.gloss} helps the child."),
        ([h("teacher"), target(item), h("with"), explain("խոսում է", "speaks")], f"The teacher speaks with the {item.gloss}."),
        ([target(item), h("school"), h("inside"), h("there_is")], f"The {item.gloss} is inside the school."),
        ([h("friend"), target(item), explain("սպասում է", "waits for")], f"A friend waits for the {item.gloss}."),
    ]
    return choose_sentences(item, frames)


def place_sentences(item: VocabItem) -> list[dict[str, object]]:
    frames = [
        ([h("i"), target(item), explain("եմ գնում", "I go")], f"I go to the {item.gloss}."),
        ([target(item), h("near"), h("is")], f"The {item.gloss} is near."),
        ([h("friend"), target(item), h("inside"), h("there_is")], f"A friend is inside the {item.gloss}."),
        ([h("teacher"), target(item), explain("գնում է", "goes")], f"The teacher goes to the {item.gloss}."),
        ([target(item), h("road_gen"), h("near"), h("there_is")], f"The {item.gloss} is near the road."),
        ([h("i"), target(item), h("see")], f"I see the {item.gloss}."),
        ([h("friend"), target(item), explain("սպասում է", "waits at")], f"A friend waits at the {item.gloss}."),
        ([h("this"), target(item), h("good"), h("is")], f"This {item.gloss} is good."),
        ([target(item), h("market"), h("near"), h("there_is")], f"The {item.gloss} is near the market."),
    ]
    return choose_sentences(item, frames)


def time_sentences(item: VocabItem) -> list[dict[str, object]]:
    if item.gloss.lower() in MONTHS:
        return [
            sentence([target(item), h("i"), h("come")], f"I come in {item.gloss}."),
            sentence([target(item), h("we"), h("learn")], f"We study in {item.gloss}."),
            sentence([target(item), h("market"), h("go")], f"I go to the market in {item.gloss}."),
        ]
    return [
        sentence([target(item), h("i"), h("come")], f"I come {item.gloss}."),
        sentence([target(item), h("we"), h("learn")], f"We study {item.gloss}."),
        sentence([target(item), h("market"), h("go")], f"I go to the market {item.gloss}."),
    ]


def food_sentences(item: VocabItem) -> list[dict[str, object]]:
    action = h("drink") if item.category == "drink" or item.gloss in DRINKS else h("eat")
    consume = "drink" if action["word"] == "խմում եմ" else "eat"
    third = explain("խմում է", "drinks") if consume == "drink" else explain("ուտում է", "eats")
    frames = [
        ([h("i"), target(item), action], f"I {consume} {item.gloss}."),
        ([h("mother"), target(item), explain("պատրաստում է", "prepares")], f"Mother prepares {item.gloss}."),
        ([h("market"), target(item), h("there_is")], f"There is {item.gloss} at the market."),
        ([h("friend"), target(item), explain("է ուզում", "wants")], f"A friend wants {item.gloss}."),
        ([target(item), h("table_gen"), h("on"), h("there_is")], f"The {item.gloss} is on the table."),
        ([h("child"), target(item), third], f"The child {consume}s {item.gloss}."),
    ]
    return choose_sentences(item, frames)


def object_sentences(item: VocabItem) -> list[dict[str, object]]:
    if item.gloss == "name":
        return [
            sentence([h("i"), target(item), explain("գրում եմ", "I write")], "I write my name."),
            sentence([target(item), h("book"), h("on"), h("there_is")], "The name is on the book."),
            sentence([h("teacher"), target(item), explain("հարցնում է", "asks")], "The teacher asks for the name."),
        ]
    frames = [
        ([h("i"), target(item), h("want")], f"I want {item.gloss}."),
        ([target(item), h("table_gen"), h("on"), h("there_is")], f"The {item.gloss} is on the table."),
        ([h("friend"), target(item), h("bring")], f"A friend brought {item.gloss}."),
        ([h("teacher"), target(item), explain("օգտագործում է", "uses")], f"The teacher uses {item.gloss}."),
        ([target(item), h("bag_gen"), h("inside"), h("there_is")], f"The {item.gloss} is inside the bag."),
        ([h("i"), target(item), h("see")], f"I see {item.gloss}."),
        ([h("child"), target(item), explain("է ուզում", "wants")], f"The child wants {item.gloss}."),
        ([target(item), h("home"), h("there_is")], f"The {item.gloss} is at home."),
        ([h("this"), target(item), h("good"), h("is")], f"This {item.gloss} is good."),
    ]
    return choose_sentences(item, frames)


def transport_sentences(item: VocabItem) -> list[dict[str, object]]:
    return [
        sentence([h("i"), target(item), explain("օգտագործում եմ", "I use")], f"I use the {item.gloss}."),
        sentence([target(item), h("road_gen"), h("on"), h("there_is")], f"The {item.gloss} is on the road."),
        sentence([h("friend"), target(item), explain("սպասում է", "waits for")], f"A friend waits for the {item.gloss}."),
    ]


def animal_sentences(item: VocabItem) -> list[dict[str, object]]:
    frames = [
        ([target(item), h("yard"), h("inside"), h("there_is")], f"The {item.gloss} is in the yard."),
        ([h("child"), target(item), explain("դիտում է", "watches")], f"The child watches the {item.gloss}."),
        ([target(item), h("water"), explain("խմում է", "drinks")], f"The {item.gloss} drinks water."),
        ([target(item), h("picture"), h("inside"), h("there_is")], f"The {item.gloss} is in the picture."),
        ([h("friend"), target(item), h("see")], f"I see the {item.gloss} with a friend."),
        ([target(item), h("outside"), h("there_is")], f"The {item.gloss} is outside."),
    ]
    return choose_sentences(item, frames)


def nature_sentences(item: VocabItem) -> list[dict[str, object]]:
    frames = [
        ([h("today"), target(item), h("there_is")], f"I see the {item.gloss} today."),
        ([h("i"), target(item), h("see")], f"I see the {item.gloss}."),
        ([h("outside"), target(item), h("there_is")], f"The {item.gloss} is outside."),
        ([h("child"), target(item), explain("դիտում է", "watches")], f"The child watches the {item.gloss}."),
        ([h("picture"), h("on"), target(item), h("there_is")], f"I see the {item.gloss} in the picture."),
        ([target(item), h("near"), h("is")], f"The {item.gloss} is near."),
        ([h("we"), target(item), h("like")], f"We like the {item.gloss}."),
        ([target(item), h("outside"), h("good"), h("is")], f"The {item.gloss} outside is good."),
        ([h("friend"), target(item), explain("տեսնում է", "sees")], f"A friend sees the {item.gloss}."),
    ]
    return choose_sentences(item, frames)


def body_sentences(item: VocabItem) -> list[dict[str, object]]:
    frames = [
        ([h("doctor"), target(item), explain("ստուգում է", "checks")], f"The doctor checks the {item.gloss}."),
        ([h("picture"), h("on"), target(item), h("there_is")], f"There is a {item.gloss} in the picture."),
        ([h("child"), target(item), explain("դիպչում է", "touches")], f"The child touches the {item.gloss}."),
        ([target(item), h("clean"), h("is")], f"The {item.gloss} is clean."),
        ([h("teacher"), target(item), explain("ցույց է տալիս", "shows")], f"The teacher shows the {item.gloss}."),
        ([h("i"), target(item), explain("զգում եմ", "I feel")], f"I feel my {item.gloss}."),
    ]
    return choose_sentences(item, frames)


def verb_sentences(item: VocabItem) -> list[dict[str, object]]:
    if item.gloss in INVOLUNTARY_VERBS:
        frames = [
            ([h("child"), target(item), explain("չի ուզում", "does not want")], f"The child does not want to {item.gloss}."),
            ([h("doctor"), target(item), explain("չի ուզում", "does not want")], f"The doctor does not want to {item.gloss}."),
            ([h("today"), h("we"), target(item), explain("չենք ուզում", "we do not want")], f"Today we do not want to {item.gloss}."),
            ([h("friend"), target(item), explain("չի ուզում", "does not want")], f"A friend does not want to {item.gloss}."),
            ([h("teacher"), target(item), explain("չի ուզում", "does not want")], f"The teacher does not want to {item.gloss}."),
            ([h("home"), h("inside"), h("we"), target(item), explain("չենք ուզում", "we do not want")], f"At home, we do not want to {item.gloss}."),
        ]
        return choose_sentences(item, frames)
    if item.gloss in SENSITIVE_VERBS:
        frames = [
            ([h("child"), target(item), explain("չի ուզում", "does not want")], f"The child does not want to {item.gloss}."),
            ([h("teacher"), target(item), explain("չի թույլ տալիս", "does not allow")], f"The teacher does not allow anyone to {item.gloss}."),
            ([h("today"), h("we"), target(item), explain("չենք ուզում", "we do not want")], f"Today we do not want to {item.gloss}."),
            ([h("doctor"), target(item), explain("չի ուզում", "does not want")], f"The doctor does not want to {item.gloss}."),
            ([h("home"), h("inside"), target(item), explain("չի կարելի", "is not allowed")], f"It is not allowed to {item.gloss} at home."),
            ([h("school"), h("inside"), target(item), explain("չի կարելի", "is not allowed")], f"It is not allowed to {item.gloss} at school."),
        ]
        return choose_sentences(item, frames)

    frames = [
        ([h("i"), explain("ուզում եմ", "I want"), target(item)], f"I want to {item.gloss}."),
        ([h("you"), h("can"), target(item)], f"Can you {item.gloss}?", True),
        ([h("today"), h("we"), explain("ուզում ենք", "we want"), target(item)], f"Today we want to {item.gloss}."),
        ([h("teacher"), explain("ուզում է", "wants"), target(item)], f"The teacher wants to {item.gloss}."),
        ([h("friend"), explain("կարող է", "can"), target(item)], f"A friend can {item.gloss}."),
        ([h("school"), h("inside"), h("child"), explain("սովորում է", "learns"), target(item)], f"At school, the child learns to {item.gloss}."),
        ([h("child"), explain("սովորում է", "learns"), target(item)], f"The child learns to {item.gloss}."),
        ([h("now"), h("i"), explain("փորձում եմ", "I try"), target(item)], f"Now I try to {item.gloss}."),
        ([h("tomorrow"), h("we"), explain("կարող ենք", "we can"), target(item)], f"Tomorrow we can {item.gloss}."),
        ([h("lesson"), h("after"), h("we"), explain("ուզում ենք", "we want"), target(item)], f"After the lesson, we want to {item.gloss}."),
        ([h("home"), h("inside"), h("i"), explain("փորձում եմ", "I try"), target(item)], f"At home, I try to {item.gloss}."),
        ([h("market"), h("before"), h("i"), explain("ուզում եմ", "I want"), target(item)], f"Before the market, I want to {item.gloss}."),
    ]
    return choose_sentences(item, frames)


def phrase_sentences(item: VocabItem) -> list[dict[str, object]]:
    return [
        sentence([h("i"), target(item), h("say")], f"I say {item.gloss}."),
        sentence([h("friend"), target(item), explain("ասում է", "says")], f"A friend says {item.gloss}."),
        sentence([h("teacher"), target(item), explain("ասում է", "says")], f"The teacher says {item.gloss}."),
    ]


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
    }
    return dispatch.get(item.category, object_sentences)(item)


def write_batches(prefix: str, items: list[VocabItem], ranges: list[tuple[int, int]]) -> None:
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
    GENERATED.mkdir(parents=True, exist_ok=True)
    write_batches(
        "armenian",
        a1_items(),
        [(1, 50), (51, 100), (101, 150), (151, 200), (201, 250), (251, 300), (301, 350), (351, 400), (401, 450), (451, 500)],
    )
    write_batches(
        "armenian_swadesh",
        swadesh_items(),
        [(1, 41), (42, 83), (84, 124), (125, 165), (166, 207)],
    )


if __name__ == "__main__":
    main()
