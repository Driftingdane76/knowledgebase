# Q\&A Knowledgebase: Setup Guide

**Target Audience: Backend/Fullstack Developers**

\---

## Developer Setup

### 1\. Environment Requirements

* **Python**: 3.10+ (Tested on 3.11)
* **PostgreSQL**: 13+

  * **CRITICAL:** The `pg\_trgm` extension must be enabled on your database for the search `GinIndex` to function. The application database user does *not* have (or require) superuser privileges, so a database administrator must run `CREATE EXTENSION IF NOT EXISTS pg\_trgm;` on the target database before you run migrations.
* **Local OCR Engine**: Microsoft Florence-2 (`microsoft/Florence-2-base`) runs 100% locally via PyTorch \& Transformers with zero external cloud API dependencies or cloud egress.
* **Redis 6+**: Required as the Celery broker and result backend for background OCR task queuing. Install locally (Windows: [Memurai](https://www.memurai.com/) or WSL2 Redis; Linux/macOS: `apt install redis-server` / `brew install redis`).

### 2\. Local Environment (`.env`)

Create a `.env` file in the project root. Make sure to replace the dummy values with your actual local database credentials.

```env
DB\_ENGINE=django.db.backends.postgresql
DB\_NAME=my\_database\_name
DB\_USER=my\_database\_user
DB\_PASSWORD=my\_secure\_password
DB\_HOST=127.0.0.1
DB\_PORT=5432

SECRET\_KEY=dev-secret-key-change-in-prod
DEBUG=True
ALLOWED\_HOSTS=\*
# Controls the IPWhitelistMiddleware (Comma separated list of allowed IPs)
ALLOWED\_TESTER\_IPS=127.0.0.1
# Optional: Florence-2 model identifier (defaults to microsoft/Florence-2-base)
FLORENCE\_MODEL\_ID=microsoft/Florence-2-base
# Celery / Redis (background OCR task queue)
CELERY\_BROKER\_URL=redis://localhost:6379/0
CELERY\_RESULT\_BACKEND=redis://localhost:6379/1
CACHE\_URL=redis://localhost:6379/2
```

### 3\. Bootstrap \& Run

```bash
# Setup venv
python -m venv .venv
.venv\\Scripts\\activate.bat  # Windows CMD

# Dependencies (Installs Django 5.2, PyTorch, Transformers, and Florence-2 dependencies)
pip install -r requirements.txt

# DB Init (Will fail if pg\_trgm is not active on the DB!)
python manage.py makemigrations
python manage.py migrate

# Auth Setup
python manage.py createsuperuser

# Boot
python manage.py runserver

# Background Worker (OCR queue — run in a separate terminal, Redis must be running first)
.venv\\Scripts\\celery.exe -A core worker -Q default,ocr -c 1 --loglevel=INFO
```

### 4\. Testing

Run tests via Windows Command Prompt (`cmd.exe`):

```cmd
:: Standalone OCR Transposition \& Fuzzy CPR Test Suite
.venv\\Scripts\\python.exe test\_ocr\_transposition.py

:: Standalone CPR Human Error \& Typo Redaction Suite
.venv\\Scripts\\python.exe test\_cpr\_human\_error.py

:: Full Django 5.2 Unit Test Suite (Including Edge Cases)
.venv\\Scripts\\python.exe manage.py test qa\_app.tests qa\_app.test\_redaction\_engine qa\_app.test\_edge\_cases users

:: Full Visual Florence-2 OCR Test
.venv\\Scripts\\python.exe test\_florence\_ocr.py


5. Testing (Ubuntu / Linux)

Run tests via Linux Terminal (`bash`):
```bash

:: Standalone OCR Transposition \& Fuzzy CPR Test Suite

python test\_ocr\_transposition.py

:: Standalone CPR Human Error \& Typo Redaction Suite
python test\_cpr\_human\_error.py

:: Full Django 5.2 Unit Test Suite (Including Edge Cases)
python manage.py test qa\_app.tests qa\_app.test\_redaction\_engine qa\_app.test\_edge\_cases users

:: Full Visual Florence-2 OCR Test
python test\_florence\_ocr.py

