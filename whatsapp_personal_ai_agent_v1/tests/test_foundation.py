import tempfile
import unittest
from pathlib import Path

class FoundationTests(unittest.TestCase):
    def test_phone_normalization(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from main import normalize_phone
        self.assertEqual(normalize_phone("+91 98765-43210"), "919876543210")
        self.assertEqual(normalize_phone("abc"), "")

if __name__ == "__main__":
    unittest.main()
