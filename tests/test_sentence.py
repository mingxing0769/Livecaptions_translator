import unittest

from live_translator.sentence import split_english_sentences


class SentenceSplitTests(unittest.TestCase):
    def test_basic_sentence_marks(self):
        self.assertEqual(
            split_english_sentences("Hello world. Are you ready? Go!"),
            ["Hello world.", "Are you ready?", "Go!"],
        )

    def test_decimal_numbers_are_not_split(self):
        self.assertEqual(
            split_english_sentences("The gap is 1.23 seconds. Verstappen leads"),
            ["The gap is 1.23 seconds.", "Verstappen leads"],
        )

    def test_common_abbreviations_are_not_split(self):
        self.assertEqual(
            split_english_sentences("Dr. Smith talks to the U.S. team. They agree."),
            ["Dr. Smith talks to the U.S. team.", "They agree."],
        )


if __name__ == "__main__":
    unittest.main()

