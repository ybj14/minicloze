const COURSES = [
  {
    code: "mon-a1",
    label: "Mongolian A1",
    slug: "mongolian-a1",
    baseLanguage: "mon",
    sentenceCount: 1500,
    corpusPath: "/data/mongolian_a1.json",
    vocabularyPath: "/data/mongolian_a1_vocab.json",
    explanationsPath: "/data/mongolian_a1_explanations.json",
  },
  {
    code: "bod-a1",
    label: "Tibetan A1",
    slug: "tibetan-a1",
    baseLanguage: "bod",
    sentenceCount: 1500,
    corpusPath: "/data/tibetan_a1.json",
    vocabularyPath: "/data/tibetan_a1_vocab.json",
    explanationsPath: "/data/tibetan_a1_explanations.json",
    tokensPath: "/data/tibetan_a1_tokens.json",
  },
];

const MAX_COUNT = 50;
const DISTANCE_FOR_CLOSE = 3;
const SRS_INTERVAL_DAYS = [1, 10, 30, 180];
const MS_PER_DAY = 24 * 60 * 60 * 1000;
const NON_SPACED_LANGUAGES = new Set([
  "cmn",
  "lzh",
  "hak",
  "cjy",
  "nan",
  "hsn",
  "gan",
  "jpn",
  "tha",
  "khm",
  "lao",
  "mya",
]);
const TIBETAN_BREAKS = new Set(["་", "༌", "།", "༎", "༏", "༐", "༑", "༔"]);
const TRANSLITERATION_TRIM = new Set([
  "(",
  ")",
  ",",
  ".",
  ";",
  ":",
  "?",
  "!",
  '"',
  "/",
  " ",
]);
const CYRILLIC_LATIN = {
  а: "a",
  б: "b",
  в: "v",
  г: "g",
  д: "d",
  е: "e",
  ё: "yo",
  ж: "j",
  з: "z",
  и: "i",
  й: "i",
  к: "k",
  л: "l",
  м: "m",
  н: "n",
  о: "o",
  ө: "o",
  п: "p",
  р: "r",
  с: "s",
  т: "t",
  у: "u",
  ү: "u",
  ф: "f",
  х: "h",
  ц: "ts",
  ч: "ch",
  ш: "sh",
  щ: "shch",
  ъ: "",
  ы: "y",
  ь: "",
  э: "e",
  ю: "yu",
  я: "ya",
};

const els = {
  languageSelect: document.querySelector("#languageSelect"),
  countSelect: document.querySelector("#countSelect"),
  inverseToggle: document.querySelector("#inverseToggle"),
  startButton: document.querySelector("#startButton"),
  roundScore: document.querySelector("#roundScore"),
  progressFill: document.querySelector("#progressFill"),
  storedPlayed: document.querySelector("#storedPlayed"),
  storedAccuracy: document.querySelector("#storedAccuracy"),
  storedStreak: document.querySelector("#storedStreak"),
  emptyState: document.querySelector("#emptyState"),
  cardView: document.querySelector("#cardView"),
  summaryView: document.querySelector("#summaryView"),
  cardPosition: document.querySelector("#cardPosition"),
  promptLabel: document.querySelector("#promptLabel"),
  promptLine: document.querySelector("#promptLine"),
  wylieLine: document.querySelector("#wylieLine"),
  translationLabel: document.querySelector("#translationLabel"),
  translationText: document.querySelector("#translationText"),
  choices: document.querySelector("#choices"),
  textAnswerForm: document.querySelector("#textAnswerForm"),
  textAnswer: document.querySelector("#textAnswer"),
  feedback: document.querySelector("#feedback"),
  wordExplanations: document.querySelector("#wordExplanations"),
  nextButton: document.querySelector("#nextButton"),
  againButton: document.querySelector("#againButton"),
  summaryViewTitle: document.querySelector("#summaryTitle"),
  summaryText: document.querySelector("#summaryText"),
};

const courseCache = new Map();

let currentRound = null;
let currentCard = null;
let currentSummary = { total: 0, answered: 0, correct: 0, finished: false };
let pendingNextCard = null;
let activeMode = "multiple_choice";
let answeredCurrentCard = false;

document.addEventListener("DOMContentLoaded", async () => {
  bindEvents();
  loadLanguages();
  renderStoredStats();
  registerServiceWorker();
});

function bindEvents() {
  els.startButton.addEventListener("click", startRound);
  els.againButton.addEventListener("click", startRound);
  els.nextButton.addEventListener("click", goNext);
  els.textAnswerForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const answer = els.textAnswer.value.trim();
    if (answer) {
      submitAnswer(answer);
    }
  });

  for (const input of document.querySelectorAll("input[name='mode']")) {
    input.addEventListener("change", renderStoredStats);
  }
  els.languageSelect.addEventListener("change", renderStoredStats);
  els.inverseToggle.addEventListener("change", renderStoredStats);
}

function loadLanguages() {
  els.languageSelect.replaceChildren(
    ...COURSES.map((language) => {
      const option = document.createElement("option");
      option.value = language.slug;
      option.textContent = `${language.label} (${language.sentenceCount})`;
      return option;
    }),
  );
}

async function startRound() {
  setBusy(true);
  hide(els.summaryView);
  hide(els.emptyState);
  hide(els.feedback);
  hide(els.wordExplanations);
  try {
    activeMode = selectedMode();
    const data = await createRound({
      language: els.languageSelect.value,
      mode: activeMode,
      count: Number(els.countSelect.value),
      inverse: els.inverseToggle.checked,
    });

    currentSummary = data.summary;
    pendingNextCard = null;
    renderCard(data.card);
    renderRoundSummary(data.summary);
  } catch (error) {
    showEmptyError(error.message);
  } finally {
    setBusy(false);
  }
}

async function submitAnswer(answer) {
  if (!currentRound || !currentCard || answeredCurrentCard) {
    return;
  }

  answeredCurrentCard = true;
  disableAnswerInputs(true);
  try {
    const data = answerRound({
      cardId: currentCard.id,
      answer,
    });

    currentSummary = data.summary;
    pendingNextCard = data.nextCard;
    recordStoredStats(data.result.outcome === "correct");
    renderRoundSummary(data.summary);
    renderFeedback(data.result);
    renderWordExplanations(data.wordExplanations || []);
    markChoices(answer, data.correctAnswer, data.result);
    els.nextButton.textContent = data.summary.finished ? "Finish" : "Next";
    show(els.nextButton);
  } catch (error) {
    answeredCurrentCard = false;
    disableAnswerInputs(false);
    renderFeedback({ outcome: "wrong", answer: error.message });
    hide(els.wordExplanations);
  }
}

function goNext() {
  if (currentSummary.finished) {
    renderFinalSummary();
    return;
  }

  if (pendingNextCard) {
    renderCard(pendingNextCard);
  }
}

async function createRound(request) {
  const course = courseForInput(request.language);
  if (!course) {
    throw new Error("Unknown language");
  }

  const data = await loadCourse(course);
  const count = clamp(Number.isFinite(request.count) ? request.count : 10, 1, MAX_COUNT);
  const srsProgress = readSrsProgress(data, request.inverse);
  const sentences = selectSrsSentences(
    data.sentences,
    data,
    request.inverse,
    count,
    srsProgress,
  );
  const cards = buildCards(sentences, data, request.inverse, request.mode, true);

  if (!cards.length) {
    throw new Error("No playable cards were generated");
  }

  currentRound = {
    course: data,
    inverse: request.inverse,
    cards,
    srsProgress,
    srsStorageKey: srsProgressKey(data, request.inverse),
    cursor: 0,
    correct: 0,
    answered: 0,
  };

  return {
    mode: request.mode,
    card: cardView(currentRound, cards[0], 0),
    summary: roundSummary(currentRound),
  };
}

function answerRound(request) {
  if (!currentRound) {
    throw new Error("Round not found");
  }
  if (currentRound.cursor >= currentRound.cards.length) {
    throw new Error("Round is already finished");
  }

  const cardIndex = currentRound.cursor;
  const card = currentRound.cards[cardIndex];
  if (!card || card.id !== request.cardId) {
    throw new Error("That card is not active");
  }

  let acceptedNewAnswer = false;
  if (!card.result) {
    card.result = checkAnswer(request.answer, card.prompt, currentRound.course);
    acceptedNewAnswer = true;
  }

  if (acceptedNewAnswer) {
    const isCorrect = card.result.outcome === "correct";
    if (isCorrect) {
      currentRound.correct += 1;
    }
    if (card.srsKey && !card.srsRecorded) {
      recordSrsReview(currentRound.srsProgress, card.srsKey, isCorrect, Date.now());
      writeSrsProgress(currentRound.srsStorageKey, currentRound.srsProgress);
      card.srsRecorded = true;
    }
    if (card.srsKey && !isCorrect) {
      currentRound.cards.push({
        ...card,
        result: null,
        srsRecorded: true,
      });
    }
    currentRound.answered += 1;
    currentRound.cursor += 1;
  }

  const summary = roundSummary(currentRound);
  const nextCard = currentRound.cards[currentRound.cursor]
    ? cardView(currentRound, currentRound.cards[currentRound.cursor], currentRound.cursor)
    : null;

  return {
    result: card.result,
    correctAnswer: card.prompt.word,
    wordExplanations: card.wordExplanations,
    summary,
    nextCard,
  };
}

async function loadCourse(course) {
  if (!courseCache.has(course.slug)) {
    courseCache.set(course.slug, fetchCourse(course));
  }
  return courseCache.get(course.slug);
}

async function fetchCourse(course) {
  const [corpus, vocabulary, explanations, tokens] = await Promise.all([
    fetchJson(course.corpusPath),
    fetchJson(course.vocabularyPath),
    fetchJson(course.explanationsPath),
    course.tokensPath ? fetchJson(course.tokensPath) : Promise.resolve({}),
  ]);

  return {
    ...course,
    sentences: corpus.data || [],
    vocabulary: vocabulary.map((entry) => entry.word).filter(Boolean),
    explanationsById: new Map(
      (explanations.data || []).map((entry) => [
        String(entry.id),
        (entry.words || []).map((word) => ({ ...word })),
      ]),
    ),
    tokensById: new Map(Object.entries(tokens || {})),
  };
}

async function fetchJson(path) {
  const response = await fetch(path, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new Error(`Could not load ${path}`);
  }
  return response.json();
}

function selectSrsSentences(sentences, course, inverse, count, progress) {
  const byKey = new Map(
    sentences.map((sentence) => [srsCardKey(course, inverse, sentence), sentence]),
  );
  const keys = Array.from(byKey.keys());
  const selectedKeys = selectSrsKeys(keys, progress, Date.now(), count);
  return selectedKeys.map((key) => byKey.get(key)).filter(Boolean);
}

function selectSrsKeys(keys, progress, now, count) {
  const uniqueKeys = Array.from(new Set(keys));
  const selected = new Set();
  const output = [];
  const cards = progress.cards || {};

  const due = uniqueKeys
    .filter((key) => cards[key] && Number(cards[key].dueAt || 0) <= now)
    .sort((left, right) => {
      const leftDue = Number(cards[left].dueAt || 0);
      const rightDue = Number(cards[right].dueAt || 0);
      return leftDue - rightDue || left.localeCompare(right);
    });
  appendSrsKeys(due, count, selected, output);

  const newKeys = shuffle(uniqueKeys.filter((key) => !cards[key]));
  appendSrsKeys(newKeys, count, selected, output);

  const upcoming = uniqueKeys
    .filter((key) => cards[key] && Number(cards[key].dueAt || 0) > now)
    .sort((left, right) => {
      const leftDue = Number(cards[left].dueAt || 0);
      const rightDue = Number(cards[right].dueAt || 0);
      return leftDue - rightDue || left.localeCompare(right);
    });
  appendSrsKeys(upcoming, count, selected, output);

  return output;
}

function appendSrsKeys(keys, count, selected, output) {
  for (const key of keys) {
    if (output.length >= count) {
      break;
    }
    if (!selected.has(key)) {
      selected.add(key);
      output.push(key);
    }
  }
}

function recordSrsReview(progress, key, isCorrect, now) {
  const cards = progress.cards || (progress.cards = {});
  const card =
    cards[key] ||
    (cards[key] = {
      intervalIndex: 0,
      dueAt: 0,
      lastReviewedAt: null,
      reviews: 0,
      correct: 0,
      wrong: 0,
      lapses: 0,
    });
  const wasNew = !card.reviews;

  if (isCorrect) {
    card.correct = Number(card.correct || 0) + 1;
    if (!wasNew) {
      card.intervalIndex = Math.min(
        Number(card.intervalIndex || 0) + 1,
        SRS_INTERVAL_DAYS.length - 1,
      );
    }
  } else {
    card.wrong = Number(card.wrong || 0) + 1;
    card.lapses = Number(card.lapses || 0) + 1;
    card.intervalIndex = 0;
  }

  card.reviews = Number(card.reviews || 0) + 1;
  card.lastReviewedAt = now;
  card.dueAt = now + SRS_INTERVAL_DAYS[card.intervalIndex] * MS_PER_DAY;
}

function readSrsProgress(course, inverse) {
  try {
    return normalizeSrsProgress(
      JSON.parse(localStorage.getItem(srsProgressKey(course, inverse)) || "{}"),
    );
  } catch {
    return normalizeSrsProgress({});
  }
}

function writeSrsProgress(key, progress) {
  localStorage.setItem(key, JSON.stringify(normalizeSrsProgress(progress)));
}

function normalizeSrsProgress(progress) {
  if (!progress || typeof progress !== "object") {
    return { cards: {} };
  }
  if (!progress.cards || typeof progress.cards !== "object") {
    progress.cards = {};
  }
  return progress;
}

function srsProgressKey(course, inverse) {
  return [
    "minicloze.srs.v1",
    course.slug,
    inverse ? "inverse" : "normal",
  ].join(":");
}

function srsCardKey(course, inverse, sentence) {
  return [
    course.slug,
    inverse ? "inverse" : "normal",
    String(sentence.id),
  ].join(":");
}

function buildCards(sentences, course, inverse, mode, withSrs = false) {
  const prompts = sentences.map((sentence) => {
    const prompt = generatePrompt(sentence, course, inverse);
    const translation = inverse
      ? firstTranslationText(sentence)
      : sentence.text || "";
    const wordExplanations =
      course.explanationsById.get(String(sentence.id)) || [];
    const srsKey = withSrs ? srsCardKey(course, inverse, sentence) : null;
    return { prompt, translation, wordExplanations, srsKey };
  });

  const optionPool = [
    ...course.vocabulary,
    ...prompts.map((item) => item.prompt.word),
  ];

  return prompts.map((item, id) => ({
    id,
    prompt: item.prompt,
    translation: item.translation,
    wordExplanations: item.wordExplanations,
    answerOptions:
      mode === "multiple_choice"
        ? buildOptions(item.prompt.word, optionPool)
        : [],
    srsKey: item.srsKey,
    srsRecorded: false,
    result: null,
  }));
}

function buildOptions(answer, pool) {
  const answerKey = normalizeOption(answer);
  const seen = new Set([answerKey]);
  const distractors = [];

  for (const candidateValue of pool) {
    const candidate = String(candidateValue || "").trim();
    const key = normalizeOption(candidate);
    if (!candidate || key === answerKey || seen.has(key)) {
      continue;
    }
    seen.add(key);
    distractors.push(candidate);
  }

  shuffle(distractors);
  const options = [answer, ...distractors.slice(0, 3)];
  return shuffle(options);
}

function generatePrompt(sentence, course, inverse) {
  const words = promptTokens(sentence, course, inverse);
  const candidates = words
    .map((word, index) => ({ word, index }))
    .filter(({ word }) => removePunctuation(word.text).length > 0)
    .map(({ index }) => index);

  const preferredIndex = preferredClozeIndex(sentence, words, candidates, inverse);
  const wordIndex =
    preferredIndex ??
    (candidates.length
      ? candidates[Math.floor(Math.random() * candidates.length)]
      : 0);
  const word = words[wordIndex] || { text: "", transliteration: null };

  return {
    firstHalf: joinPromptTokenText(words.slice(0, wordIndex)),
    word: removePunctuation(word.text),
    secondHalf: joinPromptTokenText(words.slice(wordIndex + 1)),
    firstHalfTransliteration: joinPromptTokenTransliteration(
      words.slice(0, wordIndex),
    ),
    wordTransliteration: word.transliteration
      ? removeTransliterationPunctuation(word.transliteration)
      : null,
    secondHalfTransliteration: joinPromptTokenTransliteration(
      words.slice(wordIndex + 1),
    ),
  };
}

function promptTokens(sentence, course, inverse) {
  if (inverse) {
    return tokenizePromptText("eng", sentence.text || "").map((text) => ({
      text,
      transliteration: null,
    }));
  }

  if (course.baseLanguage === "bod") {
    const tokens = course.tokensById.get(String(sentence.id));
    if (tokens) {
      return tokens.map((token) => ({
        text: token.text,
        transliteration: token.wylie && token.wylie.trim() ? token.wylie : null,
      }));
    }
    return tokenizeTibetanWithTarget(
      firstTranslationText(sentence),
      sentence.cloze_word,
    ).map((text) => ({ text, transliteration: null }));
  }

  return tokenizePromptText(course.baseLanguage, firstTranslationText(sentence)).map(
    (text) => ({ text, transliteration: null }),
  );
}

function preferredClozeIndex(sentence, words, candidates, inverse) {
  if (inverse || !sentence.cloze_word) {
    return null;
  }

  const target = normalizeClozeMatch(sentence.cloze_word);
  return (
    candidates.find((index) => normalizeClozeMatch(words[index].text) === target) ??
    null
  );
}

function tokenizePromptText(language, text) {
  const trimmed = String(text || "").trim();
  if (!trimmed) {
    return [];
  }

  if (NON_SPACED_LANGUAGES.has(language)) {
    return Array.from(trimmed);
  }
  if (language === "bod") {
    return tokenizeTibetanSyllables(trimmed);
  }

  return trimmed.match(/\S+\s*/g) || [];
}

function tokenizeTibetanWithTarget(text, target) {
  if (!target) {
    return tokenizeTibetanSyllables(text);
  }

  const index = text.indexOf(target);
  if (index < 0) {
    return tokenizeTibetanSyllables(text);
  }

  return [
    ...tokenizeTibetanSyllables(text.slice(0, index)),
    target,
    ...tokenizeTibetanSyllables(text.slice(index + target.length)),
  ];
}

function tokenizeTibetanSyllables(text) {
  const tokens = [];
  let current = "";

  for (const char of String(text || "").trim()) {
    current += char;
    if (TIBETAN_BREAKS.has(char) || /\s/u.test(char)) {
      pushTibetanToken(tokens, current);
      current = "";
    }
  }

  pushTibetanToken(tokens, current);
  return tokens;
}

function pushTibetanToken(tokens, token) {
  if (token.trim()) {
    tokens.push(token);
  }
}

function joinPromptTokenText(tokens) {
  return tokens.map((token) => token.text).join("");
}

function joinPromptTokenTransliteration(tokens) {
  const transliteration = tokens
    .map((token) => token.transliteration || "")
    .join("");
  return transliteration.trim() ? transliteration : null;
}

function cardView(round, card, index) {
  const blank = round.inverse
    ? "?"
    : "_".repeat(Math.max(Array.from(card.prompt.word).length, 3));
  const transliteration = card.prompt.wordTransliteration
    ? spacedClozeLine(
        card.prompt.firstHalfTransliteration || "",
        "_".repeat(Math.max(Array.from(card.prompt.wordTransliteration).length, 3)),
        card.prompt.secondHalfTransliteration || "",
      )
    : null;

  return {
    id: card.id,
    index: index + 1,
    total: round.cards.length,
    prompt_label: round.inverse ? "English" : round.course.label,
    translation_label: round.inverse ? round.course.label : "English",
    prompt: {
      first_half: card.prompt.firstHalf,
      blank,
      second_half: card.prompt.secondHalf,
    },
    transliteration,
    translation: card.translation,
    answer_options: card.answerOptions,
  };
}

function spacedClozeLine(firstHalf, blank, secondHalf) {
  const first = firstHalf.trimEnd();
  const second = secondHalf.trimStart();

  return {
    first_half: first ? `${first} ` : "",
    blank,
    second_half: second ? ` ${second}` : "",
  };
}

function roundSummary(round) {
  return {
    total: round.cards.length,
    answered: round.answered,
    correct: round.correct,
    finished: round.answered >= round.cards.length,
  };
}

function checkAnswer(guess, prompt, course) {
  const distance = answerDistance(guess, prompt);
  const outcome =
    distance === 0
      ? "correct"
      : distance < DISTANCE_FOR_CLOSE
        ? "close"
        : "wrong";

  return {
    outcome,
    distance,
    answer: answerWithTransliteration(prompt, course),
  };
}

function answerWithTransliteration(prompt, course) {
  if (course.baseLanguage === "bod" && prompt.wordTransliteration) {
    return `${prompt.word.toLowerCase().trim()} (${prompt.wordTransliteration})`;
  }
  return prompt.word.toLowerCase().trim();
}

function answerDistance(guess, prompt) {
  const nativeDistance = levenshtein(
    removePunctuation(String(guess || "").trim().toLowerCase()),
    prompt.word.toLowerCase().trim(),
  );
  const transliteratedWord = transliteratedAnswer(prompt);
  if (!transliteratedWord) {
    return nativeDistance;
  }

  const normalizedGuess = normalizeLatinAnswer(guess);
  if (!normalizedGuess) {
    return nativeDistance;
  }
  return Math.min(nativeDistance, levenshtein(normalizedGuess, transliteratedWord));
}

function transliteratedAnswer(prompt) {
  const transliteration = prompt.wordTransliteration || prompt.word;
  const normalized = normalizeLatinAnswer(transliteration);
  return normalized || null;
}

function normalizeLatinAnswer(answer) {
  const transliterated = Array.from(String(answer || "").toLowerCase())
    .map((char) => CYRILLIC_LATIN[char] ?? char)
    .join("");

  return transliterated
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .replace(/[^a-z0-9]/g, "");
}

function levenshtein(left, right) {
  const a = Array.from(left);
  const b = Array.from(right);
  let previous = Array.from({ length: b.length + 1 }, (_, index) => index);

  for (let i = 0; i < a.length; i += 1) {
    const current = [i + 1];
    for (let j = 0; j < b.length; j += 1) {
      const cost = a[i] === b[j] ? 0 : 1;
      current[j + 1] = Math.min(
        current[j] + 1,
        previous[j + 1] + 1,
        previous[j] + cost,
      );
    }
    previous = current;
  }

  return previous[b.length];
}

function renderCard(card) {
  currentCard = card;
  pendingNextCard = null;
  answeredCurrentCard = false;

  hide(els.emptyState);
  hide(els.summaryView);
  show(els.cardView);
  hide(els.feedback);
  hide(els.wordExplanations);
  hide(els.nextButton);

  els.cardPosition.textContent = `${card.index} / ${card.total}`;
  els.promptLabel.textContent = card.prompt_label;
  els.translationLabel.textContent = card.translation_label;
  renderClozeLine(els.promptLine, card.prompt);
  els.translationText.textContent = card.translation;

  if (card.transliteration) {
    renderClozeLine(els.wylieLine, card.transliteration);
    show(els.wylieLine);
  } else {
    hide(els.wylieLine);
  }

  if (activeMode === "multiple_choice") {
    renderChoices(card.answer_options);
    show(els.choices);
    hide(els.textAnswerForm);
  } else {
    els.textAnswer.value = "";
    hide(els.choices);
    show(els.textAnswerForm);
    requestAnimationFrame(() => els.textAnswer.focus());
  }

  disableAnswerInputs(false);
}

function renderClozeLine(element, line) {
  element.replaceChildren(
    document.createTextNode(line.first_half),
    blankNode(line.blank),
    document.createTextNode(line.second_half),
  );
}

function blankNode(text) {
  const span = document.createElement("span");
  span.className = "blank";
  span.textContent = text;
  return span;
}

function renderChoices(options) {
  els.choices.replaceChildren(
    ...options.map((option) => {
      const button = document.createElement("button");
      button.className = "choice-button";
      button.type = "button";
      button.textContent = option;
      button.addEventListener("click", () => submitAnswer(option));
      return button;
    }),
  );
}

function renderFeedback(result) {
  const labels = {
    correct: "Correct",
    close: "Close",
    wrong: "Wrong",
  };
  els.feedback.className = `feedback ${result.outcome}`;
  els.feedback.textContent = `${labels[result.outcome] || "Result"}: ${result.answer}`;
  show(els.feedback);
}

function renderWordExplanations(explanations) {
  if (!explanations.length) {
    hide(els.wordExplanations);
    return;
  }

  const title = document.createElement("p");
  title.className = "word-explanations-title";
  title.textContent = "Words";

  const list = document.createElement("dl");
  for (const explanation of explanations) {
    const term = document.createElement("dt");
    term.append(document.createTextNode(explanation.word));
    if (explanation.wylie) {
      const wylie = document.createElement("span");
      wylie.className = "word-explanations-wylie";
      wylie.textContent = explanation.wylie;
      term.append(wylie);
    }

    const definition = document.createElement("dd");
    definition.textContent = explanation.note
      ? `${explanation.gloss} (${explanation.note})`
      : explanation.gloss;
    list.append(term, definition);
  }

  els.wordExplanations.replaceChildren(title, list);
  show(els.wordExplanations);
}

function markChoices(answer, correctAnswer, result) {
  if (activeMode !== "multiple_choice") {
    return;
  }

  for (const button of els.choices.querySelectorAll("button")) {
    if (sameAnswer(button.textContent, correctAnswer)) {
      button.classList.add("correct");
    }
    if (sameAnswer(button.textContent, answer) && result.outcome !== "correct") {
      button.classList.add("wrong");
    }
  }
}

function sameAnswer(left, right) {
  return left.trim().toLocaleLowerCase() === right.trim().toLocaleLowerCase();
}

function disableAnswerInputs(disabled) {
  for (const button of els.choices.querySelectorAll("button")) {
    button.disabled = disabled;
  }
  els.textAnswer.disabled = disabled;
  const submit = els.textAnswerForm.querySelector("button");
  if (submit) {
    submit.disabled = disabled;
  }
}

function renderRoundSummary(summary) {
  els.roundScore.textContent = `${summary.correct} / ${summary.answered}`;
  const percent = summary.total ? Math.round((summary.answered / summary.total) * 100) : 0;
  els.progressFill.style.width = `${percent}%`;
}

function renderFinalSummary() {
  hide(els.cardView);
  show(els.summaryView);
  const total = currentSummary.total || 0;
  const correct = currentSummary.correct || 0;
  const percent = total ? Math.round((correct / total) * 100) : 0;
  els.summaryViewTitle.textContent = `${correct} / ${total}`;
  els.summaryText.textContent = `${percent}% correct in this round.`;
}

function renderStoredStats() {
  const stats = readStats();
  els.storedPlayed.textContent = String(stats.played);
  els.storedAccuracy.textContent = stats.played
    ? `${Math.round((stats.correct / stats.played) * 100)}%`
    : "0%";
  els.storedStreak.textContent = String(stats.streak);
}

function recordStoredStats(isCorrect) {
  const stats = readStats();
  stats.played += 1;
  if (isCorrect) {
    stats.correct += 1;
    stats.streak += 1;
    stats.bestStreak = Math.max(stats.bestStreak, stats.streak);
  } else {
    stats.streak = 0;
  }
  localStorage.setItem(statsKey(), JSON.stringify(stats));
  renderStoredStats();
}

function readStats() {
  const fallback = { played: 0, correct: 0, streak: 0, bestStreak: 0 };
  try {
    return { ...fallback, ...JSON.parse(localStorage.getItem(statsKey()) || "{}") };
  } catch {
    return fallback;
  }
}

function statsKey() {
  return [
    "minicloze.stats.v1",
    els.languageSelect.value || "mongolian-a1",
    selectedMode(),
    els.inverseToggle.checked ? "inverse" : "normal",
  ].join(":");
}

function selectedMode() {
  const selected = document.querySelector("input[name='mode']:checked");
  return selected ? selected.value : "multiple_choice";
}

function showEmptyError(message) {
  hide(els.cardView);
  hide(els.summaryView);
  els.emptyState.innerHTML = "";
  const label = document.createElement("p");
  label.className = "panel-label";
  label.textContent = "Error";
  const title = document.createElement("h2");
  title.textContent = message;
  els.emptyState.append(label, title);
  show(els.emptyState);
}

function setBusy(isBusy) {
  els.startButton.disabled = isBusy;
  els.startButton.textContent = isBusy ? "Starting" : "Start";
}

function show(element) {
  element.classList.remove("hidden");
}

function hide(element) {
  element.classList.add("hidden");
}

function courseForInput(input) {
  return COURSES.find(
    (course) => course.slug === input || course.code === input || course.baseLanguage === input,
  );
}

function firstTranslationText(sentence) {
  return sentence.translations?.[0]?.text || "";
}

function removePunctuation(word) {
  return String(word || "")
    .replace(/[(),.;:?¿!¡"«»。 །༎༏༐༑༔]/gu, "")
    .replace(/^[་༌]+|[་༌]+$/gu, "");
}

function removeTransliterationPunctuation(word) {
  const chars = Array.from(String(word || "").trim());
  let start = 0;
  let end = chars.length;

  while (start < end && TRANSLITERATION_TRIM.has(chars[start])) {
    start += 1;
  }
  while (end > start && TRANSLITERATION_TRIM.has(chars[end - 1])) {
    end -= 1;
  }

  return chars.slice(start, end).join("");
}

function normalizeClozeMatch(word) {
  return removePunctuation(word).toLowerCase();
}

function normalizeOption(option) {
  return String(option || "").trim().toLowerCase();
}

function shuffle(items) {
  for (let index = items.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [items[index], items[swapIndex]] = [items[swapIndex], items[index]];
  }
  return items;
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) {
    return;
  }

  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js").catch(() => {});
  });
}
