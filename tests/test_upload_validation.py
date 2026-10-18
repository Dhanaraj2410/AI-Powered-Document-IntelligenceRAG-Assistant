from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings

from rag_app.api.serializers import DocumentUploadSerializer


class UploadValidationTests(SimpleTestCase):
    def test_rejects_unlisted_extensions(self):
        serializer = DocumentUploadSerializer(data={
            'file': SimpleUploadedFile('payload.exe', b'MZ')
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('Unsupported file type.', str(serializer.errors))

    @override_settings(MAX_UPLOAD_SIZE=4)
    def test_rejects_oversized_documents(self):
        serializer = DocumentUploadSerializer(data={
            'file': SimpleUploadedFile('notes.txt', b'12345', content_type='text/plain')
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('upload size limit', str(serializer.errors))

    def test_rejects_pdf_extension_with_wrong_signature(self):
        serializer = DocumentUploadSerializer(data={
            'file': SimpleUploadedFile('report.pdf', b'not a PDF', content_type='application/pdf')
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('signature', str(serializer.errors))
