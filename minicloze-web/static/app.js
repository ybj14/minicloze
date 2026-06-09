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
  summaryTitle: document.querySelector("#summaryTitle"),
  summaryText: document.querySelector("#summaryText"),
};

let roundId = null;
let currentCard = null;
let currentSummary = { total: 0, answered: 0, correct: 0, finished: false };
let pendingNextCard = null;
let activeMode = "multiple_choice";
let answeredCurrentCard = false;

document.addEventListener("DOMContentLoaded", async () => {
  bindEvents();
  await loadLanguages();
  renderStoredStats();
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

async function loadLanguages() {
  const languages = await api("/api/languages");
  els.languageSelect.replaceChildren(
    ...languages.map((language) => {
      const option = document.createElement("option");
      option.value = language.slug;
      option.textContent = `${language.label} (${language.sentence_count})`;
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
    const data = await api("/api/rounds", {
      method: "POST",
      body: JSON.stringify({
        language: els.languageSelect.value,
        mode: activeMode,
        count: Number(els.countSelect.value),
        inverse: els.inverseToggle.checked,
      }),
    });

    roundId = data.round_id;
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
  if (!roundId || !currentCard || answeredCurrentCard) {
    return;
  }

  answeredCurrentCard = true;
  disableAnswerInputs(true);
  try {
    const data = await api(`/api/rounds/${roundId}/answer`, {
      method: "POST",
      body: JSON.stringify({
        card_id: currentCard.id,
        answer,
      }),
    });

    currentSummary = data.summary;
    pendingNextCard = data.next_card;
    recordStoredStats(data.result.outcome === "correct");
    renderRoundSummary(data.summary);
    renderFeedback(data.result);
    renderWordExplanations(data.word_explanations || []);
    markChoices(answer, data.correct_answer, data.result);
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
  els.summaryTitle.textContent = `${correct} / ${total}`;
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

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `Request failed with ${response.status}`);
  }
  return data;
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
