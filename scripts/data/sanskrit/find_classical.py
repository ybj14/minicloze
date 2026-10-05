#!/usr/bin/env python3
"""Print short GRETIL clauses that attest each candidate lemma.

Usage: find_classical.py VOCAB_FILE [START END] [N]
VOCAB_FILE lines: lemma|gloss|pattern1|pattern2...  (patterns are IAST word-start
substrings). Output ids ``code@LINE.SEG`` are accepted as ``## keys`` by
build_sanskrit_batches.py, which re-resolves them and stores the clause text.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import build_sanskrit_batches as b  # noqa: E402

WEIGHT = {"hit": 0, "pt": 1, "vet": 2, "bhartr": 3, "ram": 3, "bhg": 4, "manu": 5}


def main() -> None:
    vocab = [line.rstrip("\n").split("|") for line in open(sys.argv[1], encoding="utf-8") if line.strip()]
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    end = int(sys.argv[3]) if len(sys.argv) > 3 else len(vocab)
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    index = b.CorpusIndex()
    segs = []
    for code, lines in index.files.items():
        for i, line in enumerate(lines):
            loc = index.locations[code][i]
            if code == "bhg" and not loc.startswith("verse bhg_"):
                continue
            for k, seg in enumerate(b.split_segments(line), 1):
                if 18 <= len(seg) <= 90:
                    segs.append((WEIGHT[code], code, i + 1, k, seg))
    for num, row in enumerate(vocab[start - 1:end], start):
        lemma, gloss, pats = row[0], row[1], [p for p in row[2:] if p]
        rx = re.compile(r"(?:^|[\s\-'])(?:" + "|".join(re.escape(p.strip()) for p in pats) + ")")
        hits = [s for s in segs if rx.search(" " + s[4] + " ")]
        hits.sort(key=lambda s: (s[0], abs(len(s[4]) - 45)))
        chosen, used = [], set()
        for h in hits:
            if (h[1], h[2]) in used:
                continue
            used.add((h[1], h[2]))
            chosen.append(h)
            if len(chosen) >= n:
                break
        print(f"#{num} {lemma} | {gloss} [{len(hits)}]")
        for h in chosen:
            print(f"  {h[1]}@{h[2]}.{h[3]} {h[4]}")


if __name__ == "__main__":
    main()
