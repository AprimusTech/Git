"""Offline tests for the AI reply engine; no API or WhatsApp connection."""
import unittest
from ai_engine import build_prompt


class AIEngineTests(unittest.TestCase):
    def test_prompt_includes_contact_settings_and_context(self):
        contact = {"name": "Test Friend", "style": "Hinglish", "instructions": "Be polite"}
        history = [{"direction": "incoming", "body": "Kal milte hain"}]
        prompt = build_prompt(contact, "Aaj free ho?", history, "Friend prefers short replies")
        self.assertIn("Test Friend", prompt)
        self.assertIn("Hinglish", prompt)
        self.assertIn("Be polite", prompt)
        self.assertIn("Kal milte hain", prompt)
        self.assertIn("Aaj free ho?", prompt)
        self.assertIn("Friend prefers short replies", prompt)

    def test_prompt_has_natural_hinglish_quality_rules(self):
        prompt = build_prompt({}, "Bhai kal miloge?", [], "")
        self.assertIn("Do not repeat", prompt)
        self.assertIn("Do not invent", prompt)
        self.assertIn("real Indian WhatsApp chat", prompt)
        self.assertIn("do not assume", prompt)

    def test_prompt_does_not_repeat_current_incoming_or_unsent_drafts(self):
        history = [
            {"direction": "incoming", "body": "Bhai kal miloge?"},
            {"direction": "draft", "body": "Haan pakka milte hain"},
            {"direction": "outgoing", "body": "Pichle hafte baat karte hain"},
        ]
        prompt = build_prompt({}, "Bhai kal miloge?", history, "")
        self.assertEqual(prompt.count("Bhai kal miloge?"), 1)
        self.assertNotIn("Haan pakka milte hain", prompt)
        self.assertIn("Pichle hafte baat karte hain", prompt)

    def test_empty_history_handled(self):
        prompt = build_prompt({}, "Hello", [], "")
        self.assertIn("No previous messages", prompt)
        self.assertIn("Hello", prompt)

if __name__ == "__main__":
    unittest.main()
