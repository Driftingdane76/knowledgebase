import unittest
from qa_app.redaction import redact_text_content, get_redacted_words_idx

class TestCPREntryHumanError(unittest.TestCase):
    """
    Test suite verifying that numbers under explicit CPR / Personnummer labels or prefixes
    are redacted even when the date portion contains typos / human entry errors (e.g. month 22).
    """

    def test_cpr_field_with_typo_date_redacted(self):
        """
        When 'Personnummer' or 'CPR' is directly associated with the field (e.g. form label or prefix),
        human entry errors like '112233-4455' (month 22) MUST still be redacted as [REDACTED CPR].
        """
        text = "Personnummer (CPR)\n112233-4455"
        redacted = redact_text_content(text)
        self.assertIn("[REDACTED CPR]", redacted, "Failed to redact typo/human-error CPR under 'Personnummer (CPR)' label")
        self.assertNotIn("112233-4455", redacted)

    def test_cpr_prefix_with_typo_date_redacted(self):
        """
        Inline prefix like 'CPR: 112233-4455' with typo date MUST still be redacted.
        """
        text = "Kundens CPR: 112233-4455 er noteret."
        redacted = redact_text_content(text)
        self.assertIn("[REDACTED CPR]", redacted, "Failed to redact inline CPR: with typo date")
        self.assertNotIn("112233-4455", redacted)

    def test_unlabeled_invalid_date_not_redacted(self):
        """
        A random 10-digit number like '112233-4455' that is NOT under a CPR label or prefix
        should NOT be redacted if date is invalid (protecting order/invoice numbers from false positives).
        """
        text = "Generel side\nFakturanummer: 112233-4455"
        redacted = redact_text_content(text)
        self.assertNotIn("[REDACTED CPR]", redacted)
        self.assertIn("112233-4455", redacted)

    def test_spatial_cpr_label_with_typo_date_redacted(self):
        """
        Visual OCR test: When 'Personnummer' / '(CPR)' is in visual line 0,
        the value '112233-4455' in visual line 1 directly below it MUST be flagged for redaction.
        """
        d = {
            'text':   ['Personnummer', '(CPR)', '112233-4455'],
            'conf':   [99, 99, 99],
            'left':   [10, 120, 10],
            'top':    [10, 10, 40],
            'width':  [100, 50, 90],
            'height': [15, 15, 15],
        }
        text = "Personnummer (CPR)\n112233-4455"
        redacted_idx = get_redacted_words_idx(d, text)
        self.assertIn(2, redacted_idx, "Word index 2 ('112233-4455') was not flagged for visual redaction under CPR label")

if __name__ == '__main__':
    unittest.main()
