import asyncio
import os
import sys
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureTextCompletion
from github import Github

def validate_inputs(github_token, openai_api_key, issue_id, issue_title, issue_body, repo_full_name):
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
    if not repo_full_name or '/' not in repo_full_name:
        errors.append("Invalid or missing GITHUB_REPOSITORY (should be in 'owner/repo' format).")
    return errors

def update_github_issue(token, issue_id, summary, labels, repo_full_name):
    # Use repo_full_name from argument
    if not repo_full_name:
        print("Error: GITHUB_REPOSITORY not provided to update_github_issue.", file=sys.stderr)
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
    repo_full_name = os.getenv("GITHUB_REPOSITORY")

    errors = validate_inputs(github_token, openai_api_key, issue_id, issue_title, issue_body, repo_full_name)
    if errors:
        for error in errors:
            print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    # Initialize Semantic Kernel
    kernel = Kernel()
    # Validate Azure OpenAI environment variables
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    if not azure_endpoint or not azure_endpoint.startswith("https://"):
        print("Error: Invalid or missing AZURE_OPENAI_ENDPOINT (must be a valid https URL)", file=sys.stderr)
        sys.exit(1)
    if not azure_deployment or len(azure_deployment.strip()) == 0:
        print("Error: Invalid or missing AZURE_OPENAI_DEPLOYMENT", file=sys.stderr)
        sys.exit(1)
    try:

        kernel.add_service(
            AzureTextCompletion(
                api_key=openai_api_key,
                endpoint=azure_endpoint,
                deployment_name=azure_deployment
            )
        )
    except Exception as e:
        print(f"Error initializing AzureTextCompletion: {e}", file=sys.stderr)
        sys.exit(1)

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
    try:
        # Use the new SK API for text completion
        async def get_response():
            return await kernel.invoke_prompt(prompt)
        response = asyncio.run(get_response())
    except Exception as e:
        print(f"Error running Azure OpenAI completion: {e}", file=sys.stderr)
        sys.exit(1)
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
    update_github_issue(github_token, issue_id, summary, labels, repo_full_name)

if __name__ == "__main__":
    main()