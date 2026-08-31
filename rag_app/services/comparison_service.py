import logging
from typing import Dict, Any
from rag_app.models import Document
from .llm_service import LLMService

logger = logging.getLogger(__name__)

class ComparisonService:
    @staticmethod
    def compare_documents(doc_a_id: int, doc_b_id: int, user_id: int) -> Dict[str, Any]:
        """
        Executes multi-document comparison between Document A and Document B.
        Synthesizes structured side-by-side Markdown comparison report.
        """
        try:
            doc_a = Document.objects.get(id=doc_a_id, user_id=user_id)
            doc_b = Document.objects.get(id=doc_b_id, user_id=user_id)
        except Document.DoesNotExist:
            return {"success": False, "error": "One or both documents were not found or belong to another user account."}

        # Retrieve text chunks from both documents
        chunks_a = list(doc_a.chunks.all().order_by('chunk_index')[:10])
        chunks_b = list(doc_b.chunks.all().order_by('chunk_index')[:10])

        if not chunks_a and doc_a.status != 'failed':
            from .rag_service import RAGService
            RAGService().process_document(doc_a.id)
            doc_a.refresh_from_db()
            chunks_a = list(doc_a.chunks.all().order_by('chunk_index')[:10])

        if not chunks_b and doc_b.status != 'failed':
            from .rag_service import RAGService
            RAGService().process_document(doc_b.id)
            doc_b.refresh_from_db()
            chunks_b = list(doc_b.chunks.all().order_by('chunk_index')[:10])

        text_a = "\n\n".join([c.content for c in chunks_a]) if chunks_a else f"Document Title: {doc_a.title}"
        text_b = "\n\n".join([c.content for c in chunks_b]) if chunks_b else f"Document Title: {doc_b.title}"

        # Build direct system and user prompt with clear context demarcation
        system_instruction = "You are a Senior Document Comparison Analyst. Synthesize a detailed, grounded side-by-side comparison report between Document A and Document B in Markdown format."
        user_prompt = f"""DOCUMENT CONTEXT A: '{doc_a.title}' ({doc_a.page_count} Pages)
{text_a[:3500]}

DOCUMENT CONTEXT B: '{doc_b.title}' ({doc_b.page_count} Pages)
{text_b[:3500]}

USER QUESTION: Provide a detailed side-by-side comparative analysis between Document A and Document B.

INSTRUCTIONS:
Generate a clear Markdown report covering:
## 1. Executive Summary & Overview
## 2. Quantitative & Metric Diffs
## 3. Operational & Policy Comparison
## 4. Key Takeaways & Strategic Differences"""

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ]

        llm_res = LLMService.generate_response(messages)
        report_text = llm_res.get("content", "")

        # Fallback to local structured comparison if LLM is rate-limited or output is default unanswerable
        if not report_text or "I could not find this information" in report_text or len(report_text.strip()) < 40:
            report_text = ComparisonService._generate_local_comparison(doc_a, doc_b, chunks_a, chunks_b)

        return {
            "success": True,
            "doc_a": {
                "id": doc_a.id,
                "title": doc_a.title,
                "pages": doc_a.page_count,
                "chunks": doc_a.chunk_count
            },
            "doc_b": {
                "id": doc_b.id,
                "title": doc_b.title,
                "pages": doc_b.page_count,
                "chunks": doc_b.chunk_count
            },
            "comparison_report": report_text,
            "error": ""
        }

    @staticmethod
    def _generate_local_comparison(doc_a: Document, doc_b: Document, chunks_a: list, chunks_b: list) -> str:
        """Generates a structured comparative report directly from extracted chunks."""
        report = []
        report.append(f"## Side-by-Side Comparison Report: {doc_a.title} vs {doc_b.title}\n")
        report.append("### 1. Document Scope & Structure Metrics")
        report.append(f"- **Document A**: `{doc_a.title}` | **Pages**: {doc_a.page_count} | **Indexed Chunks**: {doc_a.chunk_count}")
        report.append(f"- **Document B**: `{doc_b.title}` | **Pages**: {doc_b.page_count} | **Indexed Chunks**: {doc_b.chunk_count}\n")

        report.append("### 2. Extracted Highlights from Document A")
        if chunks_a:
            lines_a = [l.strip() for c in chunks_a for l in c.content.split('\n') if len(l.strip()) > 15][:5]
            for l in lines_a:
                report.append(f"- {l}")
        else:
            report.append("- Document A text extracted and indexed.")

        report.append("\n### 3. Extracted Highlights from Document B")
        if chunks_b:
            lines_b = [l.strip() for c in chunks_b for l in c.content.split('\n') if len(l.strip()) > 15][:5]
            for l in lines_b:
                report.append(f"- {l}")
        else:
            report.append("- Document B text extracted and indexed.")

        report.append("\n### 4. Comparative Differences & Takeaways")
        if doc_a.id == doc_b.id or doc_a.title == doc_b.title:
            report.append(f"- Both selected document entries point to `{doc_a.title}`.")
            report.append(f"- **Total Document Scope**: {doc_a.page_count} pages with {doc_a.chunk_count} indexed chunks.")
        else:
            report.append(f"- Document A (`{doc_a.title}`) spans {doc_a.page_count} pages with {doc_a.chunk_count} vector chunks.")
            report.append(f"- Document B (`{doc_b.title}`) spans {doc_b.page_count} pages with {doc_b.chunk_count} vector chunks.")
            report.append("- Both documents are accessible for multi-document RAG querying in Chat.")

        return "\n".join(report)
