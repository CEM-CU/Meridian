"""In-memory job queue and result store.

Jobs are stored in a dict with TTL-based expiry. Thread-safe via asyncio locks.
No Redis needed for demo/MVP.
"""

import asyncio
import uuid
from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime, timedelta
from typing import Any

from meridian.api.jobs.models import JobCreate, JobInfo, JobStatus


class JobManager:
    """Manages evaluation job lifecycle with in-memory storage and concurrency control."""

    def __init__(self, max_concurrent: int = 3, ttl_seconds: int = 3600) -> None:
        """Initialise the job manager.

        Args:
            max_concurrent: Maximum number of jobs running simultaneously.
            ttl_seconds: Seconds after creation before a job is eligible for expiry.
        """
        self._jobs: dict[str, JobInfo] = {}
        self._results: dict[str, Any] = {}  # job_id → SynthesisOutput or ScenarioResult
        self._cached_states: dict[str, Any] = {}  # job_id → CachedPipelineState
        self._created_at_raw: dict[str, datetime] = {}  # job_id → datetime for TTL checks
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._lock = asyncio.Lock()
        self._ttl = ttl_seconds

    async def create_job(self, request: JobCreate) -> str:
        """Create a new job and return its job_id (UUID4).

        Args:
            request: Validated job creation payload.

        Returns:
            A UUID4 string identifying the new job.
        """
        job_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        job = JobInfo(
            job_id=job_id,
            status=JobStatus.QUEUED,
            created_at=now.isoformat(),
            scenario=request.scenario,
            candidate_count=len(request.candidates),
        )
        async with self._lock:
            self._jobs[job_id] = job
            self._created_at_raw[job_id] = now
        return job_id

    async def get_job(self, job_id: str) -> JobInfo | None:
        """Return job info for *job_id*, or None if not found.

        Args:
            job_id: UUID string of the target job.

        Returns:
            JobInfo instance or None.
        """
        async with self._lock:
            return self._jobs.get(job_id)

    async def update_status(self, job_id: str, status: JobStatus, error: str | None = None) -> None:
        """Update the status (and optional error) of an existing job.

        Args:
            job_id: UUID string of the target job.
            status: New JobStatus value.
            error: Optional error message to attach.
        """
        async with self._lock:
            existing = self._jobs.get(job_id)
            if existing is None:
                return
            self._jobs[job_id] = existing.model_copy(update={"status": status, "error": error})

    async def store_result(self, job_id: str, result: Any) -> None:
        """Persist the evaluation result for a completed job.

        Args:
            job_id: UUID string of the target job.
            result: SynthesisOutput or ScenarioResult object.
        """
        async with self._lock:
            self._results[job_id] = result

    async def get_result(self, job_id: str) -> Any | None:
        """Retrieve the stored result for *job_id*.

        Args:
            job_id: UUID string of the target job.

        Returns:
            The stored result or None.
        """
        async with self._lock:
            return self._results.get(job_id)

    async def store_cached_state(self, job_id: str, state: Any) -> None:
        """Store an intermediate pipeline state to support scenario switching.

        Args:
            job_id: UUID string of the target job.
            state: CachedPipelineState object.
        """
        async with self._lock:
            self._cached_states[job_id] = state

    async def get_cached_state(self, job_id: str) -> Any | None:
        """Retrieve the cached pipeline state for *job_id*.

        Args:
            job_id: UUID string of the target job.

        Returns:
            The cached state or None.
        """
        async with self._lock:
            return self._cached_states.get(job_id)

    async def cleanup_expired(self) -> None:
        """Remove all jobs (and associated data) whose age exceeds the TTL.

        Marks jobs as EXPIRED before removal so callers that hold a reference
        see the terminal state.
        """
        cutoff = datetime.now(UTC) - timedelta(seconds=self._ttl)
        async with self._lock:
            expired_ids = [job_id for job_id, created_at in self._created_at_raw.items() if created_at < cutoff]
            for job_id in expired_ids:
                existing = self._jobs.get(job_id)
                if existing is not None:
                    self._jobs[job_id] = existing.model_copy(update={"status": JobStatus.EXPIRED})
                del self._jobs[job_id]
                del self._created_at_raw[job_id]
                self._results.pop(job_id, None)
                self._cached_states.pop(job_id, None)

    def acquire_slot(self) -> AbstractAsyncContextManager[None]:
        """Return an async context manager that limits concurrent job execution.

        Usage::

            async with job_manager.acquire_slot():
                await run_pipeline(...)

        Returns:
            The internal asyncio.Semaphore (which is an async context manager).
        """
        return self._semaphore
