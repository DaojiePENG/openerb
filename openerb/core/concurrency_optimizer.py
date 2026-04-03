"""
OpenERB Concurrency Optimization Module

This module provides concurrency optimizations for high-throughput processing.
"""

import asyncio
import threading
import time
from typing import Dict, List, Any, Optional, Callable, Awaitable
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import logging
from dataclasses import dataclass
from queue import Queue, Full, Empty
import weakref

logger = logging.getLogger(__name__)


@dataclass
class TaskConfig:
    """Configuration for task execution."""
    max_workers: int = 4
    queue_size: int = 1000
    timeout: float = 30.0
    retry_attempts: int = 2
    priority_levels: int = 3


class PriorityQueue:
    """Priority queue for task scheduling."""

    def __init__(self, maxsize: int = 1000):
        self.queues: List[Queue] = [Queue(maxsize) for _ in range(3)]  # 3 priority levels
        self._lock = threading.Lock()

    def put(self, item: Any, priority: int = 1, block: bool = True, timeout: float = None):
        """Put item in queue with priority."""
        if not 0 <= priority < len(self.queues):
            priority = 1  # Default to medium priority

        try:
            self.queues[priority].put(item, block=block, timeout=timeout)
        except Full:
            logger.warning(f"Priority queue full for priority {priority}")

    def get(self, block: bool = True, timeout: float = None) -> Any:
        """Get highest priority item from queue."""
        with self._lock:
            for queue in self.queues:  # Check highest priority first
                try:
                    return queue.get(block=False)
                except Empty:
                    continue

            # All queues empty
            if block:
                # Wait for any queue to have an item
                while True:
                    for queue in self.queues:
                        try:
                            return queue.get(block=False)
                        except Empty:
                            continue
                    time.sleep(0.01)  # Small sleep to avoid busy waiting
            else:
                raise Empty

    def qsize(self) -> int:
        """Get total size of all queues."""
        return sum(queue.qsize() for queue in self.queues)

    def empty(self) -> bool:
        """Check if all queues are empty."""
        return all(queue.empty() for queue in self.queues)


class AsyncTaskExecutor:
    """Asynchronous task executor with concurrency control."""

    def __init__(self, config: TaskConfig = None):
        self.config = config or TaskConfig()
        self._semaphore = asyncio.Semaphore(self.config.max_workers)
        self._executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._task_counter = 0

    async def execute_task(self, coro: Awaitable, task_id: str = None) -> Any:
        """Execute a coroutine with concurrency control."""
        if task_id is None:
            self._task_counter += 1
            task_id = f"task_{self._task_counter}"

        async with self._semaphore:
            try:
                self._running_tasks[task_id] = asyncio.current_task()
                result = await asyncio.wait_for(coro, timeout=self.config.timeout)
                return result
            except asyncio.TimeoutError:
                logger.error(f"Task {task_id} timed out")
                raise
            except Exception as e:
                logger.error(f"Task {task_id} failed: {e}")
                raise
            finally:
                self._running_tasks.pop(task_id, None)

    async def execute_batch(self, coros: List[Awaitable], max_concurrent: int = None) -> List[Any]:
        """Execute multiple coroutines with controlled concurrency."""
        max_concurrent = max_concurrent or self.config.max_workers

        semaphore = asyncio.Semaphore(max_concurrent)
        results = []

        async def execute_with_semaphore(coro: Awaitable) -> Any:
            async with semaphore:
                return await coro

        tasks = [execute_with_semaphore(coro) for coro in coros]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch task {i} failed: {result}")

        return results

    def get_active_tasks(self) -> List[str]:
        """Get list of active task IDs."""
        return list(self._running_tasks.keys())

    def cancel_task(self, task_id: str):
        """Cancel a running task."""
        task = self._running_tasks.get(task_id)
        if task:
            task.cancel()
            logger.info(f"Cancelled task {task_id}")


class TaskScheduler:
    """Advanced task scheduler with priority and resource management."""

    def __init__(self, config: TaskConfig = None):
        self.config = config or TaskConfig()
        self._priority_queue = PriorityQueue(self.config.queue_size)
        self._executor = AsyncTaskExecutor(self.config)
        self._workers: List[threading.Thread] = []
        self._running = False
        self._stats = {
            "tasks_processed": 0,
            "tasks_failed": 0,
            "avg_processing_time": 0.0
        }

    def start(self):
        """Start the task scheduler."""
        if self._running:
            return

        self._running = True
        for i in range(self.config.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"TaskScheduler-Worker-{i}",
                daemon=True
            )
            worker.start()
            self._workers.append(worker)

        logger.info(f"Task scheduler started with {self.config.max_workers} workers")

    def stop(self):
        """Stop the task scheduler."""
        self._running = False
        for worker in self._workers:
            worker.join(timeout=1.0)
        logger.info("Task scheduler stopped")

    def submit_task(self, func: Callable, args: tuple = None, kwargs: dict = None,
                   priority: int = 1, task_id: str = None) -> str:
        """Submit a task for execution."""
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}

        if task_id is None:
            task_id = f"scheduled_task_{int(time.time() * 1000)}"

        task_data = {
            "func": func,
            "args": args,
            "kwargs": kwargs,
            "task_id": task_id,
            "priority": priority,
            "submitted_at": time.time()
        }

        try:
            self._priority_queue.put(task_data, priority=priority)
            logger.debug(f"Submitted task {task_id} with priority {priority}")
            return task_id
        except Full:
            logger.error(f"Task queue full, failed to submit task {task_id}")
            raise

    async def submit_async_task(self, coro: Awaitable, priority: int = 1, task_id: str = None) -> Any:
        """Submit an async task for execution."""
        return await self._executor.execute_task(coro, task_id)

    def _worker_loop(self):
        """Worker thread main loop."""
        while self._running:
            try:
                task_data = self._priority_queue.get(timeout=1.0)
                self._execute_task(task_data)
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")

    def _execute_task(self, task_data: Dict[str, Any]):
        """Execute a single task."""
        start_time = time.time()

        try:
            func = task_data["func"]
            args = task_data["args"]
            kwargs = task_data["kwargs"]
            task_id = task_data["task_id"]

            result = func(*args, **kwargs)

            processing_time = time.time() - start_time
            self._update_stats(processing_time, success=True)

            logger.debug(f"Task {task_id} completed in {processing_time:.2f}s")

        except Exception as e:
            processing_time = time.time() - start_time
            self._update_stats(processing_time, success=False)
            logger.error(f"Task {task_data['task_id']} failed: {e}")

    def _update_stats(self, processing_time: float, success: bool):
        """Update scheduler statistics."""
        self._stats["tasks_processed"] += 1
        if not success:
            self._stats["tasks_failed"] += 1

        # Update rolling average
        current_avg = self._stats["avg_processing_time"]
        total_tasks = self._stats["tasks_processed"]
        self._stats["avg_processing_time"] = (current_avg * (total_tasks - 1) + processing_time) / total_tasks

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return {
            **self._stats,
            "active_workers": len(self._workers),
            "queue_size": self._priority_queue.qsize(),
            "queue_empty": self._priority_queue.empty()
        }


class ResourceLimiter:
    """Resource usage limiter for system stability."""

    def __init__(self, max_memory_mb: float = 512, max_cpu_percent: float = 80):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self._check_interval = 5.0  # Check every 5 seconds

    def should_throttle(self) -> bool:
        """Check if system should throttle resource usage."""
        try:
            import psutil
            process = psutil.Process()

            # Check memory usage
            memory_mb = process.memory_info().rss / 1024 / 1024
            if memory_mb > self.max_memory_mb:
                return True

            # Check CPU usage (last 1 second)
            cpu_percent = psutil.cpu_percent(interval=1.0)
            if cpu_percent > self.max_cpu_percent:
                return True

            return False

        except ImportError:
            # psutil not available, skip checks
            return False

    async def wait_for_resources(self):
        """Wait until resources are available."""
        while self.should_throttle():
            logger.warning("System resources high, throttling...")
            await asyncio.sleep(self._check_interval)


class ConcurrencyOptimizer:
    """Main concurrency optimization coordinator."""

    def __init__(self):
        self.task_config = TaskConfig()
        self.task_scheduler = TaskScheduler(self.task_config)
        self.async_executor = AsyncTaskExecutor(self.task_config)
        self.resource_limiter = ResourceLimiter()
        self._initialized = False

    def initialize(self):
        """Initialize concurrency optimizations."""
        if self._initialized:
            return

        self.task_scheduler.start()
        self._initialized = True
        logger.info("Concurrency optimizer initialized")

    def shutdown(self):
        """Shutdown concurrency optimizations."""
        if self._initialized:
            self.task_scheduler.stop()
            self._initialized = False
            logger.info("Concurrency optimizer shutdown")

    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        return {
            "scheduler": self.task_scheduler.get_stats(),
            "active_tasks": self.async_executor.get_active_tasks(),
            "resource_throttling": self.resource_limiter.should_throttle()
        }


# Global concurrency optimizer instance
concurrency_optimizer = ConcurrencyOptimizer()


def optimize_concurrency():
    """Convenience function to initialize concurrency optimizations."""
    concurrency_optimizer.initialize()
    return concurrency_optimizer