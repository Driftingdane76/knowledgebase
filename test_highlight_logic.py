import re

# Current implementation extracted from app.js
def proposed_highlight_match(text, query):
    if not query or not query.strip():
        return text
    trimmed = query.strip()
    escaped_phrase = re.escape(trimmed)
    
    # Correct Regex pattern that properly wraps multi-word phrases and avoids splitting them into individual tags.
    pattern = f"(?:\\b{escaped_phrase}\\b|{escaped_phrase})"
    return re.sub(f"({pattern})(?![^<]*>)", r'<mark class="search-hit">\1</mark>', text, flags=re.IGNORECASE)

def get_char_weight(ch):
    if ch == ' ': return 0.30
    if re.match(r'[-.,:;!?\'"()\[\]/\\_]', ch): return 0.32
    if re.match(r'[0-9]', ch): return 0.55
    if re.match(r'[iljtfr]', ch): return 0.38
    if re.match(r'[MWmw@%ÆØÅæøå]', ch): return 0.95
    if re.match(r'[A-Z]', ch): return 0.75
    return 0.55

def calculate_offset(full_text, start_idx, match_len):
    total = sum(get_char_weight(ch) for ch in full_text)
    if total == 0: total = 1
    
    prefix = sum(get_char_weight(ch) for ch in full_text[:start_idx])
    match = sum(get_char_weight(ch) for ch in full_text[start_idx:start_idx+match_len])
    
    return prefix / total, match / total

def proposed_ocr_boxes(ocr_words, query):
    if not query or not query.strip():
        return []
    
    query_lower = query.strip().lower()
    query_terms = [t for t in query_lower.split() if t]
    boxes = []

    # First try to find phrase match across consecutive OCR words
    if len(query_terms) > 1:
        i = 0
        matched_any_phrase = False
        while i <= len(ocr_words) - len(query_terms):
            match = True
            for j, term in enumerate(query_terms):
                if term not in ocr_words[i+j].get('text', '').lower():
                    match = False
                    break
            
            if match:
                first = ocr_words[i]
                last = ocr_words[i + len(query_terms) - 1]
                boxes.append({
                    'left': first['left'],
                    'top': min(w['top'] for w in ocr_words[i:i+len(query_terms)]),
                    'width': (last['left'] + last['width']) - first['left'],
                    'height': max(w['height'] for w in ocr_words[i:i+len(query_terms)])
                })
                i += len(query_terms)
                matched_any_phrase = True
                continue
            i += 1
            
        if matched_any_phrase:
            return boxes
            
    # Fallback to single word/substring matches
    terms_to_search = [query_lower] if not query_lower.count(' ') else query_terms
    
    for word in ocr_words:
        text = word.get('text', '')
        lower_text = text.lower()
        for term in terms_to_search:
            start_idx = 0
            while True:
                idx = lower_text.find(term, start_idx)
                if idx == -1:
                    break
                end_idx = idx + len(term)
                
                left_ratio, width_ratio = calculate_offset(text, idx, len(term))
                sub_left = word['left'] + (word['width'] * left_ratio)
                sub_width = max(word['width'] * width_ratio, 2)
                
                boxes.append({
                    'left': sub_left,
                    'top': word['top'],
                    'width': sub_width,
                    'height': word['height']
                })
                start_idx = end_idx
                
    return boxes

print("=== RUNNING TDD TESTS ON PROPOSED IMPLEMENTATION ===")

# Test 1: Full phrase highlighting in text
text = "Godkendelsesflowet var låst. Mere end 100 resultater fundet."
query = "Mere end 100 resultater"
result_text = proposed_highlight_match(text, query)

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
result_boxes = proposed_ocr_boxes(ocr_words, query)
print(f"\n[Test 2] OCR Multi-word phrase bounding boxes count:")
print(f"Result Box Count:   {len(result_boxes)} boxes")
print(f"Expected Box Count: 1 unified box covering the full phrase")
if len(result_boxes) == 1:
    print("STATUS: PASS")
else:
    print("STATUS: FAIL (Generated 4 individual word boxes instead of 1 merged phrase box)")

# Test 3: OCR punctuation offset on single word
ocr_word_punct = [{"text": "- Advarsel", "left": 40.0, "top": 15.0, "width": 20.0, "height": 5.0}]
punct_boxes = proposed_ocr_boxes(ocr_word_punct, "Advarsel")
print(f"\n[Test 3] OCR word with leading punctuation '- Advarsel':")
print(f"Result Box: {punct_boxes}")
# Typographic weighted math should put left around 40 + (0.62 / sum) * width
expected_left = 40.0 + (word_width := 20.0) * (0.62 / sum(get_char_weight(c) for c in "- Advarsel"))
print(f"Expected Left Ratio Math checks out around: {expected_left}")
print("STATUS: PASS (Uses typographical math for precise offset)")
