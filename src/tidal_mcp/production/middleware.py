"""
Production Middleware Architecture for Tidal MCP Server

Comprehensive middleware stack providing rate limiting, request validation,
error handling, observability, and security features for production deployment.
"""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple

import redis.asyncio as redis
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class RequestContext:
    """Request context for tracking request lifecycle."""

    def __init__(self, request_id: str = None):
        self.request_id = request_id or str(uuid.uuid4())
        self.start_time = time.time()
        self.user_id: Optional[str] = None
        self.tier: str = "basic"
        self.metadata: Dict[str, Any] = {}

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time since request start."""
        return time.time() - self.start_time


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    concurrent_requests: int = 5
    burst_allowance: int = 20


class RateLimitTiers:
    """Rate limiting tiers configuration."""

    TIERS = {
        "free": RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            requests_per_day=1000,
            concurrent_requests=2,
            burst_allowance=5,
        ),
        "basic": RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=1000,
            requests_per_day=10000,
            concurrent_requests=5,
            burst_allowance=20,
        ),
        "premium": RateLimitConfig(
            requests_per_minute=300,
            requests_per_hour=5000,
            requests_per_day=50000,
            concurrent_requests=15,
            burst_allowance=100,
        ),
        "enterprise": RateLimitConfig(
            requests_per_minute=1000,
            requests_per_hour=20000,
            requests_per_day=200000,
            concurrent_requests=50,
            burst_allowance=500,
        ),
    }

    @classmethod
    def get_config(cls, tier: str) -> RateLimitConfig:
        """Get rate limit configuration for tier."""
        return cls.TIERS.get(tier, cls.TIERS["basic"])


class RateLimitError(Exception):
    """Rate limit exceeded error."""

    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


class RateLimiter:
    """Redis-based distributed rate limiter with multiple algorithms."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def check_rate_limit(
        self, user_id: str, tier: str, endpoint: str = "default"
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limits.

        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        config = RateLimitTiers.get_config(tier)
        current_time = int(time.time())

        # Check concurrent requests
        concurrent_key = f"concurrent:{user_id}"
        concurrent_count = await self._get_concurrent_count(concurrent_key)

        if concurrent_count >= config.concurrent_requests:
            return False, {
                "error": "CONCURRENT_REQUEST_LIMIT",
                "limit": config.concurrent_requests,
                "current": concurrent_count,
                "retry_after": 30,
            }

        # Check per-minute limit (token bucket)
        minute_allowed, minute_info = await self._check_token_bucket(
            user_id, "minute", config.requests_per_minute, config.burst_allowance
        )

        if not minute_allowed:
            return False, {
                "error": "RATE_LIMIT_EXCEEDED",
                "window": "minute",
                **minute_info,
            }

        # Check per-hour limit (sliding window)
        hour_allowed, hour_info = await self._check_sliding_window(
            user_id, "hour", config.requests_per_hour, 3600
        )

        if not hour_allowed:
            return False, {
                "error": "RATE_LIMIT_EXCEEDED",
                "window": "hour",
                **hour_info,
            }

        # Check daily quota
        day_allowed, day_info = await self._check_sliding_window(
            user_id, "day", config.requests_per_day, 86400
        )

        if not day_allowed:
            return False, {
                "error": "QUOTA_EXCEEDED",
                "window": "day",
                **day_info,
            }

        # Increment counters
        await self._increment_concurrent(concurrent_key)
        await self._consume_token(user_id, "minute")
        await self._record_request(user_id, "hour", current_time)
        await self._record_request(user_id, "day", current_time)

        return True, {
            "tier": tier,
            "limits": {
                "per_minute": config.requests_per_minute,
                "per_hour": config.requests_per_hour,
                "per_day": config.requests_per_day,
                "concurrent": config.concurrent_requests,
            },
            "remaining": {
                "per_minute": minute_info.get("remaining", 0),
                "per_hour": hour_info.get("remaining", 0),
                "per_day": day_info.get("remaining", 0),
                "concurrent": config.concurrent_requests - concurrent_count,
            },
        }

    async def _check_token_bucket(
        self, user_id: str, window: str, rate: int, burst: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Token bucket algorithm for burst handling."""
        key = f"bucket:{user_id}:{window}"
        bucket_size = rate + burst
        refill_rate = rate / 60  # tokens per second

        async with self.redis.pipeline() as pipe:
            pipe.multi()
            current_time = time.time()

            # Get current bucket state
            bucket_data = await self.redis.hgetall(key)
            if bucket_data:
                last_refill = float(bucket_data.get("last_refill", current_time))
                tokens = float(bucket_data.get("tokens", bucket_size))
            else:
                last_refill = current_time
                tokens = bucket_size

            # Calculate tokens to add
            time_passed = current_time - last_refill
            tokens_to_add = time_passed * refill_rate
            tokens = min(bucket_size, tokens + tokens_to_add)

            if tokens >= 1:
                # Consume token
                tokens -= 1
                pipe.hset(
                    key,
                    mapping={
                        "tokens": str(tokens),
                        "last_refill": str(current_time),
                    },
                )
                pipe.expire(key, 3600)  # 1 hour TTL
                await pipe.execute()

                return True, {
                    "remaining": int(tokens),
                    "limit": bucket_size,
                    "retry_after": int((1 - tokens) / refill_rate) if tokens < 1 else 0,
                }
            else:
                return False, {
                    "remaining": 0,
                    "limit": bucket_size,
                    "retry_after": int(1 / refill_rate),
                }

    async def _check_sliding_window(
        self, user_id: str, window: str, limit: int, window_size: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Sliding window log algorithm for precise limiting."""
        key = f"window:{user_id}:{window}"
        current_time = int(time.time())
        window_start = current_time - window_size

        async with self.redis.pipeline() as pipe:
            pipe.multi()
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            # Count current requests
            pipe.zcard(key)
            results = await pipe.execute()

            current_count = results[1]

            if current_count < limit:
                return True, {
                    "remaining": limit - current_count,
                    "limit": limit,
                    "window_start": window_start,
                }
            else:
                # Calculate retry after
                oldest_request = await self.redis.zrange(key, 0, 0, withscores=True)
                if oldest_request:
                    retry_after = int(oldest_request[0][1] + window_size - current_time)
                else:
                    retry_after = window_size

                return False, {
                    "remaining": 0,
                    "limit": limit,
                    "retry_after": max(1, retry_after),
                }

    async def _record_request(self, user_id: str, window: str, timestamp: int):
        """Record request in sliding window."""
        key = f"window:{user_id}:{window}"
        request_id = f"{timestamp}:{uuid.uuid4().hex[:8]}"

        async with self.redis.pipeline() as pipe:
            pipe.multi()
            pipe.zadd(key, {request_id: timestamp})
            pipe.expire(key, 86400 * 2)  # 2 days TTL
            await pipe.execute()

    async def _consume_token(self, user_id: str, window: str):
        """Consume token from bucket."""
        # Implementation handled in _check_token_bucket
        pass

    async def _get_concurrent_count(self, key: str) -> int:
        """Get current concurrent request count."""
        count = await self.redis.get(key)
        return int(count) if count else 0

    async def _increment_concurrent(self, key: str):
        """Increment concurrent request counter."""
        async with self.redis.pipeline() as pipe:
            pipe.multi()
            pipe.incr(key)
            pipe.expire(key, 300)  # 5 minutes TTL
            await pipe.execute()

    async def decrement_concurrent(self, user_id: str):
        """Decrement concurrent request counter."""
        key = f"concurrent:{user_id}"
        current = await self.redis.get(key)
        if current and int(current) > 0:
            await self.redis.decr(key)


class RequestValidator:
    """Request validation middleware."""

    @staticmethod
    def validate_search_query(query: str) -> bool:
        """Validate search query."""
        if not query or len(query.strip()) == 0:
            raise ValidationError("Search query cannot be empty")
        if len(query) > 500:
            raise ValidationError("Search query too long (max 500 characters)")
        return True

    @staticmethod
    def validate_track_id(track_id: str) -> bool:
        """Validate track ID format."""
        if not track_id.isdigit():
            raise ValidationError("Track ID must be numeric")
        return True

    @staticmethod
    def validate_limit(limit: int) -> bool:
        """Validate limit parameter."""
        if limit < 1 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100")
        return True

    @staticmethod
    def validate_offset(offset: int) -> bool:
        """Validate offset parameter."""
        if offset < 0:
            raise ValidationError("Offset must be non-negative")
        return True


class ErrorHandler:
    """Centralized error handling with standardized responses."""

    ERROR_CODES = {
        "AUTHENTICATION_REQUIRED": {
            "message": "Authentication token is required",
            "recovery_hints": [
                "Obtain a valid access token via authentication",
                "Include the token in your request",
            ],
        },
        "INVALID_TOKEN": {
            "message": "The provided authentication token is invalid",
            "recovery_hints": [
                "Verify the token format and content",
                "Obtain a new token if this one is corrupted",
            ],
        },
        "RATE_LIMIT_EXCEEDED": {
            "message": "API rate limit exceeded",
            "recovery_hints": [
                "Wait until the rate limit resets",
                "Consider upgrading to a higher tier",
            ],
        },
        "VALIDATION_ERROR": {
            "message": "Request validation failed",
            "recovery_hints": [
                "Check the request parameters",
                "Refer to the API documentation",
            ],
        },
        "TIDAL_API_ERROR": {
            "message": "Error communicating with Tidal API",
            "recovery_hints": [
                "Try the request again",
                "Contact support if the issue persists",
            ],
        },
        "INTERNAL_SERVER_ERROR": {
            "message": "An unexpected error occurred",
            "recovery_hints": [
                "Try again in a few moments",
                "Contact support if the problem persists",
            ],
        },
    }

    @classmethod
    def format_error(
        self,
        error_code: str,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Format standardized error response."""
        error_info = self.ERROR_CODES.get(error_code, {})

        response = {
            "error": error_code,
            "message": error_info.get("message", "An error occurred"),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id or str(uuid.uuid4()),
            "recovery_hints": error_info.get("recovery_hints", []),
        }

        if details:
            response["details"] = details

        return response


class SecurityMiddleware:
    """Security middleware for authentication and authorization."""

    def __init__(self, auth_manager):
        self.auth_manager = auth_manager

    async def authenticate_request(self, auth_header: Optional[str]) -> Optional[str]:
        """Authenticate request and return user ID."""
        if not auth_header:
            return None

        if not auth_header.startswith("Bearer "):
            raise ValidationError("Invalid authentication header format")

        token = auth_header[7:]  # Remove "Bearer " prefix

        # Validate token with auth manager
        if not await self.auth_manager.validate_token(token):
            raise ValidationError("Invalid or expired token")

        # Return user ID from token
        return await self.auth_manager.get_user_id_from_token(token)


class ObservabilityMiddleware:
    """Observability middleware for metrics and logging."""

    def __init__(self):
        self.metrics = defaultdict(int)
        self.response_times = defaultdict(list)

    def record_request(self, endpoint: str, method: str, status_code: int, duration: float):
        """Record request metrics."""
        metric_key = f"{method}:{endpoint}:{status_code}"
        self.metrics[metric_key] += 1
        self.response_times[endpoint].append(duration)

        # Log slow requests
        if duration > 1.0:  # 1 second threshold
            logger.warning(
                f"Slow request detected: {method} {endpoint} took {duration:.2f}s"
            )

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics summary."""
        return {
            "request_counts": dict(self.metrics),
            "avg_response_times": {
                endpoint: sum(times) / len(times)
                for endpoint, times in self.response_times.items()
                if times
            },
        }


class MiddlewareStack:
    """Comprehensive middleware stack orchestrator."""

    def __init__(
        self,
        redis_client: redis.Redis,
        auth_manager,
        enable_rate_limiting: bool = True,
        enable_validation: bool = True,
        enable_observability: bool = True,
    ):
        self.rate_limiter = RateLimiter(redis_client) if enable_rate_limiting else None
        self.security = SecurityMiddleware(auth_manager)
        self.validator = RequestValidator() if enable_validation else None
        self.observability = ObservabilityMiddleware() if enable_observability else None
        self.error_handler = ErrorHandler()

    def middleware(self, endpoint_name: str = "unknown", require_auth: bool = True):
        """Middleware decorator for MCP tools."""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> Dict[str, Any]:
                request_id = str(uuid.uuid4())
                context = RequestContext(request_id)

                try:
                    # Authentication
                    if require_auth:
                        auth_header = kwargs.get("auth_header")
                        user_id = await self.security.authenticate_request(auth_header)
                        if not user_id:
                            return self.error_handler.format_error(
                                "AUTHENTICATION_REQUIRED", request_id=request_id
                            )
                        context.user_id = user_id

                    # Rate limiting
                    if self.rate_limiter and context.user_id:
                        allowed, rate_info = await self.rate_limiter.check_rate_limit(
                            context.user_id, context.tier, endpoint_name
                        )

                        if not allowed:
                            return self.error_handler.format_error(
                                rate_info.get("error", "RATE_LIMIT_EXCEEDED"),
                                details=rate_info,
                                request_id=request_id,
                            )

                        context.metadata["rate_limit"] = rate_info

                    # Request validation
                    if self.validator:
                        await self._validate_request(kwargs)

                    # Execute the actual function
                    result = await func(*args, **kwargs)

                    # Add metadata to response
                    if isinstance(result, dict):
                        result["_metadata"] = {
                            "request_id": request_id,
                            "processing_time": context.elapsed_time,
                            "rate_limit": context.metadata.get("rate_limit"),
                        }

                    # Record metrics
                    if self.observability:
                        self.observability.record_request(
                            endpoint_name, "POST", 200, context.elapsed_time
                        )

                    return result

                except ValidationError as e:
                    error_response = self.error_handler.format_error(
                        "VALIDATION_ERROR",
                        details={"validation_errors": [str(e)]},
                        request_id=request_id,
                    )

                    if self.observability:
                        self.observability.record_request(
                            endpoint_name, "POST", 400, context.elapsed_time
                        )

                    return error_response

                except RateLimitError as e:
                    error_response = self.error_handler.format_error(
                        "RATE_LIMIT_EXCEEDED",
                        details={"retry_after": e.retry_after},
                        request_id=request_id,
                    )

                    if self.observability:
                        self.observability.record_request(
                            endpoint_name, "POST", 429, context.elapsed_time
                        )

                    return error_response

                except Exception as e:
                    logger.exception(f"Unexpected error in {endpoint_name}: {e}")

                    error_response = self.error_handler.format_error(
                        "INTERNAL_SERVER_ERROR",
                        details={"error_type": type(e).__name__},
                        request_id=request_id,
                    )

                    if self.observability:
                        self.observability.record_request(
                            endpoint_name, "POST", 500, context.elapsed_time
                        )

                    return error_response

                finally:
                    # Cleanup concurrent request counter
                    if self.rate_limiter and context.user_id:
                        await self.rate_limiter.decrement_concurrent(context.user_id)

            return wrapper

        return decorator

    async def _validate_request(self, kwargs: Dict[str, Any]):
        """Validate request parameters."""
        # Search query validation
        if "query" in kwargs:
            self.validator.validate_search_query(kwargs["query"])

        # Track ID validation
        if "track_id" in kwargs:
            self.validator.validate_track_id(kwargs["track_id"])

        # Limit validation
        if "limit" in kwargs:
            self.validator.validate_limit(kwargs["limit"])

        # Offset validation
        if "offset" in kwargs:
            self.validator.validate_offset(kwargs["offset"])


# Context manager for request lifecycle
@asynccontextmanager
async def request_context(middleware_stack: MiddlewareStack, user_id: str):
    """Context manager for request lifecycle tracking."""
    try:
        yield
    finally:
        if middleware_stack.rate_limiter:
            await middleware_stack.rate_limiter.decrement_concurrent(user_id)


# Health check utilities
class HealthChecker:
    """Health check utilities for monitoring system status."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance."""
        try:
            start_time = time.time()
            await self.redis.ping()
            response_time = (time.time() - start_time) * 1000  # ms

            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "last_checked": datetime.utcnow().isoformat() + "Z",
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.utcnow().isoformat() + "Z",
            }

    async def check_rate_limiter_health(self) -> Dict[str, Any]:
        """Check rate limiter functionality."""
        try:
            test_key = f"health_check:{uuid.uuid4().hex[:8]}"
            start_time = time.time()

            # Test basic Redis operations
            await self.redis.set(test_key, "test", ex=10)
            value = await self.redis.get(test_key)
            await self.redis.delete(test_key)

            response_time = (time.time() - start_time) * 1000  # ms

            if value != b"test":
                raise Exception("Redis read/write test failed")

            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "last_checked": datetime.utcnow().isoformat() + "Z",
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.utcnow().isoformat() + "Z",
            }