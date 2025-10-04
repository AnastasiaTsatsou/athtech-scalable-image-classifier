"""
Logging middleware for FastAPI application
"""

import time
import uuid
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.logging.config import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Log request start
        start_time = time.time()
        
        # Extract request information
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log request
        logger.info(
            f"Request started: {method} {url}",
            extra={
                'request_id': request_id,
                'method': method,
                'url': url,
                'client_ip': client_ip,
                'user_agent': user_agent,
                'endpoint': self._get_endpoint_name(request)
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Log successful response
            logger.info(
                f"Request completed: {method} {url} - {response.status_code}",
                extra={
                    'request_id': request_id,
                    'method': method,
                    'url': url,
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'endpoint': self._get_endpoint_name(request)
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate response time
            response_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed: {method} {url} - {str(e)}",
                extra={
                    'request_id': request_id,
                    'method': method,
                    'url': url,
                    'response_time': response_time,
                    'endpoint': self._get_endpoint_name(request),
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                },
                exc_info=True
            )
            
            raise
    
    def _get_endpoint_name(self, request: Request) -> str:
        """Extract endpoint name from request path"""
        path = request.url.path
        
        # Normalize path for logging
        if path.startswith('/api/v1/'):
            if '/classify' in path:
                return 'classify'
            elif '/health' in path:
                return 'health'
            elif '/model/info' in path:
                return 'model_info'
            else:
                return 'api_other'
        elif path == '/':
            return 'root'
        elif path == '/docs':
            return 'docs'
        elif path == '/redoc':
            return 'redoc'
        elif path == '/metrics':
            return 'metrics'
        else:
            return 'unknown'
