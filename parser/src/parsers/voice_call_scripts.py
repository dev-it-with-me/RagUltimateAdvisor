"""Parser for the 'Voice Call Scripts' sheet."""

import pandas as pd
from .base import BaseParser


class VoiceCallScriptsParser(BaseParser):
    SHEET_NAME = "Voice Call Scripts"
    OUTPUT_FILE = "voice_call_scripts.md"

    def to_markdown(self) -> str:
        lines = ["# Voice Call Scripts", ""]

        for _, row in self.df.iterrows():
            scenario = self.val(row.get("scenario", ""))
            script = self.val(row.get("script", ""))
            notes = self.val(row.get("notes", ""))
            if not scenario and not script:
                continue

            label = scenario.replace("_", " ").title()
            lines += [f"## {label}", ""]
            if script:
                lines += [f"> {script}", ""]
            if notes:
                lines += [f"*Note: {notes}*", ""]

        return "\n".join(lines)
