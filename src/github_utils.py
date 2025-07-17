from github import Github

def update_github_issue(token, issue_id, repo_full_name, updates):
    g = Github(token)
    repo = g.get_repo(repo_full_name)
    issue = repo.get_issue(int(issue_id))
    issue.create_comment(f"""🤖 **AI-enhanced Summary & Analysis**
    **Summary**: {updates["summary"]}

    **Completeness**
    - Title: {"✅" if updates["completeness"].get("title") else "❌"}
    - Description: {"✅" if updates["completeness"].get("description") else "❌"}
    - Acceptance Criteria: {"✅" if updates["completeness"].get("acceptance_criteria") else "❌"}

    **Importance**: {updates["importance"]}
    **Acceptance Criteria Evaluation**: {updates["acceptance_evaluation"]}

    **Suggested Labels**: {", ".join(updates["labels"])}
    """)

def write_github_output(env_file, key, value):
    if env_file:
        with open(env_file, 'a') as f:
            f.write(f"{key}={value}\n")
    else:
        print(f"{key}={value}")