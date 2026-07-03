import threading
import queue
import time
import psutil
from typing import Dict, Any

import logging
logger = logging.getLogger(__name__)

_RESULT_TTL_SECONDS = 3600

class ProcessPool:
    """Intelligent process pool with auto-scaling capabilities"""

    def __init__(self, min_workers=2, max_workers=20, scale_threshold=0.8):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.scale_threshold = scale_threshold
        self.workers = []
        self.task_queue = queue.Queue()
        self.results = {}
        self.pool_lock = threading.Lock()
        self.active_tasks = {}
        self.task_events: Dict[str, threading.Event] = {}
        self.performance_metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "avg_task_time": 0.0,
            "cpu_usage": 0.0,
            "memory_usage": 0.0
        }

        # Initialize minimum workers
        self._scale_up(self.min_workers)

        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_performance, daemon=True)
        self.monitor_thread.start()

    def submit_task(self, task_id: str, func, *args, **kwargs) -> str:
        """Submit a task to the process pool"""
        task = {
            "id": task_id,
            "func": func,
            "args": args,
            "kwargs": kwargs,
            "submitted_at": time.time(),
            "status": "queued"
        }

        with self.pool_lock:
            self.active_tasks[task_id] = task
            self.task_queue.put(task)

        logger.info(f"📋 Task submitted to pool: {task_id}")
        return task_id

    def submit_and_wait(self, task_id: str, func, *args, **kwargs) -> Dict[str, Any]:
        """Submit a task and block until it completes, returning its outcome.

        Unlike ``submit_task``/``get_task_result`` (fire-and-poll, used by the
        async HTTP endpoint), this is for callers that need the pool to gate
        concurrency while still returning a result synchronously — the result
        is removed from ``self.results`` once collected, so it never lingers.
        """
        event = threading.Event()
        with self.pool_lock:
            self.task_events[task_id] = event

        self.submit_task(task_id, func, *args, **kwargs)
        event.wait()

        with self.pool_lock:
            self.task_events.pop(task_id, None)
            outcome = self.results.pop(task_id, None)

        if outcome is None:
            return {"success": False, "error": "process pool task result missing"}
        if outcome["status"] == "failed":
            return {"success": False, "error": outcome["error"]}
        return outcome["result"]

    def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """Get result of a submitted task"""
        with self.pool_lock:
            if task_id in self.results:
                return self.results[task_id]
            elif task_id in self.active_tasks:
                return {"status": self.active_tasks[task_id]["status"], "result": None}
            else:
                return {"status": "not_found", "result": None}

    def _prune_stale_results(self):
        """Drop completed/failed results older than _RESULT_TTL_SECONDS.

        Without this, self.results grows without bound for every task
        submitted via submit_task/get_task_result (the fire-and-poll path) —
        nothing else ever removes an entry once a client stops polling it.
        """
        cutoff = time.time() - _RESULT_TTL_SECONDS
        with self.pool_lock:
            stale = [
                task_id for task_id, outcome in self.results.items()
                if outcome.get("completed_at", outcome.get("failed_at", 0)) < cutoff
            ]
            for task_id in stale:
                del self.results[task_id]

    def _worker_thread(self, worker_id: int):
        """Worker thread that processes tasks"""
        logger.info(f"🔧 Process pool worker {worker_id} started")

        while True:
            try:
                # Get task from queue with timeout
                task = self.task_queue.get(timeout=30)
                if task is None:  # Shutdown signal
                    with self.pool_lock:
                        current = threading.current_thread()
                        if current in self.workers:
                            self.workers.remove(current)
                    break

                task_id = task["id"]
                start_time = time.time()

                # Update task status
                with self.pool_lock:
                    if task_id in self.active_tasks:
                        self.active_tasks[task_id]["status"] = "running"
                        self.active_tasks[task_id]["worker_id"] = worker_id
                        self.active_tasks[task_id]["started_at"] = start_time

                try:
                    # Execute task
                    result = task["func"](*task["args"], **task["kwargs"])

                    # Store result
                    execution_time = time.time() - start_time
                    with self.pool_lock:
                        self.results[task_id] = {
                            "status": "completed",
                            "result": result,
                            "execution_time": execution_time,
                            "worker_id": worker_id,
                            "completed_at": time.time()
                        }

                        # Update performance metrics
                        self.performance_metrics["tasks_completed"] += 1
                        self.performance_metrics["avg_task_time"] = (
                            (self.performance_metrics["avg_task_time"] * (self.performance_metrics["tasks_completed"] - 1) + execution_time) /
                            self.performance_metrics["tasks_completed"]
                        )

                        # Remove from active tasks
                        if task_id in self.active_tasks:
                            del self.active_tasks[task_id]

                        event = self.task_events.get(task_id)

                    if event is not None:
                        event.set()

                    logger.info(f"✅ Task completed: {task_id} in {execution_time:.2f}s")

                except Exception as e:
                    # Handle task failure
                    with self.pool_lock:
                        self.results[task_id] = {
                            "status": "failed",
                            "error": str(e),
                            "execution_time": time.time() - start_time,
                            "worker_id": worker_id,
                            "failed_at": time.time()
                        }

                        self.performance_metrics["tasks_failed"] += 1

                        if task_id in self.active_tasks:
                            del self.active_tasks[task_id]

                        event = self.task_events.get(task_id)

                    if event is not None:
                        event.set()

                    logger.error(f"❌ Task failed: {task_id} - {str(e)}")

                self.task_queue.task_done()

            except queue.Empty:
                # No tasks available, continue waiting
                continue
            except Exception as e:
                logger.error(f"💥 Worker {worker_id} error: {str(e)}")

    def _monitor_performance(self):
        """Monitor pool performance and auto-scale"""
        while True:
            try:
                time.sleep(10)  # Monitor every 10 seconds

                self._prune_stale_results()

                with self.pool_lock:
                    queue_size = self.task_queue.qsize()
                    active_workers = len([w for w in self.workers if w.is_alive()])
                    active_tasks_count = len(self.active_tasks)

                # Calculate load metrics
                if active_workers > 0:
                    load_ratio = (active_tasks_count + queue_size) / active_workers
                else:
                    load_ratio = float('inf')

                # Auto-scaling logic
                if load_ratio > self.scale_threshold and active_workers < self.max_workers:
                    # Scale up
                    new_workers = min(2, self.max_workers - active_workers)
                    self._scale_up(new_workers)
                    logger.info(f"📈 Scaled up process pool: +{new_workers} workers (total: {active_workers + new_workers})")

                elif load_ratio < 0.3 and active_workers > self.min_workers:
                    # Scale down
                    workers_to_remove = min(1, active_workers - self.min_workers)
                    self._scale_down(workers_to_remove)
                    logger.info(f"📉 Scaled down process pool: -{workers_to_remove} workers (total: {active_workers - workers_to_remove})")

                # Update performance metrics
                try:
                    cpu_percent = psutil.cpu_percent()
                    memory_info = psutil.virtual_memory()

                    with self.pool_lock:
                        self.performance_metrics["cpu_usage"] = cpu_percent
                        self.performance_metrics["memory_usage"] = memory_info.percent

                except Exception:
                    pass  # Ignore psutil errors

            except Exception as e:
                logger.error(f"💥 Pool monitor error: {str(e)}")

    def _scale_up(self, count: int):
        """Add workers to the pool"""
        with self.pool_lock:
            for i in range(count):
                worker_id = len(self.workers)
                worker = threading.Thread(target=self._worker_thread, args=(worker_id,), daemon=True)
                worker.start()
                self.workers.append(worker)

    def _scale_down(self, count: int):
        """Remove workers from the pool.

        Sentinels are picked up by whichever idle worker dequeues them first,
        not necessarily the most-recently-started one — so the exiting worker
        removes itself from ``self.workers`` (see ``_worker_thread``) rather
        than this method popping an arbitrary (possibly still-alive) entry.
        """
        with self.pool_lock:
            current = len([w for w in self.workers if w.is_alive()])
            to_remove = max(0, min(count, current - self.min_workers))
            for _ in range(to_remove):
                self.task_queue.put(None)

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get current pool statistics"""
        with self.pool_lock:
            active_workers = len([w for w in self.workers if w.is_alive()])
            return {
                "active_workers": active_workers,
                "queue_size": self.task_queue.qsize(),
                "active_tasks": len(self.active_tasks),
                "performance_metrics": self.performance_metrics.copy(),
                "min_workers": self.min_workers,
                "max_workers": self.max_workers
            }
