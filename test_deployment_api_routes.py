import os
import sys
import zipfile
import tempfile
from pathlib import Path


def test_deployment_api_routes():
    print("==================================================================")
    print("=== TDD TEST SUITE: AZURE DEPLOYMENT API & ACTION VALIDATION ===")
    print("==================================================================")

    root_dir = Path(__file__).resolve().parent
    workflow_file = root_dir / ".github" / "workflows" / "azure-deploy.yml"
    all_tests_passed = True

    # -------------------------------------------------------------------------
    # TEST 1: Workflow Action Version Audit (Expect v3 OneDeploy)
    # -------------------------------------------------------------------------
    print("\n[TEST 1] Auditing Action Engine Version in azure-deploy.yml...")
    if not workflow_file.exists():
        print(f"  ❌ FAIL: Workflow file not found at {workflow_file}")
        return False

    content = workflow_file.read_text(encoding="utf-8")

    if "azure/webapps-deploy@v3" in content:
        print("  ✅ [PASS]: Workflow correctly pinned to modern 'azure/webapps-deploy@v3' (OneDeploy).")
        test_1_pass = True
    elif "azure/webapps-deploy@v2" in content:
        print("  ❌ [ASSERTION FAILED]: Found legacy 'azure/webapps-deploy@v2' (Direct /api/zipdeploy).")
        print("     -> Required Fix: Upgrade to 'azure/webapps-deploy@v3' for modern Node runners and OIDC auth.")
        test_1_pass = False
    else:
        print("  ❌ [FAIL]: 'azure/webapps-deploy' action not found or unknown version.")
        test_1_pass = False

    # -------------------------------------------------------------------------
    # TEST 2: Verify Package Target is Deterministic 'deploy.zip'
    # -------------------------------------------------------------------------
    print("\n[TEST 2] Auditing Package Target in azure-deploy.yml...")
    if "package: deploy.zip" in content:
        print("  ✅ [PASS]: Package target explicitly set to 'deploy.zip'.")
        test_2_pass = True
    else:
        print("  ❌ [FAIL]: Package target is not 'deploy.zip'.")
        test_2_pass = False

    # -------------------------------------------------------------------------
    # TEST 3: Validate Zip Archive Payload Structure
    # -------------------------------------------------------------------------
    print("\n[TEST 3] Validating Zip Payload Creation and Structure for Deployment...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_zip = Path(tmp_dir) / "deploy_test.zip"

        with zipfile.ZipFile(tmp_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_name in ['manage.py', 'requirements.txt']:
                src = root_dir / file_name
                if src.exists():
                    zf.write(src, file_name)

            wsgi_src = root_dir / 'core' / 'wsgi.py'
            if wsgi_src.exists():
                zf.write(wsgi_src, 'core/wsgi.py')

        with zipfile.ZipFile(tmp_zip, 'r') as zf:
            names = zf.namelist()
            if 'manage.py' in names and 'requirements.txt' in names and 'core/wsgi.py' in names:
                print(f"  ✅ [PASS]: Zip archive contains all required entrypoints at root: {names}")
                test_3_pass = True
            else:
                print(f"  ❌ [FAIL]: Missing entrypoints in archive: {names}")
                test_3_pass = False

    # -------------------------------------------------------------------------
    # TEST 4: Concurrency Lock Assertion
    # -------------------------------------------------------------------------
    print("\n[TEST 4] Auditing Concurrency Directives in azure-deploy.yml...")
    if "concurrency:" in content and "group: azure-deploy-kb-app-prod" in content:
        print("  ✅ [PASS]: Concurrency group configured to prevent parallel runs.")
        test_4_pass = True
    else:
        print("  ❌ [FAIL]: Concurrency group missing.")
        test_4_pass = False

    # -------------------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------------------
    print("\n==================================================================")
    all_tests_passed = test_1_pass and test_2_pass and test_3_pass and test_4_pass
    if all_tests_passed:
        print("🎉 [ALL TESTS PASSED]: Workflow and packaging 100% compliant with modern OneDeploy (v3)!")
    else:
        print("❌ [TEST SUITE FAILED]: Workflow configuration issues detected.")
    print("==================================================================")
    return all_tests_passed


if __name__ == "__main__":
    passed = test_deployment_api_routes()
    sys.exit(0 if passed else 1)