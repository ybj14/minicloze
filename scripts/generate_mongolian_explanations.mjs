import fs from "node:fs";

const corpusPath = new URL("../minicloze-lib/corpora/mongolian_a1.json", import.meta.url);
const vocabPath = new URL("../minicloze-lib/corpora/mongolian_a1_vocab.json", import.meta.url);
const outputPath = new URL(
  "../minicloze-lib/corpora/mongolian_a1_explanations.json",
  import.meta.url,
);

const corpus = JSON.parse(fs.readFileSync(corpusPath, "utf8"));
const vocab = JSON.parse(fs.readFileSync(vocabPath, "utf8"));

const exact = new Map();
const stems = new Map();
const verbStems = new Map();

function entry(gloss, note) {
  return note ? { gloss, note } : { gloss };
}

function key(word) {
  return word.toLocaleLowerCase("mn");
}

function e(word, gloss, note) {
  exact.set(word, entry(gloss, note));
  exact.set(key(word), entry(gloss, note));
}

function s(word, gloss) {
  stems.set(word, gloss);
  stems.set(key(word), gloss);
  if (!exact.has(word)) e(word, gloss);
}

function v(stem, gloss) {
  verbStems.set(stem, gloss);
  verbStems.set(key(stem), gloss);
}

const vocabGlossOverrides = {
  өөрийн: "own",
  тэр: "he; she; that",
  нь: "his/her; topic marker",
  байна: "is; are",
  өөр: "other; another",
  унтраах: "turn off",
  сайн: "good; well",
  эрэгтэй: "male; man",
  хүн: "person",
  дарга: "boss; leader",
  дэлхийн: "world; of the Earth",
  тусламж: "help",
  хамгаалах: "protect; cover",
  нүдний: "eye; of the eye",
  гаталж: "crossing",
  далайн: "sea; of the sea",
  урсгал: "current; flow",
  сонсооч: "please listen",
  шийдвэр: "decision",
  загвар: "model; design; style",
  акт: "act; document",
  шоу: "show",
  дулаан: "warm; warmth",
  хадгалах: "keep; save; store",
  хуваагдал: "division",
  тусгай: "special",
  хүнд: "heavy; to a person",
  зөөлөн: "soft; gentle",
  агшин: "moment",
  орө: "ore (shouted word)",
  цусны: "blood; of blood",
  хөлөө: "one's leg",
  орохдоо: "when entering",
  хувцаслан: "clothe; dress",
  илааршсан: "recovered",
  эмэгтэй: "woman; female",
  талбай: "square; field; yard",
  хувь: "percent; share",
  холино: "will mix",
  баг: "team",
  утас: "phone; wire",
  цохилт: "beat; knock; hit",
  нэгдэхийг: "to join",
};

for (const item of vocab) {
  e(item.word, vocabGlossOverrides[item.word] ?? item.gloss);
  stems.set(item.word, vocabGlossOverrides[item.word] ?? item.gloss);
  stems.set(key(item.word), vocabGlossOverrides[item.word] ?? item.gloss);
}

// Pronouns, particles, and common function words.
[
  ["Би", "I"], ["би", "I"], ["Чи", "you"], ["чи", "you"], ["Та", "you", "formal"],
  ["Бид", "we"], ["бид", "we"], ["Тэд", "they"], ["тэд", "they"],
  ["Тэр", "he; she; that"], ["тэр", "he; she; that"],
  ["Энэ", "this"], ["энэ", "this"], ["эдгээр", "these"], ["тэдгээр", "those"],
  ["нөгөө", "the other"], ["өөр", "other; another"], ["өөрийн", "own"],
  ["өөрөө", "oneself"], ["Миний", "my"], ["миний", "my"], ["Чиний", "your"], ["чиний", "your"],
  ["таны", "your", "formal"], ["Манай", "our"], ["манай", "our"], ["манайд", "at our place"],
  ["Манайд", "at our place"], ["маань", "our; my", "possessive particle"], ["минь", "my"],
  ["над", "me"], ["надад", "to me; I have", "dative pronoun"], ["Надад", "to me; I have", "dative pronoun"],
  ["надаас", "from me"], ["надтай", "with me"], ["намайг", "me", "accusative pronoun"],
  ["Намайг", "me", "accusative pronoun"], ["чамд", "to you"], ["Чамд", "to you"],
  ["чамайг", "you", "accusative pronoun"], ["биднийг", "us"], ["бидэнд", "to us"], ["Бидэнд", "to us"],
  ["түүнд", "to him/her"], ["Түүнд", "to him/her"], ["түүний", "his; her"], ["Түүний", "his; her"],
  ["түүнийг", "him; her", "accusative pronoun"], ["түүнээс", "from him/her"],
  ["тэдний", "their"], ["тэднийг", "them"], ["үүнийг", "this", "accusative pronoun"],
  ["нь", "his/her; topic marker"], ["юу", "what"], ["хэн", "who"], ["хаана", "where"],
  ["яагаад", "why"], ["хэрхэн", "how"], ["ямар", "what kind of"], ["аль", "which"],
  ["Хэрэв", "if"], ["хэрэв", "if"], ["бол", "is; as for", "topic/copula particle"],
  ["ба", "and"], ["болон", "and"], ["буюу", "or"], ["харин", "but"], ["боловч", "but"],
  ["тул", "because"], ["тэгээд", "then"], ["гэж", "that; as", "quotative/linking particle"],
  ["гээд", "saying; and then"], ["шиг", "like; as if"], ["мэт", "as if; like"],
  ["тийм", "so; yes"], ["ийм", "such; this kind of"], ["Ийм", "such; this kind of"],
  ["яг", "exactly"], ["Яг", "exactly"], ["магадгүй", "perhaps"], ["Мэдээж", "of course"],
  ["мөн", "also; too"], ["ч", "also; even"], ["лүү", "toward"], ["руу", "toward"], ["рүү", "toward"],
  ["рүүгээ", "toward one's own place"], ["дээр", "on; over"], ["дээрээ", "on oneself/itself"],
  ["дээрээс", "from above; from on"], ["доор", "under"], ["дотор", "inside"], ["дунд", "among; in the middle"],
  ["дэргэд", "near; beside"], ["хажууд", "beside"], ["хажуугаар", "by; past"], ["цаанаас", "from behind"],
  ["ард", "behind"], ["урд", "front; south"], ["зүүн", "left; east"], ["баруун", "right; west"],
  ["хойд", "north"], ["тийш", "that way"], ["энд", "here"], ["Энд", "here"], ["эндээс", "from here"],
  ["тэнд", "there"], ["Тэнд", "there"], ["гадаа", "outside"], ["Гадаа", "outside"], ["гэртээ", "at home"],
  ["гэрт", "at home"], ["ойроос", "from nearby; up close"], ["ойролцоо", "nearby"], ["Ойролцоо", "nearby"],
  ["ойрхон", "nearby"], ["холоос", "from far away"], ["хамт", "together; with"], ["хамтдаа", "together"],
  ["дагуу", "along; according to"], ["хооронд", "between"], ["хүртэл", "until; up to"], ["дараа", "after"],
  ["Дараа", "after"], ["өмнө", "before; ago"], ["үед", "during; at the time of"], ["бүх", "all; every"],
  ["бүгд", "all; everyone"], ["бүгдийг", "everything; everyone", "accusative"], ["бүр", "every; each"],
  ["бус", "not; other"], ["бусад", "other"], ["бусдад", "to others"], ["Бусдын", "others'; of others"],
  ["олон", "many"], ["нэг", "one"], ["Нэг", "one"], ["хоёр", "two"], ["Хоёр", "two"], ["гурван", "three"],
  ["дөрвөн", "four"], ["таван", "five"], ["Таван", "five"], ["зургаан", "six"], ["долоон", "seven"],
  ["Долоо", "seven"], ["найман", "eight"], ["есөн", "nine"], ["арван", "ten"], ["зуун", "hundred"],
  ["мянган", "thousand"], ["сая", "million"], ["хэдэн", "how many; several"], ["хэдийн", "already"],
  ["аль хэдийн", "already"], ["уу", "question/please particle"], ["үү", "question/please particle"],
  ["вэ", "question particle"], ["бэ", "question particle"], ["вий", "lest; might"], ["аа", "vocative particle"],
  ["өө", "uh; oh"], ["А", "A", "letter name"], ["ёстой", "should; must"], ["Битгий", "do not"],
  ["болгоомжтой", "carefully"], ["Болгоомжтой", "be careful"], ["Уучлаарай", "sorry; excuse me"],
  ["Баярлалаа", "thank you"], ["баяртай", "happy; goodbye"], ["алга", "absent; gone"],
  ["Алга", "gone; missing"], ["бий", "exists; there is"], ["байхгүй", "is not; absent"],
  ["хэрэггүй", "unnecessary"], ["болохгүй", "cannot; must not"], ["одоогоор", "for now"], ["Одоо", "now"],
  ["одоо", "now"], ["өнөө", "this; today"], ["Өнөө", "this; today"], ["өнөөдөр", "today"],
  ["Өнөөдөр", "today"], ["өчигдөр", "yesterday"], ["Өчигдөр", "yesterday"], ["маргааш", "tomorrow"],
  ["Маргааш", "tomorrow"], ["маргаашийн", "tomorrow's"], ["удахгүй", "soon"], ["Заримдаа", "sometimes"],
  ["түр", "for a short while"], ["нам", "quiet; low"], ["гүм", "silent"], ["хэт", "too; overly"], ["Хэт", "too; overly"],
].forEach(([word, gloss, note]) => e(word, gloss, note));

// Common nouns and adjective stems that appear outside the target vocabulary.
[
  ["аав", "father"], ["ээж", "mother"], ["эгч", "older sister"], ["ах", "older brother"],
  ["дүү", "younger sibling"], ["өвөө", "grandfather"], ["эмээ", "grandmother"], ["багш", "teacher"],
  ["эмч", "doctor"], ["өвчтөн", "patient"], ["оюутан", "student"], ["зочид", "guests"], ["зөөгч", "waiter"],
  ["хүүхэд", "child"], ["хүүхдүүд", "children"], ["хүмүүс", "people"], ["найз", "friend"], ["хөрш", "neighbor"],
  ["Сараа", "Saraa", "person name"], ["Бат", "Bat", "person name"],
  ["гэр", "home; yurt"], ["байр", "apartment; place"], ["хот", "city"], ["сургууль", "school"],
  ["цэцэрлэг", "kindergarten; garden"], ["анги", "class"], ["өрөө", "room"], ["дэлгүүр", "store"],
  ["оффис", "office"], ["эмнэлэг", "hospital"], ["музей", "museum"], ["Парк", "park"], ["парк", "park"],
  ["клуб", "club"], ["сүм", "church"], ["Сүм", "church"], ["буудал", "station"], ["үйлдвэр", "factory"],
  ["ордон", "palace"], ["талбай", "square; field"], ["талбар", "field"], ["гудамж", "street"], ["зам", "road"],
  ["гүүр", "bridge"], ["хаалга", "door"], ["цонх", "window"], ["хана", "wall"], ["ханан", "wall"],
  ["шал", "floor"], ["Шалан", "floor"], ["ширээ", "table"], ["сандал", "chair"], ["ор", "bed"],
  ["тавиур", "shelf"], ["шүүгээ", "cabinet; cupboard"], ["хөргөгч", "refrigerator"], ["самбар", "board"],
  ["дэлгэц", "screen"], ["Дэлгэц", "screen"], ["тайз", "stage"], ["тал", "side"], ["булан", "corner"],
  ["зах", "edge; market"], ["эрэг", "shore; bank"],
  ["ном", "book"], ["дэвтэр", "notebook"], ["үзэг", "pen"], ["үсэг", "letter"], ["бичиг", "writing; letter"],
  ["захиа", "letter; note"], ["захидал", "letter"], ["хуудас", "page"], ["цаас", "paper"], ["цүнх", "bag"],
  ["үүргэвч", "backpack"], ["тасалбар", "ticket"], ["түлхүүр", "key"], ["утас", "phone; wire"],
  ["компьютер", "computer"], ["зураг", "picture"], ["зурагт", "television"], ["кино", "movie"], ["Кино", "movie"],
  ["машин", "car; machine"], ["автобус", "bus"], ["онгоц", "airplane"], ["такси", "taxi"], ["гитар", "guitar"],
  ["хөгжим", "music; instrument"], ["шатар", "chess"], ["тоглоом", "toy; game"], ["бөмбөг", "ball"],
  ["бөгж", "ring"], ["малгай", "hat"], ["ороолт", "scarf"], ["цамц", "shirt"], ["гутал", "shoe"],
  ["хувцас", "clothes"], ["алчуур", "towel"], ["сав", "container"], ["хайрцаг", "box"], ["аяга", "cup"],
  ["таваг", "plate"], ["тогоо", "pot"], ["хоол", "food"], ["шөл", "soup"], ["талх", "bread"],
  ["гурил", "flour"], ["жимс", "fruit"], ["алим", "apple"], ["гадил", "banana"], ["ногоо", "vegetables"],
  ["сүү", "milk"], ["цай", "tea"], ["давс", "salt"], ["бэлэг", "gift"], ["төгрөг", "togrog"],
  ["төлбөр", "payment"], ["цалин", "salary"], ["даалгавар", "assignment"], ["хариу", "answer"],
  ["тайлбар", "explanation"], ["төлөвлөгөө", "plan"], ["тэмдэглэл", "note"], ["мэдээ", "news"], ["мэдээлэл", "information"],
  ["асуулт", "question"], ["асуудал", "problem"], ["шийдвэр", "decision"], ["зөвшөөрөл", "permission"],
  ["боломж", "possibility; chance"], ["хэрэг", "matter; need"], ["тушаал", "order; command"], ["хууль", "law"],
  ["хурал", "meeting"], ["Хурал", "meeting"], ["судалгаа", "study; research"], ["шинжилгээ", "test; analysis"],
  ["туршилт", "test"], ["төрөл", "kind; type"], ["зүйл", "thing"], ["юм", "thing; is"],
  ["нэр", "name"], ["үг", "word"], ["өгүүлбэр", "sentence"], ["тоо", "number"], ["цэг", "point; dot"],
  ["шугам", "line"], ["хэлбэр", "shape"], ["тойрог", "circle"], ["загалмай", "cross"], ["өнцөг", "angle"],
  ["багц", "set"], ["баг", "team"], ["бүлэг", "group"], ["эгнээ", "row"], ["жагсаалт", "list"],
  ["дүрэм", "rule"], ["акт", "act; document"], ["паспорт", "passport"], ["гэрээ", "contract"],
  ["эрх", "right"], ["түүх", "story; history"], ["үлгэр", "fairy tale; story"], ["онигоо", "joke"],
  ["хошигнол", "joke"], ["ая", "tone; tune"], ["аялгуу", "melody"], ["дуу", "sound; song"],
  ["дуудлага", "call; pronunciation"], ["инээд", "laughter"], ["нулимс", "tear"], ["аймшиг", "fear"],
  ["хайр", "love"], ["гай", "trouble"], ["дайн", "war"], ["амьдрал", "life"], ["санаа", "idea"],
  ["өөрчлөлт", "change"], ["зуршил", "habit"], ["амралт", "rest; vacation"], ["завсарлага", "break"],
  ["дасгал", "exercise"], ["уралдаан", "race"], ["айлчлал", "visit"], ["аялал", "trip"], ["үзэсгэлэн", "exhibition"],
  ["урлаг", "art"], ["хичээл", "lesson; class"], ["ажил", "work"], ["ажлын", "work; of work"],
  ["бариа", "finish"], ["барианы", "finish; finishing"], ["жин", "weight"], ["хэмжээ", "size; amount"],
  ["урт", "long; length"], ["зузаан", "thick"], ["нарийн", "narrow; fine"], ["нимгэн", "thin"], ["өргөн", "wide"],
  ["өндөр", "high; tall"], ["богино", "short"], ["том", "big"], ["жижиг", "small"], ["бага", "little; small"],
  ["их", "much; very"], ["маш", "very"], ["сайн", "good; well"], ["сайхан", "nice; beautiful"],
  ["муу", "bad"], ["буруу", "wrong"], ["зөв", "correct; right"], ["цэвэр", "clean"], ["нойтон", "wet"],
  ["хуурай", "dry"], ["зөөлөн", "soft; gentle"], ["хатуу", "hard"], ["хүйтэн", "cold"], ["дулаан", "warm"],
  ["халуун", "hot"], ["сэрүүн", "cool"], ["амар", "easy; restful"], ["амархан", "easy"], ["амаргүй", "not easy"],
  ["хэцүү", "difficult"], ["хурдан", "fast; quickly"], ["удаан", "slow; long"], ["шууд", "straight; directly"],
  ["ойр", "near"], ["хол", "far"], ["холын", "distant"], ["хүнд", "heavy; to a person"], ["хүчтэй", "strong"],
  ["сул", "loose; weak"], ["тайван", "peaceful; calm"], ["хөгжилтэй", "fun"], ["завгүй", "busy"], ["завтай", "free"],
  ["бэлэн", "ready"], ["боломжтой", "possible; able"], ["энгийн", "simple; plain"], ["ердийн", "usual"],
  ["ерөнхий", "general"], ["тодорхой", "clear; definite"], ["нийтлэг", "common"], ["тусгай", "special"],
  ["бүрэн", "complete; fully"], ["нээлттэй", "open"], ["хаалттай", "closed"], ["онгорхой", "open; ajar"],
  ["хоосон", "empty"], ["аюултай", "dangerous"], ["аюулгүй", "safe"], ["үзэсгэлэнтэй", "beautiful"],
  ["сонирхолтой", "interesting"], ["амттай", "tasty"], ["гашуун", "bitter"], ["үнэтэй", "expensive"],
  ["үнэртэй", "smelly; with a smell"], ["тохиромжтой", "suitable"], ["чухал", "important"], ["элбэг", "abundant"],
  ["хачин", "strange"], ["зэрлэг", "wild"], ["бодит", "real"], ["цэлмэг", "clear"], ["уудам", "vast"],
  ["тод", "bright; clear"], ["чанга", "loud; tight"], ["намуухан", "gentle; quiet"], ["эрт", "early"],
  ["орой", "evening; late"], ["Орой", "evening"], ["шөнө", "night"], ["Шөнө", "at night"], ["өдөр", "day"],
  ["Өдөр", "day"], ["өглөө", "morning"], ["Өглөө", "morning"], ["жил", "year"], ["сар", "month; moon"],
  ["Сар", "Moon"], ["хоног", "day-night period"], ["цаг", "time; hour"], ["минут", "minute"], ["удаа", "time; occasion"],
  ["эхлэл", "start; beginning"], ["эхний", "first"], ["эхэнд", "at the beginning"], ["эцсийн", "final"],
  ["дараагийн", "next"], ["өнгөрсөн", "past; last"], ["өнөөгийн", "present; current"], ["сүүлээр", "late; at the end"],
  ["сансар", "space"], ["орчлон", "universe"], ["дэлхий", "Earth; world"], ["нар", "sun"], ["тэнгэр", "sky"],
  ["үүл", "cloud"], ["манан", "fog"], ["бороо", "rain"], ["цас", "snow"], ["салхи", "wind"], ["шуурга", "storm"],
  ["аянга", "lightning"], ["нуур", "lake"], ["далай", "sea; ocean"], ["гол", "river"], ["хүрхрээ", "waterfall"],
  ["суваг", "canal; channel"], ["уул", "mountain"], ["ой", "forest"], ["мод", "tree; wood"], ["навч", "leaf"],
  ["өвс", "grass"], ["цэцэг", "flower"], ["газар", "place; land; ground"], ["байгаль", "nature"], ["амьтан", "animal"],
  ["загас", "fish"], ["нохой", "dog"], ["муур", "cat"], ["Муур", "cat"], ["морь", "horse"], ["үнээ", "cow"],
  ["ялаа", "fly"], ["шувуу", "bird"], ["мангас", "monster"], ["чулуу", "stone"], ["чулуулгийн", "rock; of rock"],
  ["мөс", "ice"], ["гал", "fire"], ["Гал", "fire"], ["хий", "gas"], ["долгион", "wave"], ["долгионы", "wave; of a wave"],
  ["материал", "material"], ["алт", "gold"], ["мөнгө", "money; silver"], ["төмөр", "iron"], ["шил", "glass"],
  ["шилэн", "glass; made of glass"], ["эсгий", "felt"], ["үр", "seed"], ["үрийн", "seed; of a seed"],
  ["бие", "body"], ["толгой", "head"], ["хүзүү", "neck"], ["хоолой", "throat; voice"], ["гар", "hand; arm"],
  ["хөл", "leg; foot"], ["хуруу", "finger"], ["мөр", "shoulder"], ["цус", "blood"], ["зүрх", "heart"],
  ["арьс", "skin"], ["булчин", "muscle"], ["яс", "bone"], ["тархи", "brain"], ["ам", "mouth"], ["хэл", "tongue; language"],
  ["шүд", "tooth"], ["гэдэс", "stomach; belly"], ["нүд", "eye"], ["нүүр", "face"], ["царай", "face; expression"],
  ["хацар", "cheek"], ["үс", "hair"], ["ханиад", "cold; flu"], ["өвдөлт", "pain"], ["жирэмслэлт", "pregnancy"],
  ["жирэмсэн", "pregnant"], ["огноо", "date"], ["эрэгтэй", "male; man"], ["эмэгтэй", "woman; female"], ["залуу", "young"],
  ["хос", "pair; couple"], ["бүл", "family"], ["хүмүүн", "human"], ["монгол", "Mongolian"], ["Монгол", "Mongolia; Mongolian"],
  ["цагаан", "white"], ["улаан", "red"], ["ногоон", "green"], ["хар", "black"], ["хөх", "blue"], ["цэнхэр", "blue"],
  ["шар", "yellow"], ["бор", "brown"], ["саарал", "gray"], ["мөнгөн", "silver"], ["Мөнгөн", "silver"],
].forEach(([word, gloss]) => s(word, gloss));

// Verbal stems. The suffix rules below turn these into short tense/aspect glosses.
[
  ["яв", "go"], ["ир", "come"], ["оч", "go to; arrive"], ["ор", "enter; come in"], ["гар", "go out; come out"],
  ["хар", "look; see"], ["үз", "see; watch"], ["сонс", "hear; listen"], ["мэд", "know"], ["сур", "learn; study"],
  ["заа", "teach; point"], ["хэл", "say; tell"], ["ярь", "talk; speak"], ["асуу", "ask"], ["хариул", "answer"],
  ["дууд", "call"], ["залга", "call by phone"], ["бич", "write"], ["унш", "read"], ["зур", "draw"], ["хий", "do; make"],
  ["ав", "take; get; buy"], ["өг", "give"], ["тав", "put; place"], ["оруул", "put in; include"], ["гарга", "bring out; produce"],
  ["буцаа", "return; give back"], ["барь", "hold; build"], ["баривчил", "arrest"], ["хулгайл", "steal"], ["зас", "fix"],
  ["шалг", "check"], ["хэмж", "measure"], ["тоол", "count"], ["нэм", "add"], ["үржүүл", "multiply"], ["холб", "connect"],
  ["бөгл", "fill"], ["холин", "mix"], ["шийд", "decide; solve"], ["сонго", "choose"], ["эхэл", "begin"], ["дуус", "finish"],
  ["үргэлжил", "continue"], ["өнгөр", "pass"], ["өнгөрөө", "spend; miss"], ["амьдар", "live"], ["амар", "rest"],
  ["ажилл", "work"], ["тогл", "play"], ["алх", "walk"], ["гүй", "run"], ["су", "sit"], ["зогс", "stand; stop"],
  ["бос", "get up; rise"], ["унт", "sleep"], ["ид", "eat"], ["уу", "drink"], ["чан", "boil; cook"], ["угаа", "wash"],
  ["цэвэрл", "clean"], ["хаа", "close"], ["нээ", "open"], ["асаа", "turn on"], ["унтраа", "turn off"], ["зүү", "wear; put on"],
  ["өмс", "wear"], ["тайл", "take off"], ["үүр", "carry; bear"], ["өрг", "raise; lift"], ["тат", "pull"], ["түлх", "push"],
  ["шид", "throw"], ["тайр", "cut"], ["унага", "drop"], ["уна", "fall; ride"], ["урс", "flow"], ["урга", "grow"],
  ["өс", "grow"], ["манд", "rise"], ["гэрэлт", "shine"], ["гялалз", "sparkle"], ["харагд", "appear; be seen"],
  ["сонсогд", "sound; be heard"], ["дуугар", "sound; ring"], ["цахил", "flash"], ["асгар", "spill"], ["цац", "splash"],
  ["тасар", "break; snap"], ["зангир", "tighten"], ["сэгср", "shake"], ["өвд", "hurt"], ["өвтгө", "hurt; cause pain"],
  ["илаарш", "recover"], ["мэндэл", "greet"], ["баярла", "be happy; thank"], ["баярлуул", "make happy"],
  ["сан", "remember"], ["санагд", "seem"], ["мэдэр", "feel"], ["таалагд", "be pleasing; like"], ["ич", "be embarrassed"],
  ["ядар", "be tired"], ["өлс", "be hungry"], ["ай", "fear"], ["сэжигл", "suspect; doubt"], ["дурла", "fall in love; like"],
  ["инээ", "laugh"], ["инээмсэгл", "smile"], ["уйл", "cry"], ["хашхир", "shout"], ["хани", "cough"], ["найтаа", "sneeze"],
  ["хурхир", "snore"], ["нулима", "spit"], ["баа", "defecate"], ["унга", "fart"], ["бөөлж", "vomit"], ["эвшээ", "yawn"],
  ["амьсгал", "breathe"], ["төр", "be born; give birth"], ["төрүүл", "give birth to"], ["зөвшөөр", "allow"],
  ["хамгаал", "protect"], ["хадгал", "keep; store"], ["ашигла", "use"], ["хэрэгл", "use"], ["оролдо", "try"],
  ["хүс", "want; wish"], ["хүлээ", "wait"], ["тусал", "help"], ["удирд", "lead; manage"], ["үйлчил", "serve"],
  ["үйлдвэрл", "produce"], ["боловсруул", "develop; prepare"], ["төлөөл", "represent"], ["нотол", "prove"],
  ["барагдуул", "settle; complete"], ["нэгд", "join"], ["үүсгэ", "create"], ["дага", "follow"], ["тойр", "go around"],
  ["нүү", "move"], ["зугт", "run away"], ["гуй", "ask; beg"], ["алгад", "slap; pat"], ["шах", "press; almost"],
  ["мэр", "gnaw"], ["хүр", "reach"], ["хүргэ", "lead; bring"], ["хаалга тогш", "knock on the door"],
].forEach(([stem, gloss]) => v(stem, gloss));

const exactVerbForms = [
  ["байна", "is; are"], ["байв", "was"], ["байлаа", "was"], ["байсан", "was; were"], ["байдаг", "is; exists habitually"],
  ["байх", "be"], ["байж", "being"], ["байвал", "if there is"], ["болно", "will be; can"], ["болов", "became"],
  ["боллоо", "became; is done"], ["болдог", "becomes; can be"], ["болж", "becoming"], ["болсон", "became"],
  ["болсны", "having become"], ["болгов", "made into"], ["болох", "become; can"], ["боловсруулах", "develop; prepare"],
  ["хэрэгтэй", "need; necessary"], ["боломжтой", "possible; able"], ["тэнцэхгүй", "does not equal"], ["ирээгүй", "did not come"],
  ["хүсэхгүй", "do not want"], ["зөвшөөрөхгүй", "will not allow"], ["ханиахгүй", "does not cough"], ["хийхгүй", "will not do"],
  ["орохгүй", "will not enter"], ["өргөхгүй", "will not lift"], ["орохгүй", "will not enter"], ["үзэсгэлэнтэй", "beautiful"],
  ["баяртай", "happy; goodbye"], ["дуртай", "likes"], ["дургүй", "dislikes"], ["хүсэлтэй", "wants; is willing"],
  ["эрхтэй", "has the right"], ["ихтэй", "has a lot"], ["булчинтай", "muscular; with muscle"], ["хүзүүтэй", "with a neck"],
  ["хэлбэртэй", "shaped; with a shape"], ["порттой", "with a port"], ["хүнтэй", "with a person"], ["цонхтой", "with a window"],
  ["цастай", "snowy"], ["үүлтэй", "cloudy"], ["Ханиадтай", "has a cold"], ["шилтэй", "with glass"], ["эгшигтэй", "with a vowel"],
  ["зүрхтэй", "with a heart"], ["найзтай", "has a friend"], ["найзтайгаа", "with one's friend"], ["ахтайгаа", "with one's older brother"],
  ["сургуультай", "with a school"], ["цэнэглэгчтэй", "with a charger"], ["жинтэй", "weighs; with weight"],
  ["болдог", "becomes; can be"], ["болно", "will; can"], ["байхгүй", "is not; absent"],
  ["ирээрэй", "please come"], ["хүлээгээрэй", "please wait"], ["нэмээрэй", "please add"], ["хаагаарай", "please close"],
  ["яриарай", "please talk"], ["аваарай", "please take"], ["сонсооч", "please listen"], ["Нэрээ", "your name"], ["Найзаа", "friend"],
  ["суу", "sit", "imperative"], ["яваарай", "please go"], ["залга", "call", "imperative"],
  ["Болгоомжтой", "be careful"], ["угаа", "wash", "imperative"], ["өмс", "wear", "imperative"], ["тавь", "put", "imperative"],
];
exactVerbForms.forEach(([word, gloss, note]) => e(word, gloss, note));

const extraExactForms = [
  ["ажлаа", "one's work", "reflexive possessive/direct-object form"],
  ["ажлыг", "work", "accusative case"],
  ["алдаа", "mistake"],
  ["амжилтад", "to success", "dative/locative case"],
  ["ангиа", "one's class", "reflexive possessive/direct-object form"],
  ["аргыг", "method; way", "accusative case"],
  ["арчив", "wiped"],
  ["асаалттай", "turned on; left on"],
  ["асуудлыг", "problem", "accusative case"],
  ["ачаа", "load; luggage"],
  ["аяллын", "travel; of travel", "genitive case"],
  ["Аянгын", "thunder; of lightning", "genitive case"],
  ["байгуулав", "made; established"],
  ["баяр", "joy; happiness"],
  ["бичгийг", "letter; writing", "accusative case"],
  ["биш", "not"],
  ["бүс", "belt"],
  ["газрыг", "place; land", "accusative case"],
  ["Гуравыг", "three", "accusative case"],
  ["гутлаа", "one's shoes", "reflexive possessive/direct-object form"],
  ["Гүйсний", "running; of having run", "genitive verbal noun"],
  ["Гэмт", "guilty; criminal"],
  ["гэрлээ", "one's light", "reflexive possessive/direct-object form"],
  ["даалгавраа", "one's assignment; homework", "reflexive possessive/direct-object form"],
  ["давхарт", "on the floor; storey", "dative/locative case"],
  ["даралт", "pressure"],
  ["дугуйн", "bicycle; of the bicycle", "genitive case"],
  ["завиар", "by boat", "instrumental case"],
  ["зай", "distance; space"],
  ["зардаг", "sells", "habitual present"],
  ["зочдод", "to guests", "dative/locative plural"],
  ["зун", "summer"],
  ["Зун", "summer"],
  ["зүгт", "toward; in the direction", "dative/locative case"],
  ["илгээв", "sent"],
  ["Метр", "meter"],
  ["Модон", "wooden; tree", "attributive form"],
  ["муухай", "unpleasant; ugly"],
  ["найзуудынхаа", "of one's friends", "plural genitive + reflexive possessive"],
  ["нисэж", "flying", "converb"],
  ["нойр", "sleep"],
  ["Нойр", "sleep"],
  ["Нохойн", "dog's; of the dog", "genitive case"],
  ["Нялх", "baby; infant"],
  ["олс", "rope"],
  ["оройн", "evening; of evening", "genitive case"],
  ["Оройн", "evening; of evening", "genitive case"],
  ["орох", "to enter; to rain", "verbal noun"],
  ["Өвчтэй", "sick; ill"],
  ["Өдрийн", "day; of the day", "genitive case"],
  ["Өтгөн", "thick; dense"],
  ["саван", "soap"],
  ["санамсаргүй", "accidentally; unintended"],
  ["санд", "in the library; to the fund", "dative/locative case"],
  ["сандлыг", "chair", "accusative case"],
  ["сонин", "interesting; strange"],
  ["сургуулийн", "school; of school", "genitive case"],
  ["Сургуулийн", "school; of school", "genitive case"],
  ["суудал", "seat"],
  ["суудлаасаа", "from one's seat", "ablative + reflexive possessive"],
  ["тайзан", "stage", "bound locative stem"],
  ["талбайн", "field; square; of the field", "genitive case"],
  ["танил", "familiar"],
  ["танина", "knows; recognizes", "present/future tense"],
  ["тоон", "number; numerical", "attributive form"],
  ["Тоосноос", "from dust", "ablative case"],
  ["төлнө", "will pay; pays", "present/future tense"],
  ["тус", "help; benefit"],
  ["түрийвчиндээ", "in one's wallet", "dative/locative + reflexive possessive"],
  ["урагшаа", "forward"],
  ["усан", "water; aquatic", "attributive form"],
  ["утсаа", "one's phone", "reflexive possessive/direct-object form"],
  ["утсаар", "by phone", "instrumental case"],
  ["уулан", "mountain", "bound locative stem"],
  ["уулзав", "met"],
  ["уулзаж", "meeting", "converb"],
  ["уулзана", "will meet", "present/future tense"],
  ["уулзах", "to meet", "verbal noun"],
  ["уулзлаа", "met", "past tense"],
  ["уулзъя", "let's meet"],
  ["уучлал", "apology; forgiveness"],
  ["үзгийг", "pen", "accusative case"],
  ["хаалгаа", "one's door", "reflexive possessive/direct-object form"],
  ["хаалгаар", "through the door", "instrumental case"],
  ["Хаалган", "door", "bound locative stem"],
  ["хаалгыг", "door", "accusative case"],
  ["Хайрцгийг", "box", "accusative case"],
  ["хайрцгийн", "box; of the box", "genitive case"],
  ["Хайрцгийн", "box; of the box", "genitive case"],
  ["хариулах", "to answer", "verbal noun"],
  ["хашаа", "fence; yard"],
  ["хашаанд", "in the yard", "dative/locative case"],
  ["хоолон", "food", "bound locative stem"],
  ["ширээн", "table", "oblique form before дээр"],
  ["Ширээн", "table", "oblique form before дээр"],
  ["хоцордог", "is late; usually late", "habitual present"],
  ["хоцорлоо", "was late", "past tense"],
  ["хоцрох", "to be late", "verbal noun"],
  ["хөдөлгөв", "moved"],
  ["хөдөлгөнө", "will move; moves", "present/future tense"],
  ["Хөдөөгийн", "countryside; rural", "genitive/attributive form"],
  ["хөөр", "delight; excitement"],
  ["хөшиж", "stiffening; becoming stiff", "converb"],
  ["хуудсан", "page", "bound locative stem"],
  ["хуудсыг", "page", "accusative case"],
  ["хүйтнийг", "coldness; cold", "accusative case"],
  ["хүлээ", "wait", "imperative"],
  ["Хүний", "person's; human", "genitive case"],
  ["Хүүхдийн", "child's; of a child", "genitive case"],
  ["хүүхдэд", "to a child; for children", "dative/locative case"],
  ["хүүхдээ", "one's child", "reflexive possessive/direct-object form"],
  ["цаасан", "paper; made of paper", "attributive form"],
  ["цахилаа", "flashed", "past tense"],
  ["Цонхон", "window", "bound locative stem"],
  ["цохилж", "beating", "converb"],
  ["цэвэрлэгээ", "cleaning"],
  ["чинийхтэй", "with yours", "comitative form"],
  ["шалтгаантай", "has a reason", "with suffix"],
  ["ширээн", "table", "bound locative stem"],
  ["Ширээн", "table", "bound locative stem"],
  ["шулуун", "straight"],
  ["Эм", "medicine"],
  ["эсэхийг", "whether", "accusative nominalized clause"],
  ["ээжийгээ", "one's mother", "accusative + reflexive possessive"],
  ["ядралыг", "tiredness; fatigue", "accusative case"],
];
extraExactForms.forEach(([word, gloss, note]) => e(word, gloss, note));

const directExact = [
  ["аваачив", "took away"], ["авбал", "if taking"], ["авлаа", "took; bought"], ["авмаар", "want to buy/take"],
  ["авна", "will take; will buy"], ["авсан", "took; got; bought"], ["авч", "taking; with"], ["авчирлаа", "brought"],
  ["авчирсан", "brought"], ["авчрах", "bring"], ["алхав", "walked"], ["алхлаа", "walked"], ["амардаг", "rests"],
  ["амарлаа", "rested"], ["амарна", "will rest"], ["амарсан", "rested"], ["амраадаг", "lets rest; relaxes"],
  ["амьдардаг", "lives"], ["амьдарна", "will live"], ["амьдарч", "living"], ["асуув", "asked"], ["асуулаа", "asked"],
  ["барив", "held; caught"], ["барьдаг", "holds; builds"], ["бичив", "wrote"], ["бичлээ", "wrote"], ["бичнэ", "will write"],
  ["бодлоо", "thought"], ["бодов", "thought"], ["бодож", "thinking"], ["бөглөж", "filling"], ["босдог", "gets up"],
  ["бослоо", "got up"], ["босно", "will get up"], ["бөөлжих", "vomit"], ["буцааж", "back; returning"],
  ["гарахад", "when going out"], ["гарахыг", "to go out", "accusative verbal noun"], ["гаргав", "put out; made"],
  ["гаргалаа", "released; issued"], ["гарган", "making; producing"], ["гаргана", "will make; will produce"],
  ["гардаг", "appears; comes out"], ["гарлаа", "came out; went out"], ["гарч", "going out; coming out"],
  ["гаталж", "crossing"], ["гуйв", "asked; begged"], ["гүйв", "ran"], ["гүйдэг", "runs"], ["гүйж", "running"],
  ["гэв", "said"], ["гэрэлтэв", "shone"], ["гялалзав", "sparkled"], ["дагаад", "following; after"], ["даган", "following"],
  ["дуугарлаа", "sounded; rang"], ["дуугарна", "will sound"], ["дуугарч", "sounding"], ["дуудав", "called"],
  ["дуудлаа", "called"], ["дуулж", "singing"], ["дуусаад", "after finishing"], ["дуусахыг", "to finish"],
  ["дууслаа", "finished"], ["дуусна", "will finish"], ["дүүрвэл", "if filled"], ["дүүргэв", "filled"], ["зангираад", "tightened and"],
  ["засав", "fixed"], ["засаж", "fixing"], ["засуулав", "had it fixed"], ["зогсов", "stood; stopped"],
  ["зогссон", "stopped"], ["зугтав", "ran away"], ["зур", "draw", "imperative"], ["зурж", "drawing"], ["зуржээ", "drew"],
  ["зурлаа", "drew"], ["зүүв", "put on; wore"], ["идлээ", "ate"], ["иднэ", "will eat"], ["идэв", "ate"],
  ["идэж", "eating"], ["идэх", "eat"], ["идээд", "after eating"], ["инээв", "laughed"], ["инээж", "laughing"],
  ["инээлгэв", "made laugh"], ["инээмсэглэдэг", "smiles"], ["инээмсэглэж", "smiling"], ["ирвэл", "if coming"],
  ["ирлээ", "came"], ["ирнэ", "will come"], ["ирэв", "came"], ["ирсэн", "came"], ["мэддэг", "knows"],
  ["мэднэ", "will know"], ["мэдрээд", "feeling"], ["мэдэрлээ", "felt"], ["мэдэхгүй", "does not know"], ["мэдэхийг", "to know"],
  ["мэндэлнэ", "will greet"], ["мэрэв", "gnawed"], ["нээв", "opened"], ["нээгдлээ", "opened"], ["нээгээд", "opened and"],
  ["нээлээ", "opened"], ["нүүв", "moved"], ["олох", "find"], ["олдлоо", "was found"], ["орвол", "if entering"],
  ["ордог", "enters; falls"], ["орж", "entering; falling"], ["оржээ", "entered"], ["орлоо", "entered"],
  ["орно", "will enter; will fall"], ["оролдов", "tried"], ["орсон", "entered"], ["орууллаа", "put in; let in"],
  ["орхив", "left"], ["очив", "went; arrived"], ["очлоо", "went; arrived"], ["өвдвөл", "if it hurts"], ["өвдөв", "hurt"],
  ["өвдөж", "hurting"], ["өвтгөнө", "will hurt"], ["өвтгөсөн", "hurt; caused pain"], ["өгдөг", "gives"],
  ["өгнө", "will give"], ["өгөх", "give"], ["өгсөн", "gave"], ["өлсөж", "being hungry"], ["өмсдөг", "wears"],
  ["өмслөө", "wore"], ["өмсөв", "wore"], ["өмсөнө", "will wear"], ["өмссөн", "wore"], ["өнгөрлөө", "passed"],
  ["өнгөрөөлөө", "spent"], ["өнгөрөөх", "miss; spend"], ["өнгөрөх", "pass"], ["өнгөртөл", "until it passed"],
  ["өргөв", "raised"], ["өргөлөө", "lifted"], ["санагдав", "seemed"], ["санаж", "remembering"], ["сонирхдог", "is interested in"],
  ["сонголоо", "chose"], ["сонсдог", "listens"], ["сонслоо", "heard"], ["сонсогдов", "sounded; was heard"],
  ["сонсогдож", "sounding; being heard"], ["сонсогдоно", "will sound"], ["сонсож", "listening; hearing"], ["сонсоод", "after hearing"],
  ["суув", "sat"], ["сууж", "sitting"], ["суулаа", "sat"], ["сууна", "will sit"], ["суух", "sit"], ["суухад", "when sitting"],
  ["сурдаг", "studies"], ["сурч", "studying"], ["сэрүүцүүлэв", "cooled"], ["сэрэв", "woke up"], ["сэгсрэв", "shook"],
  ["таалагдаж", "being liked"], ["таалагддаг", "is liked"], ["тавив", "put; placed"], ["татав", "pulled"], ["татлаа", "pulled"],
  ["тайлбарлав", "explained"], ["тайлна", "will take off"], ["тасарлаа", "snapped; broke"], ["тоолно", "will count"],
  ["тоглов", "played"], ["тоглодог", "plays"], ["тоглож", "playing"], ["тоглоно", "will play"], ["тоглохыг", "to play"],
  ["тогшив", "knocked"], ["тогшлоо", "knocked"], ["тойрдог", "goes around"], ["тойроод", "around; after going around"],
  ["төрөхөөр", "to give birth; about to be born"], ["төрүүлэв", "gave birth to"], ["тусалдаг", "helps"], ["тусална", "will help"],
  ["туслав", "helped"], ["түлдэг", "burns"], ["түлэгдэв", "was burned"], ["уйлав", "cried"], ["улайсан", "reddened"],
  ["унадаг", "falls; rides"], ["унахыг", "to fall; to ride"], ["унтав", "slept"], ["унтаж", "sleeping"], ["Унтахын", "of sleeping; before sleep"],
  ["унтдаг", "sleeps"], ["уншаад", "after reading"], ["уншив", "read"], ["уншиж", "reading"], ["уншина", "will read"],
  ["уншлаа", "read"], ["урсав", "flowed"], ["урсаж", "flowing"], ["усаллаа", "watered"], ["уув", "drank"],
  ["уудаг", "drinks"], ["ууж", "drinking"], ["уулаа", "drank"], ["ууна", "will drink"], ["уух", "drink"],
  ["үүрэв", "carried"], ["үүрэх", "carry; bear"], ["үүсгэлээ", "created"], ["үхэх", "die"], ["үхэхийг", "to die"],
  ["үзлээ", "saw; watched"], ["үзүүлэв", "showed"], ["үзэж", "watching"], ["үзэхийг", "to see; to watch"], ["үзээд", "after seeing"],
  ["үйлдвэрлэх", "produce"], ["хайх", "search"], ["хадгалж", "keeping; storing"], ["халаах", "heat"], ["хамгаалах", "protect"],
  ["хараад", "looking; after seeing"], ["харав", "looked"], ["харагдав", "appeared"], ["харагдаж", "appearing; being seen"],
  ["харагдана", "will appear"], ["харж", "looking"], ["харив", "returned"], ["харина", "will go back"], ["харих", "return home"],
  ["харлаа", "looked; saw"], ["харна", "will look"], ["харсан", "saw"], ["хашхирав", "shouted"], ["хийв", "did; made"],
  ["хийдэг", "does; makes"], ["хийж", "doing; making"], ["хийлээ", "did; made"], ["хийх", "do; make"], ["холино", "will mix"],
  ["холбож", "connecting"], ["худалдаж", "buying"], ["хурдан", "quickly; fast"], ["хүлээв", "waited"], ["хүлээж", "waiting"],
  ["хүлээлээ", "waited"], ["хүлээнэ", "will wait"], ["хүрвэл", "if reaching"], ["хүрээд", "after reaching"], ["хүсвэл", "if wanting"],
  ["хүсдэг", "wants"], ["хүсэв", "wanted"], ["хүсэж", "wanting"], ["хэллээ", "said"], ["хэлнэ", "will say"], ["хэлсэн", "said"],
  ["хэлсэндээ", "for saying"], ["хэлэв", "said"], ["хэлээд", "after saying"], ["хэмжив", "measured"], ["чанаж", "boiling; cooking"],
  ["чангална", "will tighten"], ["шалгав", "checked"], ["шийднэ", "will decide"], ["шийдэхээ", "how to solve"], ["шидлээ", "threw"],
  ["эхэлдэг", "starts"], ["эхэллээ", "started"], ["эхэлнэ", "will start"], ["эхэлсэн", "started"], ["яв", "go"],
  ["явав", "went"], ["явахад", "when going"], ["явдаг", "goes"], ["явж", "going"], ["явлаа", "went"], ["явна", "will go"],
  ["явсан", "went"], ["явъя", "let's go"], ["ярив", "talked"], ["ярьдаг", "speaks"], ["ярьсан", "spoke"], ["ярья", "let's talk"],
  ["яллаа", "won"],
];
directExact.forEach(([word, gloss, note]) => e(word, gloss, note));

[
  ["алдаа", "mistake"], ["амжилт", "success"], ["арга", "method; way"], ["ачаа", "load; baggage"],
  ["баяр", "joy"], ["бүс", "belt"], ["давхар", "floor; story"], ["даралт", "pressure"],
  ["зай", "distance; space"], ["зүг", "direction"], ["зун", "summer"], ["метр", "meter"],
  ["муухай", "ugly; unpleasant"], ["нойр", "sleep; sleepiness"], ["олс", "rope"], ["саван", "soap"],
  ["суудал", "seat"], ["тоос", "dust"], ["тус", "help; benefit"], ["түрийвч", "wallet"],
  ["уучлал", "apology"], ["хашаа", "fence; yard"], ["хөдөө", "countryside"], ["хөөр", "joy"],
  ["хөргөгч", "refrigerator"], ["цэвэрлэгээ", "cleaning"], ["шалтгаан", "reason"], ["шулуун", "straight"],
  ["эм", "medicine"], ["ядрал", "tiredness"], ["танил", "familiar"], ["усан", "water; aquatic"],
].forEach(([word, gloss]) => s(word, gloss));

[
  ["арч", "wipe"], ["байгуул", "make; establish"], ["зар", "sell"], ["илгээ", "send"], ["нис", "fly"],
  ["уулз", "meet"], ["тань", "recognize; know"], ["төл", "pay"], ["хоцор", "be late"],
  ["хөдөлгө", "move"], ["хөш", "be stiff"], ["цохил", "beat"], ["цахил", "flash"],
].forEach(([stem, gloss]) => v(stem, gloss));

[
  ["автобусанд", "by bus; on the bus", "dative/locative case"],
  ["ажлаа", "one's work", "reflexive possessive/direct-object form"],
  ["ажлыг", "work", "accusative case"],
  ["амжилтад", "to success", "dative/locative case"],
  ["ангиа", "one's class", "reflexive possessive/direct-object form"],
  ["аргыг", "method; way", "accusative case"],
  ["арчив", "wiped"], ["асаалттай", "on; turned on"], ["асуудлыг", "problem", "accusative case"],
  ["аяллын", "travel; of the trip", "genitive case"], ["Аянгын", "of lightning/thunder", "genitive case"],
  ["байгуулав", "made; established"], ["байранд", "in an apartment", "dative/locative case"],
  ["бичгийг", "letter; writing", "accusative case"], ["биш", "not"],
  ["газрыг", "place", "accusative case"], ["гудамжинд", "in/on the street", "dative/locative case"],
  ["Гудамжинд", "in/on the street", "dative/locative case"], ["Гуравыг", "three", "accusative case"],
  ["гутлаа", "one's shoes", "reflexive possessive/direct-object form"], ["Гүйсний", "of running; after running", "genitive verbal noun"],
  ["Гэмт", "criminal; guilty"], ["гэрлээ", "one's light", "reflexive possessive/direct-object form"],
  ["даалгавраа", "one's assignment; homework", "reflexive possessive/direct-object form"],
  ["дугуйн", "of the bicycle", "genitive case"], ["завиар", "by boat", "instrumental case"],
  ["зардаг", "sells", "habitual present"], ["зочдод", "to guests", "dative plural"],
  ["Зун", "in summer"], ["зүгт", "toward; in the direction", "dative/locative case"],
  ["илгээв", "sent"], ["Метр", "meter"], ["Модон", "tree", "oblique form before дээр"],
  ["найзуудынхаа", "one's friends", "genitive + reflexive possessive"], ["нисэж", "flying", "converb"],
  ["Нойр", "sleep"], ["Нохойн", "dog's", "genitive case"], ["нүдэнд", "in the eye(s)", "dative/locative case"],
  ["Нялх", "baby; infant"], ["Онгоцонд", "on/in the plane", "dative/locative case"],
  ["оройн", "evening; of evening"], ["Оройн", "evening; of evening"], ["Өвчтэй", "sick"],
  ["Өдрийн", "of the day", "genitive case"], ["Өтгөн", "dense; thick"], ["саванд", "in the container", "dative/locative case"],
  ["санамсаргүй", "accidentally"], ["санд", "in the library", "short for номын сан"], ["сандлыг", "chair", "accusative case"],
  ["сонин", "interesting; curious"], ["сургуулийн", "of the school", "genitive case"], ["Сургуулийн", "of the school", "genitive case"],
  ["суудлаасаа", "from one's seat", "ablative + reflexive possessive"], ["тайзан", "stage", "oblique form before дээр"],
  ["талбайн", "of the field/square", "genitive case"], ["танина", "knows; recognizes"], ["тоон", "number; numeric"],
  ["Тоосноос", "from dust", "ablative case"], ["төлнө", "will pay"], ["түрийвчиндээ", "in her wallet", "dative/locative + reflexive possessive"],
  ["урагшаа", "forward"], ["усанд", "in the water", "dative/locative case"], ["утсаа", "one's phone", "reflexive possessive/direct-object form"],
  ["утсаар", "by phone", "instrumental case"], ["уулан", "mountain", "oblique form before дээрээс"],
  ["ууланд", "in/on the mountain", "dative/locative case"], ["уулзав", "met"], ["уулзаж", "meeting", "converb"],
  ["уулзана", "will meet"], ["уулзах", "meet"], ["уулзлаа", "met"], ["уулзъя", "let's meet"],
  ["үзгийг", "pen", "accusative case"], ["хаалгаа", "one's door", "reflexive possessive/direct-object form"],
  ["хаалгаар", "through the door", "instrumental case"], ["Хаалган", "door", "oblique form before дээр"],
  ["хаалгыг", "door", "accusative case"], ["Хайрцгийг", "box", "accusative case"],
  ["хайрцгийн", "of the box", "genitive case"], ["Хайрцгийн", "of the box", "genitive case"],
  ["хариулах", "answer"], ["хашаанд", "in the yard", "dative/locative case"], ["хоолон", "food", "oblique form before дээр"],
  ["хоцордог", "is late", "habitual present"], ["хоцорлоо", "was late"], ["хоцрох", "be late"],
  ["хөдөлгөв", "moved"], ["хөдөлгөнө", "will move"], ["Хөдөөгийн", "rural; of the countryside", "genitive case"],
  ["хөргөгчинд", "in the refrigerator", "dative/locative case"], ["хөшиж", "being stiff", "converb"],
  ["хуудсан", "page", "oblique form before дээр"], ["хуудсыг", "page", "accusative case"],
  ["хүйтнийг", "coldness; cold", "accusative case"], ["хүлээ", "wait", "imperative"],
  ["Хүний", "person's; human", "genitive case"], ["Хүүхдийн", "child's", "genitive case"],
  ["хүүхдэд", "to a child; to children", "dative case"], ["хүүхдээ", "one's child", "reflexive possessive/direct-object form"],
  ["цаасан", "paper", "attributive/oblique form"], ["цахилаа", "flashed"], ["Цонхон", "window", "oblique form before дээр"],
  ["цохилж", "beating", "converb"], ["цүнхэнд", "in the bag", "dative/locative case"],
  ["Цүнхэнд", "in the bag", "dative/locative case"], ["чинийхтэй", "with yours", "comitative form"],
  ["шөлөнд", "in the soup", "dative/locative case"], ["Эм", "medicine"],
  ["эсэхийг", "whether", "accusative nominal form"], ["ээжийгээ", "one's mother", "accusative + reflexive possessive"],
  ["ядралыг", "tiredness", "accusative case"], ["ясанд", "to bones; in bones", "dative/locative case"],
].forEach(([word, gloss, note]) => e(word, gloss, note));

function contextual(item, token, index, tokens) {
  const lower = key(token);
  const english = item.text.toLocaleLowerCase("en");
  const sentence = item.translations[0].text;

  if (lower === "өглөө") {
    if (english.includes("morning")) return entry("morning");
    if (tokens[index - 1]?.endsWith("ж")) return entry("did for; gave", "auxiliary after a converb");
    return entry("gave", "past tense of өгөх");
  }
  if (lower === "гарлаа") {
    if (english.includes("happened") || english.includes("trouble") || english.includes("had a little")) {
      return entry("happened; arose");
    }
    if (english.includes("came up") || english.includes("rose")) return entry("rose; came up");
    if (english.includes("went up") || english.includes("climbed")) return entry("went up; climbed");
    return entry("went out; came out");
  }
  if (lower === "суухад") {
    if (english.includes("board")) return entry("when boarding", "converbial verbal noun");
    return entry("when sitting", "converbial verbal noun");
  }
  if (lower === "гэрээ") {
    if (english.includes("contract")) return entry("contract");
    return entry("home", "possessive/accusative form of гэр");
  }
  if (lower === "дугуй") {
    if (english.includes("bicycle") || english.includes("ride")) return entry("bicycle");
    if (english.includes("circle")) return entry("circle");
    return entry("round");
  }
  if (lower === "мод") {
    if (english.includes("wood") || english.includes("stick")) return entry("wood; stick");
    return entry("tree");
  }
  if (lower === "ая") {
    if (english.includes("tone")) return entry("tone");
    return entry("melody; tune");
  }
  if (lower === "дуу") {
    if (english.includes("song")) return entry("song");
    return entry("sound");
  }
  if (lower === "гар") {
    if (tokens[index + 1] === "барив") return entry("hand");
    return entry("hand; arm");
  }
  if (lower === "хэл") {
    if (english.includes("language")) return entry("language");
    return entry("tongue");
  }
  if (lower === "ам") {
    if (sentence.includes("амар") || sentence.includes("амь")) return undefined;
    return entry("mouth");
  }
  if (lower === "сар" || lower === "сарын") {
    if (english.includes("moon")) return entry("Moon");
    return entry("month", lower === "сарын" ? "genitive form" : undefined);
  }
  if (lower === "газар") {
    if (english.includes("land")) return entry("land");
    if (english.includes("ground")) return entry("ground");
    return entry("place");
  }
  if (lower === "хот") return entry("city");
  if (lower === "машин") {
    if (english.includes("machine")) return entry("machine");
    return entry("car");
  }
  if (lower === "хүнд") {
    if (english.includes("person")) return entry("to a person", "dative form of хүн");
    return entry("heavy");
  }
  if (lower === "ногоо") {
    if (english.includes("vegetable")) return entry("vegetables");
    return entry("greens; vegetables");
  }
  if (lower === "цаг") {
    if (sentence.includes("цаг агаар")) return entry("weather", "part of цаг агаар");
    if (english.includes("hour") || english.includes("o'clock")) return entry("hour; o'clock");
    return entry("time");
  }
  if (lower === "орох") {
    if (english.includes("rain")) return entry("rain; fall", "verbal noun/infinitive");
    return entry("enter; go in", "verbal noun/infinitive");
  }
  if (lower === "агаар") {
    if (sentence.includes("цаг агаар")) return entry("weather", "part of цаг агаар");
    return entry("air");
  }
  if (lower === "нам" && tokens[index + 1] === "гүм") return entry("quiet", "part of нам гүм");
  if (lower === "гүм" && tokens[index - 1] === "нам") return entry("silent", "part of нам гүм");

  return undefined;
}

const caseRules = [
  {
    suffixes: ["ынхаа", "ийнхээ", "ныхаа", "нийхээ"],
    note: "genitive + reflexive possessive",
    gloss: (baseGloss) => `one's ${baseGloss}`,
  },
  {
    suffixes: ["тайгаа", "тэйгээ", "тойгоо"],
    note: "comitative + reflexive possessive",
    gloss: (baseGloss) => `with one's ${baseGloss}`,
  },
  {
    suffixes: ["аасаа", "ээсээ", "оосоо", "өөсөө"],
    note: "ablative + reflexive possessive",
    gloss: (baseGloss) => `from one's ${baseGloss}`,
  },
  {
    suffixes: ["аараа", "ээрээ", "оороо", "өөрөө"],
    note: "instrumental + reflexive possessive",
    gloss: (baseGloss) => `with one's ${baseGloss}`,
  },
  {
    suffixes: ["даа", "дээ", "тоо", "төө"],
    note: "dative/locative + reflexive possessive",
    gloss: (baseGloss) => `in/to one's ${baseGloss}`,
  },
  {
    suffixes: ["аас", "ээс", "оос", "өөс"],
    note: "ablative case",
    gloss: (baseGloss) => `from ${baseGloss}`,
  },
  {
    suffixes: ["аар", "ээр", "оор", "өөр"],
    note: "instrumental case",
    gloss: (baseGloss) => `by/with ${baseGloss}`,
  },
  {
    suffixes: ["тай", "тэй", "той"],
    note: "comitative/with suffix",
    gloss: (baseGloss) => `with ${baseGloss}; having ${baseGloss}`,
  },
  {
    suffixes: ["ыг", "ийг"],
    note: "accusative case",
    gloss: (baseGloss) => `${baseGloss}`,
  },
  {
    suffixes: ["ын", "ийн", "ны", "ний"],
    note: "genitive case",
    gloss: (baseGloss) => `of ${baseGloss}`,
  },
  {
    suffixes: ["д", "т"],
    note: "dative/locative case",
    gloss: (baseGloss) => `in/at/to ${baseGloss}`,
  },
  {
    suffixes: ["аа", "ээ", "оо", "өө"],
    note: "reflexive possessive/direct-object form",
    gloss: (baseGloss) => `one's ${baseGloss}`,
  },
];

function candidateBases(raw, suffix) {
  const base = raw.slice(0, -suffix.length);
  const candidates = [base];

  // Remove common buffer vowels used before case suffixes.
  for (const ending of ["а", "э", "о", "ө"]) {
    if (base.endsWith(ending)) candidates.push(base.slice(0, -ending.length));
  }

  // Restore stems whose final vowel alternates or drops.
  if (/[аэиоөуү]н$/u.test(base)) candidates.push(base.slice(0, -2));
  if (base.endsWith("н")) candidates.push(base.slice(0, -1));
  if (base.endsWith("г")) candidates.push(base.slice(0, -1));
  if (base.endsWith("й")) candidates.push(base);

  return [...new Set(candidates.filter(Boolean))];
}

function findStemGloss(raw) {
  const candidates = [raw, key(raw)];
  for (const candidate of candidates) {
    if (stems.has(candidate)) return stems.get(candidate);
    if (exact.has(candidate)) return exact.get(candidate).gloss;
  }
  return undefined;
}

function fromCase(raw) {
  for (const rule of caseRules) {
    for (const suffix of rule.suffixes) {
      if (!raw.endsWith(suffix) || raw.length <= suffix.length + 1) continue;
      for (const base of candidateBases(raw, suffix)) {
        const baseGloss = findStemGloss(base);
        if (baseGloss) return entry(rule.gloss(baseGloss), rule.note);
      }
    }
  }

  // -г accusative after vowel, e.g. нохойг.
  if (raw.endsWith("г") && raw.length > 2) {
    const base = raw.slice(0, -1);
    const baseGloss = findStemGloss(base);
    if (baseGloss) return entry(baseGloss, "accusative case");
  }

  // Plural forms.
  for (const suffix of ["нууд", "нүүд", "ууд", "үүд"]) {
    if (raw.endsWith(suffix)) {
      const base = raw.slice(0, -suffix.length);
      const baseGloss = findStemGloss(base);
      if (baseGloss) return entry(`${baseGloss}s`, "plural");
    }
  }

  if (raw.endsWith("гүй") && raw.length > 4) {
    const base = raw.slice(0, -3);
    const baseGloss = findStemGloss(base);
    if (baseGloss) return entry(`without ${baseGloss}`, "negative/without suffix");
  }

  return undefined;
}

const verbRules = [
  [["аарай", "ээрэй", "оорой", "өөрэй", "гаарай", "гээрэй"], "please {gloss}", "polite imperative"],
  [["маар", "мээр", "моор", "мөөр"], "want to {gloss}", "desiderative suffix"],
  [["хаар", "хээр", "хоор", "хөөр"], "in order to {gloss}; about to {gloss}", "purposive suffix"],
  [["хыг", "хийг", "хийг"], "to {gloss}", "accusative verbal noun"],
  [["хад", "хэд", "ход", "хөд"], "when {gloss}ing", "converbial verbal noun"],
  [["хгүй"], "not {gloss}", "negative verbal noun"],
  [["бал", "бэл", "бол", "бөл", "вал", "вэл", "вол", "вөл"], "if {gloss}ing", "conditional"],
  [["даг", "дэг", "дог", "дөг"], "{gloss}s; usually {gloss}s", "habitual present"],
  [["сан", "сэн", "сон", "сөн"], "{gloss}ed", "past participle"],
  [["лаа", "лээ", "лоо", "лөө"], "{gloss}ed", "past tense"],
  [["на", "нэ", "но", "нө"], "will {gloss}", "present/future tense"],
  [["ав", "эв", "ов", "өв", "в"], "{gloss}ed", "past tense"],
  [["аад", "ээд", "оод", "өөд", "ад", "эд"], "after {gloss}ing; {gloss}ing and", "converb"],
  [["ж", "ч"], "{gloss}ing", "converb"],
];

function formatVerb(pattern, gloss) {
  return pattern.replaceAll("{gloss}", gloss);
}

function verbCandidates(raw, suffix) {
  const base = raw.slice(0, -suffix.length);
  const candidates = [base];
  if (suffix.startsWith("х")) candidates.push(raw.slice(0, raw.indexOf("х")));
  if (base.endsWith("и")) candidates.push(base.slice(0, -1));
  if (base.endsWith("а") || base.endsWith("э") || base.endsWith("о") || base.endsWith("ө")) {
    candidates.push(base.slice(0, -1));
  }
  if (base.endsWith("л")) candidates.push(base.slice(0, -1));
  if (base.endsWith("г")) candidates.push(base.slice(0, -1));
  if (base.endsWith("с")) candidates.push(base);
  return [...new Set(candidates.filter(Boolean))];
}

function fromVerb(raw) {
  for (const [suffixes, pattern, note] of verbRules) {
    for (const suffix of suffixes) {
      if (!raw.endsWith(suffix) || raw.length <= suffix.length + 1) continue;
      for (const candidate of verbCandidates(raw, suffix)) {
        const gloss = verbStems.get(candidate) ?? verbStems.get(key(candidate));
        if (gloss) return entry(formatVerb(pattern, gloss), note);
      }
    }
  }
  return undefined;
}

function lookup(item, token, index, tokens) {
  return (
    contextual(item, token, index, tokens) ??
    exact.get(token) ??
    exact.get(key(token)) ??
    fromCase(key(token)) ??
    fromVerb(key(token))
  );
}

function tokenize(text) {
  return [...text.matchAll(/[\p{L}]+/gu)].map((match) => match[0]);
}

const missing = new Map();
const output = {
  data: corpus.data.map((item) => {
    const tokens = tokenize(item.translations[0].text);
    const words = tokens.map((token, index) => {
      const found = lookup(item, token, index, tokens);
      if (!found) {
        const examples = missing.get(token) ?? [];
        if (examples.length < 3) examples.push(`${item.id}: ${item.translations[0].text} => ${item.text}`);
        missing.set(token, examples);
        return { word: token, gloss: "" };
      }
      return { word: token, ...found };
    });
    return { id: item.id, words };
  }),
};

if (missing.size > 0) {
  console.error(`Missing ${missing.size} word forms:`);
  for (const [word, examples] of [...missing.entries()].sort((a, b) => a[0].localeCompare(b[0], "mn"))) {
    console.error(`\n${word}`);
    for (const example of examples) console.error(`  ${example}`);
  }
  process.exit(1);
}

fs.writeFileSync(outputPath, `${JSON.stringify(output, null, 2)}\n`);

const sentenceCount = output.data.length;
const wordCount = output.data.reduce((sum, item) => sum + item.words.length, 0);
const uniqueForms = new Set(output.data.flatMap((item) => item.words.map((word) => word.word))).size;
console.log(`Wrote ${outputPath.pathname}`);
console.log(`Sentences: ${sentenceCount}`);
console.log(`Word explanations: ${wordCount}`);
console.log(`Unique surface forms: ${uniqueForms}`);
