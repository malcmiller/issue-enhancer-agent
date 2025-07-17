from github import Github
from typing import Any, Dict, Optional


def create_github_issue_comment(
    token: str,
    repo_full_name: str,
    issue_id: int,
    comment: str
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
            with open(env_file, 'a') as f:
                f.write(f"{key}={value}\n")
        except Exception as e:
            print(f"Error writing to env file: {e}")
    else:
        print(f"{key}={value}")