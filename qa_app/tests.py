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
        # Clear seeded records from data migration to avoid conflicts
        KnowledgePage.objects.all().delete()
        Category.objects.all().delete()

        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.admin = User.objects.create_superuser(email='admin@test.com', password='password')
        self.client.login(email='admin@test.com', password='password')

        # Create standard test categories
        self.cat1 = Category.objects.create(name='Database')
        self.cat2 = Category.objects.create(name='Frontend')

        # Base64 test image data (a tiny 1x1 transparent GIF)
        self.base64_gif = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

    def test_get_db(self):
        """Test the /api/db endpoint returns all categories and pages with correct metadata."""
        page = KnowledgePage.objects.create(
            category=self.cat1,
            title='How to query?',
            date='2026-06-12',
            username='user1',
            question_text='Query question',
            resolution_text='Query resolution'
        )
        # Add an image
        PageImage.objects.create(
            page=page,
            name='diagram.png'
        )

        response = self.client.get(reverse('get_db'))
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify categories count and pageCount annotation
        self.assertIn('categories', data)
        self.assertEqual(len(data['categories']), 2)
        db_cat = next(c for c in data['categories'] if c['id'] == self.cat1.id)
        self.assertEqual(db_cat['pageCount'], 1)
        fe_cat = next(c for c in data['categories'] if c['id'] == self.cat2.id)
        self.assertEqual(fe_cat['pageCount'], 0)

        # Verify pages output
        self.assertIn('pages', data)
        self.assertEqual(len(data['pages']), 1)
        self.assertEqual(data['pages'][0]['title'], 'How to query?')
        self.assertEqual(data['pages'][0]['id'], page.id)
        self.assertEqual(len(data['pages'][0]['images']), 1)

    def test_search_pages_filtering(self):
        """Test search filtering by query (q) and category."""
        p1 = KnowledgePage.objects.create(
            category=self.cat1, title='Postgres indexing issue',
            date='2026-06-01', username='alice', question_text='Slow index scan',
            resolution_text='Use GIN index'
        )
        p2 = KnowledgePage.objects.create(
            category=self.cat2, title='React rendering slow',
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
        self.assertEqual(data['pages'][0]['id'], p1.id)

        # Filter by Category Database -> matches p1
        response = self.client.get(reverse('search_pages'), {'category': self.cat1.id})
        data = response.json()
        self.assertEqual(len(data['pages']), 1)
        self.assertEqual(data['pages'][0]['id'], p1.id)

        # Filter by Category Frontend -> matches p2
        response = self.client.get(reverse('search_pages'), {'category': self.cat2.id})
        data = response.json()
        self.assertEqual(len(data['pages']), 1)
        self.assertEqual(data['pages'][0]['id'], p2.id)

        # Filter by both category and query -> matches p1
        response = self.client.get(reverse('search_pages'), {'category': self.cat1.id, 'q': 'slow'})
        data = response.json()
        self.assertEqual(len(data['pages']), 1)
        self.assertEqual(data['pages'][0]['id'], p1.id)

    def test_search_pages_sorting(self):
        """Test search sorting options."""
        p1 = KnowledgePage.objects.create(
            category=self.cat1, title='A',
            date='2026-06-05', username='charlie'
        )
        p2 = KnowledgePage.objects.create(
            category=self.cat1, title='B',
            date='2026-06-10', username='alice'
        )
        p3 = KnowledgePage.objects.create(
            category=self.cat1, title='C',
            date='2026-06-01', username='bob'
        )

        # Date Descending (default): p2 (10th), p1 (5th), p3 (1st)
        response = self.client.get(reverse('search_pages'), {'sort': 'date-desc'})
        pages = response.json()['pages']
        self.assertEqual([p['id'] for p in pages], [p2.id, p1.id, p3.id])

        # Date Ascending: p3 (1st), p1 (5th), p2 (10th)
        response = self.client.get(reverse('search_pages'), {'sort': 'date-asc'})
        pages = response.json()['pages']
        self.assertEqual([p['id'] for p in pages], [p3.id, p1.id, p2.id])

        # User Ascending: alice (p2), bob (p3), charlie (p1)
        response = self.client.get(reverse('search_pages'), {'sort': 'user-asc'})
        pages = response.json()['pages']
        self.assertEqual([p['id'] for p in pages], [p2.id, p3.id, p1.id])

        # User Descending: charlie (p1), bob (p3), alice (p2)
        response = self.client.get(reverse('search_pages'), {'sort': 'user-desc'})
        pages = response.json()['pages']
        self.assertEqual([p['id'] for p in pages], [p1.id, p3.id, p2.id])

    def test_search_pages_pagination(self):
        """Test server-side pagination metadata and limits."""
        for i in range(15):
            KnowledgePage.objects.create(
                category=self.cat1, title=f'Title {i}',
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
        self.assertEqual(data['pagination']['page_size'], 1)

    def test_categories_crud(self):
        """Test categories POST (creation & edit) and DELETE views."""
        payload = {'name': 'New Category'}
        response = self.client.post(
            reverse('categories'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['categories']), 3)
        new_cat = next(c for c in data['categories'] if c['name'] == 'New Category')
        new_cat_id = new_cat['id']
        self.assertIsInstance(new_cat_id, int)

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
        """Test that POST/DELETE endpoints enforce CSRF protection."""
        from django.test import Client

        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(email='admin@test.com', password='password')

        # 1. Missing CSRF token should return 403 Forbidden
        payload = {'name': 'CSRF Hacker Cat'}
        response = csrf_client.post(
            reverse('categories'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

        # 2. Delete endpoint missing CSRF token should return 403 Forbidden
        response = csrf_client.delete(reverse('delete_category', kwargs={'cat_id': self.cat1.id}))
        self.assertEqual(response.status_code, 403)

        # 3. Providing a valid CSRF token should allow the request
        csrf_client.get(reverse('index'))
        csrftoken = csrf_client.cookies['csrftoken'].value

        response = csrf_client.post(
            reverse('categories'),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrftoken
        )
        self.assertEqual(response.status_code, 200)

    def test_save_page_new_and_update(self):
        """Test save_page view for new pages and page updates."""
        payload = {
            'categoryId': self.cat1.id,
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
        self.assertIsInstance(page_id, int)

        # Check DB state
        page = KnowledgePage.objects.get(id=page_id)
        self.assertEqual(page.title, 'Test Page Saving')
        self.assertEqual(str(page.date), '2026-06-13')

        # Update existing page
        payload['id'] = page_id
        payload['title'] = 'Updated Title'
        payload['date'] = ''
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
            'categoryId': 999999,
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
        self.assertEqual(page.category.id, self.cat1.id)

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
        self.assertIsNotNone(page2.category.id)
        self.assertEqual(page2.category.name, 'General')

    @patch('qa_app.tasks.run_florence_ocr_and_redact', return_value=('Sanitized text', []))
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_save_page_with_base64_image(self, mock_florence):
        """Test saving page with base64 image enqueues task, converts to WebP, and updates PageImage."""
        payload = {
            'categoryId': self.cat1.id,
            'title': 'Page with Image',
            'images': [
                {
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

        img_id = data['page']['images'][0]['id']
        img = PageImage.objects.get(id=img_id)
        self.assertEqual(img.name, 'screenshot.gif')
        self.assertTrue(img.file.name.endswith('.webp'))

        # Verify physical file existence
        physical_path = os.path.join(TEMP_MEDIA_ROOT, img.file.name)
        self.assertTrue(os.path.exists(physical_path))
        self.assertGreater(os.path.getsize(physical_path), 0)

        # Verify format
        from PIL import Image
        with Image.open(physical_path) as pil_img:
            self.assertEqual(pil_img.format, 'WEBP')

        # Verify serialization
        self.assertEqual(data['page']['images'][0]['dataUrl'], img.file.url)

    def test_image_cascade_and_deletion_cleanup(self):
        """Test deleting a page or removing an image cleans up file storage."""
        # 1. Create page with image
        payload = {
            'categoryId': self.cat1.id,
            'title': 'Page to Delete',
            'images': [
                {
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
        img_id = response.json()['page']['images'][0]['id']
        img = PageImage.objects.get(id=img_id)
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
        self.assertFalse(PageImage.objects.filter(id=img_id).exists())
        self.assertFalse(os.path.exists(file_path))

        # 3. Create a new image on the page
        payload['images'] = [
            {
                'name': 'screenshot2.gif',
                'dataUrl': self.base64_gif
            }
        ]
        response = self.client.post(
            reverse('save_page'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        img2_id = response.json()['page']['images'][0]['id']
        img2 = PageImage.objects.get(id=img2_id)
        file_path2 = os.path.join(TEMP_MEDIA_ROOT, img2.file.name)
        self.assertTrue(os.path.exists(file_path2))

        # 4. Delete the page via endpoint -> checks cascade file cleanup
        response = self.client.delete(reverse('delete_page', kwargs={'page_id': page_id}))
        self.assertEqual(response.status_code, 200)

        self.assertFalse(KnowledgePage.objects.filter(id=page_id).exists())
        self.assertFalse(PageImage.objects.filter(id=img2_id).exists())
        self.assertFalse(os.path.exists(file_path2))

    def test_search_by_image_extracted_text(self):
        """Test searching query terms finds pages that match text extracted from their images."""
        p = KnowledgePage.objects.create(
            category=self.cat1, title='OCR Search Target',
            date='2026-06-13', username='bob'
        )
        PageImage.objects.create(
            page=p, name='diagram.png',
            extracted_text='Exception in thread main: java.lang.NullPointerException'
        )

        response = self.client.get(reverse('search_pages'), {'q': 'NullPointerException'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['pages']), 1)
        self.assertEqual(data['pages'][0]['id'], p.id)
        self.assertEqual(data['pages'][0]['images'][0]['extractedText'],
                         'Exception in thread main: java.lang.NullPointerException')

    @patch('qa_app.tasks.run_florence_ocr_and_redact')
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_save_page_triggers_ocr(self, mock_ocr):
        """Test saving a new image via save_page executes the background task and updates results in database."""
        mock_ocr.return_value = ("Mocked OCR Text Results",
                                 [{'text': 'Mocked', 'left': 10, 'top': 10, 'width': 20, 'height': 5}])

        payload = {
            'categoryId': self.cat1.id,
            'title': 'OCR Save Test',
            'images': [
                {
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
        self.assertTrue(mock_ocr.called)

        img_id = response.json()['page']['images'][0]['id']
        img = PageImage.objects.get(id=img_id)
        self.assertIsNotNone(img)
        self.assertEqual(img.extracted_text, "Mocked OCR Text Results")
        self.assertEqual(img.ocr_data, [{'text': 'Mocked', 'left': 10, 'top': 10, 'width': 20, 'height': 5}])
        self.assertEqual(img.ocr_status, 'completed')

class TagModelTests(TransactionTestCase):
    def setUp(self):
        Category.objects.all().delete()
        KnowledgePage.objects.all().delete()
        Tag.objects.all().delete()

        self.cat = Category.objects.create(name='Test Category')
        self.page1 = KnowledgePage.objects.create(category=self.cat, title='Page 1')
        self.page2 = KnowledgePage.objects.create(category=self.cat, title='Page 2')

    def test_tag_creation(self):
        tag = Tag.objects.create(name='python')
        self.assertEqual(tag.name, 'python')
        self.assertEqual(str(tag), 'python')

    def test_many_to_many_relationship(self):
        tag1 = Tag.objects.create(name='django')
        tag2 = Tag.objects.create(name='react')

        self.page1.tags.add(tag1, tag2)
        self.page2.tags.add(tag1)

        self.assertEqual(self.page1.tags.count(), 2)
        self.assertEqual(self.page2.tags.count(), 1)
        self.assertTrue(self.page2.tags.filter(name='django').exists())

        self.assertEqual(tag1.pages.count(), 2)
        self.assertEqual(tag2.pages.count(), 1)

    def test_tag_removal_preserves_tag(self):
        tag = Tag.objects.create(name='javascript')
        self.page1.tags.add(tag)
        self.page1.tags.remove(tag)
        self.assertEqual(self.page1.tags.count(), 0)
        self.assertTrue(Tag.objects.filter(name='javascript').exists())
