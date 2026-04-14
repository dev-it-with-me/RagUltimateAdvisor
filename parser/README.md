New Project Structure

src/
├── __init__.py
└── parsers/
    ├── __init__.py
    ├── base.py           # BaseParser abstract class
    ├── data.py           # DataParser
    ├── location_json.py  # LocationJsonParser
    ├── pricing_table.py  # PricingTableParser
    └── promotions.py     # PromotionsParser

run_parsers.py            # CLI entry point
Usage
Import and use any parser:


from src import DataParser, LocationJsonParser, PricingTableParser, PromotionsParser

# Provide Excel file path and output directory
parser = DataParser("data/file.xlsx", "output")

# Parse all locations
stats = parser.parse()

# Or parse specific location
stats = parser.parse("scarborough")
Run all parsers via CLI:


python run_parsers.py                      # All locations
python run_parsers.py --location london    # Specific location