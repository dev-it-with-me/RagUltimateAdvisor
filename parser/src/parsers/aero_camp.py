"""Parser for the 'Aero Camp' sheet.

The sheet has three logical sections separated by embedded header rows:
  1. Camp Programs (schedule & pricing)
  2. Add-Ons (per day extras)
  3. Camp Details (key-value facts)
"""

import pandas as pd
from .base import BaseParser


class AeroCampParser(BaseParser):
    SHEET_NAME = "Aero Camp"
    OUTPUT_FILE = "aero_camp.md"

    def to_markdown(self) -> str:
        df = self.df.reset_index(drop=True)
        lines = ["# Aero Camp", ""]

        # Find the row indices of the two section dividers
        addon_idx = df.index[
            df.iloc[:, 1].astype(str).str.strip() == "ADD-ONS (PER DAY)"
        ]
        detail_idx = df.index[
            df.iloc[:, 1].astype(str).str.strip() == "CAMP DETAILS"
        ]

        end_programs = addon_idx[0] if len(addon_idx) else len(df)
        end_addons = detail_idx[0] if len(detail_idx) else len(df)

        # ---- Section 1: Camp Programs (rows before ADD-ONS divider) ----
        programs_df = df.loc[:end_programs - 1]
        programs_df = programs_df[programs_df["chunk_id"].notna()]

        if not programs_df.empty:
            lines += ["## Camp Programs", ""]
            lines.append("| Program | Schedule | Price | Notes |")
            lines.append("|---------|----------|-------|-------|")
            for _, row in programs_df.iterrows():
                program = self.val(row.get("program", ""))
                schedule = self.val(row.get("schedule", ""))
                price = self.val(row.get("price", ""))
                notes = self.val(row.get("notes", ""))
                if program:
                    lines.append(f"| {program} | {schedule} | {price} | {notes} |")
            lines.append("")

        # ---- Section 2: Add-Ons (rows between ADD-ONS and CAMP DETAILS dividers) ----
        if len(addon_idx):
            # skip the divider row (+1) and the embedded column-header row (+2)
            addon_rows = df.loc[addon_idx[0] + 2 : end_addons - 1]
            addon_rows = addon_rows[addon_rows["chunk_id"].notna()]

            if not addon_rows.empty:
                lines += ["## Add-Ons (Per Day)", ""]
                for _, row in addon_rows.iterrows():
                    add_on = self.val(row.iloc[1])   # 'program' col repurposed
                    price = self.val(row.iloc[2])    # 'schedule' col repurposed
                    if add_on and price:
                        lines.append(f"- **{add_on}:** {price}")
                lines.append("")

        # ---- Section 3: Camp Details (rows after CAMP DETAILS divider) ----
        if len(detail_idx):
            detail_rows = df.loc[detail_idx[0] + 2:]   # skip divider + header
            detail_rows = detail_rows[detail_rows["chunk_id"].notna()]

            if not detail_rows.empty:
                lines += ["## Camp Details", ""]
                for _, row in detail_rows.iterrows():
                    field = self.val(row.iloc[1])   # 'program' col repurposed
                    value = self.val(row.iloc[2])   # 'schedule' col repurposed
                    if field and value:
                        lines.append(f"- **{field}:** {value}")
                lines.append("")

        return "\n".join(lines)
