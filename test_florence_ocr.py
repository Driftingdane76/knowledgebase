import os
import sys
import unittest
from PIL import Image, ImageDraw

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from qa_app.redaction import get_redacted_words_idx, redact_text_content

class TestFlorence2OCRRedaction(unittest.TestCase):
    """
    Test suite for 100% local OCR & Redaction using Microsoft Florence-2 model.
    Runs locally with zero external API calls.
    """

    @classmethod
    def setUpClass(cls):
        cls.image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_htmls', 'mock_crm_dashboard.png')
        if not os.path.exists(cls.image_path):
            raise FileNotFoundError(f"Test image not found at {cls.image_path}")

        try:
            import torch
            from transformers import AutoProcessor, AutoModelForCausalLM
        except ImportError:
            raise ImportError("PyTorch and transformers are required. Install with: pip install torch transformers timm einops")

        print("\n[Florence-2 Test] Loading local Microsoft Florence-2-base model...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        
        model_id = "microsoft/Florence-2-base"
        cls.model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch_dtype, trust_remote_code=True).to(device)
        cls.processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
        cls.device = device
        cls.torch_dtype = torch_dtype

        # Open image
        cls.image = Image.open(cls.image_path).convert("RGB")
        width, height = cls.image.size
        cls.width = width
        cls.height = height

        # Run inference with <OCR_WITH_REGION>
        prompt = "<OCR_WITH_REGION>"
        inputs = cls.processor(text=prompt, images=cls.image, return_tensors="pt")
        inputs = {k: v.to(device=cls.device, dtype=cls.torch_dtype) if v.dtype.is_floating_point else v.to(cls.device) for k, v in inputs.items()}

        print("[Florence-2 Test] Running local inference...")
        with torch.no_grad():
            generated_ids = cls.model.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=1024,
                num_beams=3,
                do_sample=False
            )

        generated_text = cls.processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
        parsed_result = cls.processor.post_process_generation(
            generated_text,
            task=prompt,
            image_size=(width, height)
        )

        ocr_data = parsed_result.get("<OCR_WITH_REGION>", {})
        quad_boxes = ocr_data.get("quad_boxes", [])
        bboxes = ocr_data.get("bboxes", [])
        labels = ocr_data.get("labels", [])

        # Build standardized dictionary format matching qa_app/redaction.py
        cls.d = {'text': [], 'left': [], 'top': [], 'width': [], 'height': [], 'conf': []}

        if quad_boxes:
            for quad, label in zip(quad_boxes, labels):
                xs = [quad[0], quad[2], quad[4], quad[6]]
                ys = [quad[1], quad[3], quad[5], quad[7]]
                left = min(xs)
                top = min(ys)
                w = max(xs) - left
                h = max(ys) - top
                cls.d['text'].append(str(label).strip())
                cls.d['left'].append(left)
                cls.d['top'].append(top)
                cls.d['width'].append(w)
                cls.d['height'].append(h)
                cls.d['conf'].append(100.0)
        elif bboxes:
            for box, label in zip(bboxes, labels):
                x1, y1, x2, y2 = box
                cls.d['text'].append(str(label).strip())
                cls.d['left'].append(x1)
                cls.d['top'].append(y1)
                cls.d['width'].append(x2 - x1)
                cls.d['height'].append(y2 - y1)
                cls.d['conf'].append(100.0)

        cls.raw_text = "\n".join(cls.d['text'])
        print(f"[Florence-2 Test] Extracted {len(cls.d['text'])} tokens.")

    def test_florence_extracted_tokens(self):
        """Verify Florence-2 detected tokens from the test image."""
        self.assertTrue(len(self.d['text']) > 0, "Florence-2 failed to extract any tokens from image.")

    def test_cpr_redaction(self):
        """Verify CPR numbers are identified and masked from extracted text."""
        redacted = redact_text_content(self.raw_text)
        self.assertNotIn("010203-4567", redacted)
        self.assertNotIn("251290-9876", redacted)
        self.assertNotIn("150688-1122", redacted)

    def test_bank_redaction(self):
        """Verify Bank numbers are identified and masked from extracted text."""
        redacted = redact_text_content(self.raw_text)
        self.assertNotIn("1234567890", redacted)
        self.assertNotIn("9876543210", redacted)

    def test_names_preserved(self):
        """Verify valid names are preserved in text."""
        redacted = redact_text_content(self.raw_text)
        self.assertTrue("Morten" in redacted or "Lars" in redacted or "Sofie" in redacted)

    def test_visual_masking_output(self):
        """Verify coordinate bounding boxes and generate visual output image."""
        redacted_idx = get_redacted_words_idx(self.d, self.raw_text)
        self.assertTrue(len(redacted_idx) > 0, "No bounding box indices were flagged for redaction.")

        img_draw = self.image.copy()
        draw = ImageDraw.Draw(img_draw)
        for i in redacted_idx:
            left, top, w, h = self.d['left'][i], self.d['top'][i], self.d['width'][i], self.d['height'][i]
            draw.rectangle([left - 2, top - 2, left + w + 2, top + h + 2], fill="black")

        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_htmls', 'florence_redacted_test.png')
        img_draw.save(out_path)
        print(f"\n[Florence-2 Test] Redacted test screenshot saved to: {out_path}")

if __name__ == '__main__':
    unittest.main()
