import asyncio
import os
import sys
from github import Github
from semantic_kernel import Kernel, KernelArguments
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.orchestration.chat_history import ChatHistory
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings

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
    g = Github(token)
    repo = g.get_repo(repo_full_name)
    issue = repo.get_issue(int(issue_id))
    issue.create_comment(f"🤖 AI-enhanced summary:\n\n{summary}")
    if labels:
        issue.add_to_labels(*labels)

async def run_completion(kernel, messages):
    chat_service = kernel.get_service("azure-openai")
    history = ChatHistory()
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "system":
            history.add_system_message(content)
        elif role == "user":
            history.add_user_message(content)

    settings = AzureChatPromptExecutionSettings()
    result = await chat_service.get_chat_message_content(
        chat_history=history,
        settings=settings,
        kernel=kernel,
        kernel_arguments=KernelArguments()
    )
    return result.content

def main():
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

    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

    if not azure_endpoint or not azure_endpoint.startswith("https://"):
        print("Error: Invalid or missing AZURE_OPENAI_ENDPOINT", file=sys.stderr)
        sys.exit(1)
    if not azure_deployment:
        print("Error: Invalid or missing AZURE_OPENAI_DEPLOYMENT", file=sys.stderr)
        sys.exit(1)

    kernel = Kernel()
    try:
        kernel.add_service(
            AzureChatCompletion(
                service_id="azure-openai",
                api_key=openai_api_key,
                endpoint=azure_endpoint,
                deployment_name=azure_deployment,
                api_version="2024-12-01-preview"
            )
        )
    except Exception as e:
        print(f"Error initializing AzureChatCompletion: {e}", file=sys.stderr)
        sys.exit(1)

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that analyzes GitHub issues using natural language."
        },
        {
            "role": "user",
            "content": (
                f"Given the following GitHub issue:\n"
                f"ID: {issue_id}\n"
                f"Title: {issue_title}\n"
                f"Body: {issue_body}\n\n"
                f"Generate an AI-enhanced summary or insight about the issue.\n"
                f"Also, suggest up to 3 relevant GitHub labels (such as 'bug', 'good first issue', 'enhancement', etc.) as a comma-separated list.\n"
                f"Format your response as:\n"
                f"Summary: <your summary>\nLabels: <comma-separated labels>"
            )
        }
    ]

    try:
        response = asyncio.run(run_completion(kernel, messages))
    except Exception as e:
        print(f"Error running Azure OpenAI completion: {e}", file=sys.stderr)
        sys.exit(1)

    summary = ""
    labels = []
    for line in response.splitlines():
        if line.lower().startswith("summary:"):
            summary = line[len("summary:"):].strip()
        elif line.lower().startswith("labels:"):
            labels = [l.strip() for l in line[len("labels:"):].split(",") if l.strip()]
    if 'ai-enhanced' not in [l.lower() for l in labels]:
        labels.append('ai-enhanced')

    print(f"::set-output name=enhanced_summary::{summary}")
    update_github_issue(github_token, issue_id, summary, labels, repo_full_name)

if __name__ == "__main__":
    main()