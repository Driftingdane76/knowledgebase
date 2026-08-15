"""
Views and API endpoints for the Q&A Knowledgebase application.
Handles frontend rendering, database serialization, search functionality,
and complex OCR processing (including redaction) for uploaded images.
"""
import base64
import datetime
import io
import json
import os
import re
import shutil
import sys
import urllib.request

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone

from .models import KnowledgePage, PageImage, Category, Tag
from .utils import extract_tags
from .florence_ocr import run_florence_ocr_and_redact

try:
    from PIL import Image, ImageDraw
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_text_from_image(img_or_path):
    """
    Performs 100% local OCR and PII redaction using Microsoft Florence-2.
    Detects Danish CPR numbers and Bank info, redacts them visually on the image,
    and returns redacted text and normalized coordinates for search indexing.
    """
    try:
        if isinstance(img_or_path, str):
            img = Image.open(img_or_path).convert("RGB")
        else:
            img = img_or_path.convert("RGB") if img_or_path.mode != "RGB" else img_or_path

        return run_florence_ocr_and_redact(img)
    except ImportError as ie:
        print(f"Florence-2 or torch not installed. OCR skipped: {ie}")
        return "", []
    except Exception as e:
        print(f"Local OCR processing failed: {e}")
        return "", []


def _serialize_page(page, include_images=True):
    """Serialise a single KnowledgePage instance to a dict."""
    data = {
        'id': page.id,
        'categoryId': page.category_id,
        'title': page.title,
        'date': str(page.date) if page.date else '',
        'username': page.username or '',
        'questionText': page.question_text or '',
        'resolutionText': page.resolution_text or '',
        'images': [],
        'createdAt': page.created_at.isoformat(),
        'updatedAt': page.updated_at.isoformat(),
        'tags': [t.name for t in page.tags.all()] if hasattr(page, 'tags') else [],
    }
    if include_images:
        data['images'] = [
            {
                'id': img.id,
                'name': img.name,
                'dataUrl': img.file.url if img.file else '',
                'extractedText': img.extracted_text or '',
                'ocrData': img.ocr_data or []
            }
            for img in page.images.all()
        ]
    return data


_IS_TESTING = 'test' in sys.argv or 'test_runner' in sys.modules

# Toggle this to True to bypass authentication for UI testing (allows subagents to test full functionality)
_UI_TESTING_BYPASS_AUTH = False

_CATEGORIES_CACHE = None

# views.py

def _serialize_categories():
    """Fetches categories directly from DB with annotated page counts."""
    return [
        {
            'id': c.id,
            'name': c.name,
            'createdAt': c.created_at.isoformat(),
            'pageCount': c.page_count
        }
        for c in Category.objects.annotate(page_count=Count('pages')).order_by('created_at')
    ]


def invalidate_categories_cache():
    global _CATEGORIES_CACHE
    _CATEGORIES_CACHE = None


def _serialize_trending_tags():
    try:
        top_tags = Tag.objects.annotate(count=Count('pages')).filter(count__gt=0).order_by('-count')[:15]
        return [{'id': t.id, 'name': t.name, 'count': t.count} for t in top_tags]
    except Exception:
        return []

def serialize_db():
    """Full DB snapshot used by write endpoints to return updated state."""
    pages_qs = (
        KnowledgePage.objects
        .select_related('category')
        .prefetch_related('images', 'tags')
        .order_by('-created_at')
    )
    return {
        'categories': _serialize_categories(),
        'trendingTags': _serialize_trending_tags(),
        'pages': [_serialize_page(p) for p in pages_qs],
    }


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

def index(request):
    """
    Renders the main single-page application (SPA) shell.
    Injects authentication status into the context for UI toggle behavior.
    """
    can_edit = True  # Proxy handles external auth
    is_superuser = False
    
    if _UI_TESTING_BYPASS_AUTH:
        is_superuser = True
    elif request.user.is_authenticated:
        is_superuser = request.user.is_superuser
            
    context = {
        'can_edit': can_edit,
        'is_superuser': is_superuser,
    }
    return render(request, 'index.html', context)


def get_db(request):
    """
    Returns all categories and pages (with images).
    For very large datasets, prefer /api/search with pagination instead.
    """
    return JsonResponse(serialize_db())


def search_pages(request):
    """
    Server-side search with filtering, sorting, and pagination.

    Query params:
        q          (str)  — full-text search across username, date, question, resolution
        category   (str)  — filter by category ID
        sort       (str)  — date-desc | date-asc | user-asc | user-desc  (default: date-desc)
        page       (int)  — 1-based page number (default: 1)
        page_size  (int)  — rows per page, max 200 (default: 5)
    """
    q = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip() or None
    sort = request.GET.get('sort', 'date-desc')
    try:
        page_num = max(1, int(request.GET.get('page', 1)))
    except (ValueError, TypeError):
        page_num = 1
    try:
        page_size = min(200, max(1, int(request.GET.get('page_size', 50))))
    except (ValueError, TypeError):
        page_size = 50

    # 1. Fetch matching page IDs from image OCR text first to prevent outer join
    matching_page_ids = set()
    if q:
        terms = q.split()
        if terms:
            img_qs = PageImage.objects.all()
            img_q = Q()
            for term in terms:
                img_q &= Q(extracted_text__icontains=term)
            matching_page_ids = set(img_qs.filter(img_q).values_list('page_id', flat=True))

    qs = KnowledgePage.objects.select_related('category').prefetch_related('images')

    # Category filter
    if category_id:
        qs = qs.filter(category_id=category_id)

    # 2. Main query utilizing GIN indexes
    if q:
        terms = q.split()
        if terms:
            q_obj = Q()
            for term in terms:
                q_obj &= (
                    Q(username__icontains=term) |
                    Q(question_text__icontains=term) |
                    Q(resolution_text__icontains=term) |
                    Q(title__icontains=term) |
                    Q(date__icontains=term)
                )
            if matching_page_ids:
                qs = qs.filter(q_obj | Q(id__in=matching_page_ids))
            else:
                qs = qs.filter(q_obj)

    # Sorting
    sort_map = {
        'date-desc': ['-date', '-created_at'],
        'date-asc':  ['date', 'created_at'],
        'user-asc':  ['username', '-created_at'],
        'user-desc': ['-username', '-created_at'],
    }
    qs = qs.order_by(*sort_map.get(sort, ['-created_at']))

    target_id = request.GET.get('target_id', '').strip()
    if target_id:
        all_ids = list(qs.values_list('id', flat=True))
        if target_id in all_ids:
            page_num = (all_ids.index(target_id) // page_size) + 1

    total = qs.count()
    start = (page_num - 1) * page_size
    end = start + page_size
    page_qs = qs[start:end]

    return JsonResponse({
        'categories': _serialize_categories(),
        'trendingTags': _serialize_trending_tags(),
        'pages': [_serialize_page(p) for p in page_qs],
        'pagination': {
            'total': total,
            'page': page_num,
            'page_size': page_size,
            'total_pages': max(1, -(-total // page_size)),  # ceiling division
            'has_next': end < total,
            'has_prev': page_num > 1,
        },
    })


def categories(request):
    """
    API endpoint to create or update a Category.
    Expects JSON payload with 'name' and optional 'id'.
    Returns the updated list of categories.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        cat_id = data.get('id')
        name = (data.get('name') or '').strip()

        if not name:
            return JsonResponse({'error': 'Category name cannot be empty'}, status=400)

        if cat_id:
            try:
                category, created = Category.objects.get_or_create(
                    id=cat_id, defaults={'name': name}
                )
                if not created:
                    category.name = name
                    category.save(update_fields=['name'])
            except ValueError:
                return JsonResponse({'error': 'Invalid Category ID format'}, status=400)
        else:
            category = Category.objects.create(name=name)

        invalidate_categories_cache()
        return JsonResponse({'categories': _serialize_categories(force_refresh=True)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def delete_category(request, cat_id):
    """
    API endpoint to delete a Category by ID.
    Restricted to superusers. Returns the updated list of categories.
    """
    if request.method != 'DELETE':
        return JsonResponse({'error': 'DELETE required'}, status=405)
        
    if not _UI_TESTING_BYPASS_AUTH:
        if not request.user.is_superuser:
            return JsonResponse({'error': 'Only superusers are allowed to delete categories.'}, status=403)
            
    try:
        Category.objects.filter(id=cat_id).delete()
        invalidate_categories_cache()
        return JsonResponse({'categories': _serialize_categories(force_refresh=True)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def save_page(request):
    """
    API endpoint to create or update a KnowledgePage.
    Handles JSON payload with text fields, base64 image uploads, OCR processing,
    tag extraction, and transactional database updates.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
        
    try:
        page_data = json.loads(request.body)
        page_id = page_data.get('id')
        category_id = page_data.get('categoryId')
        title = page_data.get('title', 'Untitled Page')
        date_str = page_data.get('date', '') or None   # '' → None for DateField
        username = page_data.get('username', 'anonymous')
        question_text = page_data.get('questionText', '')
        resolution_text = page_data.get('resolutionText', '')
        incoming_images = page_data.get('images', [])

        # Resolve category
        category = None
        if category_id:
            try:
                category = Category.objects.filter(id=category_id).first()
            except ValueError:
                pass

        if not category:
            category = Category.objects.first()
            if not category:
                category = Category.objects.create(name='General')

        if not page_id:
            page_id = f'page-{int(timezone.now().timestamp() * 1000)}'

        # Collect list of image objects to delete after transaction commit
        incoming_ids = [img['id'] for img in incoming_images if img.get('id')]
        images_to_delete = list(PageImage.objects.filter(page_id=page_id).exclude(id__in=incoming_ids))

        with transaction.atomic():
            page, _ = KnowledgePage.objects.update_or_create(
                id=page_id,
                defaults={
                    'category': category,
                    'title': title,
                    'date': date_str,
                    'username': username,
                    'question_text': question_text,
                    'resolution_text': resolution_text,
                },
            )

            # Synchronise images database records
            PageImage.objects.filter(page=page).exclude(id__in=incoming_ids).delete()
            
            # Defer filesystem cleanup until transaction commit is successful
            def commit_cleanup_files():
                for img_obj in images_to_delete:
                    if img_obj.file:
                        try:
                            img_obj.file.delete(save=False)
                        except Exception as e:
                            print(f"File delete error: {e}")
                            
            transaction.on_commit(commit_cleanup_files)

            for idx, img_info in enumerate(incoming_images):
                img_id = img_info.get('id') or f'img-{int(timezone.now().timestamp() * 1000)}-{idx}'
                data_url = img_info.get('dataUrl', '')
                
                if data_url.startswith('data:'):
                    # New base64 file upload, decode it
                    try:
                        match = re.match(r'^data:([^;]+);base64,(.+)$', data_url)
                        if match:
                            mime_type, base64_str = match.groups()
                            file_data = base64.b64decode(base64_str)
                            
                            # Backend WebP conversion & validation using Pillow
                            
                            try:
                                img = Image.open(io.BytesIO(file_data))
                                
                                # Run synchronous OCR and redaction on the PIL Image
                                text_result, ocr_data_result = extract_text_from_image(img)
                                
                                webp_io = io.BytesIO()
                                img.save(webp_io, format='WEBP', quality=80)
                                file_data = webp_io.getvalue()
                                filename = f"{img_id}.webp"
                            except Exception as img_err:
                                print(f"Image processing failed: {img_err}")
                                ext = mime_type.split('/')[-1] if '/' in mime_type else 'png'
                                filename = f"{img_id}.{ext}"
                                text_result, ocr_data_result = "", []
                            
                            img_obj, _ = PageImage.objects.update_or_create(
                                id=img_id,
                                page=page,
                                defaults={
                                    'name': img_info.get('name', 'image.png'),
                                    'extracted_text': text_result,
                                    'ocr_data': ocr_data_result
                                },
                            )
                            img_obj.file.save(filename, ContentFile(file_data), save=True)
                    except Exception as e:
                        print(f"Error saving image file: {e}")
                else:
                    # Existing file URL, keep it
                    PageImage.objects.update_or_create(
                        id=img_id,
                        page=page,
                        defaults={
                            'name': img_info.get('name', 'image.png'),
                        },
                    )
            
            # Extract tags from text
            try:
                all_text = f"{page.question_text} {page.resolution_text}"
                for existing_img in PageImage.objects.filter(page=page):
                    if existing_img.extracted_text:
                        all_text += f" {existing_img.extracted_text}"
                new_tags = extract_tags(all_text)
                page.tags.set(new_tags)
            except Exception as e:
                print(f"Tag extraction error: {e}")
                
            # Invalidate categories counts cache
            invalidate_categories_cache()

        return JsonResponse({
            'success': True,
            'page': _serialize_page(page),
            'categories': _serialize_categories(force_refresh=True),
            'trendingTags': _serialize_trending_tags(),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def delete_page(request, page_id):
    """
    API endpoint to delete a KnowledgePage by ID.
    Restricted to superusers. Cleans up associated images from the filesystem.
    """
    if request.method != 'DELETE':
        return JsonResponse({'error': 'DELETE required'}, status=405)
        
    if not _UI_TESTING_BYPASS_AUTH:
        if not request.user.is_superuser:
            return JsonResponse({'error': 'Only superusers are allowed to delete pages.'}, status=403)
        
    try:
        images = list(PageImage.objects.filter(page_id=page_id))
        
        with transaction.atomic():
            def commit_delete_files():
                for img in images:
                    if img.file:
                        try:
                            img.file.delete(save=False)
                        except Exception as e:
                            print(f"File delete error: {e}")
                            
            transaction.on_commit(commit_delete_files)
            KnowledgePage.objects.filter(id=page_id).delete()
            invalidate_categories_cache()
            
        return JsonResponse({
            'success': True,
            'categories': _serialize_categories(force_refresh=True),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def test_highlight_precision_view(request):
    """
    Renders the visual regression test suite for search highlighting precision
    and OCR sub-box positioning across multiple real-world screenshot backgrounds.
    """
    return render(request, 'test_highlight_precision.html')


def test_final_highlight_view(request):
    """
    Renders the final sandbox layout with isolated JS and CSS for the highlight logic.
    """
    can_edit = True
    is_superuser = False
    
    if _UI_TESTING_BYPASS_AUTH:
        is_superuser = True
    elif request.user.is_authenticated:
        is_superuser = request.user.is_superuser
            
    context = {
        'can_edit': can_edit,
        'is_superuser': is_superuser,
    }
    return render(request, 'test_index.html', context)
