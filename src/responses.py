from typing import Dict, Any, List

class ValidationResponse:
    def __init__(self, response: str):
        self.response = response
        self.summary: str = ""
        self.labels: List[str] = []
        self.completeness: Dict[str, bool] = {}
        self.importance: str = ""
        self.acceptance_evaluation: str = ""
        self.ready_to_work: bool = False

        # Parse response during initialization
        buffer = ""
        parsing_evaluation = False

        for line in self.response.splitlines():
            lower = line.lower().strip()
            
            if lower.startswith("summary:"):
                self.summary = line[len("summary:") :].strip()
            elif lower.startswith("labels:"):
                self.labels = [
                    l.strip() for l in line[len("labels:") :].split(",") if l.strip()
                ]
            elif lower.startswith("- title:"):
                self.completeness["title"] = line.split(":")[1].strip().lower() == "yes"
            elif lower.startswith("- description:"):
                self.completeness["description"] = (
                    line.split(":")[1].strip().lower() == "yes"
                )
            elif lower.startswith("- acceptance criteria:"):
                self.completeness["acceptance_criteria"] = (
                    line.split(":")[1].strip().lower() == "yes"
                )
            elif lower.startswith("importance:"):
                self.importance = line[len("importance:") :].strip()
            elif lower.startswith("acceptance criteria evaluation:"):
                parsing_evaluation = True
                buffer = line[len("acceptance criteria evaluation:") :].strip()
            elif lower.startswith("ready to work:"):
                self.ready_to_work = (
                    line[len("ready to work:") :].strip().lower() == "true"
                )
            elif parsing_evaluation:
                if lower.startswith("labels:") or lower.startswith("ready to work:"):
                    parsing_evaluation = False
                else:
                    buffer += "\n" + line.strip()

        # finalize buffered content
        if buffer:
            self.acceptance_evaluation = buffer.strip()
            

    def as_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "labels": self.labels,
            "completeness": self.completeness,
            "importance": self.importance,
            "acceptance_evaluation": self.acceptance_evaluation,
            "ready_to_work": self.ready_to_work,
        }

    def as_markdown_str(self) -> str:
        """Format a summary and analysis comment for a GitHub issue."""

        def emoji(checked: bool) -> str:
            return "✅" if checked else "❌"

        return (
            "🤖 **AI-enhanced Summary & Analysis**\n\n"
            f"**Summary**: {self.summary if self.summary else '_No summary provided._'}\n\n"
            "**Completeness**\n"
            f"- Title: {emoji(self.completeness.get('title', False))}\n"
            f"- Description: {emoji(self.completeness.get('description', False))}\n"
            f"- Acceptance Criteria: {emoji(self.completeness.get('acceptance_criteria', False))}\n\n"
            f"**Importance**: {self.importance if self.importance else '_No importance explanation found._'}\n\n"
            f"**Acceptance Criteria Evaluation**: {self.acceptance_evaluation if self.acceptance_evaluation else '_No evaluation provided._'}\n\n"
            f"**Suggested Labels**: {', '.join(self.labels) if self.labels else '_None_'}\n\n"
            f"**Ready To Be Worked**: {emoji(self.ready_to_work)}\n"
        )


class RewriteResponse:
    def __init__(self, response: str):
        self.response = response
        self.title: str = ""
        self.description: str = ""
        self.acceptance_criteria: List[str] = []
        self.labels: List[str] = []
        self.not_applicable: bool = False

        # Parse response during initialization
        for line in self.response.splitlines():
            lower = line.lower().strip()
            if lower.startswith("title:"):
                self.title = line[len("title:") :].strip()
            elif lower.startswith("description:"):
                self.description = line[len("description:") :].strip()
            elif lower.startswith("acceptance criteria:"):
                continue  # header only
            elif lower.startswith("- "):
                self.acceptance_criteria.append(line[2:].strip())
            elif lower.startswith("labels:"):
                self.labels = [
                    l.strip() for l in line[len("labels:") :].split(",") if l.strip()
                ]
            elif lower.startswith("not applicable:"):
                self.not_applicable = (
                    line[len("not applicable:") :].strip().lower() == "true"
                )

    def as_dict(self) -> Dict[str, Any]:
        """Convert the response to a dictionary format."""
        return {
            "title": self.title,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "labels": self.labels,
            "not_applicable": self.not_applicable,
        }

    def as_markdown_str(self) -> str:
        """Render as GitHub-style markdown block."""

        def section_list(items: List[str]) -> str:
            return (
                "\n".join(f"- {item}" for item in items)
                if items
                else "_None provided._"
            )

        if self.not_applicable():
            return (
                "❌ **AI Rewrite Not Applicable**\n\n"
                "The AI has determined that this issue is not suitable for rewriting.\n"
            )

        return (
            "📝 **AI-enhanced Rewrite**\n\n"
            f"**Title**: {self.title if self.title else '_No title provided._'}\n\n"
            f"**Description**: {self.description if self.description else '_No description provided._'}\n\n"
            "**Acceptance Criteria**\n"
            f"{section_list(self.acceptance_criteria)}\n\n"
            f"**Labels**: {', '.join(self.labels) if self.labels else '_None_'}\n\n"
            f"**Not Applicable**: {'✅' if self.not_applicable else '❌'}\n"
        )
