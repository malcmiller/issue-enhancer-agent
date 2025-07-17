from os import read
from github import Github

def sanitized_comment(response: dict) -> str:
    def emoji(checked: bool) -> str:
        return "✅" if checked else "❌"

    summary = response.get("summary", "").strip()
    importance = response.get("importance", "").strip()
    acceptance_eval = response.get("acceptance_evaluation", "").strip()
    labels = response.get("labels", [])
    completeness = response.get("completeness", {})
    ready_to_work = response.get("ready_to_work", False)

    return f"""🤖 **AI-enhanced Summary & Analysis**

**Summary**: {summary if summary else "_No summary provided._"}

**Completeness**
- Title: {emoji(completeness.get("title", False))}
- Description: {emoji(completeness.get("description", False))}
- Acceptance Criteria: {emoji(completeness.get("acceptance_criteria", False))}

**Importance**: {importance if importance else "_No importance explanation found._"}

**Acceptance Criteria Evaluation**: {acceptance_eval if acceptance_eval else "_No evaluation provided._"}

**Suggested Labels**: {", ".join(labels) if labels else "_None_"}

**Ready To Be Worked**: {emoji(ready_to_work)}
"""


def sanitized_completion_comment(response: dict) -> str:
    not_applicable = response.get("not_applicable", False)

    if not_applicable:
        return "⚠️ The issue could not be interpreted as a well-defined user story.\n\n**Not Applicable: True**"

    title = response.get("title", "").strip()
    description = response.get("description", "").strip()
    criteria = response.get("acceptance_criteria", [])
    labels = response.get("labels", [])

    formatted_criteria = (
        "\n".join(f"- {c}" for c in criteria) if criteria else "_No acceptance criteria provided._"
    )
    formatted_labels = ", ".join(labels) if labels else "_None_"

    return f"""🛠️ **AI-Rewritten Story Proposal**

**Title**: {title if title else "_No title provided._"}
**Description**: {description if description else "_No description provided._"}

**Acceptance Criteria**:
{formatted_criteria}

**Suggested Labels**: {formatted_labels}
"""

def update_github_issue(token, issue_id, repo_full_name, response):
    g = Github(token)
    repo = g.get_repo(repo_full_name)
    issue = repo.get_issue(int(issue_id))
    issue.create_comment(sanitized_comment(response))

def update_github_issue_completion(token, issue_id, repo_full_name, response):
    g = Github(token)
    repo = g.get_repo(repo_full_name)
    issue = repo.get_issue(int(issue_id))
    issue.create_comment(sanitized_completion_comment(response))

def write_github_output(env_file, key, value):
    if env_file:
        with open(env_file, 'a') as f:
            f.write(f"{key}={value}\n")
    else:
        print(f"{key}={value}")