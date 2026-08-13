from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.db.models import Count
from .models import Category, KnowledgePage, PageImage, Tag
from .utils import backfill_all_tags


class PageImageInline(admin.TabularInline):
    model = PageImage
    extra = 0
    fields = ('name', 'file', 'image_preview', 'extracted_text')
    readonly_fields = ('image_preview', 'extracted_text')

    def image_preview(self, obj):
        if obj.file:
            return mark_safe(f'<img src="{obj.file.url}" style="max-height: 100px; border-radius: 4px;" />')
        return "No Image"
    image_preview.short_description = 'Preview'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for Category models.
    Customizes the list display and allows sorting by the number of associated pages.
    """
    list_display = ('id', 'name', 'created_at', 'get_page_count')
    list_editable = ('name',)
    search_fields = ('=id', 'name')
    list_filter = ('created_at',)
    ordering = ('created_at',)

    def get_queryset(self, request):
        """Annotates the queryset with the count of pages in each category."""
        return super().get_queryset(request).annotate(page_count=Count('pages'))

    def get_page_count(self, obj):
        """Returns the annotated page count for display."""
        return obj.page_count
    get_page_count.short_description = 'Page Count'
    get_page_count.admin_order_field = 'page_count'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Admin interface for Tag models.
    Provides a custom button in the change list view to trigger retroactive tag backfilling.
    """
    list_display = ('name', 'created_at', 'get_page_count')
    search_fields = ('name',)
    ordering = ('name',)
    change_list_template = "admin/qa_app/tag/change_list.html"

    def get_urls(self):
        """Injects custom URLs into the Tag admin interface."""
        urls = super().get_urls()
        custom_urls = [
            path('run-backfill/', self.admin_site.admin_view(self.run_backfill_view), name='qa_app_tag_run_backfill'),
        ]
        return custom_urls + urls

    def run_backfill_view(self, request):
        """
        Custom admin view that triggers the backfill_all_tags utility.
        Scans all existing pages and images to apply tags retroactively.
        """
        try:
            updated, total = backfill_all_tags()
            self.message_user(request, f"Successfully tagged {updated} out of {total} pages.", level=messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Error running backfill: {e}", level=messages.ERROR)
            
        return redirect('admin:qa_app_tag_changelist')

    def get_queryset(self, request):
        """Annotates the queryset with the count of pages associated with each tag."""
        return super().get_queryset(request).annotate(page_count=Count('pages'))

    def get_page_count(self, obj):
        """Returns the annotated page count for display."""
        return obj.page_count
    get_page_count.short_description = 'Page Count'
    get_page_count.admin_order_field = 'page_count'


@admin.register(KnowledgePage)
class KnowledgePageAdmin(admin.ModelAdmin):
    """
    Admin interface for KnowledgePage models.
    Supports viewing inline images and filtering by properties.
    """
    list_display = ('id', 'title', 'category', 'date', 'username', 'created_at', 'has_images')
    list_editable = ('category',)
    list_filter = ('category', 'date', 'username', 'created_at')
    search_fields = ('title', 'question_text', 'resolution_text', 'username', 'category__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('tags',)
    inlines = [PageImageInline]

    def has_images(self, obj):
        return obj.images.exists()
    has_images.boolean = True
    has_images.short_description = 'Has Screenshots'


@admin.register(PageImage)
class PageImageAdmin(admin.ModelAdmin):
    """
    Admin interface for PageImage models.
    Shows image previews and snippets of extracted OCR text.
    """
    list_display = ('id', 'page', 'name', 'image_preview', 'extracted_text_snippet', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'extracted_text', 'page__title')
    readonly_fields = ('image_preview', 'extracted_text', 'ocr_data', 'created_at')
    ordering = ('created_at',)

    def image_preview(self, obj):
        if obj.file:
            return mark_safe(f'<img src="{obj.file.url}" style="max-height: 80px; border-radius: 4px;" />')
        return "No Image"
    image_preview.short_description = 'Image Preview'

    def extracted_text_snippet(self, obj):
        if obj.extracted_text:
            return obj.extracted_text[:100] + ('...' if len(obj.extracted_text) > 100 else '')
        return ""
    extracted_text_snippet.short_description = 'Extracted Text (OCR)'
