from github import Github
from typing import Any, Dict, Optional
import re 

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

def get_all_issue_comments(token: str, repo_full_name: str, issue_id: int) -> list:
    """Fetch all comments from a GitHub issue."""
    try:
        g = Github(token)
        repo = g.get_repo(repo_full_name)
        issue = repo.get_issue(issue_id)
        return list(issue.get_comments())
    except Exception as e:
        print(f"Error fetching issue comments: {type(e).__name__}: {e}")
        return []


def update_github_issue(
    token: str,
    repo_full_name: str,
    issue_id: int,
    title: str = None,
    body: str = None,
    labels: list = None,
) -> None:
    """Update title, body, or labels of a GitHub issue."""
    try:
        g = Github(token)
        repo = g.get_repo(repo_full_name)
        issue = repo.get_issue(issue_id)

        if title or body:
            issue.edit(title=title or issue.title, body=body or issue.body)

        if labels is not None:
            label_objs = [repo.get_label(name) for name in labels]
            issue.set_labels(*label_objs)

    except Exception as e:
        print(f"Error updating GitHub issue: {type(e).__name__}: {e}")

def parse_rewrite_comment(comment_body: str) -> dict:
    """
    Parses the bot rewrite comment and extracts title, body (including description + acceptance criteria).
    Skips updates if marked as 'No update provided.'
    """
    title_match = re.search(r"(?i)^title:\s*(.+)", comment_body, re.MULTILINE)
    desc_match = re.search(r"(?i)^description:\s*(.+)", comment_body, re.MULTILINE)

    title = title_match.group(1).strip() if title_match else None
    skip_title = title and title.lower() == "no update provided."

    description = desc_match.group(1).strip() if desc_match else None
    skip_desc = description and description.lower() == "no update provided."

    # Build full body starting from end of "Description:" line
    body = None
    if desc_match and not skip_desc:
        desc_start = desc_match.end()
        remaining = comment_body[desc_start:].strip()

        # Combine description + rest of body
        full_body = f"{description}\n\n{remaining}" if description else remaining
        body = re.sub(r"\n{2,}", "\n\n", full_body.strip())

    return {
        "title": None if skip_title else title,
        "body": body,
        "labels": None  # Add label parsing later if needed
    }