"""Database initialization script for Ultimate Advisor.

This script initializes the database tables and handles schema changes
with user prompts for safety.
"""

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings  # type: ignore
from repositories import rag_repository  # type: ignore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def check_table_status() -> dict:
    """Check the current status of the vector table.

    Returns:
        dict: Status information about the table
    """
    status = {
        "exists": False,
        "count": 0,
        "embedding_dim": None,
        "expected_dim": None,
        "dimension_mismatch": False,
    }

    if not rag_repository.engine:
        logger.error("Database engine not available")
        return status

    # Get expected dimension from model
    if rag_repository._actual_embed_dim:
        status["expected_dim"] = rag_repository._actual_embed_dim
    else:
        status["expected_dim"] = settings.EMBED_DIM

    try:
        from sqlalchemy import text

        with rag_repository.engine.connect() as conn:
            # Check if table exists
            exists_result = conn.execute(
                text("SELECT 1 FROM information_schema.tables WHERE table_name = :tbl"),
                {"tbl": settings.VECTOR_TABLE_NAME},
            ).fetchone()

            if exists_result:
                status["exists"] = True

                # Get document count
                count_result = conn.execute(
                    text(f"SELECT COUNT(*) FROM {settings.VECTOR_TABLE_NAME}")
                ).fetchone()
                status["count"] = int(count_result[0]) if count_result else 0

                # Get embedding dimension from table schema
                dim_result = conn.execute(
                    text(
                        "SELECT atttypmod FROM pg_attribute a "
                        "JOIN pg_class c ON a.attrelid=c.oid "
                        "JOIN pg_namespace n ON c.relnamespace=n.oid "
                        "WHERE c.relname=:tbl AND a.attname='embedding' "
                        "AND a.attnum>0 AND NOT a.attisdropped"
                    ),
                    {"tbl": settings.VECTOR_TABLE_NAME},
                ).fetchone()

                if dim_result and dim_result[0] is not None:
                    # pgvector stores dimension in atttypmod directly for vector types
                    status["embedding_dim"] = dim_result[0]
                    status["dimension_mismatch"] = (
                        status["embedding_dim"] != status["expected_dim"]
                    )

    except Exception as e:
        logger.error(f"Error checking table status: {e}")

    return status


def prompt_user_action(status: dict) -> str:
    """Prompt user for action based on table status.

    Args:
        status: Table status information

    Returns:
        str: User's chosen action
    """
    print("\n" + "=" * 60)
    print("DATABASE INITIALIZATION - TABLE STATUS")
    print("=" * 60)

    if not status["exists"]:
        print("✓ No existing vector table found")
        print("  → Will create new table with correct schema")
        return "create"

    print(f"Table '{settings.VECTOR_TABLE_NAME}' exists:")
    print(f"  - Documents: {status['count']}")
    print(f"  - Current embedding dimension: {status['embedding_dim']}")
    print(f"  - Expected embedding dimension: {status['expected_dim']}")

    if status["dimension_mismatch"]:
        print("\n⚠️  DIMENSION MISMATCH DETECTED!")
        print(
            f"   Current: {status['embedding_dim']}, Expected: {status['expected_dim']}"
        )

        if status["count"] == 0:
            print("   Table is empty - safe to recreate")
            while True:
                choice = (
                    input("\nRecreate table with correct dimensions? (y/n): ")
                    .lower()
                    .strip()
                )
                if choice in ["y", "yes"]:
                    return "recreate"
                elif choice in ["n", "no"]:
                    return "keep"
                print("Please enter 'y' or 'n'")
        else:
            print(f"   Table contains {status['count']} documents")
            print("\nOptions:")
            print("  (r) Recreate from scratch (DELETES ALL DATA)")
            print("  (k) Keep existing table (may cause embedding errors)")

            while True:
                choice = input("Choose action (r/k): ").lower().strip()
                if choice in ["r", "recreate"]:
                    print(
                        f"\n⚠️  WARNING: This will DELETE all {status['count']} documents!"
                    )
                    confirm = input("Are you sure? Type 'DELETE' to confirm: ")
                    if confirm == "DELETE":
                        return "recreate"
                    else:
                        print("Operation cancelled")
                        continue
                elif choice in ["k", "keep"]:
                    return "keep"
                print("Please enter 'r' or 'k'")
    else:
        print("✓ Table dimensions match model requirements")
        if status["count"] > 0:
            print(f"✓ Table contains {status['count']} documents")
        return "keep"


def init_database() -> bool:
    """Initialize database tables with user prompts for safety.

    Returns:
        bool: True if successful
    """
    try:
        logger.info("Starting database initialization")

        # Check repository health
        health = rag_repository.health_check(require_index=False)
        if not health["database"]:
            logger.error("Database connection failed")
            return False

        if not health["models"]:
            logger.error("Model setup failed")
            return False

        # Check current table status
        status = check_table_status()
        action = prompt_user_action(status)

        if action == "create":
            logger.info("Creating new vector table")
            embed_dim = rag_repository._actual_embed_dim or settings.EMBED_DIM
            rag_repository._ensure_vector_table_exists(embed_dim)
            print("✓ Vector table created successfully")

        elif action == "recreate":
            logger.info("Recreating vector table")
            success = rag_repository.force_recreate_index()
            if success:
                print("✓ Vector table recreated successfully")
            else:
                print("✗ Failed to recreate vector table")
                return False

        elif action == "keep":
            print("✓ Keeping existing table")

        # Verify final state
        final_status = check_table_status()
        print("\nFinal status:")
        print(f"  - Table exists: {final_status['exists']}")
        print(f"  - Document count: {final_status['count']}")
        print(f"  - Embedding dimension: {final_status['embedding_dim']}")
        print(f"  - Dimension match: {not final_status['dimension_mismatch']}")

        return True

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def main() -> None:
    """Main entry point."""
    try:
        logger.info("=" * 50)
        logger.info("Ultimate Advisor - Database Initialization")
        logger.info("=" * 50)

        success = init_database()

        if success:
            logger.info("✓ Database initialization completed successfully")
            sys.exit(0)
        else:
            logger.error("✗ Database initialization failed")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
