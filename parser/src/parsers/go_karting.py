"""Parser for the 'Go Karting' sheet."""

import pandas as pd
from .base import BaseParser


class GoKartingParser(BaseParser):
    SHEET_NAME = "Go Karting"
    OUTPUT_FILE = "go_karting.md"

    def to_markdown(self) -> str:
        lines = ["# Go Karting", ""]

        for track, group in self.df.groupby("track", sort=False):
            lines += [f"## {self.val(track)}", ""]

            for _, row in group.iterrows():
                race_type = self.val(row.get("race_type", ""))
                price = self.val(row.get("price", ""))
                min_height = self.val(row.get("min_height", ""))
                notes = self.val(row.get("notes", ""))

                lines += [f"### {race_type}", ""]
                lines.append(f"- **Price:** {price}")
                lines.append(f"- **Minimum Height:** {min_height}")
                if notes:
                    lines.append(f"- **Notes:** {notes}")
                lines.append("")

        return "\n".join(lines)
