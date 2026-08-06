import os
import subprocess
import sys

def test_config(env_vars, expected_error=None, should_pass=False):
    # Start with a clean base environment, removing variables that could interfere
    env = os.environ.copy()
    
    # Remove any existing .env loaded variables from our own environment just to be safe, 
    # though subprocess won't auto-load .env unless python-dotenv is doing it.
    for k in ['DEBUG', 'SECRET_KEY', 'ALLOWED_HOSTS']:
        if k in env:
            del env[k]
            
    env.update(env_vars)
    
    # We use `.venv\Scripts\python` to ensure we use the local virtual environment.
    python_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv', 'Scripts', 'python.exe')
    
    result = subprocess.run(
        [python_exe, "manage.py", "check"],
        env=env,
        capture_output=True,
        text=True
    )
    
    output = result.stderr + result.stdout
    if should_pass:
        if result.returncode != 0:
            print(f"FAIL: Expected pass but got error.\nEnv: {env_vars}\nOutput: {output}")
            return False
        else:
            print(f"PASS: Successfully booted with env: {env_vars}")
            return True
    else:
        if expected_error and expected_error in output and result.returncode != 0:
            print(f"PASS: Caught expected error '{expected_error}' with env: {env_vars}")
            return True
        else:
            print(f"FAIL: Expected error '{expected_error}' but didn't catch it.\nEnv: {env_vars}\nOutput: {output}")
            return False

if __name__ == "__main__":
    print("--- Running Security Settings Tests ---")
    
    success = True
    
    # We must temporarily move .env so settings.py doesn't forcibly overwrite our test variables
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env.backup')
    
    if os.path.exists(env_path):
        os.rename(env_path, backup_path)
        
    try:
        # 1. DEBUG=False, missing SECRET_KEY
        success &= test_config(
            {'DEBUG': 'False', 'SECRET_KEY': '', 'ALLOWED_HOSTS': 'localhost'}, 
            expected_error="SECRET_KEY must not be empty in production"
        )
        
        # 2. DEBUG=False, missing ALLOWED_HOSTS
        success &= test_config(
            {'DEBUG': 'False', 'SECRET_KEY': 'some-secret-key', 'ALLOWED_HOSTS': ''}, 
            expected_error="ALLOWED_HOSTS must not be empty in production"
        )
        
        # 3. DEBUG=True, missing everything -> should pass and assign dynamic key
        success &= test_config(
            {'DEBUG': 'True', 'SECRET_KEY': '', 'ALLOWED_HOSTS': ''}, 
            should_pass=True
        )
    finally:
        # Always restore the .env file
        if os.path.exists(backup_path):
            os.rename(backup_path, env_path)
            
    if success:
        print("\nALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\nSOME TESTS FAILED.")
        sys.exit(1)
