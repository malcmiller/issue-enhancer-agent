import asyncio
import os
import sys
from openai_utils import run_completion, initialize_kernel
from validation import validate_inputs
from github_utils import (
    get_github_issue,
    create_github_issue_comment,
    get_all_issue_comments,
    update_github_issue,
)
from prompts import build_validation_message, build_rewrite_message
from responses import ValidationResponse, RewriteResponse
from parser import parse_rewrite_comment  # assumes you’ve created this


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


def handle_apply_comment():
    token = os.getenv("INPUT_GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    issue_id = int(os.getenv("INPUT_ISSUE_ID"))
    trigger_comment_id = int(os.getenv("GITHUB_COMMENT_ID"))  # user’s apply comment ID

    comments = get_all_issue_comments(token, repo, issue_id)
    if not comments:
        print("No comments found.")
        return

    # Filter only comments before the trigger comment (by ID)
    prior_comments = [c for c in comments if c.id < trigger_comment_id]

    # Find the latest bot rewrite comment before the apply comment
    bot_comment = None
    for comment in reversed(prior_comments):
        if "ai-enhanced rewrite" in comment.body.lower():
            # Non-brittle way of looking for the bot comment
            bot_comment = comment
            break

    if not bot_comment:
        print("No valid suggestion comment found to apply.")
        return

    parsed = parse_rewrite_comment(bot_comment.body)
    if not parsed:
        print("Failed to parse bot comment for changes.")
        return

    # Filter out fields with 'No update provided.' placeholders
    updates = {}
    for field in ["title", "body", "labels"]:
        val = parsed.get(field)
        if val is None:
            continue
        if isinstance(val, str) and val.strip().lower() == "no update provided.":
            continue
        if isinstance(val, list) and (len(val) == 0 or all(s.lower() == "no update provided." for s in val)):
            continue
        updates[field] = val

    if not updates:
        print("No actual updates found in the suggestion comment.")
        return

    update_github_issue(
        token,
        repo,
        issue_id,
        title=updates.get("title"),
        body=updates.get("body"),
        labels=updates.get("labels")
    )

    print("Changes applied to issue.")


if __name__ == "__main__":
    main()
