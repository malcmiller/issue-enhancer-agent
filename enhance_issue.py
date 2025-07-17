import asyncio
import os
import sys
from github import Github
from semantic_kernel import Kernel
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings

# Constants
SYSTEM_PROMPT = "You are a helpful assistant that analyzes GitHub issues using natural language."
LABEL_ALWAYS = "ai-enhanced"
API_VERSION = "2024-12-01-preview"

# Validation
def validate_inputs(inputs):
    errors = []
    if not inputs.get("github_token") or len(inputs["github_token"].strip()) < 10:
        errors.append("Invalid or missing GitHub token.")
    if not inputs.get("openai_api_key") or len(inputs["openai_api_key"].strip()) < 10:
        errors.append("Invalid or missing OpenAI API key.")
    if not inputs.get("issue_id") or not str(inputs["issue_id"]).strip().isdigit():
        errors.append("Invalid or missing issue ID (should be a number).")
    if not inputs.get("issue_title") or len(inputs["issue_title"].strip()) == 0:
        errors.append("Missing issue title.")
    if not inputs.get("issue_body") or len(inputs["issue_body"].strip()) == 0:
        errors.append("Missing issue body.")
    if not inputs.get("repo_full_name") or '/' not in inputs["repo_full_name"]:
        errors.append("Invalid or missing GITHUB_REPOSITORY (should be in 'owner/repo' format).")
    if not inputs.get("azure_endpoint") or not inputs["azure_endpoint"].startswith("https://"):
        errors.append("Invalid or missing AZURE_OPENAI_ENDPOINT.")
    if not inputs.get("azure_deployment"):
        errors.append("Invalid or missing AZURE_OPENAI_DEPLOYMENT.")
    return errors

# GitHub Issue Update
def update_github_issue(token, issue_id, summary, labels, repo_full_name):
    g = Github(token)
    repo = g.get_repo(repo_full_name)
    issue = repo.get_issue(int(issue_id))
    issue.create_comment(f"🤖 AI-enhanced summary:\n\n{summary}")
    if labels:
        issue.add_to_labels(*labels)

# Azure OpenAI Chat Completion
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

# Main Logic
def main():
    # Gather inputs
    inputs = {
        "github_token": os.getenv("INPUT_GITHUB_TOKEN"),
        "openai_api_key": os.getenv("INPUT_OPENAI_API_KEY"),
        "issue_id": os.getenv("INPUT_ISSUE_ID"),
        "issue_title": os.getenv("INPUT_ISSUE_TITLE"),
        "issue_body": os.getenv("INPUT_ISSUE_BODY"),
        "azure_endpoint": os.getenv("INPUT_AZURE_OPENAI_ENDPOINT"),
        "azure_deployment": os.getenv("INPUT_AZURE_OPENAI_DEPLOYMENT"),
        "repo_full_name": os.getenv("GITHUB_REPOSITORY")
    }
    errors = validate_inputs(inputs)
    if errors:
        for error in errors:
            print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    # Kernel setup
    kernel = Kernel()
    try:
        kernel.add_service(
            AzureChatCompletion(
                service_id="azure-openai",
                api_key=inputs["openai_api_key"],
                endpoint=inputs["azure_endpoint"],
                deployment_name=inputs["azure_deployment"],
                api_version=API_VERSION
            )
        )
    except Exception as e:
        print(f"Error initializing AzureChatCompletion: {e}", file=sys.stderr)
        sys.exit(1)

    # Prompt construction
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Given the following GitHub issue:\n"
            f"ID: {inputs['issue_id']}\n"
            f"Title: {inputs['issue_title']}\n"
            f"Body: {inputs['issue_body']}\n\n"
            f"Generate an AI-enhanced summary or insight about the issue.\n"
            f"Also, suggest up to 3 relevant GitHub labels (such as 'bug', 'good first issue', 'enhancement', etc.) as a comma-separated list.\n"
            f"Format your response as:\n"
            f"Summary: <your summary>\nLabels: <comma-separated labels>"
        )}
    ]

    # Run completion
    try:
        response = asyncio.run(run_completion(kernel, messages))
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
    if LABEL_ALWAYS not in [l.lower() for l in labels]:
        labels.append(LABEL_ALWAYS)

    # Write enhanced summary to GitHub Actions environment file
    env_file = os.getenv('GITHUB_OUTPUT')
    if env_file:
        with open(env_file, 'a') as f:
            f.write(f"enhanced_summary={summary}\n")
    else:
        print(f"enhanced_summary={summary}")
    update_github_issue(inputs["github_token"], inputs["issue_id"], summary, labels, inputs["repo_full_name"])

if __name__ == "__main__":
    main()