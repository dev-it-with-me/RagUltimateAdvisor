"""Parser for the 'Jump Prices' sheet."""

import pandas as pd
from .base import BaseParser


class JumpPricesParser(BaseParser):
    SHEET_NAME = "Jump Prices"
    OUTPUT_FILE = "jump_prices.md"

    def to_markdown(self) -> str:
        lines = ["# Jump Prices", ""]

        for category, group in self.df.groupby("category", sort=False):
            lines += [f"## {self.val(category)}", ""]
            lines.append("| Ages | Pass Type | Price | Duration | Includes |")
            lines.append("|------|-----------|-------|----------|----------|")

            for _, row in group.iterrows():
                ages = self.val(row.get("ages", ""))
                pass_type = self.val(row.get("pass_type", ""))
                price = self.val(row.get("price", ""))
                duration = self.val(row.get("duration", ""))
                includes = self.val(row.get("includes", ""))
                lines.append(f"| {ages} | {pass_type} | {price} | {duration} | {includes} |")

            lines.append("")

        return "\n".join(lines)
