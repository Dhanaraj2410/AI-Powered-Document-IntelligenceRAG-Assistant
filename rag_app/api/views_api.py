from rest_framework import status, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import close_old_connections
from threading import Thread
from rag_app.models import DocumentCollection, Document, Conversation, Message, Bookmark, Feedback, EvaluationResult
from rag_app.services.rag_service import RAGService
from rag_app.services.analysis_service import AnalysisService
from rag_app.services.comparison_service import ComparisonService
from rag_app.services.search_service import SearchService
from .serializers import (
    DocumentCollectionSerializer, DocumentSerializer, DocumentChunkSerializer,
    ConversationSerializer, MessageSerializer, BookmarkSerializer, FeedbackSerializer,
    DocumentUploadSerializer, ChatQuerySerializer, SummaryRequestSerializer,
    SearchRequestSerializer, CompareRequestSerializer, EvaluationResultSerializer
)


def _process_document_async(document_id):
    close_old_connections()
    try:
        RAGService().process_document(document_id)
    finally:
        close_old_connections()

class HealthCheckView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            "status": "healthy",
            "service": "AI Document Intelligence & Enterprise RAG Assistant",
            "version": "2.0.0"
        })


class DocumentCollectionViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentCollectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DocumentCollection.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        file_field = instance.file
        instance.delete()  # cascades chunks first, preserving tenant ownership checks
        if file_field:
            file_field.delete(save=False)
        from rag_app.services.vector_service import VectorService
        VectorService.rebuild_from_database()

    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        doc = self.get_object()
        doc.status = 'uploaded'
        doc.processing_error = ''
        doc.save(update_fields=['status', 'processing_error'])
        Thread(target=_process_document_async, args=(doc.id,), daemon=True).start()
        return Response({
            "success": True,
            "document": DocumentSerializer(doc).data,
            "message": "Document reprocessing started."
        })

    @action(detail=True, methods=['get'])
    def analyze(self, request, pk=None):
        doc = self.get_object()
        result = AnalysisService.analyze_document_and_generate_questions(doc.id)
        return Response(result)


class DocumentUploadAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = serializer.validated_data['file']
        collection_id = serializer.validated_data.get('collection_id')
        collection = None
        if collection_id:
            collection = get_object_or_404(DocumentCollection, id=collection_id, user=request.user)

        title = serializer.validated_data.get('title') or uploaded_file.name

        doc = Document.objects.create(
            user=request.user,
            collection=collection,
            title=title,
            file=uploaded_file,
            file_size=uploaded_file.size,
            status='uploaded'
        )

        Thread(target=_process_document_async, args=(doc.id,), daemon=True).start()

        return Response({
            "success": True,
            "document": DocumentSerializer(doc).data,
            "suggested_questions": doc.suggested_questions,
            "message": "Document uploaded; ingestion started. Poll the document endpoint for status."
        }, status=status.HTTP_202_ACCEPTED)


class ChatAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChatQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        question = serializer.validated_data['question']
        conversation_id = serializer.validated_data.get('conversation_id')
        document_id = serializer.validated_data.get('document_id')
        collection_id = serializer.validated_data.get('collection_id')

        rag_service = RAGService()
        result = rag_service.query_rag(
            question=question,
            user_id=request.user.id,
            conversation_id=conversation_id,
            document_id=document_id,
            collection_id=collection_id
        )

        return Response(result, status=status.HTTP_200_OK)


class SearchAPIView(APIView):
    """Executes standalone Hybrid Search (FAISS + BM25) for inspection."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SearchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        values = serializer.validated_data

        result = SearchService.execute_search(
            query=values['query'],
            user_id=request.user.id,
            document_id=values.get('document_id'),
            collection_id=values.get('collection_id')
        )

        return Response(result, status=status.HTTP_200_OK)


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)


class SummaryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SummaryRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        document_id = serializer.validated_data['document_id']
        mode = serializer.validated_data['mode']

        rag_service = RAGService()
        summary_result = rag_service.generate_summary(document_id, request.user.id, mode=mode)
        summary_status = status.HTTP_200_OK if summary_result["success"] else status.HTTP_400_BAD_REQUEST

        return Response(summary_result, status=summary_status)


class CompareAPIView(APIView):
    """Executes multi-document comparison analysis between Document A and Document B."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CompareRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        values = serializer.validated_data

        result = ComparisonService.compare_documents(values['doc_a_id'], values['doc_b_id'], request.user.id)
        res_status = status.HTTP_200_OK if result["success"] else status.HTTP_400_BAD_REQUEST

        return Response(result, status=res_status)


class BookmarkViewSet(viewsets.ModelViewSet):
    """CRUD API for saving and managing user bookmarks."""
    serializer_class = BookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FeedbackAPIView(APIView):
    """Submits user rating (+1 / -1) and feedback comments on assistant answers."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        message_id = request.data.get('message_id')
        rating = request.data.get('rating')
        comment = request.data.get('comment', '')

        if not message_id or rating not in [1, -1]:
            return Response({"error": "Valid message_id and rating (+1 or -1) are required."}, status=status.HTTP_400_BAD_REQUEST)

        msg = get_object_or_404(Message, id=message_id, conversation__user=request.user)

        feedback, created = Feedback.objects.update_or_create(
            user=request.user,
            message=msg,
            defaults={'rating': rating, 'comment': comment}
        )

        return Response({
            "success": True,
            "feedback_id": feedback.id,
            "rating": feedback.rating,
            "message": "Feedback recorded successfully."
        }, status=status.HTTP_200_OK)


class EvaluationResultViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EvaluationResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = EvaluationResult.objects.all()
