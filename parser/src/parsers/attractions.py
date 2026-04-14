"""Parser for the 'Attractions' sheet."""

import pandas as pd
from .base import BaseParser


class AttractionsParser(BaseParser):
    SHEET_NAME = "Attractions"
    OUTPUT_FILE = "attractions.md"

    def to_markdown(self) -> str:
        lines = ["# Attractions", ""]

        for _, row in self.df.iterrows():
            name = self.val(row.get("attraction_name", ""))
            if not name:
                continue

            lines += [f"## {name}", ""]

            description = self.val(row.get("description", ""))
            if description:
                lines += [description, ""]

            age_req = self.val(row.get("age_height_requirements", ""))
            included = self.val(row.get("included_in_jump_pass", ""))
            pricing = self.val(row.get("pricing_note", ""))

            if age_req:
                lines.append(f"- **Age/Height Requirements:** {age_req}")
            if included:
                lines.append(f"- **Included in Jump Pass:** {included}")
            if pricing:
                lines.append(f"- **Pricing:** {pricing}")
            lines.append("")

        return "\n".join(lines)
