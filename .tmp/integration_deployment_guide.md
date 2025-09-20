# Integration & Deployment Guide

## Integration Strategy for Tidal MCP Server

### Phase 1: Integration with Existing Code

#### 1.1 Update Authentication Layer

**Modify `src/tidal_mcp/auth.py`:**

```python
# Add imports at the top
from .storage import SecureSessionManager, AuditLogger, EventType

class TidalAuth:
    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        # ... existing code ...

        # Replace simple session file with secure session manager
        self.session_manager = SecureSessionManager()
        self.audit_logger = AuditLogger()

        # Load existing session using new manager
        self._load_session_secure()

    def _load_session_secure(self) -> None:
        """Load session using secure session manager"""
        try:
            session_data = self.session_manager.load_session()
            if session_data:
                self.access_token = session_data.get("access_token")
                self.refresh_token = session_data.get("refresh_token")
                # ... rest of loading logic ...

                # Log session loaded
                asyncio.create_task(self.audit_logger.log_event(
                    EventType.AUTHENTICATION,
                    "session_loaded",
                    user_id=self.user_id
                ))
        except Exception as e:
            logger.warning(f"Failed to load secure session: {e}")

    def _save_session_secure(self) -> None:
        """Save session using secure session manager"""
        try:
            session_data = {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "session_id": self.session_id,
                "user_id": self.user_id,
                "country_code": self.country_code,
                "expires_at": self.token_expires_at.isoformat() if self.token_expires_at else None,
            }

            success = self.session_manager.save_session(session_data)
            if success:
                # Log session saved
                asyncio.create_task(self.audit_logger.log_event(
                    EventType.AUTHENTICATION,
                    "session_saved",
                    user_id=self.user_id
                ))
        except Exception as e:
            logger.error(f"Failed to save secure session: {e}")
```

#### 1.2 Update Service Layer

**Modify `src/tidal_mcp/service.py`:**

```python
# Add imports
from .storage import (
    TidalCacheManager, RateLimitManager, LimitType,
    MetricsCollector, AuditLogger, EventType
)
import time

class TidalService:
    def __init__(self, auth: TidalAuth):
        self.auth = auth

        # Replace simple cache with advanced cache manager
        self.cache_manager = TidalCacheManager()

        # Add new managers
        self.rate_limiter = RateLimitManager()
        self.metrics_collector = MetricsCollector()
        self.audit_logger = AuditLogger()

    async def search_tracks(self, query: str, limit: int = 20, offset: int = 0) -> list[Track]:
        """Enhanced search with caching, rate limiting, and metrics"""
        start_time = time.time()
        user_id = self.auth.user_id or "anonymous"

        try:
            # Check rate limits
            allowed, limit_info = await self.rate_limiter.check_limit(
                user_id, LimitType.SEARCH_QUERIES, 1
            )
            if not allowed:
                await self.audit_logger.log_event(
                    EventType.API_CALL,
                    "search_tracks_rate_limited",
                    user_id=user_id,
                    details=limit_info
                )
                raise Exception(f"Rate limit exceeded: {limit_info}")

            # Check cache first
            cache_key_params = {"query": query, "limit": limit, "offset": offset}
            cached_result = await self.cache_manager.get(
                "search", "tracks", cache_key_params, user_id
            )

            if cached_result:
                duration_ms = (time.time() - start_time) * 1000
                await self.metrics_collector.record_search_metrics(
                    "tracks", len(cached_result), duration_ms, cached=True
                )
                await self.audit_logger.log_event(
                    EventType.API_CALL,
                    "search_tracks_cached",
                    user_id=user_id,
                    details={"query": query, "results": len(cached_result)}
                )
                return cached_result

            # Perform actual search
            await self.ensure_authenticated()

            # ... existing search logic ...
            tracks = []  # Your existing search implementation

            # Cache results
            if tracks:
                await self.cache_manager.set(
                    "search", "tracks", cache_key_params, user_id,
                    tracks, ttl_seconds=300, tags={"type": "search", "user": user_id}
                )

            # Record metrics
            duration_ms = (time.time() - start_time) * 1000
            await self.metrics_collector.record_search_metrics(
                "tracks", len(tracks), duration_ms, cached=False
            )

            # Log successful search
            await self.audit_logger.log_event(
                EventType.API_CALL,
                "search_tracks_success",
                user_id=user_id,
                details={"query": query, "results": len(tracks), "duration_ms": duration_ms}
            )

            return tracks

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            await self.audit_logger.log_event(
                EventType.ERROR,
                "search_tracks_failed",
                user_id=user_id,
                details={"query": query, "error": str(e), "duration_ms": duration_ms}
            )

            # Record error metrics
            await self.metrics_collector.record_metric(
                "search_errors", 1, {"query_type": "tracks", "error_type": type(e).__name__}
            )

            raise
```

#### 1.3 Update Server Layer

**Modify `src/tidal_mcp/server.py`:**

```python
# Add imports
from .storage import PreferencesManager, MetricsCollector
import time

class TidalMCPServer:
    def __init__(self):
        # ... existing initialization ...

        # Add storage managers
        self.preferences_manager = PreferencesManager()
        self.metrics_collector = MetricsCollector()

    async def handle_request(self, request):
        """Enhanced request handling with metrics and preferences"""
        start_time = time.time()

        try:
            # Get user preferences
            user_id = self.get_user_id_from_request(request)
            if user_id:
                user_prefs = await self.preferences_manager.get_preferences(user_id)
                # Apply user preferences to request handling
                self.apply_user_preferences(request, user_prefs)

            # Process request (existing logic)
            response = await self.process_request(request)

            # Record successful API call
            duration_ms = (time.time() - start_time) * 1000
            await self.metrics_collector.record_api_call(
                endpoint=request.get('method', 'unknown'),
                method='POST',  # MCP is typically POST
                status_code=200,
                response_time_ms=duration_ms,
                user_id=user_id
            )

            return response

        except Exception as e:
            # Record failed API call
            duration_ms = (time.time() - start_time) * 1000
            await self.metrics_collector.record_api_call(
                endpoint=request.get('method', 'unknown'),
                method='POST',
                status_code=500,
                response_time_ms=duration_ms,
                user_id=user_id
            )
            raise

    def apply_user_preferences(self, request, user_prefs):
        """Apply user preferences to request"""
        if 'params' not in request:
            request['params'] = {}

        # Apply search preferences
        if request.get('method') == 'search_tracks':
            if 'limit' not in request['params']:
                request['params']['limit'] = user_prefs.preferences.get(
                    'search', {}
                ).get('default_limit', 20)
```

### Phase 2: Migration Strategy

#### 2.1 Data Migration Script

**Create `scripts/migrate_data.py`:**

```python
#!/usr/bin/env python3
"""
Migration script for Tidal MCP data architecture upgrade
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from tidal_mcp.storage import SecureSessionManager, PreferencesManager

async def migrate_session_data():
    """Migrate existing session.json to encrypted format"""
    old_session_file = Path.home() / ".tidal-mcp" / "session.json"

    if not old_session_file.exists():
        print("No existing session file found, skipping migration")
        return

    try:
        # Load old session
        with open(old_session_file) as f:
            old_session = json.load(f)

        # Create new session manager
        session_manager = SecureSessionManager()

        # Migrate data
        success = session_manager.save_session(old_session)

        if success:
            # Backup old file
            backup_file = old_session_file.with_suffix('.json.backup')
            old_session_file.rename(backup_file)
            print("Session data migrated successfully")
            print(f"Old session backed up to: {backup_file}")
        else:
            print("Failed to migrate session data")

    except Exception as e:
        print(f"Migration failed: {e}")

async def create_default_preferences():
    """Create default preferences for existing users"""
    try:
        # Check if we have session data to extract user ID
        session_manager = SecureSessionManager()
        session_data = session_manager.load_session()

        if session_data and session_data.get('user_id'):
            user_id = session_data['user_id']

            prefs_manager = PreferencesManager()
            user_prefs = await prefs_manager.get_preferences(user_id)

            print(f"Created default preferences for user: {user_id}")
        else:
            print("No user session found, skipping preferences creation")

    except Exception as e:
        print(f"Failed to create default preferences: {e}")

async def main():
    """Run all migration tasks"""
    print("Starting Tidal MCP data migration...")
    print("=" * 50)

    await migrate_session_data()
    await create_default_preferences()

    print("=" * 50)
    print("Migration completed!")

if __name__ == "__main__":
    asyncio.run(main())
```

#### 2.2 Gradual Rollout Plan

**Week 1-2: Core Security**
```bash
# 1. Deploy session encryption
python scripts/migrate_data.py

# 2. Enable rate limiting (start with generous limits)
# 3. Add basic audit logging
```

**Week 3-4: Performance**
```bash
# 1. Enable multi-level caching
# 2. Start metrics collection
# 3. Optimize cache hit ratios
```

**Week 5-6: Compliance**
```bash
# 1. Enable GDPR audit logging
# 2. Implement data retention
# 3. Add user preference management
```

### Phase 3: Configuration Management

#### 3.1 Configuration File

**Create `config/storage_config.yaml`:**

```yaml
# Tidal MCP Storage Configuration

session_management:
  encryption:
    enabled: true
    key_rotation_days: 90
  backup:
    enabled: true
    retention_days: 7
    max_backups: 5
  rotation:
    interval_hours: 24
    auto_rotate: true

caching:
  l1_cache:
    enabled: true
    max_size: 1000
    ttl_seconds: 300
  l2_cache:
    enabled: true
    max_size_mb: 500
    ttl_seconds: 3600
    compression: true
  invalidation:
    strategy: "tag_based"
    cleanup_interval: 300

rate_limiting:
  enabled: true
  limits:
    api_calls:
      per_minute: 100
      per_hour: 1000
      burst_allowance: 20
    search_queries:
      per_minute: 20
      per_hour: 200
      burst_allowance: 5
    playlist_operations:
      per_minute: 10
      per_hour: 100
      burst_allowance: 3
    auth_attempts:
      per_15_minutes: 5
      burst_allowance: 0
  penalty:
    max_penalty_seconds: 3600
    escalation_factor: 2

audit_logging:
  enabled: true
  retention_days: 90
  max_log_size_mb: 100
  compression: true
  encryption: true
  gdpr_compliance: true

metrics_collection:
  enabled: true
  collection_interval_seconds: 60
  aggregation_interval_seconds: 300
  retention_days: 30
  system_metrics: true
  export_prometheus: true

user_preferences:
  encryption: true
  backup:
    enabled: true
    max_backups: 5
  validation:
    strict_schema: true
    migration_support: true

storage_paths:
  base_directory: "~/.tidal-mcp"
  session_data: "sessions"
  cache_data: "cache"
  audit_logs: "audit"
  metrics_data: "metrics"
  preferences: "preferences"
  backups: "backups"

cleanup:
  enabled: true
  daily_cleanup: true
  weekly_deep_clean: true
  storage_size_alert_mb: 1000
```

#### 3.2 Configuration Loader

**Create `src/tidal_mcp/storage/config.py`:**

```python
"""
Configuration management for storage components
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class StorageConfig:
    """Storage configuration data class"""

    # Session management
    session_encryption_enabled: bool = True
    session_backup_enabled: bool = True
    session_rotation_hours: int = 24

    # Caching
    l1_cache_enabled: bool = True
    l1_cache_size: int = 1000
    l1_cache_ttl: int = 300
    l2_cache_enabled: bool = True
    l2_cache_size_mb: int = 500
    l2_cache_ttl: int = 3600

    # Rate limiting
    rate_limiting_enabled: bool = True
    api_calls_per_minute: int = 100
    search_queries_per_minute: int = 20

    # Audit logging
    audit_logging_enabled: bool = True
    audit_retention_days: int = 90
    audit_encryption: bool = True

    # Metrics
    metrics_enabled: bool = True
    metrics_retention_days: int = 30

    # Storage paths
    base_directory: str = "~/.tidal-mcp"

class ConfigManager:
    """Configuration manager for storage components"""

    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or Path(__file__).parent.parent.parent.parent / "config" / "storage_config.yaml"
        self._config = None

    def load_config(self) -> StorageConfig:
        """Load configuration from file or return defaults"""
        if self._config is not None:
            return self._config

        try:
            if self.config_file.exists():
                with open(self.config_file) as f:
                    config_data = yaml.safe_load(f)
                self._config = self._create_config_from_dict(config_data)
            else:
                self._config = StorageConfig()  # Use defaults

        except Exception as e:
            print(f"Failed to load config: {e}, using defaults")
            self._config = StorageConfig()

        return self._config

    def _create_config_from_dict(self, config_data: Dict[str, Any]) -> StorageConfig:
        """Create StorageConfig from dictionary"""
        return StorageConfig(
            # Session management
            session_encryption_enabled=config_data.get('session_management', {}).get('encryption', {}).get('enabled', True),
            session_backup_enabled=config_data.get('session_management', {}).get('backup', {}).get('enabled', True),
            session_rotation_hours=config_data.get('session_management', {}).get('rotation', {}).get('interval_hours', 24),

            # Caching
            l1_cache_enabled=config_data.get('caching', {}).get('l1_cache', {}).get('enabled', True),
            l1_cache_size=config_data.get('caching', {}).get('l1_cache', {}).get('max_size', 1000),
            l1_cache_ttl=config_data.get('caching', {}).get('l1_cache', {}).get('ttl_seconds', 300),

            # Rate limiting
            rate_limiting_enabled=config_data.get('rate_limiting', {}).get('enabled', True),
            api_calls_per_minute=config_data.get('rate_limiting', {}).get('limits', {}).get('api_calls', {}).get('per_minute', 100),

            # Add other config mappings...

            # Storage paths
            base_directory=config_data.get('storage_paths', {}).get('base_directory', '~/.tidal-mcp')
        )

# Global config instance
config_manager = ConfigManager()
```

### Phase 4: Testing Strategy

#### 4.1 Unit Tests

**Create `tests/storage/test_session_manager.py`:**

```python
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from tidal_mcp.storage import SecureSessionManager

@pytest.fixture
def temp_storage():
    """Create temporary storage directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def session_manager(temp_storage):
    """Create session manager with temporary storage"""
    return SecureSessionManager(storage_path=temp_storage)

class TestSecureSessionManager:
    """Test cases for secure session manager"""

    def test_save_and_load_session(self, session_manager):
        """Test basic save and load functionality"""
        test_session = {
            'access_token': 'test_token',
            'refresh_token': 'test_refresh',
            'user_id': 'test_user',
            'expires_at': datetime.now().isoformat()
        }

        # Save session
        success = session_manager.save_session(test_session)
        assert success

        # Load session
        loaded_session = session_manager.load_session()
        assert loaded_session is not None
        assert loaded_session['access_token'] == 'test_token'
        assert loaded_session['user_id'] == 'test_user'

    def test_encryption(self, session_manager):
        """Test that session data is encrypted on disk"""
        test_session = {'access_token': 'secret_token'}

        session_manager.save_session(test_session)

        # Read raw file content
        with open(session_manager.session_file, 'rb') as f:
            raw_content = f.read()

        # Should not contain plain text token
        assert b'secret_token' not in raw_content

    def test_device_fingerprint_validation(self, session_manager):
        """Test device fingerprint validation"""
        test_session = {'access_token': 'test_token'}

        # Save session
        session_manager.save_session(test_session)

        # Load should work with same device
        loaded_session = session_manager.load_session()
        assert loaded_session is not None

    def test_backup_creation(self, session_manager):
        """Test backup file creation"""
        # Save initial session
        session_manager.save_session({'token': 'first'})

        # Save another session (should create backup)
        session_manager.save_session({'token': 'second'})

        # Check backup exists
        backup_files = list(session_manager.backup_dir.glob("session_*.enc"))
        assert len(backup_files) >= 1
```

#### 4.2 Integration Tests

**Create `tests/integration/test_storage_integration.py`:**

```python
import pytest
import asyncio
from tidal_mcp.storage import (
    SecureSessionManager, TidalCacheManager,
    RateLimitManager, LimitType
)

@pytest.mark.asyncio
class TestStorageIntegration:
    """Integration tests for storage components"""

    async def test_rate_limit_and_cache_integration(self):
        """Test rate limiting with cache fallback"""
        rate_limiter = RateLimitManager()
        cache_manager = TidalCacheManager()

        user_id = "test_user"

        # First request - should be allowed
        allowed, _ = await rate_limiter.check_limit(
            user_id, LimitType.SEARCH_QUERIES, 1
        )
        assert allowed

        # Cache the result
        await cache_manager.set(
            "search", "tracks", {"query": "test"}, user_id,
            ["track1", "track2"]
        )

        # Exhaust rate limits
        for _ in range(25):  # Exceed limit
            await rate_limiter.check_limit(
                user_id, LimitType.SEARCH_QUERIES, 1
            )

        # Should be rate limited now
        allowed, _ = await rate_limiter.check_limit(
            user_id, LimitType.SEARCH_QUERIES, 1
        )
        assert not allowed

        # But cache should still work
        cached_result = await cache_manager.get(
            "search", "tracks", {"query": "test"}, user_id
        )
        assert cached_result == ["track1", "track2"]
```

### Phase 5: Monitoring & Alerting

#### 5.1 Health Check Endpoint

**Add to `src/tidal_mcp/server.py`:**

```python
async def health_check(self) -> Dict[str, Any]:
    """Comprehensive health check for storage components"""
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "components": {}
    }

    try:
        # Session manager health
        session_health = await self._check_session_health()
        health_status["components"]["session_manager"] = session_health

        # Cache health
        cache_health = await self._check_cache_health()
        health_status["components"]["cache_manager"] = cache_health

        # Rate limiter health
        rate_limit_health = await self._check_rate_limit_health()
        health_status["components"]["rate_limiter"] = rate_limit_health

        # Metrics collector health
        metrics_health = await self._check_metrics_health()
        health_status["components"]["metrics_collector"] = metrics_health

        # Determine overall status
        component_statuses = [comp["status"] for comp in health_status["components"].values()]
        if "critical" in component_statuses:
            health_status["overall_status"] = "critical"
        elif "warning" in component_statuses:
            health_status["overall_status"] = "warning"

    except Exception as e:
        health_status["overall_status"] = "critical"
        health_status["error"] = str(e)

    return health_status

async def _check_session_health(self) -> Dict[str, Any]:
    """Check session manager health"""
    try:
        # Test encryption key access
        session_manager = SecureSessionManager()
        test_session = {"test": "data"}
        success = session_manager.save_session(test_session)

        return {
            "status": "healthy" if success else "warning",
            "encryption_key_accessible": True,
            "backup_directory_writable": session_manager.backup_dir.exists()
        }
    except Exception as e:
        return {
            "status": "critical",
            "error": str(e)
        }
```

#### 5.2 Prometheus Metrics Export

**Create `scripts/export_metrics.py`:**

```python
#!/usr/bin/env python3
"""
Export Tidal MCP metrics in Prometheus format
"""

import asyncio
from tidal_mcp.storage import MetricsCollector

async def export_prometheus_metrics():
    """Export metrics for Prometheus scraping"""
    metrics_collector = MetricsCollector()

    # Export in Prometheus format
    prometheus_data = await metrics_collector.export_prometheus_format()

    # Write to file for Prometheus file discovery
    output_file = "/tmp/tidal_mcp_metrics.prom"
    with open(output_file, 'w') as f:
        f.write(prometheus_data)

    print(f"Metrics exported to: {output_file}")

if __name__ == "__main__":
    asyncio.run(export_prometheus_metrics())
```

### Phase 6: Documentation & Training

#### 6.1 Admin Guide

**Create `docs/admin_guide.md`:**

```markdown
# Tidal MCP Storage Administration Guide

## Overview
This guide covers administration of the Tidal MCP storage infrastructure.

## Daily Operations

### Health Monitoring
```bash
# Check storage health
python -c "from tidal_mcp.server import TidalMCPServer; import asyncio; server = TidalMCPServer(); print(asyncio.run(server.health_check()))"

# View cache metrics
python -c "from tidal_mcp.storage import TidalCacheManager; cache = TidalCacheManager(); print(cache.get_metrics())"
```

### Backup Management
```bash
# Manual backup creation
python scripts/backup_storage.py

# Verify backup integrity
python scripts/verify_backups.py
```

### User Management
```bash
# Export user data (GDPR)
python scripts/export_user_data.py --user-id USER_ID

# Delete user data (GDPR)
python scripts/delete_user_data.py --user-id USER_ID --confirm
```

## Troubleshooting

### Common Issues

1. **Session Encryption Errors**
   - Check key file permissions: `~/.tidal-mcp/session.key`
   - Verify storage directory permissions
   - Review audit logs for encryption failures

2. **Cache Performance Issues**
   - Monitor hit ratios in metrics
   - Check disk space for L2 cache
   - Review cache size limits

3. **Rate Limit Problems**
   - Check violation logs in audit
   - Review rate limit configurations
   - Monitor user activity patterns
```

## Deployment Checklist

### Pre-Deployment
- [ ] Update dependencies in `pyproject.toml`
- [ ] Run migration script: `python scripts/migrate_data.py`
- [ ] Verify configuration: `config/storage_config.yaml`
- [ ] Test health checks
- [ ] Backup existing data

### Deployment
- [ ] Deploy new storage components
- [ ] Enable monitoring
- [ ] Verify metrics collection
- [ ] Test user authentication
- [ ] Validate cache performance

### Post-Deployment
- [ ] Monitor error rates
- [ ] Check storage growth
- [ ] Validate backup creation
- [ ] Review audit logs
- [ ] Performance tuning

## Success Metrics

### Performance Targets
- Session load time: < 50ms
- Cache hit ratio: > 80%
- API response time: < 200ms (cached), < 1s (uncached)
- Storage growth: < 10MB per user per month

### Security Targets
- Zero unencrypted sensitive data at rest
- Rate limit violation rate < 1%
- Audit log coverage: 100% of sensitive operations
- GDPR compliance score: 100%

This comprehensive data architecture provides enterprise-grade storage capabilities for the Tidal MCP server while maintaining simplicity for individual users and ensuring compliance with modern security and privacy requirements.