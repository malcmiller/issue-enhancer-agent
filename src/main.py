import asyncio
import os
import sys
from openai_utils import run_completion, initialize_kernel
from validation import validate_inputs
from github_utils import update_github_issue, update_github_issue_completion

SYSTEM_PROMPT = "You are a helpful assistant that analyzes GitHub issues using natural language."

def parse_completion_response(response: str) -> dict:
    title = ""
    description = ""
    criteria = []
    labels = []
    not_applicable = False

    for line in response.splitlines():
        lower = line.lower().strip()

        if lower.startswith("title:"):
            title = line[len("title:"):].strip()

        elif lower.startswith("description:"):
            description = line[len("description:"):].strip()

        elif lower.startswith("acceptance criteria:"):
            # Start collecting criteria from the next lines
            continue  # Header itself doesn’t contain data

        elif lower.startswith("- "):
            criteria.append(line[2:].strip())

        elif lower.startswith("labels:"):
            labels = [l.strip() for l in line[len("labels:"):].split(",") if l.strip()]

        elif lower.startswith("not applicable:"):
            raw_flag = line[len("not applicable:"):].strip().lower()
            not_applicable = raw_flag == "true"

    return {
        "title": title,
        "description": description,
        "acceptance_criteria": criteria,
        "labels": labels,
        "not_applicable": not_applicable
    }

def parse_response(response):
    summary = ""
    labels = []
    completeness = {}
    importance = ""
    acceptance_evaluation = ""
    ready_to_work = False  # Default to False

    for line in response.splitlines():
        lower = line.lower()
        if lower.startswith("summary:"):
            summary = line[len("summary:"):].strip()
        elif lower.startswith("labels:"):
            labels = [l.strip() for l in line[len("labels:"):].split(",") if l.strip()]
        elif lower.startswith("- title:"):
            completeness["title"] = line.split(":")[1].strip().lower() == "yes"
        elif lower.startswith("- description:"):
            completeness["description"] = line.split(":")[1].strip().lower() == "yes"
        elif lower.startswith("- acceptance criteria:"):
            completeness["acceptance_criteria"] = line.split(":")[1].strip().lower() == "yes"
        elif lower.startswith("importance:"):
            importance = line[len("importance:"):].strip()
        elif lower.startswith("acceptance criteria evaluation:"):
            acceptance_evaluation = line[len("acceptance criteria evaluation:"):].strip()
        elif lower.startswith("ready to work:"):
            raw_flag = line[len("ready to work:"):].strip().lower()
            ready_to_work = raw_flag == "true"

    return {
        "summary": summary,
        "labels": labels,
        "completeness": completeness,
        "importance": importance,
        "acceptance_evaluation": acceptance_evaluation,
        "ready_to_work": ready_to_work
    }
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
    
    validate_inputs(inputs)

    # Kernel setup
    kernel = initialize_kernel(inputs)

    # Prompt construction
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Given the following GitHub issue:\n"
            f"ID: {inputs['issue_id']}\n"
            f"Title: {inputs['issue_title']}\n"
            f"Body: {inputs['issue_body']}\n\n"

            f"Review this issue as a potential user story for engineering work. In your response:\n"
            f"1. Provide an AI-enhanced summary or insight about the story.\n"
            f"2. Confirm whether the following elements are present:\n"
            f"   - A title\n"
            f"   - A description\n"
            f"   - Acceptance criteria\n"
            f"3. Evaluate the clarity and completeness of the description. Does it explain why the story matters (e.g. business value, customer need, technical dependency)?\n"
            f"4. Analyze the acceptance criteria. Are they clear, specific, and testable via automated testing?\n"
            f"   - If you believe the acceptance criteria are not automatable, provide a warning with suggestions for making them testable.\n"
            f"5. Suggest up to 3 relevant GitHub labels (such as 'bug', 'good first issue', 'enhancement', etc.) as a comma-separated list.\n"
            f"6. Based on your analysis, provide a final Boolean judgment of whether this story is ready to be worked. Assume 'ready' means: all required elements are present, purpose is clear, and acceptance criteria are testable.\n\n"

            f"Format your response like this:\n"
            f"Summary: <your insight>\n"
            f"Completeness:\n"
            f" - Title: <Yes/No>\n"
            f" - Description: <Yes/No>\n"
            f" - Acceptance Criteria: <Yes/No>\n"
            f"Importance: <Brief assessment of why the story matters>\n"
            f"Acceptance Criteria Evaluation: <Analysis + any testability warning>\n"
            f"Labels: <comma-separated label list>\n"
            f"Ready to Work: <True/False>"
        )}
    ]

    # Run completion
    try:
        response = asyncio.run(run_completion(kernel, messages))
    except Exception as e:
        print(f"Error running Azure OpenAI completion: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse response
    response = parse_response(response)
    update_github_issue(inputs["github_token"], inputs["issue_id"], inputs["repo_full_name"], response)
    

    if response["ready_to_work"] is False:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"The following GitHub issue appears incomplete and is not yet ready to be worked:\n"
                f"ID: {inputs['issue_id']}\n"
                f"Title: {inputs['issue_title']}\n"
                f"Body: {inputs['issue_body']}\n\n"

                f"As an AI assistant, help rewrite this issue into a well-formed user story for engineering. Your response should:\n"
                f"1. Propose an improved **title** that clearly reflects what should be built, fixed, or changed.\n"
                f"2. Write a meaningful **description** that explains why the work matters (business value, user impact, or technical need).\n"
                f"3. Provide specific and testable **acceptance criteria**.\n"
                f"4. Suggest up to 3 relevant GitHub **labels** for triage purposes (e.g. 'bug', 'enhancement', 'good first issue').\n"
                f"5. If the issue cannot reasonably be expressed as a proper user story or engineering task (e.g. it's a question or discussion), return:\n"
                f"   Not Applicable: True\n\n"

                f"Format your response like this:\n"
                f"Title: <rewritten title>\n"
                f"Description: <expanded explanation>\n"
                f"Acceptance Criteria:\n"
                f"- <criterion one>\n"
                f"- <criterion two>\n"
                f"- <etc...>\n"
                f"Labels: <comma-separated labels>\n"
                f"Not Applicable: <True/False>"
            )}
        ]
        try:
            completion_response = asyncio.run(run_completion(kernel, messages))
        except Exception as e:
            print(f"Error running Azure OpenAI completion: {e}", file=sys.stderr)
            sys.exit(1)


    if completion_response:
        completion_data = parse_completion_response(completion_response)
        update_github_issue_completion(inputs["github_token"], inputs["issue_id"], inputs["repo_full_name"], completion_data)


if __name__ == "__main__":
    main()
