from django.test import SimpleTestCase
from qa_app.redaction import redact_text_content, get_redacted_words_idx

class EdgeCaseRedactionTests(SimpleTestCase):
    
    def test_cross_line_cpr_wrap(self):
        """Test Case 1: CPR number wrapped across two visual lines in chat/text."""
        # Line 1 (y=10): "CPR", "260353"
        # Line 2 (y=30): "9773,", "og", "kan", "se"
        text = "CPR 260353\n9773, og kan se"
        d = {
            'text':   ['CPR', '260353', '9773,', 'og', 'kan', 'se'],
            'conf':   [99, 99, 99, 99, 99, 99],
            'left':   [10, 50, 10, 60, 90, 125],
            'top':    [10, 10, 30, 30, 30, 30],
            'width':  [35, 55, 45, 20, 25, 20],
            'height': [15, 15, 15, 15, 15, 15],
        }
        
        idx = get_redacted_words_idx(d, text)
        
        # Both index 1 ('260353') and index 2 ('9773,') must be redacted
        self.assertIn(1, idx, "First half of wrapped CPR ('260353') should be redacted")
        self.assertIn(2, idx, "Second half of wrapped CPR ('9773,') should be redacted")

    def test_competing_keyword_with_explicit_cpr_label(self):
        """Test Case 2: Explicit CPR label followed by a sentence containing a competing word ('fakturaen')."""
        # Line 1 (y=10): "Cpr", "nummer", "på", "fakturaen", "er", "041156-", "5350."
        text = "Cpr nummer på fakturaen er 041156-5350."
        d = {
            'text':   ['Cpr', 'nummer', 'på', 'fakturaen', 'er', '041156-', '5350.'],
            'conf':   [99, 99, 99, 99, 99, 99, 99],
            'left':   [10, 45, 100, 125, 195, 220, 285],
            'top':    [10, 10, 10, 10, 10, 10, 10],
            'width':  [30, 50, 20, 65, 20, 60, 45],
            'height': [15, 15, 15, 15, 15, 15, 15],
        }
        
        idx = get_redacted_words_idx(d, text)
        
        # Both index 5 ('041156-') and index 6 ('5350.') must be redacted despite presence of 'fakturaen'
        self.assertIn(5, idx, "Token '041156-' should be redacted")
        self.assertIn(6, idx, "Token '5350.' should be redacted")

    def test_multi_row_table_column_alignment(self):
        """Test Case 3: CPR entry in a multi-row data table exceeding default 120px vertical threshold."""
        # Header (y=10):  "CPR-NUMMER" at left=250, top=10, width=100
        # Row 1   (y=50):  "010203-4567" at left=250, top=50, width=85  (distance = 40px)
        # Row 2   (y=180): "081184", "6027" at left=250, top=180, width=45, 40 (distance = 170px > 120px)
        text = "CPR-NUMMER\n010203-4567\n081184 6027"
        d = {
            'text':   ['CPR-NUMMER', '010203-4567', '081184', '6027'],
            'conf':   [99, 99, 99, 99],
            'left':   [250, 250, 250, 300],
            'top':    [10, 50, 180, 180],
            'width':  [100, 85, 45, 40],
            'height': [15, 15, 15, 15],
        }
        
        idx = get_redacted_words_idx(d, text)
        
        # Row 1 CPR (index 1) must be redacted
        self.assertIn(1, idx, "Row 1 CPR ('010203-4567') should be redacted")
        # Row 2 CPR (indices 2 and 3) must be redacted despite y=180
        self.assertIn(2, idx, "Row 2 CPR part 1 ('081184') should be redacted")
        self.assertIn(3, idx, "Row 2 CPR part 2 ('6027') should be redacted")
