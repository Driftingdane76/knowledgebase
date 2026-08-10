import re

# Current implementation extracted from app.js
def current_highlight_match(text, query):
    if not query or not query.strip():
        return text
    trimmed = query.strip()
    escaped_phrase = re.escape(trimmed)
    words = [re.escape(w) for w in trimmed.split() if w]
    if ' ' in trimmed:
        pattern = f"(?:\\b{escaped_phrase}\\b|{escaped_phrase}|(?:\\b(?:{'|'.join(words)})\\b))"
    else:
        pattern = f"(?:\\b{escaped_phrase}\\b|{escaped_phrase})"
    return re.sub(f"({pattern})(?![^<]*>)", r'<mark class="search-hit">\1</mark>', text, flags=re.IGNORECASE)

def current_ocr_boxes(ocr_words, query):
    if not query or not query.strip():
        return []
    terms = [t.lower() for t in query.split() if t]
    boxes = []
    for word in ocr_words:
        text = word.get('text', '')
        lower_text = text.lower()
        word_len = len(text) or 1
        for term in terms:
            start_idx = 0
            while True:
                idx = lower_text.find(term, start_idx)
                if idx == -1:
                    break
                end_idx = idx + len(term)
                sub_left = word['left'] + (idx / word_len) * word['width']
                sub_width = max((len(term) / word_len) * word['width'], 2)
                boxes.append({
                    'left': sub_left,
                    'top': word['top'],
                    'width': sub_width,
                    'height': word['height']
                })
                start_idx = end_idx
    return boxes

print("=== RUNNING TDD TESTS ON CURRENT IMPLEMENTATION ===")

# Test 1: Full phrase highlighting in text
text = "Godkendelsesflowet var låst. Mere end 100 resultater fundet."
query = "Mere end 100 resultater"
result_text = current_highlight_match(text, query)

expected_text = 'Godkendelsesflowet var låst. <mark class="search-hit">Mere end 100 resultater</mark> fundet.'

print(f"\n[Test 1] Multi-word phrase matching in text:")
print(f"Result:   {result_text}")
print(f"Expected: {expected_text}")
if result_text == expected_text:
    print("STATUS: PASS")
else:
    print("STATUS: FAIL (Phrase was broken into separate mark tags or matched incorrectly)")

# Test 2: OCR multi-word phrase bounding box
ocr_words = [
    {"text": "Mere", "left": 10.0, "top": 20.0, "width": 8.0, "height": 4.0},
    {"text": "end", "left": 19.0, "top": 20.0, "width": 6.0, "height": 4.0},
    {"text": "100", "left": 26.0, "top": 20.0, "width": 6.0, "height": 4.0},
    {"text": "resultater", "left": 33.0, "top": 20.0, "width": 15.0, "height": 4.0}
]
result_boxes = current_ocr_boxes(ocr_words, query)
print(f"\n[Test 2] OCR Multi-word phrase bounding boxes count:")
print(f"Result Box Count:   {len(result_boxes)} boxes")
print(f"Expected Box Count: 1 unified box covering the full phrase")
if len(result_boxes) == 1:
    print("STATUS: PASS")
else:
    print("STATUS: FAIL (Generated 4 individual word boxes instead of 1 merged phrase box)")

# Test 3: OCR punctuation offset on single word
ocr_word_punct = [{"text": "- Advarsel", "left": 40.0, "top": 15.0, "width": 20.0, "height": 5.0}]
punct_boxes = current_ocr_boxes(ocr_word_punct, "Advarsel")
print(f"\n[Test 3] OCR word with leading punctuation '- Advarsel':")
print(f"Result Box: {punct_boxes}")
# Proportional error: linear character math puts sub_left at 40 + (2/10)*20 = 44, width = 16
# In proportional fonts, '- ' takes < 5% of space, so starting at 20% clips into the 'A'
print("STATUS: DEMONSTRATES OFFSET ERROR (Linear character slicing clips into proportional glyphs)")
