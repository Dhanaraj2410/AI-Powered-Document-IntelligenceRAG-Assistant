from django.contrib.auth.models import User
from django.test import TestCase
from django.template.base import Template

from rag_app.models import Document, DocumentCollection


class WebsitePageSmokeTests(TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='pageuser', password='password123')
        self.collection = DocumentCollection.objects.create(user=self.user, name='Smoke Collection')
        self.document = Document.objects.create(
            user=self.user,
            collection=self.collection,
            title='Smoke Document',
            status='completed',
            page_count=1,
            chunk_count=0,
        )

        # Django 5.2's template-context capture uses copy(super()), which is
        # incompatible with Python 3.14. This smoke test only needs HTTP
        # status, so render directly without the test instrumentation hook.
        self._original_template_render = Template._render
        Template._render = lambda template, context: template.nodelist.render(context)

    def tearDown(self):
        Template._render = self._original_template_render
        super().tearDown()

    def test_public_pages_render(self):
        for path in ('/', '/login/', '/register/'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)

    def test_authenticated_pages_render(self):
        self.client.force_login(self.user)
        paths = (
            '/dashboard/', '/documents/', '/collections/',
            f'/document/{self.document.id}/', '/chat/', '/search/',
            '/compare/', '/conversations/', '/bookmarks/', '/analytics/',
            '/evaluation/', '/profile/',
        )
        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)

    def test_protected_pages_redirect_anonymous_users(self):
        for path in ('/dashboard/', '/documents/', '/chat/', '/profile/'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertIn('/login/', response.url)
