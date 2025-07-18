import asyncio
import os
import sys
from typing import Any, Dict
from openai_utils import run_completion, initialize_kernel
from validation import validate_inputs, completion_is_valid
from github_utils import create_github_issue_comment
from prompts import SYSTEM_PROMPT, VALIDATION_PROMPT, REWRITE_PROMPT
from responses import ValidationResponse, RewriteResponse


def build_messages(inputs: Dict[str, Any], prompt_template: str) -> list:
    """Construct prompt messages for the AI using a given template."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": prompt_template.format(
                issue_id=inputs["issue_id"],
                issue_title=inputs["issue_title"],
                issue_body=inputs["issue_body"],
            ),
        },
    ]


def main() -> None:
    """Main entry point for the issue enhancer agent."""
    inputs = {
        "github_token": os.getenv("INPUT_GITHUB_TOKEN"),
        "openai_api_key": os.getenv("INPUT_OPENAI_API_KEY"),
        "issue_id": int(os.getenv("INPUT_ISSUE_ID")),
        "issue_title": os.getenv("INPUT_ISSUE_TITLE"),
        "issue_body": os.getenv("INPUT_ISSUE_BODY"),
        "azure_endpoint": os.getenv("INPUT_AZURE_OPENAI_ENDPOINT"),
        "azure_deployment": os.getenv("INPUT_AZURE_OPENAI_DEPLOYMENT"),
        "repo_full_name": os.getenv("GITHUB_REPOSITORY"),
    }

    validate_inputs(inputs)

    # Kernel setup
    kernel = initialize_kernel(inputs)

    # Prompt construction
    messages = build_messages(inputs, VALIDATION_PROMPT)

    # Run completion
    try:
        response = asyncio.run(run_completion(kernel, messages))
    except Exception as e:
        print(f"Error running Azure OpenAI completion: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse response
    response = ValidationResponse(response)

    create_github_issue_comment(
        inputs["github_token"],
        inputs["repo_full_name"],
        inputs["issue_id"],
        response.as_markdown_str(),
    )

    if response.ready_to_work is False:
        messages = build_messages(inputs, REWRITE_PROMPT)
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
