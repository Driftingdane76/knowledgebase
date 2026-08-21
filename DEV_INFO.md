# Developer Notes & Edge Cases

Quick notes on design choices and gotchas that aren't obvious at first glance.

### 🖼️ Why We Don't Use Image Lazy Loading
* **OCR Highlights**: Bounding boxes need the image's physical rendered size. Lazy loading collapses the image container to 0px, which breaks and distorts highlight overlays.
* **Search Navigation**: In-page search needs the exact vertical scroll positions of all 50 items right away to power the hit counter (`0/0`) and jump buttons.

### 🚇 ngrok Tunnel Testing Gotcha
* **Rate Limits**: ngrok Free limits traffic to 40 req/min and ~20 concurrent streams. Since all 50 thumbnails load eagerly at once, ngrok drops some images on the initial page load (which is why clicking the lightbox for a single image still works).
* **Fix**: Use [Cloudflare Tunnels](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) (`cloudflared tunnel --url http://127.0.0.1:8000`) for testing—it's free, has zero rate limits, and won't drop images.

### 🧪 Automated Testing & Verification Scripts

All testing scripts must be executed in Windows Command Prompt (`cmd.exe`) using the local virtual environment Python executable (`.venv\Scripts\python.exe`).

* **`test_bank_redaction_precision.py`**
  * **Purpose**: Tests true positive redaction of Danish IBAN, NemKonto, and line-wrapped bank numbers (`Reg.nr: ... \n Kontonr: ...`) while verifying false-positive guards on Danish CVR numbers, Case IDs, Policy numbers, DKK currency, and postal codes.
  * **Command**: `.venv\Scripts\python.exe test_bank_redaction_precision.py`

* **`test_dynamic_pipeline.py`**
  * **Purpose**: Synthesizes 8 distinct UI mockups (Guidewire PolicyCenter, Salesforce Customer 360, Support Chat, CRM Profile Card, ERP Refusionsblanket, Multi-Row Data Table, Email Client, and Case Notes) via Playwright, processes them through Microsoft Florence-2 OCR, and verifies visual & text redactions.
  * **Command**: `.venv\Scripts\python.exe test_dynamic_pipeline.py`

* **`test_50_distinct_generations.py`**
  * **Purpose**: Renders 50 randomized screenshots, executes SHA-256 cryptographic hash checks on both HTML code and visual image bytes to ensure zero duplicates across mockups, and validates 100% CPR & bank redaction.
  * **Command**: `.venv\Scripts\python.exe test_50_distinct_generations.py`

* **`test_cpr_bank_redaction_suite.py`**
  * **Purpose**: Unit test suite verifying Danish CPR validation algorithms (`DDMMYY-XXXX`), date validity checking (`strptime`), and spatial token matching.
  * **Command**: `.venv\Scripts\python.exe test_cpr_bank_redaction_suite.py`

* **`test_security_settings.py`**
  * **Purpose**: Verifies Django security settings, IP whitelisting middleware, and failed login attempt rate-limiting.
  * **Command**: `.venv\Scripts\python.exe test_security_settings.py`

### ⚙️ Celery / Redis Background OCR Gotchas

* **Redis must be running first**: The Django web server starts without Redis, but any image upload will fail silently at the OCR stage if the Celery worker is not connected to Redis. In development, start Redis before launching the worker.
* **Worker concurrency is intentionally 1** (`-c 1`): Florence-2 inference is CPU/GPU bound. Running more than one concurrent OCR task causes memory exhaustion. The `ocr` queue is isolated for this reason.
* **`transaction.on_commit()`**: OCR tasks are enqueued only *after* the DB transaction commits. This prevents a race condition where the Celery worker tries to load a `PageImage` row that does not yet exist.
* **`ocr_status` field on `PageImage`**: Images move through `pending → processing → completed / failed`. The Django Admin surfaces both `ocr_status` and `ocr_error` for real-time diagnostics without needing to read worker logs.
* **Flower Dashboard**: `flower>=2.0.0` is installed. Run `.venv\Scripts\celery.exe -A core flower` to open the real-time task monitor at `http://localhost:5555`.
