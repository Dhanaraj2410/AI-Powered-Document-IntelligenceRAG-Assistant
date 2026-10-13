from rest_framework import serializers
from rag_app.models import DocumentCollection, Document, DocumentChunk, Conversation, Message, Bookmark, Feedback, EvaluationResult

class DocumentCollectionSerializer(serializers.ModelSerializer):
    document_count = serializers.IntegerField(source='documents.count', read_only=True)

    class Meta:
        model = DocumentCollection
        fields = ['id', 'name', 'description', 'document_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = ['id', 'chunk_index', 'page_number', 'content', 'vector_id']


class DocumentSerializer(serializers.ModelSerializer):
    collection_name = serializers.CharField(source='collection.name', read_only=True, default='')
    collection = serializers.PrimaryKeyRelatedField(
        queryset=DocumentCollection.objects.none(), required=False, allow_null=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            self.fields['collection'].queryset = DocumentCollection.objects.filter(user=request.user)

    class Meta:
        model = Document
        fields = [
            'id', 'collection', 'collection_name', 'title', 'file', 'file_size',
            'page_count', 'chunk_count', 'status', 'processing_error', 'suggested_questions',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'file_size', 'page_count', 'chunk_count', 'status', 'processing_error', 'created_at', 'updated_at']


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'role', 'content', 'sources', 'latency_metrics', 'created_at']
        read_only_fields = ['id', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.IntegerField(source='messages.count', read_only=True)
    document = serializers.PrimaryKeyRelatedField(
        queryset=Document.objects.none(), required=False, allow_null=True
    )
    collection = serializers.PrimaryKeyRelatedField(
        queryset=DocumentCollection.objects.none(), required=False, allow_null=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            self.fields['document'].queryset = Document.objects.filter(user=request.user)
            self.fields['collection'].queryset = DocumentCollection.objects.filter(user=request.user)

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'document', 'collection', 'message_count', 'messages', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class BookmarkSerializer(serializers.ModelSerializer):
    message = serializers.PrimaryKeyRelatedField(queryset=Message.objects.none(), required=False, allow_null=True)
    conversation = serializers.PrimaryKeyRelatedField(queryset=Conversation.objects.none(), required=False, allow_null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            self.fields['message'].queryset = Message.objects.filter(conversation__user=request.user)
            self.fields['conversation'].queryset = Conversation.objects.filter(user=request.user)

    class Meta:
        model = Bookmark
        fields = ['id', 'conversation', 'message', 'question', 'answer', 'sources', 'note', 'created_at']
        read_only_fields = ['id', 'created_at']


class FeedbackSerializer(serializers.ModelSerializer):
    message = serializers.PrimaryKeyRelatedField(queryset=Message.objects.all(), required=True)

    class Meta:
        model = Feedback
        fields = ['id', 'message', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    collection_id = serializers.IntegerField(required=False, allow_null=True)
    title = serializers.CharField(required=False, allow_blank=True, max_length=255)


class ChatQuerySerializer(serializers.Serializer):
    question = serializers.CharField(required=True, max_length=2000)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)
    document_id = serializers.IntegerField(required=False, allow_null=True)
    collection_id = serializers.IntegerField(required=False, allow_null=True)


class SummaryRequestSerializer(serializers.Serializer):
    document_id = serializers.IntegerField(required=True)
    mode = serializers.ChoiceField(choices=['executive', 'key_points', 'technical', 'risks'], default='executive')


class EvaluationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationResult
        fields = '__all__'
