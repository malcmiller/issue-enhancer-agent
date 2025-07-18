import asyncio
import os
import sys
from typing import Any, Dict
from openai_utils import run_completion, initialize_kernel
from validation import validate_inputs
from github_utils import get_github_issue, create_github_issue_comment
from prompts import build_validation_message, build_rewrite_message
from responses import ValidationResponse, RewriteResponse


def main() -> None:
    """Main entry point for the issue enhancer agent."""
    inputs = {
        "github_token": os.getenv("INPUT_GITHUB_TOKEN"),
        "openai_api_key": os.getenv("INPUT_OPENAI_API_KEY"),
        "issue_id": int(os.getenv("INPUT_ISSUE_ID")),
        "azure_endpoint": os.getenv("INPUT_AZURE_OPENAI_ENDPOINT"),
        "azure_deployment": os.getenv("INPUT_AZURE_OPENAI_DEPLOYMENT"),
        "repo_full_name": os.getenv("GITHUB_REPOSITORY"),
    }


    issue = get_github_issue(inputs["github_token"], inputs["repo_full_name"], inputs["issue_id"])

    validate_inputs(inputs)

    # Kernel setup
    kernel = initialize_kernel(inputs)

    # Prompt construction
    messages = build_validation_message(inputs["issue_id"], issue.title, issue.body)

    # Run completion
    try:
        response = asyncio.run(run_completion(kernel, messages))
    except Exception as e:
        print(f"Error running Azure OpenAI completion: {e}", file=sys.stderr)
        sys.exit(1)

    response = ValidationResponse(response)

    create_github_issue_comment(
        inputs["github_token"],
        inputs["repo_full_name"],
        inputs["issue_id"],
        response.as_markdown_str(),
    )

    if response.ready_to_work: 
        return 0
    
    messages = build_rewrite_message(inputs["issue_id"], issue.title, issue.body, response.completeness)
    try:
        response = asyncio.run(run_completion(kernel, messages))
    except Exception as e:
        print(f"Error running Azure OpenAI completion: {e}", file=sys.stderr)
        sys.exit(1)

    response = RewriteResponse(response)

    create_github_issue_comment(
        inputs["github_token"],
        inputs["repo_full_name"],
        inputs["issue_id"],
        response.as_markdown_str(),
    )


if __name__ == "__main__":
    main()
