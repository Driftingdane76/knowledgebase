import os
import sys
import tempfile
from pathlib import Path

# Setup Django Environment
BASE_DIR = Path(__file__).resolve().parent
env_file = BASE_DIR / '.env'
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ.setdefault(key.strip(), val.strip().strip("'").strip('"'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.conf import settings
from django.db import connections
from django.core.management import call_command
from users.models import CustomUser
from qa_app.models import Category, KnowledgePage, PageImage, Tag

def create_sqlite_snapshot():
    print("=" * 65)
    print("=== EXPORTING POSTGRESQL DATABASE TO SQLITE SNAPSHOT ===")
    print("=" * 65)

    sqlite_path = BASE_DIR / 'db.sqlite3'
    temp_json_path = BASE_DIR / '_temp_pg_dump.json'

    # Step 1: Dump data from PostgreSQL
    print("\n[1/4] Dumping data from PostgreSQL...")
    try:
        user_cnt = CustomUser.objects.count()
        page_cnt = KnowledgePage.objects.count()
        cat_cnt = Category.objects.count()
        img_cnt = PageImage.objects.count()
        tag_cnt = Tag.objects.count()
        print(f"  -> Found in PostgreSQL: {user_cnt} users, {cat_cnt} categories, {tag_cnt} tags, {page_cnt} pages, {img_cnt} images.")

        with open(temp_json_path, 'w', encoding='utf-8') as f:
            call_command(
                'dumpdata',
                'users',
                'qa_app',
                natural_foreign=True,
                natural_primary=True,
                indent=2,
                stdout=f
            )
        print(f"  -> Serialized records to temporary fixture: {temp_json_path.name}")
    except Exception as e:
        print(f"  -> Error dumping data from PostgreSQL: {e}")
        if temp_json_path.exists():
            temp_json_path.unlink()
        return False

    # Step 2: Prepare fresh SQLite file
    print("\n[2/4] Initializing fresh SQLite database...")
    connections.close_all()

    if sqlite_path.exists():
        try:
            sqlite_path.unlink()
            print(f"  -> Removed existing {sqlite_path.name}")
        except Exception as e:
            print(f"  -> Note: {e}")

    # Reconfigure default connection to SQLite
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(sqlite_path),
        'TIME_ZONE': settings.TIME_ZONE if settings.USE_TZ else None,
        'CONN_MAX_AGE': 0,
        'AUTOCOMMIT': True,
        'OPTIONS': {},
    }
    connections.close_all()

    # Step 3: Run migrations on SQLite
    print("\n[3/4] Running schema migrations on SQLite...")
    try:
        call_command('migrate', interactive=False, verbosity=0)
        print("  -> SQLite tables created successfully.")
    except Exception as e:
        print(f"  -> Error migrating SQLite: {e}")
        if temp_json_path.exists():
            temp_json_path.unlink()
        return False

    # Step 4: Load fixture into SQLite
    print("\n[4/4] Loading data into SQLite...")
    try:
        # Avoid data duplication if data migration created anything
        KnowledgePage.objects.all().delete()
        Category.objects.all().delete()
        CustomUser.objects.all().delete()

        call_command('loaddata', str(temp_json_path), verbosity=0)
        print("  -> Data imported successfully.")
    except Exception as e:
        print(f"  -> Error loading data into SQLite: {e}")
        if temp_json_path.exists():
            temp_json_path.unlink()
        return False
    finally:
        if temp_json_path.exists():
            temp_json_path.unlink()

    # Verification
    sqlite_user_cnt = CustomUser.objects.count()
    sqlite_page_cnt = KnowledgePage.objects.count()
    sqlite_cat_cnt = Category.objects.count()
    sqlite_img_cnt = PageImage.objects.count()

    print("\n" + "=" * 65)
    print("=== RECORD PARITY VERIFICATION ===")
    print(f"  CustomUsers:   {sqlite_user_cnt} / {user_cnt}")
    print(f"  Categories:    {sqlite_cat_cnt} / {cat_cnt}")
    print(f"  KnowledgePages: {sqlite_page_cnt} / {page_cnt}")
    print(f"  PageImages:    {sqlite_img_cnt} / {img_cnt}")
    print("=" * 65)

    if sqlite_page_cnt == page_cnt and sqlite_cat_cnt == cat_cnt:
        print(f"\nSUCCESS: SQLite snapshot successfully generated at: {sqlite_path}")
        return True
    else:
        print("\nWARNING: Counts do not match PostgreSQL source.")
        return False

if __name__ == '__main__':
    success = create_sqlite_snapshot()
    sys.exit(0 if success else 1)
