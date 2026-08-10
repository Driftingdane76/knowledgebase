import os
from playwright.sync_api import sync_playwright

def main():
    artifact_dir = r"C:\Users\Driftingdane\.gemini\antigravity-ide\brain\8a5cca2e-eaeb-49eb-a5aa-98f42bb990cc"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        print("Navigating to test page...")
        page.goto("http://127.0.0.1:8000/test/highlight-precision/")
        page.wait_for_selector("#search-input", timeout=10000)
        
        # Test 1: Substring match "udbetal" (should match inside udbetalingen)
        print("Testing substring 'udbetal'...")
        page.fill("#search-input", "udbetal")
        page.wait_for_timeout(2000)  # Wait for fetch and render
        page.screenshot(path=os.path.join(artifact_dir, "proof_udbetal_substring.png"))
        
        # Test 2: Multi-word phrase that might be in the text, e.g., "hvordan udbetaler"
        # Or let's test a common word like "kan" or "ikke"
        print("Testing exact phrase 'kan ikke'...")
        page.fill("#search-input", "")
        page.wait_for_timeout(500)
        page.fill("#search-input", "kan ikke")
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(artifact_dir, "proof_kan_ikke_phrase.png"))

        browser.close()

if __name__ == "__main__":
    main()
