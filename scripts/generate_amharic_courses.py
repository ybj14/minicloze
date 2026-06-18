#!/usr/bin/env python3
"""Generate reviewed Amharic A1 and Swadesh batch data for minicloze."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

from amharic_transliteration import romanize


ROOT = Path(__file__).resolve().parents[1]
CORPORA = ROOT / "minicloze-lib" / "corpora"
GENERATED = CORPORA / "generated"
USER_AGENT = {"User-Agent": "minicloze-amharic-course-builder/1.0"}

SWADESH_SOURCE = "Wiktionary Swadesh Amharic seed"
A1_SOURCE = "Codex-curated Amharic A1 seed list"

SWADESH_OVERRIDES = {
    2: "አንተ",
    3: "እሱ",
    30: "ወፍራም",
    98: "መንፋት",
    103: "ማወቅ",
    133: "ማሸት",
    138: "መስፋት",
    147: "ፀሐይ",
    202: "ውስጥ",
    203: "ጋር",
    205: "ከሆነ",
}


@dataclass(frozen=True)
class VocabItem:
    index: int
    word: str
    gloss: str
    category: str
    source: str


A1_EXTRAS: list[tuple[str, str, str]] = [
    ("ሰላም", "hello", "phrase"),
    ("እባክህ", "please", "phrase"),
    ("አመሰግናለሁ", "thank you", "phrase"),
    ("ይቅርታ", "sorry", "phrase"),
    ("እሺ", "okay", "phrase"),
    ("አዎ", "yes", "phrase"),
    ("አይ", "no", "phrase"),
    ("ደህና", "well", "adjective"),
    ("ደስ", "joy", "noun"),
    ("እንኳን", "welcome", "phrase"),
    ("ጓደኛ", "friend", "person"),
    ("ቤተሰብ", "family", "person"),
    ("አያት", "grandparent", "person"),
    ("አጎት", "uncle", "person"),
    ("አክስት", "aunt", "person"),
    ("ባል", "husband", "person"),
    ("ሚስት", "wife", "person"),
    ("ጎረቤት", "neighbor", "person"),
    ("አስተማሪ", "teacher", "person"),
    ("ተማሪ", "student", "person"),
    ("ሐኪም", "doctor", "person"),
    ("ነርስ", "nurse", "person"),
    ("ፖሊስ", "police officer", "person"),
    ("ሾፌር", "driver", "person"),
    ("ሰራተኛ", "worker", "person"),
    ("ሻጭ", "seller", "person"),
    ("ደንበኛ", "customer", "person"),
    ("እንግዳ", "guest", "person"),
    ("ቤት", "house", "place"),
    ("ትምህርት ቤት", "school", "place"),
    ("ገበያ", "market", "place"),
    ("ሱቅ", "shop", "place"),
    ("መንገድ", "road", "place"),
    ("ከተማ", "city", "place"),
    ("መንደር", "village", "place"),
    ("ሆቴል", "hotel", "place"),
    ("ባንክ", "bank", "place"),
    ("ሆስፒታል", "hospital", "place"),
    ("መድኃኒት ቤት", "pharmacy", "place"),
    ("መናፈሻ", "park", "place"),
    ("ማቆሚያ", "stop", "place"),
    ("ጣቢያ", "station", "place"),
    ("ቢሮ", "office", "place"),
    ("ምግብ ቤት", "restaurant", "place"),
    ("ካፌ", "cafe", "place"),
    ("ሙዚየም", "museum", "place"),
    ("ቤተ መጻሕፍት", "library", "place"),
    ("ክፍል", "room", "place"),
    ("መኝታ ክፍል", "bedroom", "place"),
    ("ወጥ ቤት", "kitchen", "place"),
    ("መታጠቢያ ቤት", "bathroom", "place"),
    ("ግቢ", "yard", "place"),
    ("ዛሬ", "today", "time"),
    ("ነገ", "tomorrow", "time"),
    ("ትናንት", "yesterday", "time"),
    ("አሁን", "now", "time"),
    ("ጠዋት", "morning", "time"),
    ("ከሰዓት", "afternoon", "time"),
    ("ማታ", "evening", "time"),
    ("ሌሊት", "night", "time"),
    ("ሳምንት", "week", "time"),
    ("ወር", "month", "time"),
    ("ዓመት", "year", "time"),
    ("ሰዓት", "hour", "time"),
    ("ደቂቃ", "minute", "time"),
    ("ቅዳሜ", "Saturday", "time"),
    ("እሁድ", "Sunday", "time"),
    ("ሰኞ", "Monday", "time"),
    ("ማክሰኞ", "Tuesday", "time"),
    ("ረቡዕ", "Wednesday", "time"),
    ("ሐሙስ", "Thursday", "time"),
    ("አርብ", "Friday", "time"),
    ("ዳቦ", "bread", "food"),
    ("ቡና", "coffee", "drink"),
    ("ሻይ", "tea", "drink"),
    ("ወተት", "milk", "drink"),
    ("ስኳር", "sugar", "food"),
    ("ሩዝ", "rice", "food"),
    ("ፓስታ", "pasta", "food"),
    ("እንጀራ", "injera", "food"),
    ("ወጥ", "stew", "food"),
    ("ሾርባ", "soup", "food"),
    ("እንቁላል", "egg", "food"),
    ("አትክልት", "vegetables", "food"),
    ("ፍራፍሬ", "fruit", "food"),
    ("ሙዝ", "banana", "food"),
    ("ብርቱካን", "orange", "food"),
    ("ፖም", "apple", "food"),
    ("ድንች", "potato", "food"),
    ("ቲማቲም", "tomato", "food"),
    ("ሽንኩርት", "onion", "food"),
    ("ቅቤ", "butter", "food"),
    ("ማር", "honey", "food"),
    ("ምሳ", "lunch", "food"),
    ("ቁርስ", "breakfast", "food"),
    ("እራት", "dinner", "food"),
    ("መጽሐፍ", "book", "object"),
    ("ደብተር", "notebook", "object"),
    ("ብዕር", "pen", "object"),
    ("እርሳስ", "pencil", "object"),
    ("ጠረጴዛ", "table", "object"),
    ("ወንበር", "chair", "object"),
    ("አልጋ", "bed", "object"),
    ("በር", "door", "object"),
    ("መስኮት", "window", "object"),
    ("ቁልፍ", "key", "object"),
    ("ስልክ", "phone", "object"),
    ("ኮምፒውተር", "computer", "object"),
    ("ቴሌቪዥን", "television", "object"),
    ("ሬዲዮ", "radio", "object"),
    ("ቦርሳ", "bag", "object"),
    ("ልብስ", "clothes", "object"),
    ("ጫማ", "shoes", "object"),
    ("ቆብ", "hat", "object"),
    ("ሸሚዝ", "shirt", "object"),
    ("ሱሪ", "pants", "object"),
    ("ቀሚስ", "dress", "object"),
    ("ጃኬት", "jacket", "object"),
    ("ገንዘብ", "money", "object"),
    ("ብር", "birr", "object"),
    ("ትኬት", "ticket", "object"),
    ("ካርታ", "map", "object"),
    ("ስጦታ", "gift", "object"),
    ("ሳጥን", "box", "object"),
    ("ሳሙና", "soap", "object"),
    ("ፎጣ", "towel", "object"),
    ("መስታወት", "mirror", "object"),
    ("ጽዋ", "cup", "object"),
    ("ሳህን", "plate", "object"),
    ("ማንኪያ", "spoon", "object"),
    ("ቢላዋ", "knife", "object"),
    ("ሹካ", "fork", "object"),
    ("ትምህርት", "lesson", "object"),
    ("ሥራ", "work", "object"),
    ("የቤት ሥራ", "homework", "object"),
    ("ፈተና", "exam", "object"),
    ("ጥያቄ", "question", "object"),
    ("መልስ", "answer", "object"),
    ("ቁጥር", "number", "object"),
    ("ፊደል", "letter", "object"),
    ("ቋንቋ", "language", "object"),
    ("አማርኛ", "Amharic", "object"),
    ("እንግሊዝኛ", "English", "object"),
    ("ታሪክ", "history", "object"),
    ("ሂሳብ", "math", "object"),
    ("ሙዚቃ", "music", "object"),
    ("ስዕል", "picture", "object"),
    ("ፎቶ", "photo", "object"),
    ("ጨዋታ", "game", "object"),
    ("መልእክት", "message", "object"),
    ("ዜና", "news", "object"),
    ("መኪና", "car", "transport"),
    ("አውቶቡስ", "bus", "transport"),
    ("ባቡር", "train", "transport"),
    ("ታክሲ", "taxi", "transport"),
    ("ብስክሌት", "bicycle", "transport"),
    ("አውሮፕላን", "airplane", "transport"),
    ("ጀልባ", "boat", "transport"),
    ("ጉዞ", "trip", "transport"),
    ("ጨረቃ", "moon", "nature"),
    ("ኮከብ", "star", "nature"),
    ("ሰማይ", "sky", "nature"),
    ("ዝናብ", "rain", "nature"),
    ("ነፋስ", "wind", "nature"),
    ("ደመና", "cloud", "nature"),
    ("በረዶ", "snow", "nature"),
    ("ሙቀት", "heat", "nature"),
    ("ብርድ", "cold", "nature"),
    ("ወንዝ", "river", "nature"),
    ("ተራራ", "mountain", "nature"),
    ("ሀይቅ", "lake", "nature"),
    ("ባሕር", "sea", "nature"),
    ("አበባ", "flower", "nature"),
    ("ሣር", "grass", "nature"),
    ("ድንጋይ", "stone", "nature"),
    ("አፈር", "soil", "nature"),
    ("አየር", "air", "nature"),
    ("ድመት", "cat", "animal"),
    ("ፈረስ", "horse", "animal"),
    ("ላም", "cow", "animal"),
    ("በግ", "sheep", "animal"),
    ("ፍየል", "goat", "animal"),
    ("ዶሮ", "chicken", "animal"),
    ("አሳማ", "pig", "animal"),
    ("አንበሳ", "lion", "animal"),
    ("ዝሆን", "elephant", "animal"),
    ("ፊት", "face", "body"),
    ("ጀርባ", "back", "body"),
    ("ጥርስ", "tooth", "body"),
    ("ጤና", "health", "body"),
    ("ህመም", "pain", "body"),
    ("መድኃኒት", "medicine", "body"),
    ("ድካም", "tiredness", "body"),
    ("ሰማያዊ", "blue", "color"),
    ("አረንጓዴ", "green", "color"),
    ("ቢጫ", "yellow", "color"),
    ("ቡናማ", "brown", "color"),
    ("ግራጫ", "gray", "color"),
    ("ጥሩ", "good", "adjective"),
    ("መጥፎ", "bad", "adjective"),
    ("አዲስ", "new", "adjective"),
    ("አሮጌ", "old", "adjective"),
    ("ቆንጆ", "beautiful", "adjective"),
    ("ቀላል", "easy", "adjective"),
    ("ፈጣን", "fast", "adjective"),
    ("ዘገምተኛ", "slow", "adjective"),
    ("ሞቃት", "warm", "adjective"),
    ("ቀዝቃዛ", "cold", "adjective"),
    ("ውድ", "expensive", "adjective"),
    ("ርካሽ", "cheap", "adjective"),
    ("ንጹሕ", "clean", "adjective"),
    ("ቆሻሻ", "dirty", "adjective"),
    ("ደስተኛ", "happy", "adjective"),
    ("ያዘነ", "sad", "adjective"),
    ("ዝግጁ", "ready", "adjective"),
    ("ታማሚ", "sick", "adjective"),
    ("ጠንካራ", "strong", "adjective"),
    ("ደካማ", "weak", "adjective"),
    ("መሄድ", "go", "verb"),
    ("መምጣት", "come", "verb"),
    ("ማንበብ", "read", "verb"),
    ("መጻፍ", "write", "verb"),
    ("መማር", "learn", "verb"),
    ("ማስተማር", "teach", "verb"),
    ("መሥራት", "work", "verb"),
    ("መግዛት", "buy", "verb"),
    ("መሸጥ", "sell", "verb"),
    ("መክፈት", "open", "verb"),
    ("መዝጋት", "close", "verb"),
    ("መነሳት", "get up", "verb"),
    ("መሮጥ", "run", "verb"),
    ("መራመድ", "walk", "verb"),
    ("ማልቀስ", "cry", "verb"),
    ("መርዳት", "help", "verb"),
    ("መጠየቅ", "ask", "verb"),
    ("መመለስ", "answer", "verb"),
    ("መፈለግ", "want", "verb"),
    ("መውደድ", "like", "verb"),
    ("መቻል", "can", "verb"),
    ("መውሰድ", "take", "verb"),
    ("ማምጣት", "bring", "verb"),
    ("መላክ", "send", "verb"),
    ("መጠበቅ", "wait", "verb"),
    ("መጀመር", "start", "verb"),
    ("መጨረስ", "finish", "verb"),
    ("መታጠብ", "wash oneself", "verb"),
    ("ማዘጋጀት", "prepare", "verb"),
    ("ማብሰል", "cook", "verb"),
    ("መተርጎም", "translate", "verb"),
    ("መምረጥ", "choose", "verb"),
    ("መለወጥ", "change", "verb"),
    ("መፈረም", "sign", "verb"),
    ("መክፈል", "pay", "verb"),
    ("መጠቀም", "use", "verb"),
    ("መፈተሽ", "check", "verb"),
    ("መደወል", "call", "verb"),
    ("መጠገን", "fix", "verb"),
    ("ማጽዳት", "clean", "verb"),
    ("ማድረግ", "do", "verb"),
    ("ወይም", "or", "function"),
    ("ግን", "but", "function"),
    ("ከ", "from", "function"),
    ("ወደ", "to", "function"),
    ("በ", "in", "function"),
    ("ለ", "for", "function"),
    ("ስለ", "about", "function"),
    ("እንደ", "like", "function"),
    ("በፊት", "before", "function"),
    ("በኋላ", "after", "function"),
    ("ታች", "under", "function"),
    ("አጠገብ", "near", "function"),
    ("መካከል", "between", "function"),
    ("ያለ", "without", "function"),
    ("ጥር", "January", "time"),
    ("የካቲት", "February", "time"),
    ("መጋቢት", "March", "time"),
    ("ሚያዝያ", "April", "time"),
    ("ግንቦት", "May", "time"),
    ("ሰኔ", "June", "time"),
    ("ሐምሌ", "July", "time"),
    ("ነሐሴ", "August", "time"),
    ("መስከረም", "September", "time"),
    ("ጥቅምት", "October", "time"),
    ("ኅዳር", "November", "time"),
    ("ታኅሣሥ", "December", "time"),
    ("ሰሜን", "north", "place"),
    ("ደቡብ", "south", "place"),
    ("ምስራቅ", "east", "place"),
    ("ምዕራብ", "west", "place"),
    ("ድልድይ", "bridge", "place"),
    ("ቤተክርስቲያን", "church", "place"),
    ("መስጊድ", "mosque", "place"),
    ("አደባባይ", "square", "place"),
    ("ፋብሪካ", "factory", "place"),
    ("ዩኒቨርሲቲ", "university", "place"),
    ("መንግሥት ቤት", "government office", "place"),
    ("ወረቀት", "paper", "object"),
    ("ገጽ", "page", "object"),
    ("መስመር", "line", "object"),
    ("ዋጋ", "price", "object"),
    ("ሰነድ", "document", "object"),
    ("ፈቃድ", "permission", "object"),
    ("ቀጠሮ", "appointment", "object"),
    ("መብራት", "light", "object"),
    ("ባትሪ", "battery", "object"),
    ("መቀስ", "scissors", "object"),
    ("መነጽር", "glasses", "object"),
    ("ካሜራ", "camera", "object"),
    ("ድምፅ", "sound", "object"),
    ("አድራሻ", "address", "object"),
    ("ፖስታ", "mail", "object"),
    ("የልደት ቀን", "birthday", "time"),
    ("በዓል", "holiday", "time"),
    ("ሙሉ", "full", "adjective"),
    ("ባዶ", "empty", "adjective"),
    ("ጣፋጭ", "sweet", "adjective"),
    ("መራራ", "bitter", "adjective"),
    ("ትኩስ", "hot", "adjective"),
    ("ትክክለኛ", "correct", "adjective"),
    ("ዝምተኛ", "quiet", "adjective"),
    ("ድምፃማ", "loud", "adjective"),
    ("ጠቃሚ", "useful", "adjective"),
    ("አስፈላጊ", "important", "adjective"),
    ("ትከሻ", "shoulder", "body"),
    ("ጣት", "finger", "body"),
    ("ክንድ", "arm", "body"),
    ("አፍንጫ", "nose", "body"),
    ("መዳፍ", "palm", "body"),
    ("ማስታወስ", "remember", "verb"),
    ("መርሳት", "forget", "verb"),
    ("መቀበል", "receive", "verb"),
    ("መጠራት", "be called", "verb"),
    ("መሸከም", "carry", "verb"),
    ("መተው", "leave", "verb"),
    ("መቆየት", "stay", "verb"),
    ("መጠንቀቅ", "be careful", "verb"),
    ("መፍቀድ", "allow", "verb"),
    ("መቃወም", "refuse", "verb"),
    ("ማግኘት", "find", "verb"),
    ("ማጣት", "lose", "verb"),
    ("መለካት", "measure", "verb"),
    ("ማብራት", "turn on", "verb"),
    ("ማጥፋት", "turn off", "verb"),
    ("መቀየር", "change", "verb"),
]

COMMON = {
    "i": ("እኔ", "I"),
    "you": ("አንተ", "you"),
    "we": ("እኛ", "we"),
    "child": ("ልጅ", "child"),
    "teacher": ("አስተማሪ", "teacher"),
    "doctor": ("ሐኪም", "doctor"),
    "mother": ("እናት", "mother"),
    "friend": ("ጓደኛ", "friend"),
    "today": ("ዛሬ", "today"),
    "tomorrow": ("ነገ", "tomorrow"),
    "now": ("አሁን", "now"),
    "morning": ("ጠዋት", "morning"),
    "evening": ("ማታ", "evening"),
    "here": ("እዚህ", "here"),
    "there": ("እዚያ", "there"),
    "this": ("ይህ", "this"),
    "that": ("ያ", "that"),
    "home": ("ቤት", "home"),
    "school": ("ትምህርት ቤት", "school"),
    "market": ("ገበያ", "market"),
    "room": ("ክፍል", "room"),
    "yard": ("ግቢ", "yard"),
    "outside": ("ውጭ", "outside"),
    "coffee": ("ቡና", "coffee"),
    "tea": ("ሻይ", "tea"),
    "water": ("ውሃ", "water"),
    "book": ("መጽሐፍ", "book"),
    "question": ("ጥያቄ", "question"),
    "bag": ("ቦርሳ", "bag"),
    "table": ("ጠረጴዛ", "table"),
    "chair": ("ወንበር", "chair"),
    "bed": ("አልጋ", "bed"),
    "cup": ("ጽዋ", "cup"),
    "picture": ("ስዕል", "picture"),
    "door": ("በር", "door"),
    "road": ("መንገድ", "road"),
    "cat": ("ድመት", "cat"),
    "gift": ("ስጦታ", "gift"),
    "lesson": ("ትምህርት", "lesson"),
    "trip": ("ጉዞ", "trip"),
    "sugar": ("ስኳር", "sugar"),
    "apple": ("ፖም", "apple"),
    "sound": ("ድምፅ", "sound"),
    "music": ("ሙዚቃ", "music"),
    "work": ("ሥራ", "work"),
    "is": ("ነው", "is"),
    "are": ("ናቸው", "are"),
    "have": ("አለኝ", "I have"),
    "there_is": ("አለ", "there is"),
    "want": ("እፈልጋለሁ", "I want"),
    "like": ("እወዳለሁ", "I like"),
    "see": ("አያለሁ", "I see"),
    "bring": ("አመጣ", "brought"),
    "drink": ("እጠጣለሁ", "I drink"),
    "eat": ("እበላለሁ", "I eat"),
    "go": ("እሄዳለሁ", "I go"),
    "come": ("እመጣለሁ", "I come"),
    "learn": ("እንማራለን", "we learn"),
    "say": ("እላለሁ", "I say"),
    "can": ("ትችላለህ", "you can"),
    "good": ("ጥሩ", "good"),
    "clean": ("ንጹሕ", "clean"),
    "near": ("ቅርብ", "near"),
    "inside": ("ውስጥ", "inside"),
    "on": ("ላይ", "on"),
    "to": ("ወደ", "to"),
    "with": ("ጋር", "with"),
    "and": ("እና", "and"),
    "before": ("በፊት", "before"),
    "after": ("በኋላ", "after"),
}

QUESTION_SENTENCES = {
    "who": [
        (["x", "came"], "Who came?"),
        (["x", "here", "there_is"], "Who is here?"),
        (["teacher", "x", "sees"], "Whom does the teacher see?"),
    ],
    "what": [
        (["you", "x", "you_want"], "What do you want?"),
        (["x", "table", "on", "there_is"], "What is on the table?"),
        (["friend", "x", "bring"], "What did the friend bring?"),
    ],
    "where": [
        (["you", "to", "x", "you_go"], "Where are you going?"),
        (["book", "x", "there_is"], "Where is the book?"),
        (["teacher", "x", "will_come"], "Where will the teacher come?"),
    ],
    "when": [
        (["you", "x", "you_come"], "When will you come?"),
        (["we", "x", "learn"], "When do we study?"),
        (["market", "x", "there_is"], "When is the market?"),
    ],
    "how": [
        (["you", "x", "you_go"], "How do you go?"),
        (["we", "x", "learn"], "How do we study?"),
        (["x", "water", "i_drink"], "How do I drink water?"),
    ],
}

PRONOUN_FORMS = {
    "እኔ": ("ነኝ", "am", "I"),
    "አንተ": ("ነህ", "are", "you"),
    "አንቺ": ("ነሽ", "are", "you"),
    "እሱ": ("ነው", "is", "he"),
    "እሷ": ("ናት", "is", "she"),
    "እኛ": ("ነን", "are", "we"),
    "እናንተ": ("ናችሁ", "are", "you all"),
    "እነርሱ": ("ናቸው", "are", "they"),
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
    "injera",
    "stew",
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
    "lunch",
    "breakfast",
    "dinner",
    "salt",
    "sugar",
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
    "from",
    "to",
    "for",
    "about",
    "like",
    "before",
    "after",
    "under",
    "near",
    "between",
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
        terms = [term for term in terms if term]
        if terms:
            rows[int(match.group(1))] = terms
    return rows


def clean_term(term: str) -> str:
    term = re.sub(r"<notes:[^>]+>", "", term)
    term = re.sub(r"\(.*?\)", "", term)
    term = term.replace("….", " ").replace("...", " ").replace("…", " ")
    term = term.replace("ዉ", "ው")
    term = re.sub(r"\s+", " ", term)
    return term.strip().strip("።፣፤፥፦፧,.;:?!")


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
    if index is not None and 36 <= index <= 45:
        return "person"
    if index is not None and 46 <= index <= 50:
        return "animal"
    if index is not None and 51 <= index <= 61:
        return "nature"
    if index is not None and 62 <= index <= 91:
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
        amharic = parse_swadesh_module("am")
    except Exception:
        cached = CORPORA / "amharic_swadesh_vocab.json"
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
        word = SWADESH_OVERRIDES.get(index) or amharic[index][0]
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
    item = {
        "word": word,
        "gloss": gloss,
        "transliteration": romanize(word),
    }
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
    punctuation = "?" if question else "።"
    return {
        "target": f"{target_text}{punctuation}",
        "text": english,
        "words": words,
    }


def token_from_key(key: str, item: VocabItem) -> dict[str, str]:
    if key == "x":
        return target(item)
    if key == "came":
        return explain("መጣ", "came")
    if key == "sees":
        return explain("ያያል", "sees")
    if key == "you_want":
        return explain("ትፈልጋለህ", "you want")
    if key == "you_go":
        return explain("ትሄዳለህ", "you go")
    if key == "will_come":
        return explain("ይመጣል", "will come")
    if key == "you_come":
        return explain("ትመጣለህ", "you come")
    if key == "i_drink":
        return explain("እጠጣለሁ", "I drink")
    return h(key)


def from_keys(keys: list[str], item: VocabItem, english: str, question: bool = False) -> dict[str, object]:
    return sentence([token_from_key(key, item) for key in keys], english, question)


def choose_sentences(item: VocabItem, frames: list[tuple[list[dict[str, str]], str] | tuple[list[dict[str, str]], str, bool]]) -> list[dict[str, object]]:
    start = (item.index * 3) % len(frames)
    chosen = [frames[(start + offset) % len(frames)] for offset in range(3)]
    return [
        sentence(frame[0], frame[1], frame[2] if len(frame) > 2 else False)
        for frame in chosen
    ]


def pronoun_sentences(item: VocabItem) -> list[dict[str, object]]:
    verb, verb_gloss, english_subject = PRONOUN_FORMS.get(item.word, ("ነው", "is", item.gloss))
    subject = english_subject[0].upper() + english_subject[1:]
    return [
        sentence([target(item), h("here"), explain(verb, verb_gloss)], f"{subject} {verb_gloss} here."),
        sentence([target(item), explain("ተማሪ", "student"), explain(verb, verb_gloss)], f"{subject} {verb_gloss} a student."),
        sentence([target(item), explain("ደህና", "well"), explain(verb, verb_gloss)], f"{subject} {verb_gloss} well."),
    ]


def question_sentences(item: VocabItem) -> list[dict[str, object]]:
    frames = QUESTION_SENTENCES.get(item.gloss.lower())
    if frames:
        return [from_keys(keys, item, english, True) for keys, english in frames]
    return [
        sentence([target(item), h("here"), h("is")], f"{item.gloss.title()} is here?"),
        sentence([h("you"), target(item), h("want")], f"Do you want {item.gloss}?", True),
        sentence([h("teacher"), target(item), h("see")], f"Does the teacher see {item.gloss}?", True),
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
        sentence([target(item), h("bag"), h("table"), h("on"), h("there_is")], f"{item.gloss.title()} bag is on the table."),
    ]


def negation_sentences(item: VocabItem) -> list[dict[str, object]]:
    return [
        sentence([h("this"), h("book"), target(item)], "This is not a book."),
        sentence([h("i"), h("coffee"), target(item), explain("አልፈልግም", "I do not want")], "I do not want coffee."),
        sentence([h("today"), h("school"), target(item)], "There is no school today."),
    ]


def function_sentences(item: VocabItem) -> list[dict[str, object]]:
    g = item.gloss.lower()
    if g == "and":
        frames = [
            ([h("coffee"), target(item), h("water"), h("want")], "I want coffee and water."),
            ([h("mother"), target(item), h("friend"), explain("መጡ", "came")], "Mother and a friend came."),
            ([h("book"), target(item), h("bag"), h("table"), h("on"), h("there_is")], "The book and bag are on the table."),
        ]
    elif g == "or":
        frames = [
            ([h("coffee"), target(item), h("tea"), h("want")], "I want coffee or tea."),
            ([h("home"), target(item), h("market"), h("go")], "I go home or to the market."),
            ([h("book"), target(item), h("bag"), h("bring")], "Bring the book or the bag."),
        ]
    elif g == "but":
        frames = [
            ([h("coffee"), h("want"), target(item), h("water"), h("drink")], "I want coffee but drink water."),
            ([h("today"), h("good"), target(item), explain("ቀዝቃዛ", "cold"), h("is")], "Today is good but cold."),
            ([h("friend"), explain("መጣ", "came"), target(item), h("teacher"), explain("አልመጣም", "did not come")], "A friend came, but the teacher did not come."),
        ]
    elif g == "because":
        frames = [
            ([h("water"), h("drink"), target(item), explain("ሞቃት", "hot"), h("is")], "I drink water because it is hot."),
            ([h("home"), h("go"), target(item), explain("ደክሞኛል", "I am tired")], "I go home because I am tired."),
            ([h("book"), h("want"), target(item), h("learn")], "I want a book because we study."),
        ]
    elif g == "if":
        frames = [
            ([target(item), h("water"), h("there_is"), h("coffee"), h("drink")], "If there is water, I drink coffee."),
            ([target(item), h("teacher"), explain("ይመጣል", "comes"), h("we"), h("learn")], "If the teacher comes, we study."),
            ([target(item), h("market"), h("near"), h("is"), h("i"), h("go")], "If the market is near, I go."),
        ]
    elif g == "from":
        frames = [
            ([h("i"), target(item), h("home"), h("come")], "I come from home."),
            ([h("friend"), target(item), h("market"), explain("ይመጣል", "comes")], "A friend comes from the market."),
            ([h("teacher"), target(item), h("school"), explain("ይመጣል", "comes")], "The teacher comes from school."),
        ]
    elif g == "to":
        frames = [
            ([h("i"), target(item), h("home"), h("go")], "I go home."),
            ([h("friend"), target(item), h("market"), explain("ይሄዳል", "goes")], "A friend goes to the market."),
            ([h("teacher"), target(item), h("school"), explain("ይሄዳል", "goes")], "The teacher goes to school."),
        ]
    elif g in {"in", "at"}:
        frames = [
            ([h("book"), h("bag"), target(item), h("there_is")], "The book is in the bag."),
            ([h("friend"), h("home"), target(item), h("there_is")], "A friend is at home."),
            ([h("teacher"), h("school"), target(item), h("there_is")], "The teacher is at school."),
        ]
    elif g == "with":
        frames = [
            ([h("i"), h("friend"), target(item), h("go")], "I go with a friend."),
            ([h("teacher"), h("child"), target(item), explain("ይማራል", "studies")], "The teacher studies with the child."),
            ([h("coffee"), h("sugar"), target(item), h("is")], "The coffee is with sugar."),
        ]
    elif g == "for":
        frames = [
            ([h("this"), h("book"), target(item), h("friend"), h("is")], "This book is for a friend."),
            ([h("coffee"), target(item), h("teacher"), h("is")], "The coffee is for the teacher."),
            ([h("gift"), target(item), h("mother"), h("is")], "The gift is for mother."),
        ]
    elif g == "about":
        frames = [
            ([h("i"), target(item), h("book"), explain("እናገራለሁ", "I speak")], "I speak about the book."),
            ([h("teacher"), target(item), h("lesson"), explain("ይናገራል", "speaks")], "The teacher speaks about the lesson."),
            ([h("friend"), target(item), h("trip"), explain("ይጠይቃል", "asks")], "A friend asks about the trip."),
        ]
    elif g == "like":
        frames = [
            ([h("child"), target(item), h("teacher"), explain("ይናገራል", "speaks")], "The child speaks like the teacher."),
            ([h("this"), h("bag"), target(item), h("book"), h("is")], "This bag is like a book."),
            ([h("friend"), target(item), h("mother"), explain("ይረዳል", "helps")], "A friend helps like mother."),
        ]
    elif g == "before":
        frames = [
            ([target(item), h("school"), h("i"), h("coffee"), h("drink")], "Before school, I drink coffee."),
            ([target(item), h("market"), h("friend"), explain("ይመጣል", "comes")], "Before the market, a friend comes."),
            ([target(item), h("lesson"), h("we"), h("book"), explain("እናነባለን", "we read")], "Before the lesson, we read a book."),
        ]
    elif g == "after":
        frames = [
            ([h("school"), target(item), h("i"), h("home"), h("go")], "After school, I go home."),
            ([h("market"), target(item), h("friend"), h("coffee"), explain("ይጠጣል", "drinks")], "After the market, a friend drinks coffee."),
            ([h("lesson"), target(item), h("we"), h("book"), explain("እናነባለን", "we read")], "After the lesson, we read a book."),
        ]
    elif g == "on":
        frames = [
            ([h("book"), h("table"), target(item), h("there_is")], "The book is on the table."),
            ([h("cup"), h("table"), target(item), h("there_is")], "The cup is on the table."),
            ([h("bag"), h("chair"), target(item), h("there_is")], "The bag is on the chair."),
        ]
    elif g == "under":
        frames = [
            ([h("book"), h("table"), target(item), h("there_is")], "The book is under the table."),
            ([h("bag"), h("chair"), target(item), h("there_is")], "The bag is under the chair."),
            ([h("cat"), h("bed"), target(item), h("there_is")], "The cat is under the bed."),
        ]
    elif g == "near":
        frames = [
            ([h("school"), target(item), h("market"), h("there_is")], "The school is near the market."),
            ([h("home"), target(item), h("road"), h("there_is")], "The house is near the road."),
            ([h("friend"), target(item), h("door"), h("there_is")], "A friend is near the door."),
        ]
    elif g == "between":
        frames = [
            ([h("book"), h("cup"), target(item), h("there_is")], "The book is between the cups."),
            ([h("school"), h("market"), target(item), h("there_is")], "The school is between the market and home."),
            ([h("friend"), h("teacher"), target(item), h("there_is")], "A friend is between the teacher and mother."),
        ]
    elif g == "without":
        frames = [
            ([h("i"), target(item), h("sugar"), h("coffee"), h("drink")], "I drink coffee without sugar."),
            ([h("friend"), target(item), h("book"), h("school"), explain("ይሄዳል", "goes")], "A friend goes to school without a book."),
            ([h("teacher"), target(item), h("coffee"), explain("ይመጣል", "comes")], "The teacher comes without coffee."),
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
        ([h("table"), h("on"), target(item), h("cup"), h("there_is")], f"There are {item.gloss} cups on the table."),
        ([h("teacher"), target(item), h("question"), explain("ጠየቀ", "asked")], f"The teacher asked {item.gloss} {question}."),
        ([h("child"), target(item), h("apple"), explain("አመጣ", "brought")], f"The child brought {item.gloss} apples."),
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
    nouns = [h("bag"), h("room"), h("book")]
    frames = [
        ([nouns[0], target(item), h("is")], f"The bag is {item.gloss}."),
        ([h("this"), h("lesson"), target(item), h("is")], f"This lesson is {item.gloss}."),
        ([h("this"), nouns[2], target(item), h("is")], f"This book is {item.gloss}."),
        ([nouns[1], target(item), h("is")], f"The room is {item.gloss}."),
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
        sentence([h("this"), explain("ቀሚስ", "dress"), target(item), h("is")], f"This dress is {item.gloss}."),
        sentence([target(item), explain("ቀለም", "color"), h("like")], f"I like the color {item.gloss}."),
    ]


def person_sentences(item: VocabItem) -> list[dict[str, object]]:
    frames = [
        ([target(item), h("home"), h("there_is")], f"The {item.gloss} is at home."),
        ([h("i"), target(item), h("see")], f"I see the {item.gloss}."),
        ([target(item), h("coffee"), explain("ይጠጣል", "drinks")], f"The {item.gloss} drinks coffee."),
        ([target(item), h("market"), explain("ይሄዳል", "goes")], f"The {item.gloss} goes to the market."),
        ([target(item), h("book"), explain("ያነባል", "reads")], f"The {item.gloss} reads a book."),
        ([target(item), h("child"), explain("ይረዳል", "helps")], f"The {item.gloss} helps the child."),
        ([h("teacher"), target(item), h("with"), explain("ይናገራል", "speaks")], f"The teacher speaks with the {item.gloss}."),
        ([target(item), h("school"), h("inside"), h("there_is")], f"The {item.gloss} is inside the school."),
        ([h("friend"), target(item), explain("ይጠብቃል", "waits for")], f"A friend waits for the {item.gloss}."),
    ]
    return choose_sentences(item, frames)


def place_sentences(item: VocabItem) -> list[dict[str, object]]:
    frames = [
        ([h("i"), h("to"), target(item), h("go")], f"I go to the {item.gloss}."),
        ([target(item), h("near"), h("is")], f"The {item.gloss} is near."),
        ([h("friend"), target(item), h("inside"), h("there_is")], f"A friend is inside the {item.gloss}."),
        ([h("teacher"), h("to"), target(item), explain("ይሄዳል", "goes")], f"The teacher goes to the {item.gloss}."),
        ([target(item), h("road"), h("near"), h("there_is")], f"The {item.gloss} is near the road."),
        ([h("i"), target(item), h("see")], f"I see the {item.gloss}."),
        ([h("friend"), target(item), explain("ይጠብቃል", "waits at")], f"A friend waits at the {item.gloss}."),
        ([h("this"), target(item), h("good"), h("is")], f"This {item.gloss} is good."),
        ([target(item), h("market"), h("near"), h("there_is")], f"The {item.gloss} is near the market."),
    ]
    return choose_sentences(item, frames)


def time_sentences(item: VocabItem) -> list[dict[str, object]]:
    if item.gloss.lower() in MONTHS:
        return [
            sentence([explain("በ", "in"), target(item), h("i"), h("come")], f"I come in {item.gloss}."),
            sentence([explain("በ", "in"), target(item), h("we"), h("learn")], f"We study in {item.gloss}."),
            sentence([explain("በ", "in"), target(item), h("market"), h("go")], f"I go to the market in {item.gloss}."),
        ]
    return [
        sentence([target(item), h("i"), h("come")], f"I come {item.gloss}."),
        sentence([target(item), h("we"), h("learn")], f"We study {item.gloss}."),
        sentence([target(item), h("market"), h("go")], f"I go to the market {item.gloss}."),
    ]


def food_sentences(item: VocabItem) -> list[dict[str, object]]:
    action = h("drink") if item.category == "drink" or item.gloss in DRINKS else h("eat")
    consume = "drink" if action["word"] == "እጠጣለሁ" else "eat"
    third = explain("ይጠጣል", "drinks") if consume == "drink" else explain("ይበላል", "eats")
    frames = [
        ([h("i"), target(item), action], f"I {consume} {item.gloss}."),
        ([h("mother"), target(item), explain("ታዘጋጃለች", "prepares")], f"Mother prepares {item.gloss}."),
        ([h("market"), target(item), h("there_is")], f"There is {item.gloss} at the market."),
        ([h("friend"), target(item), h("want")], f"I want {item.gloss} for a friend."),
        ([target(item), h("table"), h("on"), h("there_is")], f"The {item.gloss} is on the table."),
        ([h("child"), target(item), third], f"The child {consume}s {item.gloss}."),
    ]
    return choose_sentences(item, frames)


def object_sentences(item: VocabItem) -> list[dict[str, object]]:
    if item.gloss == "name":
        return [
            sentence([h("i"), target(item), explain("እጽፋለሁ", "I write")], "I write my name."),
            sentence([target(item), h("book"), h("on"), h("there_is")], "The name is on the book."),
            sentence([h("teacher"), target(item), explain("ይጠይቃል", "asks")], "The teacher asks for the name."),
        ]
    frames = [
        ([h("i"), target(item), h("want")], f"I want {item.gloss}."),
        ([target(item), h("table"), h("on"), h("there_is")], f"The {item.gloss} is on the table."),
        ([h("friend"), target(item), h("bring")], f"A friend brought {item.gloss}."),
        ([h("teacher"), target(item), explain("ይጠቀማል", "uses")], f"The teacher uses {item.gloss}."),
        ([target(item), h("bag"), h("inside"), h("there_is")], f"The {item.gloss} is inside the bag."),
        ([h("i"), target(item), h("see")], f"I see {item.gloss}."),
        ([h("child"), target(item), explain("ይፈልጋል", "wants")], f"The child wants {item.gloss}."),
        ([target(item), h("home"), h("there_is")], f"The {item.gloss} is at home."),
        ([h("this"), target(item), h("good"), h("is")], f"This {item.gloss} is good."),
    ]
    return choose_sentences(item, frames)


def transport_sentences(item: VocabItem) -> list[dict[str, object]]:
    return [
        sentence([h("i"), target(item), explain("እጠቀማለሁ", "I use")], f"I use the {item.gloss}."),
        sentence([target(item), explain("በመንገድ", "on the road"), h("there_is")], f"The {item.gloss} is on the road."),
        sentence([h("friend"), target(item), explain("ይጠብቃል", "waits for")], f"A friend waits for the {item.gloss}."),
    ]


def animal_sentences(item: VocabItem) -> list[dict[str, object]]:
    frames = [
        ([target(item), h("yard"), h("inside"), h("there_is")], f"The {item.gloss} is in the yard."),
        ([h("child"), target(item), explain("ይመለከታል", "watches")], f"The child watches the {item.gloss}."),
        ([target(item), h("water"), explain("ይጠጣል", "drinks")], f"The {item.gloss} drinks water."),
        ([target(item), h("picture"), h("inside"), h("there_is")], f"The {item.gloss} is in the picture."),
        ([h("friend"), target(item), h("see")], f"I see the {item.gloss} with a friend."),
        ([target(item), h("outside"), h("there_is")], f"The {item.gloss} is outside."),
    ]
    return choose_sentences(item, frames)


def nature_sentences(item: VocabItem) -> list[dict[str, object]]:
    frames = [
        ([h("today"), target(item), h("there_is")], f"There is {item.gloss} today."),
        ([h("i"), target(item), h("see")], f"I see the {item.gloss}."),
        ([h("outside"), target(item), h("there_is")], f"There is {item.gloss} outside."),
        ([h("child"), target(item), explain("ይመለከታል", "watches")], f"The child watches the {item.gloss}."),
        ([h("picture"), h("on"), target(item), h("there_is")], f"There is {item.gloss} in the picture."),
        ([target(item), h("near"), h("is")], f"The {item.gloss} is near."),
        ([h("we"), target(item), h("like")], f"We like the {item.gloss}."),
        ([target(item), h("outside"), h("good"), h("is")], f"The {item.gloss} outside is good."),
        ([h("friend"), target(item), h("see")], f"A friend sees the {item.gloss}."),
    ]
    return choose_sentences(item, frames)


def body_sentences(item: VocabItem) -> list[dict[str, object]]:
    frames = [
        ([h("doctor"), target(item), explain("ይመረምራል", "checks")], f"The doctor checks the {item.gloss}."),
        ([h("picture"), h("on"), target(item), h("there_is")], f"There is a {item.gloss} in the picture."),
        ([h("child"), target(item), explain("ይነካል", "touches")], f"The child touches the {item.gloss}."),
        ([target(item), h("clean"), h("is")], f"The {item.gloss} is clean."),
        ([h("teacher"), target(item), explain("ያሳያል", "shows")], f"The teacher shows the {item.gloss}."),
        ([h("i"), target(item), explain("እሰማለሁ", "I feel")], f"I feel my {item.gloss}."),
    ]
    return choose_sentences(item, frames)


def verb_sentences(item: VocabItem) -> list[dict[str, object]]:
    if item.gloss in INVOLUNTARY_VERBS:
        frames = [
            ([h("child"), target(item), explain("አይፈልግም", "does not want")], f"The child does not want to {item.gloss}."),
            ([h("doctor"), target(item), explain("አይፈልግም", "does not want")], f"The doctor does not want to {item.gloss}."),
            ([h("today"), h("we"), target(item), explain("አንፈልግም", "we do not want")], f"Today we do not want to {item.gloss}."),
            ([h("friend"), target(item), explain("አይፈልግም", "does not want")], f"A friend does not want to {item.gloss}."),
            ([h("teacher"), target(item), explain("አይፈልግም", "does not want")], f"The teacher does not want to {item.gloss}."),
            ([h("home"), h("inside"), h("we"), target(item), explain("አንፈልግም", "we do not want")], f"At home, we do not want to {item.gloss}."),
        ]
        return choose_sentences(item, frames)

    if item.gloss in SENSITIVE_VERBS:
        frames = [
            ([h("child"), target(item), explain("አይፈልግም", "does not want")], f"The child does not want to {item.gloss}."),
            ([h("teacher"), target(item), explain("አይፈቅድም", "does not allow")], f"The teacher does not allow anyone to {item.gloss}."),
            ([h("today"), h("we"), target(item), explain("አንፈልግም", "we do not want")], f"Today we do not want to {item.gloss}."),
            ([h("doctor"), target(item), explain("አይፈልግም", "does not want")], f"The doctor does not want to {item.gloss}."),
            ([h("home"), h("inside"), target(item), explain("አይፈቀድም", "is not allowed")], f"It is not allowed to {item.gloss} at home."),
            ([h("school"), h("inside"), target(item), explain("አይፈቀድም", "is not allowed")], f"It is not allowed to {item.gloss} at school."),
        ]
        return choose_sentences(item, frames)

    frames = [
        ([h("i"), target(item), h("want")], f"I want to {item.gloss}."),
        ([h("you"), target(item), h("can")], f"Can you {item.gloss}?", True),
        ([h("today"), h("we"), target(item), explain("እንፈልጋለን", "we want")], f"Today we want to {item.gloss}."),
        ([h("teacher"), target(item), explain("ይፈልጋል", "wants")], f"The teacher wants to {item.gloss}."),
        ([h("friend"), target(item), explain("ይችላል", "can")], f"A friend can {item.gloss}."),
        ([h("school"), h("inside"), h("child"), target(item), explain("ይማራል", "learns")], f"At school, the child learns to {item.gloss}."),
        ([h("child"), target(item), explain("ይማራል", "learns")], f"The child learns to {item.gloss}."),
        ([h("now"), h("i"), target(item), explain("እሞክራለሁ", "I try")], f"Now I try to {item.gloss}."),
        ([h("tomorrow"), h("we"), target(item), explain("እንችላለን", "we can")], f"Tomorrow we can {item.gloss}."),
        ([h("lesson"), h("after"), h("we"), target(item), explain("እንፈልጋለን", "we want")], f"After the lesson, we want to {item.gloss}."),
        ([h("home"), h("inside"), h("i"), target(item), explain("እሞክራለሁ", "I try")], f"At home, I try to {item.gloss}."),
        ([h("market"), h("before"), h("i"), target(item), h("want")], f"Before the market, I want to {item.gloss}."),
    ]
    return choose_sentences(item, frames)


def phrase_sentences(item: VocabItem) -> list[dict[str, object]]:
    return [
        sentence([h("i"), target(item), h("say")], f"I say {item.gloss}."),
        sentence([h("friend"), target(item), explain("ይላል", "says")], f"A friend says {item.gloss}."),
        sentence([h("teacher"), target(item), explain("ይጠቀማል", "uses")], f"The teacher uses {item.gloss}."),
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
        "amharic",
        a1_items(),
        [(1, 50), (51, 100), (101, 150), (151, 200), (201, 250), (251, 300), (301, 350), (351, 400), (401, 450), (451, 500)],
    )
    write_batches(
        "amharic_swadesh",
        swadesh_items(),
        [(1, 41), (42, 83), (84, 124), (125, 165), (166, 207)],
    )


if __name__ == "__main__":
    main()
