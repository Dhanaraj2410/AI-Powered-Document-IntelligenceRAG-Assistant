from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from rag_app.models import Conversation, Message

class APIEndpointsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client.force_authenticate(user=self.user)

    def test_health_check_endpoint(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')
        self.assertEqual(response.data['version'], '2.0.0')

    def test_documents_list_endpoint(self):
        response = self.client.get('/api/documents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_collections_list_endpoint(self):
        response = self.client.get('/api/collections/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_documents_endpoint_requires_authentication(self):
        self.client.logout()
        response = self.client.get('/api/documents/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_export_is_scoped_to_the_authenticated_user(self):
        conversation = Conversation.objects.create(user=self.user, title='Test')
        message = Message.objects.create(conversation=conversation, role='assistant', content='Evidence based answer.')
        response = self.client.post('/api/export/', {'message_id': message.id, 'format': 'pdf'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')

        other_user = User.objects.create_user(username='other', password='password123')
        other_conversation = Conversation.objects.create(user=other_user, title='Private')
        private_message = Message.objects.create(conversation=other_conversation, role='assistant', content='Private')
        response = self.client.post('/api/export/', {'message_id': private_message.id, 'format': 'pdf'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
