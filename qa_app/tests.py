import os
import json
import base64
import shutil
import tempfile
from django.test import TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.core.files.base import ContentFile
from django.conf import settings
from unittest.mock import patch

from .models import Category, KnowledgePage, PageImage, Tag

# Create a temporary directory for media files during testing
TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class BackendLogicTests(TransactionTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        # Clean up temporary media directory
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        # Clear seeded records from data migration 0002 to avoid conflicts
        KnowledgePage.objects.all().delete()
        Category.objects.all().delete()

        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.admin = User.objects.create_superuser(email='admin@test.com', password='password')
        self.client.login(email='admin@test.com', password='password')

        # Create standard test categories
        self.cat1 = Category.objects.create(id='cat-1', name='Database')
        self.cat2 = Category.objects.create(id='cat-2', name='Frontend')
        
        # Base64 test image data (a tiny 1x1 transparent GIF)
        self.base64_gif = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

    def test_get_db(self):
        """Test the /api/db endpoint returns all categories and pages with correct metadata."""
        page = KnowledgePage.objects.create(
            id='page-1',
            category=self.cat1,
            title='How to query?',
            date='2026-06-12',
            username='user1',
            question_text='Query question',
            resolution_text='Query resolution'
        )
        # Add an image
        PageImage.objects.create(
            id='img-1',
            page=page,
            name='diagram.png'
        )

        response = self.client.get(reverse('get_db'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify categories count and pageCount annotation
        self.assertIn('categories', data)
        self.assertEqual(len(data['categories']), 2)
        # Database category should have 1 page
        db_cat = next(c for c in data['categories'] if c['id'] == 'cat-1')
        self.assertEqual(db_cat['pageCount'], 1)
        # Frontend category should have 0 pages
        fe_cat = next(c for c in data['categories'] if c['id'] == 'cat-2')
        self.assertEqual(fe_cat['pageCount'], 0)

        # Verify pages output
        self.assertIn('pages', data)
        self.assertEqual(len(data['pages']), 1)
        self.assertEqual(data['pages'][0]['title'], 'How to query?')
        self.assertEqual(len(data['pages'][0]['images']), 1)

    def test_search_pages_filtering(self):
        """Test search filtering by query (q) and category."""
        p1 = KnowledgePage.objects.create(
            id='page-1', category=self.cat1, title='Postgres indexing issue',
            date='2026-06-01', username='alice', question_text='Slow index scan',
            resolution_text='Use GIN index'
        )
        p2 = KnowledgePage.objects.create(
            id='page-2', category=self.cat2, title='React rendering slow',
            date='2026-06-02', username='bob', question_text='Too many updates',
            resolution_text='Use memoization'
        )

        # Search by general query 'slow' -> matches both
        response = self.client.get(reverse('search_pages'), {'q': 'slow'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['pages']), 2)

        # Search by query 'Postgres' -> matches p1
        response = self.client.get(reverse('search_pages'), {'q': 'Postgres'})
        data = response.json()
        self.assertEqual(len(data['pages']), 1)
        self.assertEqual(data['pages'][0]['id'], 'page-1')

        # Filter by Category Database -> matches p1
        response = self.client.get(reverse('search_pages'), {'category': 'cat-1'})
        data = response.json()
        self.assertEqual(len(data['pages']), 1)
        self.assertEqual(data['pages'][0]['id'], 'page-1')

        # Filter by Category Frontend -> matches p2
        response = self.client.get(reverse('search_pages'), {'category': 'cat-2'})
        data = response.json()
        self.assertEqual(len(data['pages']), 1)
        self.assertEqual(data['pages'][0]['id'], 'page-2')

        # Filter by both category and query -> matches p1
        response = self.client.get(reverse('search_pages'), {'category': 'cat-1', 'q': 'slow'})
        data = response.json()
        self.assertEqual(len(data['pages']), 1)
        self.assertEqual(data['pages'][0]['id'], 'page-1')

    def test_search_pages_sorting(self):
        """Test search sorting options."""
        p1 = KnowledgePage.objects.create(
            id='page-1', category=self.cat1, title='A',
            date='2026-06-05', username='charlie'
        )
        p2 = KnowledgePage.objects.create(
            id='page-2', category=self.cat1, title='B',
            date='2026-06-10', username='alice'
        )
        p3 = KnowledgePage.objects.create(
            id='page-3', category=self.cat1, title='C',
            date='2026-06-01', username='bob'
        )

        # Date Descending (default): p2 (10th), p1 (5th), p3 (1st)
        response = self.client.get(reverse('search_pages'), {'sort': 'date-desc'})
        pages = response.json()['pages']
        self.assertEqual([p['id'] for p in pages], ['page-2', 'page-1', 'page-3'])

        # Date Ascending: p3 (1st), p1 (5th), p2 (10th)
        response = self.client.get(reverse('search_pages'), {'sort': 'date-asc'})
        pages = response.json()['pages']
        self.assertEqual([p['id'] for p in pages], ['page-3', 'page-1', 'page-2'])

        # User Ascending: alice (p2), bob (p3), charlie (p1)
        response = self.client.get(reverse('search_pages'), {'sort': 'user-asc'})
        pages = response.json()['pages']
        self.assertEqual([p['id'] for p in pages], ['page-2', 'page-3', 'page-1'])

        # User Descending: charlie (p1), bob (p3), alice (p2)
        response = self.client.get(reverse('search_pages'), {'sort': 'user-desc'})
        pages = response.json()['pages']
        self.assertEqual([p['id'] for p in pages], ['page-1', 'page-3', 'page-2'])

    def test_search_pages_pagination(self):
        """Test server-side pagination metadata and limits."""
        for i in range(15):
            KnowledgePage.objects.create(
                id=f'page-{i}', category=self.cat1, title=f'Title {i}',
                date='2026-06-01', username='user'
            )

        # Request page 1 with page_size 5
        response = self.client.get(reverse('search_pages'), {'page': 1, 'page_size': 5})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['pages']), 5)
        pagination = data['pagination']
        self.assertEqual(pagination['total'], 15)
        self.assertEqual(pagination['page'], 1)
        self.assertEqual(pagination['page_size'], 5)
        self.assertEqual(pagination['total_pages'], 3)
        self.assertTrue(pagination['has_next'])
        self.assertFalse(pagination['has_prev'])

        # Request page 3 with page_size 5
        response = self.client.get(reverse('search_pages'), {'page': 3, 'page_size': 5})
        data = response.json()
        self.assertEqual(len(data['pages']), 5)
        pagination = data['pagination']
        self.assertFalse(pagination['has_next'])
        self.assertTrue(pagination['has_prev'])

        # Request invalid page inputs (should default gracefully)
        response = self.client.get(reverse('search_pages'), {'page': 'invalid', 'page_size': -10})
        data = response.json()
        self.assertEqual(data['pagination']['page'], 1)
        self.assertEqual(data['pagination']['page_size'], 1)  # min size bound is 1

    def test_categories_crud(self):
        """Test categories POST (creation & edit) and DELETE views."""
        # Create category via POST
        payload = {'name': 'New Category'}
        response = self.client.post(
            reverse('categories'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['categories']), 3)  # cat-1, cat-2, and the new one
        new_cat = next(c for c in data['categories'] if c['name'] == 'New Category')
        new_cat_id = new_cat['id']
        self.assertTrue(new_cat_id.startswith('cat-'))

        # Edit/rename existing category
        payload = {'id': new_cat_id, 'name': 'Renamed Category'}
        response = self.client.post(
            reverse('categories'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        category_obj = Category.objects.get(id=new_cat_id)
        self.assertEqual(category_obj.name, 'Renamed Category')

        # Edit empty validation
        payload = {'id': new_cat_id, 'name': '   '}
        response = self.client.post(
            reverse('categories'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

        # Delete category
        response = self.client.delete(reverse('delete_category', kwargs={'cat_id': new_cat_id}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Category.objects.filter(id=new_cat_id).exists())

    def test_csrf_protection_enforced(self):
        """Test that POST/DELETE endpoints now enforce CSRF protection."""
        from django.test import Client
        
        # Instantiate a strict client that enforces CSRF
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(email='admin@test.com', password='password')

        # 1. Missing CSRF token should return 403 Forbidden
        payload = {'name': 'CSRF Hacker Cat'}
        response = csrf_client.post(
            reverse('categories'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403, "CSRF check failed: request was not blocked!")

        # 2. Delete endpoint missing CSRF token should return 403 Forbidden
        response = csrf_client.delete(reverse('delete_category', kwargs={'cat_id': 'cat-1'}))
        self.assertEqual(response.status_code, 403, "CSRF check failed: DELETE request was not blocked!")
        
        # 3. Providing a valid CSRF token should allow the request
        # First make a GET request to obtain the CSRF cookie
        csrf_client.get(reverse('index'))
        csrftoken = csrf_client.cookies['csrftoken'].value
        
        response = csrf_client.post(
            reverse('categories'),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrftoken
        )
        self.assertEqual(response.status_code, 200, "Valid CSRF token was rejected!")

    def test_save_page_new_and_update(self):
        """Test save_page view for new pages and page updates."""
        # Save new page
        payload = {
            'categoryId': 'cat-1',
            'title': 'Test Page Saving',
            'date': '2026-06-13',
            'username': 'tester',
            'questionText': 'How do tests work?',
            'resolutionText': 'Run manage.py test.',
            'images': []
        }
        response = self.client.post(
            reverse('save_page'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        page_id = data['page']['id']
        self.assertTrue(page_id.startswith('page-'))

        # Check DB state
        page = KnowledgePage.objects.get(id=page_id)
        self.assertEqual(page.title, 'Test Page Saving')
        self.assertEqual(str(page.date), '2026-06-13')

        # Update existing page
        payload['id'] = page_id
        payload['title'] = 'Updated Title'
        payload['date'] = ''  # sets date to None
        response = self.client.post(
            reverse('save_page'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.title, 'Updated Title')
        self.assertIsNone(page.date)

    def test_save_page_fallback_category(self):
        """Test save_page handles non-existent categoryIds gracefully by falling back."""
        payload = {
            'categoryId': 'non-existent-cat-id',
            'title': 'Fallback Test',
            'images': []
        }
        response = self.client.post(
            reverse('save_page'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        page_id = response.json()['page']['id']
        page = KnowledgePage.objects.get(id=page_id)
        # Should fallback to the first available category (cat-1)
        self.assertEqual(page.category.id, 'cat-1')

        # Test fallback when NO categories exist in DB
        Category.objects.all().delete()
        response = self.client.post(
            reverse('save_page'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        page_id2 = response.json()['page']['id']
        page2 = KnowledgePage.objects.get(id=page_id2)
        # Should create cat-1 General
        self.assertEqual(page2.category.id, 'cat-1')
        self.assertEqual(page2.category.name, 'General')

    def test_save_page_with_base64_image(self):
        """Test saving page with base64 image decodes it, saves file to disk, and updates PageImage.file."""
        payload = {
            'categoryId': 'cat-1',
            'title': 'Page with Image',
            'images': [
                {
                    'id': 'img-test-1',
                    'name': 'screenshot.gif',
                    'dataUrl': self.base64_gif
                }
            ]
        }
        response = self.client.post(
            reverse('save_page'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verify database record
        img = PageImage.objects.get(id='img-test-1')
        self.assertEqual(img.name, 'screenshot.gif')
        self.assertTrue(img.file.name.startswith('page_images/img-test-1.'))
        self.assertTrue(img.file.name.endswith('.webp'))
        
        # Verify physical file existence in temporary media directory
        physical_path = os.path.join(TEMP_MEDIA_ROOT, img.file.name)
        self.assertTrue(os.path.exists(physical_path))
        self.assertGreater(os.path.getsize(physical_path), 0)

        # Verify it is a valid WebP image
        from PIL import Image
        with Image.open(physical_path) as pil_img:
            self.assertEqual(pil_img.format, 'WEBP')

        # Verify that serialization contains the media file's URL
        page_data = data['page']
        self.assertEqual(len(page_data['images']), 1)
        self.assertEqual(page_data['images'][0]['dataUrl'], img.file.url)

    def test_image_cascade_and_deletion_cleanup(self):
        """Test deleting a page or removing an image cleans up file storage."""
        # 1. Create page with image
        payload = {
            'categoryId': 'cat-1',
            'title': 'Page to Delete',
            'images': [
                {
                    'id': 'img-cleanup-1',
                    'name': 'screenshot.gif',
                    'dataUrl': self.base64_gif
                }
            ]
        }
        response = self.client.post(
            reverse('save_page'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        page_id = response.json()['page']['id']
        img = PageImage.objects.get(id='img-cleanup-1')
        file_path = os.path.join(TEMP_MEDIA_ROOT, img.file.name)
        self.assertTrue(os.path.exists(file_path))

        # 2. Update page, removing the image
        payload['id'] = page_id
        payload['images'] = []
        response = self.client.post(
            reverse('save_page'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        # Verify image model is gone and file on disk is deleted
        self.assertFalse(PageImage.objects.filter(id='img-cleanup-1').exists())
        self.assertFalse(os.path.exists(file_path))

        # 3. Create a new image on the page
        payload['images'] = [
            {
                'id': 'img-cleanup-2',
                'name': 'screenshot2.gif',
                'dataUrl': self.base64_gif
            }
        ]
        response = self.client.post(
            reverse('save_page'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        img2 = PageImage.objects.get(id='img-cleanup-2')
        file_path2 = os.path.join(TEMP_MEDIA_ROOT, img2.file.name)
        self.assertTrue(os.path.exists(file_path2))

        # 4. Delete the page via endpoint -> checks cascade file cleanup
        response = self.client.delete(reverse('delete_page', kwargs={'page_id': page_id}))
        self.assertEqual(response.status_code, 200)
        
        # Verify models are deleted
        self.assertFalse(KnowledgePage.objects.filter(id=page_id).exists())
        self.assertFalse(PageImage.objects.filter(id='img-cleanup-2').exists())
        # Verify file on disk is deleted
        self.assertFalse(os.path.exists(file_path2))

    def test_search_by_image_extracted_text(self):
        """Test searching query terms finds pages that match text extracted from their images."""
        p = KnowledgePage.objects.create(
            id='page-ocr-search', category=self.cat1, title='OCR Search Target',
            date='2026-06-13', username='bob'
        )
        PageImage.objects.create(
            id='img-ocr-search', page=p, name='diagram.png',
            extracted_text='Exception in thread main: java.lang.NullPointerException'
        )

        # Search for "NullPointerException" -> should match the image's extracted text and return p
        response = self.client.get(reverse('search_pages'), {'q': 'NullPointerException'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['pages']), 1)
        self.assertEqual(data['pages'][0]['id'], 'page-ocr-search')
        self.assertEqual(data['pages'][0]['images'][0]['extractedText'], 'Exception in thread main: java.lang.NullPointerException')

    @patch('qa_app.views.extract_text_from_image')
    def test_save_page_triggers_ocr(self, mock_ocr):
        """Test saving a new image via save_page calls the OCR helper and saves results in the database."""
        mock_ocr.return_value = ("Mocked OCR Text Results", [{'text': 'Mocked', 'left': 10, 'top': 10, 'width': 20, 'height': 5}])
        
        payload = {
            'categoryId': 'cat-1',
            'title': 'OCR Save Test',
            'images': [
                {
                    'id': 'img-ocr-save-1',
                    'name': 'test_ocr.png',
                    'dataUrl': self.base64_gif
                }
            ]
        }
        response = self.client.post(
            reverse('save_page'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify OCR helper was called
        self.assertTrue(mock_ocr.called)
        
        # Since OCR is now synchronous, verify text and ocr_data were stored immediately
        img = PageImage.objects.get(id='img-ocr-save-1')
        self.assertIsNotNone(img)
        self.assertEqual(img.extracted_text, "Mocked OCR Text Results")
        self.assertEqual(img.ocr_data, [{'text': 'Mocked', 'left': 10, 'top': 10, 'width': 20, 'height': 5}])
        
        # Verify serialized response contains the OCR results
        data = response.json()
        self.assertEqual(data['page']['images'][0]['extractedText'], "Mocked OCR Text Results")
        self.assertEqual(data['page']['images'][0]['ocrData'], [{'text': 'Mocked', 'left': 10, 'top': 10, 'width': 20, 'height': 5}])


class TagModelTests(TransactionTestCase):
    def setUp(self):
        Category.objects.all().delete()
        KnowledgePage.objects.all().delete()
        Tag.objects.all().delete()
        
        self.cat = Category.objects.create(id='test-cat', name='Test Category')
        self.page1 = KnowledgePage.objects.create(id='p1', category=self.cat, title='Page 1')
        self.page2 = KnowledgePage.objects.create(id='p2', category=self.cat, title='Page 2')

    def test_tag_creation(self):
        tag = Tag.objects.create(name='python')
        self.assertEqual(tag.name, 'python')
        self.assertEqual(str(tag), 'python')
        
    def test_many_to_many_relationship(self):
        tag1 = Tag.objects.create(name='django')
        tag2 = Tag.objects.create(name='react')
        
        # Add tags to pages
        self.page1.tags.add(tag1, tag2)
        self.page2.tags.add(tag1)
        
        # Verify from page perspective
        self.assertEqual(self.page1.tags.count(), 2)
        self.assertEqual(self.page2.tags.count(), 1)
        self.assertTrue(self.page2.tags.filter(name='django').exists())
        
        # Verify from tag perspective
        self.assertEqual(tag1.pages.count(), 2)
        self.assertEqual(tag2.pages.count(), 1)
        
    def test_tag_removal_preserves_tag(self):
        tag = Tag.objects.create(name='javascript')
        self.page1.tags.add(tag)
        
        # Remove the tag from the page
        self.page1.tags.remove(tag)
        
        # Verify page has no tags
        self.assertEqual(self.page1.tags.count(), 0)
        
        # Verify tag itself still exists in database
        self.assertTrue(Tag.objects.filter(name='javascript').exists())
