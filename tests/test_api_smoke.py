from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient


class APIEndpointSmokeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='api-smoke', password='password123')

    def test_health_endpoint_is_public(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'healthy')

    def test_protected_api_lists_require_authentication(self):
        paths = (
            '/api/collections/', '/api/documents/', '/api/conversations/',
            '/api/bookmarks/', '/api/evaluations/',
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 403)

    def test_authenticated_api_lists_render(self):
        self.client.force_authenticate(user=self.user)
        paths = (
            '/api/collections/', '/api/documents/', '/api/conversations/',
            '/api/bookmarks/', '/api/evaluations/',
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_invalid_requests_return_json_validation_errors(self):
        self.client.force_authenticate(user=self.user)
        invalid_requests = (
            ('/api/chat/', {}),
            ('/api/search/', {}),
            ('/api/summary/', {}),
            ('/api/compare/', {}),
            ('/api/upload/', {}),
            ('/api/feedback/', {}),
            ('/api/export/', {}),
        )
        for path, payload in invalid_requests:
            with self.subTest(path=path):
                response = self.client.post(path, payload, format='json')
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response['Content-Type'], 'application/json')
