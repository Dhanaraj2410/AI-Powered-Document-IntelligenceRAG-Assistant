"""
Audit Logging Middleware — records every API request/response pair to the
standard Python logging system with structured fields.

Fields logged per request:
  - method, path, query_string
  - status_code
  - latency_ms
  - user_id (if authenticated)
  - content_length
"""
import logging
import time

logger = logging.getLogger("rag_app.audit")


class AuditLogMiddleware:
    """
    Django WSGI middleware that logs every inbound request and its response.

    Add to MIDDLEWARE in settings.py **before** the session / auth middleware
    to capture unauthenticated requests as well:

        MIDDLEWARE = [
            "rag_app.middleware.AuditLogMiddleware",
            ...
        ]
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        t_start = time.monotonic()

        response = self.get_response(request)

        latency_ms = int((time.monotonic() - t_start) * 1000)

        user_id = (
            request.user.id
            if hasattr(request, "user") and request.user.is_authenticated
            else None
        )

        logger.info(
            "method=%s path=%s status=%d latency_ms=%d user_id=%s",
            request.method,
            request.path,
            response.status_code,
            latency_ms,
            user_id,
            extra={
                "http_method": request.method,
                "http_path": request.path,
                "http_status": response.status_code,
                "latency_ms": latency_ms,
                "user_id": user_id,
                "content_length": response.get("Content-Length", "-"),
            },
        )

        return response
