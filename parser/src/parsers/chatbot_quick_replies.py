"""Parser for the 'Chatbot Quick Replies' sheet."""

import pandas as pd
from .base import BaseParser


class ChatbotQuickRepliesParser(BaseParser):
    SHEET_NAME = "Chatbot Quick Replies"
    OUTPUT_FILE = "chatbot_quick_replies.md"

    def to_markdown(self) -> str:
        lines = ["# Chatbot Quick Replies", ""]

        for _, row in self.df.iterrows():
            intent = self.val(row.get("intent", ""))
            sample_question = self.val(row.get("sample_question", ""))
            response = self.val(row.get("response", ""))
            if not intent and not sample_question:
                continue

            label = intent.replace("_", " ").title()
            lines += [f"## {label}", ""]
            if sample_question:
                lines += [f"**Sample question:** {sample_question}", ""]
            if response:
                lines += [f"**Response:** {response}", ""]

        return "\n".join(lines)
