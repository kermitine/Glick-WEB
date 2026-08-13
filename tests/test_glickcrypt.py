import unittest

from glickcrypt import DECRYPTION_FAILURE, decrypt_text, decrypt_word, encrypt_text


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

    def test_decrypt_word_uses_dictionary_for_consonants(self):
        dictionary = FakeDictionary({"hello"})
        self.assertEqual(decrypt_word("ellohay,", dictionary), "hello,")

    def test_decrypt_text_handles_vowel_words_without_dictionary(self):
        self.assertEqual(decrypt_text("appleyay."), "Apple.")

    def test_decrypt_word_returns_failure_for_invalid_ciphertext(self):
        dictionary = FakeDictionary({"hello"})
        self.assertEqual(decrypt_word("plain", dictionary), DECRYPTION_FAILURE)


if __name__ == "__main__":
    unittest.main()
