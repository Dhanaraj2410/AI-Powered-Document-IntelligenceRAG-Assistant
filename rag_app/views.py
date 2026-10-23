from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme
from rag_app.models import DocumentCollection, Document, Conversation, Message, Bookmark, Feedback, EvaluationResult

def index_view(request):
    """Hero landing page."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'index.html')


def register_view(request):
    """User Registration view."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to AI Document Intelligence, {user.username}!")
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form})


def login_view(request):
    """User Login view."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next', '')
            if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                next_url = 'dashboard'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


@require_POST
def logout_view(request):
    """User Logout view."""
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('login')


@login_required
def dashboard_view(request):
    """User Document & Collections Management Dashboard."""
    documents = Document.objects.filter(user=request.user)
    collections = DocumentCollection.objects.filter(user=request.user)
    conversations = Conversation.objects.filter(user=request.user)

    total_chunks = sum(d.chunk_count for d in documents)

    context = {
        'documents': documents,
        'collections': collections,
        'conversations': conversations,
        'stats': {
            'doc_count': documents.count(),
            'completed_count': documents.filter(status='completed').count(),
            'failed_count': documents.filter(status='failed').count(),
            'collection_count': collections.count(),
            'total_chunks': total_chunks
        }
    }
    return render(request, 'dashboard.html', context)


@login_required
def documents_list_view(request):
    """Dedicated Document Management Page with Filter and Processing Controls."""
    documents = Document.objects.filter(user=request.user)
    collections = DocumentCollection.objects.filter(user=request.user)

    status_filter = request.GET.get('status')
    if status_filter:
        documents = documents.filter(status=status_filter)

    collection_filter = request.GET.get('collection')
    if collection_filter:
        documents = documents.filter(collection_id=collection_filter)

    context = {
        'documents': documents,
        'collections': collections
    }
    return render(request, 'documents.html', context)


@login_required
def collections_list_view(request):
    """Multi-Document Knowledge Base Collections Page."""
    collections = DocumentCollection.objects.filter(user=request.user)
    documents = Document.objects.filter(user=request.user)

    context = {
        'collections': collections,
        'documents': documents
    }
    return render(request, 'collections.html', context)


@login_required
def document_detail_view(request, doc_id):
    """Document detail page with Chunk preview and Summarizer."""
    doc = get_object_or_404(Document, id=doc_id, user=request.user)
    chunks = doc.chunks.all().order_by('chunk_index')[:50]

    context = {
        'document': doc,
        'chunks': chunks
    }
    return render(request, 'document_detail.html', context)


@login_required
def chat_view(request):
    """Interactive Multi-turn RAG Chat interface with Citations and Latency metrics."""
    documents = Document.objects.filter(user=request.user, status='completed')
    collections = DocumentCollection.objects.filter(user=request.user)
    conversations = Conversation.objects.filter(user=request.user)

    active_conv_id = request.GET.get('conv_id')
    active_conv = None
    chat_messages = []

    if active_conv_id:
        active_conv = Conversation.objects.filter(id=active_conv_id, user=request.user).first()
        if active_conv:
            chat_messages = active_conv.messages.all()

    # Preserve scope when entering chat from Documents, Collections, or a
    # saved conversation. Invalid IDs are ignored so the page remains usable.
    selected_doc_id = request.GET.get('doc_id')
    selected_collection_id = request.GET.get('coll_id')
    if selected_doc_id and not documents.filter(id=selected_doc_id).exists():
        selected_doc_id = ''
    if selected_collection_id and not collections.filter(id=selected_collection_id).exists():
        selected_collection_id = ''
    if active_conv:
        selected_doc_id = selected_doc_id or str(active_conv.document_id or '')
        selected_collection_id = selected_collection_id or str(active_conv.collection_id or '')

    context = {
        'documents': documents,
        'collections': collections,
        'conversations': conversations,
        'active_conv': active_conv,
        'chat_messages': chat_messages,
        'selected_doc_id': selected_doc_id or '',
        'selected_collection_id': selected_collection_id or '',
    }
    return render(request, 'chat.html', context)


@login_required
def search_view(request):
    """Standalone Hybrid Vector + Keyword Search Inspector."""
    documents = Document.objects.filter(user=request.user, status='completed')
    collections = DocumentCollection.objects.filter(user=request.user)

    context = {
        'documents': documents,
        'collections': collections
    }
    return render(request, 'search.html', context)


@login_required
def compare_view(request):
    """Multi-document comparative analysis interface."""
    documents = Document.objects.filter(user=request.user, status='completed')

    context = {
        'documents': documents
    }
    return render(request, 'compare.html', context)


@login_required
def conversations_list_view(request):
    """Chat Thread History Management Page."""
    conversations = Conversation.objects.filter(user=request.user)

    context = {
        'conversations': conversations
    }
    return render(request, 'conversations.html', context)


@login_required
def bookmarks_view(request):
    """Saved Q&A answers and bookmarked responses page."""
    bookmarks = Bookmark.objects.filter(user=request.user)

    context = {
        'bookmarks': bookmarks
    }
    return render(request, 'bookmarks.html', context)


@login_required
def analytics_view(request):
    """System Analytics Dashboard tracking Queries, Feedback %, Latency & Usage."""
    user_convs = Conversation.objects.filter(user=request.user)
    total_messages = Message.objects.filter(conversation__user=request.user, role='user').count()

    feedbacks = Feedback.objects.filter(user=request.user)
    total_feedbacks = feedbacks.count()
    positive_feedbacks = feedbacks.filter(rating=1).count()
    positive_pct = round((positive_feedbacks / total_feedbacks) * 100) if total_feedbacks > 0 else None

    assistant_messages = Message.objects.filter(
        conversation__user=request.user, role='assistant'
    ).values_list('latency_metrics', flat=True)
    latencies_ms = [
        metrics.get('total_ms') for metrics in assistant_messages
        if isinstance(metrics, dict) and isinstance(metrics.get('total_ms'), (int, float))
    ]
    avg_latency = round(sum(latencies_ms) / len(latencies_ms) / 1000, 2) if latencies_ms else None

    documents = Document.objects.filter(user=request.user)

    context = {
        'stats': {
            'total_queries': total_messages,
            'total_documents': documents.count(),
            'total_conversations': user_convs.count(),
            'positive_feedback_pct': positive_pct,
            'avg_latency': avg_latency
        },
        'documents': documents[:5]
    }
    return render(request, 'analytics.html', context)


@login_required
def evaluation_view(request):
    """RAG Evaluation & Performance Metrics Dashboard."""
    latest_eval = EvaluationResult.objects.first()
    eval_history = EvaluationResult.objects.all()[:10]

    context = {
        'latest_eval': latest_eval,
        'eval_history': eval_history
    }
    return render(request, 'evaluation.html', context)


@login_required
def profile_view(request):
    """User Profile and Account Statistics page."""
    documents = Document.objects.filter(user=request.user)
    collections = DocumentCollection.objects.filter(user=request.user)
    conversations = Conversation.objects.filter(user=request.user)
    total_chunks = sum(d.chunk_count for d in documents)

    context = {
        'documents': documents,
        'collections': collections,
        'conversations': conversations,
        'doc_count': documents.count(),
        'collection_count': collections.count(),
        'conversation_count': conversations.count(),
        'total_chunks': total_chunks
    }
    return render(request, 'profile.html', context)
