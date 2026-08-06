"""
Local OCR & PII Redaction Engine using Microsoft Florence-2.
Runs 100% on-premise / in-process with zero cloud egress.
"""
import os
import torch
from PIL import Image, ImageDraw
from transformers import AutoProcessor, AutoModelForCausalLM
from .redaction import get_redacted_words_idx, redact_text_content

_MODEL = None
_PROCESSOR = None
_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
_DTYPE = torch.float16 if torch.cuda.is_available() else torch.float32

def get_florence_model():
    """
    Lazy-loads and caches the Microsoft Florence-2 model and processor.
    """
    global _MODEL, _PROCESSOR
    if _MODEL is None:
        model_id = os.environ.get("FLORENCE_MODEL_ID", "microsoft/Florence-2-base")
        _MODEL = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=_DTYPE,
            trust_remote_code=True
        ).to(_DEVICE)
        _PROCESSOR = AutoProcessor.from_pretrained(
            model_id,
            trust_remote_code=True
        )
    return _MODEL, _PROCESSOR

def run_florence_ocr_and_redact(img):
    """
    Executes local OCR on the PIL Image using Florence-2 <OCR_WITH_REGION>.
    Identifies Danish CPR numbers and Bank info, paints black masking boxes over coordinates,
    and returns (sanitized_text, ocr_words_percentage_dict).
    """
    model, processor = get_florence_model()
    
    if img.mode != "RGB":
        img = img.convert("RGB")
        
    width, height = img.size
    if width < 10 or height < 10:
        return "", []

    prompt = "<OCR_WITH_REGION>"
    
    inputs = processor(text=prompt, images=img, return_tensors="pt")
    inputs = {
        k: v.to(device=_DEVICE, dtype=_DTYPE) if v.dtype.is_floating_point else v.to(_DEVICE)
        for k, v in inputs.items()
    }
    
    with torch.no_grad():
        generated_ids = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=1024,
            num_beams=3,
            do_sample=False
        )
        
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
    parsed_result = processor.post_process_generation(
        generated_text,
        task=prompt,
        image_size=(width, height)
    )
    
    ocr_data = parsed_result.get("<OCR_WITH_REGION>", {})
    quad_boxes = ocr_data.get("quad_boxes", [])
    bboxes = ocr_data.get("bboxes", [])
    labels = ocr_data.get("labels", [])
    
    d = {'text': [], 'left': [], 'top': [], 'width': [], 'height': [], 'conf': []}
    
    if quad_boxes:
        for quad, label in zip(quad_boxes, labels):
            xs = [quad[0], quad[2], quad[4], quad[6]]
            ys = [quad[1], quad[3], quad[5], quad[7]]
            left, top = min(xs), min(ys)
            w = max(xs) - left
            h = max(ys) - top
            d['text'].append(str(label).strip())
            d['left'].append(left)
            d['top'].append(top)
            d['width'].append(w)
            d['height'].append(h)
            d['conf'].append(100.0)
    elif bboxes:
        for box, label in zip(bboxes, labels):
            x1, y1, x2, y2 = box
            d['text'].append(str(label).strip())
            d['left'].append(x1)
            d['top'].append(y1)
            d['width'].append(x2 - x1)
            d['height'].append(y2 - y1)
            d['conf'].append(100.0)

    # 1. Identify sensitive words to redact
    full_text = "\n".join(d['text'])
    redacted_words_idx = get_redacted_words_idx(d, full_text)
    
    # 2. Draw black boxes on the image canvas
    draw = ImageDraw.Draw(img)
    for i in redacted_words_idx:
        left, top, w, h = d['left'][i], d['top'][i], d['width'][i], d['height'][i]
        draw.rectangle([left - 2, top - 2, left + w + 2, top + h + 2], fill="black")
        d['text'][i] = "[REDACTED]"
        
    # 3. Sanitize plain text for search indexing
    sanitized_text = redact_text_content("\n".join(d['text']))
    
    # 4. Construct percentage coordinates for UI word highlighting
    ocr_words = []
    for i in range(len(d['text'])):
        word = d['text'][i].strip()
        ocr_words.append({
            'text': word,
            'left': round((d['left'][i] / width) * 100, 2),
            'top': round((d['top'][i] / height) * 100, 2),
            'width': round((d['width'][i] / width) * 100, 2),
            'height': round((d['height'][i] / height) * 100, 2)
        })
        
    return sanitized_text.strip(), ocr_words
