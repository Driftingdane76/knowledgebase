import io
import os
from celery import shared_task
from django.core.files.base import ContentFile
from PIL import Image

from .models import PageImage
from .florence_ocr import run_florence_ocr_and_redact
from .utils import extract_tags


@shared_task
def probe_default_queue_task(message='default_ok'):
    """Probe task routed to the default queue."""
    return message


@shared_task
def probe_ocr_queue_task(message='ocr_ok'):
    """Probe task routed to the dedicated OCR queue."""
    return message


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def process_page_image_ocr(self, page_image_id):
    """
    Dedicated OCR background task routed to the 'ocr' queue.
    Executes Florence-2 inference, redacts CPR & Bank PII on the image,
    saves sanitized WebP file, updates OCR coordinates, and recalculates tags.
    """
    try:
        img_obj = PageImage.objects.select_related('page').get(id=page_image_id)
    except PageImage.DoesNotExist:
        return f"PageImage {page_image_id} does not exist. Skipping."

    try:
        img_obj.ocr_status = PageImage.OCRStatus.PROCESSING
        img_obj.ocr_error = ''
        img_obj.save(update_fields=['ocr_status', 'ocr_error'])

        if not img_obj.file or not os.path.exists(img_obj.file.path):
            img_obj.ocr_status = PageImage.OCRStatus.FAILED
            img_obj.ocr_error = "File not found on disk."
            img_obj.save(update_fields=['ocr_status', 'ocr_error'])
            return f"PageImage {page_image_id} missing file on disk."

        with Image.open(img_obj.file.path) as pil_img:
            pil_img = pil_img.convert("RGB")
            sanitized_text, ocr_words = run_florence_ocr_and_redact(pil_img)

            webp_io = io.BytesIO()
            pil_img.save(webp_io, format='WEBP', quality=80)
            redacted_bytes = webp_io.getvalue()

        webp_filename = f"{img_obj.id}.webp"
        img_obj.file.save(webp_filename, ContentFile(redacted_bytes), save=False)
        img_obj.extracted_text = sanitized_text
        img_obj.ocr_data = ocr_words
        img_obj.ocr_status = PageImage.OCRStatus.COMPLETED
        img_obj.ocr_error = ''
        img_obj.save(update_fields=['file', 'extracted_text', 'ocr_data', 'ocr_status', 'ocr_error'])

        # Recalculate parent page tags with OCR text
        if img_obj.page:
            all_text = f"{img_obj.page.question_text} {img_obj.page.resolution_text}"
            for sibling in img_obj.page.images.exclude(extracted_text=''):
                all_text += f" {sibling.extracted_text}"
            new_tags = extract_tags(all_text)
            if new_tags:
                img_obj.page.tags.set(new_tags)

        return f"Successfully processed OCR for PageImage {page_image_id}."

    except Exception as exc:
        img_obj.ocr_status = PageImage.OCRStatus.FAILED
        img_obj.ocr_error = str(exc)
        img_obj.save(update_fields=['ocr_status', 'ocr_error'])
        raise self.retry(exc=exc)