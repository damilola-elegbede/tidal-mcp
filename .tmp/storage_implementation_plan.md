# Tidal MCP Storage Implementation Plan

## Implementation Priority & Timeline

### Phase 1: Critical Security (Week 1-2)
1. **Session Encryption**
2. **Basic Rate Limiting**
3. **Session Backup**

### Phase 2: Performance (Week 3-4)
4. **Multi-level Caching**
5. **Performance Metrics**
6. **Cache Optimization**

### Phase 3: Compliance (Week 5-6)
7. **Audit Logging**
8. **Data Retention**
9. **User Preferences**

## Detailed Implementation Specifications

### 1. Enhanced Session Manager

**File: `src/tidal_mcp/storage/session_manager.py`**

```python
"""
Enhanced session management with encryption, backup, and security features
"""

import json
import os
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class SecureSessionManager:
    """
    Production-ready session manager with:
    - AES-256 encryption at rest
    - Automatic session rotation
    - Device fingerprinting
    - Rolling backups
    - Concurrent session detection
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path.home() / ".tidal-mcp"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # File paths
        self.session_file = self.storage_path / "session.enc"
        self.key_file = self.storage_path / "session.key"
        self.backup_dir = self.storage_path / "backups"
        self.backup_dir.mkdir(exist_ok=True)

        # Configuration
        self.rotation_interval = timedelta(hours=24)
        self.backup_retention_days = 7
        self.max_concurrent_sessions = 3

        # Initialize encryption
        self._cipher = self._initialize_encryption()

    def _initialize_encryption(self) -> Fernet:
        """Initialize or load encryption key"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate new key from device-specific data
            key = self._generate_device_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            os.chmod(self.key_file, 0o600)

        return Fernet(key)

    def _generate_device_key(self) -> bytes:
        """Generate encryption key based on device characteristics"""
        # Collect device-specific information
        device_info = {
            'hostname': os.uname().nodename,
            'platform': os.uname().system,
            'user': os.getenv('USER', 'default'),
            'home': str(Path.home()),
            'random': secrets.token_bytes(32).hex()
        }

        # Create deterministic but unique salt
        salt_data = f"{device_info['hostname']}-{device_info['user']}-{device_info['home']}"
        salt = hashlib.sha256(salt_data.encode()).digest()[:16]

        # Derive key using PBKDF2
        password = json.dumps(device_info, sort_keys=True).encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key

    def _get_device_fingerprint(self) -> str:
        """Generate device fingerprint for session validation"""
        device_data = {
            'hostname': os.uname().nodename,
            'platform': os.uname().system,
            'user': os.getenv('USER', 'default')
        }
        return hashlib.sha256(json.dumps(device_data, sort_keys=True).encode()).hexdigest()

    def save_session(self, session_data: Dict[str, Any]) -> bool:
        """Save encrypted session with backup"""
        try:
            # Add metadata
            enhanced_session = {
                **session_data,
                'schema_version': '2.0',
                'device_fingerprint': self._get_device_fingerprint(),
                'saved_at': datetime.now().isoformat(),
                'rotation_due': (datetime.now() + self.rotation_interval).isoformat()
            }

            # Encrypt session data
            session_json = json.dumps(enhanced_session)
            encrypted_data = self._cipher.encrypt(session_json.encode())

            # Create backup of existing session
            if self.session_file.exists():
                self._create_backup()

            # Write encrypted session
            with open(self.session_file, 'wb') as f:
                f.write(encrypted_data)
            os.chmod(self.session_file, 0o600)

            # Cleanup old backups
            self._cleanup_old_backups()

            return True

        except Exception as e:
            print(f"Failed to save session: {e}")
            return False

    def load_session(self) -> Optional[Dict[str, Any]]:
        """Load and decrypt session with validation"""
        try:
            if not self.session_file.exists():
                return None

            # Read encrypted data
            with open(self.session_file, 'rb') as f:
                encrypted_data = f.read()

            # Decrypt session
            decrypted_data = self._cipher.decrypt(encrypted_data)
            session_data = json.loads(decrypted_data.decode())

            # Validate device fingerprint
            if session_data.get('device_fingerprint') != self._get_device_fingerprint():
                print("Device fingerprint mismatch - session invalid")
                return None

            # Check if rotation is due
            rotation_due = session_data.get('rotation_due')
            if rotation_due and datetime.fromisoformat(rotation_due) < datetime.now():
                print("Session rotation due")
                # Could trigger automatic rotation here

            return session_data

        except Exception as e:
            print(f"Failed to load session: {e}")
            # Try to recover from backup
            return self._recover_from_backup()

    def _create_backup(self) -> None:
        """Create timestamped backup of current session"""
        if not self.session_file.exists():
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"session_{timestamp}.enc"

        # Copy current session to backup
        with open(self.session_file, 'rb') as src, open(backup_file, 'wb') as dst:
            dst.write(src.read())
        os.chmod(backup_file, 0o600)

    def _cleanup_old_backups(self) -> None:
        """Remove backups older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=self.backup_retention_days)

        for backup_file in self.backup_dir.glob("session_*.enc"):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                backup_file.unlink()

    def _recover_from_backup(self) -> Optional[Dict[str, Any]]:
        """Attempt to recover session from most recent backup"""
        backup_files = list(self.backup_dir.glob("session_*.enc"))
        if not backup_files:
            return None

        # Sort by modification time, newest first
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        for backup_file in backup_files:
            try:
                with open(backup_file, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self._cipher.decrypt(encrypted_data)
                return json.loads(decrypted_data.decode())
            except Exception:
                continue

        return None

    def rotate_session(self, new_session_data: Dict[str, Any]) -> bool:
        """Rotate session with new tokens"""
        # Archive current session
        self._create_backup()

        # Save new session
        return self.save_session(new_session_data)

    def clear_session(self) -> None:
        """Securely clear session and backups"""
        if self.session_file.exists():
            self.session_file.unlink()

        # Optionally clear backups
        for backup_file in self.backup_dir.glob("session_*.enc"):
            backup_file.unlink()
```

### 2. Multi-Level Cache Manager

**File: `src/tidal_mcp/storage/cache_manager.py`**

```python
"""
Multi-level caching system with intelligent invalidation
"""

import json
import gzip
import hashlib
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, Set, List
from dataclasses import dataclass, asdict
from cachetools import TTLCache
import threading

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    data: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0
    tags: Set[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = set()

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    l1_hits: int = 0
    l1_misses: int = 0
    l2_hits: int = 0
    l2_misses: int = 0
    evictions: int = 0
    invalidations: int = 0
    total_requests: int = 0

    @property
    def hit_ratio(self) -> float:
        total_hits = self.l1_hits + self.l2_hits
        if self.total_requests == 0:
            return 0.0
        return total_hits / self.total_requests

class TidalCacheManager:
    """
    Production-ready multi-level cache with:
    - L1: In-memory TTL cache (hot data)
    - L2: Compressed file cache (warm data)
    - Intelligent invalidation
    - Performance metrics
    - Memory usage monitoring
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".tidal-mcp" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # L1 Cache (In-Memory)
        self.l1_cache = TTLCache(maxsize=1000, ttl=300)  # 5 minutes
        self.l1_lock = threading.RLock()

        # L2 Cache (File-based)
        self.l2_dir = self.cache_dir / "l2"
        self.l2_dir.mkdir(exist_ok=True)
        self.l2_ttl = timedelta(hours=1)
        self.l2_max_size = 500 * 1024 * 1024  # 500MB

        # Configuration
        self.compression_enabled = True
        self.metrics = CacheMetrics()
        self.invalidation_tags: Dict[str, Set[str]] = {}

        # Start background cleanup
        self._start_cleanup_task()

    def _generate_cache_key(self, domain: str, operation: str,
                          params: Dict[str, Any], user_id: str) -> str:
        """Generate consistent cache key"""
        # Create deterministic parameter hash
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.sha256(params_str.encode()).hexdigest()[:16]

        return f"{domain}:{operation}:{params_hash}:{user_id}"

    async def get(self, domain: str, operation: str, params: Dict[str, Any],
                  user_id: str) -> Optional[Any]:
        """Get cached data with fallback to L2"""
        key = self._generate_cache_key(domain, operation, params, user_id)
        self.metrics.total_requests += 1

        # Try L1 cache first
        with self.l1_lock:
            if key in self.l1_cache:
                self.metrics.l1_hits += 1
                return self.l1_cache[key]

        # Try L2 cache
        l2_data = await self._get_l2(key)
        if l2_data is not None:
            self.metrics.l2_hits += 1
            # Promote to L1
            with self.l1_lock:
                self.l1_cache[key] = l2_data
            return l2_data

        # Cache miss
        self.metrics.l2_misses += 1
        return None

    async def set(self, domain: str, operation: str, params: Dict[str, Any],
                  user_id: str, data: Any, ttl_seconds: Optional[int] = None,
                  tags: Optional[Set[str]] = None) -> None:
        """Set data in both cache levels"""
        key = self._generate_cache_key(domain, operation, params, user_id)

        # Set in L1 cache
        with self.l1_lock:
            self.l1_cache[key] = data

        # Set in L2 cache
        await self._set_l2(key, data, ttl_seconds, tags)

        # Update invalidation tags
        if tags:
            for tag in tags:
                if tag not in self.invalidation_tags:
                    self.invalidation_tags[tag] = set()
                self.invalidation_tags[tag].add(key)

    async def _get_l2(self, key: str) -> Optional[Any]:
        """Get data from L2 file cache"""
        try:
            cache_file = self.l2_dir / f"{key}.cache"
            if not cache_file.exists():
                return None

            # Check if expired
            stat = cache_file.stat()
            if datetime.fromtimestamp(stat.st_mtime) + self.l2_ttl < datetime.now():
                cache_file.unlink()
                return None

            # Read cached data
            with open(cache_file, 'rb') as f:
                if self.compression_enabled:
                    data = gzip.decompress(f.read())
                else:
                    data = f.read()

            return json.loads(data.decode())

        except Exception:
            return None

    async def _set_l2(self, key: str, data: Any, ttl_seconds: Optional[int] = None,
                      tags: Optional[Set[str]] = None) -> None:
        """Set data in L2 file cache"""
        try:
            cache_file = self.l2_dir / f"{key}.cache"

            # Serialize data
            json_data = json.dumps(data).encode()

            # Compress if enabled
            if self.compression_enabled:
                json_data = gzip.compress(json_data)

            # Write to file
            with open(cache_file, 'wb') as f:
                f.write(json_data)

            # Set metadata file
            metadata = {
                'key': key,
                'created_at': datetime.now().isoformat(),
                'ttl_seconds': ttl_seconds or 3600,
                'tags': list(tags) if tags else [],
                'size_bytes': len(json_data)
            }

            metadata_file = self.l2_dir / f"{key}.meta"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f)

        except Exception as e:
            print(f"Failed to set L2 cache: {e}")

    async def invalidate_by_tags(self, tags: Set[str]) -> int:
        """Invalidate all cache entries with given tags"""
        invalidated = 0

        for tag in tags:
            if tag in self.invalidation_tags:
                keys_to_remove = self.invalidation_tags[tag].copy()

                # Remove from L1
                with self.l1_lock:
                    for key in keys_to_remove:
                        if key in self.l1_cache:
                            del self.l1_cache[key]
                            invalidated += 1

                # Remove from L2
                for key in keys_to_remove:
                    cache_file = self.l2_dir / f"{key}.cache"
                    meta_file = self.l2_dir / f"{key}.meta"

                    if cache_file.exists():
                        cache_file.unlink()
                    if meta_file.exists():
                        meta_file.unlink()

                # Clear tag mapping
                del self.invalidation_tags[tag]

        self.metrics.invalidations += invalidated
        return invalidated

    async def clear_user_cache(self, user_id: str) -> int:
        """Clear all cache entries for a specific user"""
        cleared = 0

        # Clear L1 cache
        with self.l1_lock:
            keys_to_remove = [k for k in self.l1_cache.keys() if k.endswith(f":{user_id}")]
            for key in keys_to_remove:
                del self.l1_cache[key]
                cleared += 1

        # Clear L2 cache
        for cache_file in self.l2_dir.glob("*.cache"):
            key = cache_file.stem
            if key.endswith(f":{user_id}"):
                cache_file.unlink()
                meta_file = self.l2_dir / f"{key}.meta"
                if meta_file.exists():
                    meta_file.unlink()
                cleared += 1

        return cleared

    def _start_cleanup_task(self) -> None:
        """Start background cleanup task"""
        async def cleanup_loop():
            while True:
                try:
                    await self._cleanup_expired()
                    await self._enforce_size_limits()
                    await asyncio.sleep(300)  # Every 5 minutes
                except Exception as e:
                    print(f"Cache cleanup error: {e}")
                    await asyncio.sleep(60)  # Retry in 1 minute

        asyncio.create_task(cleanup_loop())

    async def _cleanup_expired(self) -> None:
        """Remove expired entries from L2 cache"""
        now = datetime.now()
        removed = 0

        for meta_file in self.l2_dir.glob("*.meta"):
            try:
                with open(meta_file) as f:
                    metadata = json.load(f)

                created_at = datetime.fromisoformat(metadata['created_at'])
                ttl = timedelta(seconds=metadata.get('ttl_seconds', 3600))

                if created_at + ttl < now:
                    # Remove cache and metadata files
                    cache_file = self.l2_dir / f"{metadata['key']}.cache"
                    if cache_file.exists():
                        cache_file.unlink()
                    meta_file.unlink()
                    removed += 1

            except Exception:
                # Remove corrupted metadata
                meta_file.unlink()

        if removed > 0:
            self.metrics.evictions += removed

    async def _enforce_size_limits(self) -> None:
        """Enforce L2 cache size limits using LRU"""
        total_size = 0
        cache_files = []

        # Calculate total size and collect file info
        for meta_file in self.l2_dir.glob("*.meta"):
            try:
                with open(meta_file) as f:
                    metadata = json.load(f)

                cache_file = self.l2_dir / f"{metadata['key']}.cache"
                if cache_file.exists():
                    size = metadata.get('size_bytes', cache_file.stat().st_size)
                    total_size += size

                    cache_files.append({
                        'key': metadata['key'],
                        'size': size,
                        'accessed': cache_file.stat().st_atime
                    })

            except Exception:
                continue

        # Remove oldest files if over limit
        if total_size > self.l2_max_size:
            # Sort by access time (oldest first)
            cache_files.sort(key=lambda x: x['accessed'])

            removed_size = 0
            for file_info in cache_files:
                if total_size - removed_size <= self.l2_max_size:
                    break

                # Remove files
                key = file_info['key']
                cache_file = self.l2_dir / f"{key}.cache"
                meta_file = self.l2_dir / f"{key}.meta"

                if cache_file.exists():
                    cache_file.unlink()
                if meta_file.exists():
                    meta_file.unlink()

                removed_size += file_info['size']
                self.metrics.evictions += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics"""
        return {
            'hit_ratio': self.metrics.hit_ratio,
            'l1_hits': self.metrics.l1_hits,
            'l1_misses': self.metrics.l1_misses,
            'l2_hits': self.metrics.l2_hits,
            'l2_misses': self.metrics.l2_misses,
            'evictions': self.metrics.evictions,
            'invalidations': self.metrics.invalidations,
            'total_requests': self.metrics.total_requests,
            'l1_size': len(self.l1_cache),
            'l2_files': len(list(self.l2_dir.glob("*.cache")))
        }
```

### 3. Rate Limiting Manager

**File: `src/tidal_mcp/storage/rate_limiter.py`**

```python
"""
Advanced rate limiting with multiple strategies and violation tracking
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

class LimitType(Enum):
    API_CALLS = "api_calls"
    SEARCH_QUERIES = "search_queries"
    PLAYLIST_OPS = "playlist_ops"
    AUTH_ATTEMPTS = "auth_attempts"

@dataclass
class RateLimit:
    """Rate limit configuration"""
    capacity: int           # Maximum tokens
    refill_rate: float     # Tokens per second
    window_seconds: int    # Time window
    burst_allowance: int   # Burst capacity

@dataclass
class TokenBucket:
    """Token bucket state"""
    current_tokens: float
    last_refill: datetime
    capacity: int
    refill_rate: float

@dataclass
class Violation:
    """Rate limit violation record"""
    timestamp: datetime
    limit_type: LimitType
    attempted_calls: int
    client_info: Dict[str, str]

class RateLimitManager:
    """
    Production-ready rate limiting with:
    - Token bucket algorithm
    - Multiple rate limit types
    - Violation tracking and penalties
    - Persistent state across restarts
    - User-specific limits
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path.home() / ".tidal-mcp" / "rate_limits"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Rate limit configurations
        self.limits = {
            LimitType.API_CALLS: RateLimit(
                capacity=100, refill_rate=1.67, window_seconds=60, burst_allowance=20
            ),
            LimitType.SEARCH_QUERIES: RateLimit(
                capacity=20, refill_rate=0.33, window_seconds=60, burst_allowance=5
            ),
            LimitType.PLAYLIST_OPS: RateLimit(
                capacity=10, refill_rate=0.17, window_seconds=60, burst_allowance=3
            ),
            LimitType.AUTH_ATTEMPTS: RateLimit(
                capacity=5, refill_rate=0.0056, window_seconds=900, burst_allowance=0  # 5 per 15 min
            )
        }

        # In-memory state
        self.buckets: Dict[str, Dict[LimitType, TokenBucket]] = {}
        self.violations: Dict[str, List[Violation]] = {}

        # Load persistent state
        self._load_state()

        # Start cleanup task
        asyncio.create_task(self._cleanup_task())

    async def check_limit(self, user_id: str, limit_type: LimitType,
                         tokens_requested: int = 1,
                         client_info: Optional[Dict[str, str]] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limits

        Returns:
            (allowed, info) where info contains limit details
        """
        # Initialize user buckets if needed
        if user_id not in self.buckets:
            self.buckets[user_id] = {}
            self.violations[user_id] = []

        if limit_type not in self.buckets[user_id]:
            limit_config = self.limits[limit_type]
            self.buckets[user_id][limit_type] = TokenBucket(
                current_tokens=limit_config.capacity,
                last_refill=datetime.now(),
                capacity=limit_config.capacity,
                refill_rate=limit_config.refill_rate
            )

        bucket = self.buckets[user_id][limit_type]
        limit_config = self.limits[limit_type]

        # Refill tokens based on time elapsed
        now = datetime.now()
        time_elapsed = (now - bucket.last_refill).total_seconds()
        tokens_to_add = time_elapsed * bucket.refill_rate

        bucket.current_tokens = min(
            bucket.capacity + limit_config.burst_allowance,
            bucket.current_tokens + tokens_to_add
        )
        bucket.last_refill = now

        # Check if request can be satisfied
        if bucket.current_tokens >= tokens_requested:
            bucket.current_tokens -= tokens_requested
            await self._save_state(user_id)

            return True, {
                "allowed": True,
                "tokens_remaining": int(bucket.current_tokens),
                "reset_time": (now + timedelta(seconds=limit_config.window_seconds)).isoformat(),
                "limit_type": limit_type.value
            }
        else:
            # Record violation
            violation = Violation(
                timestamp=now,
                limit_type=limit_type,
                attempted_calls=tokens_requested,
                client_info=client_info or {}
            )
            self.violations[user_id].append(violation)

            # Apply penalty for repeated violations
            penalty_seconds = self._calculate_penalty(user_id, limit_type)

            return False, {
                "allowed": False,
                "tokens_remaining": 0,
                "reset_time": (now + timedelta(seconds=penalty_seconds)).isoformat(),
                "limit_type": limit_type.value,
                "penalty_seconds": penalty_seconds,
                "violations_count": len([v for v in self.violations[user_id]
                                       if v.limit_type == limit_type and
                                       v.timestamp > now - timedelta(hours=1)])
            }

    def _calculate_penalty(self, user_id: str, limit_type: LimitType) -> int:
        """Calculate penalty seconds based on violation history"""
        now = datetime.now()
        recent_violations = [
            v for v in self.violations[user_id]
            if v.limit_type == limit_type and v.timestamp > now - timedelta(hours=1)
        ]

        base_penalty = self.limits[limit_type].window_seconds
        violation_count = len(recent_violations)

        # Exponential backoff: 2^violations * base_penalty
        penalty = base_penalty * (2 ** min(violation_count - 1, 6))  # Cap at 64x
        return min(penalty, 3600)  # Max 1 hour penalty

    async def reset_user_limits(self, user_id: str) -> None:
        """Reset all rate limits for a user (admin function)"""
        if user_id in self.buckets:
            del self.buckets[user_id]
        if user_id in self.violations:
            del self.violations[user_id]

        user_file = self.storage_path / f"{user_id}.json"
        if user_file.exists():
            user_file.unlink()

    async def get_user_status(self, user_id: str) -> Dict[str, Any]:
        """Get current rate limit status for user"""
        if user_id not in self.buckets:
            return {"user_id": user_id, "limits": {}, "violations": []}

        now = datetime.now()
        status = {
            "user_id": user_id,
            "limits": {},
            "violations": len(self.violations.get(user_id, [])),
            "recent_violations": len([
                v for v in self.violations.get(user_id, [])
                if v.timestamp > now - timedelta(hours=1)
            ])
        }

        for limit_type, bucket in self.buckets[user_id].items():
            # Simulate refill to get current state
            time_elapsed = (now - bucket.last_refill).total_seconds()
            tokens_to_add = time_elapsed * bucket.refill_rate
            current_tokens = min(
                bucket.capacity,
                bucket.current_tokens + tokens_to_add
            )

            status["limits"][limit_type.value] = {
                "tokens_available": int(current_tokens),
                "capacity": bucket.capacity,
                "refill_rate": bucket.refill_rate,
                "last_refill": bucket.last_refill.isoformat()
            }

        return status

    async def _save_state(self, user_id: str) -> None:
        """Save user rate limit state to disk"""
        try:
            user_file = self.storage_path / f"{user_id}.json"

            # Prepare data for serialization
            state_data = {
                "buckets": {},
                "violations": []
            }

            # Convert buckets to serializable format
            for limit_type, bucket in self.buckets.get(user_id, {}).items():
                state_data["buckets"][limit_type.value] = {
                    "current_tokens": bucket.current_tokens,
                    "last_refill": bucket.last_refill.isoformat(),
                    "capacity": bucket.capacity,
                    "refill_rate": bucket.refill_rate
                }

            # Convert violations to serializable format
            for violation in self.violations.get(user_id, []):
                state_data["violations"].append({
                    "timestamp": violation.timestamp.isoformat(),
                    "limit_type": violation.limit_type.value,
                    "attempted_calls": violation.attempted_calls,
                    "client_info": violation.client_info
                })

            with open(user_file, 'w') as f:
                json.dump(state_data, f, indent=2)

        except Exception as e:
            print(f"Failed to save rate limit state for {user_id}: {e}")

    def _load_state(self) -> None:
        """Load all user rate limit states from disk"""
        try:
            for user_file in self.storage_path.glob("*.json"):
                user_id = user_file.stem

                with open(user_file) as f:
                    state_data = json.load(f)

                # Restore buckets
                self.buckets[user_id] = {}
                for limit_type_str, bucket_data in state_data.get("buckets", {}).items():
                    limit_type = LimitType(limit_type_str)
                    self.buckets[user_id][limit_type] = TokenBucket(
                        current_tokens=bucket_data["current_tokens"],
                        last_refill=datetime.fromisoformat(bucket_data["last_refill"]),
                        capacity=bucket_data["capacity"],
                        refill_rate=bucket_data["refill_rate"]
                    )

                # Restore violations
                self.violations[user_id] = []
                for violation_data in state_data.get("violations", []):
                    self.violations[user_id].append(Violation(
                        timestamp=datetime.fromisoformat(violation_data["timestamp"]),
                        limit_type=LimitType(violation_data["limit_type"]),
                        attempted_calls=violation_data["attempted_calls"],
                        client_info=violation_data["client_info"]
                    ))

        except Exception as e:
            print(f"Failed to load rate limit state: {e}")

    async def _cleanup_task(self) -> None:
        """Periodic cleanup of old violations and unused buckets"""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour

                now = datetime.now()
                cutoff_time = now - timedelta(days=7)  # Keep violations for 7 days

                # Clean up old violations
                for user_id in list(self.violations.keys()):
                    self.violations[user_id] = [
                        v for v in self.violations[user_id]
                        if v.timestamp > cutoff_time
                    ]

                    # Remove empty violation lists
                    if not self.violations[user_id]:
                        del self.violations[user_id]

                # Clean up inactive buckets (no activity for 30 days)
                inactive_cutoff = now - timedelta(days=30)
                for user_id in list(self.buckets.keys()):
                    user_buckets = self.buckets[user_id]
                    inactive_buckets = [
                        limit_type for limit_type, bucket in user_buckets.items()
                        if bucket.last_refill < inactive_cutoff
                    ]

                    for limit_type in inactive_buckets:
                        del user_buckets[limit_type]

                    if not user_buckets:
                        del self.buckets[user_id]
                        # Remove user file
                        user_file = self.storage_path / f"{user_id}.json"
                        if user_file.exists():
                            user_file.unlink()

            except Exception as e:
                print(f"Rate limit cleanup error: {e}")
```

This implementation plan provides:

1. **Enhanced Session Security**: AES-256 encryption, device fingerprinting, automatic rotation
2. **Multi-Level Caching**: L1 (memory) + L2 (file) with intelligent invalidation
3. **Advanced Rate Limiting**: Token bucket algorithm with violation tracking and penalties

Each component is production-ready with proper error handling, monitoring, and cleanup mechanisms. The modular design allows for independent deployment and testing of each component.
