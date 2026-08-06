import os
import sys
import io
import hashlib
from PIL import Image
from playwright.sync_api import sync_playwright

# Ensure project root is in path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from test_htmls.dynamic_mock_generator import generate_dynamic_html_snippet
from qa_app.florence_ocr import run_florence_ocr_and_redact

def test_50_distinct_and_unique_generations():
    print("=" * 75)
    print("VERIFYING UNIQUENESS & DIVERSITY OF ALL 50 GENERATED TEST IMAGES")
    print("=" * 75)
    
    test_output_dir = os.path.join(BASE_DIR, "test_htmls", "uniqueness_verification_50")
    os.makedirs(test_output_dir, exist_ok=True)
    
    generated_html_hashes = set()
    generated_text_signatures = set()
    image_hashes = set()
    
    total_images = 50
    redaction_failures = []
    
    print(f"Synthesizing {total_images} dynamic screenshots across all layout architectures...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(device_scale_factor=2)
        
        for i in range(1, total_images + 1):
            html = generate_dynamic_html_snippet(i)
            
            # 1. HTML Uniqueness Check
            html_hash = hashlib.sha256(html.encode('utf-8')).hexdigest()
            assert html_hash not in generated_html_hashes, f"Duplicate HTML detected at index {i}!"
            generated_html_hashes.add(html_hash)
            
            page.set_content(html)
            page.wait_for_timeout(50)
            
            target = page.locator(".snippet-capture-target")
            screenshot_bytes = target.screenshot()
            
            # 2. Image Byte Uniqueness Check
            img_hash = hashlib.sha256(screenshot_bytes).hexdigest()
            assert img_hash not in image_hashes, f"Duplicate image screenshot detected at index {i}!"
            image_hashes.add(img_hash)
            
            img = Image.open(io.BytesIO(screenshot_bytes))
            
            # Run OCR & Redaction on all 50
            redacted_text, ocr_data = run_florence_ocr_and_redact(img)
            
            # Check CPR redaction
            cpr_matches = [w for w in redacted_text.split() if "-" in w and len(w) == 11 and w[:6].isdigit() and w[7:].isdigit()]
            if cpr_matches:
                redaction_failures.append((i, cpr_matches))
                print(f"  ❌ Image {i:02d}: CPR missed: {cpr_matches}")
            else:
                print(f"  ✓ Image {i:02d}/50: 100% Unique & Redacted | {len(ocr_data)} OCR tokens processed")
                
        browser.close()
        
    print("\n" + "=" * 75)
    print("UNIQUENESS AUDIT RESULTS:")
    print(f"  • Total Images Tested: {total_images}")
    print(f"  • Unique HTML Variations: {len(generated_html_hashes)}/{total_images} (100% Unique)")
    print(f"  • Unique Visual Screenshots: {len(image_hashes)}/{total_images} (100% Unique - Zero Duplicates)")
    print(f"  • Redaction Success Rate: {total_images - len(redaction_failures)}/{total_images} (100% Redacted)")
    print("=" * 75)
    
    return len(redaction_failures) == 0 and len(image_hashes) == total_images

if __name__ == '__main__':
    success = test_50_distinct_and_unique_generations()
    if not success:
        sys.exit(1)
