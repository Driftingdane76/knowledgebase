import os
import subprocess
import sys

def test_azure_env(env_vars, check_keys=None, expected_error=None, should_pass=False):
    """
    Spawns a subprocess running `manage.py check` or settings inspection with a controlled environment.
    Uses .venv\\Scripts\\python.exe in accordance with project constraints.
    """
    env = os.environ.copy()
    
    # Remove existing conflicting env vars
    for k in ['DEBUG', 'SECRET_KEY', 'ALLOWED_HOSTS', 'WEBSITE_HOSTNAME', 'CSRF_TRUSTED_ORIGINS', 'REQUIRE_HTTPS']:
        if k in env:
            del env[k]
            
    env['DJANGO_SETTINGS_MODULE'] = 'core.settings'
    env.update(env_vars)
    
    python_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv', 'Scripts', 'python.exe')
    
    # If check_keys provided, run python inline to inspect Django settings directly
    if check_keys:
        inspect_script = (
            "import django; "
            "django.setup(); "
            "from django.conf import settings; "
            "print('ALLOWED_HOSTS=' + repr(settings.ALLOWED_HOSTS)); "
            "print('CSRF_TRUSTED_ORIGINS=' + repr(settings.CSRF_TRUSTED_ORIGINS)); "
            "print('SECURE_PROXY_SSL_HEADER=' + repr(settings.SECURE_PROXY_SSL_HEADER)); "
            "print('USE_X_FORWARDED_HOST=' + repr(getattr(settings, 'USE_X_FORWARDED_HOST', False))); "
            "print('USE_X_FORWARDED_PORT=' + repr(getattr(settings, 'USE_X_FORWARDED_PORT', False))); "
            "print('SESSION_COOKIE_SECURE=' + repr(getattr(settings, 'SESSION_COOKIE_SECURE', False))); "
            "print('CSRF_COOKIE_SECURE=' + repr(getattr(settings, 'CSRF_COOKIE_SECURE', False))); "
        )
        result = subprocess.run(
            [python_exe, "-c", inspect_script],
            env=env,
            capture_output=True,
            text=True
        )
    else:
        result = subprocess.run(
            [python_exe, "manage.py", "check"],
            env=env,
            capture_output=True,
            text=True
        )
    
    output = result.stderr + result.stdout
    return result.returncode, output

if __name__ == "__main__":
    print("==========================================================")
    print("=== RUNNING AZURE APP SERVICE SETTINGS TDD TEST SUITE ===")
    print("==========================================================")
    
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env.backup')
    
    if os.path.exists(env_path):
        os.rename(env_path, backup_path)
        
    all_passed = True
    
    try:
        # TEST 1: Azure WEBSITE_HOSTNAME auto-included in ALLOWED_HOSTS & CSRF_TRUSTED_ORIGINS in production
        print("\n[TEST 1] Testing WEBSITE_HOSTNAME auto-inclusion (Azure App Service)...")
        code, out = test_azure_env({
            'DEBUG': 'False',
            'SECRET_KEY': 'test-secret-key-for-azure-validation-suite-1234',
            'WEBSITE_HOSTNAME': 'kb-app-prod.azurewebsites.net',
        }, check_keys=True)
        
        expected_host = "'kb-app-prod.azurewebsites.net'"
        expected_csrf = "'https://kb-app-prod.azurewebsites.net'"
        
        if code == 0 and expected_host in out and expected_csrf in out:
            print("  -> PASS: WEBSITE_HOSTNAME successfully resolved in ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS.")
        else:
            print(f"  -> FAIL: Expected {expected_host} in ALLOWED_HOSTS and {expected_csrf} in CSRF_TRUSTED_ORIGINS.\nOutput:\n{out}")
            all_passed = False

        # TEST 2: SECURE_PROXY_SSL_HEADER, USE_X_FORWARDED_HOST & USE_X_FORWARDED_PORT
        print("\n[TEST 2] Testing Azure Reverse Proxy SSL & Forwarded Host headers...")
        code, out = test_azure_env({
            'DEBUG': 'False',
            'SECRET_KEY': 'test-secret-key-for-azure-validation-suite-1234',
            'ALLOWED_HOSTS': 'localhost',
            'WEBSITE_HOSTNAME': 'kb-app-prod.azurewebsites.net',
        }, check_keys=True)
        
        if ("SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')" in out and
            "USE_X_FORWARDED_HOST=True" in out and
            "USE_X_FORWARDED_PORT=True" in out):
            print("  -> PASS: Reverse proxy headers properly configured.")
        else:
            print(f"  -> FAIL: Reverse proxy headers missing or incorrect.\nOutput:\n{out}")
            all_passed = False

        # TEST 3: Production missing both ALLOWED_HOSTS and WEBSITE_HOSTNAME -> Must raise ImproperlyConfigured
        print("\n[TEST 3] Testing production safeguard when neither ALLOWED_HOSTS nor WEBSITE_HOSTNAME is set...")
        code, out = test_azure_env({
            'DEBUG': 'False',
            'SECRET_KEY': 'test-secret-key-for-azure-validation-suite-1234',
            'ALLOWED_HOSTS': '',
        }, check_keys=False)
        
        if code != 0 and "ALLOWED_HOSTS must not be empty in production" in out:
            print("  -> PASS: Properly caught ImproperlyConfigured for empty host list.")
        else:
            print(f"  -> FAIL: Did not fail as expected on empty hosts in production.\nOutput:\n{out}")
            all_passed = False

    finally:
        if os.path.exists(backup_path):
            os.rename(backup_path, env_path)
            
    print("\n==========================================================")
    if all_passed:
        print("ALL AZURE SETTINGS TESTS PASSED!")
        sys.exit(0)
    else:
        print("TEST SUITE FAILED (Expected failure prior to applying settings.py edits).")
        sys.exit(1)
