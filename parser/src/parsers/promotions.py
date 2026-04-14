"""Parser for the 'Promotions' sheet."""

import pandas as pd
from .base import BaseParser


class PromotionsParser(BaseParser):
    SHEET_NAME = "Promotions"
    OUTPUT_FILE = "promotions.md"

    def to_markdown(self) -> str:
        lines = ["# Promotions", ""]

        for promo_name, group in self.df.groupby("promo_name", sort=False):
            lines += [f"## {self.val(promo_name)}", ""]

            description = self.val(group.iloc[0].get("description", ""))
            if description:
                lines += [description, ""]

            terms = self.val(group.iloc[0].get("terms", ""))
            status = self.val(group.iloc[0].get("status", ""))

            if status:
                lines.append(f"- **Status:** {status}")
            if terms:
                lines.append(f"- **Terms:** {terms}")
            lines.append("")

            lines += ["### Promo Codes", ""]
            lines.append("| Applies To | Discount | Code |")
            lines.append("|------------|----------|------|")
            for _, row in group.iterrows():
                applies_to = self.val(row.get("applies_to", ""))
                discount = self.val(row.get("discount", ""))
                code = self.val(row.get("code", ""))
                lines.append(f"| {applies_to} | {discount} | {code} |")
            lines.append("")

        return "\n".join(lines)
