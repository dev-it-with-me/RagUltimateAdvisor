import hashlib
import json
import logging
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
META_FILE = DATA_DIR / ".sheet_meta.json"


def _xlsx_url(spreadsheet_id: str) -> str:
    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=xlsx"


def _fetch_xlsx(spreadsheet_id: str) -> bytes:
    url = _xlsx_url(spreadsheet_id)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content


def _content_hash(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()


def _load_meta() -> dict:
    if META_FILE.exists():
        with open(META_FILE) as f:
            return json.load(f)
    return {}


def _save_meta(meta: dict) -> None:
    with open(META_FILE, "w") as f:
        json.dump(meta, f, indent=2)


def _output_path(spreadsheet_id: str) -> Path:
    return DATA_DIR / f"{spreadsheet_id}.xlsx"


def download_sheet(
    spreadsheet_id: str,
    force: bool = False,
) -> Path | None:
    """
    Downloads a public Google Sheet as an Excel file (.xlsx) with all worksheets.
    Skips download if the content hasn't changed since last run.

    Args:
        spreadsheet_id: The ID from the sheet URL:
                        https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit
        force:          If True, download even if no changes detected.

    Returns:
        Path to the saved .xlsx file, or None if no update was needed.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Fetching spreadsheet %s", spreadsheet_id)
    content = _fetch_xlsx(spreadsheet_id)
    new_hash = _content_hash(content)

    meta = _load_meta()
    out_path = _output_path(spreadsheet_id)

    if not force and meta.get(spreadsheet_id) == new_hash and out_path.exists():
        logger.info("No changes detected. Skipping save.")
        return None

    with open(out_path, "wb") as f:
        f.write(content)

    meta[spreadsheet_id] = new_hash
    _save_meta(meta)

    logger.info("Saved to %s", out_path)
    return out_path


if __name__ == "__main__":
    SPREADSHEET_ID = "1SGK35TNPDZ8ipEsCe9w1wCmFQNBOTWo1b0ZaWVIa14s"

    path = download_sheet(SPREADSHEET_ID)
    if path:
        print(f"Downloaded and saved to: {path}")
    else:
        print("Sheet is up to date. No download needed.")
