import unittest

from live_translator.caption_tracker import CaptionTracker


class CaptionTrackerTests(unittest.TestCase):
    def test_first_run_adds_recent_complete_sentence_and_live_tail(self):
        tracker = CaptionTracker()
        update = tracker.process("One sentence. Two is still live")
        self.assertEqual(update.complete_sentences, ["One sentence."])
        self.assertEqual(update.live_sentence, "Two is still live")
        self.assertEqual(update.action, "first_run")

    def test_repeated_text_is_ignored(self):
        tracker = CaptionTracker()
        tracker.process("One sentence. Two is live")
        update = tracker.process("One sentence. Two is live")
        self.assertEqual(update.complete_sentences, [])
        self.assertEqual(update.live_sentence, "")
        self.assertEqual(update.action, "no_change")

    def test_normal_anchor_flow_finds_new_complete_sentence(self):
        tracker = CaptionTracker()
        tracker.process("One sentence. Two is live")
        update = tracker.process("One sentence. Two is complete. Three is live")
        self.assertEqual(update.complete_sentences, ["Two is complete."])
        self.assertEqual(update.live_sentence, "Three is live")
        self.assertEqual(update.action, "normal")

    def test_major_jump_resets_state(self):
        tracker = CaptionTracker()
        tracker.process("Alpha done. Beta live")
        update = tracker.process("Completely different. New live")
        self.assertEqual(update.complete_sentences, ["Completely different."])
        self.assertEqual(update.live_sentence, "")
        self.assertEqual(update.action, "reset")

    def test_last_preview_word_is_removed_when_fragment_has_no_trailing_space(self):
        tracker = CaptionTracker()
        tracker.process("First done. Second fragment")
        self.assertEqual(tracker.anchor_history[-1]["next_preview"], ["second"])


if __name__ == "__main__":
    unittest.main()

