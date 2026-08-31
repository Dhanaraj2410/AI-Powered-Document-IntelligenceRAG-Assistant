from django.contrib import admin
from .models import DocumentCollection, Document, DocumentChunk, Conversation, Message, EvaluationResult

@admin.register(DocumentCollection)
class DocumentCollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'user__username')
    list_filter = ('created_at',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'collection', 'status', 'page_count', 'chunk_count', 'file_size', 'created_at')
    search_fields = ('title', 'user__username', 'processing_error')
    list_filter = ('status', 'created_at', 'collection')

@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ('document', 'chunk_index', 'page_number', 'vector_id', 'index_version', 'created_at')
    search_fields = ('content', 'document__title')
    list_filter = ('page_number', 'index_version')

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'document', 'collection', 'created_at', 'updated_at')
    search_fields = ('title', 'user__username')
    list_filter = ('created_at',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'role', 'short_content', 'created_at')
    search_fields = ('content', 'conversation__title')
    list_filter = ('role', 'created_at')

    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Content Preview'

@admin.register(EvaluationResult)
class EvaluationResultAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'precision_at_k', 'mrr_score', 'faithfulness_score', 'relevance_score', 'avg_latency_sec', 'total_test_cases')
    list_filter = ('created_at',)
