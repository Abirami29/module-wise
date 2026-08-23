"""
Pulls commit metadata per file using GitPython. Attached as properties on
graph nodes later (Epic 3), not embedded as a separate vector source.
"""
from pathlib import Path

from git import Repo


def get_file_history(repo_path: Path, file_relative_path: str, max_commits: int = 5) -> list[dict]:
    """Return recent commits that touched a given file, most recent first."""
    repo = Repo(repo_path)
    commits = list(repo.iter_commits(paths=file_relative_path, max_count=max_commits))
    return [
        {
            "sha": c.hexsha[:8],
            "message": c.message.strip(),
            "author": c.author.name,
            "date": c.committed_datetime.isoformat(),
        }
        for c in commits
    ]


def get_repo_summary(repo_path: Path) -> dict:
    """Basic repo-level metadata: commit count, tags, latest commit."""
    repo = Repo(repo_path)
    commits = list(repo.iter_commits())
    return {
        "total_commits": len(commits),
        "tags": [t.name for t in repo.tags],
        "latest_commit": {
            "sha": commits[0].hexsha[:8],
            "message": commits[0].message.strip(),
            "date": commits[0].committed_datetime.isoformat(),
        } if commits else None,
    }