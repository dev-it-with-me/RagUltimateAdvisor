"""Parser for the 'Park Rules' sheet."""

import pandas as pd
from .base import BaseParser


class ParkRulesParser(BaseParser):
    SHEET_NAME = "Park Rules"
    OUTPUT_FILE = "park_rules.md"

    def to_markdown(self) -> str:
        lines = ["# Park Rules", ""]

        for _, row in self.df.iterrows():
            topic = self.val(row.get("rule_topic", ""))
            text = self.val(row.get("rule_text", ""))
            if not topic and not text:
                continue

            if topic:
                lines += [f"## {topic}", ""]
            if text:
                lines += [text, ""]

        return "\n".join(lines)
