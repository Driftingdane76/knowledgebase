# Q&A Knowledgebase: Setup Guide
**Target Audience: Backend/Fullstack Developers**

---

## Developer Setup

### 1. Environment Requirements
- **Python**: 3.10+ (Tested on 3.11)
- **PostgreSQL**: 13+
  - **CRITICAL:** The `pg_trgm` extension must be enabled on your database for the search `GinIndex` to function. The application database user does *not* have (or require) superuser privileges, so a database administrator must run `CREATE EXTENSION IF NOT EXISTS pg_trgm;` on the target database before you run migrations.
- **Local OCR Engine**: Microsoft Florence-2 (`microsoft/Florence-2-base`) runs 100% locally via PyTorch & Transformers with zero external cloud API dependencies or cloud egress.

### 2. Local Environment (`.env`)
Create a `.env` file in the project root. Make sure to replace the dummy values with your actual local database credentials.
```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=my_database_name
DB_USER=my_database_user
DB_PASSWORD=my_secure_password
DB_HOST=127.0.0.1
DB_PORT=5432

SECRET_KEY=dev-secret-key-change-in-prod
DEBUG=True
ALLOWED_HOSTS=*
# Controls the IPWhitelistMiddleware (Comma separated list of allowed IPs)
ALLOWED_TESTER_IPS=127.0.0.1
# Optional: Florence-2 model identifier (defaults to microsoft/Florence-2-base)
FLORENCE_MODEL_ID=microsoft/Florence-2-base
```

### 3. Bootstrap & Run
```bash
# Setup venv
python -m venv .venv
.venv\Scripts\activate.bat  # Windows CMD

# Dependencies (Installs Django 5.2, PyTorch, Transformers, and Florence-2 dependencies)
pip install -r requirements.txt

# DB Init (Will fail if pg_trgm is not active on the DB!)
python manage.py makemigrations
python manage.py migrate

# Auth Setup
python manage.py createsuperuser

# Boot
python manage.py runserver
```

### 4. Testing
Run tests via Windows Command Prompt (`cmd.exe`):
```cmd
:: Standalone OCR Transposition & Fuzzy CPR Test Suite
.venv\Scripts\python.exe test_ocr_transposition.py

:: Standalone CPR Human Error & Typo Redaction Suite
.venv\Scripts\python.exe test_cpr_human_error.py

:: Full Django 5.2 Unit Test Suite (Including Edge Cases)
.venv\Scripts\python.exe manage.py test qa_app.tests qa_app.test_redaction_engine qa_app.test_edge_cases users

:: Full Visual Florence-2 OCR Test
.venv\Scripts\python.exe test_florence_ocr.py
```
