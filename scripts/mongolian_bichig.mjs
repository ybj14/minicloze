#!/usr/bin/env node
/**
 * Build-time Cyrillic → Traditional Mongolian (Hudum / Mongol bichig) + Poppe
 * (Classical / scholarly Latin, 鲍培转写) converter.
 *
 * Uses @gege-mn/gege-converter (a CANDIDATE GENERATOR, ~74% top-1 per its own
 * README — output is NOT expert-reviewed). The top candidate's `classical` field
 * is the converter's code-point romanization, not true Poppe: it leaks FVS
 * digits (`mašin1`), letter-boundary dots, `kh` for ᠻ, and — in the harvested
 * tier — writes q/γ in front-vowel words (`deγer-e`, `qeüqed`). We therefore
 * run it through normalizePoppe() (mechanical, harmony-based) and apply the
 * reviewed per-surface overrides in scripts/data/mongolian_bichig_overrides.json
 * (each row cites its source). Fallback: fromScript(bichig).
 *
 * Display order (UI): Cyrillic → bichig → poppe (mirrors Tibetan native → zwpy → Wylie).
 *
 * Usage:
 *   node scripts/mongolian_bichig.mjs [--course mongolian_a1] [--log PATH]
 * Default: both mongolian_a1 and mongolian_swadesh.
 *
 * Reads/writes under minicloze-web/static/data/ (after copy_base_data).
 * Also writes tokens (+ enriched explanations) into minicloze-lib/corpora/.
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { analyze, convert } from "@gege-mn/gege-converter";
import { fromScript, harmonyOf } from "@gege-mn/mongol-bichig";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const STATIC_DATA = path.join(ROOT, "minicloze-web", "static", "data");
const CORPORA = path.join(ROOT, "minicloze-lib", "corpora");

const OVERRIDES_PATH = path.join(ROOT, "scripts", "data", "mongolian_bichig_overrides.json");

function loadOverrides() {
  if (!fs.existsSync(OVERRIDES_PATH)) return new Map();
  const rows = JSON.parse(fs.readFileSync(OVERRIDES_PATH, "utf8")).overrides || [];
  const map = new Map();
  for (const row of rows) {
    const key = String(row.cyrillic).toLowerCase();
    if (!map.has(key)) map.set(key, []);
    map.get(key).push({ ...row, glossRe: row.when_gloss ? new RegExp(row.when_gloss, "i") : null });
  }
  return map;
}

const OVERRIDES = loadOverrides();

/** Reviewed override for this surface (+ gloss, for homograph rows), or null. */
function findOverride(surface, gloss, sentenceId = null) {
  const rows = OVERRIDES.get(String(surface || "").trim().toLowerCase());
  if (!rows) return null;
  for (const row of rows) {
    if (sentenceId != null && (row.except_sentence_ids || []).includes(String(sentenceId))) continue;
    if (!row.glossRe) return row;
    if (gloss && row.glossRe.test(gloss)) return row;
  }
  return null;
}

function overrideResult(row) {
  return {
    bichig: row.bichig,
    poppe: row.poppe,
    provenance: "reviewed-override",
    confidence: 1,
    source: row.source || [],
  };
}

// ---------------------------------------------------------------------------
// Review status ("verified" marker).
//
// A word form is verified:true only if
//   (a) a sourced override row covers it, or
//   (b) its bichig equals a dictionary string recorded in
//       scripts/data/mongolian_dictionary_evidence.json (mongoltoli.mn and/or
//       Wiktionary, exact match after NNBSP/space -> MVS) AND its Poppe equals
//       the rule-based transliteration of that bichig (toPoppe below),
// and it is not in a known-unresolved category from
// scripts/data/mongolian_review_flags.json. Everything else is verified:false
// with the reason codes in `review`. The marker never changes bichig/Poppe.
// ---------------------------------------------------------------------------

const EVIDENCE_PATH = path.join(ROOT, "scripts", "data", "mongolian_dictionary_evidence.json");
const FLAGS_PATH = path.join(ROOT, "scripts", "data", "mongolian_review_flags.json");
const REVIEW_QUEUE_JSON = path.join(ROOT, "scripts", "data", "mongolian_review_queue.json");
const REVIEW_QUEUE_MD = path.join(ROOT, "scripts", "data", "mongolian_review_queue.md");
const VERIFIED_WORDS_JSON = path.join(ROOT, "scripts", "data", "mongolian_verified_words.json");

const EVIDENCE = fs.existsSync(EVIDENCE_PATH)
  ? JSON.parse(fs.readFileSync(EVIDENCE_PATH, "utf8")).evidence || {}
  : {};
const FLAGS = fs.existsSync(FLAGS_PATH) ? JSON.parse(fs.readFileSync(FLAGS_PATH, "utf8")) : {};
const PAST_LAA_RE = new RegExp(FLAGS.past_laa?.surface_regex || "(лаа|лоо|лээ|лөө)$", "iu");
const PAST_LAA_EXCLUDE_RE = new RegExp(FLAGS.past_laa?.exclude_gloss_regex || "^$", "iu");
const HOMOGRAPHS = new Set((FLAGS.homographs || []).map((r) => r.cyrillic.toLowerCase()));
const GLOSS_ERRORS = (FLAGS.gloss_errors || []).map((r) => ({
  cyrillic: r.cyrillic.toLowerCase(),
  ids: new Set((r.sentence_ids || []).map(String)),
}));

const MVS = "\u180e";
function normScript(s) {
  return String(s || "").trim().replace(/[\u202f ]/g, MVS);
}
function normScriptMt(s) {
  return normScript(s).replace(/\u1836$/u, "\u1822");
}

/** Dictionary sources whose recorded bichig equals `bichig` exactly. */
export function dictionaryMatches(surface, bichig) {
  const ev = EVIDENCE[String(surface || "").toLowerCase()];
  if (!ev || !bichig) return [];
  const b = normScript(bichig);
  const out = [];
  if (ev.mongoltoli && normScriptMt(ev.mongoltoli.bichig) === b) out.push("mongoltoli.mn");
  if (ev.wiktionary && (ev.wiktionary.bichig || []).some((x) => normScript(x) === b)) {
    out.push("Wiktionary");
  }
  return out;
}

const POPPE_LETTERS = {
  "\u1820": "a", "\u1821": "e", "\u1822": "i", "\u1823": "o", "\u1824": "u",
  "\u1825": "ö", "\u1826": "ü", "\u1827": "ē", "\u1828": "n", "\u1829": "ng",
  "\u182a": "b", "\u182b": "p", "\u182c": "Q", "\u182d": "G", "\u182e": "m",
  "\u182f": "l", "\u1830": "s", "\u1831": "š", "\u1832": "t", "\u1833": "d",
  "\u1834": "č", "\u1835": "ǰ", "\u1836": "y", "\u1837": "r", "\u1838": "w",
  "\u1839": "f", "\u183a": "k", "\u183b": "k", "\u183c": "c", "\u183d": "z",
  "\u183e": "h", "\u180e": "-", "\u202f": "-", " ": " ",
};
const IGNORABLE = /[\u180b-\u180d\u180f\u200c\u200d]/u;

/**
 * Rule-based Poppe-style transliteration of bichig (independent of the
 * converter): one letter per code point; ᠬ/ᠭ are q/γ in a back-vowel word
 * (any a/o/u in the space-separated chunk) and k/g otherwise. Unknown code
 * points become "?" so they never match.
 */
export function toPoppe(bichig) {
  let s = "";
  for (const ch of String(bichig || "")) {
    if (IGNORABLE.test(ch)) continue;
    s += POPPE_LETTERS[ch] ?? "?";
  }
  return s
    .split(" ")
    .map((w) => {
      const back = /[aou]/.test(w.replace(/[QG]/g, ""));
      return w.replace(/Q/g, back ? "q" : "k").replace(/G/g, back ? "γ" : "g");
    })
    .join(" ");
}

/** Review status for one token (context-dependent: gloss and sentence id). */
export function reviewToken({ surface, gloss, sentenceId, result }) {
  if (!result?.bichig) return null;
  const lower = String(surface || "").trim().toLowerCase();
  const dict = dictionaryMatches(lower, result.bichig);
  if (result.provenance === "reviewed-override") {
    return { verified: true, verifiedBy: ["sourced override", ...(result.source || [])], dict };
  }
  const reasons = [];
  if (GLOSS_ERRORS.some((g) => g.cyrillic === lower && g.ids.has(String(sentenceId)))) {
    reasons.push("gloss-error");
  }
  if (HOMOGRAPHS.has(lower)) reasons.push("homograph");
  if (PAST_LAA_RE.test(lower) && !PAST_LAA_EXCLUDE_RE.test(String(gloss || "").trim())) {
    reasons.push("past-laa");
  }
  const poppe = String(result.poppe || "");
  if (/(тай|тэй|той|төй)$/u.test(lower) && /-t[ae]i(\s|$)/u.test(poppe)) {
    reasons.push("tai-detached");
  }
  if (/-(du|tu|dü|tü)-(ban|ben)\b/u.test(poppe)) reasons.push("du-ban");
  if (dict.length) {
    if (toPoppe(result.bichig) !== poppe) reasons.push("poppe-rule-mismatch");
  } else {
    if (result.provenance === "guess") reasons.push("guess-tier");
    reasons.push("not-dictionary-checked");
  }
  if (reasons.length) return { verified: false, reasons, dict };
  return { verified: true, verifiedBy: dict, dict };
}

const BACK_VOWELS = /[aou]/;
const FRONT_VOWELS = /[eöüē]/;

/**
 * Mechanical clean-up of the converter's `classical` string into Poppe-style
 * transcription. Only changes that are unambiguous:
 *  - drop FVS digits (1–4) and letter-boundary dots — encoding artefacts;
 *  - `kh` (ᠻ, loan KHA) → k;
 *  - in a word whose vowels are all front (e ö ü ē, optionally i) and that has
 *    no back vowel (a o u), ᠬ/ᠭ can only be k/g, so q→k and γ→g.
 * Back-vowel and mixed (loan) words are left as the converter wrote them, so
 * reviewed lexicon readings such as `salkin` are untouched.
 * "Word" = one space-separated chunk including its MVS-joined suffixes.
 */
export function normalizePoppe(classical) {
  if (!classical) return classical;
  return classical
    .split(" ")
    .map((word) => {
      let w = word.replace(/(?<=\p{L})[1-4]/gu, "").replace(/(?<=\p{L})\.(?=\p{L})/gu, "");
      w = w.replace(/kh/g, "k");
      if (FRONT_VOWELS.test(w) && !BACK_VOWELS.test(w)) {
        w = w.replace(/q/g, "k").replace(/γ/g, "g");
      }
      return w;
    })
    .join(" ");
}

const DEFAULT_COURSES = ["mongolian_a1", "mongolian_swadesh"];

/** Strip trailing Mongolian/Cyrillic punctuation that shouldn't be converted alone. */
const PUNCT_RE = /^[\s.,!?;:'"“”‘’…—–\-()[\]{}«»]+$/u;

function parseArgs(argv) {
  const courses = [];
  let logPath = null;
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--course" && argv[i + 1]) {
      courses.push(argv[++i]);
    } else if (arg === "--log" && argv[i + 1]) {
      logPath = argv[++i];
    }
  }
  return {
    courses: courses.length ? courses : DEFAULT_COURSES,
    logPath,
  };
}

/**
 * Join Classical romanization segments from analyze() parts.
 * Skip empty/whitespace-only parts; separate with a single space.
 */
function classicalFromParts(parts) {
  const segments = [];
  for (const part of parts) {
    const top = part.candidates?.[0];
    const classical = String(top?.classical || "").trim();
    if (classical) {
      segments.push(classical);
    }
  }
  return segments.join(" ");
}

/**
 * Top-1 conversion for a single surface form.
 * Returns { bichig, poppe, provenance, confidence } or null if empty/punct.
 */
function convertWord(raw) {
  const text = String(raw || "").trim();
  if (!text || PUNCT_RE.test(text)) {
    return null;
  }

  const override = findOverride(text, null);
  if (override) {
    return overrideResult(override);
  }

  let provenance = "unknown";
  let confidence = null;
  let parts = [];
  try {
    parts = analyze(text);
    // Prefer worst provenance across tokens (guess < toli < harvested < lexicon).
    const rank = { guess: 0, toli: 1, harvested: 2, lexicon: 3, unknown: -1 };
    let worst = "lexicon";
    let confSum = 0;
    let confN = 0;
    for (const part of parts) {
      const top = part.candidates?.[0];
      if (!top) continue;
      const p = top.provenance || "unknown";
      if ((rank[p] ?? -1) < (rank[worst] ?? 99)) {
        worst = p;
      }
      if (typeof top.confidence === "number") {
        confSum += top.confidence;
        confN += 1;
      }
    }
    provenance = worst;
    confidence = confN ? confSum / confN : null;
  } catch {
    provenance = "error";
    parts = [];
  }

  let bichig = "";
  try {
    bichig = convert(text) || "";
  } catch {
    bichig = "";
    provenance = "error";
  }

  let poppe = normalizePoppe(classicalFromParts(parts));
  if (!poppe && bichig.trim()) {
    try {
      const harmony = harmonyOf(bichig) || undefined;
      poppe = normalizePoppe(fromScript(bichig, harmony) || "");
    } catch {
      poppe = "";
    }
  }

  if (!bichig.trim() && !poppe.trim()) {
    return null;
  }

  return {
    bichig: bichig.trim() || null,
    poppe: poppe.trim() || null,
    provenance,
    confidence,
  };
}

/** Aggregate review status per lower-cased surface (for queue / verified list). */
function recordReview(reviewLog, { course, sentence, word, result, review }) {
  const key = String(word.word || "").trim().toLowerCase();
  if (!reviewLog.has(key)) {
    reviewLog.set(key, { cyrillic: key, tokens: 0, unverifiedTokens: 0, forms: new Map() });
  }
  const entry = reviewLog.get(key);
  entry.tokens += 1;
  if (!review.verified) entry.unverifiedTokens += 1;
  const formKey = `${result.bichig}\t${result.poppe}\t${review.verified}\t${(review.reasons || []).join(" ")}`;
  if (!entry.forms.has(formKey)) {
    entry.forms.set(formKey, {
      bichig: result.bichig,
      poppe: result.poppe,
      verified: review.verified,
      verified_by: review.verified ? review.verifiedBy : undefined,
      reasons: review.verified ? undefined : review.reasons,
      dictionary_match: review.dict.length ? review.dict : undefined,
      converter_tier: result.provenance,
      glosses: new Set(),
      courses: new Set(),
      sentence_ids: [],
      tokens: 0,
    });
  }
  const form = entry.forms.get(formKey);
  form.tokens += 1;
  if (word.gloss) form.glosses.add(word.gloss);
  form.courses.add(course);
  if (form.sentence_ids.length < 5) form.sentence_ids.push(String(sentence.id));
}

function formOut(f) {
  return { ...f, glosses: [...f.glosses], courses: [...f.courses] };
}

function writeReviewOutputs(reviewLog) {
  const totalTokens = [...reviewLog.values()].reduce((a, e) => a + e.tokens, 0);
  const unverifiedTokens = [...reviewLog.values()].reduce((a, e) => a + e.unverifiedTokens, 0);
  const queue = [];
  const verified = [];
  for (const entry of reviewLog.values()) {
    for (const f of entry.forms.values()) {
      const row = { cyrillic: entry.cyrillic, ...formOut(f) };
      (f.verified ? verified : queue).push(row);
    }
  }
  const byFreq = (a, b) => b.tokens - a.tokens || a.cyrillic.localeCompare(b.cyrillic, "mn");
  queue.sort(byFreq).forEach((row, i) => (row.rank = i + 1));
  verified.sort(byFreq);

  const reasonCounts = {};
  for (const row of queue) {
    for (const r of row.reasons) {
      reasonCounts[r] = reasonCounts[r] || { types: 0, tokens: 0 };
      reasonCounts[r].types += 1;
      reasonCounts[r].tokens += row.tokens;
    }
  }
  const summary = {
    tokens: totalTokens,
    verifiedTokens: totalTokens - unverifiedTokens,
    unverifiedTokens,
    verifiedTokenPct: Number(((100 * (totalTokens - unverifiedTokens)) / totalTokens).toFixed(1)),
    verifiedForms: verified.length,
    unverifiedForms: queue.length,
    reasons: reasonCounts,
  };

  writeJsonPretty(REVIEW_QUEUE_JSON, {
    _comment:
      "GENERATED by scripts/mongolian_bichig.mjs - do not edit. Mongolian word forms whose bichig/Poppe are NOT verified (verified:false in the data), ranked by token frequency across mongolian_a1 + mongolian_swadesh. One row per (surface, reading, reason set). Reason codes: scripts/data/mongolian_review_flags.json. To resolve a row, add a sourced row to scripts/data/mongolian_bichig_overrides.json and rebuild.",
    summary,
    queue,
  });
  writeJsonPretty(VERIFIED_WORDS_JSON, {
    _comment:
      "GENERATED by scripts/mongolian_bichig.mjs - do not edit. Word forms marked verified:true and the source(s) that support them: a sourced override row, or an exact bichig match in scripts/data/mongolian_dictionary_evidence.json (mongoltoli.mn / Wiktionary) with Poppe equal to the rule-based transliteration of that bichig. 'Verified' means dictionary-checked, not reviewed by a reader of Traditional Mongolian.",
    summary,
    verified,
  });

  const esc = (v) => String(v ?? "").replace(/\|/g, "\\|");
  const line = (r) =>
    `| ${r.rank} | ${esc(r.cyrillic)} | ${esc(r.glosses.join("; "))} | ${esc(r.bichig)} | ${esc(r.poppe)} | ${r.tokens} | ${r.reasons.join(", ")} | ${r.dictionary_match ? r.dictionary_match.join(", ") : ""} | ${r.sentence_ids.join(" ")} |`;
  const head =
    "| # | Cyrillic | Gloss | Bichig (current) | Poppe (current) | Tokens | Reasons | Dict. match | Sentences |\n|---|---|---|---|---|---|---|---|---|";
  const top = queue.slice(0, 230);
  const topSet = new Set(top);
  const guessRest = queue.filter((r) => !topSet.has(r) && r.reasons.includes("guess-tier"));
  const rest = queue.filter((r) => !topSet.has(r) && !r.reasons.includes("guess-tier"));
  const reasonDocs = FLAGS.reasons || {};
  const md = [
    "# Mongolian bichig / Poppe review queue",
    "",
    "GENERATED by `scripts/mongolian_bichig.mjs` — do not edit by hand. Source of truth: `mongolian_review_queue.json`.",
    "",
    `Every form below is shown in the app as **unverified** (\`verified: false\`). The bichig and Poppe are the current machine output of \`@gege-mn/gege-converter\` 0.5.0 (plus mechanical Poppe clean-up) and have **not** been checked by a reader of Traditional Mongolian. Fix a form by adding a sourced row to \`scripts/data/mongolian_bichig_overrides.json\` and rebuilding.`,
    "",
    `Tokens: ${summary.tokens}; verified (dictionary-checked or sourced override): ${summary.verifiedTokens} (${summary.verifiedTokenPct}%); unverified: ${summary.unverifiedTokens}. Unverified forms: ${summary.unverifiedForms}.`,
    "",
    "## Reason codes",
    "",
    "| Code | Forms | Tokens | Meaning |",
    "|---|---|---|---|",
    ...Object.entries(reasonCounts)
      .sort((a, b) => b[1].tokens - a[1].tokens)
      .map(([k, v]) => `| ${k} | ${v.types} | ${v.tokens} | ${esc(reasonDocs[k] || "")} |`),
    "",
    "Dict. match = a dictionary string matches the bichig, but the form is held back because it is in a known-unresolved category or its Poppe is not the rule transliteration.",
    "",
    `## 1. Top ${top.length} by token frequency`,
    "",
    head,
    ...top.map(line),
    "",
    `## 2. Remaining guess-tier forms (${guessRest.length})`,
    "",
    head,
    ...guessRest.map(line),
    "",
    `## 3. All other unverified forms (${rest.length})`,
    "",
    head,
    ...rest.map(line),
    "",
  ].join("\n");
  fs.writeFileSync(REVIEW_QUEUE_MD, md, "utf8");
  return summary;
}

function loadJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJsonCompact(filePath, value) {
  fs.writeFileSync(filePath, JSON.stringify(value, null, 0), "utf8");
}

function writeJsonPretty(filePath, value) {
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function processCourse(course, cache, guessLog, reviewLog) {
  const explanationsPath = path.join(STATIC_DATA, `${course}_explanations.json`);
  if (!fs.existsSync(explanationsPath)) {
    throw new Error(`Missing explanations: ${explanationsPath}`);
  }

  const explanations = loadJson(explanationsPath);
  const tokenized = {};
  let wordCount = 0;
  let withBichig = 0;
  let withPoppe = 0;
  let guessCount = 0;

  for (const sentence of explanations.data || []) {
    const words = sentence.words || [];
    const tokens = [];

    for (let index = 0; index < words.length; index++) {
      const word = words[index];
      const surface = word.word || "";
      wordCount += 1;

      const glossOverride = findOverride(surface, word.gloss || "", sentence.id);
      let cached = glossOverride?.glossRe ? overrideResult(glossOverride) : cache.get(surface);
      if (cached === undefined) {
        cached = convertWord(surface);
        cache.set(surface, cached);
        if (cached && cached.provenance === "guess") {
          guessLog.push({
            course,
            word: surface,
            bichig: cached.bichig,
            poppe: cached.poppe,
            confidence: cached.confidence,
          });
        }
      }

      const review = reviewToken({
        surface,
        gloss: word.gloss || "",
        sentenceId: sentence.id,
        result: cached,
      });
      delete word.verified;
      delete word.verified_by;
      delete word.review;
      if (review) {
        word.verified = review.verified;
        if (review.verified) {
          word.verified_by = review.verifiedBy.join("; ");
        } else {
          word.review = review.reasons.join(" ");
        }
        recordReview(reviewLog, { course, sentence, word, result: cached, review });
      }

      if (cached?.bichig) {
        word.bichig = cached.bichig;
        withBichig += 1;
        if (cached.provenance === "guess") {
          guessCount += 1;
        }
      } else {
        delete word.bichig;
      }

      if (cached?.poppe) {
        word.poppe = cached.poppe;
        withPoppe += 1;
      } else {
        delete word.poppe;
      }

      let text = surface;
      if (index + 1 < words.length) {
        text = `${text} `;
      }
      const token = { text };
      if (cached?.bichig) {
        token.bichig = cached.bichig;
      }
      if (cached?.poppe) {
        token.poppe = cached.poppe;
      }
      if (review) {
        token.verified = review.verified;
      }
      tokens.push(token);
    }

    tokenized[String(sentence.id)] = tokens;
  }

  // Write enriched explanations + tokens to static/
  writeJsonPretty(explanationsPath, explanations);
  const tokensStatic = path.join(STATIC_DATA, `${course}_tokens.json`);
  writeJsonCompact(tokensStatic, tokenized);

  // Sync to corpora/
  writeJsonPretty(path.join(CORPORA, `${course}_explanations.json`), explanations);
  writeJsonCompact(path.join(CORPORA, `${course}_tokens.json`), tokenized);

  return {
    course,
    sentences: (explanations.data || []).length,
    words: wordCount,
    withBichig,
    withPoppe,
    guessSurfaceUses: guessCount,
    uniqueGuesses: guessLog.filter((g) => g.course === course).length,
  };
}

function main() {
  const { courses, logPath } = parseArgs(process.argv.slice(2));
  fs.mkdirSync(STATIC_DATA, { recursive: true });
  fs.mkdirSync(CORPORA, { recursive: true });

  const cache = new Map();
  const guessLog = [];
  const reviewLog = new Map();
  const summaries = [];

  for (const course of courses) {
    summaries.push(processCourse(course, cache, guessLog, reviewLog));
  }

  // Unique lemma guess list across courses
  const uniqueGuesses = new Map();
  for (const g of guessLog) {
    if (!uniqueGuesses.has(g.word)) {
      uniqueGuesses.set(g.word, g);
    }
  }

  const reviewSummary = writeReviewOutputs(reviewLog);

  const report = {
    converter: "@gege-mn/gege-converter",
    poppeSource:
      "normalizePoppe(candidate.classical) — FVS digits/dots stripped, kh→k, front-harmony q/γ→k/g; reviewed overrides from scripts/data/mongolian_bichig_overrides.json; fallback fromScript(bichig). NOT expert-reviewed beyond the override rows.",
    overridesApplied: OVERRIDES.size,
    review: reviewSummary,
    courses: summaries,
    uniqueSurfaces: cache.size,
    guessTierUnique: [...uniqueGuesses.values()].sort((a, b) =>
      a.word.localeCompare(b.word, "mn"),
    ),
  };

  const outLog =
    logPath || path.join(ROOT, "scripts", "data", "mongolian_bichig_qa.json");
  fs.mkdirSync(path.dirname(outLog), { recursive: true });
  writeJsonPretty(outLog, report);

  console.log("Mongolian bichig + Poppe build complete:");
  for (const s of summaries) {
    console.log(
      `  ${s.course}: bichig ${s.withBichig}/${s.words}; poppe ${s.withPoppe}/${s.words}; guess uses=${s.guessSurfaceUses}; unique guesses=${s.uniqueGuesses}`,
    );
  }
  console.log(`  unique surfaces cached: ${cache.size}`);
  console.log(
    `  verified tokens: ${reviewSummary.verifiedTokens}/${reviewSummary.tokens} (${reviewSummary.verifiedTokenPct}%); unverified forms: ${reviewSummary.unverifiedForms}`,
  );
  console.log(`  unique guess-tier lemmas: ${uniqueGuesses.size}`);
  console.log(`  QA log: ${outLog}`);

  // Sample conversions for SHIP.md
  const samples = [
    "сансар",
    "Хүү",
    "харав",
    "Өглөө",
    "би",
    "цай",
    "уудаг",
    "од",
    "нар",
    "тэнгэр",
    "монгол",
  ];
  console.log("  samples (Cyrillic → bichig → poppe):");
  for (const w of samples) {
    const c = cache.get(w) || convertWord(w);
    console.log(
      `    ${w} → ${c?.bichig || "(none)"} → ${c?.poppe || "(none)"} [${c?.provenance || "?"}]`,
    );
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main();
}
