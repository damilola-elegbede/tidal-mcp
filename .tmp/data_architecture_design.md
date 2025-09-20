# Tidal MCP Server - Data Architecture Design

## Executive Summary

This document outlines a comprehensive data architecture for the Tidal MCP server, addressing session management, caching, rate limiting, user preferences, audit logging, and performance metrics with security, compliance, and performance optimization in mind.

## Architecture Overview

### Storage Layer Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│                   Data Access Layer                        │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐ │
│  │   Session   │    Cache    │ Rate Limit  │   Metrics   │ │
│  │   Manager   │   Manager   │   Manager   │   Manager   │ │
│  └─────────────┴─────────────┴─────────────┴─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                   Storage Abstraction                      │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐ │
│  │ Encrypted   │ In-Memory   │ Time-Series │   Archive   │ │
│  │ File Store  │   Cache     │   Store     │   Store     │ │
│  └─────────────┴─────────────┴─────────────┴─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                 Physical Storage                           │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐ │
│  │    Files    │   Memory    │   SQLite    │   Optional  │ │
│  │ (~/.tidal-  │   (Redis-   │  (Metrics)  │  External   │ │
│  │   mcp/)     │   like)     │             │     DB      │ │
│  └─────────────┴─────────────┴─────────────┴─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 1. Session Management Architecture

### 1.1 Enhanced Session Storage

**Current Issues:**
- Plain text JSON storage
- No encryption at rest
- No session rotation
- No concurrent session handling

**Proposed Solution:**

```python
class SecureSessionManager:
    """Enhanced session management with encryption and rotation"""

    def __init__(self, storage_path: Path = None):
        self.storage_path = storage_path or Path.home() / ".tidal-mcp"
        self.session_file = self.storage_path / "session.enc"
        self.key_file = self.storage_path / "session.key"
        self.backup_retention_days = 7

    # Encryption using Fernet (symmetric encryption)
    # Session rotation every 24 hours
    # Concurrent session detection
    # Automatic backup and cleanup
```

**Key Features:**
- **Encryption**: AES-256 encryption using cryptography.Fernet
- **Key Management**: Separate key file with restricted permissions (0o600)
- **Session Rotation**: Automatic rotation every 24 hours
- **Backup Strategy**: Rolling backups with 7-day retention
- **Concurrent Detection**: Device fingerprinting to detect multiple sessions

### 1.2 Session Schema

```json
{
  "schema_version": "1.0",
  "session_id": "uuid",
  "access_token": "encrypted_token",
  "refresh_token": "encrypted_token",
  "token_expires_at": "iso_timestamp",
  "user_id": "user_id",
  "country_code": "US",
  "device_fingerprint": "sha256_hash",
  "created_at": "iso_timestamp",
  "last_accessed": "iso_timestamp",
  "rotation_due": "iso_timestamp",
  "backup_count": 3
}
```

## 2. Cache Architecture

### 2.1 Multi-Level Caching Strategy

**L1 Cache - In-Memory (Hot Data)**
- TTL: 5 minutes
- Size Limit: 100MB
- LRU eviction policy
- Thread-safe implementation

**L2 Cache - File-based (Warm Data)**
- TTL: 1 hour
- Size Limit: 500MB
- Compressed JSON storage
- Automatic cleanup

**Cache Hierarchy:**

```python
class TidalCacheManager:
    """Multi-level cache with intelligent invalidation"""

    def __init__(self):
        self.l1_cache = TTLCache(maxsize=1000, ttl=300)  # 5 minutes
        self.l2_cache_path = Path.home() / ".tidal-mcp" / "cache"
        self.compression = True
        self.metrics = CacheMetrics()
```

### 2.2 Cache Key Strategy

```
Format: {domain}:{operation}:{params_hash}:{user_id}

Examples:
- search:tracks:sha256(query+limit+offset):user123
- playlist:details:playlist_id:user123
- artist:albums:artist_id+limit:user123
```

### 2.3 Cache Invalidation

**Time-based TTL:**
- Search results: 5 minutes
- User playlists: 15 minutes
- Artist/Album metadata: 1 hour
- Track details: 6 hours

**Event-based Invalidation:**
- Playlist modifications
- User preference changes
- Token refresh

## 3. Rate Limiting Architecture

### 3.1 Rate Limit Implementation

**Multi-tier Rate Limiting:**

```python
class RateLimitManager:
    """Advanced rate limiting with multiple strategies"""

    def __init__(self):
        self.limiters = {
            "api_calls": TokenBucket(capacity=100, refill_rate=1),      # per minute
            "search_queries": TokenBucket(capacity=20, refill_rate=0.33), # per minute
            "playlist_ops": TokenBucket(capacity=10, refill_rate=0.17),   # per minute
        }
        self.storage = FileBasedStorage()
```

**Rate Limit Rules:**
- API Calls: 100 per minute, 1000 per hour
- Search Queries: 20 per minute, 200 per hour
- Playlist Operations: 10 per minute, 100 per hour
- Authentication: 5 attempts per 15 minutes

### 3.2 Rate Limit Storage

```json
{
  "user_id": "user123",
  "limits": {
    "api_calls": {
      "current_tokens": 95,
      "last_refill": "timestamp",
      "capacity": 100,
      "refill_rate": 1
    }
  },
  "violations": [
    {
      "timestamp": "iso_timestamp",
      "limit_type": "search_queries",
      "attempted_calls": 25
    }
  ]
}
```

## 4. User Preferences Storage

### 4.1 Preferences Schema

```python
@dataclass
class UserPreferences:
    user_id: str
    created_at: datetime
    updated_at: datetime
    preferences: dict = field(default_factory=dict)

    # Default preferences structure
    DEFAULT_PREFERENCES = {
        "audio_quality": "HIGH",
        "search_defaults": {
            "limit": 20,
            "include_explicit": True
        },
        "cache_preferences": {
            "enable_cache": True,
            "cache_duration": 300
        },
        "privacy": {
            "enable_analytics": True,
            "share_usage_data": False
        }
    }
```

### 4.2 Preferences Storage Strategy

- **File-based**: JSON files per user in encrypted format
- **Validation**: Schema validation on load/save
- **Migration**: Version-aware schema migration
- **Backup**: Daily backups with 30-day retention

## 5. Audit Logging Architecture

### 5.1 Compliance Logging

**GDPR Compliance Features:**
- User consent tracking
- Data access logging
- Deletion request tracking
- Data export capabilities

```python
class AuditLogger:
    """GDPR-compliant audit logging"""

    def __init__(self):
        self.log_path = Path.home() / ".tidal-mcp" / "audit"
        self.encryption_enabled = True
        self.retention_days = 90  # Configurable
        self.max_log_size = 100 * 1024 * 1024  # 100MB
```

### 5.2 Audit Event Schema

```json
{
  "event_id": "uuid",
  "timestamp": "iso_timestamp",
  "user_id": "user123",
  "session_id": "session_uuid",
  "event_type": "api_call|auth|data_access|error",
  "action": "search_tracks|create_playlist|login",
  "resource": {
    "type": "track|playlist|user_data",
    "id": "resource_id"
  },
  "details": {
    "ip_address": "hashed_ip",
    "user_agent": "hashed_agent",
    "response_code": 200,
    "processing_time_ms": 150
  },
  "gdpr_category": "necessary|analytics|marketing|preferences"
}
```

## 6. Performance Metrics Collection

### 6.1 Metrics Architecture

**Time-Series Storage:**
- SQLite for local metrics
- Prometheus format export capability
- Automatic aggregation and cleanup

```python
class MetricsCollector:
    """Performance and usage metrics collection"""

    def __init__(self):
        self.db_path = Path.home() / ".tidal-mcp" / "metrics.db"
        self.collection_interval = 60  # seconds
        self.retention_days = 30
```

### 6.2 Collected Metrics

**Performance Metrics:**
- API response times (p50, p95, p99)
- Cache hit/miss ratios
- Error rates by endpoint
- Authentication success/failure rates

**Usage Metrics:**
- Search query patterns
- Popular content types
- Session duration
- Feature usage frequency

**System Metrics:**
- Memory usage
- File system usage
- Network I/O
- CPU utilization

## 7. Data Retention & Cleanup Policies

### 7.1 Retention Schedule

| Data Type | Retention Period | Cleanup Strategy |
|-----------|------------------|------------------|
| Session Data | 30 days inactive | Automatic purge |
| L1 Cache | 5 minutes | TTL eviction |
| L2 Cache | 1 hour | TTL + size limits |
| Audit Logs | 90 days | Rolling deletion |
| Metrics | 30 days | Aggregation + deletion |
| User Preferences | Indefinite | User-controlled |
| Backups | 7 days | Rolling cleanup |

### 7.2 Automated Cleanup

```python
class DataRetentionManager:
    """Automated data cleanup and archival"""

    def __init__(self):
        self.cleanup_schedule = {
            "session_cleanup": "daily",
            "cache_cleanup": "hourly",
            "audit_cleanup": "weekly",
            "metrics_cleanup": "daily"
        }
```

## 8. Security Implementation

### 8.1 Encryption Strategy

**Data at Rest:**
- Session tokens: AES-256-GCM encryption
- User preferences: AES-256-GCM encryption
- Audit logs: Optional encryption for sensitive events

**Key Management:**
- Derived keys using PBKDF2 with device-specific salt
- Key rotation every 90 days
- Secure key storage with restricted permissions

### 8.2 Security Headers & Validation

```python
class SecurityManager:
    """Security validation and encryption"""

    def __init__(self):
        self.token_validator = TokenValidator()
        self.encryption = EncryptionManager()
        self.input_sanitizer = InputSanitizer()
```

## 9. Backup & Recovery Strategy

### 9.1 Backup Strategy

**Session Data:**
- Daily encrypted backups
- 7-day retention
- Automatic integrity verification

**User Preferences:**
- Weekly backups
- 30-day retention
- Cross-platform compatibility

**Audit Logs:**
- Weekly compressed backups
- 90-day retention
- Tamper-proof archival

### 9.2 Recovery Procedures

**Session Recovery:**
1. Detect corrupted session file
2. Attempt repair from backup
3. Fallback to re-authentication
4. Log recovery event

**Data Recovery:**
1. Automatic backup detection
2. User-guided recovery options
3. Partial data recovery capability
4. Recovery validation

## 10. Performance Optimization

### 10.1 File I/O Optimization

- Asynchronous file operations
- Memory-mapped files for large datasets
- Batch operations for multiple writes
- Compression for archive storage

### 10.2 Cache Optimization

- Intelligent prefetching based on usage patterns
- Adaptive TTL based on data volatility
- Cache warming strategies
- Memory usage monitoring

### 10.3 Database Optimization

**SQLite Optimizations:**
- WAL mode for concurrent access
- Appropriate indexes for time-series queries
- Vacuum operations for space reclamation
- Connection pooling

## 11. Migration Strategy

### 11.1 Current to New Architecture

**Phase 1: Backward Compatibility**
- Maintain existing session.json format
- Add new storage components alongside
- Gradual migration of data

**Phase 2: Enhanced Features**
- Enable encryption for new sessions
- Implement caching improvements
- Add audit logging

**Phase 3: Full Migration**
- Convert existing sessions to encrypted format
- Remove legacy storage code
- Enable all advanced features

### 11.2 Version Management

```python
class StorageVersionManager:
    """Handle storage format migrations"""

    CURRENT_VERSION = "2.0"
    MIGRATION_MAP = {
        "1.0": "migrate_v1_to_v2",
        "1.1": "migrate_v11_to_v2"
    }
```

## 12. Monitoring & Alerting

### 12.1 Health Checks

- Storage system availability
- Encryption key accessibility
- Cache performance metrics
- Disk space monitoring

### 12.2 Alert Conditions

- Failed encryption/decryption
- Cache hit ratio below threshold
- Excessive rate limit violations
- Storage space exhaustion

## 13. Configuration Management

### 13.1 Configuration Schema

```yaml
storage:
  base_path: "~/.tidal-mcp"
  encryption:
    enabled: true
    key_rotation_days: 90
  backup:
    enabled: true
    retention_days: 7

cache:
  l1_ttl_seconds: 300
  l2_ttl_seconds: 3600
  max_memory_mb: 100
  compression: true

rate_limiting:
  api_calls_per_minute: 100
  search_queries_per_minute: 20
  enforcement: true

audit:
  enabled: true
  retention_days: 90
  encryption: true
  gdpr_compliance: true

metrics:
  collection_enabled: true
  retention_days: 30
  export_format: "prometheus"
```

## 14. Implementation Recommendations

### 14.1 Phased Implementation

**Phase 1 (Immediate - Security Critical):**
- Implement session encryption
- Add basic rate limiting
- Enhance session backup

**Phase 2 (Performance):**
- Multi-level caching
- Performance metrics collection
- Cache optimization

**Phase 3 (Compliance):**
- GDPR audit logging
- Data retention automation
- User preference management

### 14.2 Technology Choices

**Recommended Libraries:**
- **Encryption**: `cryptography` (already in dependencies)
- **Caching**: `cachetools` for in-memory, custom file cache
- **Rate Limiting**: `asyncio-throttle` (already in dependencies)
- **Metrics**: `sqlite3` for storage, custom collection
- **Compression**: `gzip` (built-in) for cache and backups

### 14.3 Performance Targets

- Session load time: < 50ms
- Cache hit ratio: > 80%
- API response time: < 200ms (cached), < 1s (uncached)
- Storage growth: < 10MB per user per month
- Cleanup operations: < 5 seconds daily

## 15. Risk Assessment & Mitigation

### 15.1 Security Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Key compromise | High | Low | Key rotation, secure storage |
| Session hijacking | High | Medium | Device fingerprinting, encryption |
| Data corruption | Medium | Low | Backup strategy, integrity checks |

### 15.2 Performance Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Cache invalidation | Medium | Medium | Smart invalidation, fallback |
| Storage exhaustion | High | Low | Automatic cleanup, monitoring |
| Rate limit abuse | Medium | Medium | Graduated penalties, detection |

## Conclusion

This comprehensive data architecture provides a robust foundation for the Tidal MCP server with strong security, performance optimization, and compliance capabilities. The phased implementation approach ensures minimal disruption while delivering immediate security improvements and long-term scalability.

The architecture balances file-based simplicity with advanced features like encryption, caching, and audit logging, making it suitable for both individual users and potential future enterprise deployments.