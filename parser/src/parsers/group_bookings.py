"""Parser for the 'Group Bookings' sheet."""

import pandas as pd
from .base import BaseParser


_CHUNK_TITLES = {
    "scb_group_012": "Group Bookings",
    "scb_corporate_030": "Corporate & Team Parties",
    "scb_school_031": "School and Field Trips",
    "scb_fundraise_032": "Fundraising Events",
    "scb_facility_013": "Facility Rentals",
    "scb_rooms_014": "Room Rentals",
}


class GroupBookingsParser(BaseParser):
    SHEET_NAME = "Group Bookings"
    OUTPUT_FILE = "group_bookings.md"

    def to_markdown(self) -> str:
        lines = ["# Group Bookings", ""]

        # Drop rows with no chunk_id and skip separator header rows (--- ... ---)
        df = self.df[self.df["chunk_id"].notna()].copy()
        df = df[~df["field"].astype(str).str.startswith("---")]

        for chunk_id, group in df.groupby("chunk_id", sort=False):
            cid = self.val(chunk_id)
            title = _CHUNK_TITLES.get(cid, cid.replace("_", " ").title())
            lines += [f"## {title}", ""]

            for _, row in group.iterrows():
                field = self.val(row.get("field", ""))
                value = self.val(row.get("value", ""))
                notes = self.val(row.get("notes", ""))
                if not field or not value:
                    continue
                note_suffix = f" *(Note: {notes})*" if notes else ""
                lines.append(f"- **{field}:** {value}{note_suffix}")

            lines.append("")

        return "\n".join(lines)
