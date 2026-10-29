// Regression checks for the Mongolian bichig + Poppe build.
// Run: node --test scripts/test_mongolian_poppe.mjs
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { normalizePoppe } from "./mongolian_bichig.mjs";

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
