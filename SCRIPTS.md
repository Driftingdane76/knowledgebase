# Root Scripts Reference

Complete inventory of all root-level scripts. Run all Python commands in **cmd.exe** using the local venv:
`.venv\Scripts\python.exe <script>`

---

## Operational Scripts

| Script | Purpose | Command |
|---|---|---|
| `run.bat` | Starts the Django dev server using the local `.venv`. Shorthand for `manage.py runserver`. | `run.bat` |
| `manage.py` | Standard Django management entry point. | `.venv\Scripts\python.exe manage.py <command>` |
| `seed_from_mock.py` | **Primary data loader.** Clears the DB, generates N dynamic mock UI screenshots via Playwright, runs Florence-2 OCR + PII redaction on each, and seeds everything into the Django DB. Use `--count` to set how many records to generate (default: 50). | `.venv\Scripts\python.exe seed_from_mock.py --count 10` |
| `backfill_tags.py` | Retroactively applies tag extraction logic to all existing `KnowledgePage` DB records. Run after updating tag rules. | `.venv\Scripts\python.exe backfill_tags.py` |
| `create_db.py` | One-time setup. Creates the PostgreSQL database using credentials from `.env`. Only needed on fresh environments. | `.venv\Scripts\python.exe create_db.py` |
| `export_to_sqlite.py` | Exports the PostgreSQL DB to a portable SQLite file. Useful for offline snapshots or sharing without a Postgres server. | `.venv\Scripts\python.exe export_to_sqlite.py` |

---

## Test and Verification Scripts

> Core test scripts are also documented in DEV_INFO.md and README.md.

| Script | Purpose | Command |
|---|---|---|
| `test_bank_redaction_precision.py` | Tests true-positive redaction of Danish IBAN, NemKonto, and line-wrapped bank numbers. Also verifies false-positive guards on CVR, Case IDs, Policy numbers, DKK currency, and postal codes. | `.venv\Scripts\python.exe test_bank_redaction_precision.py` |
| `test_dynamic_pipeline.py` | Renders 8 UI mockup layouts via Playwright, runs Florence-2 OCR + redaction, and verifies all CPR numbers are redacted. Saves PNG artifacts to `test_htmls/sample_dynamic_output/`. Does NOT touch the DB. | `.venv\Scripts\python.exe test_dynamic_pipeline.py` |
| `test_distinct_generations.py` | Renders N randomized screenshots and runs SHA-256 hash checks on HTML and image bytes to ensure zero duplicates. Validates 100% CPR + bank redaction. | `.venv\Scripts\python.exe test_distinct_generations.py` |
| `test_cpr_bank_redaction_suite.py` | Unit test suite for Danish CPR validation algorithms (DDMMYY-XXXX), date validity checking, and spatial token matching. | `.venv\Scripts\python.exe test_cpr_bank_redaction_suite.py` |
| `test_cpr_human_error.py` | Tests redaction resilience against human entry errors in CPR formatting (missing hyphen, extra spaces, etc.). | `.venv\Scripts\python.exe test_cpr_human_error.py` |
| `test_security_settings.py` | Verifies Django security settings, IP whitelisting middleware, and failed login attempt rate-limiting. | `.venv\Scripts\python.exe test_security_settings.py` |
| `test_florence_ocr.py` | Unit tests for the Florence-2 OCR pipeline using synthetic PIL images to verify text extraction accuracy. | `.venv\Scripts\python.exe test_florence_ocr.py` |
| `test_florence_deep_dive.py` | Deep diagnostic suite for Florence-2. Tests complex layouts, multi-column text, and edge-case fonts. | `.venv\Scripts\python.exe test_florence_deep_dive.py` |
| `test_highlight_logic.py` | Pure Python unit tests for the highlightMatch JS logic (ported to Python). Verifies phrase-exact substring matching and HTML escaping. | `.venv\Scripts\python.exe test_highlight_logic.py` |
| `test_image_resilience.py` | Stress tests the OCR pipeline against images with extreme contrast, noise, rotation, and compression artifacts. | `.venv\Scripts\python.exe test_image_resilience.py` |
| `test_ocr_transposition.py` | Tests redaction against transposed/fuzzy CPR formats that OCR commonly misreads (e.g. O vs 0, l vs 1). | `.venv\Scripts\python.exe test_ocr_transposition.py` |
| `test_asset_versioning_and_css.py` | Verifies that static asset versioning is applied and that key CSS classes exist in `app.css`. | `.venv\Scripts\python.exe test_asset_versioning_and_css.py` |
| `test_tags_mock_distribution.py` | Seeds mock data and verifies that tag extraction produces a realistic distribution (no single tag dominates). | `.venv\Scripts\python.exe test_tags_mock_distribution.py` |
| `test_env_precedence.py` | Verifies that `.env` settings load correctly and production overrides take precedence over defaults. | `.venv\Scripts\python.exe test_env_precedence.py` |
| `test_azure_settings.py` | Validates Azure Blob Storage settings, connection strings, and Django DEFAULT_FILE_STORAGE config. | `.venv\Scripts\python.exe test_azure_settings.py` |
| `test_deployment_api_routes.py` | Tests that all expected API routes (/api/search, /api/db, etc.) exist and return correct status codes. | `.venv\Scripts\python.exe test_deployment_api_routes.py` |
| `test_deployment_archive.py` | Validates the deployment ZIP archive: checks required files are present and no dev-only secrets are bundled. | `.venv\Scripts\python.exe test_deployment_archive.py` |
| `test_sqlite_fallback.py` | Verifies the app starts correctly with a SQLite fallback when PostgreSQL is unavailable. | `.venv\Scripts\python.exe test_sqlite_fallback.py` |
| `test_inspect_images.py` | Django-aware diagnostic: queries the DB and inspects PageImage records for missing files, corrupt OCR data, or empty extracted_text. | `.venv\Scripts\python.exe test_inspect_images.py` |
| `test_inspect_tokens.py` | Low-level diagnostic: loads Florence-2 tokenizer directly and inspects token outputs for a given image. Used for debugging OCR misreads. | `.venv\Scripts\python.exe test_inspect_tokens.py` |
| `test_quick_seed_preview.py` | Runs a small 3-case edge-case redaction preview using `test_htmls/mock_edge_cases.html`. Faster than the full pipeline for quick spot checks. | `.venv\Scripts\python.exe test_quick_seed_preview.py` |

---

## Document Generation Scripts

| Script | Purpose | Command |
|---|---|---|
| `generate_pdf_guide.py` | Generates `Azure_Deployment_Guide_2026.pdf` from source content. Re-run after updating deployment steps. | `.venv\Scripts\python.exe generate_pdf_guide.py` |
| `build_pdf_binary.py` | Lower-level PDF builder used internally by `generate_pdf_guide.py`. Handles binary encoding and layout assembly. | Called internally — not run directly. |
| `generate_pitch.py` | Generates a PowerPoint pitch deck (.pptx) using python-pptx. | `.venv\Scripts\python.exe generate_pitch.py` |

---

## Diagnostic and Dev Tools

| Script | Purpose | Command |
|---|---|---|
| `proof.py` | Playwright-based visual proof tool. Takes a screenshot of a specific page or element for quick visual verification. | `.venv\Scripts\python.exe proof.py` |
| `render_mock.py` | Renders a single mock HTML snippet to a PNG screenshot via Playwright. Lightweight alternative to the full seeding pipeline. | `.venv\Scripts\python.exe render_mock.py` |
| `diagnose_deployment_pipeline.py` | Inspects the deployment ZIP, checks Azure settings, validates API routes, and produces a full diagnostic report. | `.venv\Scripts\python.exe diagnose_deployment_pipeline.py` |

---

## Deprecated (Safe to Ignore)

| Script | Status |
|---|---|
| `cleanup_deprecated.py` | Emptied. Was a one-off cleanup script, no longer needed. |
| `scratch_fetch_html.py` | Emptied. Was a dev scratch tool, superseded. |
| `test_50_distinct_generations.py` | Emptied. Superseded by `test_distinct_generations.py`. |
