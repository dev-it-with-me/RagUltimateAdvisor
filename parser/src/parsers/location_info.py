"""Parser for the 'Location Info' sheet."""

import pandas as pd
from .base import BaseParser


_SECTION_LABELS = {
    "contact": "Contact Information",
    "hours": "Hours of Operation",
    "links": "Important Links",
}


class LocationInfoParser(BaseParser):
    SHEET_NAME = "Location Info"
    OUTPUT_FILE = "location_info.md"

    def to_markdown(self) -> str:
        lines = ["# AeroSports Scarborough — Location Info", ""]

        for chunk_id, group in self.df.groupby("chunk_id", sort=False):
            chunk_key = self.val(chunk_id).lower()
            section = next(
                (label for key, label in _SECTION_LABELS.items() if key in chunk_key),
                self.val(chunk_id),
            )
            lines += [f"## {section}", ""]

            for _, row in group.iterrows():
                field = self.val(row.get("field", ""))
                value = self.val(row.get("value", ""))
                if field and value:
                    lines.append(f"- **{field}:** {value}")

            lines.append("")

        return "\n".join(lines)
