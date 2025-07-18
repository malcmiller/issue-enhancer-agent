from github import Github
from typing import Any, Dict, Optional


def get_github_issue(
    token: str, repo_full_name: str, issue_id: int
) -> Optional[Dict[str, Any]]:
    """Fetch a GitHub issue by its ID."""
    try:
        g = Github(token)
        repo = g.get_repo(repo_full_name)
        issue = repo.get_issue(issue_id)
        return {
            "id": issue.id,
            "number": issue.number,
            "title": issue.title,
            "body": issue.body,
            "state": issue.state,
            "labels": [label.name for label in issue.labels],
            "assignee": issue.assignee.login if issue.assignee else None,
            "created_at": issue.created_at.isoformat(),
            "updated_at": issue.updated_at.isoformat(),
        }
    except Exception as e:
        print(f"Error fetching GitHub issue: {type(e).__name__}: {e}")
        return None


def create_github_issue_comment(
    token: str, repo_full_name: str, issue_id: int, comment: str
) -> None:
    """Create a comment on a GitHub issue with detailed error reporting."""
    try:
        g = Github(token)
        repo = g.get_repo(repo_full_name)
        issue = repo.get_issue(issue_id)
        issue.create_comment(comment)
    except Exception as e:
        print(f"Error creating GitHub issue comment: {type(e).__name__}: {e}")


def write_github_output(env_file: Optional[str], key: str, value: str) -> None:
    """Write a key-value pair to the GitHub Actions environment file."""
    if env_file:
        try:
            with open(env_file, "a") as f:
                f.write(f"{key}={value}\n")
        except Exception as e:
            print(f"Error writing to env file: {e}")
    else:
        print(f"{key}={value}")
