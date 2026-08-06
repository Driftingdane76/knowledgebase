import os
import sys
import io
import random
import argparse
import django
from django.utils import timezone
from django.core.files.base import ContentFile
from PIL import Image

# 1. Setup Django Environment
env_file = '.env'
if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip().strip("'").strip('"')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
django.setup()

from qa_app.models import Category, KnowledgePage, PageImage
from qa_app.views import extract_text_from_image
from test_htmls.dynamic_mock_generator import generate_dynamic_html_snippet

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Please install playwright: pip install playwright && playwright install chromium")
    sys.exit(1)

def clear_db():
    print("Clearing old data...")
    PageImage.objects.all().delete()
    KnowledgePage.objects.all().delete()
    Category.objects.all().delete()
    print("Old DB records cleared.")

def clean_media_folder():
    print("Cleaning media/page_images/ folder...")
    media_images_dir = os.path.join(os.path.dirname(__file__), 'media', 'page_images')
    if os.path.isdir(media_images_dir):
        for fname in os.listdir(media_images_dir):
            fpath = os.path.join(media_images_dir, fname)
            if os.path.isfile(fpath):
                os.remove(fpath)
    else:
        os.makedirs(media_images_dir, exist_ok=True)

# --- Dummy Data Generators ---
def get_random_name():
    firsts = ["Morten", "Lars", "Sofie", "Mette", "Jens", "Camilla", "Anders", "Louise", "Henrik", "Maria"]
    lasts = ["Noerregaard", "Jensen", "Petersen", "Frederiksen", "Nielsen", "Hansen", "Pedersen", "Andersen", "Christensen", "Larsen"]
    return f"{random.choice(firsts)} {random.choice(lasts)}"

def get_random_cpr(format_type=1):
    day = str(random.randint(1, 28)).zfill(2)
    month = str(random.randint(1, 12)).zfill(2)
    year = str(random.randint(0, 99)).zfill(2)
    last_4 = str(random.randint(1000, 9999))
    if format_type == 1: return f"{day}{month}{year}-{last_4}"
    if format_type == 2: return f"{day}{month}{year} {last_4}"
    return f"{day}{month}{year}-{last_4}"

def get_random_bank(format_type=1):
    reg = str(random.randint(1000, 9999))
    konto = str(random.randint(1000000000, 9999999999))
    if format_type == 1: return f"Reg.nr {reg} Konto {konto}"
    if format_type == 2: return f"{reg} {konto}"
    if format_type == 3: return f"Reg {reg} Kontonr {konto}"
    if format_type == 4: return f"Reg.nr {reg} og Kontonummer {konto}"
    return f"{reg} {konto}"

def get_random_danish_qa():
    plate = f"{random.choice(['AB', 'XY', 'CD', 'ZZ', 'EF'])} {random.randint(10, 99)} {random.randint(100, 999)}"
    
    questions = [
        f"Kunden ringer ind angående en skade på deres bil (nummerplade {plate}). Vi har brug for at finde den korrekte forsikringspolice for at se om stenslag er dækket. Kan du tjekke vedhæftede skærmbillede fra systemet og bekræfte dækningen?",
        f"Vi har en sag åben på nummerplade {plate}. Kunden påstår at de ikke har modtaget udbetalingen for den totalskadede bil. Se venligst udbetalingsformularen på billedet. Hvorfor er den blevet afvist i systemet?",
        f"Kan du hjælpe med at rette en fejl i systemet? Når jeg slår bil med nummerplade {plate} op, viser den de forkerte bankoplysninger på kunden. Vedhæftet er et udklip af kundens rigtige oplysninger fra vores CRM.",
        f"Kunde har fået en ridse på en parkeringsplads (nummerplade {plate}). Jeg prøver at oprette skadesanmeldelsen, men systemet kaster en database-fejl når jeg gemmer billedet. Hvad er løsningen her?",
        f"Udbetaling til kunden med forsikret bil (nummerplade {plate}) hænger i godkendelsesflowet. Jeg har vedhæftet et klip fra godkendelsessiden i portalen. Hvordan får jeg frigivet beløbet til kundens konto?"
    ]
    
    answers = [
        f"Fejlen skyldtes at policen for bilen med nummerplade {plate} ikke havde kaskodækning tilføjet korrekt. Jeg har manuelt opdateret systemet og godkendt udbetalingen. Sagen kan nu lukkes.",
        "Udbetalingen blev afvist fordi bankoplysningerne ikke matchede kundens CPR-nummer. Jeg har bedt kunden sende ny dokumentation, og vi har nu opdateret registreringsnummer og kontonummer. Beløbet er frigivet til udbetaling.",
        "Dette er et kendt problem i vores CRM-system. Når man søger på visse nummerplader, cache-lagres gamle PII-data desværre. Jeg har ryddet cachen, og systemet viser nu de korrekte informationer. Se vedhæftede for bekræftelse.",
        "Jeg har undersøgt fejlen vedrørende skadesanmeldelsen. Fejlen opstod fordi der manglede en digital underskrift på formularen. Jeg har omgået fejlen i backend. Næste gang skal kunden bruge MitID til at godkende.",
        "Godkendelsesflowet var låst på grund af en manglende ledergodkendelse. Jeg har eskaleret sagen til IT, som nu har frigivet betalingen. Erstatningen er nu på vej til kundens NemKonto."
    ]
    
    title = f"Sag vedr. bil {plate}"
    return title, random.choice(questions), random.choice(answers)

# --- Local HTML Mock Randomizer ---
def randomize_html(original_html):
    html = original_html
    html = html.replace("Morten Noerregaard", get_random_name()).replace("Lars Jensen", get_random_name())
    html = html.replace("Sofie Petersen", get_random_name()).replace("Mette Frederiksen", get_random_name())
    html = html.replace("Jens Hansen", get_random_name())
    
    html = html.replace("010203-4567", get_random_cpr(1)).replace("120485-1234", get_random_cpr(1))
    html = html.replace("120485 1234", get_random_cpr(2)).replace("251290-9876", get_random_cpr(1))
    html = html.replace("112233-4455", get_random_cpr(1)).replace("150688-1122", get_random_cpr(1))
    
    html = html.replace("Reg.nr 1234 Konto 1234567890", get_random_bank(1)).replace("9876 5432109876", get_random_bank(2))
    html = html.replace("Reg 9090 Kontonr 1122334455", get_random_bank(3)).replace("Reg.nr 3344 Konto 5566778899", get_random_bank(1))
    html = html.replace("Reg.nr 4321 og Kontonummer 9876543210", get_random_bank(4))
    
    html = html.replace("#10042", f"#{random.randint(10000, 99999)}")
    html = html.replace("#10043", f"#{random.randint(10000, 99999)}")
    html = html.replace("#10044", f"#{random.randint(10000, 99999)}")
    return html

def generate_and_seed(total_cases=50):
    print("Creating Category...")
    cat_ui = Category.objects.create(id="UI-Pro-Snippets", name="Professional UI Snippets")
    
    print(f"\nStarting Redaction API pipeline for {total_cases} dynamic multi-layout UI component snippets...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page_ctx = browser.new_page(device_scale_factor=2)
        
        for i in range(1, total_cases + 1):
            title = f"Test #{i}: UI Element Snippet"
            print(f"\nProcessing {title}...")
            
            # 1. Generate dynamic HTML snippet across 8 layout architectures & 6 color themes
            html = generate_dynamic_html_snippet(i)
            page_ctx.set_content(html)
            page_ctx.wait_for_timeout(50)
            
            # 2. Capture high-DPI bounded screenshot of the snippet target
            target_element = page_ctx.locator(".snippet-capture-target")
            screenshot_bytes = target_element.screenshot()
            
            # 3. OCR & Redaction Pipeline via Local Florence-2
            print("  -> Running Local Florence-2 OCR on snippet...")
            img_to_redact = Image.open(io.BytesIO(screenshot_bytes))
            extracted_text, ocr_data = extract_text_from_image(img_to_redact)
            
            # 4. Save visual artifact and seed Django database
            print("  -> Saving redacted image to disk...")
            redacted_buf = io.BytesIO()
            img_to_redact.save(redacted_buf, format="PNG")
            
            qa_title, qa_question, qa_answer = get_random_danish_qa()
            
            db_page = KnowledgePage.objects.create(
                id=f"page-pro-snippet-{i}",
                category=cat_ui,
                title=qa_title,
                date=timezone.now().date(),
                username="IFagent",
                question_text=qa_question,
                resolution_text=qa_answer
            )
            
            img_filename = f"pro_snippet_{i}.png"
            image_instance = PageImage(
                id=f"img-pro-snippet-{i}",
                page=db_page,
                name=img_filename,
                extracted_text=extracted_text,
                ocr_data=ocr_data
            )
            image_instance.file.save(img_filename, ContentFile(redacted_buf.getvalue()), save=True)
            print(f"  -> Successfully seeded DB for {img_filename}")
            
        browser.close()
        
    print(f"\nDone! All {total_cases} Professional Element Snippet test cases generated and seeded.")

def main():
    parser = argparse.ArgumentParser(description="Seed mock UI snippets with Florence-2 OCR redaction.")
    parser.add_argument("--count", type=int, default=50, help="Number of test snippets to generate and seed (default: 50)")
    args = parser.parse_args()

    clean_media_folder()
    clear_db()
    generate_and_seed(total_cases=args.count)

if __name__ == "__main__":
    main()
