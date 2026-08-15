import unittest

from glickcrypt import DECRYPTION_FAILURE, convert_text, decrypt_text, decrypt_word, encrypt_text


class FakeDictionary:
    def __init__(self, words):
        self.words = set(words)

    def check(self, word):
        return word in self.words


class GlickcryptTests(unittest.TestCase):
    def test_encrypt_text_moves_consonants(self):
        self.assertEqual(encrypt_text("Hello, world!"), "Ellohay, orldway!")

    def test_encrypt_text_moves_vowel_words(self):
        self.assertEqual(encrypt_text("Apple."), "Appleyay.")

    def test_encrypt_text_expands_numbers_before_pig_latin(self):
        self.assertEqual(encrypt_text("300"), "Eethray undredhay")
        self.assertEqual(
            encrypt_text("I have 300 apples."),
            "Iyay avehay eethray undredhay applesyay.",
        )

    def test_decrypt_word_uses_dictionary_for_consonants(self):
        dictionary = FakeDictionary({"hello"})
        self.assertEqual(decrypt_word("ellohay,", dictionary), "hello,")

    def test_decrypt_text_handles_vowel_words_without_dictionary(self):
        self.assertEqual(decrypt_text("appleyay."), "Apple.")

    def test_decrypt_text_collapses_number_words_to_digits(self):
        dictionary = FakeDictionary({"three", "hundred"})
        self.assertEqual(decrypt_text("eethray undredhay.", dictionary), "300.")

    def test_decrypt_word_returns_failure_for_invalid_ciphertext(self):
        dictionary = FakeDictionary({"hello"})
        self.assertEqual(decrypt_word("plain", dictionary), DECRYPTION_FAILURE)

    def test_convert_text_includes_process_steps(self):
        result = convert_text("encrypt", "Hello")
        self.assertEqual(result.result, "Ellohay")
        self.assertIn("mode: encrypt", result.steps)
        self.assertIn("01: Hello -> ellohay", result.steps)

    def test_convert_text_traces_number_expansion(self):
        result = convert_text("encrypt", "300")
        self.assertEqual(result.result, "Eethray undredhay")
        self.assertIn(
            "01: number 300 -> three hundred -> eethray undredhay",
            result.steps,
        )


if __name__ == "__main__":
    unittest.main()
