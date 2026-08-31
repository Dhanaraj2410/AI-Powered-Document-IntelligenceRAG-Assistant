import logging
import re
from django.conf import settings

logger = logging.getLogger(__name__)

class LLMService:
    @staticmethod
    def generate_response(messages: list) -> dict:
        """
        Communicates with LLM API (Google Gemini API or OpenAI API) to generate grounded RAG response.
        If no API key is available or API calls fail, uses local context-synthesis generator.

        Returns:
            dict: {"success": bool, "content": str, "error": str}
        """
        gemini_key = getattr(settings, 'GEMINI_API_KEY', '') or ''
        gemini_model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-3.6-flash')

        openai_key = getattr(settings, 'OPENAI_API_KEY', '') or ''
        openai_model_name = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')

        # --- Priority 1: Google Gemini API ---
        if gemini_key and gemini_key != 'your_gemini_api_key_here':
            try:
                from google import genai
                client = genai.Client(api_key=gemini_key)

                # Format messages array into combined text prompt for Gemini
                combined_prompt = LLMService._format_messages_for_gemini(messages)
                
                # Use configured gemini model name (fallback to gemini-3.6-flash)
                target_model = gemini_model_name if 'gemini' in gemini_model_name else 'gemini-3.6-flash'

                response = client.models.generate_content(
                    model=target_model,
                    contents=combined_prompt
                )

                answer_text = response.text.strip() if response and response.text else ""
                if answer_text:
                    return {
                        "success": True,
                        "content": answer_text,
                        "error": ""
                    }
            except Exception as e:
                logger.warning(f"Google Gemini API call failed: {str(e)}. Trying OpenAI / local fallback.", exc_info=True)

        # --- Priority 2: OpenAI API ---
        if openai_key and openai_key != 'your_openai_api_key_here':
            try:
                import openai
                client = openai.OpenAI(api_key=openai_key)

                response = client.chat.completions.create(
                    model=openai_model_name,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=800
                )

                answer_text = response.choices[0].message.content.strip()
                return {
                    "success": True,
                    "content": answer_text,
                    "error": ""
                }
            except Exception as e:
                logger.warning(f"OpenAI API call failed: {str(e)}. Falling back to local context synthesis generator.")

        # --- Priority 3: Local RAG Context Synthesis Generator ---
        return LLMService._synthesize_answer_from_context(messages)

    @staticmethod
    def _format_messages_for_gemini(messages: list) -> str:
        """Converts structured messages list into unified prompt string for Gemini API."""
        prompt_parts = []
        for m in messages:
            role = m.get("role", "user").upper()
            content = m.get("content", "")
            if role == "SYSTEM":
                prompt_parts.append(f"INSTRUCTIONS:\n{content}\n")
            else:
                prompt_parts.append(f"[{role}]:\n{content}\n")
        return "\n\n".join(prompt_parts)

    @staticmethod
    def _synthesize_answer_from_context(messages: list) -> dict:
        """Local context synthesis generator fallback."""
        user_message = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_message = m.get("content", "")
                break

        if not user_message:
            return {"success": False, "content": "No user question provided.", "error": "Empty prompt"}

        question = ""
        context_text = ""

        if "USER QUESTION:" in user_message:
            parts = user_message.split("USER QUESTION:")
            context_text = parts[0]
            question = parts[1].strip() if len(parts) > 1 else ""
        else:
            question = user_message

        if "DOCUMENT CONTEXT:" in context_text:
            context_text = context_text.split("DOCUMENT CONTEXT:")[1]

        context_text = context_text.replace("Please answer the question based strictly on the document context above.", "").strip()

        if not context_text or "No relevant context found" in context_text:
            return {
                "success": True,
                "content": "I could not find this information in the uploaded documents.",
                "error": ""
            }

        source_blocks = re.findall(r'\[Source \d+: Document \'(.*?)\', Page (\d+)\]\n(.*?)(?=\[Source \d+:|\Z)', context_text, re.DOTALL)

        if not source_blocks:
            clean_snippet = context_text[:500].strip()
            return {
                "success": True,
                "content": f"Based on the uploaded document:\n\n{clean_snippet}",
                "error": ""
            }

        q_words = [w.lower() for w in re.findall(r'\w+', question) if len(w) > 3 and w.lower() not in ['what', 'which', 'where', 'when', 'who', 'about', 'from', 'with', 'have', 'been', 'were']]

        relevant_sentences = []
        for doc_name, page_num, snippet in source_blocks:
            sentences = [s.strip() for s in snippet.split('\n') if len(s.strip()) > 5]
            for s in sentences:
                s_lower = s.lower()
                matched_count = sum(1 for w in q_words if w in s_lower)
                if matched_count > 0 or len(relevant_sentences) < 2:
                    relevant_sentences.append((matched_count, doc_name, page_num, s))

        relevant_sentences.sort(key=lambda x: x[0], reverse=True)

        if relevant_sentences:
            selected_facts = []
            seen = set()
            for score, doc_name, page_num, fact in relevant_sentences[:3]:
                if fact not in seen:
                    seen.add(fact)
                    selected_facts.append(f"- {fact} (Source: {doc_name}, Page {page_num})")

            answer_body = "\n".join(selected_facts)
            formatted_answer = f"Based on the uploaded documents:\n\n{answer_body}"
        else:
            first_doc, first_page, first_snippet = source_blocks[0]
            first_line = first_snippet.strip().split('\n')[0]
            formatted_answer = f"Based on document {first_doc} (Page {first_page}):\n\n- {first_line}"

        return {
            "success": True,
            "content": formatted_answer,
            "error": ""
        }
