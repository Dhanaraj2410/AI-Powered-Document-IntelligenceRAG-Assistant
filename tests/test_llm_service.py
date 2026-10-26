from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from rag_app.services.llm_service import LLMService


class LLMServiceTests(SimpleTestCase):
    @override_settings(GEMINI_API_KEY='real-key', OPENAI_API_KEY='')
    def test_provider_configuration_detects_real_gemini_key(self):
        self.assertTrue(LLMService.is_configured())

    @override_settings(GEMINI_API_KEY='test-key', GEMINI_MODEL='gemini-3.8-flash')
    @patch('google.genai.Client')
    def test_gemini_is_used_with_configured_model(self, client_class):
        response = SimpleNamespace(text='Gemini answer')
        client = Mock()
        client.models.generate_content.return_value = response
        client_class.return_value = client

        result = LLMService.generate_response([
            {'role': 'system', 'content': 'Be helpful.'},
            {'role': 'user', 'content': 'Hello'},
        ])

        self.assertEqual(result['content'], 'Gemini answer')
        self.assertTrue(result['success'])
        call = client.models.generate_content.call_args
        self.assertEqual(call.kwargs['model'], 'gemini-3.8-flash')
        self.assertIn('Be helpful.', call.kwargs['contents'])
        self.assertIn('Hello', call.kwargs['contents'])
        self.assertEqual(call.kwargs['config'].temperature, 0.2)

    @override_settings(GEMINI_API_KEY='your_gemini_api_key_here', OPENAI_API_KEY='')
    def test_missing_provider_key_uses_local_grounded_fallback(self):
        result = LLMService.generate_response([
            {'role': 'user', 'content': (
                'DOCUMENT CONTEXT:\n'
                '<source id="1" document="Report" page="2">Revenue increased.</source>\n'
                'USER QUESTION:\nWhat increased?'
            )},
        ])

        self.assertTrue(result['success'])
        self.assertIn('Revenue increased.', result['content'])
