"""Validate words against the system spelling dictionary (wamerican)."""

import difflib
import sys

from settings import DICT_PATH

_dictionary: set[str] | None = None


def _load_dictionary() -> set[str]:
    global _dictionary
    if _dictionary is not None:
        return _dictionary

    if not DICT_PATH.is_file():
        print(
            f"⚠️ Warning: spelling dictionary not found at {DICT_PATH} "
            "(install wamerican on Ubuntu).",
            file=sys.stderr,
        )
        _dictionary = set()
        return _dictionary

    words: set[str] = set()
    with open(DICT_PATH, encoding="utf-8") as f:
        for line in f:
            word = line.strip()
            if word:
                words.add(word)
                words.add(word.lower())
    _dictionary = words
    return _dictionary


def check_words(*words: str) -> list[str]:
    """Return input words that are not in the system dictionary."""
    dictionary = _load_dictionary()
    if not dictionary:
        return []

    invalid: list[str] = []
    for word in words:
        candidate = word.strip()
        if not candidate:
            continue
        if candidate not in dictionary and candidate.lower() not in dictionary:
            invalid.append(candidate)
    return invalid


def suggest_spelling(word: str, n: int = 3) -> list[str]:
    """Return close dictionary matches for a misspelled word."""
    dictionary = _load_dictionary()
    if not dictionary:
        return []
    return difflib.get_close_matches(word, dictionary, n=n, cutoff=0.6)


def report_invalid_words(invalid: list[str]) -> None:
    for word in invalid:
        suggestions = suggest_spelling(word)
        if suggestions:
            print(
                f"❌ '{word}' is not in the dictionary. Did you mean: {', '.join(suggestions)}?",
                file=sys.stderr,
            )
        else:
            print(f"❌ '{word}' is not in the dictionary.", file=sys.stderr)
