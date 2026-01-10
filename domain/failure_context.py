"""
Failure Context aggregate entity for error analysis.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from .github_actions import GHRun, GHRunAttempt, GHJob, GHStep, GHWorkflow, GHCommit, GHActor
from .repository import GHRepository


@dataclass
class GHFailureContext:
    """
    Aggregate entity that encapsulates all contextual information necessary
    for analyzing a failure in GitHub Actions.

    This entity links the execution hierarchy with the responsible code,
    enabling understanding of not only what failed, but where, when, and who
    made the associated change.
    """

    # Execution context
    run: GHRun
    attempt: GHRunAttempt
    job: GHJob
    failed_step: Optional[GHStep] = None

    # Code context
    commit: Optional[GHCommit] = None
    repository: Optional[GHRepository] = None

    # Additional metadata
    workflow: Optional[GHWorkflow] = None
    actor: Optional[GHActor] = None
    full_log_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "run": self.run.to_dict(),
            "attempt": self.attempt.to_dict(),
            "job": self.job.to_dict(),
            "failed_step": self.failed_step.to_dict() if self.failed_step else None,
            "commit": self.commit.to_dict() if self.commit else None,
            "repository": self.repository.to_dict() if self.repository else None,
            "workflow": self.workflow.to_dict() if self.workflow else None,
            "actor": self.actor.to_dict() if self.actor else None,
            "full_log_path": self.full_log_path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GHFailureContext":
        """Deserialize from dictionary."""
        return cls(
            run=GHRun.from_dict(data["run"]),
            attempt=GHRunAttempt.from_dict(data["attempt"]),
            job=GHJob.from_dict(data["job"]),
            failed_step=GHStep.from_dict(data["failed_step"]) if data.get("failed_step") else None,
            commit=GHCommit.from_dict(data["commit"]) if data.get("commit") else None,
            repository=GHRepository.from_dict(data["repository"]) if data.get("repository") else None,
            workflow=GHWorkflow.from_dict(data["workflow"]) if data.get("workflow") else None,
            actor=GHActor.from_dict(data["actor"]) if data.get("actor") else None,
            full_log_path=data.get("full_log_path"),
        )

    def get_failure_summary(self) -> str:
        """Generate a human-readable summary of the failure."""
        summary_parts = []

        if self.workflow:
            summary_parts.append(f"Workflow: {self.workflow.name} ({self.workflow.path})")

        summary_parts.append(f"Run: #{self.run.run_number} (ID: {self.run.id})")
        summary_parts.append(f"Job: {self.job.name} - {self.job.conclusion}")

        if self.failed_step:
            summary_parts.append(f"Failed Step: {self.failed_step.name} (#{self.failed_step.number})")

        if self.commit:
            summary_parts.append(f"Commit: {self.commit.id[:7]} - {self.commit.message[:50]}...")

        if self.actor:
            summary_parts.append(f"Triggered by: {self.actor.login}")

        if self.repository:
            summary_parts.append(f"Repository: {self.repository.full_name}")
            if self.repository.languages:
                summary_parts.append(f"Primary Language: {self.repository.languages.primary_language}")

        return "\n".join(summary_parts)

    def get_log_path(self) -> Optional[str]:
        """Get the path to the log file for the failed step."""
        if self.failed_step and self.failed_step.log_file_path:
            return self.failed_step.log_file_path
        return self.job.full_log_path if self.job else None

    @property
    def is_failure(self) -> bool:
        """Check if this context represents a failure."""
        return (
            self.job.conclusion == "failure" or
            self.attempt.conclusion == "failure" or
            self.run.conclusion == "failure"
        )

    @property
    def repository_name(self) -> str:
        """Get the repository name."""
        if self.repository:
            return self.repository.full_name
        return "unknown"

    @property
    def run_identifier(self) -> str:
        """Get a unique identifier for this run."""
        return f"run_{self.run.id}_number_{self.run.run_number}_{self.job.name.replace(' ', '_')}"
