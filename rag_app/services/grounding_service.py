from typing import List, Dict
import re

class GroundingService:
    @staticmethod
    def verify_grounding(answer: str, retrieved_chunks: List[Dict[str, any]]) -> dict:
        """
        Verifies if generated answer is grounded in retrieved context snippets.

        Returns:
            dict: {"is_grounded": bool, "faithfulness_score": float, "notes": str}
        """
        if not answer:
            return {"is_grounded": False, "faithfulness_score": 0.0, "notes": "Empty answer"}

        answer_lower = answer.lower()

        # Check if model declared information missing
        if "could not find this information" in answer_lower or "not available in the uploaded documents" in answer_lower:
            return {
                "is_grounded": True,
                "faithfulness_score": 1.0,
                "notes": "Model correctly identified unanswerable query."
            }

        if not retrieved_chunks:
            return {
                "is_grounded": False,
                "faithfulness_score": 0.0,
                "notes": "Answer generated without retrieved context."
            }

        # Check word overlap between answer and retrieved context
        context_words = set(re.findall(r"\w+", " ".join(
            c.get("content", "") for c in retrieved_chunks
        ).lower()))
        answer_words = set(
            word for word in re.findall(r"\w+", answer_lower) if len(word) > 3
        )

        if not answer_words:
            return {"is_grounded": True, "faithfulness_score": 0.8, "notes": "Short answer"}

        matches = sum(1 for word in answer_words if word in context_words)
        faithfulness = round(matches / len(answer_words), 2)
        is_grounded = faithfulness >= 0.35

        return {
            "is_grounded": is_grounded,
            "faithfulness_score": min(faithfulness, 1.0),
            "notes": "Sufficient keyword overlap with source text." if is_grounded else "Low overlap with context."
        }
