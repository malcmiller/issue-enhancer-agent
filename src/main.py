import asyncio
import os
import sys
from semantic_kernel import Kernel
from openai_utils import run_completion
from validation import validate_inputs
from github_utils import update_github_issue

SYSTEM_PROMPT = "You are a helpful assistant that analyzes GitHub issues using natural language."
LABEL_ALWAYS = "ai-enhanced"
API_VERSION = "2024-12-01-preview"

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
            # ...existing code...
            # AzureChatCompletion import and setup
            # ...existing code...
            __import__('semantic_kernel.connectors.ai.open_ai').connectors.ai.open_ai.AzureChatCompletion(
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
