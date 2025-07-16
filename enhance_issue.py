import os
import sys
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAITextCompletion
from github import Github

def validate_inputs(github_token, openai_api_key, issue_id, issue_title, issue_body):
    errors = []
    if not github_token or len(github_token.strip()) < 10:
        errors.append("Invalid or missing GitHub token.")
    if not openai_api_key or len(openai_api_key.strip()) < 10:
        errors.append("Invalid or missing OpenAI API key.")
    if not issue_id or not issue_id.strip().isdigit():
        errors.append("Invalid or missing issue ID (should be a number).")
    if not issue_title or len(issue_title.strip()) == 0:
        errors.append("Missing issue title.")
    if not issue_body or len(issue_body.strip()) == 0:
        errors.append("Missing issue body.")
    return errors

def update_github_issue(token, issue_id, summary, labels=None):
    # Get repo info from environment (GITHUB_REPOSITORY: owner/repo)
    repo_full_name = os.getenv("GITHUB_REPOSITORY")
    if not repo_full_name:
        print("Error: GITHUB_REPOSITORY environment variable not set.", file=sys.stderr)
        sys.exit(1)
    g = Github(token)
    repo = g.get_repo(repo_full_name)
    issue = repo.get_issue(int(issue_id))
    issue.create_comment(f"🤖 AI-enhanced summary:\n\n{summary}")
    if labels:
        # Add labels to the issue (labels must be a list of strings)
        issue.add_to_labels(*labels)

def main():
    # Read inputs from environment variables (as is typical in GitHub Actions)
    github_token = os.getenv("INPUT_GITHUB_TOKEN")
    openai_api_key = os.getenv("INPUT_OPENAI_API_KEY")
    issue_id = os.getenv("INPUT_ISSUE_ID")
    issue_title = os.getenv("INPUT_ISSUE_TITLE")
    issue_body = os.getenv("INPUT_ISSUE_BODY")

    errors = validate_inputs(github_token, openai_api_key, issue_id, issue_title, issue_body)
    if errors:
        for error in errors:
            print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    # Initialize Semantic Kernel
    kernel = Kernel()
    kernel.add_text_completion_service(
        "openai-gpt",
        OpenAITextCompletion(
            service_id="openai-gpt",
            api_key=openai_api_key,
            model="gpt-3.5-turbo"  # You can change the model as needed
        )
    )

    # Define the prompt for enhancement and label suggestion
    prompt = (
        f"Given the following GitHub issue:\n"
        f"ID: {issue_id}\n"
        f"Title: {issue_title}\n"
        f"Body: {issue_body}\n\n"
        f"Generate an AI-enhanced summary or insight about the issue.\n"
        f"Also, suggest up to 3 relevant GitHub labels (such as 'bug', 'good first issue', 'enhancement', etc.) as a comma-separated list.\n"
        f"Format your response as:\n"
        f"Summary: <your summary>\nLabels: <comma-separated labels>"
    )

    # Run the completion
    response = kernel.text_completion("openai-gpt", prompt)
    # Parse response
    summary = ""
    labels = []
    for line in response.splitlines():
        if line.lower().startswith("summary:"):
            summary = line[len("summary:"):].strip()
        elif line.lower().startswith("labels:"):
            labels = [l.strip() for l in line[len("labels:"):].split(",") if l.strip()]
    # Always include 'ai-enhanced' label
    if 'ai-enhanced' not in [l.lower() for l in labels]:
        labels.append('ai-enhanced')
    print(f"::set-output name=enhanced_summary::{summary}")
    # Update the GitHub issue with the summary and AI-generated labels
    update_github_issue(github_token, issue_id, summary, labels=labels)

if __name__ == "__main__":
    main()