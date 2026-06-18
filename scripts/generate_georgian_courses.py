#!/usr/bin/env python3
"""Generate reviewed Georgian A1 and Swadesh batch data for minicloze."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

from georgian_transliteration import romanize


ROOT = Path(__file__).resolve().parents[1]
CORPORA = ROOT / "minicloze-lib" / "corpora"
GENERATED = CORPORA / "generated"
USER_AGENT = {"User-Agent": "minicloze-georgian-course-builder/1.0"}

SWADESH_SOURCE = "Wiktionary Georgian Swadesh seed"
A1_SOURCE = "Codex-curated Georgian A1 seed list"

SWADESH_OVERRIDES = {
    3: "იგი",
    70: "ბუმბული",
    109: "სიკვდილი",
    125: "დგომა",
    196: "მართალი",
    201: "თან",
    202: "შიგნით",
    203: "ერთად",
    205: "თუ",
    207: "სახელი",
}


@dataclass(frozen=True)
class VocabItem:
    index: int
    word: str
    gloss: str
    category: str
    source: str


A1_EXTRAS: list[tuple[str, str, str]] = [
    ("გამარჯობა", "hello", "phrase"),
    ("გთხოვ", "please", "phrase"),
    ("მადლობა", "thank you", "phrase"),
    ("ბოდიში", "sorry", "phrase"),
    ("ნახვამდის", "goodbye", "phrase"),
    ("დიახ", "yes", "phrase"),
    ("არა", "no", "phrase"),
    ("კარგად", "okay", "adjective"),
    ("კეთილი იყოს", "welcome", "phrase"),
    ("მეგობარი", "friend", "person"),
    ("ოჯახი", "family", "person"),
    ("ბებია", "grandmother", "person"),
    ("ბაბუა", "grandfather", "person"),
    ("და", "sister", "person"),
    ("ძმა", "brother", "person"),
    ("ბიძა", "uncle", "person"),
    ("დეიდა", "aunt", "person"),
    ("მეზობელი", "neighbor", "person"),
    ("მასწავლებელი", "teacher", "person"),
    ("სტუდენტი", "student", "person"),
    ("მოსწავლე", "pupil", "person"),
    ("ექიმი", "doctor", "person"),
    ("ექთანი", "nurse", "person"),
    ("პოლიციელი", "police officer", "person"),
    ("მძღოლი", "driver", "person"),
    ("მუშა", "worker", "person"),
    ("გამყიდველი", "seller", "person"),
    ("მომხმარებელი", "customer", "person"),
    ("სტუმარი", "guest", "person"),
    ("ბიჭი", "boy", "person"),
    ("გოგო", "girl", "person"),
    ("შვილი", "son or daughter", "person"),
    ("ვაჟი", "son", "person"),
    ("ქალიშვილი", "daughter", "person"),
    ("მშობელი", "parent", "person"),
    ("ნათესავი", "relative", "person"),
    ("უფროსი", "boss", "person"),
    ("კოლეგა", "colleague", "person"),
    ("სახლი", "house", "place"),
    ("სკოლა", "school", "place"),
    ("ბაზარი", "market", "place"),
    ("მაღაზია", "shop", "place"),
    ("ქუჩა", "street", "place"),
    ("ქალაქი", "city", "place"),
    ("სოფელი", "village", "place"),
    ("სასტუმრო", "hotel", "place"),
    ("ბანკი", "bank", "place"),
    ("საავადმყოფო", "hospital", "place"),
    ("აფთიაქი", "pharmacy", "place"),
    ("პარკი", "park", "place"),
    ("გაჩერება", "stop", "place"),
    ("სადგური", "station", "place"),
    ("ოფისი", "office", "place"),
    ("რესტორანი", "restaurant", "place"),
    ("კაფე", "cafe", "place"),
    ("მუზეუმი", "museum", "place"),
    ("ბიბლიოთეკა", "library", "place"),
    ("ოთახი", "room", "place"),
    ("საძინებელი", "bedroom", "place"),
    ("სამზარეულო", "kitchen", "place"),
    ("აბაზანა", "bathroom", "place"),
    ("ეზო", "yard", "place"),
    ("ხიდი", "bridge", "place"),
    ("ეკლესია", "church", "place"),
    ("უნივერსიტეტი", "university", "place"),
    ("ქარხანა", "factory", "place"),
    ("მოედანი", "square", "place"),
    ("აეროპორტი", "airport", "place"),
    ("ფოსტა", "post office", "place"),
    ("კლასი", "classroom", "place"),
    ("აუზი", "pool", "place"),
    ("თეატრი", "theater", "place"),
    ("კინო", "cinema", "place"),
    ("პლაჟი", "beach", "place"),
    ("ბაღი", "garden", "place"),
    ("ზოოპარკი", "zoo", "place"),
    ("დღეს", "today", "time"),
    ("ხვალ", "tomorrow", "time"),
    ("გუშინ", "yesterday", "time"),
    ("ახლა", "now", "time"),
    ("დილა", "morning", "time"),
    ("შუადღე", "noon", "time"),
    ("საღამო", "evening", "time"),
    ("კვირა", "week", "time"),
    ("თვე", "month", "time"),
    ("საათი", "hour", "time"),
    ("წუთი", "minute", "time"),
    ("ორშაბათი", "Monday", "time"),
    ("სამშაბათი", "Tuesday", "time"),
    ("ოთხშაბათი", "Wednesday", "time"),
    ("ხუთშაბათი", "Thursday", "time"),
    ("პარასკევი", "Friday", "time"),
    ("შაბათი", "Saturday", "time"),
    ("კვირა დღე", "Sunday", "time"),
    ("იანვარი", "January", "time"),
    ("თებერვალი", "February", "time"),
    ("მარტი", "March", "time"),
    ("აპრილი", "April", "time"),
    ("მაისი", "May", "time"),
    ("ივნისი", "June", "time"),
    ("ივლისი", "July", "time"),
    ("აგვისტო", "August", "time"),
    ("სექტემბერი", "September", "time"),
    ("ოქტომბერი", "October", "time"),
    ("ნოემბერი", "November", "time"),
    ("დეკემბერი", "December", "time"),
    ("პური", "bread", "food"),
    ("ყავა", "coffee", "drink"),
    ("ჩაი", "tea", "drink"),
    ("რძე", "milk", "drink"),
    ("შაქარი", "sugar", "food"),
    ("ბრინჯი", "rice", "food"),
    ("მაკარონი", "pasta", "food"),
    ("სუპი", "soup", "food"),
    ("ბოსტნეული", "vegetables", "food"),
    ("ბანანი", "banana", "food"),
    ("ფორთოხალი", "orange", "food"),
    ("ვაშლი", "apple", "food"),
    ("კარტოფილი", "potato", "food"),
    ("პომიდორი", "tomato", "food"),
    ("ხახვი", "onion", "food"),
    ("კარაქი", "butter", "food"),
    ("თაფლი", "honey", "food"),
    ("ყველი", "cheese", "food"),
    ("სალათი", "salad", "food"),
    ("საუზმე", "breakfast", "food"),
    ("სადილი", "lunch", "food"),
    ("ვახშამი", "dinner", "food"),
    ("წვენი", "juice", "drink"),
    ("იოგურტი", "yogurt", "food"),
    ("სენდვიჩი", "sandwich", "food"),
    ("კიტრი", "cucumber", "food"),
    ("სტაფილო", "carrot", "food"),
    ("მარწყვი", "strawberry", "food"),
    ("ლიმონი", "lemon", "food"),
    ("ნამცხვარი", "cake", "food"),
    ("წიგნი", "book", "object"),
    ("რვეული", "notebook", "object"),
    ("კალამი", "pen", "object"),
    ("ფანქარი", "pencil", "object"),
    ("მაგიდა", "table", "object"),
    ("სკამი", "chair", "object"),
    ("საწოლი", "bed", "object"),
    ("კარი", "door", "object"),
    ("ფანჯარა", "window", "object"),
    ("გასაღები", "key", "object"),
    ("ტელეფონი", "phone", "object"),
    ("კომპიუტერი", "computer", "object"),
    ("ტელევიზორი", "television", "object"),
    ("რადიო", "radio", "object"),
    ("ჩანთა", "bag", "object"),
    ("ტანსაცმელი", "clothes", "object"),
    ("ფეხსაცმელი", "shoes", "object"),
    ("ქუდი", "hat", "object"),
    ("პერანგი", "shirt", "object"),
    ("შარვალი", "pants", "object"),
    ("კაბა", "dress", "object"),
    ("ქურთუკი", "jacket", "object"),
    ("ფული", "money", "object"),
    ("ლარი", "lari", "object"),
    ("ბილეთი", "ticket", "object"),
    ("რუკა", "map", "object"),
    ("საჩუქარი", "gift", "object"),
    ("ყუთი", "box", "object"),
    ("საპონი", "soap", "object"),
    ("პირსახოცი", "towel", "object"),
    ("სარკე", "mirror", "object"),
    ("ჭიქა", "cup", "object"),
    ("თეფში", "plate", "object"),
    ("კოვზი", "spoon", "object"),
    ("დანა", "knife", "object"),
    ("ჩანგალი", "fork", "object"),
    ("გაკვეთილი", "lesson", "object"),
    ("საქმე", "work", "object"),
    ("საშინაო დავალება", "homework", "object"),
    ("გამოცდა", "exam", "object"),
    ("კითხვა", "question", "object"),
    ("პასუხი", "answer", "object"),
    ("ნომერი", "number", "object"),
    ("ასო", "letter", "object"),
    ("ენა", "language", "object"),
    ("ქართული", "Georgian", "object"),
    ("ინგლისური", "English", "object"),
    ("ისტორია", "history", "object"),
    ("მათემატიკა", "math", "object"),
    ("მუსიკა", "music", "object"),
    ("სურათი", "picture", "object"),
    ("ფოტო", "photo", "object"),
    ("თამაში", "game", "object"),
    ("წერილი", "letter", "object"),
    ("შეტყობინება", "message", "object"),
    ("ამბავი", "news", "object"),
    ("დოკუმენტი", "document", "object"),
    ("ქაღალდი", "paper", "object"),
    ("გვერდი", "page", "object"),
    ("ფასი", "price", "object"),
    ("მისამართი", "address", "object"),
    ("პასპორტი", "passport", "object"),
    ("ვიზა", "visa", "object"),
    ("ბარგი", "luggage", "object"),
    ("ქოლგა", "umbrella", "object"),
    ("სათვალე", "glasses", "object"),
    ("მანქანა", "car", "transport"),
    ("ავტობუსი", "bus", "transport"),
    ("მატარებელი", "train", "transport"),
    ("ტაქსი", "taxi", "transport"),
    ("ველოსიპედი", "bicycle", "transport"),
    ("თვითმფრინავი", "airplane", "transport"),
    ("ნავი", "boat", "transport"),
    ("მოგზაურობა", "trip", "transport"),
    ("მეტრო", "metro", "transport"),
    ("ტრამვაი", "tram", "transport"),
    ("მოტოციკლი", "motorcycle", "transport"),
    ("კატა", "cat", "animal"),
    ("ცხენი", "horse", "animal"),
    ("ძროხა", "cow", "animal"),
    ("ცხვარი", "sheep", "animal"),
    ("თხა", "goat", "animal"),
    ("ქათამი", "chicken", "animal"),
    ("ღორი", "pig", "animal"),
    ("ლომი", "lion", "animal"),
    ("სპილო", "elephant", "animal"),
    ("თაგვი", "mouse", "animal"),
    ("კურდღელი", "rabbit", "animal"),
    ("იხვი", "duck", "animal"),
    ("სახე", "face", "body"),
    ("მხარი", "shoulder", "body"),
    ("თითი", "finger", "body"),
    ("მკლავი", "arm", "body"),
    ("ჯანმრთელობა", "health", "body"),
    ("ტკივილი", "pain", "body"),
    ("წამალი", "medicine", "body"),
    ("დაღლილობა", "tiredness", "body"),
    ("ლურჯი", "blue", "color"),
    ("ყავისფერი", "brown", "color"),
    ("ნაცრისფერი", "gray", "color"),
    ("ლამაზი", "beautiful", "adjective"),
    ("ადვილი", "easy", "adjective"),
    ("სწრაფი", "fast", "adjective"),
    ("ნელი", "slow", "adjective"),
    ("ძვირი", "expensive", "adjective"),
    ("იაფი", "cheap", "adjective"),
    ("სუფთა", "clean", "adjective"),
    ("ბედნიერი", "happy", "adjective"),
    ("მოწყენილი", "sad", "adjective"),
    ("მზად", "ready", "adjective"),
    ("ავად", "sick", "adjective"),
    ("ძლიერი", "strong", "adjective"),
    ("სუსტი", "weak", "adjective"),
    ("მნიშვნელოვანი", "important", "adjective"),
    ("სასარგებლო", "useful", "adjective"),
    ("ჩუმი", "quiet", "adjective"),
    ("ხმამაღალი", "loud", "adjective"),
    ("მშიერი", "hungry", "adjective"),
    ("მწყურვალი", "thirsty", "adjective"),
    ("დაკავებული", "busy", "adjective"),
    ("თავისუფალი", "free", "adjective"),
    ("საშუალო", "medium", "adjective"),
    ("წასვლა", "go", "verb"),
    ("წაკითხვა", "read", "verb"),
    ("წერა", "write", "verb"),
    ("სწავლა", "learn", "verb"),
    ("სწავლება", "teach", "verb"),
    ("მუშაობა", "work", "verb"),
    ("ყიდვა", "buy", "verb"),
    ("გაყიდვა", "sell", "verb"),
    ("გახსნა", "open", "verb"),
    ("დახურვა", "close", "verb"),
    ("ადგომა", "get up", "verb"),
    ("სირბილი", "run", "verb"),
    ("დახმარება", "help", "verb"),
    ("პასუხის გაცემა", "answer", "verb"),
    ("ნდომა", "want", "verb"),
    ("სიყვარული", "like", "verb"),
    ("შეძლება", "can", "verb"),
    ("აღება", "take", "verb"),
    ("მოტანა", "bring", "verb"),
    ("გაგზავნა", "send", "verb"),
    ("ლოდინი", "wait", "verb"),
    ("დაწყება", "start", "verb"),
    ("დასრულება", "finish", "verb"),
    ("დაბანა", "wash", "verb"),
    ("მომზადება", "prepare", "verb"),
    ("თარგმნა", "translate", "verb"),
    ("არჩევა", "choose", "verb"),
    ("შეცვლა", "change", "verb"),
    ("ხელმოწერა", "sign", "verb"),
    ("გადახდა", "pay", "verb"),
    ("გამოყენება", "use", "verb"),
    ("შემოწმება", "check", "verb"),
    ("დარეკვა", "call", "verb"),
    ("შეკეთება", "fix", "verb"),
    ("გასუფთავება", "clean", "verb"),
    ("გაკეთება", "do", "verb"),
    ("გახსენება", "remember", "verb"),
    ("დავიწყება", "forget", "verb"),
    ("მიღება", "receive", "verb"),
    ("ტარება", "carry", "verb"),
    ("დარჩენა", "stay", "verb"),
    ("პოვნა", "find", "verb"),
    ("დაკარგვა", "lose", "verb"),
    ("გაზომვა", "measure", "verb"),
    ("ჩართვა", "turn on", "verb"),
    ("გამორთვა", "turn off", "verb"),
    ("მოსმენა", "listen", "verb"),
    ("ყურება", "look", "verb"),
    ("გაგება", "understand", "verb"),
    ("გამეორება", "repeat", "verb"),
    ("შეხვედრა", "meet", "verb"),
    ("ღიმილი", "smile", "verb"),
    ("ცეკვა", "dance", "verb"),
    ("ან", "or", "function"),
    ("მაგრამ", "but", "function"),
    ("შესახებ", "about", "function"),
    ("მსგავსად", "like", "function"),
    ("წინ", "before", "function"),
    ("შემდეგ", "after", "function"),
    ("ქვეშ", "under", "function"),
    ("გარეშე", "without", "function"),
    ("მდე", "until", "function"),
]

COMMON = {
    "i": ("მე", "I"),
    "you": ("შენ", "you"),
    "we": ("ჩვენ", "we"),
    "child": ("ბავშვი", "child"),
    "teacher": ("მასწავლებელი", "teacher"),
    "doctor": ("ექიმი", "doctor"),
    "mother": ("დედა", "mother"),
    "friend": ("მეგობარი", "friend"),
    "today": ("დღეს", "today"),
    "tomorrow": ("ხვალ", "tomorrow"),
    "now": ("ახლა", "now"),
    "morning": ("დილა", "morning"),
    "evening": ("საღამო", "evening"),
    "here": ("აქ", "here"),
    "there": ("იქ", "there"),
    "this": ("ეს", "this"),
    "that": ("ის", "that"),
    "home": ("სახლი", "home"),
    "school": ("სკოლა", "school"),
    "market": ("ბაზარი", "market"),
    "room": ("ოთახი", "room"),
    "yard": ("ეზო", "yard"),
    "outside": ("გარეთ", "outside"),
    "coffee": ("ყავა", "coffee"),
    "tea": ("ჩაი", "tea"),
    "water": ("წყალი", "water"),
    "book": ("წიგნი", "book"),
    "bag": ("ჩანთა", "bag"),
    "table": ("მაგიდა", "table"),
    "chair": ("სკამი", "chair"),
    "bed": ("საწოლი", "bed"),
    "cup": ("ჭიქა", "cup"),
    "picture": ("სურათი", "picture"),
    "door": ("კარი", "door"),
    "road": ("გზა", "road"),
    "cat": ("კატა", "cat"),
    "gift": ("საჩუქარი", "gift"),
    "lesson": ("გაკვეთილი", "lesson"),
    "trip": ("მოგზაურობა", "trip"),
    "sugar": ("შაქარი", "sugar"),
    "apple": ("ვაშლი", "apple"),
    "sound": ("ხმა", "sound"),
    "music": ("მუსიკა", "music"),
    "work": ("საქმე", "work"),
    "question": ("კითხვა", "question"),
    "is": ("არის", "is"),
    "are": ("არიან", "are"),
    "have": ("მაქვს", "I have"),
    "there_is": ("არის", "there is"),
    "want": ("მინდა", "I want"),
    "like": ("მომწონს", "I like"),
    "see": ("ვხედავ", "I see"),
    "bring": ("მოიტანა", "brought"),
    "drink": ("ვსვამ", "I drink"),
    "eat": ("ვჭამ", "I eat"),
    "go": ("მივდივარ", "I go"),
    "come": ("მოვდივარ", "I come"),
    "learn": ("ვსწავლობთ", "we learn"),
    "say": ("ვამბობ", "I say"),
    "can": ("შეგიძლია", "you can"),
    "good": ("კარგი", "good"),
    "clean": ("სუფთა", "clean"),
    "near": ("ახლოს", "near"),
    "inside": ("შიგნით", "inside"),
    "on": ("ზედ", "on"),
    "to": ("კენ", "to"),
    "with": ("ერთად", "with"),
    "and": ("და", "and"),
    "before": ("წინ", "before"),
    "after": ("შემდეგ", "after"),
    "bag_inside": ("ჩანთაში", "in the bag"),
    "table_on": ("მაგიდაზე", "on the table"),
    "chair_on": ("სკამზე", "on the chair"),
    "bed_under": ("საწოლის ქვეშ", "under the bed"),
    "road_on": ("გზაზე", "on the road"),
    "school_inside": ("სკოლაში", "at school"),
    "home_inside": ("სახლში", "at home"),
    "room_inside": ("ოთახში", "in the room"),
    "door_near": ("კართან", "near the door"),
    "market_at": ("ბაზარში", "at the market"),
}

QUESTION_SENTENCES = {
    "who": [
        (["x", "came"], "Who came?"),
        (["x", "here", "is"], "Who is here?"),
        (["teacher_def", "x", "sees"], "Whom does the teacher see?"),
    ],
    "what": [
        (["you", "x", "you_want"], "What do you want?"),
        (["table_on", "x", "there_is"], "What is on the table?"),
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
    "მე": ("ვარ", "am", "I"),
    "შენ": ("ხარ", "are", "you"),
    "იგი": ("არის", "is", "he"),
    "ჩვენ": ("ვართ", "are", "we"),
    "თქვენ": ("ხართ", "are", "you all"),
    "ისინი": ("არიან", "are", "they"),
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
DRINKS = {"water", "coffee", "tea", "milk", "juice"}
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
    "juice",
    "yogurt",
    "sandwich",
    "cucumber",
    "carrot",
    "strawberry",
    "lemon",
    "cake",
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
    "until",
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
    for match in re.finditer(r"m\[(\d+)\]\s*=\s*(.*?)(?=\nm\[\d+\]|\Z)", text, re.S):
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
    return term.strip().strip("჻,.;:?!")


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
    if gloss in FOOD_GLOSSES:
        return "drink" if gloss in DRINKS else "food"
    if index is not None and 62 <= index <= 91:
        return "body"
    if index is not None and 92 <= index <= 146:
        return "verb"
    if index is not None and 147 <= index <= 179:
        return "nature"
    return fallback


def swadesh_items() -> list[VocabItem]:
    try:
        english = parse_swadesh_module("en")
        georgian = parse_swadesh_module("ka")
    except Exception:
        cached = CORPORA / "georgian_swadesh_vocab.json"
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
        word = SWADESH_OVERRIDES.get(index) or georgian[index][0]
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
        "target": f"{target_text}{'?' if question else '.'}",
        "text": english,
        "words": words,
    }


def token_from_key(key: str, item: VocabItem) -> dict[str, str]:
    if key == "x":
        return target(item)
    fixed = {
        "came": ("მოვიდა", "came"),
        "sees": ("ხედავს", "sees"),
        "you_want": ("გინდა", "you want"),
        "you_go": ("მიდიხარ", "you go"),
        "will_come": ("მოვა", "will come"),
        "you_come": ("მოხვალ", "you come"),
        "i_drink": ("ვსვამ", "I drink"),
        "teacher_def": ("მასწავლებელი", "the teacher"),
        "friend_def": ("მეგობარი", "the friend"),
        "book_def": ("წიგნი", "the book"),
        "market_def": ("ბაზარი", "the market"),
    }
    if key in fixed:
        values = fixed[key]
        return explain(values[0], values[1])
    return h(key)


def from_keys(keys: list[str], item: VocabItem, english: str, question: bool = False) -> dict[str, object]:
    return sentence([token_from_key(key, item) for key in keys], english, question)


def choose_sentences(item: VocabItem, frames: list[tuple[list[dict[str, str]], str] | tuple[list[dict[str, str]], str, bool]]) -> list[dict[str, object]]:
    start = (item.index * 3) % len(frames)
    chosen = [frames[(start + offset) % len(frames)] for offset in range(3)]
    return [sentence(frame[0], frame[1], frame[2] if len(frame) > 2 else False) for frame in chosen]


def pronoun_sentences(item: VocabItem) -> list[dict[str, object]]:
    verb, verb_gloss, english_subject = PRONOUN_FORMS.get(item.word, ("არის", "is", item.gloss))
    subject = english_subject[0].upper() + english_subject[1:]
    return [
        sentence([target(item), h("here"), explain(verb, verb_gloss)], f"{subject} {verb_gloss} here."),
        sentence([target(item), explain("სტუდენტი", "student"), explain(verb, verb_gloss)], f"{subject} {verb_gloss} a student."),
        sentence([target(item), h("good"), explain(verb, verb_gloss)], f"{subject} {verb_gloss} well."),
    ]


def question_sentences(item: VocabItem) -> list[dict[str, object]]:
    frames = QUESTION_SENTENCES.get(item.gloss.lower())
    if frames:
        return [from_keys(keys, item, english, True) for keys, english in frames]
    return [
        sentence([target(item), h("here"), h("is")], f"{item.gloss.title()} is here?", True),
        sentence([h("you"), target(item), explain("გინდა", "you want")], f"Do you want {item.gloss}?", True),
        sentence([h("teacher"), target(item), explain("ხედავს", "sees")], f"Does the teacher see {item.gloss}?", True),
    ]


def deictic_sentences(item: VocabItem) -> list[dict[str, object]]:
    if item.gloss in {"here", "there"}:
        return [
            sentence([h("i"), target(item), h("is")], f"I am {item.gloss}."),
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
        sentence([target(item), h("this"), h("book"), explain("არ არის", "is not")], "No, this is not a book."),
        sentence([h("i"), h("coffee"), target(item), explain("არ მინდა", "do not want")], "I do not want coffee."),
        sentence([h("today"), h("school"), target(item), explain("არ არის", "there is no")], "There is no school today."),
    ]


def function_sentences(item: VocabItem) -> list[dict[str, object]]:
    g = item.gloss.lower()
    if g == "and":
        frames = [
            ([h("coffee"), target(item), h("water"), h("want")], "I want coffee and water."),
            ([h("mother"), target(item), h("friend"), explain("მოვიდა", "came")], "Mother and a friend came."),
            ([h("book"), target(item), h("bag"), h("there_is")], "There are a book and a bag."),
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
            ([h("today"), h("good"), h("is"), target(item), explain("ცივი", "cold"), h("is")], "Today is good but cold."),
            ([h("friend"), explain("მოვიდა", "came"), target(item), h("teacher"), explain("არ მოვიდა", "did not come")], "A friend came, but the teacher did not come."),
        ]
    elif g == "because":
        frames = [
            ([h("water"), h("drink"), target(item), explain("თბილი", "warm"), h("is")], "I drink water because it is warm."),
            ([h("home"), h("go"), target(item), explain("დაღლილი ვარ", "I am tired")], "I go home because I am tired."),
            ([h("book"), h("want"), target(item), h("learn")], "I want a book because we study."),
        ]
    elif g == "if":
        frames = [
            ([target(item), h("water"), h("there_is"), h("coffee"), h("drink")], "If there is water, I drink coffee."),
            ([target(item), h("teacher"), explain("მოვა", "comes"), h("we"), h("learn")], "If the teacher comes, we study."),
            ([target(item), h("market"), h("near"), h("is"), h("i"), h("go")], "If the market is near, I go."),
        ]
    elif g in {"in", "at"}:
        frames = [
            ([h("book"), h("bag_inside"), target(item), h("there_is")], "The book is inside the bag."),
            ([h("friend"), h("home_inside"), target(item), h("there_is")], "A friend is at home."),
            ([h("teacher"), h("school_inside"), target(item), h("there_is")], "The teacher is at school."),
        ]
    elif g == "with":
        frames = [
            ([h("i"), h("friend"), target(item), h("go")], "I go with a friend."),
            ([h("teacher"), h("child"), target(item), explain("სწავლობს", "studies")], "The teacher studies with the child."),
            ([h("coffee"), h("sugar"), target(item), h("is")], "The coffee is with sugar."),
        ]
    elif g == "about":
        frames = [
            ([h("i"), h("book"), target(item), explain("ვამბობ", "I speak")], "I speak about the book."),
            ([h("teacher"), h("lesson"), target(item), explain("ამბობს", "speaks")], "The teacher speaks about the lesson."),
            ([h("friend"), h("trip"), target(item), explain("კითხულობს", "asks")], "A friend asks about the trip."),
        ]
    elif g == "like":
        frames = [
            ([h("child"), h("teacher"), target(item), explain("ლაპარაკობს", "speaks")], "The child speaks like the teacher."),
            ([h("this"), h("bag"), h("book"), target(item), h("is")], "This bag is like a book."),
            ([h("friend"), h("mother"), target(item), explain("ეხმარება", "helps")], "A friend helps like mother."),
        ]
    elif g == "before":
        frames = [
            ([h("school"), target(item), h("i"), h("coffee"), h("drink")], "Before school, I drink coffee."),
            ([h("market"), target(item), h("friend"), explain("მოდის", "comes")], "Before the market, a friend comes."),
            ([h("lesson"), target(item), h("we"), h("book"), explain("ვკითხულობთ", "we read")], "Before the lesson, we read a book."),
        ]
    elif g == "after":
        frames = [
            ([h("school"), target(item), h("i"), h("home"), h("go")], "After school, I go home."),
            ([h("market"), target(item), h("friend"), h("coffee"), explain("სვამს", "drinks")], "After the market, a friend drinks coffee."),
            ([h("lesson"), target(item), h("we"), h("book"), explain("ვკითხულობთ", "we read")], "After the lesson, we read a book."),
        ]
    elif g == "under":
        frames = [
            ([h("book"), h("table"), target(item), h("there_is")], "The book is under the table."),
            ([h("bag"), h("chair"), target(item), h("there_is")], "The bag is under the chair."),
            ([h("cat"), h("bed_under"), target(item), h("there_is")], "The cat is under the bed."),
        ]
    elif g == "near":
        frames = [
            ([h("school"), h("market"), target(item), h("there_is")], "The school is near the market."),
            ([h("home"), h("road"), target(item), h("there_is")], "The house is near the road."),
            ([h("friend"), h("door_near"), target(item), h("there_is")], "A friend is near the door."),
        ]
    elif g == "without":
        frames = [
            ([h("i"), h("sugar"), target(item), h("coffee"), h("drink")], "I drink coffee without sugar."),
            ([h("friend"), h("book"), target(item), h("school"), explain("მიდის", "goes")], "A friend goes to school without a book."),
            ([h("teacher"), h("coffee"), target(item), explain("მოდის", "comes")], "The teacher comes without coffee."),
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
        ([h("table_on"), target(item), h("cup"), h("there_is")], f"There are {item.gloss} cups on the table."),
        ([h("teacher"), target(item), h("question"), explain("იკითხა", "asked")], f"The teacher asked {item.gloss} {question}."),
        ([h("child"), target(item), h("apple"), explain("მოიტანა", "brought")], f"The child brought {item.gloss} apples."),
        ([h("room_inside"), target(item), h("chair"), h("there_is")], f"There are {item.gloss} chairs in the room."),
        ([h("market_at"), target(item), h("bag"), h("there_is")], f"There are {item.gloss} bags at the market."),
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
        sentence([h("this"), explain("კაბა", "dress"), target(item), h("is")], f"This dress is {item.gloss}."),
        sentence([target(item), explain("ფერი", "color"), h("like")], f"I like the color {item.gloss}."),
    ]


def person_sentences(item: VocabItem) -> list[dict[str, object]]:
    frames = [
        ([target(item), h("home_inside"), h("there_is")], f"The {item.gloss} is at home."),
        ([h("i"), target(item), h("see")], f"I see the {item.gloss}."),
        ([target(item), h("coffee"), explain("სვამს", "drinks")], f"The {item.gloss} drinks coffee."),
        ([target(item), h("market"), explain("მიდის", "goes")], f"The {item.gloss} goes to the market."),
        ([target(item), h("book"), explain("კითხულობს", "reads")], f"The {item.gloss} reads a book."),
        ([target(item), h("child"), explain("ეხმარება", "helps")], f"The {item.gloss} helps the child."),
        ([h("teacher"), target(item), h("with"), explain("ლაპარაკობს", "speaks")], f"The teacher speaks with the {item.gloss}."),
        ([target(item), h("school_inside"), h("there_is")], f"The {item.gloss} is inside the school."),
        ([h("friend"), target(item), explain("ელოდება", "waits for")], f"A friend waits for the {item.gloss}."),
    ]
    return choose_sentences(item, frames)


def place_sentences(item: VocabItem) -> list[dict[str, object]]:
    frames = [
        ([h("i"), target(item), h("go")], f"I go to the {item.gloss}."),
        ([target(item), h("near"), h("is")], f"The {item.gloss} is near."),
        ([h("friend"), target(item), h("inside"), h("there_is")], f"A friend is inside the {item.gloss}."),
        ([h("teacher"), target(item), explain("მიდის", "goes")], f"The teacher goes to the {item.gloss}."),
        ([target(item), h("road"), h("near"), h("there_is")], f"The {item.gloss} is near the road."),
        ([h("i"), target(item), h("see")], f"I see the {item.gloss}."),
        ([h("friend"), target(item), explain("ელოდება", "waits at")], f"A friend waits at the {item.gloss}."),
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
    consume = "drink" if action["word"] == "ვსვამ" else "eat"
    third = explain("სვამს", "drinks") if consume == "drink" else explain("ჭამს", "eats")
    frames = [
        ([h("i"), target(item), action], f"I {consume} {item.gloss}."),
        ([h("mother"), target(item), explain("ამზადებს", "prepares")], f"Mother prepares {item.gloss}."),
        ([h("market_at"), target(item), h("there_is")], f"There is {item.gloss} at the market."),
        ([h("friend"), target(item), explain("უნდა", "wants")], f"A friend wants {item.gloss}."),
        ([target(item), h("table_on"), h("there_is")], f"The {item.gloss} is on the table."),
        ([h("child"), target(item), third], f"The child {consume}s {item.gloss}."),
    ]
    return choose_sentences(item, frames)


def object_sentences(item: VocabItem) -> list[dict[str, object]]:
    if item.gloss == "name":
        return [
            sentence([h("i"), target(item), explain("ვწერ", "I write")], "I write my name."),
            sentence([target(item), h("book"), h("on"), h("there_is")], "The name is on the book."),
            sentence([h("teacher"), target(item), explain("კითხულობს", "asks")], "The teacher asks for the name."),
        ]
    frames = [
        ([h("i"), target(item), h("want")], f"I want {item.gloss}."),
        ([target(item), h("table_on"), h("there_is")], f"The {item.gloss} is on the table."),
        ([h("friend"), target(item), h("bring")], f"A friend brought {item.gloss}."),
        ([h("teacher"), target(item), explain("იყენებს", "uses")], f"The teacher uses {item.gloss}."),
        ([target(item), h("bag_inside"), h("there_is")], f"The {item.gloss} is inside the bag."),
        ([h("i"), target(item), h("see")], f"I see {item.gloss}."),
        ([h("child"), target(item), explain("უნდა", "wants")], f"The child wants {item.gloss}."),
        ([target(item), h("home_inside"), h("there_is")], f"The {item.gloss} is at home."),
        ([h("this"), target(item), h("good"), h("is")], f"This {item.gloss} is good."),
    ]
    return choose_sentences(item, frames)


def transport_sentences(item: VocabItem) -> list[dict[str, object]]:
    return [
        sentence([h("i"), target(item), explain("ვიყენებ", "I use")], f"I use the {item.gloss}."),
        sentence([target(item), h("road_on"), h("there_is")], f"The {item.gloss} is on the road."),
        sentence([h("friend"), target(item), explain("ელოდება", "waits for")], f"A friend waits for the {item.gloss}."),
    ]


def animal_sentences(item: VocabItem) -> list[dict[str, object]]:
    frames = [
        ([target(item), h("yard"), h("inside"), h("there_is")], f"The {item.gloss} is in the yard."),
        ([h("child"), target(item), explain("უყურებს", "watches")], f"The child watches the {item.gloss}."),
        ([target(item), h("water"), explain("სვამს", "drinks")], f"The {item.gloss} drinks water."),
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
        ([h("child"), target(item), explain("უყურებს", "watches")], f"The child watches the {item.gloss}."),
        ([h("picture"), h("on"), target(item), h("there_is")], f"I see the {item.gloss} in the picture."),
        ([target(item), h("near"), h("is")], f"The {item.gloss} is near."),
        ([h("we"), target(item), h("like")], f"We like the {item.gloss}."),
        ([target(item), h("outside"), h("good"), h("is")], f"The {item.gloss} outside is good."),
        ([h("friend"), target(item), explain("ხედავს", "sees")], f"A friend sees the {item.gloss}."),
    ]
    return choose_sentences(item, frames)


def body_sentences(item: VocabItem) -> list[dict[str, object]]:
    frames = [
        ([h("doctor"), target(item), explain("ამოწმებს", "checks")], f"The doctor checks the {item.gloss}."),
        ([h("picture"), h("on"), target(item), h("there_is")], f"There is a {item.gloss} in the picture."),
        ([h("child"), target(item), explain("ეხება", "touches")], f"The child touches the {item.gloss}."),
        ([target(item), h("clean"), h("is")], f"The {item.gloss} is clean."),
        ([h("teacher"), target(item), explain("აჩვენებს", "shows")], f"The teacher shows the {item.gloss}."),
        ([h("i"), target(item), explain("ვგრძნობ", "I feel")], f"I feel my {item.gloss}."),
    ]
    return choose_sentences(item, frames)


def verb_sentences(item: VocabItem) -> list[dict[str, object]]:
    if item.gloss in INVOLUNTARY_VERBS:
        frames = [
            ([h("child"), target(item), explain("არ უნდა", "does not want")], f"The child does not want to {item.gloss}."),
            ([h("doctor"), target(item), explain("არ უნდა", "does not want")], f"The doctor does not want to {item.gloss}."),
            ([h("today"), h("we"), target(item), explain("არ გვინდა", "we do not want")], f"Today we do not want to {item.gloss}."),
            ([h("friend"), target(item), explain("არ უნდა", "does not want")], f"A friend does not want to {item.gloss}."),
            ([h("teacher"), target(item), explain("არ უნდა", "does not want")], f"The teacher does not want to {item.gloss}."),
            ([h("home_inside"), h("we"), target(item), explain("არ გვინდა", "we do not want")], f"At home, we do not want to {item.gloss}."),
        ]
        return choose_sentences(item, frames)
    if item.gloss in SENSITIVE_VERBS:
        frames = [
            ([h("child"), target(item), explain("არ უნდა", "does not want")], f"The child does not want to {item.gloss}."),
            ([h("teacher"), target(item), explain("არ უშვებს", "does not allow")], f"The teacher does not allow anyone to {item.gloss}."),
            ([h("today"), h("we"), target(item), explain("არ გვინდა", "we do not want")], f"Today we do not want to {item.gloss}."),
            ([h("doctor"), target(item), explain("არ უნდა", "does not want")], f"The doctor does not want to {item.gloss}."),
            ([h("home_inside"), target(item), explain("არ შეიძლება", "is not allowed")], f"It is not allowed to {item.gloss} at home."),
            ([h("school_inside"), target(item), explain("არ შეიძლება", "is not allowed")], f"It is not allowed to {item.gloss} at school."),
        ]
        return choose_sentences(item, frames)

    frames = [
        ([h("i"), target(item), h("want")], f"I want to {item.gloss}."),
        ([h("you"), h("can"), target(item)], f"Can you {item.gloss}?", True),
        ([h("today"), h("we"), target(item), explain("გვინდა", "we want")], f"Today we want to {item.gloss}."),
        ([h("teacher"), target(item), explain("უნდა", "wants")], f"The teacher wants to {item.gloss}."),
        ([h("friend"), target(item), explain("შეუძლია", "can")], f"A friend can {item.gloss}."),
        ([h("school_inside"), h("child"), target(item), explain("სწავლობს", "learns")], f"At school, the child learns to {item.gloss}."),
        ([h("child"), target(item), explain("სწავლობს", "learns")], f"The child learns to {item.gloss}."),
        ([h("now"), h("i"), target(item), explain("ვცდილობ", "I try")], f"Now I try to {item.gloss}."),
        ([h("tomorrow"), h("we"), target(item), explain("შეგვიძლია", "we can")], f"Tomorrow we can {item.gloss}."),
        ([h("lesson"), h("after"), h("we"), target(item), explain("გვინდა", "we want")], f"After the lesson, we want to {item.gloss}."),
        ([h("home_inside"), h("i"), target(item), explain("ვცდილობ", "I try")], f"At home, I try to {item.gloss}."),
        ([h("market"), h("before"), h("i"), target(item), h("want")], f"Before the market, I want to {item.gloss}."),
    ]
    return choose_sentences(item, frames)


def phrase_sentences(item: VocabItem) -> list[dict[str, object]]:
    return [
        sentence([h("i"), target(item), h("say")], f"I say {item.gloss}."),
        sentence([h("friend"), target(item), explain("ამბობს", "says")], f"A friend says {item.gloss}."),
        sentence([h("teacher"), target(item), explain("ამბობს", "says")], f"The teacher says {item.gloss}."),
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
        "georgian",
        a1_items(),
        [(1, 50), (51, 100), (101, 150), (151, 200), (201, 250), (251, 300), (301, 350), (351, 400), (401, 450), (451, 500)],
    )
    write_batches(
        "georgian_swadesh",
        swadesh_items(),
        [(1, 41), (42, 83), (84, 124), (125, 165), (166, 207)],
    )


if __name__ == "__main__":
    main()
