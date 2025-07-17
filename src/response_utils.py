from typing import Any, Dict

def parse_validation_response(response: str) -> Dict[str, Any]:
    """Parse the initial AI response for summary and completeness."""
    summary = ""
    labels = []
    completeness = {}
    importance = ""
    acceptance_evaluation = ""
    ready_to_work = False
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

def parse_rewrite_response(response: str) -> Dict[str, Any]:
    """Parse the completion response into its components."""
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
            continue
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

def stringify_validation_response(response: Dict[str, Any]) -> str:
    """Format a summary and analysis comment for a GitHub issue."""
    def emoji(checked: bool) -> str:
        return "✅" if checked else "❌"
    summary = response.get("summary", "").strip()
    importance = response.get("importance", "").strip()
    acceptance_eval = response.get("acceptance_evaluation", "").strip()
    labels = response.get("labels", [])
    completeness = response.get("completeness", {})
    ready_to_work = response.get("ready_to_work", False)
    return f"""🤖 **AI-enhanced Summary & Analysis**\n\n**Summary**: {summary if summary else "_No summary provided._"}\n\n**Completeness**\n- Title: {emoji(completeness.get("title", False))}\n- Description: {emoji(completeness.get("description", False))}\n- Acceptance Criteria: {emoji(completeness.get("acceptance_criteria", False))}\n\n**Importance**: {importance if importance else "_No importance explanation found._"}\n\n**Acceptance Criteria Evaluation**: {acceptance_eval if acceptance_eval else "_No evaluation provided._"}\n\n**Suggested Labels**: {", ".join(labels) if labels else "_None_"}\n\n**Ready To Be Worked**: {emoji(ready_to_work)}\n"""

def stringify_rewrite_response(response: Dict[str, Any]) -> str:
    """Format a rewritten story proposal comment for a GitHub issue."""
    not_applicable = response.get("not_applicable", False)
    if not_applicable:
        return "⚠️ The issue could not be interpreted as a well-defined user story."
    title = response.get("title", "").strip()
    description = response.get("description", "").strip()
    criteria = response.get("acceptance_criteria", [])
    labels = response.get("labels", [])
    formatted_criteria = (
        "\n".join(f"- {c}" for c in criteria) if criteria else "_No acceptance criteria provided._"
    )
    formatted_labels = ", ".join(labels) if labels else "_None_"
    return f"""🛠️ **AI-Rewritten Story Proposal**\n\n**Title**: {title if title else "_No title provided._"}\n**Description**: {description if description else "_No description provided._"}\n\n**Acceptance Criteria**:\n{formatted_criteria}\n\n**Suggested Labels**: {formatted_labels}\n"""
