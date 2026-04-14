"""Parser for the 'Passes' sheet."""

import pandas as pd
from .base import BaseParser


class PassesParser(BaseParser):
    SHEET_NAME = "Passes"
    OUTPUT_FILE = "passes.md"

    def to_markdown(self) -> str:
        lines = ["# Passes", ""]

        for _, row in self.df.iterrows():
            name = self.val(row.get("pass_name", ""))
            if not name:
                continue

            lines += [f"## {name}", ""]

            validity = self.val(row.get("validity", ""))
            price = self.val(row.get("price", ""))
            jump_time = self.val(row.get("jump_time", ""))

            if validity:
                lines.append(f"- **Validity:** {validity}")
            if price:
                lines.append(f"- **Price:** {price}")
            if jump_time:
                lines.append(f"- **Jump Time:** {jump_time}")
            lines.append("")

        return "\n".join(lines)
