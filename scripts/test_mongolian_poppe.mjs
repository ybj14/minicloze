// Regression checks for the Mongolian bichig + Poppe build.
// Run: node --test scripts/test_mongolian_poppe.mjs
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { normalizePoppe, toPoppe, dictionaryMatches } from "./mongolian_bichig.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const COURSES = ["mongolian_a1", "mongolian_swadesh"];
const load = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, p), "utf8"));
const overrides = load("scripts/data/mongolian_bichig_overrides.json").overrides;

function* words() {
  for (const course of COURSES) {
    for (const sentence of load(`minicloze-web/static/data/${course}_explanations.json`).data) {
      for (const w of sentence.words) yield { course, sentence, w };
    }
  }
}

test("normalizePoppe strips encoding artefacts and fixes front-harmony q/γ", () => {
  assert.equal(normalizePoppe("mašin1"), "mašin");
  assert.equal(normalizePoppe("khino1"), "kino");
  assert.equal(normalizePoppe("deγer-e"), "deger-e");
  assert.equal(normalizePoppe("qeüqed"), "keüked");
  assert.equal(normalizePoppe("üγei"), "ügei");
  // back-vowel words and reviewed lexicon readings are left alone
  assert.equal(normalizePoppe("γarqu"), "γarqu");
  assert.equal(normalizePoppe("salkin"), "salkin");
});

test("Poppe has no FVS digits, letter dots or kh digraph", () => {
  for (const { w } of words()) {
    assert.doesNotMatch(w.poppe, /\p{L}[1-4]|\p{L}\.\p{L}|kh/u, `${w.word} → ${w.poppe}`);
  }
});

test("front-vowel words never romanize ᠬ/ᠭ as q/γ", () => {
  for (const { w } of words()) {
    for (const chunk of w.poppe.split(" ")) {
      if (/[eöüē]/.test(chunk) && !/[aou]/.test(chunk)) {
        assert.doesNotMatch(chunk, /[qγ]/, `${w.word} → ${w.poppe}`);
      }
    }
  }
});

test("bichig uses MVS, never NNBSP, as the suffix connector", () => {
  for (const { w } of words()) assert.ok(!w.bichig.includes("\u202f"), w.word);
});

test("reviewed overrides are applied", () => {
  const byKey = new Map(overrides.map((r) => [r.cyrillic, r]));
  let hits = 0;
  for (const { sentence, w } of words()) {
    const row = byKey.get(w.word.toLowerCase());
    if (!row) continue;
    if ((row.except_sentence_ids || []).includes(String(sentence.id))) continue;
    if (row.when_gloss && !new RegExp(row.when_gloss, "i").test(w.gloss || "")) continue;
    assert.equal(w.bichig, row.bichig, w.word);
    assert.equal(w.poppe, row.poppe, w.word);
    hits += 1;
  }
  assert.ok(hits > 300, `expected >300 overridden tokens, got ${hits}`);
});

test("tokens mirror explanations", () => {
  for (const course of COURSES) {
    const tokens = load(`minicloze-web/static/data/${course}_tokens.json`);
    for (const s of load(`minicloze-web/static/data/${course}_explanations.json`).data) {
      const t = tokens[String(s.id)];
      assert.equal(t.length, s.words.length);
      s.words.forEach((w, i) => {
        assert.equal(t[i].bichig, w.bichig);
        assert.equal(t[i].poppe, w.poppe);
      });
    }
  }
});

// ---- review status ("verified" marker) -------------------------------------

const flags = load("scripts/data/mongolian_review_flags.json");
const queue = load("scripts/data/mongolian_review_queue.json");
const verifiedList = load("scripts/data/mongolian_verified_words.json");

test("toPoppe transliterates bichig by vowel harmony", () => {
  assert.equal(toPoppe("ᠳᠡᠭᠡᠷ\u180eᠡ"), "deger-e");
  assert.equal(toPoppe("ᠬᠡᠦᠬᠡᠳ"), "keüked");
  assert.equal(toPoppe("ᠭᠠᠷᠬᠤ"), "γarqu");
  assert.equal(toPoppe("ᠮᠠᠱᠢᠨ\u180b"), "mašin");
});

test("every Mongolian word and token carries a boolean verified marker", () => {
  for (const { w } of words()) {
    assert.equal(typeof w.verified, "boolean", w.word);
    if (w.verified) {
      assert.ok(w.verified_by && !w.review, `${w.word}: verified needs verified_by`);
    } else {
      assert.ok(w.review && !w.verified_by, `${w.word}: unverified needs review reasons`);
      for (const code of w.review.split(" ")) assert.ok(flags.reasons[code], code);
    }
  }
  for (const course of COURSES) {
    const tokens = load(`minicloze-web/static/data/${course}_tokens.json`);
    for (const s of load(`minicloze-web/static/data/${course}_explanations.json`).data) {
      s.words.forEach((w, i) => assert.equal(tokens[String(s.id)][i].verified, w.verified));
    }
  }
});

test("verified means sourced override, or dictionary match + rule-consistent Poppe", () => {
  for (const { w } of words()) {
    if (!w.verified) continue;
    if (w.verified_by.startsWith("sourced override")) continue;
    assert.ok(dictionaryMatches(w.word, w.bichig).length > 0, `${w.word} has no dictionary match`);
    assert.equal(w.poppe, toPoppe(w.bichig), `${w.word} Poppe not derivable from bichig`);
  }
});

test("known-unresolved categories are flagged unverified", () => {
  const homographs = new Set(flags.homographs.map((r) => r.cyrillic));
  const pastRe = new RegExp(flags.past_laa.surface_regex, "iu");
  const pastExclude = new RegExp(flags.past_laa.exclude_gloss_regex, "iu");
  const seen = { "past-laa": 0, "tai-detached": 0, "du-ban": 0, homograph: 0, "gloss-error": 0 };
  for (const { sentence, w } of words()) {
    if (w.verified_by?.startsWith("sourced override")) continue;
    const lower = w.word.toLowerCase();
    const expect = (code, cond) => {
      if (!cond) return;
      seen[code] += 1;
      assert.equal(w.verified, false, `${w.word} (${code}) must be unverified`);
      assert.match(w.review, new RegExp(`(^| )${code}( |$)`), `${w.word} missing ${code}`);
    };
    expect("past-laa", pastRe.test(lower) && !pastExclude.test(w.gloss || ""));
    expect("tai-detached", /(тай|тэй|той|төй)$/u.test(lower) && /-t[ae]i(\s|$)/u.test(w.poppe));
    expect("du-ban", /-(du|tu|dü|tü)-(ban|ben)\b/u.test(w.poppe));
    expect("homograph", homographs.has(lower));
    expect("gloss-error", lower === "хүнд" && String(sentence.id) === "-100859");
  }
  for (const [code, n] of Object.entries(seen)) assert.ok(n > 0, `no ${code} tokens seen`);
  // the -100859 хүнд token keeps its (sentence-correct) dative reading
  const s = load("minicloze-web/static/data/mongolian_a1_explanations.json").data.find(
    (x) => String(x.id) === "-100859",
  );
  const w = s.words.find((x) => x.word.toLowerCase() === "хүнд");
  assert.equal(w.bichig, "ᠬᠦᠮᠦᠨ\u180eᠳᠦ");
  assert.equal(w.verified, false);
});

test("guess-tier forms without a dictionary match are unverified", () => {
  const guess = new Set(load("scripts/data/mongolian_bichig_qa.json").guessTierUnique.map((g) => g.word));
  let n = 0;
  for (const { w } of words()) {
    if (!guess.has(w.word) || w.verified_by?.startsWith("sourced override")) continue;
    if (dictionaryMatches(w.word, w.bichig).length) continue;
    assert.equal(w.verified, false, w.word);
    n += 1;
  }
  assert.ok(n > 100, `expected >100 guess-tier tokens, got ${n}`);
});

test("review queue and verified list agree with the data", () => {
  let total = 0;
  let unverified = 0;
  for (const { w } of words()) {
    total += 1;
    if (!w.verified) unverified += 1;
  }
  assert.equal(queue.summary.tokens, total);
  assert.equal(queue.summary.unverifiedTokens, unverified);
  assert.equal(queue.queue.reduce((a, r) => a + r.tokens, 0), unverified);
  assert.equal(verifiedList.verified.reduce((a, r) => a + r.tokens, 0), total - unverified);
  for (let i = 1; i < queue.queue.length; i++) {
    assert.ok(queue.queue[i - 1].tokens >= queue.queue[i].tokens, "queue not ranked by frequency");
  }
  assert.ok(queue.summary.verifiedTokenPct < 100);
});
