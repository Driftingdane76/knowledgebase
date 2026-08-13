from django.db import models
from django.utils import timezone
from django.contrib.postgres.indexes import GinIndex


# models.py

class Category(models.Model):
    """
    Standard Django Category model.
    Django automatically provides an auto-incrementing integer 'id' primary key.
    """
    name = models.CharField(max_length=255, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['created_at']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Tag(models.Model):
    """
    Represents an administrative tag that can be applied to Knowledge Pages.
    Tags are used for quick categorization based on frequently occurring keywords or topics.
    """
    name = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class KnowledgePage(models.Model):
    """
    The core entity representing a single Question & Answer entry in the knowledgebase.
    Stores the user's question, the resolution, associated category, and dynamically extracted tags.
    """
    id = models.CharField(max_length=100, primary_key=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='pages', db_index=True
    )
    title = models.CharField(max_length=255, default='Untitled Question')
    # Changed from CharField to DateField for proper database-level sorting and chronological indexing
    date = models.DateField(null=True, blank=True, db_index=True)
    username = models.CharField(max_length=100, default='anonymous', db_index=True)
    question_text = models.TextField(blank=True, default='')
    resolution_text = models.TextField(blank=True, default='')
    tags = models.ManyToManyField(Tag, related_name='pages', blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # Composite index for category + default created_at sort
            models.Index(fields=['category', '-created_at'], name='idx_page_cat_created'),
            # Composite index for the most common filter: category + date sort
            models.Index(fields=['category', '-date'], name='idx_page_cat_date'),
            # Composite index for category + username sort
            models.Index(fields=['category', 'username'], name='idx_page_cat_user'),
            # Trigram GIN indexes for fast searching
            GinIndex(fields=['title'], name='page_title_trigm_gin', opclasses=['gin_trgm_ops']),
            GinIndex(fields=['question_text'], name='page_quest_trigm_gin', opclasses=['gin_trgm_ops']),
            GinIndex(fields=['resolution_text'], name='page_resol_trigm_gin', opclasses=['gin_trgm_ops']),
        ]

    def __str__(self):
        return self.title


class PageImage(models.Model):
    """
    Represents an image (e.g., a screenshot) attached to a KnowledgePage.
    Stores the physical file, the raw extracted OCR text, and the parsed word coordinates (ocr_data)
    for UI highlighting and redaction purposes.
    """
    id = models.CharField(max_length=100, primary_key=True)
    page = models.ForeignKey(
        KnowledgePage, on_delete=models.CASCADE, related_name='images', db_index=True
    )
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='page_images/', null=True, blank=True)
    extracted_text = models.TextField(blank=True, default='')
    ocr_data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']
        indexes = [
            # Trigram GIN index for fast search of OCR text
            GinIndex(fields=['extracted_text'], name='img_ocr_trigm_gin', opclasses=['gin_trgm_ops']),
        ]

    def __str__(self):
        return self.name

