"""
GitHub Actions domain entities.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class GHActor:
    """Represents a GitHub user or bot that triggered an event."""

    login: str
    id: int
    node_id: str
    type: str
    avatar_url: Optional[str] = None
    url: Optional[str] = None
    html_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "login": self.login,
            "id": self.id,
            "node_id": self.node_id,
            "type": self.type,
            "avatar_url": self.avatar_url,
            "url": self.url,
            "html_url": self.html_url,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GHActor":
        """Deserialize from dictionary."""
        return cls(
            login=data["login"],
            id=data["id"],
            node_id=data["node_id"],
            type=data["type"],
            avatar_url=data.get("avatar_url"),
            url=data.get("url"),
            html_url=data.get("html_url"),
        )


@dataclass
class GHCommit:
    """Represents a git commit snapshot."""

    id: str  # SHA hash
    message: str
    timestamp: str
    author_name: str
    author_email: str
    tree_id: str
    committer_name: Optional[str] = None
    committer_email: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "message": self.message,
            "timestamp": self.timestamp,
            "author_name": self.author_name,
            "author_email": self.author_email,
            "tree_id": self.tree_id,
            "committer_name": self.committer_name,
            "committer_email": self.committer_email,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GHCommit":
        """Deserialize from dictionary."""
        # Handle nested structure from GitHub API
        if "author" in data and isinstance(data["author"], dict):
            author_name = data["author"].get("name", "")
            author_email = data["author"].get("email", "")
        else:
            author_name = data.get("author_name", "")
            author_email = data.get("author_email", "")

        if "committer" in data and isinstance(data["committer"], dict):
            committer_name = data["committer"].get("name")
            committer_email = data["committer"].get("email")
        else:
            committer_name = data.get("committer_name")
            committer_email = data.get("committer_email")

        return cls(
            id=data["id"],
            message=data["message"],
            timestamp=data["timestamp"],
            author_name=author_name,
            author_email=author_email,
            tree_id=data["tree_id"],
            committer_name=committer_name,
            committer_email=committer_email,
        )


@dataclass
class GHStep:
    """Represents an atomic unit of work within a Job."""

    name: str
    number: int
    status: str
    conclusion: Optional[str]
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    log_file_path: Optional[str] = None
    log_content: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "number": self.number,
            "status": self.status,
            "conclusion": self.conclusion,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "log_file_path": self.log_file_path,
            "log_content": self.log_content,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GHStep":
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            number=data["number"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            log_file_path=data.get("log_file_path"),
            log_content=data.get("log_content"),
        )


@dataclass
class GHJob:
    """Represents a set of steps executed on the same runner."""

    id: int
    name: str
    node_id: str
    run_attempt: int
    status: str
    conclusion: Optional[str]
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: Optional[str] = None
    url: Optional[str] = None
    html_url: Optional[str] = None
    runner_name: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    full_log_path: Optional[str] = None
    steps: List[GHStep] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "node_id": self.node_id,
            "run_attempt": self.run_attempt,
            "status": self.status,
            "conclusion": self.conclusion,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "created_at": self.created_at,
            "url": self.url,
            "html_url": self.html_url,
            "runner_name": self.runner_name,
            "labels": self.labels,
            "dependencies": self.dependencies,
            "full_log_path": self.full_log_path,
            "steps": [step.to_dict() for step in self.steps],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GHJob":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            node_id=data["node_id"],
            run_attempt=data["run_attempt"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            created_at=data.get("created_at"),
            url=data.get("url"),
            html_url=data.get("html_url"),
            runner_name=data.get("runner_name"),
            labels=data.get("labels", []),
            dependencies=data.get("dependencies", []),
            full_log_path=data.get("full_log_path"),
            steps=[GHStep.from_dict(step) for step in data.get("steps", [])],
        )


@dataclass
class GHRunAttempt:
    """Represents a specific attempt to complete a Run."""

    run_attempt: int
    status: str
    conclusion: Optional[str]
    started_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_at: Optional[str] = None
    jobs: List[GHJob] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "run_attempt": self.run_attempt,
            "status": self.status,
            "conclusion": self.conclusion,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "created_at": self.created_at,
            "jobs": [job.to_dict() for job in self.jobs],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GHRunAttempt":
        """Deserialize from dictionary."""
        return cls(
            run_attempt=data["run_attempt"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            started_at=data.get("started_at") or data.get("run_started_at"),
            updated_at=data.get("updated_at"),
            created_at=data.get("created_at"),
            jobs=[GHJob.from_dict(job) for job in data.get("jobs", [])],
        )


@dataclass
class GHWorkflow:
    """Represents the definition of an automated workflow."""

    id: int
    node_id: str
    path: str
    name: Optional[str] = None
    state: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    url: Optional[str] = None
    html_url: Optional[str] = None
    badge_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "node_id": self.node_id,
            "path": self.path,
            "name": self.name,
            "state": self.state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "url": self.url,
            "html_url": self.html_url,
            "badge_url": self.badge_url,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GHWorkflow":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            node_id=data["node_id"],
            path=data["path"],
            name=data.get("name"),
            state=data.get("state"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            url=data.get("url"),
            html_url=data.get("html_url"),
            badge_url=data.get("badge_url"),
        )


@dataclass
class GHRun:
    """Represents an instantiated execution of a Workflow."""

    id: int
    node_id: str
    run_number: int
    workflow_id: int
    status: str
    conclusion: Optional[str]
    name: Optional[str] = None
    display_title: Optional[str] = None
    event: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    run_started_at: Optional[str] = None
    url: Optional[str] = None
    html_url: Optional[str] = None
    check_suite_id: Optional[int] = None
    workflow: Optional[GHWorkflow] = None
    actor: Optional[GHActor] = None
    triggering_actor: Optional[GHActor] = None
    commit: Optional[GHCommit] = None
    attempts: List[GHRunAttempt] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "node_id": self.node_id,
            "run_number": self.run_number,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "conclusion": self.conclusion,
            "name": self.name,
            "display_title": self.display_title,
            "event": self.event,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "run_started_at": self.run_started_at,
            "url": self.url,
            "html_url": self.html_url,
            "check_suite_id": self.check_suite_id,
            "workflow": self.workflow.to_dict() if self.workflow else None,
            "actor": self.actor.to_dict() if self.actor else None,
            "triggering_actor": self.triggering_actor.to_dict() if self.triggering_actor else None,
            "commit": self.commit.to_dict() if self.commit else None,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GHRun":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            node_id=data["node_id"],
            run_number=data["run_number"],
            workflow_id=data["workflow_id"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            name=data.get("name"),
            display_title=data.get("display_title"),
            event=data.get("event"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            run_started_at=data.get("run_started_at"),
            url=data.get("url"),
            html_url=data.get("html_url"),
            check_suite_id=data.get("check_suite_id"),
            workflow=GHWorkflow.from_dict(data["workflow"]) if data.get("workflow") else None,
            actor=GHActor.from_dict(data["actor"]) if data.get("actor") else None,
            triggering_actor=GHActor.from_dict(data["triggering_actor"]) if data.get("triggering_actor") else None,
            commit=GHCommit.from_dict(data["head_commit"]) if data.get("head_commit") else None,
            attempts=[GHRunAttempt.from_dict(attempt) for attempt in data.get("run_attempts", [])],
        )
