import os
import io
import django
from PIL import Image
from playwright.sync_api import sync_playwright

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from qa_app.views import extract_text_from_image

def run_preview():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(base_dir, 'test_htmls', 'mock_edge_cases.html')
    
    if not os.path.exists(html_path):
        print(f"Error: {html_path} not found.")
        return

    cases = [
        {
            "id": 1,
            "name": "Cross-Line CPR Wrap",
            "selector": "#case-wrap",
            "output_img": "preview_edge_case_1_wrap_redacted.png",
            "expected_pii": ["260353", "9773"],
            "expected_preserved": ["Morten Noerregaard"]
        },
        {
            "id": 2,
            "name": "Competing Keyword with CPR Label",
            "selector": "#case-competing",
            "output_img": "preview_edge_case_2_competing_redacted.png",
            "expected_pii": ["041156-5350"],
            "expected_preserved": ["Lars Jensen"]
        },
        {
            "id": 3,
            "name": "Multi-Row Table Column Alignment",
            "selector": "#case-table",
            "output_img": "preview_edge_case_3_table_redacted.png",
            "expected_pii": ["010203-4567", "081184 6027", "1234567890", "5432109876"],
            "expected_preserved": ["Sofie Petersen", "Mette Frederiksen"]
        }
    ]

    print("=" * 70)
    print("STARTING 3-CASE EDGE CASE REDACTION PREVIEW")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 1024})
        page.goto(f'file:///{html_path.replace(os.sep, "/")}')
        page.wait_for_timeout(500)

        for case in cases:
            print(f"\n[Case {case['id']}] {case['name']}...")
            element = page.locator(case['selector'])
            
            # Take clean bounding box screenshot
            screenshot_bytes = element.screenshot()
            img = Image.open(io.BytesIO(screenshot_bytes)).convert("RGB")
            
            # Run local Florence-2 OCR and visual redaction
            extracted_text, ocr_data = extract_text_from_image(img)
            
            # Save redacted visual artifact
            out_path = os.path.join(base_dir, 'test_htmls', case['output_img'])
            img.save(out_path, format="PNG")
            
            redacted_words = [d['text'] for d in ocr_data if d.get('redacted')]
            print(f"  -> Extracted Text Snippet: {extracted_text[:90]}...")
            print(f"  -> Redacted Words Count: {len(redacted_words)} ({', '.join(redacted_words)})")
            print(f"  -> Visual Artifact Saved: {case['output_img']}")

        browser.close()

    print("\n" + "=" * 70)
    print("PREVIEW COMPLETE: All 3 visual artifacts saved to test_htmls/")
    print("=" * 70)

if __name__ == '__main__':
    run_preview()
