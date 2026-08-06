import os
import sys
import io
from PIL import Image
from playwright.sync_api import sync_playwright

# Ensure project root is in path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from test_htmls.dynamic_mock_generator import generate_dynamic_html_snippet, LAYOUT_BUILDERS
from qa_app.florence_ocr import run_florence_ocr_and_redact

def test_dynamic_generation_and_redaction():
    print("=" * 70)
    print("TESTING DYNAMIC MOCK GENERATION & OCR REDACTION PIPELINE")
    print("=" * 70)
    
    test_output_dir = os.path.join(BASE_DIR, "test_htmls", "sample_dynamic_output")
    os.makedirs(test_output_dir, exist_ok=True)
    
    print(f"Testing {len(LAYOUT_BUILDERS)} distinct layout generators...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(device_scale_factor=2)
        
        for idx in range(len(LAYOUT_BUILDERS)):
            html = generate_dynamic_html_snippet(idx)
            page.set_content(html)
            page.wait_for_timeout(200)
            
            target = page.locator(".snippet-capture-target")
            screenshot_bytes = target.screenshot()
            
            img = Image.open(io.BytesIO(screenshot_bytes))
            sample_path = os.path.join(test_output_dir, f"dynamic_sample_{idx+1}_original.png")
            img.save(sample_path)
            
            print(f"\n[Layout {idx+1}] Rendered screenshot -> {sample_path}")
            
            # Run Florence-2 OCR + Redaction
            redacted_text, ocr_data = run_florence_ocr_and_redact(img)
            
            redacted_img_path = os.path.join(test_output_dir, f"dynamic_sample_{idx+1}_redacted.png")
            img.save(redacted_img_path)
            print(f"  -> Saved Redacted Image -> {redacted_img_path}")
            print(f"  -> Redacted Text Preview:  {redacted_text[:120].strip()}...")
            
            # Verify no unredacted CPR remains in the redacted text
            cpr_matches = [w for w in redacted_text.split() if "-" in w and len(w) == 11 and w[:6].isdigit() and w[7:].isdigit()]
            if cpr_matches:
                print(f"  ❌ FAILED: Found unredacted CPR in output text: {cpr_matches}")
                browser.close()
                return False
            else:
                print("  ✓ All CPR numbers successfully redacted!")
                
        browser.close()
        
    print("\n" + "=" * 70)
    print("ALL DYNAMIC LAYOUTS RENDERED & OCR REDACTION VERIFIED 100%!")
    print("=" * 70)
    return True

if __name__ == '__main__':
    success = test_dynamic_generation_and_redaction()
    if not success:
        sys.exit(1)
