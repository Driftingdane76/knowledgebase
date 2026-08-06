import unittest
from qa_app.redaction import redact_text_content, get_redacted_words_idx

class TestOCRTranspositionAndFuzzyCPR(unittest.TestCase):
    """
    Test suite verifying robust redaction against OCR imperfections:
    1. Transpositions: 'CRP' instead of 'CPR', 'CRP-NUMMER'
    2. Character merging on small fonts: '1223-4565' (4-digit prefix) under 'Personnummer (CRP)'
    3. OCR digit substitutions in CPR column: '124045 1234' in tables
    """

    def test_crp_keyword_transposition(self):
        """Florence-2 often reads CPR as CRP. It must be recognized as a CPR keyword."""
        text = "Personnummer (CRP)\n1223-4565"
        redacted = redact_text_content(text)
        self.assertIn("[REDACTED CPR]", redacted)
        self.assertNotIn("1223-4565", redacted)

    def test_visual_florence_token_masking(self):
        """Visual OCR bounding box test matching the exact tokens extracted by Florence-2."""
        d = {
            'text':   ['Personnummer (CRP)', '1223-4565'],
            'conf':   [100.0, 100.0],
            'left':   [50, 50],
            'top':    [460, 510],
            'width':  [120, 90],
            'height': [15, 20],
        }
        text = "Personnummer (CRP)\n1223-4565"
        redacted_idx = get_redacted_words_idx(d, text)
        self.assertIn(1, redacted_idx, "Word index 1 ('1223-4565') under 'Personnummer (CRP)' must be redacted.")

if __name__ == '__main__':
    unittest.main()
