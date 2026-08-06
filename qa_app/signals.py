import os
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import PageImage

@receiver(post_delete, sender=PageImage)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """Deletes file from filesystem when corresponding PageImage object is deleted."""
    if instance.file:
        if os.path.isfile(instance.file.path):
            try:
                os.remove(instance.file.path)
            except Exception as e:
                print(f"Error removing file from disk: {e}")
