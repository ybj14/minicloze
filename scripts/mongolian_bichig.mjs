#!/usr/bin/env node
/**
 * Build-time Cyrillic → Traditional Mongolian (Hudum / Mongol bichig) converter.
 *
 * Uses @gege-mn/gege-converter. Enrich explanations with `bichig`, emit
 * mongolian_*_tokens.json, and log guess-tier lemmas for QA.
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

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const STATIC_DATA = path.join(ROOT, "minicloze-web", "static", "data");
const CORPORA = path.join(ROOT, "minicloze-lib", "corpora");

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
 * Top-1 conversion for a single surface form.
 * Returns { bichig, provenance, confidence } or null if empty/punct.
 */
function convertWord(raw) {
  const text = String(raw || "").trim();
  if (!text || PUNCT_RE.test(text)) {
    return null;
  }

  let provenance = "unknown";
  let confidence = null;
  try {
    const parts = analyze(text);
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
  }

  let bichig = "";
  try {
    bichig = convert(text) || "";
  } catch {
    bichig = "";
    provenance = "error";
  }

  if (!bichig.trim()) {
    return null;
  }

  return { bichig, provenance, confidence };
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
  let guessCount = 0;

  for (const sentence of explanations.data || []) {
    const words = sentence.words || [];
    const tokens = [];

    for (let index = 0; index < words.length; index++) {
      const word = words[index];
      const surface = word.word || "";
      wordCount += 1;

      let cached = cache.get(surface);
      if (cached === undefined) {
        cached = convertWord(surface);
        cache.set(surface, cached);
        if (cached && cached.provenance === "guess") {
          guessLog.push({
            course,
            word: surface,
            bichig: cached.bichig,
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

      let text = surface;
      if (index + 1 < words.length) {
        text = `${text} `;
      }
      const token = { text };
      if (cached?.bichig) {
        token.bichig = cached.bichig;
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

  console.log("Mongolian bichig build complete:");
  for (const s of summaries) {
    console.log(
      `  ${s.course}: ${s.withBichig}/${s.words} words with bichig; guess uses=${s.guessSurfaceUses}; unique guesses=${s.uniqueGuesses}`,
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
  ];
  console.log("  samples:");
  for (const w of samples) {
    const c = cache.get(w) || convertWord(w);
    console.log(`    ${w} → ${c?.bichig || "(none)"} [${c?.provenance || "?"}]`);
  }
}

main();
