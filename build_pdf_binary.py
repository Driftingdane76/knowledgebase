import os
from pathlib import Path

def create_pdf(output_path):
    # Dimensions for A4: 595.28 x 841.89 pt
    W, H = 595.28, 841.89
    
    pages_content = []
    
    # --- PAGE 1: Header, Phase 1, Phase 2 ---
    p1 = []
    # Header Card Background (dark blue gradient box)
    p1.append("0.06 0.09 0.16 rg 30 710 535.28 100 re f")
    # Accent bar
    p1.append("0.15 0.39 0.92 rg 30 805 535.28 5 re f")
    # Header Text
    p1.append("BT /F2 18 Tf 1 1 1 rg 45 775 Td (Azure Deployment Guide (2026 Edition)) Tj ET")
    p1.append("BT /F1 10 Tf 0.58 0.77 0.99 rg 45 755 Td (Step-by-Step CI/CD Setup for Django 5.2 on Azure App Service using GitHub Actions) Tj ET")
    p1.append("BT /F2 8 Tf 1 1 1 rg 45 730 Td ([ Django 5.2 LTS ]  [ Python 3.11 ]  [ Azure App Service Linux ]  [ PostgreSQL Flexible Server ]) Tj ET")
    
    # --- Phase 1 Box ---
    p1.append("0.96 0.97 0.98 rg 30 520 535.28 175 re f")
    p1.append("0.89 0.91 0.94 RG 1 w 30 520 535.28 175 re S")
    # Title badge & text
    p1.append("0.15 0.39 0.92 rg 45 665 18 18 re f")
    p1.append("BT /F2 10 Tf 1 1 1 rg 51 670 Td (1) Tj ET")
    p1.append("BT /F2 12 Tf 0.06 0.09 0.16 rg 70 670 Td (Phase 1: Unlock Azure Security Gate (SCM Basic Auth)) Tj ET")
    
    # Phase 1 Steps
    steps_p1 = [
        "1. Log into the Azure Portal (https://portal.azure.com) and open your App Service.",
        "2. In the left sidebar under 'Settings', click 'Configuration' (or 'Environment variables').",
        "3. Click the 'General settings' tab at the top.",
        "4. Scroll down to the 'Basic Auth' section.",
        "5. Toggle 'SCM Basic Auth Publishing Credentials' to ON.",
        "6. Click the 'Save' button at the top of the blade."
    ]
    y = 645
    for s in steps_p1:
        p1.append(f"BT /F1 9.5 Tf 0.12 0.16 0.23 rg 45 {y} Td ({s}) Tj ET")
        y -= 16
    
    # Note callout box
    p1.append("0.94 0.96 1.0 rg 45 530 505.28 28 re f")
    p1.append("0.23 0.51 0.96 RG 1 w 45 530 505.28 28 re S")
    p1.append("BT /F2 8.5 Tf 0.12 0.25 0.69 rg 55 540 Td (Note: In 2026, Basic Auth is off by default. Enabling SCM Basic Auth is mandatory for Publish Profiles.) Tj ET")

    # --- Phase 2 Box ---
    p1.append("0.96 0.97 0.98 rg 30 330 535.28 175 re f")
    p1.append("0.89 0.91 0.94 RG 1 w 30 330 535.28 175 re S")
    p1.append("0.15 0.39 0.92 rg 45 475 18 18 re f")
    p1.append("BT /F2 10 Tf 1 1 1 rg 51 480 Td (2) Tj ET")
    p1.append("BT /F2 12 Tf 0.06 0.09 0.16 rg 70 480 Td (Phase 2: Get Master Key (Publish Profile)) Tj ET")
    
    steps_p2 = [
        "1. In Azure Portal, click 'Overview' on the left menu to return to App Service dashboard.",
        "2. On the top toolbar, click 'Get publish profile'.",
        "   -> This downloads a file named '<app-name>.PublishSettings'.",
        "3. Open this downloaded file in any text editor (Notepad, VS Code).",
        "4. Copy EVERY SINGLE line of XML text inside this file (Ctrl+A, Ctrl+C)."
    ]
    y = 455
    for s in steps_p2:
        p1.append(f"BT /F1 9.5 Tf 0.12 0.16 0.23 rg 45 {y} Td ({s}) Tj ET")
        y -= 16

    # --- Phase 3 Box ---
    p1.append("0.96 0.97 0.98 rg 30 140 535.28 175 re f")
    p1.append("0.89 0.91 0.94 RG 1 w 30 140 535.28 175 re S")
    p1.append("0.15 0.39 0.92 rg 45 285 18 18 re f")
    p1.append("BT /F2 10 Tf 1 1 1 rg 51 290 Td (3) Tj ET")
    p1.append("BT /F2 12 Tf 0.06 0.09 0.16 rg 70 290 Td (Phase 3: Hide Key in GitHub Secrets Vault) Tj ET")
    
    steps_p3 = [
        "1. Open your browser to your GitHub repo: https://github.com/Driftingdane76/knowledgebase",
        "2. Click the 'Settings' tab at the top of the repository.",
        "3. In the left sidebar under 'Security', click 'Secrets and variables' -> 'Actions'.",
        "4. Click the green 'New repository secret' button.",
        "5. Under Name, type exactly: AZURE_WEBAPP_PUBLISH_PROFILE",
        "6. Under Secret, paste the complete block of XML code copied from Phase 2.",
        "7. Click 'Add secret'."
    ]
    y = 265
    for s in steps_p3:
        p1.append(f"BT /F1 9.5 Tf 0.12 0.16 0.23 rg 45 {y} Td ({s}) Tj ET")
        y -= 16
        
    p1.append("BT /F1 8 Tf 0.4 0.45 0.55 rg 240 30 Td (Page 1 of 3 - Azure Deployment Guide 2026) Tj ET")
    pages_content.append("\n".join(p1))

    # --- PAGE 2: Phase 4 (App Settings & Startup Command) ---
    p2 = []
    # Header minimal
    p2.append("0.06 0.09 0.16 rg 30 780 535.28 35 re f")
    p2.append("BT /F2 12 Tf 1 1 1 rg 45 792 Td (Phase 4: Mandatory Azure App Service Environment Settings) Tj ET")
    
    # Table of Environment variables
    p2.append("0.96 0.97 0.98 rg 30 450 535.28 315 re f")
    p2.append("0.89 0.91 0.94 RG 1 w 30 450 535.28 315 re S")
    p2.append("BT /F2 10 Tf 0.06 0.09 0.16 rg 45 745 Td (Configure under: App Service -> Settings -> Configuration / Environment variables) Tj ET")
    
    # Table headers
    p2.append("0.91 0.93 0.96 rg 45 715 505.28 20 re f")
    p2.append("BT /F2 9 Tf 0.1 0.15 0.25 rg 55 721 Td (Environment Variable Name) Tj 250 0 Td (Required Production Value / Purpose) Tj ET")
    
    rows = [
        ("SCM_DO_BUILD_DURING_DEPLOYMENT", "true  (CRITICAL: Triggers pip install -r requirements.txt)"),
        ("SCM_COMMAND_IDLE_TIMEOUT", "1800  (Extends Kudu timeout for build downloads)"),
        ("DJANGO_SETTINGS_MODULE", "core.settings"),
        ("DEBUG", "False"),
        ("SECRET_KEY", "<50+ random characters for production cryptographic security>"),
        ("DB_ENGINE", "django.db.backends.postgresql"),
        ("DB_NAME", "<your-azure-postgresql-database-name>"),
        ("DB_USER", "<your-database-admin-username>"),
        ("DB_PASSWORD", "<your-database-admin-password>"),
        ("DB_HOST", "<your-server>.postgres.database.azure.com"),
        ("DB_PORT", "5432"),
        ("ALLOWED_HOSTS", "kb-app-prod-dve8cybhcpgvaed8.denmarkeast-01.azurewebsites.net"),
        ("REQUIRE_HTTPS", "True  (Enforces secure HTTPS cookies behind Azure SSL)")
    ]
    y = 695
    for k, v in rows:
        p2.append(f"BT /F2 8 Tf 0.06 0.09 0.16 rg 55 {y} Td ({k}) Tj ET")
        p2.append(f"BT /F1 8 Tf 0.2 0.25 0.35 rg 250 {y} Td ({v}) Tj ET")
        y -= 17

    # Startup Command Box
    p2.append("0.96 0.97 0.98 rg 30 330 535.28 105 re f")
    p2.append("0.89 0.91 0.94 RG 1 w 30 330 535.28 105 re S")
    p2.append("0.15 0.39 0.92 rg 45 405 18 18 re f")
    p2.append("BT /F2 10 Tf 1 1 1 rg 51 410 Td (!) Tj ET")
    p2.append("BT /F2 11 Tf 0.06 0.09 0.16 rg 70 410 Td (Mandatory Startup Command (General Settings -> Startup Command)) Tj ET")
    
    p2.append("0.06 0.09 0.16 rg 45 350 505.28 35 re f")
    p2.append("BT /F3 9 Tf 0.95 0.98 1.0 rg 55 363 Td (gunicorn --bind=0.0.0.0 --timeout 600 --workers 4 core.wsgi:application) Tj ET")
    
    # Workflow overview
    p2.append("0.96 0.97 0.98 rg 30 80 535.28 235 re f")
    p2.append("0.89 0.91 0.94 RG 1 w 30 80 535.28 235 re S")
    p2.append("0.15 0.39 0.92 rg 45 285 18 18 re f")
    p2.append("BT /F2 10 Tf 1 1 1 rg 51 290 Td (5) Tj ET")
    p2.append("BT /F2 12 Tf 0.06 0.09 0.16 rg 70 290 Td (Phase 5: Create .github/workflows/azure-deploy.yml) Tj ET")
    
    steps_p5 = [
        "1. In your local repository, create folder: .github/workflows/",
        "2. Create file: azure-deploy.yml inside that folder.",
        "3. Paste the production-ready YAML pipeline specification (detailed on Page 3).",
        "4. App name is configured as 'kb-app-prod' targeting Azure App Service."
    ]
    y = 265
    for s in steps_p5:
        p2.append(f"BT /F1 9.5 Tf 0.12 0.16 0.23 rg 45 {y} Td ({s}) Tj ET")
        y -= 16

    p2.append("BT /F1 8 Tf 0.4 0.45 0.55 rg 240 30 Td (Page 2 of 3 - Azure Deployment Guide 2026) Tj ET")
    pages_content.append("\n".join(p2))

    # --- PAGE 3: Workflow YAML, Commit & Launch ---
    p3 = []
    p3.append("0.06 0.09 0.16 rg 30 780 535.28 35 re f")
    p3.append("BT /F2 12 Tf 1 1 1 rg 45 792 Td (Production Workflow YAML & Deployment Execution) Tj ET")
    
    # Code block for YAML
    p3.append("0.06 0.09 0.16 rg 30 290 535.28 475 re f")
    yaml_lines = [
        "name: Build and deploy Python app to Azure Web App - kb-app-prod",
        "on:",
        "  push:",
        "    branches: [ main ]",
        "  workflow_dispatch:",
        "jobs:",
        "  build:",
        "    runs-on: ubuntu-latest",
        "    steps:",
        "      - uses: actions/checkout@v4",
        "      - uses: actions/setup-python@v5",
        "        with: { python-version: '3.11' }",
        "      - name: Upload artifact for deployment",
        "        uses: actions/upload-artifact@v4",
        "        with:",
        "          name: python-app",
        "          path: |",
        "            .",
        "            !.git/ !.venv/ !venv/ !antenv/ !__pycache__/",
        "            !*.sqlite3 !.env !production_env !.agents/ !AGENTS.md",
        "            !.cursorrules !test_output_images/ !test_htmls/",
        "  deploy:",
        "    runs-on: ubuntu-latest",
        "    needs: build",
        "    steps:",
        "      - uses: actions/download-artifact@v4",
        "        with: { name: python-app }",
        "      - name: 'Deploy to Azure Web App'",
        "        uses: azure/webapps-deploy@v3",
        "        with:",
        "          app-name: 'kb-app-prod'",
        "          slot-name: 'Production'",
        "          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}"
    ]
    y = 750
    for line in yaml_lines:
        p3.append(f"BT /F3 8 Tf 0.95 0.98 1.0 rg 45 {y} Td ({line}) Tj ET")
        y -= 13

    # Phase 6 & 7 Box
    p3.append("0.96 0.97 0.98 rg 30 70 535.28 205 re f")
    p3.append("0.89 0.91 0.94 RG 1 w 30 70 535.28 205 re S")
    p3.append("0.15 0.39 0.92 rg 45 245 18 18 re f")
    p3.append("BT /F2 10 Tf 1 1 1 rg 51 250 Td (6) Tj ET")
    p3.append("BT /F2 12 Tf 0.06 0.09 0.16 rg 70 250 Td (Phase 6: Commit, Deploy & Execute Database Migrations) Tj ET")
    
    launch_steps = [
        "1. In Command Prompt (cmd.exe), commit and push the pipeline:",
        "   git add requirements.txt .github/workflows/azure-deploy.yml",
        "   git commit -m 'Configure PyTorch CPU index for lightweight Azure deployment'",
        "   git push origin main",
        "2. Monitor real-time logs under the 'Actions' tab on GitHub.",
        "3. Once deployment turns GREEN, run database migrations in Azure Portal:",
        "   App Service -> Development Tools -> SSH -> type: python manage.py migrate",
        "4. Your application is now live at: https://kb-app-prod-dve8cybhcpgvaed8.denmarkeast-01.azurewebsites.net"
    ]
    y = 225
    for s in launch_steps:
        p3.append(f"BT /F1 9 Tf 0.12 0.16 0.23 rg 45 {y} Td ({s}) Tj ET")
        y -= 16

    p3.append("BT /F1 8 Tf 0.4 0.45 0.55 rg 240 30 Td (Page 3 of 3 - Azure Deployment Guide 2026) Tj ET")
    pages_content.append("\n".join(p3))

    # --- BUILD PDF OBJECTS ---
    objects = []
    
    def add_object(content):
        objects.append(content)
        return len(objects)

    # Obj 1: Catalog
    add_object("<< /Type /Catalog /Pages 2 0 R >>")
    
    # Obj 2: Pages (placeholder, updated later)
    pages_obj_idx = 2
    add_object("") 
    
    # Obj 3: Font Helvetica
    add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    # Obj 4: Font Helvetica-Bold
    add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    # Obj 5: Font Courier
    add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
    
    page_obj_ids = []
    
    for stream_content in pages_content:
        # Stream object
        stream_bytes = stream_content.encode('latin1')
        stream_id = add_object(f"<< /Length {len(stream_bytes)} >>\nstream\n{stream_content}\nendstream")
        
        # Page object
        page_id = add_object(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] "
            f"/Contents {stream_id} 0 R "
            f"/Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R >> >> >>"
        )
        page_obj_ids.append(page_id)
    
    # Update Obj 2: Pages
    kids_str = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
    objects[pages_obj_idx - 1] = f"<< /Type /Pages /Kids [{kids_str}] /Count {len(page_obj_ids)} >>"
    
    # Write PDF file
    with open(output_path, "wb") as f:
        f.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for i, obj in enumerate(objects):
            offsets.append(f.tell())
            f.write(f"{i+1} 0 obj\n{obj}\nendobj\n".encode('latin1'))
            
        xref_offset = f.tell()
        f.write(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode('latin1'))
        for off in offsets:
            f.write(f"{off:010d} 00000 n \n".encode('latin1'))
            
        f.write(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode('latin1'))

    print(f"Successfully generated pure PDF: {output_path}")

create_pdf(r"d:\knowledgebase\Azure_Deployment_Guide_2026.pdf")
