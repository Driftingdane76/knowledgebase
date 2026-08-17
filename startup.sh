#!/bin/bash
# startup.sh (executed by Azure App Service on container boot)

# 1. Install Playwright browser binaries and system libraries if missing
python -m playwright install --with-deps chromium

# 2. Start Celery worker in background
celery -A core worker -Q default,ocr -c 1 --loglevel=INFO &

# 3. Start Gunicorn / WSGI web server
gunicorn --bind=0.0.0.0 --timeout 600 --workers 2 core.wsgi