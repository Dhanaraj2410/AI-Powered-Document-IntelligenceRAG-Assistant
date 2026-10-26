"""
Pytest tests for the ExportService.
"""
import json
import pytest

from rag_app.services.export_service import ExportService, _slug


SAMPLE_SOURCES = [
    {
        "source_index": 1,
        "document_title": "Annual Report 2024",
        "page_number": 3,
        "passage": "Revenue grew by 15% year-over-year.",
    }
]


class TestExportServiceQA:
    def test_plain_text_export_structure(self):
        result = ExportService.export_qa_result(
            question="What was the revenue growth?",
            answer="Revenue grew by 15% year-over-year.",
            sources=SAMPLE_SOURCES,
            fmt="plain_text",
            document_title="Annual Report 2024",
        )
        assert result["media_type"] == "text/plain"
        assert result["filename"].endswith(".txt")
        assert "Revenue grew" in result["content"]
        assert "QUESTION:" in result["content"]
        assert "ANSWER:" in result["content"]
        assert "SOURCES:" in result["content"]

    def test_json_export_structure(self):
        result = ExportService.export_qa_result(
            question="What was the revenue growth?",
            answer="Revenue grew by 15% year-over-year.",
            sources=SAMPLE_SOURCES,
            fmt="json",
        )
        assert result["media_type"] == "application/json"
        assert result["filename"].endswith(".json")
        parsed = json.loads(result["content"])
        assert parsed["question"] == "What was the revenue growth?"
        assert parsed["answer"] == "Revenue grew by 15% year-over-year."
        assert "exported_at" in parsed
        assert isinstance(parsed["sources"], list)

    def test_markdown_export_structure(self):
        result = ExportService.export_qa_result(
            question="What was the revenue growth?",
            answer="Revenue grew by 15%.",
            sources=SAMPLE_SOURCES,
            fmt="markdown",
        )
        assert result["media_type"] == "text/markdown"
        assert result["filename"].endswith(".md")
        assert "## Question" in result["content"]
        assert "## Answer" in result["content"]

    def test_empty_sources_does_not_crash(self):
        result = ExportService.export_qa_result(
            question="Any question?",
            answer="Any answer.",
            sources=[],
            fmt="plain_text",
        )
        assert "QUESTION:" in result["content"]

    def test_unknown_format_falls_back_to_plain_text(self):
        result = ExportService.export_qa_result(
            question="test",
            answer="answer",
            sources=[],
            fmt="xml",
        )
        assert result["media_type"] == "text/plain"


class TestExportServiceSummary:
    def test_plain_text_summary_export(self):
        result = ExportService.export_summary(
            summary="Key finding: profits doubled.",
            document_title="Q4 Report",
            mode="executive",
            fmt="plain_text",
        )
        assert "executive" in result["content"].lower() or "Executive" in result["content"]
        assert "Key finding" in result["content"]

    def test_json_summary_export(self):
        result = ExportService.export_summary(
            summary="Risks identified: vendor lock-in.",
            document_title="Risk Assessment",
            mode="risks",
            fmt="json",
        )
        parsed = json.loads(result["content"])
        assert parsed["mode"] == "risks"
        assert parsed["document"] == "Risk Assessment"

    def test_markdown_summary_export(self):
        result = ExportService.export_summary(
            summary="Top 3 action items: ...",
            document_title="Action Plan",
            mode="key_points",
            fmt="markdown",
        )
        assert result["content"].startswith("#")


class TestSlugHelper:
    def test_slug_lowercases(self):
        assert _slug("Hello World") == "hello_world"

    def test_slug_removes_special_chars(self):
        assert "!" not in _slug("What is AI?!")

    def test_slug_respects_max_len(self):
        assert len(_slug("a" * 100)) <= 30

    def test_slug_handles_empty_string(self):
        assert _slug("") == "export"
