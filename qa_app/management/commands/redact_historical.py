import re
import io
from PIL import Image
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from qa_app.models import KnowledgePage, PageImage
from qa_app.views import extract_text_from_image

class Command(BaseCommand):
    help = 'Retroactively scans all KnowledgePages and PageImages, redacting CPR numbers from text and images.'

    def handle(self, *args, **options):
        self.stdout.write("Starting historical CPR redaction...")

        from qa_app.redaction import redact_text_content

        # 1. Redact KnowledgePages
        pages = KnowledgePage.objects.all()
        pages_updated = 0
        for page in pages:
            updated = False
            
            def process_text(text_val):
                return redact_text_content(text_val)

            new_q = process_text(page.question_text)
            if new_q != page.question_text:
                page.question_text = new_q
                updated = True
                
            new_r = process_text(page.resolution_text)
            if new_r != page.resolution_text:
                page.resolution_text = new_r
                updated = True
                
            if updated:
                page.save(update_fields=['question_text', 'resolution_text'])
                pages_updated += 1
                self.stdout.write(f"Redacted text in KnowledgePage ID: {page.id}")

        # 2. Redact PageImages
        images = PageImage.objects.all()
        images_updated = 0
        for img_obj in images:
            # We don't just redact the text, we need to redraw the image file if it contains a CPR
            # To do this correctly, we will just run our updated extract_text_from_image on it
            if not img_obj.file:
                continue
                
            try:
                # Read the current file
                file_data = img_obj.file.read()
                pil_img = Image.open(io.BytesIO(file_data))
                
                # Check if we even need to redact this image (fast path: check if text has CPR)
                # But to be safe, let's just re-run the full OCR and let it redact
                text_result, ocr_data_result = extract_text_from_image(pil_img)
                
                # Compare the new text_result with what we had. If there is a [REDACTED CPR] in it,
                # we know the image was mutated and needs to be saved.
                if "[REDACTED CPR]" in text_result or "[REDACTED BANK]" in text_result or "[REDACTED NAME]" in text_result:
                    # Save the mutated image
                    webp_io = io.BytesIO()
                    pil_img.save(webp_io, format='WEBP', quality=80)
                    new_file_data = webp_io.getvalue()
                    
                    filename = img_obj.file.name.split('/')[-1]
                    img_obj.file.save(filename, ContentFile(new_file_data), save=False)
                    img_obj.extracted_text = text_result
                    img_obj.ocr_data = ocr_data_result
                    img_obj.save()
                    
                    images_updated += 1
                    self.stdout.write(f"Redacted image & text in PageImage ID: {img_obj.id}")
            except Exception as e:
                self.stderr.write(f"Error processing PageImage {img_obj.id}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Finished! Updated {pages_updated} pages and {images_updated} images."))
