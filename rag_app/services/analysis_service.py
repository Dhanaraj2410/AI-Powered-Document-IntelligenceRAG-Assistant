import logging
import json
import re
from typing import List, Dict, Any
from rag_app.models import Document
from .llm_service import LLMService

logger = logging.getLogger(__name__)

class AnalysisService:
    @staticmethod
    def analyze_document_and_generate_questions(document_id: int) -> Dict[str, Any]:
        """
        Analyzes an ingested document's extracted text chunks and generates
        a list of 4-5 relevant suggested questions tailored specifically to the document's content.

        Returns:
            dict: {
                "success": bool,
                "document_title": str,
                "suggested_questions": List[str],
                "topics": List[str]
            }
        """
        try:
            doc = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            return {"success": False, "document_title": "", "suggested_questions": [], "topics": []}

        # If already analyzed and has stored suggested questions, return them
        if doc.suggested_questions and len(doc.suggested_questions) > 0:
            return {
                "success": True,
                "document_title": doc.title,
                "suggested_questions": doc.suggested_questions,
                "topics": []
            }

        chunks = list(doc.chunks.all().order_by('chunk_index')[:8])
        if not chunks:
            fallback_q = [
                f"What is the main topic of {doc.title}?",
                "What are the key financial or operational highlights?",
                "What are the major conclusions or recommendations?",
                "What risk factors or issues are mentioned?"
            ]
            doc.suggested_questions = fallback_q
            doc.save(update_fields=['suggested_questions'])
            return {
                "success": True,
                "document_title": doc.title,
                "suggested_questions": fallback_q,
                "topics": []
            }

        sample_text = "\n\n".join([c.content for c in chunks])[:4000]

        prompt = f"""You are a document analysis AI.
Analyze the following text extracted from the document '{doc.title}'.
Generate 4 specific, relevant, and insightful questions that a user would likely ask about this document.

DOCUMENT TEXT:
{sample_text}

INSTRUCTIONS:
Return ONLY a valid JSON array of 4 question strings. Example:
[
  "What is the total revenue reported for FY2025?",
  "Who are the key executives mentioned?",
  "What operational risks are identified?",
  "What is the policy for employee annual leave?"
]"""

        messages = [
            {"role": "system", "content": "You analyze documents and output JSON arrays of suggested questions."},
            {"role": "user", "content": prompt}
        ]

        try:
            res = LLMService.generate_response(messages)
            content = res.get("content", "")

            # Extract JSON array from response
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                questions = json.loads(match.group(0))
            else:
                # Fallback splitting by lines
                lines = [l.strip('- *0123456789. ') for l in content.split('\n') if '?' in l]
                questions = lines[:4]

            if not questions or not isinstance(questions, list):
                questions = [
                    f"What are the core findings in {doc.title}?",
                    "What key metrics or figures are highlighted?",
                    "What risks or challenges are identified?",
                    "What future strategy or action items are proposed?"
                ]

            # Save to document model
            doc.suggested_questions = questions
            doc.save(update_fields=['suggested_questions'])

            return {
                "success": True,
                "document_title": doc.title,
                "suggested_questions": questions,
                "topics": []
            }

        except Exception as e:
            logger.error(f"Error analyzing document {document_id}: {str(e)}", exc_info=True)
            fallback_q = [
                f"What are the key takeaways from {doc.title}?",
                "What major statistics or figures are reported?",
                "What risks or recommendations are outlined?"
            ]
            doc.suggested_questions = fallback_q
            doc.save(update_fields=['suggested_questions'])
            return {
                "success": True,
                "document_title": doc.title,
                "suggested_questions": fallback_q,
                "topics": []
            }
