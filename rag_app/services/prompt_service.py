from typing import List, Dict

class PromptService:
    SYSTEM_PROMPT = """You are an expert Document Intelligence Assistant.

Your task is to answer the user's question accurately and concisely using ONLY the provided document context snippets below.

CRITICAL RULES FOR ACCURACY AND ANTI-HALLUCINATION:
1. Base your answer STRICTLY on the facts present in the provided Context.
2. Do NOT invent, assume, or extrapolate facts that are not explicitly stated in the Context.
3. If the answer cannot be found in or deduced from the provided Context, state clearly: "I could not find this information in the uploaded documents."
4. Maintain a professional, informative, and direct tone.
5. Reference specific page numbers or document names in your textual explanation when helpful."""

    @classmethod
    def build_context_string(cls, retrieved_chunks: List[Dict[str, any]]) -> str:
        """Formats list of retrieved chunk dicts into structured context block."""
        if not retrieved_chunks:
            return "No relevant context found."

        context_blocks = []
        for idx, chunk in enumerate(retrieved_chunks, 1):
            doc_title = chunk.get("document_title", "Document")
            page_num = chunk.get("page_number", "N/A")
            content = chunk.get("content", "").strip()

            block = f"[Source {idx}: Document '{doc_title}', Page {page_num}]\n{content}"
            context_blocks.append(block)

        return "\n\n" + ("=" * 40) + "\n\n" + "\n\n---\n\n".join(context_blocks) + "\n\n" + ("=" * 40)

    @classmethod
    def build_qa_prompt(cls, question: str, retrieved_chunks: List[Dict[str, any]], chat_history: List[Dict[str, str]] = None) -> dict:
        """
        Builds messages payload for LLM API call.

        Returns:
            dict: {"system": str, "messages": list}
        """
        context_str = cls.build_context_string(retrieved_chunks)

        messages = [
            {"role": "system", "content": cls.SYSTEM_PROMPT}
        ]

        # Add recent conversation memory if available
        if chat_history:
            for msg in chat_history[-4:]:  # last 2 turns
                role = "user" if msg.get("role") == "user" else "assistant"
                messages.append({"role": role, "content": msg.get("content", "")})

        # Append current user prompt with context
        user_prompt = f"DOCUMENT CONTEXT:\n{context_str}\n\nUSER QUESTION:\n{question}\n\nPlease answer the question based strictly on the document context above."
        messages.append({"role": "user", "content": user_prompt})

        return {
            "system": cls.SYSTEM_PROMPT,
            "messages": messages
        }
