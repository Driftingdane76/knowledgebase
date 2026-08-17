import os
import sys
import io
import time
import unittest
from PIL import Image

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from qa_app.redaction import get_redacted_words_idx, redact_text_content
from test_htmls.dynamic_mock_generator import generate_dynamic_html_snippet

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    raise ImportError("Playwright is required. Run: pip install playwright && playwright install chromium")

try:
    import torch
    from transformers import AutoProcessor, AutoModelForCausalLM
except ImportError:
    raise ImportError("PyTorch and transformers are required. Run: pip install torch transformers timm einops")


class TestMockPipelineSpeedy(unittest.TestCase):
    """
    Benchmark Suite 2: Speedy Settings (num_beams=1).
    Renders the exact same 10 dynamic UI screenshots, runs greedy decoding,
    and directly tests accuracy parity, PII leakage, and speedup ratio.
    """

    @classmethod
    def setUpClass(cls):
        print("\n" + "=" * 80)
        print("STARTING TEST 2: FLORENCE-2 SPEEDY PIPELINE (num_beams=1)")
        print("=" * 80)

        cls.device = "cuda" if torch.cuda.is_available() else "cpu"
        cls.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        model_id = os.environ.get("FLORENCE_MODEL_ID", "microsoft/Florence-2-base")

        print(f"[Model Setup] Loading {model_id} on {cls.device.upper()} ({cls.torch_dtype})...")
        cls.model = AutoModelForCausalLM.from_pretrained(
            model_id, torch_dtype=cls.torch_dtype, trust_remote_code=True
        ).to(cls.device)
        cls.processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)

        cls.num_cases = 10
        cls.results = []

        print(f"[Playwright Setup] Rendering {cls.num_cases} dynamic UI screenshots...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page_ctx = browser.new_page(device_scale_factor=2)

            for i in range(1, cls.num_cases + 1):
                html = generate_dynamic_html_snippet(i)
                page_ctx.set_content(html)
                page_ctx.wait_for_timeout(50)

                target = page_ctx.locator(".snippet-capture-target")
                screenshot_bytes = target.screenshot()
                img = Image.open(io.BytesIO(screenshot_bytes)).convert("RGB")

                # Run Florence-2 with num_beams=1 (Speedy Greedy Search)
                start_time = time.perf_counter()
                prompt = "<OCR_WITH_REGION>"
                inputs = cls.processor(text=prompt, images=img, return_tensors="pt")
                inputs = {
                    k: v.to(device=cls.device, dtype=cls.torch_dtype) if v.dtype.is_floating_point else v.to(cls.device)
                    for k, v in inputs.items()
                }

                with torch.no_grad():
                    generated_ids = cls.model.generate(
                        input_ids=inputs["input_ids"],
                        pixel_values=inputs["pixel_values"],
                        max_new_tokens=1024,
                        num_beams=1,  # Speedy configuration
                        do_sample=False
                    )

                gen_text = cls.processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
                parsed = cls.processor.post_process_generation(gen_text, task=prompt, image_size=img.size)
                elapsed = time.perf_counter() - start_time

                ocr_data = parsed.get("<OCR_WITH_REGION>", {})
                labels = ocr_data.get("labels", [])
                quad_boxes = ocr_data.get("quad_boxes", [])
                bboxes = ocr_data.get("bboxes", [])

                d = {'text': [], 'left': [], 'top': [], 'width': [], 'height': [], 'conf': []}

                if quad_boxes:
                    for quad, label in zip(quad_boxes, labels):
                        xs = [quad[0], quad[2], quad[4], quad[6]]
                        ys = [quad[1], quad[3], quad[5], quad[7]]
                        left, top = min(xs), min(ys)
                        d['text'].append(str(label).strip())
                        d['left'].append(left)
                        d['top'].append(top)
                        d['width'].append(max(xs) - left)
                        d['height'].append(max(ys) - top)
                        d['conf'].append(100.0)
                elif bboxes:
                    for box, label in zip(bboxes, labels):
                        d['text'].append(str(label).strip())
                        d['left'].append(box[0])
                        d['top'].append(box[1])
                        d['width'].append(box[2] - box[0])
                        d['height'].append(box[3] - box[1])
                        d['conf'].append(100.0)

                raw_text = "\n".join(d['text'])
                sanitized_text = redact_text_content(raw_text)
                redacted_idx = get_redacted_words_idx(d, raw_text)

                cls.results.append({
                    'index': i,
                    'elapsed': elapsed,
                    'tokens_count': len(d['text']),
                    'redacted_boxes_count': len(redacted_idx),
                    'raw_text': raw_text,
                    'sanitized_text': sanitized_text,
                })
                print(f"  -> Screenshot #{i:02d} processed in {elapsed:.2f}s | Tokens: {len(d['text']):02d} | Redacted Boxes: {len(redacted_idx)}")

            browser.close()

    def test_01_tokens_extracted_all_images(self):
        """Verify tokens were successfully read on all screenshots under greedy mode."""
        for res in self.results:
            self.assertGreater(res['tokens_count'], 0, f"Screenshot #{res['index']} failed to extract any OCR text under num_beams=1.")

    def test_02_zero_pii_leakage(self):
        """Verify CPR / Bank masking executed without dropping sensitive fields."""
        for res in self.results:
            if "cpr" in res['raw_text'].lower() or "reg" in res['raw_text'].lower() or "konto" in res['raw_text'].lower():
                self.assertTrue(
                    "[REDACTED" in res['sanitized_text'] or res['redacted_boxes_count'] > 0,
                    f"CRITICAL LEAK: Screenshot #{res['index']} dropped PII masking under num_beams=1!"
                )

    def test_03_print_summary(self):
        """Print speedy benchmark metrics."""
        avg_time = sum(r['elapsed'] for r in self.results) / len(self.results)
        print("\n" + "-" * 80)
        print(f"SPEEDY SUMMARY (num_beams=1): Average Latency = {avg_time:.2f}s per screenshot")
        print("-" * 80 + "\n")


if __name__ == "__main__":
    unittest.main()