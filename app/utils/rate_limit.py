"""Simple in-memory rate limiting middleware for FastAPI."""

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware that limits requests per client IP using a sliding window.

    Stores request timestamps in memory (resets on app restart).
    For production, use Redis-backed rate limiting.
    """

    def __init__(self, app, max_requests: int | None = None, window_seconds: int = 1):
        super().__init__(app)
        self.max_requests = max_requests or settings.RATE_LIMIT_RPS
        self.window_seconds = window_seconds
        self._requests: defaultdict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old entries outside the window
        self._requests[client_ip] = [
            ts for ts in self._requests[client_ip]
            if now - ts < self.window_seconds
        ]

        if len(self._requests[client_ip]) >= self.max_requests:
            return Response(
                content='{"detail":"Rate limit exceeded. Please slow down."}',
                status_code=429,
                media_type="application/json",
            )

        self._requests[client_ip].append(now)
        return await call_next(request)


def add_rate_limit_middleware(app) -> None:
    """Attach rate-limiting middleware to the FastAPI application."""
    app.add_middleware(RateLimitMiddleware)
