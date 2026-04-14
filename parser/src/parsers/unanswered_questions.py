"""Parser for the 'Unanswered Questions' sheet."""

import pandas as pd
from .base import BaseParser


class UnansweredQuestionsParser(BaseParser):
    SHEET_NAME = "Unanswered Questions"
    OUTPUT_FILE = "unanswered_questions.md"

    def to_markdown(self) -> str:
        lines = ["# Unanswered Questions", ""]

        for category, group in self.df.groupby("category", sort=False):
            lines += [f"## {self.val(category)}", ""]

            for _, row in group.iterrows():
                question = self.val(row.get("question", ""))
                answer = self.val(row.get("answer", ""))
                status = self.val(row.get("status", ""))
                if not question:
                    continue

                status_badge = f" `[{status}]`" if status else ""
                lines += [f"**Q: {question}**{status_badge}", ""]
                if answer:
                    lines += [f"A: {answer}", ""]

        return "\n".join(lines)
