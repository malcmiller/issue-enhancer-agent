import asyncio
import os
import sys
from openai_utils import run_completion, initialize_kernel
from validation import validate_inputs
from github_utils import (
    get_github_issue,
    create_github_issue_comment,
    get_github_comment,
    update_github_issue,
)
from prompts import build_validation_message, build_rewrite_message
from responses import ValidationResponse, RewriteResponse


def main() -> None:
    if os.getenv("GITHUB_COMMENT_ID"):
        handle_apply_comment()
    else:
        handle_new_issue()


def handle_new_issue():
    """Handles enhancement when a new issue is created."""
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

    kernel = initialize_kernel(inputs)

    # Step 1: Run validation
    messages = build_validation_message(issue["number"], issue["title"], issue["body"])
    try:
        validation_raw = asyncio.run(run_completion(kernel, messages))
        validation = ValidationResponse(validation_raw)
    except Exception as e:
        print(f"Error during validation: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)

    create_github_issue_comment(
        inputs["github_token"],
        inputs["repo_full_name"],
        inputs["issue_id"],
        validation.as_markdown_str(),
    )

    if validation.ready_to_work:
        return

    # Step 2: Run rewrite
    messages = build_rewrite_message(issue["number"], issue["title"], issue["body"], validation.completeness)
    try:
        rewrite_raw = asyncio.run(run_completion(kernel, messages))
        rewrite = RewriteResponse(rewrite_raw)
    except Exception as e:
        print(f"Error during rewrite: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)

    create_github_issue_comment(
        inputs["github_token"],
        inputs["repo_full_name"],
        inputs["issue_id"],
        rewrite.as_markdown_str(),
    )


def update_issue_body_with_rewrite(original_body: str, new_description: str, new_acceptance_criteria: list[str]) -> str:
    import re

    criteria_text = "\n".join(f"- {item}" for item in new_acceptance_criteria) if new_acceptance_criteria else ""

    description_pattern = re.compile(
        r"(Description:\s*\n)(.*?)(\n\n|\Z)", re.IGNORECASE | re.DOTALL
    )
    acceptance_pattern = re.compile(
        r"(Acceptance Criteria:\s*\n)(.*?)(\n\n|\Z)", re.IGNORECASE | re.DOTALL
    )

    if new_description:
        if description_pattern.search(original_body):
            original_body = description_pattern.sub(r"\1" + new_description + r"\3", original_body)
        else:
            original_body += f"\n\nDescription:\n{new_description}"

    if criteria_text:
        if acceptance_pattern.search(original_body):
            original_body = acceptance_pattern.sub(r"\1" + criteria_text + r"\3", original_body)
        else:
            original_body += f"\n\nAcceptance Criteria:\n{criteria_text}"

    return original_body

def update_issue_body_with_rewrite(original_body: str, new_description: str, new_acceptance_criteria: list[str]) -> str:
    import re

    criteria_text = "\n".join(f"- {item}" for item in new_acceptance_criteria) if new_acceptance_criteria else ""

    description_pattern = re.compile(
        r"(Description:\s*\n)(.*?)(\n\n|\Z)", re.IGNORECASE | re.DOTALL
    )
    acceptance_pattern = re.compile(
        r"(Acceptance Criteria:\s*\n)(.*?)(\n\n|\Z)", re.IGNORECASE | re.DOTALL
    )

    if new_description:
        if description_pattern.search(original_body):
            original_body = description_pattern.sub(r"\1" + new_description + r"\3", original_body)
        else:
            original_body += f"\n\nDescription:\n{new_description}"

    if criteria_text:
        if acceptance_pattern.search(original_body):
            original_body = acceptance_pattern.sub(r"\1" + criteria_text + r"\3", original_body)
        else:
            original_body += f"\n\nAcceptance Criteria:\n{criteria_text}"

    return original_body


def handle_apply_comment() -> None:
    """Handles applying enhancements on user comment."""
    inputs = {
        "token": os.getenv("INPUT_GITHUB_TOKEN"),
        "issue_id": int(os.getenv("INPUT_ISSUE_ID")),
        "comment_id": int(os.getenv("GITHUB_COMMENT_ID")),
        "repo_full_name": os.getenv("GITHUB_REPOSITORY"),
    }

    token = inputs["token"]
    issue_number = inputs["issue_id"]
    comment_id = inputs["comment_id"]
    repo_full_name = inputs["repo_full_name"]

    print(f"🛠 Handling apply comment for issue #{issue_number} and comment {comment_id}")

    # Fetch current issue and comment from GitHub
    issue = get_github_issue(token, repo_full_name, issue_number)
    comment = get_github_comment(token, repo_full_name, issue_number, comment_id)

    # Parse rewrite from comment body
    rewrite = RewriteResponse.from_comment(comment.body)

    # Normalize title check helper
    def normalize_text(text: str) -> str:
        return text.lower().strip(" _*")

    # Prepare updated title if valid
    new_title = None
    if rewrite.title and normalize_text(rewrite.title) != "no update provided.":
        new_title = rewrite.title
        print(f"✅ Will update title to: {new_title}")
    else:
        print("🟡 Skipping title update")

    # Update issue body with description and acceptance criteria
    new_body = issue["body"]
    new_body = update_issue_body_with_rewrite(
        original_body=new_body,
        new_description=rewrite.description if rewrite.description and normalize_text(rewrite.description) != "no update provided." else None,
        new_acceptance_criteria=rewrite.acceptance_criteria,
    )
    print("✅ Issue body updated with new description and acceptance criteria")

    # Push update to GitHub
    try:
        update_github_issue(
            token=token,
            repo_full_name=repo_full_name,
            issue_number=issue_number,
            title=new_title,  # None means no change
            body=new_body,
            labels=None,  # No label changes here
        )
        print(f"🎉 Successfully applied rewrite updates to issue #{issue_number}")
    except Exception as e:
        print(f"❌ Failed to update issue: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)



if __name__ == "__main__":
    main()
