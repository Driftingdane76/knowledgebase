from django.test import SimpleTestCase
from qa_app.redaction import is_valid_date, redact_text_content, get_redacted_words_idx

class RedactionEngineTests(SimpleTestCase):
    
    def test_calendar_validation(self):
        """Test that is_valid_date correctly validates Danish dates (DDMMYY)"""
        # Valid dates
        self.assertTrue(is_valid_date("150390"))  # 15th March 1990
        self.assertTrue(is_valid_date("010100"))  # 1st Jan 2000
        self.assertTrue(is_valid_date("290224"))  # 29th Feb 2024 (Leap year)
        self.assertTrue(is_valid_date("311299"))  # 31st Dec 1999
        self.assertTrue(is_valid_date("10424"))   # 1st April 2024 (5 digit)

        # Invalid dates
        self.assertFalse(is_valid_date("320390")) # 32nd March
        self.assertFalse(is_valid_date("151390")) # 13th month
        self.assertFalse(is_valid_date("290223")) # 29th Feb 2023 (Not leap year)
        self.assertFalse(is_valid_date("000000")) # All zeros
        
    def test_redact_text_content_cpr(self):
        """Test CPR redaction based on keywords"""
        # Should redact because keyword "CPR" is present
        text_with_cpr = "Kunde CPR: 150390-1234 ringede i dag."
        redacted = redact_text_content(text_with_cpr)
        self.assertIn("[REDACTED CPR]", redacted)
        self.assertNotIn("150390", redacted)

        # Should redact if under explicit CPR keyword even if date has human error / typo
        text_typo_cpr = "Kunde CPR: 320390-1234 ringede i dag."
        redacted_typo = redact_text_content(text_typo_cpr)
        self.assertIn("[REDACTED CPR]", redacted_typo)
        self.assertNotIn("320390-1234", redacted_typo)

        # Should NOT redact when date is invalid AND not under a local CPR label (protecting invoice numbers on pages with CPR mentions)
        text_general_invalid = "CPR Oplysning:\nFaktura 320390-1234 er modtaget."
        redacted_general = redact_text_content(text_general_invalid)
        self.assertNotIn("[REDACTED CPR]", redacted_general)
        self.assertIn("320390-1234", redacted_general)

        # Should NOT redact because there is no keyword
        text_no_keyword = "Reference 150390-1234 på fakturaen."
        redacted_no_keyword = redact_text_content(text_no_keyword)
        self.assertNotIn("[REDACTED CPR]", redacted_no_keyword)
        self.assertIn("150390", redacted_no_keyword)

    def test_redact_text_content_bank(self):
        """Test Bank redaction based on keywords"""
        # Should redact combined format because keyword "Reg.nr" is present
        text_with_bank = "Betaling til Reg.nr 1234 konto 1234567890."
        redacted = redact_text_content(text_with_bank)
        self.assertIn("[REDACTED BANK]", redacted)
        self.assertNotIn("1234567890", redacted)
        
        # Should NOT redact loose numbers without keyword
        text_no_keyword = "Faktura 1234 og beløb 1234567890."
        redacted_no_keyword = redact_text_content(text_no_keyword)
        self.assertNotIn("[REDACTED BANK]", redacted_no_keyword)
        self.assertIn("1234567890", redacted_no_keyword)

    def test_spatial_geometry_redaction(self):
        """Test that get_redacted_words_idx groups lines and redacts only when on the same line"""
        text = "Reg 1234\nFaktura 5678"
        # Mock OCR bounding box output
        # Line 1 (y=10): "Reg", "1234"
        # Line 2 (y=50): "Faktura", "5678"
        d = {
            'text':   ['Reg', '1234', 'Faktura', '5678'],
            'conf':   [99, 99, 99, 99],
            'left':   [10, 50, 10, 80],
            'top':    [10, 10, 50, 50],
            'width':  [30, 40, 60, 40],
            'height': [15, 15, 15, 15],
        }
        
        idx = get_redacted_words_idx(d, text)
        
        # Word at index 1 ("1234") should be redacted because it shares line 1 with "Reg"
        self.assertIn(1, idx)
        
        # Word at index 3 ("5678") should NOT be redacted because it is on line 2 (no keyword)
        self.assertNotIn(3, idx)
