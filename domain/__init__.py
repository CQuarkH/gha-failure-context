"""
Domain entities for GitHub Actions and Failure Context analysis.
"""

from .github_actions import (
    GHActor,
    GHCommit,
    GHStep,
    GHJob,
    GHRunAttempt,
    GHRun,
    GHWorkflow,
)
from .repository import (
    GHOwner,
    GHFile,
    GHFileTree,
    GHLanguages,
    GHRepository,
    GHContributor,
)
from .failure_context import GHFailureContext

__all__ = [
    # GitHub Actions entities
    "GHActor",
    "GHCommit",
    "GHStep",
    "GHJob",
    "GHRunAttempt",
    "GHRun",
    "GHWorkflow",
    # Repository entities
    "GHOwner",
    "GHFile",
    "GHFileTree",
    "GHLanguages",
    "GHRepository",
    "GHContributor",
    # Aggregate entity
    "GHFailureContext",
]
