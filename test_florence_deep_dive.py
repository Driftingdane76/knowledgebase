import os
import sys
import io
import json
from PIL import Image
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from qa_app.florence_ocr import run_florence_ocr_and_redact, get_florence_model

def run_florence_deep_dive():
    print("=" * 70)
    print("RUNNING FLORENCE-2 OCR DEEP DIVE & SCREENSHOT TEST")
    print("=" * 70)

    output_dir = os.path.join(BASE_DIR, "test_htmls", "florence_deep_dive")
    os.makedirs(output_dir, exist_ok=True)

    # 1. HTML Snippet to render and screenshot
    test_html = """<!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body { margin: 0; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; }
            .card { background: #1e293b; border-radius: 8px; border: 1px solid #334155; padding: 18px; width: 650px; color: #f8fafc; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
            .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 12px; margin-bottom: 14px; font-size: 15px; font-weight: 600; }
            .badge { background: #f59e0b; color: #000; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
            .row-item { margin-bottom: 10px; font-size: 13.5px; color: #cbd5e1; }
            .row-item strong { color: #f8fafc; }
            .chat-bubble { background: #312e81; border-radius: 6px; padding: 12px; margin-top: 14px; font-size: 13px; color: #e0e7ff; }
        </style>
    </head>
    <body>
        <div class="card" id="target-capture">
            <div class="header">
                <span>Support Sag #88648 - Mere end 100 resultater</span>
                <span class="badge">Afventer</span>
            </div>
            <div class="row-item">
                <span>Kunde: <strong>Lars Nielsen</strong> &bull; CPR: <strong>041156-5350</strong></span>
            </div>
            <div class="row-item">
                <span>Betalingsoplysninger: <strong>Reg: 7821 Konto: 9806263564</strong></span>
            </div>
            <div class="row-item">
                <span>Systembesked: <strong>Advarsel: Mere end 100 resultater fundet i batch</strong></span>
            </div>
            <div class="chat-bubble">
                <strong>Freja Petersen (Kundeservice):</strong><br>
                Mange tak Lars. Jeg har undersøgt sagen vedr. 'Mere end 100 resultater' og 'Advarsel' og registreret dine oplysninger.
            </div>
        </div>
    </body>
    </html>
    """

    screenshot_path = os.path.join(output_dir, "florence_source_screenshot.png")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(device_scale_factor=2)
        page.set_content(test_html)
        page.wait_for_timeout(300)
        target = page.locator("#target-capture")
        target.screenshot(path=screenshot_path)
        browser.close()

    print(f"[Step 1] Source screenshot captured: {screenshot_path}")

    # 2. Run Florence-2 OCR
    img = Image.open(screenshot_path)
    redacted_text, ocr_words = run_florence_ocr_and_redact(img)

    redacted_path = os.path.join(output_dir, "florence_redacted_screenshot.png")
    img.save(redacted_path)
    print(f"[Step 2] Florence-2 Redacted Screenshot saved: {redacted_path}")
    print(f"[Step 3] Florence-2 Extracted Tokens ({len(ocr_words)} regions):")
    for idx, w in enumerate(ocr_words):
        print(f"   [{idx}] '{w['text']}' -> Left: {w['left']}%, Top: {w['top']}%, W: {w['width']}%, H: {w['height']}%")

    # 3. Generate HTML Visual Deep Dive Report
    report_path = os.path.join(BASE_DIR, "test_florence_deep_dive_report.html")
    
    html_report = f"""<!DOCTYPE html>
    <html lang="da">
    <head>
        <meta charset="utf-8">
        <title>Florence-2 Deep Dive Test Report</title>
        <link rel="stylesheet" href="static/css/bootstrap/bootstrap.min.css">
        <link rel="stylesheet" href="static/css/fontawesome/all.min.css">
        <link rel="stylesheet" href="static/css/app.css">
        <style>
            body {{ background-color: #0f172a; color: #f8fafc; padding: 24px; font-family: 'Inter', sans-serif; }}
            .panel {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
            .img-wrap {{ position: relative; display: inline-block; width: 100%; border: 1px solid #475569; border-radius: 6px; overflow: hidden; }}
            .img-wrap img {{ width: 100%; display: block; }}
            .ocr-orig {{ position: absolute; background-color: #fde047; mix-blend-mode: multiply; outline: 1.5px solid #ca8a04; border-radius: 2px; pointer-events: none; }}
            .ocr-weighted {{ position: absolute; background-color: rgba(254, 240, 138, 0.70); border: 1px solid #eab308; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.15); pointer-events: none; }}
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <h3 class="fw-bold mb-3"><i class="fa-solid fa-microchip text-primary me-2"></i>Florence-2 OCR Deep Dive Verification Report</h3>
            
            <div class="panel">
                <h5 class="fw-bold mb-3">Extracted Florence-2 OCR Tokens from Generated Screenshot</h5>
                <div class="table-responsive">
                    <table class="table table-dark table-sm table-bordered">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Detected Text Label</th>
                                <th>Left %</th>
                                <th>Top %</th>
                                <th>Width %</th>
                                <th>Height %</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join([f"<tr><td>{i}</td><td><code>{w['text']}</code></td><td>{w['left']}%</td><td>{w['top']}%</td><td>{w['width']}%</td><td>{w['height']}%</td></tr>" for i, w in enumerate(ocr_words)])}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="panel">
                <h5 class="fw-bold mb-3">Highlight Comparison: Query = "Mere end 100 resultater"</h5>
                <div class="row g-4">
                    <div class="col-md-6">
                        <div class="p-3 bg-dark rounded border border-danger">
                            <span class="fw-bold text-danger d-block mb-2"><i class="fa-solid fa-xmark me-1"></i>Original Linear Math (Clipped)</span>
                            <div class="img-wrap">
                                <img src="test_htmls/florence_deep_dive/florence_redacted_screenshot.png">
                                <div id="orig-layer" class="position-absolute top-0 start-0 w-100 h-100"></div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="p-3 bg-dark rounded border border-success">
                            <span class="fw-bold text-success d-block mb-2"><i class="fa-solid fa-check me-1"></i>Typographic Weighted Math (Exact Match)</span>
                            <div class="img-wrap">
                                <img src="test_htmls/florence_deep_dive/florence_redacted_screenshot.png">
                                <div id="weighted-layer" class="position-absolute top-0 start-0 w-100 h-100"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            const ocrData = {json.dumps(ocr_words)};
            const query = "Mere end 100 resultater";

            // Original Math
            function getOrigBoxes(data, q) {{
                const trimmed = q.trim().toLowerCase();
                const terms = trimmed.split(/\\s+/);
                const boxes = [];
                data.forEach(item => {{
                    const raw = item.text || '';
                    const lower = raw.toLowerCase();
                    const totalLen = raw.length || 1;
                    const targets = (trimmed.length > 2 && lower.includes(trimmed)) ? [trimmed] : terms;
                    targets.forEach(target => {{
                        let startIdx = 0;
                        while ((startIdx = lower.indexOf(target, startIdx)) !== -1) {{
                            const endIdx = startIdx + target.length;
                            const subLeft = item.left + (startIdx / totalLen) * item.width;
                            const subWidth = Math.max((target.length / totalLen) * item.width, 2);
                            boxes.push({{ left: subLeft, top: item.top, width: subWidth, height: item.height }});
                            startIdx = endIdx;
                        }}
                    }});
                }});
                return boxes;
            }}

            // Typographic Weighting Math
            function getCharWeight(ch) {{
                if (ch === ' ') return 0.30;
                if (/[-.,:;!?'"()\\[\\]\\/\\\\]/.test(ch)) return 0.32;
                if (/[0-9]/.test(ch)) return 0.55;
                if (/[iljtfr]/.test(ch)) return 0.38;
                if (/[MWmw@%ÆØÅ]/.test(ch)) return 0.95;
                if (/[A-Z]/.test(ch)) return 0.75;
                return 0.55;
            }}

            function calculateOffset(fullText, startIdx, matchLen) {{
                let total = 0;
                for (let i = 0; i < fullText.length; i++) total += getCharWeight(fullText[i]);
                if (total === 0) total = 1;
                let prefix = 0;
                for (let i = 0; i < startIdx; i++) prefix += getCharWeight(fullText[i]);
                let match = 0;
                for (let i = startIdx; i < startIdx + matchLen; i++) match += getCharWeight(fullText[i]);
                return {{ leftRatio: prefix / total, widthRatio: match / total }};
            }}

            function getWeightedBoxes(data, q) {{
                const trimmed = q.trim().toLowerCase();
                const terms = trimmed.split(/\\s+/);
                const boxes = [];
                data.forEach(item => {{
                    const raw = item.text || '';
                    const lower = raw.toLowerCase();
                    const targets = (trimmed.length > 2 && lower.includes(trimmed)) ? [trimmed] : terms;
                    targets.forEach(target => {{
                        let startIdx = 0;
                        while ((startIdx = lower.indexOf(target, startIdx)) !== -1) {{
                            const endIdx = startIdx + target.length;
                            const {{ leftRatio, widthRatio }} = calculateOffset(raw, startIdx, target.length);
                            const paddingPct = Math.min(item.width * 0.035, 1.8);
                            const calcLeft = item.left + (leftRatio * item.width);
                            const calcWidth = widthRatio * item.width;
                            const subLeft = Math.max(item.left, calcLeft - paddingPct);
                            const subWidth = Math.min(item.width, calcWidth + (2 * paddingPct));
                            boxes.push({{ left: subLeft, top: item.top - 0.3, width: Math.max(subWidth, 2), height: item.height + 0.6 }});
                            startIdx = endIdx;
                        }}
                    }});
                }});
                return boxes;
            }}

            const origBoxes = getOrigBoxes(ocrData, query);
            const weightedBoxes = getWeightedBoxes(ocrData, query);

            const origLayer = document.getElementById('orig-layer');
            origBoxes.forEach(b => {{
                const div = document.createElement('div');
                div.className = 'ocr-orig';
                div.style.left = b.left + '%';
                div.style.top = b.top + '%';
                div.style.width = b.width + '%';
                div.style.height = b.height + '%';
                origLayer.appendChild(div);
            }});

            const weightedLayer = document.getElementById('weighted-layer');
            weightedBoxes.forEach(b => {{
                const div = document.createElement('div');
                div.className = 'ocr-weighted';
                div.style.left = b.left + '%';
                div.style.top = b.top + '%';
                div.style.width = b.width + '%';
                div.style.height = b.height + '%';
                weightedLayer.appendChild(div);
            }});
        </script>
    </body>
    </html>
    """

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_report)

    print(f"[Step 4] Deep Dive HTML Report written: {report_path}")
    print("=" * 70)
    print("FLORENCE-2 DEEP DIVE TEST COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    run_florence_deep_dive()
