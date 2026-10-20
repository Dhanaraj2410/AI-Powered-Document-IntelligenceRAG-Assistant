// Enterprise RAG Assistant Dynamic JavaScript System
document.addEventListener('DOMContentLoaded', () => {

    // --- Helper to get CSRF Token ---
    function getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // --- Drag & Drop Document Upload Handling ---
    const dropzone = document.getElementById('uploadDropzone');
    const fileInput = document.getElementById('pdfFileInput');
    const uploadProgress = document.getElementById('uploadProgress');
    const uploadStatusText = document.getElementById('uploadStatusText');

    if (dropzone && fileInput) {
        dropzone.addEventListener('click', () => fileInput.click());

        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropzone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropzone.classList.remove('dragover');
            });
        });

        dropzone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                handleFileUpload(files[0]);
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                handleFileUpload(fileInput.files[0]);
            }
        });
    }

    function handleFileUpload(file) {
        if (!/\.(pdf|docx|pptx|xlsx|csv|txt|md)$/i.test(file.name)) {
            alert('Choose a PDF, DOCX, PPTX, XLSX, CSV, TXT, or Markdown file.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        const collectionSelect = document.getElementById('collectionSelect');
        if (collectionSelect && collectionSelect.value) {
            formData.append('collection_id', collectionSelect.value);
        }

        if (uploadProgress) uploadProgress.classList.remove('d-none');
        if (uploadStatusText) uploadStatusText.textContent = `Uploading and queueing "${file.name}"...`;

        fetch('/api/upload/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                if (uploadStatusText) uploadStatusText.textContent = `✓ Upload & Analysis Completed for "${file.name}"!`;
                const documentId = data.document && data.document.id;
                const pollStatus = () => fetch(`/api/documents/${documentId}/`)
                    .then(response => response.json())
                    .then(doc => {
                        if (doc.status === 'completed') {
                            if (uploadStatusText) uploadStatusText.textContent = `Indexed "${file.name}".`;
                            setTimeout(() => window.location.reload(), 800);
                        } else if (doc.status === 'failed') {
                            if (uploadStatusText) uploadStatusText.textContent = doc.processing_error || 'Ingestion failed.';
                        } else {
                            if (uploadStatusText) uploadStatusText.textContent = `Processing "${file.name}"...`;
                            setTimeout(pollStatus, 1500);
                        }
                    }).catch(() => setTimeout(pollStatus, 3000));
                if (documentId) pollStatus();
            } else {
                alert(`Upload Failed: ${data.message || data.error}`);
                if (uploadProgress) uploadProgress.classList.add('d-none');
            }
        })
        .catch(err => {
            console.error('Upload Error:', err);
            alert('An error occurred during file upload.');
            if (uploadProgress) uploadProgress.classList.add('d-none');
        });
    }

    const createCollectionForm = document.getElementById('createCollectionForm');
    if (createCollectionForm) {
        createCollectionForm.addEventListener('submit', (event) => {
            event.preventDefault();
            const submitButton = createCollectionForm.querySelector('button[type="submit"]');
            const formData = new FormData(createCollectionForm);
            const payload = {
                name: String(formData.get('name') || '').trim(),
                description: String(formData.get('description') || '').trim()
            };
            if (!payload.name) return;

            if (submitButton) {
                submitButton.disabled = true;
                submitButton.setAttribute('aria-busy', 'true');
            }
            fetch(createCollectionForm.action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify(payload)
            })
                .then(async response => {
                    const data = await response.json().catch(() => ({}));
                    if (!response.ok) {
                        const detail = data.detail || data.name || data.error || 'Unable to create collection.';
                        throw new Error(Array.isArray(detail) ? detail.join(', ') : String(detail));
                    }
                    return data;
                })
                .then(() => window.location.reload())
                .catch(error => {
                    if (submitButton) {
                        submitButton.disabled = false;
                        submitButton.removeAttribute('aria-busy');
                    }
                    alert(error.message);
                });
        });
    }

    // --- Dynamic Suggested Questions Fetcher ---
    const chatDocSelect = document.getElementById('chatDocSelect');
    const initialDocId = document.getElementById('chatSelectedDocId')?.value || '';
    const initialCollectionId = document.getElementById('chatSelectedCollectionId')?.value || '';
    const chatCollectionSelect = document.getElementById('chatCollSelect');
    const suggestedQuestionsList = document.getElementById('suggestedQuestionsList');
    const analysisSpinner = document.getElementById('analysisSpinner');

    function bindPresetButtons() {
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.onclick = () => {
                const chatInput = document.getElementById('chatInput');
                if (chatInput) {
                    const text = btn.innerText || btn.textContent;
                    // Strip icon if present
                    const cleanText = text.replace(/^[💰📈⚠️📋]\s*/, '').trim();
                    chatInput.value = cleanText;
                    document.getElementById('chatForm').dispatchEvent(new Event('submit'));
                }
            };
        });
    }

    bindPresetButtons();

    function fetchSuggestedQuestions(docId) {
        if (!suggestedQuestionsList || !docId) return;

        if (analysisSpinner) analysisSpinner.classList.remove('d-none');

        fetch(`/api/documents/${docId}/analyze/`, {
            headers: { 'X-CSRFToken': getCsrfToken() }
        })
        .then(res => res.json())
        .then(data => {
            if (analysisSpinner) analysisSpinner.classList.add('d-none');
            if (data.success && data.suggested_questions && data.suggested_questions.length > 0) {
                suggestedQuestionsList.innerHTML = '';
                data.suggested_questions.forEach(q => {
                    const btn = document.createElement('button');
                    btn.className = 'preset-btn text-start';
                    btn.textContent = q;
                    suggestedQuestionsList.appendChild(btn);
                });
                bindPresetButtons();
            }
        })
        .catch(err => {
            if (analysisSpinner) analysisSpinner.classList.add('d-none');
        });
    }

    if (chatDocSelect) {
        if (initialDocId) chatDocSelect.value = initialDocId;
        if (chatCollectionSelect && initialCollectionId) chatCollectionSelect.value = initialCollectionId;
        if (chatDocSelect.value) {
            fetchSuggestedQuestions(chatDocSelect.value);
        }

        chatDocSelect.addEventListener('change', () => {
            if (chatDocSelect.value) {
                fetchSuggestedQuestions(chatDocSelect.value);
            }
        });
    }

    document.getElementById('clearChatScope')?.addEventListener('click', () => {
        if (chatDocSelect) chatDocSelect.value = '';
        const collectionSelect = chatCollectionSelect;
        if (collectionSelect) collectionSelect.value = '';
        if (suggestedQuestionsList) {
            suggestedQuestionsList.innerHTML = '<div class="text-muted small py-2">Choose a document to see tailored questions.</div>';
        }
    });

    // --- RAG Chat Query & Step-by-Step Thinking Handler ---
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');
    const chatCharCount = document.getElementById('chatCharCount');
    const chatSubmitButton = document.getElementById('chatSubmitButton');
    let chatRequestPending = false;

    function setConversationExportState(enabled) {
        document.querySelectorAll('.export-conversation-btn').forEach(button => {
            button.disabled = !enabled;
        });
    }

    document.querySelectorAll('.export-conversation-btn').forEach(button => {
        button.addEventListener('click', async () => {
            const conversationId = document.getElementById('currentConvId')?.value || '';
            const format = button.getAttribute('data-format') || 'pdf';
            if (!conversationId) return;

            button.disabled = true;
            try {
                const response = await fetch('/api/export/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({ conversation_id: Number(conversationId), format })
                });
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.error || 'Conversation export failed.');
                }
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `conversation.${format}`;
                document.body.appendChild(link);
                link.click();
                link.remove();
                URL.revokeObjectURL(url);
            } catch (error) {
                alert(error.message);
            } finally {
                setConversationExportState(Boolean(document.getElementById('currentConvId')?.value));
            }
        });
    });

    if (chatInput) {
        const updateComposer = () => {
            if (chatCharCount) chatCharCount.textContent = `${chatInput.value.length} / ${chatInput.maxLength}`;
            chatInput.style.height = 'auto';
            chatInput.style.height = `${Math.min(chatInput.scrollHeight, 160)}px`;
        };

        chatInput.addEventListener('input', updateComposer);
        chatInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
                event.preventDefault();
                chatForm?.requestSubmit();
            }
        });
        updateComposer();
    }

    if (chatForm && chatInput && chatMessages) {
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const question = chatInput.value.trim();
            if (!question || chatRequestPending) return;

            chatRequestPending = true;
            if (chatSubmitButton) {
                chatSubmitButton.disabled = true;
                chatSubmitButton.setAttribute('aria-busy', 'true');
                chatSubmitButton.querySelector('span').textContent = 'Thinking';
            }
            chatInput.disabled = true;

            appendUserMessage(question);
            chatInput.value = '';
            chatInput.style.height = 'auto';
            if (chatCharCount) chatCharCount.textContent = `0 / ${chatInput.maxLength}`;

            const loadingBubbleId = appendStepLoadingMessage();
            chatMessages.scrollTop = chatMessages.scrollHeight;

            const selectedDoc = document.getElementById('chatDocSelect')?.value || null;
            const selectedCollection = document.getElementById('chatCollSelect')?.value || null;
            const currentConvId = document.getElementById('currentConvId')?.value || null;

            fetch('/api/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    question: question,
                    conversation_id: currentConvId ? parseInt(currentConvId) : null,
                    document_id: selectedDoc ? parseInt(selectedDoc) : null,
                    collection_id: selectedCollection ? parseInt(selectedCollection) : null
                })
            })
            .then(async res => {
                const data = await res.json().catch(() => ({}));
                if (!res.ok) throw new Error(data.message || data.error || `Request failed (${res.status})`);
                return data;
            })
            .then(data => {
                removeLoadingMessage(loadingBubbleId);
                chatRequestPending = false;
                chatInput.disabled = false;
                if (chatSubmitButton) {
                    chatSubmitButton.disabled = false;
                    chatSubmitButton.removeAttribute('aria-busy');
                    chatSubmitButton.querySelector('span').textContent = 'Ask';
                }
                if (data.answer) {
                    streamAssistantMessage(data, question);
                    if (data.conversation_id && (!currentConvId || currentConvId != data.conversation_id)) {
                        const convIdInput = document.getElementById('currentConvId');
                        if (convIdInput) convIdInput.value = data.conversation_id;
                        setConversationExportState(true);
                    }
                } else {
                    appendFriendlyError(question, data.error || data.message);
                }
                chatInput.focus();
            })
            .catch(err => {
                removeLoadingMessage(loadingBubbleId);
                chatRequestPending = false;
                chatInput.disabled = false;
                if (chatSubmitButton) {
                    chatSubmitButton.disabled = false;
                    chatSubmitButton.removeAttribute('aria-busy');
                    chatSubmitButton.querySelector('span').textContent = 'Ask';
                }
                appendFriendlyError(question, err.message);
                chatInput.focus();
            });
        });
    }

    function appendUserMessage(text) {
        const div = document.createElement('div');
        div.className = 'chat-bubble chat-bubble-user';
        div.setAttribute('aria-label', 'Your message');
        div.textContent = text;
        chatMessages.appendChild(div);
    }

    function appendStepLoadingMessage() {
        const id = 'loading_' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = 'chat-bubble chat-bubble-assistant';
        div.setAttribute('role', 'status');
        div.setAttribute('aria-live', 'polite');
        div.innerHTML = `
            <div class="small fw-semibold text-info mb-2"><i class="bi bi-cpu spinner-border spinner-border-sm me-2"></i> AI is thinking...</div>
            <div class="small text-light mb-1"><span class="text-success me-1">✓</span> Searching vector documents</div>
            <div class="small text-light mb-1"><span class="text-success me-1">✓</span> Finding relevant passages (FAISS + BM25)</div>
            <div class="small text-info"><span class="spinner-grow spinner-grow-sm me-1"></span> Generating grounded answer...</div>
        `;
        chatMessages.appendChild(div);
        return id;
    }

    function removeLoadingMessage(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function appendFriendlyError(question, detail = '') {
        const div = document.createElement('div');
        div.className = 'chat-bubble chat-bubble-assistant w-100 border-danger';
        div.innerHTML = `
            <div class="text-danger fw-bold mb-2"><i class="bi bi-exclamation-triangle-fill me-1"></i> ⚠️ Something went wrong</div>
            <div class="text-light small mb-3">${escapeHtml(detail || "We couldn't process your request. Check your connection and try again.")}</div>
            <button class="btn btn-sm btn-outline-danger rounded-pill px-3 try-again-btn" data-q="${escapeHtml(question)}">
                <i class="bi bi-arrow-clockwise me-1"></i> Try Again
            </button>
        `;
        chatMessages.appendChild(div);

        div.querySelector('.try-again-btn').onclick = () => {
            div.remove();
            if (chatInput) {
                chatInput.value = question;
                chatForm.dispatchEvent(new Event('submit'));
            }
        };
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function formatMarkdown(text) {
        if (!text) return '';
        let formatted = escapeHtml(text);
        formatted = formatted.replace(/^### (.*$)/gim, '<h5 class="fw-bold text-info mt-3 mb-2">$1</h5>');
        formatted = formatted.replace(/^## (.*$)/gim, '<h4 class="fw-bold gradient-text mt-4 mb-2">$1</h4>');
        formatted = formatted.replace(/^# (.*$)/gim, '<h3 class="fw-bold text-light mt-4 mb-3">$1</h3>');
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong class="text-light">$1</strong>');
        formatted = formatted.replace(/^- (.*$)/gim, '• $1');
        formatted = formatted.replace(/\n/g, '<br>');
        return formatted;
    }

    function streamAssistantMessage(data, question) {
        const div = document.createElement('div');
        div.className = 'chat-bubble chat-bubble-assistant w-100';

        const textHolder = document.createElement('div');
        textHolder.className = 'mb-2';
        div.appendChild(textHolder);

        chatMessages.appendChild(div);

        const words = (data.answer || '').split(' ');
        let currentIdx = 0;

        const interval = setInterval(() => {
            if (currentIdx < words.length) {
                const textChunk = words.slice(0, currentIdx + 1).join(' ');
                textHolder.innerHTML = formatMarkdown(textChunk);
                chatMessages.scrollTop = chatMessages.scrollHeight;
                currentIdx++;
            } else {
                clearInterval(interval);
                renderMessageFooter(div, data, question);
            }
        }, 25);
    }

    function renderMessageFooter(containerDiv, data, question) {
        let footerHtml = '';
        const msgId = data.message_id || 'msg_' + Date.now();

        if (data.sources && data.sources.length > 0) {
            footerHtml += `
                <hr class="my-2 border-secondary">
                <div class="d-flex justify-content-between align-items-center mb-2 flex-wrap gap-2">
                    <div class="fw-semibold text-info small">
                        <i class="bi bi-journal-check me-1"></i> Grounded Citations (${data.sources.length} Sources):
                    </div>
                    <button class="btn btn-sm btn-outline-info rounded-pill px-3 py-1 inspect-source-btn"
                        data-doc-title="${escapeHtml(data.sources[0].document_title)}"
                        data-doc-id="${data.sources[0].document_id || ''}"
                        data-page="${data.sources[0].page_number}"
                        data-score="${data.sources[0].retrieval_score}"
                        data-reason="${escapeHtml(data.sources[0].reason || 'Matches vector query terms and semantic context.')}"
                        data-content="${escapeHtml(data.sources[0].chunk_preview)}">
                        <i class="bi bi-eye me-1"></i> View Source
                    </button>
                </div>
            `;

            data.sources.forEach((src, sIdx) => {
                footerHtml += `
                    <button type="button" class="citation-box mb-2 w-100 text-start cursor-pointer inspect-source-btn"
                        data-doc-title="${escapeHtml(src.document_title)}"
                        data-doc-id="${src.document_id || ''}"
                        data-page="${src.page_number}"
                        data-score="${src.retrieval_score}"
                        data-reason="${escapeHtml(src.reason || 'Contains semantic keywords matching your question.')}"
                        data-content="${escapeHtml(src.chunk_preview)}">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <span class="fw-semibold text-light small"><i class="bi bi-file-earmark-text text-danger me-1"></i> ${escapeHtml(src.document_title)} — Page ${src.page_number}</span>
                            <span class="badge badge-score">Relevance: ${src.retrieval_score}</span>
                        </div>
                        <div class="text-light small" style="font-style: italic;">"${escapeHtml(src.chunk_preview)}"</div>
                    </button>
                `;
            });
        }

        footerHtml += `
            <div class="mt-3 pt-2 border-top border-secondary d-flex justify-content-between align-items-center flex-wrap gap-2">
                <div class="d-flex align-items-center gap-1">
                    <button class="btn btn-sm btn-outline-success feedback-btn" data-msg-id="${msgId}" data-rating="1" title="Helpful answer">
                        <i class="bi bi-hand-thumbs-up"></i> Helpful
                    </button>
                    <button class="btn btn-sm btn-outline-danger feedback-btn" data-msg-id="${msgId}" data-rating="-1" title="Unhelpful answer">
                        <i class="bi bi-hand-thumbs-down"></i> Not Helpful
                    </button>
                    <button class="btn btn-sm btn-outline-warning bookmark-btn ms-2" data-msg-id="${msgId}" data-question="${escapeHtml(question)}" data-answer="${escapeHtml(data.answer)}" title="Bookmark answer">
                        <i class="bi bi-star"></i> Save
                    </button>
                    <button class="btn btn-sm btn-outline-info copy-answer-btn ms-1" data-answer="${escapeHtml(data.answer)}" title="Copy to clipboard">
                        <i class="bi bi-clipboard"></i> Copy
                    </button>
                </div>
                ${data.latency_metrics && data.latency_metrics.total_ms ? `
                <div>
                    <span class="latency-pill"><i class="bi bi-clock-history me-1"></i> ${data.latency_metrics.total_ms}ms</span>
                </div>` : ''}
            </div>
        `;

        const footerWrapper = document.createElement('div');
        footerWrapper.innerHTML = footerHtml;
        containerDiv.appendChild(footerWrapper);

        bindMessageControls(containerDiv, data, question);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function bindMessageControls(container, data, question) {
        // Source Inspector Handler
        container.querySelectorAll('.inspect-source-btn').forEach(btn => {
            btn.onclick = () => {
                const docTitle = btn.getAttribute('data-doc-title') || 'Document';
                const docId = btn.getAttribute('data-doc-id') || '';
                const page = btn.getAttribute('data-page') || '1';
                const scoreRaw = parseFloat(btn.getAttribute('data-score') || '0.90');
                const scorePct = Math.min(Math.round(scoreRaw <= 1.0 ? scoreRaw * 100 : scoreRaw), 100);
                const reason = btn.getAttribute('data-reason') || 'High vector similarity & semantic match.';
                const content = btn.getAttribute('data-content') || '';

                const inspectorOutput = document.getElementById('sourceInspectorContent');
                if (inspectorOutput) {
                    inspectorOutput.innerHTML = `
                        <div class="glass-card p-3 mb-3 border-info" style="background: rgba(15, 23, 42, 0.95);">
                            <div class="fw-bold text-light mb-1"><i class="bi bi-file-pdf text-danger me-1"></i> ${escapeHtml(docTitle)}</div>
                            <div class="text-info small mb-3">Page ${page}</div>

                            <div class="mb-3">
                                <div class="d-flex justify-content-between align-items-center small text-muted mb-1">
                                    <span>Retrieval Similarity</span>
                                    <span class="fw-bold text-info">${scorePct}%</span>
                                </div>
                                <div class="progress" style="height: 8px; background: rgba(255, 255, 255, 0.1);">
                                    <div class="progress-bar bg-info" style="width: ${scorePct}%;"></div>
                                </div>
                            </div>

                            <div class="small text-light mb-2">
                                <strong class="text-info">Why retrieved:</strong> ${escapeHtml(reason)}
                            </div>

                            <div class="p-2 bg-dark rounded border border-secondary text-light small mb-3 font-monospace" style="white-space: pre-wrap; font-size: 0.82rem;">
                                "${escapeHtml(content)}"
                            </div>

                            ${docId ? `
                            <a href="/document/${docId}/" class="btn btn-outline-info btn-sm rounded-pill w-100 fw-bold">
                                <i class="bi bi-box-arrow-up-right me-1"></i> Open Full Document
                            </a>` : ''}
                        </div>
                    `;
                }
            };
        });

        // Feedback Buttons
        container.querySelectorAll('.feedback-btn').forEach(btn => {
            btn.onclick = () => {
                const msgId = btn.getAttribute('data-msg-id');
                const rating = parseInt(btn.getAttribute('data-rating'));
                if (!msgId) return;

                fetch('/api/feedback/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({ message_id: parseInt(msgId), rating: rating })
                })
                .then(res => res.json())
                .then(resData => {
                    if (resData.success) {
                        btn.classList.replace('btn-outline-success', 'btn-success');
                        btn.classList.replace('btn-outline-danger', 'btn-danger');
                    }
                });
            };
        });

        // Bookmark Button
        container.querySelectorAll('.bookmark-btn').forEach(btn => {
            btn.onclick = () => {
                const msgId = btn.getAttribute('data-msg-id');
                const qText = btn.getAttribute('data-question') || question;
                const aText = btn.getAttribute('data-answer') || data.answer;

                fetch('/api/bookmarks/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({
                        message: msgId && !msgId.startsWith('msg_') ? parseInt(msgId) : null,
                        question: qText,
                        answer: aText,
                        sources: data.sources || []
                    })
                })
                .then(res => res.json())
                .then(bData => {
                    if (bData.id) {
                        btn.innerHTML = `<i class="bi bi-star-fill"></i> Saved!`;
                        btn.className = 'btn btn-sm btn-warning text-dark fw-bold ms-2';
                    }
                });
            };
        });

        // Copy Button
        container.querySelectorAll('.copy-answer-btn').forEach(btn => {
            btn.onclick = () => {
                const text = btn.getAttribute('data-answer') || data.answer;
                navigator.clipboard.writeText(text).then(() => {
                    const orig = btn.innerHTML;
                    btn.innerHTML = `<i class="bi bi-check2"></i> Copied!`;
                    setTimeout(() => btn.innerHTML = orig, 2000);
                });
            };
        });
    }

    // --- Standalone Hybrid Search Inspector Handler ---
    const searchInspectorForm = document.getElementById('searchInspectorForm');
    const searchResultsOutput = document.getElementById('searchResultsOutput');

    if (searchInspectorForm && searchResultsOutput) {
        searchInspectorForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const query = document.getElementById('inspectorQuery')?.value.trim();
            const docId = document.getElementById('inspectorDoc')?.value || null;
            const collId = document.getElementById('inspectorColl')?.value || null;

            if (!query) return;

            searchResultsOutput.innerHTML = `<div class="text-center py-5"><span class="spinner-border text-info me-2"></span> Executing Hybrid FAISS Vector & BM25 Keyword Search...</div>`;

            fetch('/api/search/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    query: query,
                    document_id: docId ? parseInt(docId) : null,
                    collection_id: collId ? parseInt(collId) : null
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success && data.results && data.results.length > 0) {
                    let html = `<div class="mb-3 text-muted small"><i class="bi bi-clock-history me-1"></i> Found ${data.result_count} candidate vector chunks in ${data.latency_ms}ms:</div>`;
                    data.results.forEach(resItem => {
                        html += `
                            <div class="glass-card p-3 mb-3 border-secondary">
                                <div class="d-flex justify-content-between align-items-center mb-2">
                                    <span class="fw-bold text-light small"><i class="bi bi-file-earmark-pdf text-danger me-1"></i> Rank #${resItem.rank}: ${escapeHtml(resItem.document_title)} (Page ${resItem.page_number})</span>
                                    <span class="badge badge-score">Retrieval Score: ${resItem.retrieval_score}</span>
                                </div>
                                <div class="p-2 bg-dark rounded border border-secondary text-light small" style="white-space: pre-wrap; font-family: monospace;">
                                    ${escapeHtml(resItem.content)}
                                </div>
                            </div>
                        `;
                    });
                    searchResultsOutput.innerHTML = html;
                } else {
                    searchResultsOutput.innerHTML = `<div class="text-center py-4 text-muted small">No matching vector chunks found for query.</div>`;
                }
            })
            .catch(err => {
                searchResultsOutput.innerHTML = `<div class="alert alert-danger">Error communicating with hybrid search service.</div>`;
            });
        });
    }

    // --- Multi-Document Comparison Handler ---
    const compareForm = document.getElementById('compareForm');
    const compareSubmitBtn = document.getElementById('compareSubmitBtn');
    const comparisonResult = document.getElementById('comparisonResult');

    if (compareForm && compareSubmitBtn && comparisonResult) {
        compareForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const docA = document.getElementById('docASelect')?.value;
            const docB = document.getElementById('docBSelect')?.value;

            if (!docA || !docB) {
                alert('Please select both Document A and Document B for comparison.');
                return;
            }

            comparisonResult.innerHTML = `<div class="text-center py-5"><span class="spinner-border text-info me-2"></span> Synthesizing side-by-side comparison report using AI Gemini...</div>`;

            fetch('/api/compare/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({ doc_a_id: parseInt(docA), doc_b_id: parseInt(docB) })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    comparisonResult.innerHTML = `
                        <div class="mb-3 d-flex gap-3 flex-wrap">
                            <span class="badge bg-danger text-light px-3 py-2 fw-bold"><i class="bi bi-file-pdf me-1"></i> Document A: ${escapeHtml(data.doc_a.title)} (${data.doc_a.pages} Pages)</span>
                            <span class="badge bg-info text-dark px-3 py-2 fw-bold"><i class="bi bi-file-pdf me-1"></i> Document B: ${escapeHtml(data.doc_b.title)} (${data.doc_b.pages} Pages)</span>
                        </div>
                        <div class="comparison-report-box">
                            ${formatMarkdown(data.comparison_report)}
                        </div>
                    `;
                } else {
                    comparisonResult.innerHTML = `<div class="alert alert-danger">Comparison Failed: ${escapeHtml(data.error)}</div>`;
                }
            })
            .catch(err => {
                comparisonResult.innerHTML = `<div class="alert alert-danger">Error communicating with document comparison service.</div>`;
            });
        });
    }

    // --- Bookmarks Deletion Control ---
    document.querySelectorAll('.delete-bookmark-btn').forEach(btn => {
        btn.onclick = () => {
            const bmId = btn.getAttribute('data-bm-id');
            if (!bmId) return;

            fetch(`/api/bookmarks/${bmId}/`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCsrfToken() }
            })
            .then(res => {
                const card = document.getElementById(`bookmark_card_${bmId}`);
                if (card) card.remove();
            });
        };
    });

    document.querySelectorAll('.delete-doc-btn').forEach(btn => {
        btn.onclick = () => {
            const docId = btn.getAttribute('data-doc-id');
            if (!docId || !confirm('Are you sure you want to delete this document?')) return;

            fetch(`/api/documents/${docId}/`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCsrfToken() }
            })
            .then(res => {
                window.location.reload();
            });
        };
    });

    document.querySelectorAll('.reprocess-doc-btn').forEach(btn => {
        btn.onclick = () => {
            const docId = btn.getAttribute('data-doc-id');
            if (!docId || btn.disabled) return;
            btn.disabled = true;
            btn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i> Processing...';

            fetch(`/api/documents/${docId}/reprocess/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrfToken() }
            })
                .then(async response => {
                    const data = await response.json().catch(() => ({}));
                    if (!response.ok) throw new Error(data.detail || data.error || 'Unable to reprocess document.');
                    return data;
                })
                .then(() => window.location.reload())
                .catch(error => {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="bi bi-arrow-repeat me-1"></i> Retry';
                    alert(error.message);
                });
        };
    });

    function escapeHtml(text) {
        if (!text) return '';
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

});
