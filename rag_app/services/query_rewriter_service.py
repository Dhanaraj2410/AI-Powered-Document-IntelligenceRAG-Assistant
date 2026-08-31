import logging
import re
from typing import List, Dict, Any
from .llm_service import LLMService

logger = logging.getLogger(__name__)

class QueryRewriterService:
    @staticmethod
    def rewrite_query(question: str, history: List[Dict[str, str]]) -> str:
        """
        Rewrites conversational / ambiguous user questions into standalone, explicit search queries.
        Example: 'What about last year?' + History -> 'What was the company revenue in FY2024?'
        """
        if not history or len(history) < 2:
            return question

        # If question is long and self-contained (> 8 words), return as-is
        words = question.strip().split()
        if len(words) > 10:
            return question

        # Build context prompt for rewriter
        recent_history_str = ""
        for msg in history[-4:]:
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "")
            recent_history_str += f"{role}: {content}\n"

        prompt = f"""You are a Conversational Query Expansion AI.
Given the recent chat history and a follow-up user question, rewrite the question into a single, standalone search query that preserves all relevant context (company names, years, entities).

CHAT HISTORY:
{recent_history_str}

FOLLOW-UP QUESTION:
{question}

INSTRUCTIONS:
Output ONLY the rewritten standalone question string. Do NOT add extra explanations or tags."""

        messages = [
            {"role": "system", "content": "You expand conversational follow-up questions into clear standalone search queries."},
            {"role": "user", "content": prompt}
        ]

        try:
            res = LLMService.generate_response(messages)
            rewritten = res.get("content", "").strip()

            # Clean output
            rewritten = re.sub(r'^(Rewritten Question|Query|Standalone Question):\s*', '', rewritten, flags=re.IGNORECASE)
            rewritten = rewritten.strip('"\'')

            if len(rewritten) > 5 and len(rewritten) < 200:
                logger.info(f"Query Rewriter: '{question}' -> '{rewritten}'")
                return rewritten

        except Exception as e:
            logger.warning(f"Query rewriter failed: {str(e)}. Using original question.")

        return question
