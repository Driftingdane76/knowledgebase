import os
import re
import email
import email.policy
from datetime import datetime
from html.parser import HTMLParser

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from qa_app.models import Category, KnowledgePage, PageImage

class SimpleTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.current_row = []
        self.current_cell = None
        self.current_cell_imgs = []
        self.in_tr = False
        self.in_td = False

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.in_tr = True
            self.current_row = []
        elif tag in ('td', 'th') and self.in_tr:
            self.in_td = True
            self.current_cell = []
            self.current_cell_imgs = []
        elif tag == 'img' and self.in_td:
            attr_dict = dict(attrs)
            if 'src' in attr_dict:
                self.current_cell_imgs.append(attr_dict['src'])
        elif tag in ('br', 'p', 'div', 'tr', 'li') and self.in_td:
            self.current_cell.append('<NEWLINE>')

    def handle_data(self, data):
        if self.in_td and self.current_cell is not None:
            self.current_cell.append(data)

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.in_td:
            self.in_td = False
            raw_text = "".join(self.current_cell)
            
            # HTML source newlines and tabs become single spaces
            raw_text = re.sub(r'\s+', ' ', raw_text)
            
            # Replace markers with actual newlines
            text = raw_text.replace('<NEWLINE>', '\n')
            
            # Clean up spaces around newlines
            text = re.sub(r'[ \t]*\n[ \t]*', '\n', text)
            
            # Reduce multiple newlines
            text = re.sub(r'\n{3,}', '\n\n', text).strip()
            
            # Now, apply our smart line merge logic to make it flow naturally!
            lines = text.split('\n')
            cleaned_lines = []
            for line in lines:
                if not line:
                    cleaned_lines.append('')
                else:
                    if cleaned_lines and cleaned_lines[-1] != '' and not line.startswith('-') and not line.startswith('*'):
                        # merge with previous line
                        join_char = ' '
                        if cleaned_lines[-1].endswith('-') and not cleaned_lines[-1].endswith(' -'):
                            join_char = ''
                        elif cleaned_lines[-1].endswith('/'):
                            join_char = ''
                        cleaned_lines[-1] = cleaned_lines[-1] + join_char + line
                    else:
                        cleaned_lines.append(line)
            
            text = '\n'.join(cleaned_lines)
            
            self.current_row.append({'text': text, 'imgs': self.current_cell_imgs})
            self.current_cell = None
        elif tag == 'tr' and self.in_tr:
            self.in_tr = False
            if self.current_row:
                self.rows.append(self.current_row)


class Command(BaseCommand):
    help = 'Imports MHT data into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Path to the MHT file to import'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data for this imported file\'s category before importing'
        )

    def handle(self, *args, **options):
        from concurrent.futures import ThreadPoolExecutor
        from qa_app.views import extract_text_from_image

        def run_ocr_for_image(image_id, file_path):
            try:
                text_result, ocr_data_result = extract_text_from_image(file_path)
                PageImage.objects.filter(id=image_id).update(
                    extracted_text=text_result,
                    ocr_data=ocr_data_result
                )
            except Exception:
                pass

        ocr_executor = ThreadPoolExecutor(max_workers=4)
        ocr_futures = []

        mht_path = options['file_path']
        if not os.path.isabs(mht_path):
            mht_path = os.path.join(os.getcwd(), mht_path)

        if not os.path.exists(mht_path):
            self.stdout.write(self.style.ERROR(f"File not found: {mht_path}"))
            return

        base_name = os.path.splitext(os.path.basename(mht_path))[0]
        cat_id = base_name.upper()

        if options['clear']:
            self.stdout.write(f"Clearing existing data for category '{cat_id}'...")
            # Deleting the category cascades to KnowledgePages, which cascades to PageImages
            Category.objects.filter(id=cat_id).delete()

        category, created = Category.objects.get_or_create(
            id=cat_id, 
            defaults={'name': f'Imported {base_name}'}
        )

        with open(mht_path, 'r', encoding='utf-8', errors='ignore') as f:
            msg = email.message_from_file(f, policy=email.policy.default)

        html_content = None
        images_dict = {}

        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == 'text/html':
                html_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
            elif content_type.startswith('image/'):
                filename = part.get_filename()
                if filename:
                    images_dict[filename] = part.get_payload(decode=True)
                    images_dict[os.path.basename(filename)] = part.get_payload(decode=True)
                content_location = part.get('Content-Location')
                if content_location:
                    images_dict[content_location] = part.get_payload(decode=True)
                    images_dict[content_location.split('/')[-1]] = part.get_payload(decode=True)

        if not html_content:
            self.stdout.write(self.style.ERROR("No HTML content found in MHT."))
            return

        parser = SimpleTableParser()
        parser.feed(html_content)
        
        if not parser.rows:
            self.stdout.write(self.style.ERROR("No table rows found in HTML."))
            return
        
        imported_count = 0
        for row in parser.rows[1:]:  # skip header
            if len(row) < 5:
                continue

            nr = row[0]['text']
            user = row[1]['text']
            dato_str = row[2]['text']
            
            question_cell = row[3]
            answer_cell = row[4]

            q_text = question_cell['text']
            a_text = answer_cell['text']

            # Skip rows that are completely empty
            if not nr and not q_text and not a_text and not question_cell['imgs'] and not answer_cell['imgs']:
                continue

            parsed_date = None
            if dato_str:
                try:
                    parsed_date = datetime.strptime(dato_str, '%d-%m-%Y').date()
                except ValueError:
                    pass

            # Create title from first 50 chars of question
            title_base = q_text.replace('\n', ' ')
            title = title_base[:50] + ('...' if len(title_base) > 50 else '')
            if not title:
                title = f"EJO Question {nr}"

            page_id = f"{cat_id}-{nr}" if nr else f"{cat_id}-Unknown-{imported_count}"
            while KnowledgePage.objects.filter(id=page_id).exists():
                page_id += "-dup"

            page = KnowledgePage.objects.create(
                id=page_id,
                category=category,
                title=title,
                date=parsed_date,
                username=user if user else 'anonymous',
                question_text=q_text,
                resolution_text=a_text
            )

            # Extract images from the cells
            all_imgs = question_cell['imgs'] + answer_cell['imgs']
            for src in all_imgs:
                img_data = images_dict.get(src)
                if not img_data:
                    basename = src.split('/')[-1].split('\\')[-1]
                    img_data = images_dict.get(basename)
                
                if img_data:
                    import io
                    from PIL import Image

                    filename = os.path.basename(src)
                    # Use the same optimization logic as views.py
                    try:
                        img_pil = Image.open(io.BytesIO(img_data))
                        webp_io = io.BytesIO()
                        img_pil.save(webp_io, format='WEBP', quality=80)
                        img_data = webp_io.getvalue()
                        filename = f"{filename.rsplit('.', 1)[0]}.webp"
                    except Exception as img_err:
                        self.stdout.write(self.style.WARNING(f"Image optimization failed for {filename}: {img_err}"))

                    page_img = PageImage(
                        id=f"{page.id}-{filename}",
                        page=page,
                        name=filename
                    )
                    if len(page_img.id) > 100:
                        page_img.id = page_img.id[:100]
                    page_img.file.save(filename, ContentFile(img_data), save=True)

                    # Queue OCR
                    if page_img.file:
                        ocr_futures.append(
                            ocr_executor.submit(run_ocr_for_image, page_img.id, page_img.file.path)
                        )

            imported_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully imported {imported_count} records."))
        
        if ocr_futures:
            self.stdout.write("Waiting for OCR tasks to complete (this might take a minute)...")
            ocr_executor.shutdown(wait=True)
            self.stdout.write(self.style.SUCCESS("All OCR tasks completed!"))
