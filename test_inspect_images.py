import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from qa_app.models import PageImage, KnowledgePage
from django.conf import settings

def inspect():
    print(f"MEDIA_URL = {settings.MEDIA_URL}")
    print(f"MEDIA_ROOT = {settings.MEDIA_ROOT}")
    
    images = PageImage.objects.all()[:5]
    print(f"Total PageImages in DB: {PageImage.objects.count()}")
    for img in images:
        print(f"\nID: {img.id}")
        print(f"Name: {img.name}")
        print(f"File Name: {img.file.name if img.file else 'None'}")
        print(f"File URL: {img.file.url if img.file else 'None'}")
        if img.file:
            full_path = os.path.join(settings.MEDIA_ROOT, img.file.name)
            exists = os.path.exists(full_path)
            print(f"Full path: {full_path} (Exists: {exists})")

if __name__ == '__main__':
    inspect()
