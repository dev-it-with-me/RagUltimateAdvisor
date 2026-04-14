"""
Base Parser class shared by all sheet parsers.
"""

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd


class BaseParser(ABC):
    """Abstract base for all sheet parsers. Each subclass handles one worksheet."""

    SHEET_NAME: str = ""
    OUTPUT_FILE: str = ""  # e.g. "jump_prices.md"

    def __init__(self, excel_file: str, output_dir: str = "output"):
        self.excel_file = excel_file
        self.output_dir = output_dir
        self._df: pd.DataFrame | None = None

    @property
    def df(self) -> pd.DataFrame:
        if self._df is None:
            self._df = pd.read_excel(self.excel_file, sheet_name=self.SHEET_NAME)
        return self._df

    def write_markdown(self, content: str) -> Path:
        out_dir = Path(self.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        file_path = out_dir / self.OUTPUT_FILE
        file_path.write_text(content, encoding="utf-8")
        return file_path

    @abstractmethod
    def to_markdown(self) -> str:
        """Convert the sheet data to a Markdown string."""

    def parse(self) -> dict:
        content = self.to_markdown()
        if content.strip():
            path = self.write_markdown(content)
            return {"output_file": self.OUTPUT_FILE, "path": str(path)}
        return {"output_file": self.OUTPUT_FILE, "path": None}

    @staticmethod
    def val(v) -> str:
        """Return string value or empty string if NaN/None."""
        if pd.isna(v) or v is None:
            return ""
        return str(v).strip()
