import os
import subprocess
import sys

def test_sqlite_engine():
    print("==========================================================")
    print("=== RUNNING SQLITE FALLBACK CONFIGURATION TEST ===")
    print("==========================================================")

    python_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv', 'Scripts', 'python.exe')

    test_env = os.environ.copy()
    test_env['DJANGO_SETTINGS_MODULE'] = 'core.settings'
    test_env['DB_ENGINE'] = 'django.db.backends.sqlite3'
    test_env['DB_NAME'] = 'db.sqlite3'

    inspect_script = (
        "import django; "
        "django.setup(); "
        "from django.conf import settings; "
        "engine = settings.DATABASES['default']['ENGINE']; "
        "name = str(settings.DATABASES['default']['NAME']); "
        "options = settings.DATABASES['default'].get('OPTIONS', {}); "
        "print('RESOLVED_ENGINE=' + engine); "
        "print('RESOLVED_NAME=' + name); "
        "print('RESOLVED_OPTIONS=' + repr(options)); "
    )

    result = subprocess.run(
        [python_exe, "-c", inspect_script],
        env=test_env,
        capture_output=True,
        text=True
    )

    output = result.stderr + result.stdout
    print(f"Output from Django inspection:\n{output.strip()}")

    # We expect clean sqlite configuration without PostgreSQL-specific connect_timeout options
    if (
        "RESOLVED_ENGINE=django.db.backends.sqlite3" in output
        and "db.sqlite3" in output
        and "connect_timeout" not in output
    ):
        print("\n-> PASS: SQLite engine configured cleanly without Postgres options!")
        sys.exit(0)
    else:
        print("\n-> FAIL: Settings did not configure SQLite cleanly (Expected failure prior to settings.py update).")
        sys.exit(1)

if __name__ == "__main__":
    test_sqlite_engine()
