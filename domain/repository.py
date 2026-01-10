"""
GitHub Repository domain entities.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class GHOwner:
    """Represents the owner of a repository (User or Organization)."""

    login: str
    type: str
    id: Optional[int] = None
    node_id: Optional[str] = None
    avatar_url: Optional[str] = None
    url: Optional[str] = None
    html_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "login": self.login,
            "type": self.type,
            "id": self.id,
            "node_id": self.node_id,
            "avatar_url": self.avatar_url,
            "url": self.url,
            "html_url": self.html_url,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GHOwner":
        """Deserialize from dictionary."""
        return cls(
            login=data["login"],
            type=data["type"],
            id=data.get("id"),
            node_id=data.get("node_id"),
            avatar_url=data.get("avatar_url"),
            url=data.get("url"),
            html_url=data.get("html_url"),
        )


@dataclass
class GHLanguages:
    """Represents the technological composition of a repository."""

    primary_language: str
    languages: Dict[str, int] = field(default_factory=dict)  # language -> bytes
    percentages: Dict[str, float] = field(default_factory=dict)  # language -> percentage

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "primary_language": self.primary_language,
            "languages": self.languages,
            "percentages": self.percentages,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GHLanguages":
        """Deserialize from dictionary."""
        return cls(
            primary_language=data["primary_language"],
            languages=data.get("languages", {}),
            percentages=data.get("percentages", {}),
        )


@dataclass
class GHFile:
    """Represents a file in the repository tree."""

    path: str
    type: str  # blob or tree
    sha: str
    size: Optional[int] = None
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "path": self.path,
            "type": self.type,
            "sha": self.sha,
            "size": self.size,
            "url": self.url,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GHFile":
        """Deserialize from dictionary."""
        return cls(
            path=data["path"],
            type=data["type"],
            sha=data["sha"],
            size=data.get("size"),
            url=data.get("url"),
        )


@dataclass
class GHFileTree:
    """Represents the hierarchical structure of repository contents."""

    sha: str
    url: Optional[str] = None
    files: List[GHFile] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "sha": self.sha,
            "url": self.url,
            "files": [file.to_dict() for file in self.files],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GHFileTree":
        """Deserialize from dictionary."""
        # Handle nested structure with 'tree' key
        if "tree" in data and isinstance(data["tree"], dict):
            files_data = data["tree"].get("files", [])
        else:
            files_data = data.get("files", [])

        return cls(
            sha=data["sha"],
            url=data.get("url"),
            files=[GHFile.from_dict(file) for file in files_data],
        )


@dataclass
class GHContributor:
    """Represents a contributor to the repository."""

    login: str
    contributions: int
    type: str = "User"  # User or Bot, defaults to User
    id: Optional[int] = None
    url: Optional[str] = None
    html_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "login": self.login,
            "contributions": self.contributions,
            "type": self.type,
            "id": self.id,
            "url": self.url,
            "html_url": self.html_url,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GHContributor":
        """Deserialize from dictionary."""
        return cls(
            login=data["login"],
            contributions=data["contributions"],
            type=data.get("type", "User"),
            id=data.get("id"),
            url=data.get("url"),
            html_url=data.get("html_url"),
        )


@dataclass
class GHRepository:
    """
    Represents a GitHub repository with its metadata, structure, and statistics.
    Acts as an aggregate containing all repository-related information.
    """

    full_name: str
    name: str
    owner: GHOwner
    default_branch: str
    description: Optional[str] = None
    id: Optional[int] = None
    node_id: Optional[str] = None

    # Visibility flags
    is_private: bool = False
    is_fork: bool = False
    is_archived: bool = False

    # Timestamps
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    pushed_at: Optional[str] = None

    # Statistics
    size: Optional[int] = None  # Size in KB
    stargazers_count: Optional[int] = None
    forks_count: Optional[int] = None
    open_issues_count: Optional[int] = None
    watchers_count: Optional[int] = None

    # URLs
    html_url: Optional[str] = None
    clone_url: Optional[str] = None
    url: Optional[str] = None

    # Additional metadata
    license: Optional[str] = None
    homepage: Optional[str] = None
    topics: List[str] = field(default_factory=list)

    # Language and file structure
    languages: Optional[GHLanguages] = None
    file_tree: Optional[GHFileTree] = None
    contributors: List[GHContributor] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "full_name": self.full_name,
            "name": self.name,
            "owner": self.owner.to_dict(),
            "default_branch": self.default_branch,
            "description": self.description,
            "id": self.id,
            "node_id": self.node_id,
            "is_private": self.is_private,
            "is_fork": self.is_fork,
            "is_archived": self.is_archived,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "pushed_at": self.pushed_at,
            "size": self.size,
            "stargazers_count": self.stargazers_count,
            "forks_count": self.forks_count,
            "open_issues_count": self.open_issues_count,
            "watchers_count": self.watchers_count,
            "html_url": self.html_url,
            "clone_url": self.clone_url,
            "url": self.url,
            "license": self.license,
            "homepage": self.homepage,
            "topics": self.topics,
            "languages": self.languages.to_dict() if self.languages else None,
            "file_tree": self.file_tree.to_dict() if self.file_tree else None,
            "contributors": [contrib.to_dict() for contrib in self.contributors],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GHRepository":
        """Deserialize from dictionary."""
        # Handle the 'repository' wrapper if present
        repo_data = data.get("repository", data)

        # Parse contributors - handle nested structure
        contributors = []
        contributors_data = data.get("contributors", [])
        if isinstance(contributors_data, dict):
            # Handle nested structure with 'top_contributors'
            contributors_list = contributors_data.get("top_contributors", [])
        elif isinstance(contributors_data, list):
            contributors_list = contributors_data
        else:
            contributors_list = []

        try:
            contributors = [GHContributor.from_dict(c) for c in contributors_list]
        except Exception:
            # If contributors fail to parse, just use empty list
            contributors = []

        return cls(
            full_name=repo_data["full_name"],
            name=repo_data["name"],
            owner=GHOwner.from_dict(repo_data["owner"]),
            default_branch=repo_data["default_branch"],
            description=repo_data.get("description"),
            id=repo_data.get("id"),
            node_id=repo_data.get("node_id"),
            is_private=repo_data.get("private", repo_data.get("is_private", False)),
            is_fork=repo_data.get("fork", repo_data.get("is_fork", False)),
            is_archived=repo_data.get("archived", repo_data.get("is_archived", False)),
            created_at=repo_data.get("created_at"),
            updated_at=repo_data.get("updated_at"),
            pushed_at=repo_data.get("pushed_at"),
            size=repo_data.get("size"),
            stargazers_count=repo_data.get("stargazers_count"),
            forks_count=repo_data.get("forks_count"),
            open_issues_count=repo_data.get("open_issues_count"),
            watchers_count=repo_data.get("watchers_count"),
            html_url=repo_data.get("html_url"),
            clone_url=repo_data.get("clone_url"),
            url=repo_data.get("url"),
            license=repo_data.get("license", {}).get("name") if isinstance(repo_data.get("license"), dict) else repo_data.get("license"),
            homepage=repo_data.get("homepage"),
            topics=repo_data.get("topics", []),
            languages=GHLanguages.from_dict(data["languages"]) if "languages" in data and data["languages"] else None,
            file_tree=GHFileTree.from_dict(data["file_tree"]) if "file_tree" in data and data["file_tree"] else None,
            contributors=contributors,
        )
