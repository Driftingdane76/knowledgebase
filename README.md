# Q&A Knowledgebase App (Django & PostgreSQL)

This is a full-stack Django 5 application backed by PostgreSQL for managing an internal Q&A Knowledgebase. It features full-text trigram searching with GIN indexes, inline click-to-edit cells, base64 image pasting with OCR text extraction & automated local PII redaction, strict security middleware, and a responsive Bootstrap dark/light theme.

---

## Key Architecture & Components

### 1. Models, Database & Background Signals (`qa_app/models.py`, `qa_app/signals.py`)
- **KnowledgePage**: The core entity storing questions, resolutions, categories, and tags. Indexed with PostgreSQL `GinIndex` trigrams (`pg_trgm`) for high-performance full-text searching.
- **PageImage**: Stores screenshots attached to Knowledge Pages. Contains `extracted_text` and `ocr_data` fields used for search indexing and displaying UI highlights. A background `post_delete` signal automatically deletes physical files from disk upon deletion.
- **Category & Tag**: Used for organization. Tags are dynamically extracted from content using word-boundary regex rules.

### 2. Search Engine (`qa_app/views.py -> search_pages`)
- Server-side search with sorting and pagination.
- Leverages Trigram GIN indexes (`pg_trgm`) to quickly match queries across multiple fields (`username`, `question_text`, `resolution_text`, `title`, and `date`).

### 3. Local OCR & PII Redaction Pipeline (`qa_app/views.py`, `qa_app/florence_ocr.py`, `qa_app/redaction.py`)
- **OCR Engine**: 100% self-hosted, local OCR using Microsoft Florence-2 (`microsoft/Florence-2-base`) with zero external cloud egress.
- **Local Regex & Spatial Redaction**: Utilizes `qa_app/redaction.py` to scan extracted text and visual coordinates for sensitive Danish CPR numbers and Bank account info while preserving valid names.
- **Edge-Case Resilience**:
  - **Cross-Line Word-Wrapping**: Global character-to-token span mapping (`char_to_word_idx`) detects and redacts 10-digit CPRs even when split across line breaks in chat/free-text bubbles.
  - **Punctuation & Token Boundaries**: Character interval intersection cleanly masks tokens with trailing punctuation (e.g. `5350.`).
  - **Multi-Row Table Geometry**: Column X-span alignment tracks vertical table columns (e.g. `CPR-NUMMER`) regardless of table row depth.
- **Visual Masking**: When sensitive data is found, Pillow (`ImageDraw`) draws solid black redaction boxes directly onto the image coordinates before saving as WEBP.

### 4. Security & Administration (`users/views.py`, `core/middleware.py`, `qa_app/admin.py`)
- **IP Whitelisting**: `IPWhitelistMiddleware` restricts application access using the `ALLOWED_TESTER_IPS` setting.
- **Login Rate Limiting**: `CustomLoginView` tracks `LoginAttempt` records, blocking IP addresses after 5 failed attempts within 15 minutes.
- **Admin Tag Backfilling**: Admin view (`run_backfill_view`) enables retroactively tagging older documents via `backfill_all_tags`.
### 4. Background Processing & Task Queues ( `core/celery.py` , `qa_app/tasks.py` )

- **Celery & Redis Architecture**: Image OCR and PII redaction offloaded to background workers, returning fast (`<100ms`) HTTP responses.
- **Dual-Queue Isolation**:
  - **Default Queue**: `default` queue handles lightweight general application tasks.
  - **OCR Queue**: `ocr` queue dedicated solely to Microsoft Florence-2 inference and PII masking, running with bounded concurrency (`-c 1`) to prevent GPU/CPU starvation.
- **State Tracking**: `PageImage.ocr_status` (`pending`, `processing`, `completed`, `failed`) and `ocr_error` provide real-time status and error diagnostics directly in Django Admin.

---

## Directory Structure
- [core/](file:///d:/knowledgebase/core) - Core Django project configuration (`settings.py`, `urls.py`, `middleware.py`, etc.).
- [qa_app/](file:///d:/knowledgebase/qa_app) - Main Q&A knowledgebase app (views, models, OCR/redaction engine, templates).
- [users/](file:///d:/knowledgebase/users) - User management and rate-limited authentication.
- [templates/](file:///d:/knowledgebase/templates) - Global HTML templates.
- [static/](file:///d:/knowledgebase/static) - Custom CSS styles, JavaScript, and UI assets.
- [locale/](file:///d:/knowledgebase/locale) - Internationalization files (`da` / `en`).
- [requirements.txt](file:///d:/knowledgebase/requirements.txt) - Python package dependencies.
- [manage.py](file:///d:/knowledgebase/manage.py) - Django CLI entry point script.

---

## Prerequisites & Setup

- **Python 3.10+** (verified on Python 3.11)
- **PostgreSQL 13+** with the `pg_trgm` extension enabled (`CREATE EXTENSION IF NOT EXISTS pg_trgm;`)
- **Local Microsoft Florence-2** dependencies (`torch`, `transformers<=4.47.1`, `timm`, `einops`)
- **Redis 6+** — Required as the Celery message broker and result backend for background OCR task queuing (`redis://localhost:6379`).

### Quick Start (Windows Command Prompt)

1. **Virtual Environment & Dependencies:**
   ```cmd
   python -m venv .venv
   .venv\Scripts\activate.bat
   pip install -r requirements.txt
   ```

2. **Database Migrations:**
   ```cmd
   python manage.py migrate
   ```

3. **Run Development Server:**
   ```cmd
   python manage.py runserver
   ```

4. **Start the Celery Worker (Background OCR — run in a separate terminal):**
   ```cmd
   .venv\Scripts\celery.exe -A core worker -Q default,ocr -c 1 --loglevel=INFO
   ```
   > Redis must be running locally on `redis://localhost:6379` before starting the worker.

5. **Access the Application:**
   Open `http://127.0.0.1:8000/` in your browser.

---

## Testing & Validation Suites

Execute the test suites in Windows Command Prompt (`cmd.exe`) via the local virtual environment:

```cmd
:: 1. Bank Redaction Precision & False-Positive Guardrails
.venv\Scripts\python.exe test_bank_redaction_precision.py

:: 2. Dynamic 8-Layout Generation & Florence-2 OCR Redaction
.venv\Scripts\python.exe test_dynamic_pipeline.py

:: 3. 50 Distinct Generation Uniqueness & Redaction Audit
.venv\Scripts\python.exe test_50_distinct_generations.py

:: 4. Core CPR / Bank Unit Tests
.venv\Scripts\python.exe test_cpr_bank_redaction_suite.py

:: 5. Security & Rate Limiting Middleware Tests
.venv\Scripts\python.exe test_security_settings.py
```
