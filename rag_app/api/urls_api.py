from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_api import (
    HealthCheckView, DocumentCollectionViewSet, DocumentViewSet,
    DocumentUploadAPIView, ChatAPIView, SearchAPIView, ConversationViewSet,
    SummaryAPIView, CompareAPIView, BookmarkViewSet, FeedbackAPIView,
    EvaluationResultViewSet
)

router = DefaultRouter()
router.register(r'collections', DocumentCollectionViewSet, basename='collection')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'bookmarks', BookmarkViewSet, basename='bookmark')
router.register(r'evaluations', EvaluationResultViewSet, basename='evaluation')

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='api-health'),
    path('upload/', DocumentUploadAPIView.as_view(), name='api-upload'),
    path('chat/', ChatAPIView.as_view(), name='api-chat'),
    path('search/', SearchAPIView.as_view(), name='api-search'),
    path('summary/', SummaryAPIView.as_view(), name='api-summary'),
    path('compare/', CompareAPIView.as_view(), name='api-compare'),
    path('feedback/', FeedbackAPIView.as_view(), name='api-feedback'),
    path('', include(router.urls)),
]
