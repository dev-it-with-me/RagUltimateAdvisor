"""
Database initialization script for Ultimate Advisor.

This script creates the database tables if they don't exist and handles schema changes.
"""

import logging
import sys
from pathlib import Path

from sqlalchemy import inspect, text
from sqlmodel import SQLModel, create_engine

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_tables_exist(engine) -> dict[str, bool]:
    """Check which tables already exist in the database.

    Returns:
        dict: Table name -> exists boolean
    """
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    expected_tables = {
        "queryhistory": False,
        "sourcedocumenthistory": False,
    }

    for table in existing_tables:
        if table.lower() in expected_tables:
            expected_tables[table.lower()] = True

    return expected_tables


def get_table_info(engine, table_name: str) -> dict:
    """Get information about an existing table."""
    inspector = inspect(engine)
    try:
        columns = inspector.get_columns(table_name)
        return {"columns": [col["name"] for col in columns]}
    except Exception as e:
        logger.warning(f"Could not get info for table {table_name}: {e}")
        return {"columns": []}


def prompt_user_action(table_status: dict[str, bool]) -> str:
    """Prompt user for action when tables exist or don't exist.

    Returns:
        str: User choice ('create', 'recreate', 'migrate', 'abort')
    """
    existing_tables = [name for name, exists in table_status.items() if exists]
    missing_tables = [name for name, exists in table_status.items() if not exists]

    if not existing_tables and not missing_tables:
        logger.info("All expected tables already exist and are up to date.")
        return "none"

    if missing_tables and not existing_tables:
        logger.info(f"Missing tables: {missing_tables}")
        response = input("Create missing tables? (y/n): ").lower().strip()
        return "create" if response == "y" else "abort"

    if existing_tables and not missing_tables:
        logger.info(f"All tables exist: {existing_tables}")
        print("\nOptions:")
        print("(r) Recreate all tables (DROP and CREATE - will lose all data)")
        print("(k) Keep existing tables (no changes)")
        print("(a) Abort")

        while True:
            response = input("Choose action (r/k/a): ").lower().strip()
            if response in ["r", "k", "a"]:
                action_map = {"r": "recreate", "k": "none", "a": "abort"}
                return action_map[response]
            print("Invalid choice. Please enter 'r', 'k', or 'a'.")

    if existing_tables and missing_tables:
        logger.info(f"Existing tables: {existing_tables}")
        logger.info(f"Missing tables: {missing_tables}")
        print("\nOptions:")
        print("(c) Create missing tables only")
        print("(r) Recreate all tables (DROP and CREATE - will lose all data)")
        print("(a) Abort")

        while True:
            response = input("Choose action (c/r/a): ").lower().strip()
            if response in ["c", "r", "a"]:
                action_map = {"c": "create", "r": "recreate", "a": "abort"}
                return action_map[response]
            print("Invalid choice. Please enter 'c', 'r', or 'a'.")

    return "abort"


def confirm_destructive_action() -> bool:
    """Get confirmation for destructive operations."""
    print("\n⚠️  WARNING: This will DELETE ALL EXISTING DATA in the tables!")
    response = input("Are you absolutely sure? Type 'yes' to confirm: ").strip()
    return response.lower() == "yes"


def init_database():
    """Initialize database tables with user prompts for safety."""
    try:
        logger.info("Connecting to database...")
        engine = create_engine(settings.database_url, echo=False)

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")

        table_status = check_tables_exist(engine)
        logger.info(f"Table status: {table_status}")

        action = prompt_user_action(table_status)

        if action == "abort":
            logger.info("Operation aborted by user")
            return

        if action == "none":
            logger.info("No changes needed")
            return

        if action == "recreate":
            if not confirm_destructive_action():
                logger.info("Operation cancelled by user")
                return

            logger.info("Dropping all tables...")
            SQLModel.metadata.drop_all(engine)
            logger.info("Creating all tables from scratch...")
            SQLModel.metadata.create_all(engine)
            logger.info("✅ Database tables recreated successfully")

        elif action == "create":
            logger.info("Creating missing tables...")
            SQLModel.metadata.create_all(engine)
            logger.info("✅ Missing tables created successfully")

        final_status = check_tables_exist(engine)
        logger.info(f"Final table status: {final_status}")

        for table_name, exists in final_status.items():
            if exists:
                info = get_table_info(engine, table_name)
                logger.info(f"Table '{table_name}' columns: {info.get('columns', [])}")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("Ultimate Advisor Database Initialization")
    print("=" * 50)
    print(f"Database URL: {settings.database_url}")
    print()

    init_database()
    print("\nDatabase initialization completed!")
