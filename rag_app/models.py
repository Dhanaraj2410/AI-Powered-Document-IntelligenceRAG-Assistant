from django.db import models
from django.contrib.auth.models import User

class DocumentCollection(models.Model):
    """Collection grouping multiple PDF documents together for multi-doc RAG."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class Document(models.Model):
    """PDF Document record with processing status and metadata."""
    STATUS_CHOICES = (
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    collection = models.ForeignKey(
        DocumentCollection, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents'
    )
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='pdfs/%Y/%m/')
    file_size = models.BigIntegerField(default=0)  # in bytes
    page_count = models.IntegerField(default=0)
    chunk_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    processing_error = models.TextField(blank=True, default='')
    suggested_questions = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} [{self.status}]"


class DocumentChunk(models.Model):
    """Text chunk extracted from a document with source location and vector reference."""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField()
    page_number = models.IntegerField()
    section = models.CharField(max_length=500, blank=True, default='')
    content = models.TextField()
    vector_id = models.IntegerField(db_index=True)
    index_version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['document', 'chunk_index']

    def __str__(self):
        return f"Doc {self.document_id} Chunk #{self.chunk_index} (P.{self.page_number})"


class Conversation(models.Model):
    """Multi-turn RAG chat conversation thread scoped to user and document/collection."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    document = models.ForeignKey(
        Document, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations'
    )
    collection = models.ForeignKey(
        DocumentCollection, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations'
    )
    title = models.CharField(max_length=255, default='New Conversation')
    summary = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Chat '{self.title}' ({self.user.username})"


class Message(models.Model):
    """Individual user or assistant message in a RAG conversation thread."""
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
    )

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=15, choices=ROLE_CHOICES)
    content = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    latency_metrics = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.role.upper()}] {self.content[:40]}..."


class Bookmark(models.Model):
    """Saved Q&A answers bookmarked by user for reference."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    conversation = models.ForeignKey(Conversation, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='bookmarks', null=True, blank=True)
    question = models.TextField()
    answer = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    note = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Bookmark '{self.question[:30]}' ({self.user.username})"


class Feedback(models.Model):
    """User rating (+1 / -1) and feedback comments on assistant answers."""
    RATING_CHOICES = (
        (1, 'Positive / Helpful'),
        (-1, 'Negative / Unhelpful'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='feedbacks')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback {self.rating} on Message {self.message_id}"


class EvaluationResult(models.Model):
    """Audit log storing benchmark evaluation metrics for RAG retrieval and answer generation."""
    evaluation_date = models.DateTimeField(auto_now_add=True)
    precision_at_k = models.FloatField()
    mrr_score = models.FloatField()
    faithfulness_score = models.FloatField()
    relevance_score = models.FloatField()
    avg_latency_sec = models.FloatField()
    total_test_cases = models.IntegerField()
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Eval {self.created_at.strftime('%Y-%m-%d %H:%M')} - P@K: {self.precision_at_k:.2f}"
