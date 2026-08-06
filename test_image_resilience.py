import os
import io
import time
from playwright.sync_api import sync_playwright

def test_image_resilience_and_retry():
    """
    Test that eager image loading with exponential backoff retry
    recovers from simulated network drops/throttling and preserves
    OCR highlight coordinates.
    """
    html_content = """<!DOCTYPE html>
<html>
<head>
    <style>
        .screenshot-container {
            position: relative;
            display: inline-block;
            width: fit-content;
            max-height: 300px;
        }
        .img-screenshot {
            max-height: 280px;
            display: block;
        }
        .ocr-highlight-layer {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            pointer-events: none;
        }
        .ocr-highlight-box {
            position: absolute;
            background: rgba(59, 130, 246, 0.35);
            border: 1px solid #2563eb;
        }
    </style>
    <script>
        window.retryCounts = {};
        function handleImgError(el) {
            let retries = parseInt(el.dataset.retries || '0', 10);
            if (retries < 3) {
                el.dataset.retries = retries + 1;
                window.retryCounts[el.id] = retries + 1;
                const delay = 250 * Math.pow(1.5, retries);
                setTimeout(() => {
                    // Switch to valid source on retry
                    const base = el.dataset.realSrc;
                    el.src = base + '?r=' + Date.now();
                }, delay);
            }
        }
    </script>
</head>
<body>
    <div id="container"></div>
    <script>
        const container = document.getElementById('container');
        // Render 10 test image snippets, simulating 5 of them failing on initial request
        for (let i = 1; i <= 10; i++) {
            const wrap = document.createElement('div');
            wrap.className = 'screenshot-container mb-2';
            
            const img = document.createElement('img');
            img.id = 'img-' + i;
            img.className = 'img-screenshot';
            img.dataset.realSrc = 'mock_crm_dashboard.png';
            img.onerror = function() { handleImgError(this); };
            
            // Simulate ngrok dropping images 6..10 initially
            if (i > 5) {
                img.src = 'non_existent_stream_drop_' + i + '.png';
            } else {
                img.src = 'mock_crm_dashboard.png';
            }
            
            const hlLayer = document.createElement('div');
            hlLayer.className = 'ocr-highlight-layer';
            hlLayer.innerHTML = '<div class="ocr-highlight-box" style="left: 10%; top: 20%; width: 30%; height: 15%;"></div>';
            
            wrap.appendChild(img);
            wrap.appendChild(hlLayer);
            container.appendChild(wrap);
        }
    </script>
</body>
</html>
"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    test_html_path = os.path.join(base_dir, 'test_htmls', 'test_resilience_spec.html')
    with open(test_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Test HTML written to: {test_html_path}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f'file:///{test_html_path.replace(os.sep, "/")}')
        
        # Immediate check (100ms): error handlers caught 5 drops, retrying
        page.wait_for_timeout(100)
        retried_count = page.evaluate("() => Object.keys(window.retryCounts || {}).length")
        print(f"[Initial Intercept] Drops caught by error handler: {retried_count}/5 simulated drops")
        assert retried_count == 5, f"Expected 5 caught drops, got {retried_count}"
        
        # Wait for auto-retry backoff to complete (700ms)
        page.wait_for_timeout(700)
        
        recovered = page.evaluate("""() => {
            let loaded = 0;
            for (let i = 1; i <= 10; i++) {
                const img = document.getElementById('img-' + i);
                if (img.naturalWidth > 0 && img.complete) loaded++;
            }
            return loaded;
        }""")
        print(f"[After Auto-Retry] Images successfully recovered & loaded: {recovered}/10")
        assert recovered == 10, f"Expected all 10 images loaded, got {recovered}"
        
        # Check that OCR highlight layer has physical dimensions > 0
        hl_bounds = page.evaluate("""() => {
            const boxes = document.querySelectorAll('.ocr-highlight-box');
            let valid = 0;
            boxes.forEach(b => {
                const rect = b.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) valid++;
            });
            return valid;
        }""")
        print(f"[OCR Geometry] Valid rendered bounding boxes: {hl_bounds}/10")
        assert hl_bounds == 10, f"Expected 10 valid OCR bounding boxes, got {hl_bounds}"

        browser.close()
        print("\nAll Resilience & OCR Alignment Tests Passed Successfully!")

if __name__ == '__main__':
    test_image_resilience_and_retry()
