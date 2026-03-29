"""Tests for JobManager and related job models."""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from api.jobs.manager import JobManager
from api.jobs.models import CandidateInput, JobCreate, JobInfo, JobStatus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(*, candidates: int = 2, scenario: str = "GROWTH_OPERATOR") -> JobCreate:
    """Build a minimal JobCreate fixture."""
    return JobCreate(
        jd_text="Chief Technology Officer required.",
        candidates=[
            CandidateInput(name=f"Candidate {i}", cv_text=f"CV text for candidate {i}") for i in range(candidates)
        ],
        scenario=scenario,
    )


# ---------------------------------------------------------------------------
# create_job
# ---------------------------------------------------------------------------


async def test_create_job_returns_valid_uuid() -> None:
    """create_job should return a well-formed UUID4 string."""
    manager = JobManager()
    request = _make_request()
    job_id = await manager.create_job(request)

    # Must be parseable as UUID
    parsed = uuid.UUID(job_id, version=4)
    assert str(parsed) == job_id


async def test_create_job_stores_job_with_queued_status() -> None:
    """Newly created jobs should have QUEUED status."""
    manager = JobManager()
    request = _make_request(candidates=3, scenario="CAPITAL_ALLOCATOR")
    job_id = await manager.create_job(request)

    job = await manager.get_job(job_id)
    assert job is not None
    assert job.status == JobStatus.QUEUED
    assert job.scenario == "CAPITAL_ALLOCATOR"
    assert job.candidate_count == 3


# ---------------------------------------------------------------------------
# get_job
# ---------------------------------------------------------------------------


async def test_get_job_returns_correct_info() -> None:
    """get_job should return the JobInfo stored during create_job."""
    manager = JobManager()
    request = _make_request(scenario="STEADY_OPERATOR")
    job_id = await manager.create_job(request)

    job = await manager.get_job(job_id)
    assert isinstance(job, JobInfo)
    assert job.job_id == job_id
    assert job.scenario == "STEADY_OPERATOR"
    assert job.candidate_count == 2


async def test_get_nonexistent_job_returns_none() -> None:
    """get_job should return None for an unknown job_id."""
    manager = JobManager()
    result = await manager.get_job("00000000-0000-4000-8000-000000000000")
    assert result is None


# ---------------------------------------------------------------------------
# update_status
# ---------------------------------------------------------------------------


async def test_update_status_changes_state() -> None:
    """update_status should transition a job from QUEUED to the target state."""
    manager = JobManager()
    job_id = await manager.create_job(_make_request())

    await manager.update_status(job_id, JobStatus.RUNNING)
    job = await manager.get_job(job_id)
    assert job is not None
    assert job.status == JobStatus.RUNNING


async def test_update_status_stores_error_message() -> None:
    """update_status should persist the error string on FAILED transitions."""
    manager = JobManager()
    job_id = await manager.create_job(_make_request())

    await manager.update_status(job_id, JobStatus.FAILED, error="LLM timeout")
    job = await manager.get_job(job_id)
    assert job is not None
    assert job.status == JobStatus.FAILED
    assert job.error == "LLM timeout"


async def test_update_status_unknown_job_does_not_raise() -> None:
    """update_status on a missing job_id should be a no-op, not an exception."""
    manager = JobManager()
    # Should not raise
    await manager.update_status("nonexistent-id", JobStatus.COMPLETED)


# ---------------------------------------------------------------------------
# store_result / get_result
# ---------------------------------------------------------------------------


async def test_store_and_get_result_round_trip() -> None:
    """Results stored via store_result must be returned unchanged by get_result."""
    manager = JobManager()
    job_id = await manager.create_job(_make_request())
    payload = {"verdict": "hire", "score": 0.92}

    await manager.store_result(job_id, payload)
    retrieved = await manager.get_result(job_id)

    assert retrieved == payload


async def test_get_result_returns_none_for_unknown_job() -> None:
    """get_result should return None when no result has been stored."""
    manager = JobManager()
    assert await manager.get_result("does-not-exist") is None


# ---------------------------------------------------------------------------
# store_cached_state / get_cached_state
# ---------------------------------------------------------------------------


async def test_store_and_get_cached_state_round_trip() -> None:
    """Cached states stored via store_cached_state must round-trip through get_cached_state."""
    manager = JobManager()
    job_id = await manager.create_job(_make_request())
    state = {"stage_c_output": {"requirements": []}, "stage_d_output": {"flags": []}}

    await manager.store_cached_state(job_id, state)
    retrieved = await manager.get_cached_state(job_id)

    assert retrieved == state


async def test_get_cached_state_returns_none_for_unknown_job() -> None:
    """get_cached_state should return None when nothing has been stored."""
    manager = JobManager()
    assert await manager.get_cached_state("does-not-exist") is None


# ---------------------------------------------------------------------------
# cleanup_expired
# ---------------------------------------------------------------------------


async def test_cleanup_expired_removes_old_jobs() -> None:
    """Jobs older than TTL should be removed after cleanup_expired."""
    manager = JobManager(ttl_seconds=60)
    job_id = await manager.create_job(_make_request())

    # Back-date the creation timestamp so it appears expired
    manager._created_at_raw[job_id] = datetime.now(UTC) - timedelta(seconds=120)

    await manager.cleanup_expired()

    assert await manager.get_job(job_id) is None
    assert await manager.get_result(job_id) is None
    assert await manager.get_cached_state(job_id) is None


async def test_cleanup_expired_preserves_fresh_jobs() -> None:
    """Jobs younger than TTL must survive cleanup_expired."""
    manager = JobManager(ttl_seconds=3600)
    job_id = await manager.create_job(_make_request())

    await manager.cleanup_expired()

    job = await manager.get_job(job_id)
    assert job is not None


async def test_cleanup_expired_also_removes_associated_result_and_state() -> None:
    """Results and cached states must be purged alongside the expired job."""
    manager = JobManager(ttl_seconds=60)
    job_id = await manager.create_job(_make_request())
    await manager.store_result(job_id, {"score": 1.0})
    await manager.store_cached_state(job_id, {"flags": []})

    manager._created_at_raw[job_id] = datetime.now(UTC) - timedelta(seconds=120)
    await manager.cleanup_expired()

    assert await manager.get_result(job_id) is None
    assert await manager.get_cached_state(job_id) is None


# ---------------------------------------------------------------------------
# Semaphore / concurrency limiting
# ---------------------------------------------------------------------------


async def test_semaphore_limits_concurrency() -> None:
    """Only max_concurrent jobs should run simultaneously; the 4th must wait."""
    manager = JobManager(max_concurrent=3)
    started: list[int] = []
    finished: list[int] = []
    gate = asyncio.Event()

    async def _worker(idx: int) -> None:
        async with manager.acquire_slot():
            started.append(idx)
            await gate.wait()
            finished.append(idx)

    tasks = [asyncio.create_task(_worker(i)) for i in range(4)]

    # Give the first 3 tasks time to acquire the semaphore and reach gate.wait()
    await asyncio.sleep(0.05)

    # Exactly 3 should have started; the 4th is still blocked on the semaphore
    assert len(started) == 3, f"Expected 3 started, got {started}"
    assert len(finished) == 0

    # Release the gate — all workers finish
    gate.set()
    await asyncio.gather(*tasks)

    assert len(finished) == 4


async def test_acquire_slot_returns_semaphore_context_manager() -> None:
    """acquire_slot must be usable as an async context manager."""
    manager = JobManager(max_concurrent=2)
    async with manager.acquire_slot():
        pass  # must not raise
