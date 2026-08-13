"""
Reusable Glickcrypt conversion helpers.

Copyright (C) 2025 Ayrik Nabirahni. This file
is apart of the Glick project, and licensed under
the GNU AGPL-3.0-or-later. See LICENSE and README for more details.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

try:
    import enchant
except ImportError:  # pragma: no cover - exercised in minimal environments
    enchant = None

from files.vars import else_punc, end_punc, full_stop_punc, nums, punctuation, vowels


DECRYPTION_FAILURE = "|decryption_failure|"


class Dictionary(Protocol):
    def check(self, word: str) -> bool:
        ...


class DecryptionUnavailable(RuntimeError):
    """Raised when the English dictionary dependency is not ready."""


@dataclass(frozen=True)
class ConversionResult:
    mode: str
    text: str
    result: str
    steps: tuple[str, ...] = ()


_dictionary: Dictionary | None = None


def _get_dictionary() -> Dictionary:
    global _dictionary

    if _dictionary is not None:
        return _dictionary

    if enchant is None:
        raise DecryptionUnavailable("PyEnchant is not installed.")

    try:
        _dictionary = enchant.Dict("en_US")
    except Exception as exc:  # pragma: no cover - depends on host dictionary
        raise DecryptionUnavailable("The en_US dictionary is not available.") from exc

    return _dictionary


def _move_tokens(tokens: list[str], move_chars: list[str], remove_chars: list[str]) -> list[str]:
    body: list[str] = []
    trailing: list[str] = []

    for token in tokens:
        if token in move_chars:
            trailing.append(token)
        elif token in remove_chars:
            continue
        else:
            body.append(token)

    return body + trailing


def _capitalize_sentence_words(words: list[str]) -> list[str]:
    if not words:
        return words

    capitalized = words[:]
    capitalized[0] = capitalized[0].capitalize()

    for index in range(1, len(capitalized)):
        if any(char in full_stop_punc for char in capitalized[index - 1]):
            capitalized[index] = capitalized[index].capitalize()

    return capitalized


def encrypt_word(word: str) -> str:
    if not word:
        return word

    chars = list(word)
    if any(char in nums for char in chars):
        return word

    consonants: list[str] = []
    for char in chars:
        if char in vowels:
            break
        consonants.append(char)

    if consonants:
        converted = chars[len(consonants) :] + consonants + ["ay"]
        converted = _move_tokens(converted, end_punc, else_punc)
    else:
        converted = chars + ["yay"]
        converted = _move_tokens(converted, punctuation, [])

    return "".join(token.lower() for token in converted)


def encrypt_text(text: str) -> str:
    words = text.split()
    converted = [encrypt_word(word) for word in words]
    return " ".join(_capitalize_sentence_words(converted))


def _encrypt_with_steps(text: str) -> ConversionResult:
    words = text.split()
    converted = [encrypt_word(word) for word in words]
    result = " ".join(_capitalize_sentence_words(converted))
    steps = _build_trace_steps("encrypt", words, converted, result)
    return ConversionResult(mode="encrypt", text=text, result=result, steps=tuple(steps))


def _filter_decryption_punctuation(chars: list[str]) -> tuple[list[str], list[str]]:
    body: list[str] = []
    trailing: list[str] = []

    for char in chars:
        if char in end_punc:
            trailing.append(char)
        elif char in else_punc:
            continue
        else:
            body.append(char)

    return body, trailing


def decrypt_word(word: str, dictionary: Dictionary | None = None) -> str:
    if not word:
        return word

    if any(char in nums for char in word):
        return word

    chars, punctuation_chars = _filter_decryption_punctuation([char.lower() for char in word])

    if len(chars) < 3 or chars[-2:] != ["a", "y"]:
        return DECRYPTION_FAILURE

    core = chars[:-2]
    if core and core[-1] == "y":
        return "".join(core[:-1] + punctuation_chars)

    dictionary = dictionary or _get_dictionary()

    for end_consonants in range(1, 5):
        split_at = len(core) - end_consonants
        if split_at < 0:
            break

        candidate_chars = core[split_at:] + core[:split_at]
        candidate = "".join(candidate_chars)
        if dictionary.check(candidate):
            return "".join(candidate_chars + punctuation_chars)

    return DECRYPTION_FAILURE


def decrypt_text(text: str, dictionary: Dictionary | None = None) -> str:
    words = text.split()
    converted = [decrypt_word(word, dictionary) for word in words]
    return " ".join(_capitalize_sentence_words(converted))


def _decrypt_with_steps(text: str) -> ConversionResult:
    words = text.split()
    dictionary = _get_dictionary() if words else None
    converted = [decrypt_word(word, dictionary) for word in words]
    result = " ".join(_capitalize_sentence_words(converted))
    steps = _build_trace_steps("decrypt", words, converted, result)
    return ConversionResult(mode="decrypt", text=text, result=result, steps=tuple(steps))


def _build_trace_steps(mode: str, words: list[str], converted: list[str], result: str) -> list[str]:
    steps = [
        f"mode: {mode}",
        f"tokens: {len(words)}",
    ]

    if not words:
        steps.append("input: empty")
        steps.append("result: empty")
        return steps

    for index, (source, output) in enumerate(zip(words, converted), start=1):
        if output == source:
            steps.append(f"{index:02d}: pass {source}")
        elif output == DECRYPTION_FAILURE:
            steps.append(f"{index:02d}: fail {source}")
        else:
            steps.append(f"{index:02d}: {source} -> {output}")

    steps.append(f"result: {result}")
    return steps


def convert_text(mode: str, text: str) -> ConversionResult:
    normalized_mode = mode.strip().lower()

    if normalized_mode == "encrypt":
        return _encrypt_with_steps(text)
    elif normalized_mode == "decrypt":
        return _decrypt_with_steps(text)
    else:
        raise ValueError("Mode must be either 'encrypt' or 'decrypt'.")
