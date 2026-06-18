import { readFileSync } from "node:fs";
import { get_phonetics } from "tibetan-ewts-converter";

const input = JSON.parse(readFileSync(0, "utf8"));
const phonetics = get_phonetics({ style: "thl", lang: "en" });

const output = input.map((text) =>
  phonetics.phonetics(String(text || ""), { autosplit: true }).trim(),
);

process.stdout.write(JSON.stringify(output));
