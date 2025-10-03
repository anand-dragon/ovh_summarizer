import logging
import time
from typing import Awaitable, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response

logger = logging.getLogger("app")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
            self, request: Request,
            call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start_time = time.time()
        response = None
        try:
            logger.info(f"Incoming request: {request.method} {request.url}")
            response = await call_next(request)
            return response
        finally:
            duration = (time.time() - start_time) * 1000
            status_code = response.status_code if response else "N/A"
            logger.info(f"Completed {request.method} {request.url} with status {status_code} in {duration:.2f}ms")
