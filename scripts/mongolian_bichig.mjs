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
  return { bichig: row.bichig, poppe: row.poppe, provenance: "reviewed-override", confidence: 1 };
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

function loadJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJsonCompact(filePath, value) {
  fs.writeFileSync(filePath, JSON.stringify(value, null, 0), "utf8");
}

function writeJsonPretty(filePath, value) {
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function processCourse(course, cache, guessLog) {
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
  const summaries = [];

  for (const course of courses) {
    summaries.push(processCourse(course, cache, guessLog));
  }

  // Unique lemma guess list across courses
  const uniqueGuesses = new Map();
  for (const g of guessLog) {
    if (!uniqueGuesses.has(g.word)) {
      uniqueGuesses.set(g.word, g);
    }
  }

  const report = {
    converter: "@gege-mn/gege-converter",
    poppeSource:
      "normalizePoppe(candidate.classical) — FVS digits/dots stripped, kh→k, front-harmony q/γ→k/g; reviewed overrides from scripts/data/mongolian_bichig_overrides.json; fallback fromScript(bichig). NOT expert-reviewed beyond the override rows.",
    overridesApplied: OVERRIDES.size,
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
