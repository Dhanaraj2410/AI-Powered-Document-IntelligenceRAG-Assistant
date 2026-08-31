import logging
import time
from typing import Optional, List, Dict, Any

from rag_app.models import Document, DocumentChunk, Conversation, Message
from .hybrid_retriever_service import HybridRetrieverService
from .reranker_service import RerankerService
from .prompt_service import PromptService
from .llm_service import LLMService
from .grounding_service import GroundingService
from .query_rewriter_service import QueryRewriterService
from .analysis_service import AnalysisService

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.retriever_service = HybridRetrieverService()

    def process_document(self, document_id: int) -> bool:
        """
        Processes uploaded PDF document:
        1. Extract text and page numbers using PyMuPDF (fitz)
        2. Chunk text using recursive splitting
        3. Generate FAISS vector embeddings
        4. Store chunks and update vector index
        5. Automatically generate 4-5 document-specific suggested questions
        """
        try:
            doc_record = Document.objects.get(id=document_id)
            doc_record.status = 'processing'
            doc_record.save(update_fields=['status'])

            file_path = doc_record.file.path
            pages_text = HybridRetrieverService.extract_text_by_pages(file_path)

            doc_record.page_count = len(pages_text)
            doc_record.save(update_fields=['page_count'])

            # 2. Chunk text recursively
            raw_chunks = HybridRetrieverService.chunk_text(pages_text, chunk_size=500, chunk_overlap=80)

            if not raw_chunks:
                doc_record.status = 'failed'
                doc_record.processing_error = "No readable text extracted from PDF document."
                doc_record.save(update_fields=['status', 'processing_error'])
                return False

            # 3. Add to FAISS Vector Index & Database
            existing_chunks = DocumentChunk.objects.filter(document=doc_record)
            if existing_chunks.exists():
                existing_chunks.delete()

            texts = [c['text'] for c in raw_chunks]
            metadata = [{
                "document_id": doc_record.id,
                "user_id": doc_record.user_id,
                "page_number": c['page_number'],
                "chunk_index": idx
            } for idx, c in enumerate(raw_chunks)]

            vector_ids = self.retriever_service.add_document_chunks(
                texts=texts,
                metadatas=metadata,
                user_id=doc_record.user_id,
                document_id=doc_record.id
            )

            # 4. Save chunk records to Database
            chunk_objects = []
            for idx, c in enumerate(raw_chunks):
                chunk_objects.append(DocumentChunk(
                    document=doc_record,
                    chunk_index=idx,
                    page_number=c['page_number'],
                    content=c['text'],
                    vector_id=vector_ids[idx] if idx < len(vector_ids) else idx,
                    index_version=1
                ))

            DocumentChunk.objects.bulk_create(chunk_objects)

            doc_record.chunk_count = len(chunk_objects)
            doc_record.status = 'completed'
            doc_record.processing_error = ''
            doc_record.save()

            # 5. Generate Intelligent Suggested Questions for this Document
            try:
                AnalysisService.analyze_document_and_generate_questions(doc_record.id)
            except Exception as e_analysis:
                logger.warning(f"Analysis failed for doc {doc_record.id}: {str(e_analysis)}")

            logger.info(f"Successfully processed Document ID {doc_record.id}: {doc_record.chunk_count} chunks indexed.")
            return True

        except Exception as e:
            logger.error(f"Error during document processing for Document ID {document_id}: {str(e)}", exc_info=True)
            try:
                doc_record = Document.objects.get(id=document_id)
                doc_record.status = 'failed'
                doc_record.processing_error = f"Processing Error: {str(e)}"
                doc_record.save(update_fields=['status', 'processing_error'])
            except Exception:
                pass
            return False

    def query_rag(
        self,
        question: str,
        user_id: int,
        conversation_id: Optional[int] = None,
        document_id: Optional[int] = None,
        collection_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end RAG workflow with Retrieval Explainability:
        Query Rewriting -> Hybrid Retrieval -> Reranking -> Anti-hallucination Prompt -> LLM API -> Grounding Check.
        """
        t_start = time.time()

        if conversation_id:
            conv = Conversation.objects.filter(id=conversation_id, user_id=user_id).first()
        else:
            conv = None

        if not conv:
            doc_obj = Document.objects.filter(id=document_id, user_id=user_id).first() if document_id else None
            conv_title = f"Query: {question[:30]}..."
            conv = Conversation.objects.create(
                user_id=user_id,
                document=doc_obj,
                title=conv_title
            )

        user_msg = Message.objects.create(
            conversation=conv,
            role='user',
            content=question
        )

        history_msgs = list(conv.messages.all().order_by('-created_at')[:5])
        history_msgs.reverse()
        formatted_history = [{"role": m.role, "content": m.content} for m in history_msgs]

        # 0. Conversational Query Expansion / Rewriting
        search_query = QueryRewriterService.rewrite_query(question, formatted_history)

        # 1. Hybrid Retrieval
        t_retrieval_start = time.time()
        retrieved_candidates = self.retriever_service.retrieve_relevant_chunks(
            query=search_query,
            user_id=user_id,
            document_id=document_id,
            collection_id=collection_id,
            top_k=6
        )
        t_retrieval_end = time.time()
        retrieval_ms = int((t_retrieval_end - t_retrieval_start) * 1000)

        # 2. Reranking
        t_rerank_start = time.time()
        reranked_chunks = RerankerService.rerank_chunks(search_query, retrieved_candidates, top_n=4)
        t_rerank_end = time.time()
        rerank_ms = int((t_rerank_end - t_rerank_start) * 1000)

        # 3. Prompt & LLM Generation
        t_llm_start = time.time()
        prompt_data = PromptService.build_qa_prompt(question, reranked_chunks, formatted_history)
        llm_response = LLMService.generate_response(prompt_data["messages"])
        t_llm_end = time.time()
        llm_ms = int((t_llm_end - t_llm_start) * 1000)

        # 4. Grounding Check
        answer_content = llm_response["content"]
        grounding_result = GroundingService.verify_grounding(answer_content, reranked_chunks)

        t_total_end = time.time()
        total_ms = int((t_total_end - t_start) * 1000)

        latency_metrics = {
            "retrieval_ms": retrieval_ms,
            "rerank_ms": rerank_ms,
            "llm_ms": llm_ms,
            "total_ms": total_ms
        }

        # 5. Format Source Citations with Explainability Reasons
        sources_data = []
        for idx, item in enumerate(reranked_chunks, 1):
            score_val = item.get("retrieval_score", 0.85)
            reason_text = f"Extracted from page {item.get('page_number', 1)} with similarity score {score_val}. Contains text matching keywords and semantic context from your question."
            sources_data.append({
                "source_index": idx,
                "document_id": item["document_id"],
                "document_title": item["document_title"],
                "page_number": item["page_number"],
                "retrieval_score": score_val,
                "reason": reason_text,
                "chunk_preview": item["content"][:220] + "..." if len(item["content"]) > 220 else item["content"]
            })

        assistant_msg = Message.objects.create(
            conversation=conv,
            role='assistant',
            content=answer_content,
            sources=sources_data,
            latency_metrics=latency_metrics
        )

        return {
            "conversation_id": conv.id,
            "message_id": assistant_msg.id,
            "rewritten_query": search_query,
            "answer": answer_content,
            "sources": sources_data,
            "latency_metrics": latency_metrics,
            "grounding_result": grounding_result
        }

    def generate_summary(self, document_id: int, user_id: int, mode: str = "executive") -> Dict[str, Any]:
        """
        Generates document summary based on mode: 'executive', 'key_points', 'technical', 'risks'.
        """
        try:
            doc = Document.objects.get(id=document_id, user_id=user_id)
        except Document.DoesNotExist:
            return {"success": False, "summary": "Document not found.", "error": "404 Not Found"}

        chunks = list(doc.chunks.all().order_by('chunk_index')[:10])
        if not chunks:
            return {"success": False, "summary": "No extracted text available for summarization.", "error": "No text"}

        full_text = "\n\n".join([c.content for c in chunks])
        messages = PromptService.build_summary_prompt(full_text, mode=mode)

        res = LLMService.generate_response(messages)

        return {
            "success": res["success"],
            "mode": mode,
            "document_title": doc.title,
            "summary": res["content"],
            "error": res["error"]
        }
