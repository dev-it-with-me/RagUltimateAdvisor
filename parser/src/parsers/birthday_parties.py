"""Parser for the 'Birthday Parties' sheet."""

import pandas as pd
from .base import BaseParser


class BirthdayPartiesParser(BaseParser):
    SHEET_NAME = "Birthday Parties"
    OUTPUT_FILE = "birthday_parties.md"

    def to_markdown(self) -> str:
        lines = ["# Birthday Parties", ""]

        for package_name, group in self.df.groupby("package_name", sort=False):
            lines += [f"## {self.val(package_name)}", ""]

            for _, row in group.iterrows():
                field = self.val(row.get("field", ""))
                value = self.val(row.get("value", ""))
                if not field or not value:
                    continue

                # Long-form fields render as a paragraph; others as bold key-value
                if field.lower() in ("summary", "overview"):
                    lines += [value, ""]
                else:
                    label = field.replace("_", " ").title()
                    lines += [f"**{label}:** {value}", ""]

        return "\n".join(lines)
