import json
import unittest

from demo import EARLIER, LATER, ROOT, capture, recall


class RecallTest(unittest.TestCase):
    def setUp(self):
        self.earlier = capture(EARLIER)

    def test_resume_recovers_decision_and_test_with_exact_citation(self):
        question = capture(LATER)[0].prompt
        found = recall(self.earlier, question)
        self.assertEqual(found.message_id, "message-retry")
        self.assertIn("I've decided the queue will reuse the original print job ID", found.prompt)
        self.assertIn("original print job ID", found.outcome)
        self.assertIn("replay produces exactly one label", found.outcome)
        record = (ROOT / found.path).read_text().splitlines()[found.final_line - 1]
        self.assertEqual(json.loads(record)["payload"]["content"][0]["text"], found.outcome)

    def test_another_question_recovers_a_different_turn(self):
        self.assertEqual(recall(self.earlier, "Where should the fold mark go?").message_id,
                         "message-border")

    def test_commentary_and_followup_stay_out_of_search(self):
        self.assertEqual(len(self.earlier), 3)
        for query in ["clock", "comparing", "changing", "dispenser", "astronomy", "and why?"]:
            with self.subTest(query=query):
                self.assertIsNone(recall(self.earlier, query))


if __name__ == "__main__":
    unittest.main()
