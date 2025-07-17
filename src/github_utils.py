from github import Github

def update_github_issue(token, issue_id, summary, labels, repo_full_name):
    g = Github(token)
    repo = g.get_repo(repo_full_name)
    issue = repo.get_issue(int(issue_id))
    issue.create_comment(f"🤖 AI-enhanced summary:\n\n{summary}")
    if labels:
        issue.add_to_labels(*labels)
