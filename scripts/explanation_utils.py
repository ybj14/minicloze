from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    from thai_paiboon import romanize as romanize_thai_paiboon
except ModuleNotFoundError:  # pragma: no cover - supports package-style imports in QA snippets.
    from scripts.thai_paiboon import romanize as romanize_thai_paiboon


CYRILLIC_WORD = re.compile(r"[A-Za-z\u0400-\u04FF'-]+")
PUNCTUATION = ".,!?;:«»\"()[]{}“”"
UNKNOWN_NOTE = "needs lexicon review"
THAI_COMBINING_MARKS = set("ัิีึืุู็่้๊๋์ํฺ")
THAI_BLOCK = re.compile(r"[\u0E00-\u0E7F]")
TIBETAN_DELIMITERS = set("་༌།༎༏༐༑༔ \t\r\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def first_gloss(gloss: str) -> str:
    return gloss.split(";", 1)[0].split("|", 1)[0].strip()


def compact_note(note: str | None) -> str | None:
    if not note:
        return None
    note = note.strip()
    return note or None


def explanation(word: str, gloss: str, note: str | None = None) -> dict[str, str]:
    item = {"word": word, "gloss": gloss}
    note = compact_note(note)
    if note:
        item["note"] = note
    return item


def add_paiboon(item: dict[str, str]) -> dict[str, str]:
    paiboon = romanize_thai_paiboon(item.get("word", ""))
    if paiboon.strip():
        item["paiboon"] = paiboon
    return item


def load_vocab_lexicon(vocab_path: Path) -> dict[str, dict[str, str]]:
    vocab = read_json(vocab_path)
    lexicon: dict[str, dict[str, str]] = {}
    for entry in vocab:
        word = str(entry["word"])
        lexicon[word] = explanation(
            word,
            first_gloss(str(entry["gloss"])),
            entry.get("note"),
        )
    return lexicon


def load_existing_explanation_lexicon(
    corpora_dir: Path,
    language: str,
) -> dict[str, dict[str, str]]:
    lexicon: dict[str, dict[str, str]] = {}
    for suffix in ["a1", "swadesh"]:
        path = corpora_dir / f"{language}_{suffix}_explanations.json"
        if not path.exists():
            continue
        for row in read_json(path).get("data", []):
            for word in row.get("words", []):
                value = str(word.get("word", "")).strip()
                gloss = str(word.get("gloss", "")).strip()
                if not value or not gloss or word.get("note") == UNKNOWN_NOTE:
                    continue
                lexicon.setdefault(value, explanation(value, gloss, word.get("note")))
    return lexicon


def parse_pipe_lexicon(text: str) -> dict[str, dict[str, str]]:
    lexicon: dict[str, dict[str, str]] = {}
    for line in text.strip().splitlines():
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) == 2:
            word, gloss = parts
            note = None
        elif len(parts) == 3:
            word, gloss, note = parts
        else:
            raise ValueError(f"bad lexicon line: {line}")
        lexicon[word] = explanation(word, gloss, note)
    return lexicon


TAJIK_COMMON = parse_pipe_lexicon(
    """
ман|I|pronoun
ту|you|pronoun
шумо|you|polite/plural pronoun
вай|he; she|pronoun
ӯ|he; she|pronoun
мо|we|pronoun
онҳо|they|pronoun
ин|this|demonstrative
он|that|demonstrative
дар|in; at|preposition
ба|to; toward|preposition
аз|from; after|preposition
бо|with|preposition
барои|for|preposition
дар бораи|about|phrase
назди|near; by|preposition
пеши|near; before|preposition
зери|under|preposition
болои|on top of|preposition
байни|between|preposition
баъд|after|time word
пеш|before|time word
то|until; to|preposition
ва|and|conjunction
ё|or|conjunction
аммо|but|conjunction
чунки|because|conjunction
агар|if|conjunction
ки|that; who|connector
ҳам|also; too|particle
не|no|negative response
ҳа|yes|response
на|not|negative particle
нест|is not; there is not|negative verb
аст|is|copula
ҳаст|there is; exists|existential verb
буд|was|past copula
шуд|became; happened|past verb
мешавад|becomes; can be|verb form
шаванд|become|verb form
дорад|has|verb form
дорам|I have|verb form
дорем|we have|verb form
доранд|they have|verb form
мекунад|does; makes|verb form
мекунам|I do; make|verb form
мекунем|we do; make|verb form
мекунанд|they do; make|verb form
кард|did; made|past verb
кардам|I did; made|past verb
кардем|we did; made|past verb
меравад|goes|verb form
меравам|I go|verb form
меравем|we go|verb form
мераванд|they go|verb form
рафт|went|past verb
рафтам|I went|past verb
рафтем|we went|past verb
меояд|comes|verb form
меоям|I come|verb form
меоем|we come|verb form
омад|came|past verb
омадам|I came|past verb
мебинад|sees|verb form
мебинам|I see|verb form
дид|saw|past verb
мешунавад|hears|verb form
мешунавам|I hear|verb form
мегӯяд|says|verb form
мегӯям|I say|verb form
гуфт|said|past verb
мехонад|reads; studies|verb form
мехонам|I read; study|verb form
мехонем|we read; study|verb form
хонд|read; studied|past verb
менависад|writes|verb form
менависам|I write|verb form
навишт|wrote|past verb
мехӯрад|eats|verb form
мехӯрам|I eat|verb form
мехӯрем|we eat|verb form
хӯрд|ate|past verb
менӯшад|drinks|verb form
менӯшам|I drink|verb form
нӯшид|drank|past verb
мехобад|sleeps|verb form
мехобам|I sleep|verb form
хобид|slept|past verb
менишинад|sits|verb form
менишинам|I sit|verb form
нишаст|sat|past verb
меистад|stands; stops|verb form
меистам|I stand|verb form
истод|stood|past verb
медавад|runs|verb form
медавам|I run|verb form
давид|ran|past verb
меомӯзад|learns|verb form
меомӯзам|I learn|verb form
меомӯзем|we learn|verb form
омӯхт|learned|past verb
меомӯзонад|teaches|verb form
мепазад|cooks|verb form
мепазам|I cook|verb form
пухт|cooked|past verb
мекушояд|opens|verb form
мекушоям|I open|verb form
кушод|opened|past verb
мебандад|closes|verb form
мебандам|I close|verb form
баст|closed|past verb
мегирад|takes|verb form
мегирам|I take; get|verb form
гирифт|took; got|past verb
медиҳад|gives|verb form
медиҳам|I give|verb form
дод|gave|past verb
мехарад|buys|verb form
мехарам|I buy|verb form
харид|bought|past verb
мефурӯшад|sells|verb form
мепардозад|pays|verb form
мепурсад|asks|verb form
мепурсам|I ask|verb form
пурсид|asked|past verb
мефаҳмад|understands|verb form
мефаҳмам|I understand|verb form
фаҳмид|understood|past verb
медонад|knows|verb form
медонам|I know|verb form
донист|knew|past verb
мешӯяд|washes|verb form
мешӯям|I wash|verb form
шуст|washed|past verb
мебардорад|lifts; picks up|verb form
мегузорад|puts|verb form
мегузорам|I put|verb form
гузошт|put|past verb
меёбад|finds|verb form
меёбам|I find|verb form
ёфт|found|past verb
месозад|builds; makes|verb form
мебурад|cuts|verb form
мекашад|pulls; draws|verb form
мешиканад|breaks|verb form
мекӯшад|tries|verb form
механад|laughs|verb form
мерақсад|dances|verb form
мепӯшад|wears|verb form
меронад|drives|verb form
мехоҳад|wants|verb form
мехоҳам|I want|verb form
метавонад|can; is able to|modal verb
метавонам|I can|modal verb
бояд|must; should|modal verb
лутфан|please|polite word
имрӯз|today|time word
фардо|tomorrow|time word
дирӯз|yesterday|time word
субҳ|morning|time word
рӯз|day|time word
шаб|night|time word
бегоҳ|evening|time word
ҳоло|now|time word
акнун|now|adverb
ҳар|each; every|determiner
ҳама|all|determiner
хеле|very|adverb
кам|little; few|adverb
зиёд|much; many|adverb
дигар|other; another|adjective
нав|new|adjective
хуб|good; well|adjective/adverb
бад|bad|adjective
калон|big|adjective
хурд|small|adjective
гарм|warm; hot|adjective
хунук|cold|adjective
тоза|clean; fresh|adjective
куҳна|old|adjective
кутоҳ|short|adjective
дароз|long|adjective
рост|right; straight|adjective/adverb
чап|left|adjective
мекунад|does; makes|verb form
кор|work; job|noun
кори|work/job + ezafe|ezafe form
дарс|lesson; class|noun
синф|class; classroom|noun
кӯмак|help|noun
маъқул|pleasing; liked|adjective
бозӣ|game; play|noun
нишон|sign; mark; show|noun/verb
бисёр|many; much; very|adverb
нигоҳ|look; gaze|noun/verb
сомонӣ|somoni|currency
автобус|bus|noun
билет|ticket|noun
сафед|white|adjective
гап|talk; word|noun
салом|hello|greeting
сафар|trip; travel|noun
дер|late|adverb/adjective
зиндагӣ|life; living|noun
сабз|green|adjective
сурх|red|adjective
андоз|put; throw|imperative stem
савол|question|noun
қуттӣ|box|noun
даст|hand|noun
ид|holiday|noun
интизор|waiting|adjective/noun
саҳар|morning|time word
футбол|football; soccer|noun
бе|without|preposition
вале|but|conjunction
зад|hit; rang|past verb
занг|bell; call|noun
зард|yellow|adjective
каме|a little|adverb
меҳмонӣ|party; visit|noun
овезон|hanging|adjective
рӯи|on top of; face|postposition/noun
рӯйи|on top of|postposition
саҳифа|page|noun
ҳайвонот|animals|noun
ҷой|place|noun
Душанбе|Dushanbe|place name
Оё|question marker|yes/no question particle
оё|question marker|yes/no question particle
вазифа|task; homework|noun
дандон|tooth|noun
истироҳат|rest|noun/verb
кабуд|blue|adjective
мошин|car|noun
парвоз|flight|noun
рақам|number; digit|noun
суруд|song|noun
тоҷикӣ|Tajik|language/adjective
хабар|news|noun
ҳастанд|are; there are|plural existential/copula
ҳуҷҷат|document|noun
ҷамъ|total; gathered|adjective/noun
ҷо|place|noun
дӯкон|shop|noun
поезд|train|noun
суроға|address|noun
шабона|at night; nightly|adverb
акс|photo|noun
ангушт|finger|noun
боло|up; above|noun/adverb
бошад|may be; is|subjunctive copula
гум|lost|adjective
дору|medicine|noun
бӯй|smell|noun
бӯи|smell + ezafe|ezafe form
дӯстам|my friend|possessive form
дӯстамро|my friend + object marker|possessive object form
маро|me|direct object pronoun
дарсро|lesson + object marker|object form
дастам|my hand|possessive form
дасти|hand + ezafe|ezafe form
забони|language + ezafe|ezafe form
филм|film; movie|noun
филми|film/movie + ezafe|ezafe form
месӯзад|burns|verb form
нишастааст|is sitting|perfect/progressive form
истодааст|is standing|perfect/progressive form
мондааст|has remained; is left|perfect form
шудааст|has become; has happened|perfect form
овард|brought|past verb
дидем|we saw|past verb
гирифтем|we took; received|past verb
харидем|we bought|past verb
монд|put; left; stayed|past verb
бармегардам|I return|verb form
бармегардад|returns|verb form
мебарад|carries; takes|verb form
мебарам|I carry; take|verb form
мебарояд|goes out; comes out|verb form
медарояд|enters|verb form
мезанад|hits; rings; plays|verb form
мезанам|I hit; call; play|verb form
мерезад|pours; falls|verb form
мемонад|stays; remains|verb form
менамояд|seems; shows|verb form
диҳед|give|polite imperative
биёр|bring|imperative
андозед|put; throw|polite imperative
бишӯй|wash|imperative
бурд|took away; won|past verb
вохӯрд|met|past verb
деҳ|give|imperative/stem
пӯш|wear|imperative/stem
гир|take; get|imperative/stem
навис|write|imperative/stem
гузор|put|imperative/stem
хоб|sleep; bed|noun
дорӣ|you have|verb form
беҳтар|better|adjective/adverb
бисёранд|are many|copula phrase
зарур|necessary|adjective
интихоб|choice|noun
камтар|less; fewer|adverb
канор|edge; side|noun
канори|edge/side + ezafe|ezafe form
километр|kilometer|noun
марказ|center|noun
маслиҳат|advice|noun
машқ|exercise; practice|noun
майда|small; tiny|adjective
навбат|turn; queue|noun
навишта|written|participle
овоз|voice; sound|noun
овози|voice/sound + ezafe|ezafe form
ошёна|floor; story|noun
ошёнаи|floor/story + ezafe|ezafe form
оғоз|beginning; start|noun
пагоҳ|tomorrow|time word
пинҳон|hidden|adjective
поён|down; lower part|noun/adverb
сола|years old|age adjective
соф|clear; pure|adjective
таксӣ|taxi|noun
тамошо|watching; viewing|noun/verb
танӯр|oven|noun
тараф|side; direction|noun
тарафи|side/direction + ezafe|ezafe form
тару|fresh|adjective component
толор|hall|noun
тӯй|wedding|noun
худ|self|reflexive pronoun
худро|oneself + object marker|reflexive object
шавқовар|interesting|adjective
шиша|glass|noun
шуста|washed|participle
ҷавоб|answer|noun
ҷавоби|answer + ezafe|ezafe form
ҷома|robe; dress|noun
ароба|cart|noun
барвақт|early|adverb
бароям|for me|prepositional pronoun
биби|grandmother|noun
биё|come|imperative
биёед|come|polite imperative
бигӯед|say; tell|polite imperative
бор|load; time|noun
бори|load/time + ezafe|ezafe form
имшаб|tonight|time word
кадом|which|question word
нақша|plan; map|noun
нақшаи|plan/map + ezafe|ezafe form
пешхизмат|waiter|noun
пирамард|old man|noun
почта|post office; mail|noun
саҳаргоҳ|early morning|time word
сухан|word; speech|noun
сухани|word/speech + ezafe|ezafe form
тоҷикистон|Tajikistan|place name
хат|line; letter|noun
чеҳра|face|noun
чеҳраи|face + ezafe|ezafe form
чӯпон|shepherd|noun
шанбе|Saturday|noun
шоха|branch|noun
ях|ice|noun
айб|fault; shame|noun
алафзор|grassy field|noun
алифбо|alphabet|noun
анбор|storehouse|noun
анҷом|end; completion|noun
афсона|story; fairy tale|noun
болишт|pillow|noun
бом|roof|noun
бонк|bank|noun
бозигар|player|noun
даста|team; group|noun
дақиқа|minute|noun
вайрон|broken|adjective
варақ|sheet of paper|noun
гардан|neck|noun
гарон|expensive|adjective
давр|round; period|noun
дард|pain|noun
дарозанд|are long|copula phrase
даромадан|entering|infinitive
дил|heart|noun
дили|heart + ezafe|ezafe form
имрӯза|today's|adjective
имрӯзаи|today's + ezafe|ezafe form
калима|word|noun
корт|card|noun
курсии|chair + ezafe|ezafe form
лозим|necessary|adjective
мӯй|hair|noun
мӯямро|my hair + object marker|possessive object form
нақд|cash|noun
накун|do not do|negative imperative
одат|habit|noun
оромӣ|calm; peace|noun
осонтар|easier|comparative adjective
охир|end|noun
охири|end + ezafe|ezafe form
пешвоз|welcome; meeting|noun
пой|foot; leg|noun
қатор|row; line|noun
қатори|row/line + ezafe|ezafe form
қоида|rule|noun
қоидаи|rule + ezafe|ezafe form
қайчӣ|scissors|noun
роҳрав|corridor|noun
рӯйхат|list|noun
сабр|patience|noun
саҳн|yard; courtyard|noun
саҳни|yard/courtyard + ezafe|ezafe form
суфа|platform; bench|noun
танаффус|break; recess|noun
фаромӯш|forgotten; forgetting|adjective/verb stem
хурсандист|is happiness; is pleasing|copula phrase
хушбахтист|is happiness|copula phrase
шарм|shame|noun
намехоҳам|I do not want|negative verb form
надорам|I do not have|negative verb form
рав|go|imperative
кунед|do; make|polite imperative
деҳед|give|polite imperative
бош|be|imperative
вомехӯрем|we meet|verb form
мумкин|possible|adjective
метр|meter|noun
ҳаракат|movement; motion|noun
бардошта|lifted; carrying|participle
давида|running; having run|participle
дастшӯяк|washbasin|noun
дода|given|participle
долон|hallway|noun
дон|grain; animal feed|noun
донаи|grain/piece + ezafe|ezafe form
дутор|dutor; two-stringed instrument|noun
дӯхт|sewed|past verb
забон|language; tongue|noun
завод|factory|noun
занед|speak; hit|polite imperative
зарф|container|noun
зарфи|container + ezafe|ezafe form
иваз|change; replacement|noun
имзо|signature|noun
имтиҳон|exam|noun
интернет|internet|noun
интизорем|we are waiting|verb form
кашед|pull; draw; take off|polite imperative
кино|cinema; movie|noun
китобча|booklet|noun
китобчаи|booklet + ezafe|ezafe form
кишт|planting; sowing|noun
кофӣ|enough|adjective/adverb
коғазӣ|paper; made of paper|adjective
қоғазӣ|paper; made of paper|adjective
кун|do; make|imperative
кушоед|open|polite imperative
куҷо|where|question word
куҷост|where is it|question phrase
матн|text|noun
мато|fabric|noun
матои|fabric + ezafe|ezafe form
мебарорад|produces; takes out|verb form
мебароянд|go out; come out|verb form
мебошад|is|formal copula
мегиронад|lights; causes to take|verb form
мегузаронем|we spend; pass|verb form
менавозад|plays an instrument|verb form
меоянд|come|verb form
мепӯшонам|I cover; put on for someone|verb form
мерӯбем|we sweep|verb form
месарояд|sings|verb form
мефаҳмонад|explains|verb form
мечарад|grazes|verb form
мечаспад|sticks|verb form
мечинад|picks; gathers|verb form
мешинонад|plants|verb form
мешукуфад|blooms|verb form
меҷӯшад|boils|verb form
меҷӯям|I search|verb form
мизоҷ|customer; client|noun
мон|put; leave|imperative
мост|is ours|possessive copula
мулоим|mild; soft|adjective
мусиқӣ|music|noun
мусиқиро|music + object marker|object form
нависед|write|polite imperative
навохт|played an instrument|past verb
надидем|we did not see|negative past verb
надиҳед|do not give|negative polite imperative
надод|did not give|negative past verb
надорем|we do not have|negative verb form
назан|do not hit; do not touch|negative imperative
намоён|visible|adjective
наор|do not bring|negative imperative
напарто|do not throw away|negative imperative
нахон|do not read|negative imperative
нахӯр|do not eat|negative imperative
нашав|do not become; do not be|negative imperative
нашуд|did not happen; did not become|negative past verb
наъно|mint|noun
ниёз|need|noun
ногаҳон|suddenly|adverb
нуҳ|nine|number variant
нӯш|drink|imperative
нӯшем|let's drink; we drink|subjunctive/imperative form
омода|ready|adjective
орд|flour|noun
оғил|stable; barn|noun
пайваст|connected; connects|verb/adjective
палто|coat|noun
партов|trash|noun
пикник|picnic|noun
пухтааст|has ripened; has cooked|perfect verb form
пӯшид|wore; put on|past verb
равшананд|are bright|copula phrase
расид|arrived; reached|past verb
раҳмат|thanks|noun
рехт|poured|past verb
роҳравӣ|walking|noun
рӯзнома|newspaper|noun
сабад|basket|noun
сард|cold|adjective
сафҳа|page|noun
сафҳаҳои|pages; plural/ezafe form|plural form
саҳна|stage|noun
сиёҳанд|are black|copula phrase
содда|simple|adjective
соус|sauce|noun
сохтанд|built|past verb
соҳиб|owner|noun
соҳибаш|its owner|possessive form
стакан|glass; tumbler|noun
таба|frying pan|noun
табақча|small plate|noun
тамом|finished; all gone|adjective
тартиб|order; arrangement|noun
таърих|history|noun
таърихи|history + ezafe|ezafe form
тақвим|calendar|noun
тӯҳфа|gift|noun
устохона|workshop|noun
фармоиш|order|noun
фаҳмонд|explained|past verb
фуромадем|we descended|past verb
харидааст|has bought|perfect verb form
хартум|trunk|elephant trunk
хомӯш|off; silent|adjective
хонача|little house|noun
хуш|pleasant; good|adjective
хушбӯй|fragrant|adjective
чанд|how many; several|question word/quantifier
шав|become; be|imperative/stem
шеър|poem|noun
шино|swim|imperative/stem
шунидам|I heard|past verb
якшанбе|Sunday|day name
якҷо|together|adverb
ёрӣ|help|noun
ғизо|food|noun
ғизои|food + ezafe|ezafe form
қадам|step|noun
қафас|cage|noun
қисм|part|noun
қисса|story|noun
қулай|convenient|adjective
қуттӣ|box|noun
қуттии|box + ezafe|ezafe form
ҳамин|this same|demonstrative
ҳамроҳ|together with; companion|adverb/noun
ҳамроҳи|with; accompanying + ezafe|ezafe form
ҳарф|letter|noun
ҳарфҳоро|letters + object marker|plural object form
ҳикоя|story|noun
ҷайб|pocket|noun
ҷайбам|my pocket|possessive form
ҷаҳид|jumped|past verb
ҷорӣ|flowing; current|adjective
ҷунбонд|moved; shook|past verb
духтур|doctor|noun
шудан|becoming; to become|infinitive
механдад|laughs|verb form
пок|clean; pure|adjective
тела|push|noun/verb stem
берун|outside|place word
бораи|about; concerning|postpositional form
нафас|breath|noun
тавр|way; manner|noun
туф|spit|noun/verb stem
шикор|hunt|noun/verb stem
шиновар|swimmer; floating|noun/adjective
қай|vomit|noun/verb stem
вақте|when|time connector
баромад|came out; went out|past verb
биология|biology|noun
гардед|turn; become|polite imperative/subjunctive
гирад|takes; may take|get verb form
дида|seen; having seen|participle
крем|cream|noun
намехост|did not want|negative past verb
расонд|delivered; caused to reach|past verb
эҳтиёт|care; caution|noun/adverb
қаҳрамон|hero|noun
ахлотро|trash + object marker|object form
нӯги|tip; end + ezafe|ezafe form
ресмон|rope|string noun
тугма|button|noun
чархи|wheel + ezafe|ezafe form
аждаҳоро|dragon + object marker|object form
аробачаро|cart + object marker|object form
афтодааст|has fallen|perfect verb form
бадан|body|noun
балки|but rather; maybe|connector
беоб|without water; waterless|adjective
беодобист|is rude|copula phrase
биншинед|sit down|polite imperative
бозии|game/play + ezafe|ezafe form
даромад|entered|past verb
диван|sofa|noun
зина|stairs; step|noun
ист|stop; stand|imperative/stem
калонсол|adult|noun/adjective
касе|someone; a person|pronoun
касеро|someone + object marker|object form
каш|pull; draw|imperative/stem
манъ|forbidden; prohibition|adjective/noun
мевазад|blows|verb form
мемолад|rubs; applies|verb form
мепошад|sprinkles; scatters|verb form
мерасем|we arrive; we reach|verb form
мерӯяд|grows|verb form
месанҷад|checks; tests|verb form
метарсам|I fear; I am afraid|verb form
мешинонам|I plant; seat|verb form
мисли|like; similar to|preposition
монӣ|you put; you leave|verb form
набошад|if there is not; is not|negative subjunctive
намегазад|does not bite|negative verb form
намерасонад|does not deliver; does not harm|negative verb form
нарасон|do not deliver; do not harm|negative imperative
нохуш|unpleasant; unwell|adjective
пиёда|on foot|adverb/adjective
пурс|ask|imperative/stem
рақс|dance|noun/verb stem
саломатӣ|health|noun
сер|full; satiated|adjective
сулфа|cough|noun/verb stem
табиӣ|natural|adjective
тахта|board|noun
торикӣ|darkness|noun
хобидааст|is lying down; has slept|perfect verb form
хонаанд|are houses; are at home|plural copula form
хоҳӣ|you want; you will|verb form
хурсандӣ|happiness|noun
чуқурӣ|hole; depth|noun
шӯед|wash|polite imperative
қаиқ|boat|noun
қайчии|scissors + ezafe|ezafe form
ҳангоми|during; when|time connector
ҳезум|firewood|noun
ҳавопаймо|airplane|noun
ҳис|feeling; sense|noun
ҷудо|separate|adjective/adverb
    """
)


TAJIK_VERB_STEMS = {
    "рав": ("go", "present stem"),
    "о": ("come", "present stem"),
    "кун": ("do; make", "present stem"),
    "дор": ("have", "present stem"),
    "бин": ("see", "present stem"),
    "шунав": ("hear", "present stem"),
    "гӯ": ("say", "present stem"),
    "хон": ("read; study", "present stem"),
    "навис": ("write", "present stem"),
    "хӯр": ("eat", "present stem"),
    "нӯш": ("drink", "present stem"),
    "хоб": ("sleep", "present stem"),
    "нишин": ("sit", "present stem"),
    "ист": ("stand", "present stem"),
    "дав": ("run", "present stem"),
    "омӯз": ("learn", "present stem"),
    "омӯзон": ("teach", "present stem"),
    "паз": ("cook", "present stem"),
    "кушо": ("open", "present stem"),
    "банд": ("close", "present stem"),
    "гир": ("take; get", "present stem"),
    "деҳ": ("give", "present stem"),
    "хар": ("buy", "present stem"),
    "фурӯш": ("sell", "present stem"),
    "пардоз": ("pay", "present stem"),
    "пурс": ("ask", "present stem"),
    "фаҳм": ("understand", "present stem"),
    "дон": ("know", "present stem"),
    "шӯ": ("wash", "present stem"),
    "бардор": ("lift; pick up", "present stem"),
    "гузор": ("put", "present stem"),
    "ёб": ("find", "present stem"),
    "соз": ("build; make", "present stem"),
    "бур": ("cut", "present stem"),
    "каш": ("pull; draw", "present stem"),
    "шикан": ("break", "present stem"),
    "кӯш": ("try", "present stem"),
    "хан": ("laugh", "present stem"),
    "рақс": ("dance", "present stem"),
    "пӯш": ("wear", "present stem"),
    "рон": ("drive", "present stem"),
    "хоҳ": ("want", "present stem"),
    "тавон": ("can; be able to", "present stem"),
    "намо": ("show; seem", "present stem"),
    "бар": ("carry; take", "present stem"),
    "баро": ("go out; come out", "present stem"),
    "даро": ("enter", "present stem"),
    "зан": ("hit; call; play", "present stem"),
    "рез": ("pour; fall", "present stem"),
    "мон": ("stay; put", "present stem"),
    "сӯз": ("burn", "present stem"),
    "афт": ("fall", "present stem"),
    "гард": ("turn; return", "present stem"),
    "биёр": ("bring", "imperative stem"),
    "андоз": ("put; throw", "present stem"),
    "бор": ("rain; fall", "present stem"),
    "гузар": ("pass; cross", "present stem"),
    "диҳ": ("give", "present stem"),
    "дурахш": ("shine", "present stem"),
    "ор": ("bring", "present stem"),
    "парто": ("throw away", "present stem"),
    "шав": ("become", "present stem"),
    "шин": ("sit", "present stem"),
}


TAJIK_PAST_STEMS = {
    "афтод": ("fell", "past stem"),
    "борид": ("rained", "past stem"),
    "бурд": ("took away; won", "past stem"),
    "давид": ("ran", "past stem"),
    "дид": ("saw", "past stem"),
    "ёфт": ("found", "past stem"),
    "гузашт": ("passed", "past stem"),
    "гузошт": ("put", "past stem"),
    "гирифт": ("took; got", "past stem"),
    "истод": ("stood; waited", "past stem"),
    "кард": ("did; made", "past stem"),
    "кашид": ("pulled; drew", "past stem"),
    "монд": ("put; left; stayed", "past stem"),
    "навишт": ("wrote", "past stem"),
    "нишаст": ("sat", "past stem"),
    "нӯшид": ("drank", "past stem"),
    "овард": ("brought", "past stem"),
    "омад": ("came", "past stem"),
    "омӯхт": ("learned", "past stem"),
    "пардохт": ("paid", "past stem"),
    "пухт": ("cooked", "past stem"),
    "рафт": ("went", "past stem"),
    "фаҳмид": ("understood", "past stem"),
    "фиристод": ("sent", "past stem"),
    "харид": ("bought", "past stem"),
    "хонд": ("read; studied", "past stem"),
    "хӯрд": ("ate", "past stem"),
    "шинонд": ("planted", "past stem"),
    "шуст": ("washed", "past stem"),
}


MONGOLIAN_COMMON = parse_pipe_lexicon(
    """
Би|I|pronoun
би|I|pronoun
Чи|you|pronoun
чи|you|pronoun
Та|you|polite pronoun
та|you|polite pronoun
Бид|we|pronoun
бид|we|pronoun
Тэд|they|pronoun
тэд|they|pronoun
Энэ|this|demonstrative
энэ|this|demonstrative
Тэр|he; she; that|pronoun/demonstrative
тэр|he; she; that|pronoun/demonstrative
Миний|my|possessive pronoun
миний|my|possessive pronoun
Таны|your|polite possessive pronoun
таны|your|polite possessive pronoun
бүх|all|determiner
олон|many|determiner
зарим|some|determiner
нэг|one|number
хоёр|two|number
гурван|three|number
дөрвөн|four|number
таван|five|number
ба|and|conjunction
болон|and|conjunction
хамт|with; together|postposition/adverb
дээр|on|postposition
дотор|in; inside|postposition
дэргэд|near; beside|postposition
хэрэв|if|conjunction
учир|because|reason word
болохгүй|must not; cannot|negative modal
биш|not|negative copula
байна|is; are|copula
байдаг|is usually; exists|verb form
байхгүй|is not; absent|negative existential
ирсэн|came|past verb
ирлээ|came|past verb
ирдэг|comes; usually comes|verb form
явна|goes; will go|verb form
явдаг|goes; usually goes|verb form
явъя|let us go|hortative
харлаа|saw|past verb
хардаг|sees; usually sees|verb form
харж|seeing; looking|converb
ууж|drinking|converb
уудаг|drinks|verb form
иддэг|eats|verb form
идэж|eating|converb
өгнө|gives|verb form
авна|takes; buys|verb form
нээдэг|opens|verb form
хаадаг|closes|verb form
уншдаг|reads|verb form
бичдэг|writes|verb form
сурдаг|learns|verb form
ярьдаг|speaks; talks|verb form
асуудаг|asks|verb form
хэлдэг|says|verb form
мэднэ|knows|verb form
мэддэг|knows|verb form
хүсэж|wanting|converb
чадна|can|modal verb
сайн|good; well|adjective/adverb
муу|bad|adjective
цэвэр|clean|adjective
дулаан|warm|adjective
хүйтэн|cold|adjective
шинэ|new|adjective
хуучин|old|adjective
өнөөдөр|today|time word
Өнөөдөр|today|time word
өглөө|morning|time word
Өглөө|morning|time word
орой|evening|time word
Орой|evening|time word
энд|here|place word
тэнд|there|place word
гэрт|at home|location
сургуульд|at school|location
гадаа|outside|location
цүнх|bag|noun
хаалга|door|noun
цай|tea|noun
ус|water|noun
хоол|food|noun
талх|bread|noun
аяга|cup|noun
ширээн|table|oblique form
багш|teacher|noun
эмч|doctor|noun
ээж|mother|noun
найз|friend|noun
хүүхэд|child|noun
зураг|picture|noun
биед|in the body|locative form
бие|body|noun
өвдөж|hurting|converb
шалгалаа|checked|past verb
харуулж|showing|converb
Анчин|hunter|noun
Ахын|older brother + genitive|genitive form
Аяганы|cup + genitive|genitive form
Бохийг|gum + object marker|object form
Бяцхан|little|adjective
Бөмбөлөг|balloon|noun
Галын|fire + genitive|genitive form
Гэмтсэн|injured|participle
Зууханд|in the stove|locative form
Зүү|needle|noun
Зөгий|bee|noun
Намар|autumn|season
намар|autumn|season
Сагс|basket|noun
сагс|basket|noun
Сагсанд|in the basket|locative form
Шувууны|bird + genitive|genitive form
Хазуулсан|bitten|participle
бай|be; stay|imperative/stem
барихгүй|will not hold; will not catch|negative verb form
гэвэл|because; if one says|connector
унав|fell|past verb
салхинд|in the wind|locative form
сурлаа|learned|past verb
хийсгэв|blew away|past verb
хутга|knife|noun
цаана|behind; on the other side|place word
цэцгийн|flower + genitive|genitive form
үнэр|smell; scent|noun
чанав|boiled; cooked|past verb
эрүүл|healthy|adjective
өвдсөн|hurt; sore|participle
нээ|open|imperative/stem
үзэхээр|in order to see|purpose form
гал|fire|noun
шувуу|bird|noun
үүр|nest|noun
салхи|wind|noun
цэцэг|flower|noun
цонх|window|noun
лимон|lemon|noun
малын|livestock + genitive|genitive form
онгоц|airplane|noun
охины|girl + genitive|genitive form
соруултай|with a straw|comitative form
тамирчид|athletes|plural noun
тамирчин|athlete|noun
унасны|falling + genitive|genitive/verbal form
урагдсан|torn|participle
ургамлын|plant + genitive|genitive form
хайруулын|frying + genitive|genitive form
хайч|scissors|noun
хогоо|one's trash|reflexive object form
хортон|pest|noun
чамтай|with you|comitative pronoun
эрвээхэй|butterfly|noun
ямааны|goat + genitive|genitive form
айдсаа|one's fear|reflexive object form
алхана|walks; will walk|verb form
амтат|sweet; tasty|adjective
анхааралтай|carefully; attentive|adverb/adjective
арилгах|remove; erase|verb
асаж|burning; lit|converb
байшинг|house + object marker|object form
барин|holding|converb
битүүрсэн|blocked; stuffy|participle
боль|stop|imperative
босгов|raised; stood up|past verb
бүү|do not|negative imperative
газарт|on the ground; to the land|locative form
газраа|one's place; ground|reflexive form
гаргахын|to take out; producing + genitive|verbal genitive form
гарна|comes out; goes out|verb form
гутлын|shoe + genitive|genitive form
гэрэлтэж|shining|converb
давж|crossing; passing|converb
дор|under; below|postposition
дэлгэв|spread out; opened|past verb
дээш|upward|direction word
жаахан|a little; small|adjective/adverb
жимээр|by path|instrumental form
залуудaa|in youth; when young|time form
залуудаа|in youth; when young|time form
зангидав|tied; knotted|past verb
засдаг|fixes; repairs|verb form
ир|come|imperative/stem
лаа|candle|noun
мэдрэгдэв|was felt|past verb
мэрэхгүй|will not gnaw|negative verb form
нэмлээ|added|past verb
нээх|open|verb
нян|germ|noun
нүх|hole|noun
онгойлгов|opened|past verb
орондоо|in one's bed|locative/reflexive form
оч|spark|noun
очно|goes; will go|verb form
сурагч|student|noun
тавганд|on a plate|locative form
тарив|planted|past verb
татаж|pulling|converb
товч|button|noun
толбыг|stain + object marker|object form
тэвэрлээ|hugged|past verb
тэрэг|cart; vehicle|noun
түүв|picked; collected|past verb
улайдаг|turns red|verb form
унаад|after falling|converb
уналаа|fell|past verb
ургажээ|has grown|perfect verb form
ургана|grows; will grow|verb form
ухаж|digging|converb
хаа|close|imperative/stem
хавар|spring|season
хайлав|melted|past verb
хайрладаг|loves; cares for|verb form
харандаа|pencil|noun
хариуг|answer + object marker|object form
хориотой|forbidden|adjective
хуруугаа|one's finger|reflexive object form
хуулахгүй|will not peel; will not copy|negative verb form
хэрэглэ|use|imperative/stem
хэрэглэдэг|uses|verb form
хөдөл|move|imperative/stem
хөдөлдөг|moves|verb form
хөдөлнө|moves; will move|verb form
чадалтай|strong; capable|adjective
чадвартай|capable; skilled|adjective
шалыг|floor + object marker|object form
шампунь|shampoo|noun
шарсан|fried; roasted|participle
шингээдэг|absorbs|verb form
шударгаар|honestly; fairly|adverb
шүүс|juice|noun
эгнээнд|in a row; in line|locative form
эдгэрэв|healed|past verb
эмчид|to the doctor|dative form
эргэнэ|turns; returns|verb form
эрэгт|on the shore|locative form
ядарлаа|got tired|past verb
ёсгүй|must not; should not|negative modal
үхрийн|cow/cattle + genitive|genitive form
үдээс|shoelace; lace|noun
үлдлээ|remained; stayed|past verb
үлдэв|remained; stayed|past verb
үлдэнэ|remains; will stay|verb form
өвсөн|grass + attributive|attributive form
өргөс|thorn|noun
    """
)


MONGOLIAN_SUFFIXES = [
    ("тайгаа", "with; comitative/reflexive form"),
    ("тэйгээ", "with; comitative/reflexive form"),
    ("тойгоо", "with; comitative/reflexive form"),
    ("гүй", "negative form"),
    ("ийг", "object marker"),
    ("ыг", "object marker"),
    ("аар", "by; through; instrumental form"),
    ("ээр", "by; through; instrumental form"),
    ("оор", "by; through; instrumental form"),
    ("өөр", "by; through; instrumental form"),
    ("аас", "from; ablative form"),
    ("ээс", "from; ablative form"),
    ("оос", "from; ablative form"),
    ("өөс", "from; ablative form"),
    ("анд", "in; at; dative-locative form"),
    ("энд", "in; at; dative-locative form"),
    ("онд", "in; at; dative-locative form"),
    ("өнд", "in; at; dative-locative form"),
    ("тай", "with; having"),
    ("тэй", "with; having"),
    ("той", "with; having"),
    ("ны", "genitive form"),
    ("ний", "genitive form"),
    ("ын", "genitive form"),
    ("ийн", "genitive form"),
    ("ад", "when; dative/verbal form"),
    ("эд", "when; dative/verbal form"),
    ("аа", "reflexive/object form"),
    ("ээ", "reflexive/object form"),
    ("оо", "reflexive/object form"),
    ("өө", "reflexive/object form"),
]


def build_mongolian_lexicon(vocab_path: Path) -> dict[str, dict[str, str]]:
    raw: dict[str, dict[str, str]] = {}
    raw.update(load_existing_explanation_lexicon(vocab_path.parent, "mongolian"))
    raw.update(load_vocab_lexicon(vocab_path))
    raw.update(MONGOLIAN_COMMON)
    lexicon: dict[str, dict[str, str]] = {}
    for word, item in raw.items():
        lexicon[word.lower()] = item
    return lexicon


def explain_spaced_token(
    token: str,
    lexicon: dict[str, dict[str, str]],
) -> dict[str, str]:
    normalized = token.strip(PUNCTUATION)
    key = normalized.lower()
    if key in lexicon:
        base = lexicon[key]
        return explanation(normalized, base["gloss"], base.get("note"))
    return explanation(normalized, normalized, UNKNOWN_NOTE)


def explain_mongolian_token(
    token: str,
    lexicon: dict[str, dict[str, str]],
) -> dict[str, str]:
    normalized = token.strip(PUNCTUATION)
    key = normalized.lower()
    if key in lexicon:
        base = lexicon[key]
        return explanation(normalized, base["gloss"], base.get("note"))

    for suffix, note in MONGOLIAN_SUFFIXES:
        if not key.endswith(suffix) or len(key) <= len(suffix):
            continue
        base_key = key[: -len(suffix)]
        if base_key in lexicon:
            base = lexicon[base_key]
            return explanation(normalized, base["gloss"], note)

    return explanation(normalized, normalized, UNKNOWN_NOTE)


def explain_mongolian_sentence(
    text: str,
    lexicon: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    return [explain_mongolian_token(token, lexicon) for token in tajik_tokens(text)]


def clean_tibetan_word(word: str) -> str:
    return word.strip().strip("་༌།༎༏༐༑༔")


TIBETAN_COMMON = parse_pipe_lexicon(
    """
བཅུག|put; let|verb form
གཟབ|careful|adjective component
པོས|adjectival suffix + ergative|suffix form
འཛུལ|enter|verb
རྗེས|after|postposition
ཁྱིས|dog + ergative|ergative form
གྲི|knife|noun
ཆས|things; equipment|noun
ཆེན|big; great|adjective component
ཕར|away; over there|direction word
བརྟག|check; examine|verb
བྱའི|bird + genitive|genitive form
ཚ|hot|adjective component
འབྲི|write; draw|verb
རྩེད|play|verb/noun
ཁར|at; on|postposition form
ཆད|cut; broken|verb/adjective
ཆུས|water + ergative|ergative form
ཐོན|come out|verb
དཀྲིས|wrapped; tied|verb form
དབྱར|summer|season
ཕྱིར|back; outside|direction word
བཅད|cut|past verb
བཏོན|took out|past verb
བསྟན|showed|past verb
བྱུགས|spread; applied|past verb
མིས|person + ergative|ergative form
ཚོར|felt; sense|verb form
འཆང|hold; carry|verb
འཚོལ|look for|verb
སྔོན|before; earlier|time word
སྨྱུ|pen; reed pen|noun component
ཀས|pillar/post + ergative|ergative form
ཁེངས|full; filled|adjective/verb
ཁྱིའི|dog + genitive|genitive form
གཙང|clean|adjective component
གྲུ|boat; corner|noun
ཐིག|line; drop|noun
པོའི|adjectival suffix + genitive|suffix form
ཕས|father + ergative|ergative form
བཀབ|covered|past verb
བཏང|sent; let go|past verb
བཏུབས|cut|past verb
བརྐོས|dug; carved|past verb
བརྗེ|change; exchange|verb
བས|by; because|particle
བོ|nominal suffix|suffix
བླངས|took|past verb
མཆིན|liver|noun component
མདོ|main point; area|noun
མཛུབ|finger|noun component
མའི|mother/female suffix + genitive|genitive form
ཚྭའི|salt + genitive|genitive form
ཞི|gentle; peaceful|adjective component
ཞིང|field|noun
འགག|blocked; stopped|verb/adjective
འཐོན|come out|verb
འདྲ|like; similar|adjective
འཕར|jump; increase|verb
འབུས|bug + ergative|ergative form
འཛུམ|smile|verb/noun
རིང|long|adjective component
རུང|may; suitable|modal/adjective
རུས|bone|noun component
རོ|taste; corpse|noun
རྐང|leg; foot|noun component
རྒྱུ|guts; material; will|noun
རྒྱུགས|run|verb form
རྙེད|found|past verb
རྟུལ|dull|adjective component
རྣ|ear|noun component
ལག|hand|noun component
ལན|answer; time|noun
ལིམ|lemon|noun component
ལྗིད|heavy|adjective component
ལྷག|remain; extra|verb/adjective
ལྷམ|shoe|noun
སྐུད|string; thread|noun
སྐྱ|gray|adjective component
སྔོ|blue; green|adjective component
    """
)


TIBETAN_SUFFIXES = [
    ("འི", "genitive form"),
    ("ཡི", "genitive form"),
    ("ཀྱི", "genitive form"),
    ("གྱི", "genitive form"),
    ("གི", "genitive form"),
    ("ས", "ergative/instrumental form"),
    ("ར", "dative/locative form"),
    ("ལ", "dative/locative form"),
]


def build_tibetan_lexicon(vocab_path: Path) -> dict[str, dict[str, str]]:
    raw: dict[str, dict[str, str]] = {}
    raw.update(load_existing_explanation_lexicon(vocab_path.parent, "tibetan"))
    raw.update(load_vocab_lexicon(vocab_path))
    raw.update(TIBETAN_COMMON)
    lexicon: dict[str, dict[str, str]] = {}
    for word, item in raw.items():
        cleaned = clean_tibetan_word(word)
        if cleaned:
            lexicon[cleaned] = explanation(cleaned, item["gloss"], item.get("note"))
    return lexicon


def tibetan_has_boundary(text: str, index: int) -> bool:
    return index >= len(text) or text[index] in TIBETAN_DELIMITERS


def match_tibetan_word(
    text: str,
    index: int,
    keys: list[str],
    lexicon: dict[str, dict[str, str]],
) -> tuple[str, str, str | None] | None:
    for key in keys:
        if not text.startswith(key, index):
            continue
        end = index + len(key)
        if tibetan_has_boundary(text, end):
            return key, key, lexicon[key].get("note")
        for suffix, note in TIBETAN_SUFFIXES:
            suffix_end = end + len(suffix)
            if text.startswith(suffix, end) and tibetan_has_boundary(text, suffix_end):
                return text[index:suffix_end], key, note
    return None


def explain_tibetan_sentence(
    text: str,
    lexicon: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    keys = sorted(lexicon, key=lambda item: (-len(item), item))
    words: list[dict[str, str]] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char in TIBETAN_DELIMITERS:
            index += 1
            continue

        matched = match_tibetan_word(text, index, keys, lexicon)
        if matched:
            surface, key, suffix_note = matched
            base = lexicon[key]
            words.append(explanation(surface, base["gloss"], suffix_note or base.get("note")))
            index += len(surface)
            continue

        end = index
        while end < len(text) and text[end] not in TIBETAN_DELIMITERS:
            end += 1
        token = clean_tibetan_word(text[index:end])
        if token:
            words.append(explanation(token, token, UNKNOWN_NOTE))
        index = end
    return words


THAI_COMMON = parse_pipe_lexicon(
    """
ก็|also; then|particle
จึง|so; therefore|connector
แล้ว|already; then|aspect particle
ให้|give; for; let|verb/function word
ไว้|keep;ไว้ aspect|aspect particle
ไว้ใน|kept in|phrase
ไป|go|verb
มา|come|verb
ได้|can; get|auxiliary
ไม่ได้|cannot; did not get|negative auxiliary
เป็น|be; become|verb
คือ|is; means|copula
มี|have; there is|verb
ไม่มี|do not have; there is no|negative verb
อยู่|be at; stay|verb
ไหม|question particle|particle
หรือ|or|conjunction
และ|and|conjunction
แต่|but|conjunction
เพราะ|because|conjunction
ถ้า|if|conjunction
กับ|with|preposition
ของ|of; belonging to|possessive marker
จาก|from|preposition
ถึง|to; arrive|preposition/verb
ใน|in|preposition
บน|on|preposition
ใต้|under|preposition
หน้า|front; face|noun/preposition
หลัง|behind; after; back|noun/preposition
ข้าง|beside; side|noun/preposition
ระหว่าง|between; during|preposition
ใกล้|near|adjective/preposition
ไกล|far|adjective
ที่|at; that; which|function word
นี้|this|demonstrative suffix
นั้น|that|demonstrative suffix
ทุก|every|determiner
หลาย|many|determiner
มาก|very; many|adverb
น้อย|little; few|adjective
นิดหน่อย|a little|adverb
กว่า|than|comparison marker
ขึ้น|up; more|verb/adverb
ก่อน|before|time word
หลังจาก|after|time phrase
ตอน|at the time of|time word
กลาง|middle|noun/adjective
กลางวัน|daytime|time word
กลางคืน|nighttime|time word
เที่ยง|noon|time word
บ่าย|afternoon|time word
ทุ่ม|evening hour unit|time unit
โมง|o'clock|time unit
ครั้ง|time; occasion|classifier
ใบ|sheet/container classifier|classifier
เล่ม|book classifier|classifier
ลูก|round object classifier; child|classifier/noun
คน|person; people classifier|noun/classifier
ตัว|animal/object classifier|classifier
คัน|vehicle/fork classifier|classifier
ด้าม|pen/handle classifier|classifier
ฟอง|egg classifier|classifier
แก้ว|glass; cup|noun/classifier
ถ้วย|cup; bowl|noun/classifier
ชิ้น|piece|classifier
กล่อง|box|noun/classifier
ขวด|bottle|noun/classifier
ถุง|bag|noun/classifier
บาท|baht|money unit
ครับ|polite particle|male speech particle
ค่ะ|polite particle|female speech particle
นะ|softening particle|particle
กรุณา|please|polite request word
อย่า|do not|negative imperative
ไม่|not|negative particle
ยัง|still; yet|adverb
เท่านั้น|only|adverb
เอง|by oneself|adverb
กัน|together; each other|reciprocal particle
เลย|at all; very|particle
พอ|enough|adjective
ไปก่อน|go first; leave now|phrase
ของคุณ|yours|possessive phrase
อย่าง|in a way; kind|function word
อย่างไร|how|question word
อย่างระวัง|carefully|adverbial phrase
อย่างสุภาพ|politely|adverbial phrase
อย่างอ่อนโยน|gently|adverbial phrase
ช้าๆ|slowly|adverb
เบาๆ|softly|adverb
ไกลๆ|far away|adverb
ง่ายๆ|simple; simply|adverb/adjective
กำลัง|currently|progressive marker
จะ|will|future marker
ต้อง|must; need to|modal verb
อยาก|want to|verb
สามารถ|can; be able to|modal verb
ควร|should|modal verb
ทำให้|make; cause|verb phrase
ทำงาน|work|verb phrase
ทำการบ้าน|do homework|verb phrase
ทำอาหาร|make food|verb phrase
เลิกเรียน|finish school|verb phrase
รอรถเมล์|wait for the bus|verb phrase
รถเมล์|bus|noun
รถไฟ|train|noun
รถไฟฟ้า|electric train|noun
แท็กซี่|taxi|noun
จักรยาน|bicycle|noun
เครื่องบิน|airplane|noun
กรุงเทพ|Bangkok|place name
เมืองไทย|Thailand|place name
ครอบครัว|family|noun
ครู|teacher|noun
นักเรียน|student|noun
เด็ก|child|noun
เพื่อน|friend|noun
พ่อ|father|noun
แม่|mother|noun
พี่|older sibling|noun
น้อง|younger sibling|noun
ยาย|grandmother|noun
ตา|grandfather; eye|noun
ปู่|grandfather|noun
ย่า|grandmother|noun
ลูก|child; round-object classifier|noun/classifier
ข้าว|rice; meal|noun
น้ำ|water|noun
อาหาร|food|noun
ภาษาไทย|Thai language|noun
ภาษาอังกฤษ|English language|noun
ชื่อ|name|noun
เรื่อง|story; matter|noun
ทาง|way; road|noun
บ้าน|home; house|noun
ห้อง|room|noun
ห้องเรียน|classroom|noun
โรงเรียน|school|noun
ตลาด|market|noun
ร้าน|shop|noun
ร้านอาหาร|restaurant|noun
โรงพยาบาล|hospital|noun
สถานี|station|noun
สนามบิน|airport|noun
โรงแรม|hotel|noun
วัด|temple|noun
สวน|park; garden|noun
ทะเล|sea|noun
ภูเขา|mountain|noun
แม่น้ำ|river|noun
ถนน|road|noun
บนฟ้า|in the sky|phrase
สี|color|noun
แดง|red|adjective
ดำ|black|adjective
ขาว|white|adjective
เขียว|green|adjective
เหลือง|yellow|adjective
น้ำเงิน|blue|adjective
สีน้ำตาล|brown|color adjective
สีดำ|black|color adjective
สีขาว|white|color adjective
สีแดง|red|color adjective
สีเขียว|green|color adjective
สีเหลือง|yellow|color adjective
แล้ว|already|aspect particle
ว่า|that; says that|connector
ด้วย|with; also|function word
แก่|to; for|formal preposition
สำหรับ|for|preposition
ต่อ|per; next to|preposition
อุ่น|warm|adjective
หยุด|stop|verb
ตื่น|wake up|verb
ไทย|Thai|adjective/noun
ริม|edge; along|preposition/noun
ดอกไม้|flower|noun
ทอด|fry|verb
แบ่ง|share; divide|verb
ตก|fall; rain falls|verb
แรง|strong|adjective
ข้อสอบ|test; exam question|noun
ตัวเลข|number; digit|noun
ประโยค|sentence|noun
เบอร์|number|noun
ลงท้าย|end with|verb
อายุ|age|noun
ตัก|scoop|verb
หั่น|cut; slice|verb
เตา|stove|noun
ผนัง|wall|noun
พับ|fold|verb
ลบ|erase|verb
มอง|look at|verb
ซ่อม|repair|verb
จอด|park; stop|verb
ข้าม|cross; across|verb/preposition
เห็น|see|verb
ทราย|sand|noun
แยก|separate; intersection|verb/noun
หนังสือพิมพ์|newspaper|noun
เตรียม|prepare|verb
ชนิด|kind; type|noun
เม็ด|small round item classifier|classifier/noun
คม|sharp|adjective
พัด|blow; fan|verb/noun
พี่ชาย|older brother|noun
ตึก|building|noun
อื่น|other|adjective
วงกลม|circle|noun
จันทร์|Monday|day name
เลข|number; digit|noun
เล็กๆ|small; little|adverb/adjective
วง|circle; ring|noun
ซ้าย|left|direction
การ|nominalizing prefix|grammar prefix
หนัง|movie; leather|noun
เมื่อ|when|time connector
แตก|break; broken|verb/adjective
ความ|abstract noun prefix|grammar prefix
หมา|dog|noun
ปลอบ|comfort; soothe|verb
สดใส|bright; cheerful|adjective
ใส|clear; bright|adjective
ได้ยิน|hear|verb
เจ็บ|hurt; sore|adjective/verb
ไอ|cough|verb
แปรง|brush|verb/noun
หวี|comb|verb/noun
อาบ|bathe|verb
ต้น|tree; stem; classifier|noun/classifier
เก็บ|collect; keep|verb
หญ้า|grass|noun
ทุ่ง|field|noun
ดูแล|care for; look after|verb
สัตว์|animal|noun
บ่อ|pond; pit|noun
ตรวจ|check; inspect|verb
ผ่าน|pass through|verb/preposition
ถ่าย|take a photo; transfer|verb
สุภาพ|polite|adjective
ฟรี|free of charge|adjective
หอม|fragrant|adjective
ร่างกาย|body|noun
แข็งแรง|strong; healthy|adjective
ท้าย|end; back part|noun
เกิน|too; exceed|adverb/verb
ห่าง|far from; apart|adjective/verb
กิโลเมตร|kilometer|noun
แก้|fix; solve|verb
อบอุ่น|warm; cozy|adjective
ปลูก|plant; grow|verb
นา|rice field|noun
เวที|stage|noun
ซ้อม|practice; rehearse|verb
อาคาร|building|noun
แขวน|hang|verb
กอด|hug|verb
นุ่ม|soft|adjective
ค่า|fee; cost|noun prefix
คำ|word|noun
คำศัพท์|vocabulary word|noun
หมด|finished; all gone|adjective/verb
สระ|pool; vowel|noun
เพื่อ|for; in order to|purpose marker
ใจดี|kind|adjective
คุย|chat|verb
เรียก|call|verb
ช้าๆ|slowly|adverb
สั้นๆ|short; briefly|adverb/adjective
ท่า|pier; posture|noun
ทางซ้าย|to the left|direction phrase
วันจันทร์|Monday|day name
นิด|a little|adverb
แผ่น|sheet; flat classifier|noun/classifier
แตงกวา|cucumber|noun
บางๆ|thinly|adverb
ลุง|uncle|noun
ห้าม|must not; forbid|negative imperative
เลื้อย|crawl; slither|verb
ไม้|wood; tree|noun
ค้ำ|support; prop up|verb
ปลิว|blow away; flutter|verb
โผล่|emerge; show|verb
จับ|touch; hold|verb
ม้วน|roll up|verb
แขน|arm|noun
นิ้ว|finger|noun
หัก|broken; break|verb/adjective
แพะ|goat|noun
ควาย|buffalo|noun
แกว่ง|swing; wag|verb
ดม|smell; sniff|verb
ตัน|blocked; stuffy|adjective
ชิม|taste|verb
แลบ|stick out|verb
ยก|lift|verb
ล้ม|fall|verb
กาง|spread; open|verb
อักเสบ|inflamed|adjective/verb
รอบ|around|preposition/noun
ก้อน|lump; piece classifier|noun/classifier
ติด|stick to; attached|verb
กระถาง|pot; planter|noun
เหนือ|above; north|preposition/direction
ญี่ปุ่น|Japan|place name
ฤดูหนาว|winter|season
แรก|first|adjective
ไหม้|burn; be on fire|verb
ดับ|put out; go out|verb
แตะ|touch|verb
กองไฟ|fire pit; campfire|noun
ชาวสวน|gardener|noun
จน|until; so that|connector
ขยะ|trash|noun
หลับ|sleep; asleep|verb/adjective
คู่|pair; couple|noun/classifier
รู้สึก|feel|verb
ถังขยะ|trash can|noun
เส้น|line; noodle/thread classifier|noun/classifier
ระวัง|be careful|verb
บาด|cut; wound|verb
กรรไกร|scissors|noun
รอย|mark; trace|noun
เลี้ยว|turn|verb
ผ้าพันคอ|scarf|noun
พัน|wrap|verb
แบก|carry on the back|verb
ผัด|stir-fry|verb
ยุง|mosquito|noun
หลอด|straw; tube|noun
บ้วน|rinse; spit out|verb
เมารถ|carsick|adjective
ลึกๆ|deeply|adverb
เชื้อ|germ; infection|noun
แมลง|insect|noun
ทีม|team|noun
หนู|mouse; rat; child pronoun|noun/pronoun
เสือ|tiger|noun
เหยื่อ|prey; victim|noun
บอล|ball|noun
ลูกบอล|ball|noun
ชาม|bowl|noun
ฟืน|firewood|noun
แผล|wound|noun
หนาม|thorn|noun
แหลม|sharp; pointed|adjective
ขาด|torn; broken|adjective/verb
เข็ม|needle|noun
หลุม|hole|noun
เสื่อ|mat|noun
หงาย|face up; on one's back|adverb/verb
พลาสติก|plastic|noun/adjective
แถว|line; row|noun
กระดุม|button|noun
น้ำปั่น|smoothie|noun
ลูกโป่ง|balloon|noun
เป่า|blow|verb
ลับ|set; disappear behind|verb
ดวง|celestial/body classifier|classifier/noun
ทั้ง|all; whole|determiner
    """
)


def build_tajik_lexicon(vocab_path: Path) -> dict[str, dict[str, str]]:
    lexicon = {
        key.lower(): value
        for key, value in load_existing_explanation_lexicon(vocab_path.parent, "tajik").items()
    }
    lexicon.update({key.lower(): value for key, value in load_vocab_lexicon(vocab_path).items()})
    lexicon.update({key.lower(): value for key, value in TAJIK_COMMON.items()})
    return lexicon


def tajik_tokens(text: str) -> list[str]:
    return [match.group(0).strip(PUNCTUATION) for match in CYRILLIC_WORD.finditer(text)]


def explain_tajik_token(token: str, lexicon: dict[str, dict[str, str]]) -> dict[str, str]:
    normalized = token.strip(PUNCTUATION)
    key = normalized.lower()
    if key in lexicon:
        base = lexicon[key]
        return explanation(normalized, base["gloss"], base.get("note"))

    for suffix, note in [
        ("ҳоро", "plural with object marker -ро"),
        ("ҳои", "plural/ezafe form"),
        ("ҳоямро", "plural with my + object marker"),
        ("ҳояшро", "plural with his/her + object marker"),
        ("ҳо", "plural form"),
        ("они", "plural + ezafe form"),
        ("амро", "my + object marker -ро"),
        ("атро", "your + object marker -ро"),
        ("ашро", "his/her + object marker -ро"),
        ("ро", "with object marker -ро"),
        ("амон", "with possessive suffix"),
        ("атон", "with possessive suffix"),
        ("ашон", "with possessive suffix"),
        ("ям", "with first-person possessive suffix"),
        ("ам", "with possessive/person suffix"),
        ("ат", "with possessive/person suffix"),
        ("аш", "with possessive suffix"),
        ("он", "plural form"),
        ("и", "ezafe/attributive form"),
    ]:
        if key.endswith(suffix) and len(key) > len(suffix):
            base_key = key[: -len(suffix)]
            if base_key in lexicon:
                base = lexicon[base_key]
                return explanation(normalized, base["gloss"], note)

    if key.startswith("наме") or key.startswith("ме"):
        is_negative = key.startswith("наме")
        stem_with_ending = key[4:] if is_negative else key[2:]
        for ending, person_note in [
            ("ам", "first person present"),
            ("ӣ", "second person present"),
            ("ад", "third person present"),
            ("яд", "third person present"),
            ("ем", "first person plural present"),
            ("ед", "second person plural present"),
            ("анд", "third person plural present"),
        ]:
            if stem_with_ending.endswith(ending):
                stem = stem_with_ending[: -len(ending)]
                if stem in TAJIK_VERB_STEMS:
                    gloss, stem_note = TAJIK_VERB_STEMS[stem]
                    note = f"{person_note}; {stem_note}"
                    if is_negative:
                        note = f"negative {note}"
                    return explanation(normalized, gloss, note)

    if key in TAJIK_PAST_STEMS:
        gloss, stem_note = TAJIK_PAST_STEMS[key]
        return explanation(normalized, gloss, stem_note)

    for ending, person_note in [
        ("ам", "first person past"),
        ("ӣ", "second person past"),
        ("ем", "first person plural past"),
        ("ед", "second person plural past"),
        ("анд", "third person plural past"),
    ]:
        if key.endswith(ending) and len(key) > len(ending):
            stem = key[: -len(ending)]
            if stem in TAJIK_PAST_STEMS:
                gloss, stem_note = TAJIK_PAST_STEMS[stem]
                return explanation(normalized, gloss, f"{person_note}; {stem_note}")

    return explanation(normalized, normalized, UNKNOWN_NOTE)


def explain_tajik_sentence(
    text: str,
    lexicon: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    return [explain_tajik_token(token, lexicon) for token in tajik_tokens(text)]


def build_thai_lexicon(vocab_path: Path) -> dict[str, dict[str, str]]:
    lexicon = load_existing_explanation_lexicon(vocab_path.parent, "thai")
    lexicon.update(load_vocab_lexicon(vocab_path))
    lexicon.update(THAI_COMMON)
    return lexicon


def thai_bad_single_token(token: str) -> bool:
    return len(token) == 1 and (token in THAI_COMBINING_MARKS or token == "ๆ" or bool(THAI_BLOCK.match(token)))


def explain_thai_sentence(
    text: str,
    lexicon: dict[str, dict[str, str]],
    cloze_word: str | None = None,
) -> list[dict[str, str]]:
    cloze = cloze_word.strip(PUNCTUATION) if cloze_word else None
    words_by_first: dict[str, list[str]] = {}
    for word in sorted(lexicon, key=lambda item: (-len(item), item)):
        if word:
            words_by_first.setdefault(word[0], []).append(word)

    def add_score(
        left: tuple[int, int, int, int, int],
        right: tuple[int, int, int, int, int],
    ) -> tuple[int, int, int, int, int]:
        return tuple(a + b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]

    @lru_cache(maxsize=None)
    def best(index: int, seen_cloze: bool) -> tuple[tuple[int, int, int, int, int], tuple[str, ...]]:
        if index >= len(text):
            return ((0 if seen_cloze or not cloze else 1, 0, 0, 0, 0), ())

        char = text[index]
        if char.isspace() or char in PUNCTUATION:
            return best(index + 1, seen_cloze)

        options: list[tuple[tuple[int, int, int, int, int], tuple[str, ...]]] = []
        for word in words_by_first.get(char, []):
            if not text.startswith(word, index):
                continue
            next_seen = seen_cloze or word == cloze or bool(
                cloze and word == f"{cloze}ๆ"
            )
            tail_score, tail_words = best(index + len(word), next_seen)
            score = add_score((0, 0, 1 if thai_bad_single_token(word) else 0, 1, -len(word)), tail_score)
            options.append((score, (word, *tail_words)))

        tail_score, tail_words = best(index + 1, seen_cloze)
        unknown_score = add_score((0, 1, 1 if thai_bad_single_token(char) else 0, 1, -1), tail_score)
        options.append((unknown_score, (char, *tail_words)))

        return min(options, key=lambda item: item[0])

    _, tokens = best(0, False)
    explanations: list[dict[str, str]] = []
    for token in tokens:
        if token in lexicon:
            item = lexicon[token]
            explanations.append(add_paiboon(explanation(token, item["gloss"], item.get("note"))))
        else:
            explanations.append(add_paiboon(explanation(token, token, UNKNOWN_NOTE)))
    return explanations


def build_explanations_from_corpus(
    corpus_path: Path,
    vocab_path: Path,
    language: str,
) -> dict[str, list[dict[str, object]]]:
    corpus = read_json(corpus_path)["data"]
    vocab_lexicon = load_vocab_lexicon(vocab_path)
    if language == "mongolian":
        lexicon = build_mongolian_lexicon(vocab_path)
        explain = explain_mongolian_sentence
    elif language == "tibetan":
        lexicon = build_tibetan_lexicon(vocab_path)
        explain = explain_tibetan_sentence
    elif language == "tajik":
        lexicon = build_tajik_lexicon(vocab_path)
        explain = explain_tajik_sentence
    elif language == "thai":
        lexicon = build_thai_lexicon(vocab_path)
        explain = explain_thai_sentence
    else:
        raise ValueError(f"unsupported language: {language}")

    rows = []
    for row in corpus:
        target = row["translations"][0]["text"]
        if language == "thai":
            words = explain_thai_sentence(target, lexicon, row.get("cloze_word"))
        else:
            words = explain(target, lexicon)
        cloze = str(row.get("cloze_word") or "")
        cloze_key = cloze.lower()
        vocab_item = (
            vocab_lexicon.get(cloze)
            or vocab_lexicon.get(cloze_key)
            or vocab_lexicon.get(cloze.strip(PUNCTUATION))
        )
        if vocab_item:
            for word in words:
                if word["word"].strip(PUNCTUATION).lower() == cloze_key:
                    word["gloss"] = vocab_item["gloss"]
                    if "note" in vocab_item:
                        word["note"] = vocab_item["note"]
                    elif "note" in word:
                        word.pop("note")
                    break
        rows.append({"id": row["id"], "words": words})
    return {"data": rows}


def write_explanations_from_corpus(
    corpus_path: Path,
    vocab_path: Path,
    output_path: Path,
    language: str,
) -> None:
    write_json(output_path, build_explanations_from_corpus(corpus_path, vocab_path, language))


def collect_unknowns(explanations: dict[str, Any]) -> dict[str, int]:
    unknowns: dict[str, int] = {}
    for row in explanations["data"]:
        for word in row["words"]:
            if word.get("note") == UNKNOWN_NOTE:
                unknowns[word["word"]] = unknowns.get(word["word"], 0) + 1
    return dict(sorted(unknowns.items(), key=lambda item: (-item[1], item[0])))
