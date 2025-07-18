from typing import Dict

SYSTEM_PROMPT = "You are a helpful assistant that analyzes GitHub issues using natural language."

def build_validation_message(issue_id: str, issue_title: str, issue_body: str) -> list:
    prompt = (
        f"Given the following GitHub issue:\n"
        f"ID: {issue_id}\n"
        f"Title: {issue_title}\n"
        f"Body: {issue_body}\n\n"
        "Review this issue as a potential user story for engineering work. In your response:\n"
        "1. Provide an AI-enhanced summary or insight about the story.\n"
        "2. Confirm whether the following elements are present:\n"
        "   - A title\n"
        "   - A description\n"
        "   - Acceptance criteria\n"
        "3. Evaluate the clarity and completeness of the description. Does it explain why the story matters (e.g. business value, customer need, technical dependency)?\n"
        "4. Analyze the acceptance criteria. Are they clear, specific, and testable via automated testing?\n"
        "   - If you believe the acceptance criteria are not automatable, provide a warning with suggestions for making them testable.\n"
        "5. Suggest up to 3 relevant GitHub labels (such as 'bug', 'good first issue', 'enhancement', etc.) as a comma-separated list.\n"
        "6. Based on your analysis, provide a final Boolean judgment of whether this story is ready to be worked. Assume 'ready' means: all required elements are present, purpose is clear, and acceptance criteria are testable.\n\n"
        "Format your response like this:\n"
        "Summary: <your insight>\n"
        "Completeness:\n"
        " - Title: <Yes/No>\n"
        " - Description: <Yes/No>\n"
        " - Acceptance Criteria: <Yes/No>\n"
        "Importance: <Brief assessment of why the story matters>\n"
        "Acceptance Criteria Evaluation: <Analysis + any testability warning>\n"
        "Labels: <comma-separated label list>\n"
        "Ready to Work: <True/False>"
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

def build_rewrite_message(issue_id: str, issue_title: str, issue_body: str, incomplete_parts: Dict[str, bool]) -> str:
    prompt = (
        f"The following GitHub issue appears incomplete and is not yet ready to be worked:\n"
        f"ID: {issue_id}\n"
        f"Title: {issue_title}\n"
        f"Body: {issue_body}\n\n"
        "As an AI assistant, help rewrite this issue into a well-formed user story for engineering.\n"
    )

    # Conditional instructions based on what’s missing
    sections = []
    if not incomplete_parts.get("title", True):
        sections.append("1. Propose an improved **title** that clearly reflects what should be built, fixed, or changed.")
    if not incomplete_parts.get("description", True):
        sections.append("2. Write a meaningful **description** that explains why the work matters (business value, user impact, or technical need).")
    if not incomplete_parts.get("acceptance_criteria", True):
        sections.append("3. Provide specific and testable **acceptance criteria**.")

    if sections:
        prompt += "\n".join(sections) + "\n"
    else:
        prompt += "All core elements are sufficiently present. No rewrite necessary.\n"

    prompt += (
        "\n4. Suggest up to 3 relevant GitHub **labels** for triage purposes (e.g. 'bug', 'enhancement', 'good first issue').\n"
        "5. If you are unable to confidently generate any missing core elements, return:\n"
        "   Not Applicable: True\n\n"
        "Format your response like this:\n"
    )

    # Format section is always shown for consistency
    if not incomplete_parts.get("title", True):
        prompt += "Title: <rewritten title>\n"
    if not incomplete_parts.get("description", True):
        prompt += "Description: <expanded explanation>\n"
    if not incomplete_parts.get("acceptance_criteria", True):
        prompt += (
            "Acceptance Criteria:\n"
            "- <criterion one>\n"
            "- <criterion two>\n"
            "- <etc...>\n"
        )
    
    prompt += "Labels: <comma-separated labels>\nNot Applicable: <True/False>"

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": prompt,
        },
    ]
