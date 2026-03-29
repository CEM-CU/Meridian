"""Job manager package — exposes shared module-level JobManager instance."""

from api.jobs.manager import JobManager

# Module-level singleton; routes import this to share state.
job_manager: JobManager = JobManager()
