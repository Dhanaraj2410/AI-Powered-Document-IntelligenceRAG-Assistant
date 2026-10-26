"""
Health-check and readiness probe views for the RAG application.

Endpoints:
  GET /health/         - Liveness probe (always 200 if the server is up)
  GET /health/ready/   - Readiness probe (checks DB + vector index)
  GET /health/version/ - Returns application version metadata
"""
import logging
import time

from django.http import JsonResponse
from django.views import View
from django.db import connection, OperationalError

logger = logging.getLogger(__name__)

APP_VERSION = "1.0.0"
_START_TIME = time.time()


class LivenessView(View):
    """
    Kubernetes / Docker liveness probe.
    Returns HTTP 200 with basic server info as long as the Django process
    is running. No external dependencies are checked.
    """

    def get(self, request):
        uptime_seconds = int(time.time() - _START_TIME)
        return JsonResponse(
            {
                "status": "ok",
                "uptime_seconds": uptime_seconds,
                "service": "AI-Powered Document Intelligence RAG",
            }
        )


class ReadinessView(View):
    """
    Kubernetes / Docker readiness probe.
    Verifies the database connection and (optionally) the FAISS vector index
    are accessible before marking the pod as ready to serve traffic.
    """

    def get(self, request):
        checks: dict[str, dict] = {}
        overall_ok = True

        # --- Database connectivity check ---
        try:
            connection.ensure_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            checks["database"] = {"status": "ok"}
        except OperationalError as exc:
            checks["database"] = {"status": "error", "detail": str(exc)}
            overall_ok = False
            logger.error("Readiness probe: DB check failed. %s", exc)

        # --- Vector index check (non-fatal) ---
        try:
            from rag_app.services.vector_service import VectorService
            index = VectorService.get_index()
            checks["vector_index"] = {
                "status": "ok",
                "total_vectors": int(index.ntotal),
            }
        except Exception as exc:  # pragma: no cover
            checks["vector_index"] = {"status": "unavailable", "detail": str(exc)}
            logger.warning("Readiness probe: Vector index unavailable. %s", exc)
            # Not marked overall_ok = False — index rebuilds are recoverable

        http_status = 200 if overall_ok else 503
        return JsonResponse(
            {
                "status": "ready" if overall_ok else "not_ready",
                "checks": checks,
            },
            status=http_status,
        )


class VersionView(View):
    """Returns application version and environment metadata."""

    def get(self, request):
        from django.conf import settings

        return JsonResponse(
            {
                "version": APP_VERSION,
                "debug": settings.DEBUG,
                "embedding_model": getattr(settings, "EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2"),
                "llm_provider": _detect_llm_provider(settings),
            }
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _detect_llm_provider(settings) -> str:
    """Return the active LLM provider label based on configured API keys."""
    gemini_key = (getattr(settings, "GEMINI_API_KEY", "") or "").strip()
    openai_key = (getattr(settings, "OPENAI_API_KEY", "") or "").strip()
    placeholder_gemini = "your_gemini_api_key_here"
    placeholder_openai = "your_openai_api_key_here"

    if gemini_key and gemini_key != placeholder_gemini:
        return "google_gemini"
    if openai_key and openai_key != placeholder_openai:
        return "openai"
    return "local_fallback"
