import os
from playwright.sync_api import sync_playwright

def render():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    p_in = os.path.join(base_dir, 'test_htmls', 'mock_crm_dashboard.html')
    p_out = os.path.join(base_dir, 'test_htmls', 'mock_crm_dashboard.png')
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1280, 'height': 1024})
        page.goto(f'file:///{p_in.replace(os.sep, "/")}')
        page.wait_for_timeout(500)
        page.screenshot(path=p_out, full_page=True)
        browser.close()
        print(f"Screenshot successfully saved to: {p_out}")

if __name__ == '__main__':
    render()
