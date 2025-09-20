# Tidal MCP Server Production Architecture

## Executive Summary

This document outlines the technical architecture for transforming the Tidal MCP server from a development prototype into a production-ready system. The architecture addresses critical gaps in testing, resilience, performance, monitoring, and scalability while maintaining backward compatibility with existing MCP clients.

## System Context

### Business Context

- **Business Drivers**: Production deployment of Tidal MCP server for enterprise use
- **Key Stakeholders**: Development teams, DevOps teams, End users
- **Success Metrics**:
  - < 200ms p99 latency for API calls
  - 99.9% availability
  - Zero data loss
  - < 5% error rate

### Technical Context

- **Current State**: FastMCP-based async Python server with OAuth2 authentication
- **Technology Stack**: Python 3.10+, FastMCP, tidalapi, aiohttp
- **Integration Points**: Tidal API, MCP clients, OAuth2 providers

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              MCP Clients                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         API Gateway Layer                                │
│                    (Rate Limiting, Circuit Breaker)                      │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Tidal MCP Server                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │   FastMCP    │  │   Service    │  │     Auth     │  │   Cache    │ │
│  │   Protocol   │  │    Layer     │  │   Manager    │  │   Layer    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         External Services                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │  Tidal API   │  │   Redis      │  │  Monitoring  │                  │
│  │              │  │   Cache      │  │   (Prometheus)│                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Architecture

- **API Gateway**: Handles rate limiting, circuit breaking, request routing
- **MCP Protocol Layer**: FastMCP framework for MCP protocol handling
- **Service Layer**: Business logic and Tidal API orchestration
- **Auth Manager**: OAuth2 PKCE flow, token management, session handling
- **Cache Layer**: Multi-tier caching (in-memory + Redis)
- **Resilience Layer**: Retry logic, circuit breakers, timeout management

## Detailed Design

### 1. Test Framework Architecture

#### Technology Choices

- **Unit Testing**: pytest + pytest-asyncio
- **Integration Testing**: pytest + aioresponses (mock HTTP)
- **E2E Testing**: pytest + real Tidal sandbox API
- **Coverage**: pytest-cov (target: 80%)

#### Test Structure

```python
tests/
├── unit/
│   ├── test_auth.py          # Auth manager unit tests
│   ├── test_service.py       # Service layer unit tests
│   ├── test_models.py        # Data model tests
│   └── test_utils.py         # Utility function tests
├── integration/
│   ├── test_mcp_protocol.py  # MCP protocol integration
│   ├── test_api_flow.py      # API flow integration
│   └── test_cache.py         # Cache integration tests
├── e2e/
│   ├── test_full_flow.py     # Complete user workflows
│   └── test_performance.py   # Performance benchmarks
├── fixtures/
│   ├── mock_data.py          # Test data fixtures
│   └── tidal_responses.json  # Sample API responses
└── conftest.py               # Pytest configuration
```

#### Testing Strategy

```yaml
test_strategy:
  unit:
    coverage: 80%
    execution_time: < 10s
    mock_strategy: all_external
  integration:
    coverage: 60%
    execution_time: < 30s
    mock_strategy: external_apis_only
  e2e:
    coverage: critical_paths
    execution_time: < 2m
    environment: staging_sandbox
  performance:
    load_profile:
      - concurrent_users: 100
      - requests_per_second: 1000
      - duration: 5m
    targets:
      - p50_latency: < 50ms
      - p99_latency: < 200ms
      - error_rate: < 1%
```

### 2. Resilience Patterns Implementation

#### Retry Strategy

```python
# retry_config.py
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

RETRY_CONFIG = {
    'auth': {
        'stop': stop_after_attempt(3),
        'wait': wait_exponential(multiplier=1, min=2, max=10),
        'retry_on': (AuthenticationError, TokenExpiredError),
    },
    'api': {
        'stop': stop_after_attempt(5),
        'wait': wait_exponential(multiplier=1, min=1, max=30),
        'retry_on': (NetworkError, TimeoutError, RateLimitError),
    },
    'cache': {
        'stop': stop_after_attempt(2),
        'wait': wait_exponential(multiplier=0.5, min=0.5, max=2),
        'retry_on': (RedisConnectionError,),
    }
}
```

#### Circuit Breaker Pattern

```python
# circuit_breaker.py
from aiocircuitbreaker import CircuitBreaker

CIRCUIT_BREAKER_CONFIG = {
    'tidal_api': {
        'failure_threshold': 5,
        'recovery_timeout': 60,
        'expected_exception': TidalAPIError,
        'fallback_function': cached_response_fallback,
    },
    'redis_cache': {
        'failure_threshold': 3,
        'recovery_timeout': 30,
        'expected_exception': RedisError,
        'fallback_function': in_memory_cache_fallback,
    }
}

class ResilientTidalClient:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=TidalAPIError
        )

    @circuit_breaker
    async def make_api_call(self, endpoint: str, **kwargs):
        # API call implementation
        pass
```

#### Timeout Management

```python
TIMEOUT_CONFIG = {
    'auth_flow': 300,      # 5 minutes for OAuth flow
    'api_call': 30,        # 30 seconds for API calls
    'cache_operation': 2,  # 2 seconds for cache ops
    'search': 10,          # 10 seconds for search
    'playlist_update': 15, # 15 seconds for playlist updates
}
```

### 3. Caching Strategy

#### Multi-Tier Cache Architecture

```python
# cache_architecture.py
class CacheLayer:
    """
    Three-tier caching strategy:
    L1: In-memory LRU cache (process-local)
    L2: Redis cache (shared)
    L3: Tidal API (source of truth)
    """

    def __init__(self):
        self.l1_cache = LRUCache(maxsize=1000, ttl=60)
        self.l2_cache = RedisCache(ttl=300)

    async def get(self, key: str):
        # Check L1 cache
        if value := self.l1_cache.get(key):
            return value

        # Check L2 cache
        if value := await self.l2_cache.get(key):
            self.l1_cache.set(key, value)
            return value

        # Fetch from source
        return None

    async def set(self, key: str, value: Any):
        # Write-through caching
        self.l1_cache.set(key, value)
        await self.l2_cache.set(key, value)
```

#### Cache Key Strategy

```python
CACHE_KEY_PATTERNS = {
    'track': 'tidal:track:{track_id}',
    'album': 'tidal:album:{album_id}',
    'artist': 'tidal:artist:{artist_id}',
    'playlist': 'tidal:playlist:{playlist_id}:{user_id}',
    'search': 'tidal:search:{query_hash}:{content_type}:{limit}:{offset}',
    'user_favorites': 'tidal:favorites:{user_id}:{content_type}',
    'recommendations': 'tidal:recommendations:{user_id}:{seed}',
}

CACHE_TTL = {
    'track': 3600,           # 1 hour
    'album': 3600,           # 1 hour
    'artist': 3600,          # 1 hour
    'playlist': 300,         # 5 minutes (changes frequently)
    'search': 600,           # 10 minutes
    'user_favorites': 300,   # 5 minutes
    'recommendations': 1800, # 30 minutes
}
```

### 4. Rate Limiting Implementation

#### Token Bucket Algorithm

```python
# rate_limiter.py
from asyncio_throttle import Throttler

class TidalRateLimiter:
    """
    Implements rate limiting for Tidal API calls
    """

    def __init__(self):
        # Tidal API limits (assumed)
        self.search_limiter = Throttler(rate_limit=10, period=1)  # 10 req/s
        self.user_limiter = Throttler(rate_limit=5, period=1)     # 5 req/s
        self.playlist_limiter = Throttler(rate_limit=2, period=1) # 2 req/s

    async def acquire(self, operation_type: str):
        limiter = self._get_limiter(operation_type)
        async with limiter:
            yield
```

#### Per-User Rate Limiting

```python
USER_RATE_LIMITS = {
    'free_tier': {
        'requests_per_minute': 60,
        'requests_per_hour': 1000,
        'concurrent_requests': 5,
    },
    'premium_tier': {
        'requests_per_minute': 300,
        'requests_per_hour': 10000,
        'concurrent_requests': 20,
    }
}
```

### 5. Performance Optimization

#### Async Optimization

```python
# performance.py
import asyncio
from concurrent.futures import ThreadPoolExecutor

class OptimizedTidalService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)

    async def batch_fetch(self, ids: List[str], fetch_func):
        """Batch fetch with concurrent execution"""
        tasks = [fetch_func(id) for id in ids]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def parallel_search(self, query: str):
        """Parallel search across all content types"""
        tasks = [
            self.search_tracks(query),
            self.search_albums(query),
            self.search_artists(query),
            self.search_playlists(query),
        ]
        results = await asyncio.gather(*tasks)
        return SearchResults(*results)
```

#### Connection Pooling

```python
# connection_pool.py
import aiohttp

class ConnectionManager:
    def __init__(self):
        self.connector = aiohttp.TCPConnector(
            limit=100,              # Total connection pool limit
            limit_per_host=30,      # Per-host connection limit
            ttl_dns_cache=300,      # DNS cache TTL
            keepalive_timeout=30,   # Keep-alive timeout
        )
        self.session = aiohttp.ClientSession(
            connector=self.connector,
            timeout=aiohttp.ClientTimeout(total=30),
        )
```

### 6. Monitoring and Observability

#### Metrics Collection

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_count = Counter(
    'tidal_mcp_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'tidal_mcp_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

# Cache metrics
cache_hits = Counter(
    'tidal_mcp_cache_hits_total',
    'Total number of cache hits',
    ['cache_level', 'content_type']
)

# Connection metrics
active_connections = Gauge(
    'tidal_mcp_active_connections',
    'Number of active connections'
)
```

#### Structured Logging

```python
# logging_config.py
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
```

#### Health Checks

```python
# health.py
from enum import Enum
from typing import Dict, Any

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class HealthChecker:
    async def check_health(self) -> Dict[str, Any]:
        checks = await asyncio.gather(
            self.check_tidal_api(),
            self.check_redis(),
            self.check_auth_service(),
            return_exceptions=True
        )

        return {
            "status": self._overall_status(checks),
            "checks": {
                "tidal_api": checks[0],
                "redis": checks[1],
                "auth": checks[2],
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
```

### 7. Configuration Management

#### Environment-Based Configuration

```yaml
# config/production.yaml
server:
  host: 0.0.0.0
  port: 8080
  workers: 4

tidal:
  api_base_url: https://api.tidal.com
  oauth_url: https://login.tidal.com
  timeout: 30
  max_retries: 3

redis:
  host: ${REDIS_HOST}
  port: 6379
  db: 0
  password: ${REDIS_PASSWORD}
  ssl: true
  connection_pool_size: 20

logging:
  level: INFO
  format: json
  output: stdout

monitoring:
  prometheus_port: 9090
  health_check_path: /health
  metrics_path: /metrics
```

#### Secret Management

```python
# secrets.py
from cryptography.fernet import Fernet
import os

class SecretManager:
    """Manages encrypted secrets and credentials"""

    def __init__(self):
        self.cipher = Fernet(os.getenv('ENCRYPTION_KEY').encode())

    def encrypt_secret(self, secret: str) -> bytes:
        return self.cipher.encrypt(secret.encode())

    def decrypt_secret(self, encrypted: bytes) -> str:
        return self.cipher.decrypt(encrypted).decode()

    def get_tidal_credentials(self):
        return {
            'client_id': os.getenv('TIDAL_CLIENT_ID'),
            'client_secret': self.decrypt_secret(
                os.getenv('TIDAL_CLIENT_SECRET_ENCRYPTED').encode()
            ),
        }
```

### 8. Package Distribution Architecture

#### Package Structure

```
tidal-mcp/
├── src/
│   └── tidal_mcp/
│       ├── __init__.py
│       ├── server.py
│       ├── auth.py
│       ├── service.py
│       ├── models.py
│       ├── cache.py
│       ├── resilience.py
│       ├── metrics.py
│       └── config.py
├── tests/
├── config/
│   ├── development.yaml
│   ├── staging.yaml
│   └── production.yaml
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yaml
├── helm/
│   └── tidal-mcp/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
├── pyproject.toml
├── setup.py
└── requirements/
    ├── base.txt
    ├── dev.txt
    └── prod.txt
```

#### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements/prod.txt .
RUN pip install --no-cache-dir -r prod.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY src/ ./src/
COPY config/ ./config/

ENV PYTHONPATH=/app/src
ENV CONFIG_ENV=production

EXPOSE 8080 9090

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health').raise_for_status()"

CMD ["python", "-m", "tidal_mcp.server"]
```

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

- [ ] Set up test framework infrastructure
- [ ] Implement unit tests for existing code
- [ ] Add structured logging
- [ ] Basic health checks

### Phase 2: Resilience (Weeks 3-4)

- [ ] Implement retry logic with tenacity
- [ ] Add circuit breaker pattern
- [ ] Timeout management
- [ ] Error handling improvements

### Phase 3: Performance (Weeks 5-6)

- [ ] Implement multi-tier caching
- [ ] Add rate limiting
- [ ] Connection pooling
- [ ] Async optimizations

### Phase 4: Observability (Weeks 7-8)

- [ ] Prometheus metrics integration
- [ ] Distributed tracing setup
- [ ] Performance dashboards
- [ ] Alert configuration

### Phase 5: Production Readiness (Weeks 9-10)

- [ ] Docker containerization
- [ ] Kubernetes deployment configs
- [ ] CI/CD pipeline setup
- [ ] Security hardening
- [ ] Documentation completion

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Tidal API rate limits exceeded | High | Medium | Implement intelligent caching and rate limiting |
| Token refresh failures | High | Low | Implement robust retry logic and fallback auth |
| Cache inconsistency | Medium | Medium | TTL management and cache invalidation strategy |
| Performance degradation under load | High | Medium | Load testing and auto-scaling |
| Security vulnerabilities | High | Low | Security scanning and secret management |
| Dependency version conflicts | Low | Medium | Dependency pinning and regular updates |

## Non-Functional Requirements

### Performance

- Response time: < 200ms p99
- Throughput: 1000 RPS minimum
- Concurrent users: 500

### Security

- OAuth2 PKCE flow
- TLS 1.3 for all communications
- Secret encryption at rest
- No PII logging

### Scalability

- Horizontal scaling support
- Stateless architecture
- Database connection pooling
- Cache-first approach

### Reliability

- 99.9% uptime SLA
- Graceful degradation
- Circuit breaker patterns
- Automated failover

## Technology Stack Summary

### Core Technologies

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.11+ | Async support, type hints, performance |
| Framework | FastMCP | MCP protocol native support |
| HTTP Client | aiohttp | Async, connection pooling |
| Tidal Integration | tidalapi | Official library support |

### Infrastructure Technologies

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Caching | Redis | Distributed, persistent, fast |
| Container | Docker | Standardized deployment |
| Orchestration | Kubernetes | Scalability, resilience |
| Monitoring | Prometheus + Grafana | Industry standard, powerful |
| Tracing | OpenTelemetry | Distributed tracing |
| CI/CD | GitHub Actions | Integration with repo |

### Testing Technologies

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Unit Testing | pytest | Python standard, async support |
| Mocking | pytest-mock, aioresponses | Comprehensive mocking |
| Coverage | pytest-cov | Coverage reporting |
| Load Testing | Locust | Python-based, scalable |
| Security | Bandit, Safety | Security scanning |

## Security Architecture

### Authentication Flow

```
┌─────────┐      ┌─────────┐      ┌──────────┐      ┌─────────┐
│  Client │─────▶│   MCP   │─────▶│  OAuth2  │─────▶│  Tidal  │
│         │◀─────│  Server │◀─────│  Handler │◀─────│   API   │
└─────────┘      └─────────┘      └──────────┘      └─────────┘
     │                                   │
     └───────────────────────────────────┘
              Encrypted Token Store
```

### Data Protection

- **In Transit**: TLS 1.3 for all connections
- **At Rest**: AES-256 encryption for secrets
- **Token Storage**: Encrypted file storage with restricted permissions
- **Session Management**: JWT with short expiry and refresh tokens

## Conclusion

This architecture provides a comprehensive approach to making the Tidal MCP server production-ready. It addresses all identified technical gaps while maintaining simplicity and performance. The phased implementation approach allows for incremental improvements with measurable milestones at each stage.

The architecture emphasizes:
- **Resilience** through retry patterns and circuit breakers
- **Performance** via caching and connection pooling
- **Observability** with comprehensive monitoring
- **Security** through proper authentication and encryption
- **Scalability** with stateless design and horizontal scaling support

With this architecture, the Tidal MCP server will be capable of handling production workloads with high reliability and performance.