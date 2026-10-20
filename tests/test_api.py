from django.test import TestCase
from django.contrib.auth.models import User
from django.test import RequestFactory
from rest_framework.test import APIClient
from rest_framework import status
from rag_app.models import Conversation, Message, DocumentCollection, Document
from unittest.mock import patch

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

    def test_create_collection_is_owned_by_authenticated_user(self):
        response = self.client.post(
            '/api/collections/',
            {'name': 'Automation Test Collection', 'description': 'Smoke test'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Automation Test Collection')
        self.assertEqual(DocumentCollection.objects.get(pk=response.data['id']).user, self.user)

    @patch('rag_app.api.views_api.RAGService.generate_summary')
    def test_summary_endpoint_returns_generated_summary(self, generate_summary):
        generate_summary.return_value = {
            'success': True,
            'mode': 'executive',
            'document_title': 'Report',
            'summary': 'Grounded summary',
            'error': '',
        }
        response = self.client.post(
            '/api/summary/',
            {'document_id': 1, 'mode': 'executive'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['summary'], 'Grounded summary')

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

    @patch('rag_app.api.views_api.RAGService.query_rag')
    def test_chat_returns_rag_result(self, query_rag):
        query_rag.return_value = {
            'conversation_id': 10,
            'message_id': 20,
            'answer': 'Grounded answer',
            'sources': [],
            'latency_metrics': {},
            'grounding_result': {},
        }
        response = self.client.post('/api/chat/', {'question': 'What is in the report?'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['answer'], 'Grounded answer')

    @patch('rag_app.api.views_api.RAGService.query_rag', side_effect=RuntimeError('backend unavailable'))
    def test_chat_returns_json_error_when_rag_fails(self, query_rag):
        response = self.client.post('/api/chat/', {'question': 'What is in the report?'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('chat service', response.data['error'].lower())

    @patch('rag_app.views.render')
    def test_chat_scope_links_select_owned_document_and_collection(self, render):
        collection = DocumentCollection.objects.create(user=self.user, name='Reports')
        document = Document.objects.create(
            user=self.user,
            collection=collection,
            title='Annual Report',
            status='completed',
        )
        request = RequestFactory().get(f'/chat/?doc_id={document.id}&coll_id={collection.id}')
        request.user = self.user
        from rag_app.views import chat_view
        chat_view(request)
        context = render.call_args.args[2]
        self.assertEqual(context['selected_doc_id'], str(document.id))
        self.assertEqual(context['selected_collection_id'], str(collection.id))
