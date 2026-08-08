import os
import sys
from pathlib import Path

# Create professional HTML template with embedded styling tailored for PDF printing
HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Azure Deployment Guide 2026 - Django 5.2 App Service</title>
<style>
  @page {
    size: A4;
    margin: 18mm 16mm 18mm 16mm;
    @bottom-right {
      content: "Page " counter(page) " of " counter(pages);
      font-size: 8pt;
      font-family: 'Segoe UI', system-ui, sans-serif;
      color: #64748b;
    }
  }

  * {
    box-sizing: border-box;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    color: #1e293b;
    background-color: #ffffff;
    line-height: 1.55;
    font-size: 10pt;
    margin: 0;
    padding: 0;
  }

  .header-card {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
    color: #ffffff;
    padding: 24px 28px;
    border-radius: 12px;
    margin-bottom: 22px;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
  }

  .header-card h1 {
    margin: 0 0 6px 0;
    font-size: 20pt;
    font-weight: 700;
    letter-spacing: -0.5px;
  }

  .header-card .subtitle {
    font-size: 10.5pt;
    color: #93c5fd;
    margin: 0 0 10px 0;
    font-weight: 500;
  }

  .badge-row {
    display: flex;
    gap: 8px;
    margin-top: 8px;
  }

  .badge {
    display: inline-block;
    background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.25);
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 8pt;
    font-weight: 600;
    color: #ffffff;
  }

  .section {
    margin-bottom: 20px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 18px 20px;
    page-break-inside: avoid;
  }

  .section-title {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 0 0 12px 0;
    font-size: 12.5pt;
    font-weight: 700;
    color: #0f172a;
    border-bottom: 2px solid #f1f5f9;
    padding-bottom: 8px;
  }

  .section-number {
    background: #2563eb;
    color: #ffffff;
    width: 24px;
    height: 24px;
    border-radius: 6px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 9pt;
    font-weight: 700;
  }

  ol, ul {
    margin: 0 0 12px 0;
    padding-left: 20px;
  }

  li {
    margin-bottom: 6px;
  }

  .code-block {
    background: #0f172a;
    color: #f8fafc;
    border-radius: 8px;
    padding: 12px 16px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 8.5pt;
    line-height: 1.45;
    margin: 10px 0;
    overflow-x: auto;
    border: 1px solid #1e293b;
  }

  .code-inline {
    background: #f1f5f9;
    color: #0f172a;
    font-family: 'Consolas', monospace;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 8.5pt;
    border: 1px solid #cbd5e1;
    font-weight: 600;
  }

  .alert {
    padding: 10px 14px;
    border-radius: 8px;
    margin: 10px 0;
    font-size: 9pt;
    line-height: 1.45;
  }

  .alert-warning {
    background: #fffbeb;
    border-left: 4px solid #f59e0b;
    color: #92400e;
  }

  .alert-info {
    background: #eff6ff;
    border-left: 4px solid #3b82f6;
    color: #1e40af;
  }

  .alert-success {
    background: #f0fdf4;
    border-left: 4px solid #10b981;
    color: #065f46;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
    font-size: 8.5pt;
  }

  th {
    background: #f8fafc;
    color: #334155;
    text-align: left;
    padding: 8px 10px;
    border-bottom: 2px solid #cbd5e1;
    font-weight: 700;
  }

  td {
    padding: 7px 10px;
    border-bottom: 1px solid #e2e8f0;
    vertical-align: top;
  }

  tr:nth-child(even) td {
    background-color: #f8fafc;
  }

  .page-break {
    page-break-before: always;
  }

  .footer-note {
    font-size: 8pt;
    color: #64748b;
    text-align: center;
    margin-top: 14px;
  }
</style>
</head>
<body>

<div class="header-card">
  <h1>Azure Deployment Guide (2026 Edition)</h1>
  <div class="subtitle">Production CI/CD Pipeline Specification for Django 5.2 on Azure App Service</div>
  <div class="badge-row">
    <span class="badge">Django 5.2</span>
    <span class="badge">Python 3.11</span>
    <span class="badge">Azure Linux App Service</span>
    <span class="badge">GitHub Actions CI/CD</span>
    <span class="badge">PostgreSQL Flexible Server</span>
  </div>
</div>

<div class="section">
  <div class="section-title">
    <span class="section-number">1</span>
    Phase 1: Unlock Azure SCM Basic Auth Publishing
  </div>
  <p>In modern Azure releases, Basic Auth is restricted by default. SCM Basic Auth must be explicitly enabled for GitHub Publish Profile deployments.</p>
  <ol>
    <li>Log into the <a href="https://portal.azure.com">Azure Portal</a> and navigate to your <strong>App Service</strong> instance.</li>
    <li>In the left sidebar under <strong>Settings</strong>, click <strong>Configuration</strong> (or <strong>Environment variables / General settings</strong>).</li>
    <li>Click the <strong>General settings</strong> tab at the top.</li>
    <li>Scroll down to the <strong>Basic Auth</strong> section.</li>
    <li>Set <strong>SCM Basic Auth Publishing Credentials</strong> to <strong>On</strong>.</li>
    <li>Click the <strong>Save</strong> button at the top of the blade.</li>
  </ol>
  <div class="alert alert-info">
    <strong>Note:</strong> If your organization restricts Basic Auth via Azure Policy, use OpenID Connect (OIDC) Service Principals instead. For standard setups, SCM Basic Auth with GitHub Secrets is fast, reliable, and secure.
  </div>
</div>

<div class="section">
  <div class="section-title">
    <span class="section-number">2</span>
    Phase 2: Download Publish Profile & Store in GitHub Secrets
  </div>
  <ol>
    <li>In the Azure Portal, click <strong>Overview</strong> on the left-hand menu.</li>
    <li>In the top action bar, click <strong>Get publish profile</strong>. This downloads an XML file ending in <span class="code-inline">.PublishSettings</span>.</li>
    <li>Open this file in a text editor (Notepad, VS Code) and <strong>copy the entire XML contents</strong>.</li>
    <li>Navigate to your GitHub repository: <span class="code-inline">https://github.com/Driftingdane76/knowledgebase</span>.</li>
    <li>Go to <strong>Settings</strong> ➔ <strong>Secrets and variables</strong> ➔ <strong>Actions</strong>.</li>
    <li>Click <strong>New repository secret</strong>.</li>
    <li>Set <strong>Name</strong> exactly as: <span class="code-inline">AZURE_WEBAPP_PUBLISH_PROFILE</span></li>
    <li>In <strong>Secret</strong>, paste the complete XML block and click <strong>Add secret</strong>.</li>
  </ol>
</div>

<div class="page-break"></div>

<div class="section">
  <div class="section-title">
    <span class="section-number">3</span>
    Phase 3: Azure App Service Environment & Startup Configuration
  </div>
  <p>Before launching the pipeline, configure these mandatory environment variables and startup command in Azure Portal (<strong>Settings ➔ Environment variables / Configuration</strong>):</p>
  
  <table>
    <thead>
      <tr>
        <th>Setting Name</th>
        <th>Recommended Value / Description</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>SCM_DO_BUILD_DURING_DEPLOYMENT</strong></td>
        <td><code>true</code> <em>(Mandatory: tells Azure Oryx to run <code>pip install -r requirements.txt</code>)</em></td>
      </tr>
      <tr>
        <td><strong>DJANGO_SETTINGS_MODULE</strong></td>
        <td><code>core.settings</code></td>
      </tr>
      <tr>
        <td><strong>DEBUG</strong></td>
        <td><code>False</code></td>
      </tr>
      <tr>
        <td><strong>SECRET_KEY</strong></td>
        <td>Strong 50+ random character string for production security</td>
      </tr>
      <tr>
        <td><strong>DB_ENGINE</strong></td>
        <td><code>django.db.backends.postgresql</code></td>
      </tr>
      <tr>
        <td><strong>DB_NAME</strong> / <strong>DB_USER</strong> / <strong>DB_PASSWORD</strong></td>
        <td>Your Azure Database for PostgreSQL credentials</td>
      </tr>
      <tr>
        <td><strong>DB_HOST</strong> / <strong>DB_PORT</strong></td>
        <td><code>&lt;server-name&gt;.postgres.database.azure.com</code> / <code>5432</code></td>
      </tr>
      <tr>
        <td><strong>ALLOWED_HOSTS</strong></td>
        <td><code>&lt;your-app-name&gt;.azurewebsites.net</code></td>
      </tr>
      <tr>
        <td><strong>REQUIRE_HTTPS</strong></td>
        <td><code>True</code> <em>(Enforces secure cookies behind Azure SSL termination)</em></td>
      </tr>
    </tbody>
  </table>

  <p><strong>Startup Command</strong> (Under <em>Configuration ➔ General settings ➔ Startup Command</em>):</p>
  <div class="code-block">gunicorn --bind=0.0.0.0 --timeout 600 --workers 4 core.wsgi:application</div>
</div>

<div class="section">
  <div class="section-title">
    <span class="section-number">4</span>
    Phase 4: GitHub Actions Workflow Specification
  </div>
  <p>Create the file at <span class="code-inline">.github/workflows/azure-deploy.yml</span> in your repository with the following production pipeline:</p>
  
<div class="code-block">name: Build and deploy Python app to Azure Web App

on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Upload artifact for deployment
        uses: actions/upload-artifact@v4
        with:
          name: python-app
          path: |
            .
            !.git/
            !.github/
            !.venv/
            !venv/
            !antenv/
            !__pycache__/
            !*.sqlite3
            !*.sqlite3-journal
            !.env
            !production_env
            !.agents/
            !AGENTS.md
            !.cursorrules
            !.cursor/
            !test_output_images/
            !test_htmls/
            !presentation_screenshots/

  deploy:
    runs-on: ubuntu-latest
    needs: build
    environment:
      name: 'Production'
      url: ${{ steps.deploy-to-webapp.outputs.webapp-url }}
    steps:
      - name: Download artifact from build job
        uses: actions/download-artifact@v4
        with:
          name: python-app

      - name: 'Deploy to Azure Web App'
        uses: azure/webapps-deploy@v3
        id: deploy-to-webapp
        with:
          app-name: 'YOUR_AZURE_APP_NAME'   # &lt;-- Replace with actual App Service name
          slot-name: 'Production'
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}</div>
</div>

<div class="page-break"></div>

<div class="section">
  <div class="section-title">
    <span class="section-number">5</span>
    Phase 5: Commit, Deploy & Live Monitoring
  </div>
  <ol>
    <li>Commit and push the deployment workflow via <strong>Command Prompt (`cmd.exe`)</strong>:
      <div class="code-block">git add .github/workflows/azure-deploy.yml
git commit -m "Add production Azure GitHub Actions deployment pipeline"
git push origin main</div>
    </li>
    <li>Open your browser and navigate to <a href="https://github.com/Driftingdane76/knowledgebase/actions">GitHub Actions</a>.</li>
    <li>Click on the active workflow to monitor real-time build and deployment logs.</li>
    <li>Once the workflow finishes with green checkmarks, open your Azure App URL:
      <div class="code-block">https://&lt;your-app-name&gt;.azurewebsites.net</div>
    </li>
  </ol>

  <div class="alert alert-success">
    <strong>Post-Deployment Tip (Database Migrations):</strong><br>
    To run your initial database migrations against Azure PostgreSQL, open the <strong>SSH Console</strong> in Azure Portal (under <em>Development Tools ➔ SSH</em>) and run:
    <br><code>python manage.py migrate</code>
  </div>
</div>

<div class="footer-note">
  Generated for Q&amp;A Knowledgebase | Django 5.2 LTS Production Architecture | Verified 2026
</div>

</body>
</html>
"""

def generate_pdf():
    output_html_path = Path(r"d:\knowledgebase\Azure_Deployment_Guide_2026.html")
    output_pdf_path = Path(r"d:\knowledgebase\Azure_Deployment_Guide_2026.pdf")
    
    # Save the HTML file
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
    print(f"HTML Guide generated at: {output_html_path}")
    
    # Try playwright to generate PDF
    try:
        from playwright.sync_api import sync_playwright
        print("Using Playwright to generate PDF...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(output_html_path.as_uri())
            page.pdf(
                path=str(output_pdf_path),
                format="A4",
                print_background=True,
                margin={"top": "15mm", "bottom": "15mm", "left": "15mm", "right": "15mm"}
            )
            browser.close()
        print(f"PDF successfully generated at: {output_pdf_path}")
        return True
    except Exception as e:
        print(f"Playwright PDF generation skipped: {e}")
        return False

if __name__ == "__main__":
    generate_pdf()
