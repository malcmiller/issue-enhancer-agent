import sys

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

    if errors:
        for error in errors:
            print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
