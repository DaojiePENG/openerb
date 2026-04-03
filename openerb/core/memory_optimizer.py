"""
OpenERB Memory Optimization Module

This module provides memory optimization utilities for the OpenERB system.
"""

import gc
import psutil
import threading
import time
from typing import Dict, List, Any, Optional, Callable
from collections import defaultdict
import weakref
import logging

logger = logging.getLogger(__name__)


class MemoryMonitor:
    """Monitor memory usage and provide alerts."""

    def __init__(self, warning_threshold_mb: float = 200, critical_threshold_mb: float = 300):
        self.warning_threshold = warning_threshold_mb
        self.critical_threshold = critical_threshold_mb
        self.process = psutil.Process()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)

    def start_monitoring(self, interval_seconds: float = 60.0):
        """Start background memory monitoring."""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self._monitor_thread.start()
        logger.info(f"Memory monitoring started (interval: {interval_seconds}s)")

    def stop_monitoring(self):
        """Stop memory monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
        logger.info("Memory monitoring stopped")

    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics."""
        mem_info = self.process.memory_info()
        return {
            "rss": mem_info.rss / 1024 / 1024,  # MB
            "vms": mem_info.vms / 1024 / 1024,  # MB
            "percent": self.process.memory_percent()
        }

    def add_callback(self, event: str, callback: Callable):
        """Add callback for memory events."""
        self._callbacks[event].append(callback)

    def _monitor_loop(self, interval: float):
        """Background monitoring loop."""
        while self._monitoring:
            try:
                usage = self.get_memory_usage()
                rss_mb = usage["rss"]

                if rss_mb >= self.critical_threshold:
                    logger.warning(f"Critical memory usage: {rss_mb:.1f} MB")
                    self._trigger_callbacks("critical", rss_mb)
                elif rss_mb >= self.warning_threshold:
                    logger.warning(f"High memory usage: {rss_mb:.1f} MB")
                    self._trigger_callbacks("warning", rss_mb)

            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")

            time.sleep(interval)

    def _trigger_callbacks(self, event: str, memory_mb: float):
        """Trigger callbacks for memory events."""
        for callback in self._callbacks[event]:
            try:
                callback(memory_mb)
            except Exception as e:
                logger.error(f"Callback error: {e}")


class ObjectPool:
    """Generic object pool for memory reuse."""

    def __init__(self, object_class: type, max_size: int = 100, factory: Optional[Callable] = None):
        self.object_class = object_class
        self.max_size = max_size
        self.factory = factory or object_class
        self._pool: List[Any] = []
        self._lock = threading.Lock()
        self._created_count = 0

    def acquire(self, *args, **kwargs) -> Any:
        """Acquire an object from the pool."""
        with self._lock:
            if self._pool:
                obj = self._pool.pop()
                logger.debug(f"Reused {self.object_class.__name__} from pool")
                return obj
            else:
                self._created_count += 1
                obj = self.factory(*args, **kwargs)
                logger.debug(f"Created new {self.object_class.__name__} (total: {self._created_count})")
                return obj

    def release(self, obj: Any):
        """Return an object to the pool."""
        with self._lock:
            if len(self._pool) < self.max_size:
                # Reset object state if possible
                if hasattr(obj, 'reset'):
                    obj.reset()
                self._pool.append(obj)
                logger.debug(f"Returned {self.object_class.__name__} to pool (size: {len(self._pool)})")
            else:
                # Pool is full, let GC handle it
                logger.debug(f"Pool full, discarding {self.object_class.__name__}")

    def get_stats(self) -> Dict[str, int]:
        """Get pool statistics."""
        with self._lock:
            return {
                "created": self._created_count,
                "available": len(self._pool),
                "max_size": self.max_size
            }


class SkillCache:
    """Cache for skill objects to reduce memory usage."""

    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        self.max_size = max_size
        self.ttl_seconds = ttl_hours * 3600
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = threading.Lock()

    def get(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Get skill from cache."""
        with self._lock:
            if skill_id in self._cache:
                # Check if expired
                if time.time() - self._access_times[skill_id] > self.ttl_seconds:
                    del self._cache[skill_id]
                    del self._access_times[skill_id]
                    return None

                self._access_times[skill_id] = time.time()
                return self._cache[skill_id]
            return None

    def put(self, skill_id: str, skill_data: Dict[str, Any]):
        """Put skill in cache."""
        with self._lock:
            current_time = time.time()

            # Evict old entries if needed
            if len(self._cache) >= self.max_size:
                self._evict_oldest()

            self._cache[skill_id] = skill_data
            self._access_times[skill_id] = current_time

    def invalidate(self, skill_id: str):
        """Remove skill from cache."""
        with self._lock:
            if skill_id in self._cache:
                del self._cache[skill_id]
                del self._access_times[skill_id]

    def clear(self):
        """Clear all cached skills."""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()

    def _evict_oldest(self):
        """Evict least recently used items."""
        if not self._access_times:
            return

        # Find oldest access time
        oldest_id = min(self._access_times.keys(),
                       key=lambda k: self._access_times[k])

        del self._cache[oldest_id]
        del self._access_times[oldest_id]

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hit_rate": 0.0,  # Would need hit/miss counters
                "ttl_hours": self.ttl_seconds / 3600
            }


class GCOptimizer:
    """Garbage collection optimizer."""

    def __init__(self):
        self._gc_thread: Optional[threading.Thread] = None
        self._optimizing = False

    def enable_adaptive_gc(self):
        """Enable adaptive garbage collection."""
        import gc
        gc.set_threshold(700, 10, 10)  # More aggressive collection
        logger.info("Adaptive GC enabled")

    def schedule_gc(self, hour: int = 2):
        """Schedule garbage collection at specific hour."""
        if self._optimizing:
            return

        self._optimizing = True
        self._gc_thread = threading.Thread(
            target=self._gc_scheduler,
            args=(hour,),
            daemon=True
        )
        self._gc_thread.start()
        logger.info(f"GC scheduler started (hour: {hour})")

    def force_gc(self):
        """Force garbage collection immediately."""
        import gc
        collected = gc.collect()
        logger.info(f"GC completed: {collected} objects collected")

    def _gc_scheduler(self, target_hour: int):
        """Background GC scheduler."""
        while self._optimizing:
            current_hour = time.localtime().tm_hour
            if current_hour == target_hour:
                self.force_gc()
                time.sleep(3600)  # Wait an hour before next check
            else:
                time.sleep(300)  # Check every 5 minutes


class MemoryOptimizer:
    """Main memory optimization coordinator."""

    def __init__(self):
        self.monitor = MemoryMonitor()
        self.gc_optimizer = GCOptimizer()
        self.skill_cache = SkillCache()
        self._pools: Dict[str, ObjectPool] = {}
        self._initialized = False

    def initialize(self):
        """Initialize memory optimizations."""
        if self._initialized:
            return

        # Setup memory monitoring with auto-GC
        self.monitor.add_callback("warning", lambda mb: self.gc_optimizer.force_gc())
        self.monitor.add_callback("critical", lambda mb: self._emergency_cleanup())

        # Enable adaptive GC
        self.gc_optimizer.enable_adaptive_gc()

        # Schedule nightly GC
        self.gc_optimizer.schedule_gc(hour=2)

        # Start monitoring
        self.monitor.start_monitoring(interval_seconds=300)  # 5 minutes

        self._initialized = True
        logger.info("Memory optimizer initialized")

    def create_pool(self, name: str, object_class: type, max_size: int = 50) -> ObjectPool:
        """Create an object pool."""
        pool = ObjectPool(object_class, max_size)
        self._pools[name] = pool
        return pool

    def get_pool(self, name: str) -> Optional[ObjectPool]:
        """Get an object pool by name."""
        return self._pools.get(name)

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        stats = self.monitor.get_memory_usage()
        stats.update({
            "pools": {name: pool.get_stats() for name, pool in self._pools.items()},
            "cache": self.skill_cache.get_stats(),
            "gc_enabled": True
        })
        return stats

    def _emergency_cleanup(self, memory_mb: float):
        """Emergency memory cleanup."""
        logger.warning(f"Emergency cleanup triggered at {memory_mb:.1f} MB")

        # Force GC
        self.gc_optimizer.force_gc()

        # Clear caches if needed
        if memory_mb > 400:  # Really critical
            self.skill_cache.clear()
            logger.warning("Skill cache cleared during emergency cleanup")

        # Clear object pools if needed
        for name, pool in self._pools.items():
            pool_stats = pool.get_stats()
            if pool_stats["available"] > pool_stats["max_size"] // 2:
                # Clear half the pool
                with pool._lock:
                    del pool._pool[pool_stats["max_size"] // 4:]
                logger.warning(f"Pool {name} partially cleared")


# Global memory optimizer instance
memory_optimizer = MemoryOptimizer()


def optimize_memory():
    """Convenience function to initialize memory optimizations."""
    memory_optimizer.initialize()
    return memory_optimizer