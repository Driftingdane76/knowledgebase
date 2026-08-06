import os
import subprocess
import sys

def run_test():
    print("==========================================================")
    print("=== RUNNING ENVIRONMENT PRECEDENCE TDD TEST SUITE ===")
    print("==========================================================")
    
    python_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv', 'Scripts', 'python.exe')
    
    # We pass explicit OS environment variables that differ from .env
    test_env = os.environ.copy()
    test_env['DJANGO_SETTINGS_MODULE'] = 'core.settings'
    test_env['DEBUG'] = 'False'
    test_env['SECRET_KEY'] = 'test-secret-key-50-characters-long-for-env-precedence-check-123'
    test_env['ALLOWED_HOSTS'] = 'override.azurewebsites.net'
    
    inspect_script = (
        "import django; "
        "django.setup(); "
        "from django.conf import settings; "
        "print('RESOLVED_DEBUG=' + str(settings.DEBUG)); "
        "print('RESOLVED_ALLOWED_HOSTS=' + repr(settings.ALLOWED_HOSTS)); "
    )
    
    result = subprocess.run(
        [python_exe, "-c", inspect_script],
        env=test_env,
        capture_output=True,
        text=True
    )
    
    output = result.stderr + result.stdout
    print(f"Output from Django inspection:\n{output.strip()}")
    
    if "RESOLVED_DEBUG=False" in output and "override.azurewebsites.net" in output:
        print("\n-> PASS: OS Environment variables took precedence over .env!")
        sys.exit(0)
    else:
        print("\n-> FAIL: .env forcibly overwrote OS environment variables! (Expected failure prior to fix)")
        sys.exit(1)

if __name__ == "__main__":
    run_test()
