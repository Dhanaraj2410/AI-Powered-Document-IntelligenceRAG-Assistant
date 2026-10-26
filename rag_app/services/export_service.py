"""
Document Export Service — converts RAG responses and summaries into
downloadable text and JSON formats.

Supported formats:
  - plain_text   : Human-readable .txt report
  - json         : Structured JSON payload
  - markdown     : Markdown formatted report
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class ExportService:
    """Converts RAG query results and document summaries into export formats."""

    # ------------------------------------------------------------------
    # Entry points
    # ------------------------------------------------------------------

    @staticmethod
    def export_qa_result(
        question: str,
        answer: str,
        sources: List[Dict[str, Any]],
        fmt: str = "plain_text",
        document_title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Export a single Q&A exchange.

        Args:
            question: The user question.
            answer: The assistant's answer.
            sources: List of source citation dicts from RAG pipeline.
            fmt: One of ``plain_text``, ``json``, ``markdown``.
            document_title: Optional document name shown in the header.

        Returns:
            dict with keys ``content`` (str), ``filename`` (str),
            ``media_type`` (str).
        """
        fmt = fmt.lower().strip()
        if fmt == "json":
            return ExportService._qa_to_json(question, answer, sources, document_title)
        if fmt == "markdown":
            return ExportService._qa_to_markdown(question, answer, sources, document_title)
        return ExportService._qa_to_plain_text(question, answer, sources, document_title)

    @staticmethod
    def export_summary(
        summary: str,
        document_title: str,
        mode: str = "executive",
        fmt: str = "plain_text",
    ) -> Dict[str, Any]:
        """
        Export a generated document summary.

        Args:
            summary: Generated summary text.
            document_title: Name of the source document.
            mode: Summary mode label (e.g. executive, key_points).
            fmt: Export format.

        Returns:
            dict with keys ``content``, ``filename``, ``media_type``.
        """
        fmt = fmt.lower().strip()
        if fmt == "json":
            return ExportService._summary_to_json(summary, document_title, mode)
        if fmt == "markdown":
            return ExportService._summary_to_markdown(summary, document_title, mode)
        return ExportService._summary_to_plain_text(summary, document_title, mode)

    # ------------------------------------------------------------------
    # Q&A formatters
    # ------------------------------------------------------------------

    @staticmethod
    def _qa_to_plain_text(question, answer, sources, doc_title) -> Dict[str, Any]:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            "=" * 60,
            "AI-Powered Document Intelligence — Q&A Export",
            f"Generated: {timestamp}",
        ]
        if doc_title:
            lines.append(f"Document: {doc_title}")
        lines += [
            "=" * 60,
            "",
            f"QUESTION:\n{question}",
            "",
            f"ANSWER:\n{answer}",
            "",
        ]
        if sources:
            lines.append("SOURCES:")
            for s in sources:
                lines.append(
                    f"  [{s.get('source_index', '?')}] {s.get('document_title', 'Document')}, "
                    f"Page {s.get('page_number', 'N/A')}"
                )
        lines.append("")
        return {
            "content": "\n".join(lines),
            "filename": f"qa_export_{_slug(question)}.txt",
            "media_type": "text/plain",
        }

    @staticmethod
    def _qa_to_json(question, answer, sources, doc_title) -> Dict[str, Any]:
        payload = {
            "exported_at": datetime.utcnow().isoformat(),
            "document": doc_title,
            "question": question,
            "answer": answer,
            "sources": sources,
        }
        return {
            "content": json.dumps(payload, indent=2, ensure_ascii=False),
            "filename": f"qa_export_{_slug(question)}.json",
            "media_type": "application/json",
        }

    @staticmethod
    def _qa_to_markdown(question, answer, sources, doc_title) -> Dict[str, Any]:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            "# Q&A Export — AI Document Intelligence",
            f"*Generated: {timestamp}*",
        ]
        if doc_title:
            lines.append(f"\n**Document:** {doc_title}\n")
        lines += [
            f"\n## Question\n\n{question}\n",
            f"## Answer\n\n{answer}\n",
        ]
        if sources:
            lines.append("## Sources\n")
            for s in sources:
                lines.append(
                    f"- **[{s.get('source_index', '?')}]** {s.get('document_title', 'Document')}, "
                    f"Page {s.get('page_number', 'N/A')}"
                )
        return {
            "content": "\n".join(lines),
            "filename": f"qa_export_{_slug(question)}.md",
            "media_type": "text/markdown",
        }

    # ------------------------------------------------------------------
    # Summary formatters
    # ------------------------------------------------------------------

    @staticmethod
    def _summary_to_plain_text(summary, doc_title, mode) -> Dict[str, Any]:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        content = (
            f"{'=' * 60}\n"
            f"AI-Powered Document Intelligence — {mode.title()} Summary\n"
            f"Generated: {timestamp}\n"
            f"Document: {doc_title}\n"
            f"{'=' * 60}\n\n"
            f"{summary}\n"
        )
        return {
            "content": content,
            "filename": f"summary_{_slug(doc_title)}_{mode}.txt",
            "media_type": "text/plain",
        }

    @staticmethod
    def _summary_to_json(summary, doc_title, mode) -> Dict[str, Any]:
        payload = {
            "exported_at": datetime.utcnow().isoformat(),
            "document": doc_title,
            "mode": mode,
            "summary": summary,
        }
        return {
            "content": json.dumps(payload, indent=2, ensure_ascii=False),
            "filename": f"summary_{_slug(doc_title)}_{mode}.json",
            "media_type": "application/json",
        }

    @staticmethod
    def _summary_to_markdown(summary, doc_title, mode) -> Dict[str, Any]:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        content = (
            f"# {mode.title()} Summary — {doc_title}\n\n"
            f"*Generated: {timestamp}*\n\n"
            f"---\n\n"
            f"{summary}\n"
        )
        return {
            "content": content,
            "filename": f"summary_{_slug(doc_title)}_{mode}.md",
            "media_type": "text/markdown",
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slug(text: str, max_len: int = 30) -> str:
    """Convert arbitrary text to a safe filename slug."""
    import re
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text).strip("_")
    return text[:max_len] or "export"
