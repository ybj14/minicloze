#!/usr/bin/env python3
"""Build regressions on temporary corpora; requires Node and `npm ci`."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import build_static_web_data as build


ROOT = Path(__file__).resolve().parents[1]
COURSES = build.MONGOLIAN_COURSES


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def without_generated_fields(explanations: dict) -> dict:
    explanations = copy.deepcopy(explanations)
    for sentence in explanations["data"]:
        for word in sentence["words"]:
            word.pop("bichig", None)
            word.pop("poppe", None)
    return explanations


class MongolianBuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.corpora = self.root / "minicloze-lib" / "corpora"
        self.static = self.root / "minicloze-web" / "static" / "data"
        self.corpora.mkdir(parents=True)
        self.static.mkdir(parents=True)
        shutil.copytree(ROOT / "scripts", self.root / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copyfile(ROOT / "package.json", self.root / "package.json")
        # Exercise the real pinned converter in a fully isolated workspace.
        shutil.copytree(ROOT / "node_modules", self.root / "node_modules")
        for filename in build.SOURCE_FILES:
            write_json(self.corpora / filename, {"data": []})

        self.original = {}
        for index, course in enumerate(COURSES):
            explanations = {
                "revision": "new source 中文",
                "data": [{
                    "id": -100 - index,
                    "explanation": "Keep the newly edited explanation.",
                    "words": [
                        {"word": "нар", "meaning": "new source meaning", "bichig": "stale", "poppe": "stale"},
                        {"word": "тэнгэр", "notes": ["preserve me"]},
                        {"word": ".", "meaning": "punctuation", "bichig": "stale", "poppe": "stale"},
                    ],
                }],
            }
            self.original[course] = explanations
            source_path = self.corpora / f"{course}_explanations.json"
            static_path = self.static / source_path.name
            write_json(source_path, explanations)
            write_json(static_path, {"revision": "stale static", "data": [{"id": -999, "words": []}]})
            # Explicitly reproduce a source edit newer than its stale mirror.
            os.utime(static_path, (1, 1))
            os.utime(source_path, (2, 2))
            for directory in (self.corpora, self.static):
                write_json(directory / f"{course}_tokens.json", {"stale": []})
        self.base_files = {
            path: path.read_bytes()
            for course in COURSES
            for suffix in ("", "_vocab")
            for path in [self.corpora / f"{course}{suffix}.json"]
        }

    def run_command(self, *args: str, succeeds: bool = True) -> subprocess.CompletedProcess:
        result = subprocess.run(args, cwd=self.root, capture_output=True, text=True)
        if succeeds:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def assert_built(self, courses: list[str] = COURSES) -> None:
        for course in courses:
            with self.subTest(course=course):
                source = read_json(self.corpora / f"{course}_explanations.json")
                self.assertEqual(without_generated_fields(source), without_generated_fields(self.original[course]))
                self.assertEqual(source, read_json(self.static / f"{course}_explanations.json"))
                sentence = source["data"][0]
                words = sentence["words"]
                self.assertEqual(words[0]["bichig"], "ᠨᠠᠷᠠᠨ")
                self.assertEqual(words[0]["poppe"], "naran")
                self.assertEqual(words[1]["poppe"], "tngri")
                self.assertNotIn("bichig", words[2])
                self.assertNotIn("poppe", words[2])
                tokens = read_json(self.static / f"{course}_tokens.json")
                self.assertEqual(tokens, read_json(self.corpora / f"{course}_tokens.json"))
                self.assertEqual(tokens, {str(sentence["id"]): [
                    {"text": "нар ", "bichig": words[0]["bichig"], "poppe": words[0]["poppe"]},
                    {"text": "тэнгэр ", "bichig": words[1]["bichig"], "poppe": words[1]["poppe"]},
                    {"text": "."},
                ]})
        for path, original in self.base_files.items():
            self.assertEqual(path.read_bytes(), original)

    def test_npm_entry_uses_newer_source_instead_of_stale_static(self) -> None:
        self.run_command("npm", "run", "build:mongolian-bichig")
        self.assert_built()

    def test_direct_node_build_works_without_static_data(self) -> None:
        shutil.rmtree(self.static)
        self.run_command("node", "scripts/mongolian_bichig.mjs")
        self.assert_built()

    def test_single_course_and_custom_log_leave_other_course_untouched(self) -> None:
        other_files = [*self.corpora.glob(f"{COURSES[1]}*.json"), *self.static.glob(f"{COURSES[1]}*.json")]
        original = {path: path.read_bytes() for path in other_files}
        self.run_command("node", "scripts/mongolian_bichig.mjs", "--course", COURSES[0], "--log", "logs/qa.json")
        self.assert_built([COURSES[0]])
        for path, content in original.items():
            self.assertEqual(path.read_bytes(), content)
        self.assertEqual([row["course"] for row in read_json(self.root / "logs/qa.json")["courses"]], [COURSES[0]])

    def test_missing_source_does_not_fall_back_to_static(self) -> None:
        source = self.corpora / f"{COURSES[0]}_explanations.json"
        source.unlink()
        static = self.static / source.name
        before = static.read_bytes()
        result = self.run_command("node", "scripts/mongolian_bichig.mjs", "--course", COURSES[0], succeeds=False)
        self.assertIn("Missing explanations", result.stderr)
        self.assertFalse(source.exists())
        self.assertEqual(static.read_bytes(), before)

    def test_invalid_source_does_not_overwrite_either_copy(self) -> None:
        source = self.corpora / f"{COURSES[0]}_explanations.json"
        source.write_text("{invalid JSON", encoding="utf-8")
        static = self.static / source.name
        before = {path: path.read_bytes() for path in (source, static)}
        self.run_command("node", "scripts/mongolian_bichig.mjs", "--course", COURSES[0], succeeds=False)
        for path, content in before.items():
            self.assertEqual(path.read_bytes(), content)

    def test_mongolian_only_wrapper_preserves_source(self) -> None:
        self.run_command(sys.executable, "scripts/build_static_web_data.py", "--mongolian-only")
        self.assert_built()
        for path in self.base_files:
            self.assertEqual((self.static / path.name).read_bytes(), path.read_bytes())

    def test_full_build_regenerates_mongolian(self) -> None:
        spec = importlib.util.spec_from_file_location("fixture_build", self.root / "scripts/build_static_web_data.py")
        fixture_build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixture_build)
        # Other-language fixtures are empty; only stub the Tibetan constructor
        # so this regression suite does not require optional Python dependencies.
        with patch.object(fixture_build, "pyewts"):
            fixture_build.main()
        self.assert_built()
        self.assertEqual(
            [row["course"] for row in read_json(self.root / "scripts/data/mongolian_bichig_qa.json")["courses"]],
            COURSES,
        )

    def test_repeated_build_is_deterministic(self) -> None:
        self.run_command("node", "scripts/mongolian_bichig.mjs")
        files = [*self.corpora.glob("mongolian*.json"), *self.static.glob("mongolian*.json"), self.root / "scripts/data/mongolian_bichig_qa.json"]
        original = {path: path.read_bytes() for path in files}
        self.run_command("node", "scripts/mongolian_bichig.mjs")
        for path, content in original.items():
            self.assertEqual(path.read_bytes(), content)


if __name__ == "__main__":
    unittest.main()
