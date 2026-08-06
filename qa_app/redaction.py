import re
import datetime

# Pre-compile patterns
cpr_pattern = re.compile(r'(?<!\d)(\d{5,6})\s*[-–—.]?\s*(\d{4})(?!\d)')

# Robust Bank Registration Number Regex
reg_keywords_pattern = re.compile(r'\b(reg\.?(?:\s*(?:nr|nummer))?|registrerings(?:\s*(?:nr|nummer))?)\b', re.IGNORECASE)

# Comprehensive Danish Bank / Konto Keywords (including NemKonto, Pengeinstitut, IBAN)
konto_keywords_pattern = re.compile(r'\b(nemkonto|udbetalingskonto|bank\s*oplysninger|konto\s*oplysninger|konto\s*nummer|kontonummer|konto|kontonr|ontonummer|ontonr|pengeinstitut|iban)\b', re.IGNORECASE)
bank_combined_pattern = re.compile(r'(?<!\d)(\d{4})\s*(?:[-–—\s]|[-–—]?\s*(?:kontonr|konto|nr\.?)?:?\s*)\s*(\d{7,10})(?!\d)', re.IGNORECASE)
iban_pattern = re.compile(r'\bDK\s*\d{2}(?:\s*\d{4}){3}\s*\d{2}\b|\bDK\d{16}\b|\bDK\s*\d{2}(?:\s*\d{2,4}){3,5}\b', re.IGNORECASE)
reg_loose_pattern = re.compile(r'(?<!\d)\d{4}(?!\d)')
konto_loose_pattern = re.compile(r'(?<!\d)\d{7,14}(?!\d)')
cpr_keywords = [r'\bcpr\b', r'cpr-nummer', r'\bcrp\b', r'crp-nummer', r'personnummer', r'er nummer', r'\bcor\b']
cpr_keyword_pattern = re.compile(r'(' + '|'.join(cpr_keywords) + r')', re.IGNORECASE)

def is_valid_date(ddmmyy):
    if len(ddmmyy) == 5:
        ddmmyy = "0" + ddmmyy
    try:
        datetime.datetime.strptime(ddmmyy, "%d%m%y")
        return True
    except ValueError:
        return False

def redact_text_content(text):
    if not text:
        return text
    
    has_bank_keyword = bool(reg_keywords_pattern.search(text) or konto_keywords_pattern.search(text))
    
    new_val = text
    # Redact CPR: Any valid Danish birthdate (DDMMYY) or explicit CPR/Personnummer label
    lines = new_val.split('\n')
    processed_lines = []
    for idx, line in enumerate(lines):
        prev_has_cpr = (idx > 0 and bool(cpr_keyword_pattern.search(lines[idx - 1])))
        has_local_label = (bool(cpr_keyword_pattern.search(line)) or prev_has_cpr) and "cvr" not in line.lower()
        def redact_match(m):
            if "cvr" in line.lower():
                return m.group(0)
            if is_valid_date(m.group(1)) or has_local_label:
                return "[REDACTED CPR]"
            return m.group(0)
        processed_lines.append(cpr_pattern.sub(redact_match, line))
    new_val = '\n'.join(processed_lines)
    
    # Redact explicit Danish IBANs globally
    new_val = iban_pattern.sub(r"[REDACTED BANK]", new_val)
        
    if has_bank_keyword:
        # First redact global combined bank patterns
        new_val = bank_combined_pattern.sub(r"[REDACTED BANK]", new_val)
            
        lines = []
        raw_lines = new_val.split('\n')
        for idx, line in enumerate(raw_lines):
            line_lower = line.lower()
            prev_line_lower = raw_lines[idx - 1].lower() if idx > 0 else ""
            is_reg = bool(reg_keywords_pattern.search(line_lower))
            is_konto = bool(konto_keywords_pattern.search(line_lower)) or bool(konto_keywords_pattern.search(prev_line_lower))
            
            # Guard against CVR false positives
            if "cvr" not in line_lower:
                if is_reg:
                    line = reg_loose_pattern.sub("[REDACTED BANK]", line)
                if is_konto:
                    line = konto_loose_pattern.sub("[REDACTED BANK]", line)
            lines.append(line)
        new_val = '\n'.join(lines)
        
    return new_val

def get_redacted_words_idx(d, text):
    has_bank_keyword = bool(reg_keywords_pattern.search(text) or konto_keywords_pattern.search(text))
    
    visual_lines = []
    n_boxes = len(d['text'])
    for i in range(n_boxes):
        word = d['text'][i].strip()
        conf = float(d['conf'][i]) if d['conf'][i] is not None else -1
        if conf > 0 and word:
            w_top = d['top'][i]
            w_height = d['height'][i]
            center_y = w_top + w_height / 2
            
            found_line = False
            for line in visual_lines:
                if abs(center_y - line['center_y']) < max(10, w_height / 2):
                    line['words'].append({'text': word, 'idx': i, 'left': d['left'][i]})
                    line['center_y'] = (line['center_y'] * (len(line['words'])-1) + center_y) / len(line['words'])
                    found_line = True
                    break
            
            if not found_line:
                visual_lines.append({
                    'center_y': center_y,
                    'words': [{'text': word, 'idx': i, 'left': d['left'][i]}]
                })
                
    visual_lines.sort(key=lambda x: x['center_y'])
    for line in visual_lines:
        line['words'].sort(key=lambda x: x['left'])

    global_str = ""
    char_to_word_idx = []
    
    for line in visual_lines:
        for w in line['words']:
            word_text = w['text']
            global_str += word_text
            char_to_word_idx.extend([w['idx']] * len(word_text))
            global_str += " "
            char_to_word_idx.append(-1)
        global_str += "\n"
        char_to_word_idx.append(-1)

    global_str_lower = global_str.lower()
    redacted_words_idx = set()
    
    # 1. CPR Redaction (Matches any valid Danish birthdate or explicit CPR label)
    cpr_label_boxes = []
    for i in range(n_boxes):
        if cpr_keyword_pattern.search(d['text'][i]) and "cvr" not in d['text'][i].lower():
            cpr_label_boxes.append((d['left'][i], d['top'][i], d['width'][i], d['height'][i]))

    # Global CPR span matching across line breaks and token boundaries
    for match in cpr_pattern.finditer(global_str):
        ddmmyy, _ = match.groups()
        start, end = match.span()
        matched_word_indices = {char_to_word_idx[c] for c in range(start, end) if char_to_word_idx[c] != -1}
        
        is_spatially_under_cpr = any(
            any(
                abs((d['left'][w_idx] + d['width'][w_idx]/2) - (l_left + l_width/2)) < max(100, l_width)
                and (d['top'][w_idx] > l_top)
                for l_left, l_top, l_width, _ in cpr_label_boxes
            )
            for w_idx in matched_word_indices
        )
        
        # Check context around match in global_str
        context_snippet = global_str[max(0, start - 40):min(len(global_str), end + 40)]
        has_explicit_cpr = bool(cpr_keyword_pattern.search(context_snippet)) and "cvr" not in context_snippet.lower()
        
        if (has_explicit_cpr or is_spatially_under_cpr or is_valid_date(ddmmyy)) and "cvr" not in context_snippet.lower():
            redacted_words_idx.update(matched_word_indices)
                        
    # 2. Danish IBAN Redaction globally
    for match in iban_pattern.finditer(global_str):
        start, end = match.span()
        for char_idx in range(start, end):
            w_idx = char_to_word_idx[char_idx]
            if w_idx != -1:
                redacted_words_idx.add(w_idx)

    # 3. Bank Redaction
    if has_bank_keyword:
        # Combined pattern globally
        for match in bank_combined_pattern.finditer(global_str):
            start, end = match.span()
            for char_idx in range(start, end):
                w_idx = char_to_word_idx[char_idx]
                if w_idx != -1:
                    redacted_words_idx.add(w_idx)
                    
        # Loose patterns per line with multi-line keyword context
        prev_line_is_bank = False
        for line in visual_lines:
            words_info = line['words']
            line_str = " ".join(w['text'] for w in words_info)
            line_str_lower = line_str.lower()
            
            is_reg = bool(reg_keywords_pattern.search(line_str_lower))
            is_konto = bool(konto_keywords_pattern.search(line_str_lower)) or prev_line_is_bank
            
            if "cvr" not in line_str_lower:
                if is_reg:
                    for match in reg_loose_pattern.finditer(line_str):
                        num_str = match.group(0)
                        for w in words_info:
                            if num_str in w['text']:
                                redacted_words_idx.add(w['idx'])
                                
                if is_konto:
                    for match in konto_loose_pattern.finditer(line_str):
                        num_str = match.group(0)
                        for w in words_info:
                            if num_str in w['text']:
                                redacted_words_idx.add(w['idx'])
                                
            prev_line_is_bank = bool(konto_keywords_pattern.search(line_str_lower))

    return redacted_words_idx
