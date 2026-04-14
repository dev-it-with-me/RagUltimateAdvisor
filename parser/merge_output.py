"""
Merge all Markdown files from a location folder into a single file.

Usage:
    python merge_output.py output/scarborough
    python merge_output.py output/london --output merged_london
"""

import argparse
from pathlib import Path


def merge_markdown_files(location_dir: str, output_name: str = None) -> tuple[Path, Path]:
    """
    Merge all Markdown files from a location directory.

    Args:
        location_dir: Path to location folder (e.g., output/scarborough)
        output_name: Optional output filename (without extension)

    Returns:
        Tuple of (markdown_path, text_path)
    """
    location_path = Path(location_dir)

    if not location_path.exists():
        raise FileNotFoundError(f"Directory not found: {location_dir}")

    # Get location name for default output filename
    location_name = location_path.name
    output_name = output_name or f"merged_{location_name}"

    # Find all markdown files
    md_files = sorted(location_path.rglob("*.md"))

    if not md_files:
        raise ValueError(f"No Markdown files found in {location_dir}")

    # Merge content
    merged_lines = []
    merged_lines.append(f"# {location_name.replace('-', ' ').title()} - Complete Content")
    merged_lines.append("")
    merged_lines.append(f"*Merged from {len(md_files)} files*")
    merged_lines.append("")
    merged_lines.append("---")
    merged_lines.append("")

    for md_file in md_files:
        # Get relative path for section header
        relative_path = md_file.relative_to(location_path)
        folder_name = relative_path.parent.name if relative_path.parent.name else "Root"

        merged_lines.append(f"## Source: {folder_name}/{md_file.name}")
        merged_lines.append("")

        # Read and append content
        content = md_file.read_text(encoding="utf-8").strip()
        merged_lines.append(content)
        merged_lines.append("")
        merged_lines.append("---")
        merged_lines.append("")

    merged_content = "\n".join(merged_lines)

    # Save merged markdown
    md_output = location_path / f"{output_name}.md"
    md_output.write_text(merged_content, encoding="utf-8")

    # Save as plain text (same content works for both)
    txt_output = location_path / f"{output_name}.txt"
    txt_output.write_text(merged_content, encoding="utf-8")

    return md_output, txt_output


def main():
    parser = argparse.ArgumentParser(description="Merge Markdown files from a location folder")
    parser.add_argument("location_dir", help="Path to location folder (e.g., output/scarborough)")
    parser.add_argument("--output", "-o", help="Output filename (without extension)")
    args = parser.parse_args()

    md_path, txt_path = merge_markdown_files(args.location_dir, args.output)

    print(f"Merged {len(list(Path(args.location_dir).rglob('*.md')) ) - 1} files")
    print(f"Markdown: {md_path}")
    print(f"Text:     {txt_path}")


if __name__ == "__main__":
    main()
