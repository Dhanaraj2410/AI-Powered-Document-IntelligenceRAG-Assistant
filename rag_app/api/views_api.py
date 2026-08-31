from rest_framework import status, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rag_app.models import DocumentCollection, Document, Conversation, Message, Bookmark, Feedback, EvaluationResult
from rag_app.services.rag_service import RAGService
from rag_app.services.analysis_service import AnalysisService
from rag_app.services.comparison_service import ComparisonService
from rag_app.services.search_service import SearchService
from .serializers import (
    DocumentCollectionSerializer, DocumentSerializer, DocumentChunkSerializer,
    ConversationSerializer, MessageSerializer, BookmarkSerializer, FeedbackSerializer,
    DocumentUploadSerializer, ChatQuerySerializer, SummaryRequestSerializer, EvaluationResultSerializer
)

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

    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        doc = self.get_object()
        rag_service = RAGService()
        success = rag_service.process_document(doc.id)
        
        doc.refresh_from_db()
        return Response({
            "success": success,
            "document": DocumentSerializer(doc).data,
            "message": "Document reprocessed successfully." if success else doc.processing_error
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
        if not uploaded_file.name.lower().endswith('.pdf'):
            return Response({"error": "Only PDF documents are supported."}, status=status.HTTP_400_BAD_REQUEST)

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

        rag_service = RAGService()
        process_success = rag_service.process_document(doc.id)
        doc.refresh_from_db()

        res_status = status.HTTP_201_CREATED if process_success else status.HTTP_400_BAD_REQUEST

        return Response({
            "success": process_success,
            "document": DocumentSerializer(doc).data,
            "suggested_questions": doc.suggested_questions,
            "message": "Document uploaded and indexed successfully." if process_success else f"Upload failed: {doc.processing_error}"
        }, status=res_status)


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
        query = request.data.get('query', '').strip()
        doc_id = request.data.get('document_id')
        coll_id = request.data.get('collection_id')

        if not query:
            return Response({"error": "Query string is required."}, status=status.HTTP_400_BAD_REQUEST)

        result = SearchService.execute_search(
            query=query,
            user_id=request.user.id,
            document_id=int(doc_id) if doc_id else None,
            collection_id=int(coll_id) if coll_id else None
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
        doc_a_id = request.data.get('doc_a_id')
        doc_b_id = request.data.get('doc_b_id')

        if not doc_a_id or not doc_b_id:
            return Response({"error": "Both doc_a_id and doc_b_id parameters are required."}, status=status.HTTP_400_BAD_REQUEST)

        result = ComparisonService.compare_documents(int(doc_a_id), int(doc_b_id), request.user.id)
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
