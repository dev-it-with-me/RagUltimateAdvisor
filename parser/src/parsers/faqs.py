"""Parser for the 'FAQs' sheet."""

import pandas as pd
from .base import BaseParser


class FAQsParser(BaseParser):
    SHEET_NAME = "FAQs"
    OUTPUT_FILE = "faqs.md"

    def to_markdown(self) -> str:
        lines = ["# Frequently Asked Questions", ""]

        for category, group in self.df.groupby("category", sort=False):
            lines += [f"## {self.val(category)}", ""]

            for _, row in group.iterrows():
                question = self.val(row.get("question", ""))
                answer = self.val(row.get("answer", ""))
                if not question:
                    continue

                lines += [f"**Q: {question}**", ""]
                if answer:
                    lines += [f"A: {answer}", ""]

        return "\n".join(lines)
