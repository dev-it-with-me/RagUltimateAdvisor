"""Parser for the 'Special Programs' sheet."""

import pandas as pd
from .base import BaseParser


class SpecialProgramsParser(BaseParser):
    SHEET_NAME = "Special Programs"
    OUTPUT_FILE = "special_programs.md"

    def to_markdown(self) -> str:
        lines = ["# Special Programs", ""]

        for _, row in self.df.iterrows():
            program = self.val(row.get("program", ""))
            if not program:
                continue

            lines += [f"## {program}", ""]

            details = self.val(row.get("details", ""))
            if details:
                lines += [details, ""]

            availability = self.val(row.get("availability", ""))
            time = self.val(row.get("time", ""))
            price = self.val(row.get("price", ""))

            if availability:
                lines.append(f"- **Availability:** {availability}")
            if time:
                lines.append(f"- **Time:** {time}")
            if price:
                lines.append(f"- **Price:** {price}")
            lines.append("")

        return "\n".join(lines)
