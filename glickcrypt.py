"""
Reusable Glickcrypt conversion helpers.

Copyright (C) 2025 Ayrik Nabirahni. This file
is apart of the Glick project, and licensed under
the GNU AGPL-3.0-or-later. See LICENSE and README for more details.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Protocol

try:
    import enchant
except ImportError:  # pragma: no cover - exercised in minimal environments
    enchant = None

from files.vars import else_punc, end_punc, full_stop_punc, nums, punctuation, vowels


DECRYPTION_FAILURE = "|decryption_failure|"
MAX_SUPPORTED_NUMBER = 999_999_999_999

_INTEGER_TOKEN_RE = re.compile(r"^[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)$")

_SMALL_NUMBER_WORDS = {
    0: "zero",
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
    11: "eleven",
    12: "twelve",
    13: "thirteen",
    14: "fourteen",
    15: "fifteen",
    16: "sixteen",
    17: "seventeen",
    18: "eighteen",
    19: "nineteen",
}
_TENS_NUMBER_WORDS = {
    20: "twenty",
    30: "thirty",
    40: "forty",
    50: "fifty",
    60: "sixty",
    70: "seventy",
    80: "eighty",
    90: "ninety",
}
_SCALE_NUMBER_WORDS = (
    (1_000_000_000, "billion"),
    (1_000_000, "million"),
    (1_000, "thousand"),
)
_WORD_TO_SMALL_NUMBER = {word: value for value, word in _SMALL_NUMBER_WORDS.items()}
_WORD_TO_TENS_NUMBER = {word: value for value, word in _TENS_NUMBER_WORDS.items()}
_WORD_TO_SCALE_NUMBER = {word: value for value, word in _SCALE_NUMBER_WORDS}
_NUMBER_WORDS = (
    set(_WORD_TO_SMALL_NUMBER)
    | set(_WORD_TO_TENS_NUMBER)
    | set(_WORD_TO_SCALE_NUMBER)
    | {"hundred", "negative", "and"}
)


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


def _under_thousand_to_words(number: int) -> list[str]:
    if number < 20:
        return [_SMALL_NUMBER_WORDS[number]]

    if number < 100:
        tens, remainder = divmod(number, 10)
        words = [_TENS_NUMBER_WORDS[tens * 10]]
        if remainder:
            words.extend(_under_thousand_to_words(remainder))
        return words

    hundreds, remainder = divmod(number, 100)
    words = [_SMALL_NUMBER_WORDS[hundreds], "hundred"]
    if remainder:
        words.extend(_under_thousand_to_words(remainder))
    return words


def _integer_to_words(number: int) -> list[str]:
    if number < 0:
        return ["negative", *_integer_to_words(abs(number))]

    if number == 0:
        return [_SMALL_NUMBER_WORDS[0]]

    words: list[str] = []
    remainder = number

    for scale, scale_word in _SCALE_NUMBER_WORDS:
        chunk, remainder = divmod(remainder, scale)
        if chunk:
            words.extend(_under_thousand_to_words(chunk))
            words.append(scale_word)

    if remainder:
        words.extend(_under_thousand_to_words(remainder))

    return words


def _split_numeric_token(token: str) -> tuple[str, str] | None:
    for suffix_length in range(len(token) + 1):
        body = token[: len(token) - suffix_length]
        suffix = token[len(token) - suffix_length :]

        if not body:
            continue
        if suffix and any(char not in end_punc for char in suffix):
            continue
        if _INTEGER_TOKEN_RE.fullmatch(body):
            return body, suffix

    return None


def _number_token_to_words(token: str) -> list[str] | None:
    split_token = _split_numeric_token(token)
    if split_token is None:
        return None

    number_text, suffix = split_token
    number = int(number_text.replace(",", ""))

    if abs(number) > MAX_SUPPORTED_NUMBER:
        return None

    words = _integer_to_words(number)
    if suffix:
        words[-1] += suffix

    return words


def _strip_end_punctuation(word: str) -> tuple[str, str]:
    body = word
    suffix = ""

    while body and body[-1] in end_punc:
        suffix = body[-1] + suffix
        body = body[:-1]

    return body, suffix


def _parse_under_thousand_words(words: list[str], start: int) -> tuple[int, int] | None:
    index = start
    value = 0

    if (
        index + 1 < len(words)
        and words[index] in _WORD_TO_SMALL_NUMBER
        and 1 <= _WORD_TO_SMALL_NUMBER[words[index]] <= 9
        and words[index + 1] == "hundred"
    ):
        value += _WORD_TO_SMALL_NUMBER[words[index]] * 100
        index += 2
        if index < len(words) and words[index] == "and":
            index += 1

    if index < len(words):
        if words[index] in _WORD_TO_SMALL_NUMBER:
            value += _WORD_TO_SMALL_NUMBER[words[index]]
            index += 1
        elif words[index] in _WORD_TO_TENS_NUMBER:
            value += _WORD_TO_TENS_NUMBER[words[index]]
            index += 1
            if (
                index < len(words)
                and words[index] in _WORD_TO_SMALL_NUMBER
                and 1 <= _WORD_TO_SMALL_NUMBER[words[index]] <= 9
            ):
                value += _WORD_TO_SMALL_NUMBER[words[index]]
                index += 1

    if index == start:
        return None

    return value, index


def _parse_number_words(words: list[str]) -> int | None:
    if not words:
        return None

    sign = 1
    index = 0
    if words[index] == "negative":
        sign = -1
        index += 1

    if index >= len(words):
        return None

    if words[index:] == ["zero"]:
        return 0

    total = 0
    previous_scale = float("inf")

    while index < len(words):
        if total and words[index] == "and":
            index += 1

        parsed_chunk = _parse_under_thousand_words(words, index)
        if parsed_chunk is None:
            return None

        chunk, index = parsed_chunk

        if index < len(words) and words[index] in _WORD_TO_SCALE_NUMBER:
            scale = _WORD_TO_SCALE_NUMBER[words[index]]
            if scale >= previous_scale:
                return None
            total += chunk * scale
            previous_scale = scale
            index += 1
        elif index == len(words):
            total += chunk
        else:
            return None

    return sign * total


def _parse_number_phrase(words: list[str], start: int) -> tuple[str, int] | None:
    candidate_words: list[str] = []
    punctuation_suffix = ""

    for index in range(start, len(words)):
        body, suffix = _strip_end_punctuation(words[index])
        normalized = body.lower()

        if normalized not in _NUMBER_WORDS:
            break

        candidate_words.append(normalized)
        if suffix:
            punctuation_suffix = suffix
            break

    for length in range(len(candidate_words), 0, -1):
        value = _parse_number_words(candidate_words[:length])
        if value is not None:
            suffix = punctuation_suffix if length == len(candidate_words) else ""
            return f"{value}{suffix}", length

    return None


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


def _encrypt_token(token: str) -> tuple[list[str], str]:
    number_words = _number_token_to_words(token)
    if number_words is not None:
        converted_words = [encrypt_word(word) for word in number_words]
        return (
            converted_words,
            f"number {token} -> {' '.join(number_words)} -> {' '.join(converted_words)}",
        )

    converted = encrypt_word(token)
    return [converted], _build_token_trace(token, converted)


def encrypt_text(text: str) -> str:
    tokens = text.split()
    converted = [word for token in tokens for word in _encrypt_token(token)[0]]
    return " ".join(_capitalize_sentence_words(converted))


def _encrypt_with_steps(text: str) -> ConversionResult:
    tokens = text.split()
    conversions = [_encrypt_token(token) for token in tokens]
    converted = [word for converted_words, _trace in conversions for word in converted_words]
    result = " ".join(_capitalize_sentence_words(converted))
    steps = _build_trace_steps(
        "encrypt",
        len(tokens),
        [trace for _converted_words, trace in conversions],
        result,
    )
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
    converted = _collapse_number_phrases(words, converted)[0]
    return " ".join(_capitalize_sentence_words(converted))


def _decrypt_with_steps(text: str) -> ConversionResult:
    words = text.split()
    dictionary = _get_dictionary() if words else None
    converted = [decrypt_word(word, dictionary) for word in words]
    converted, trace_lines = _collapse_number_phrases(words, converted)
    result = " ".join(_capitalize_sentence_words(converted))
    steps = _build_trace_steps("decrypt", len(words), trace_lines, result)
    return ConversionResult(mode="decrypt", text=text, result=result, steps=tuple(steps))


def _build_token_trace(source: str, output: str) -> str:
    if output == source:
        return f"pass {source}"
    if output == DECRYPTION_FAILURE:
        return f"fail {source}"
    return f"{source} -> {output}"


def _collapse_number_phrases(
    source_words: list[str], converted_words: list[str]
) -> tuple[list[str], list[str]]:
    collapsed: list[str] = []
    trace_lines: list[str] = []
    index = 0

    while index < len(converted_words):
        parsed_number = _parse_number_phrase(converted_words, index)
        if parsed_number is not None:
            number_text, consumed = parsed_number
            source_phrase = " ".join(source_words[index : index + consumed])
            converted_phrase = " ".join(converted_words[index : index + consumed])
            collapsed.append(number_text)
            trace_lines.append(f"number {source_phrase} -> {converted_phrase} -> {number_text}")
            index += consumed
            continue

        output = converted_words[index]
        collapsed.append(output)
        trace_lines.append(_build_token_trace(source_words[index], output))
        index += 1

    return collapsed, trace_lines


def _build_trace_steps(
    mode: str, token_count: int, trace_lines: list[str], result: str
) -> list[str]:
    steps = [
        f"mode: {mode}",
        f"tokens: {token_count}",
    ]

    if not trace_lines:
        steps.append("input: empty")
        steps.append("result: empty")
        return steps

    for index, trace_line in enumerate(trace_lines, start=1):
        steps.append(f"{index:02d}: {trace_line}")

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
