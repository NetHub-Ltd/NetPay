"""Fail CI if the migrated database schema drifts from the ORM models."""

from sqlalchemy import create_engine, inspect
from sqlmodel import SQLModel

from app.config import get_settings
from app import models  # noqa: F401 — register every table in SQLModel.metadata


def main() -> None:
    database_url = get_settings().database_url
    sync_url = database_url.replace("sqlite+aiosqlite://", "sqlite://", 1).replace(
        "postgresql+asyncpg://", "postgresql+psycopg2://", 1
    )
    engine = create_engine(sync_url)
    try:
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        expected_tables = set(SQLModel.metadata.tables)
        missing_tables = expected_tables - existing_tables
        if missing_tables:
            raise SystemExit(f"Migrated database is missing tables: {sorted(missing_tables)}")

        mismatches: list[str] = []
        for table_name, table in SQLModel.metadata.tables.items():
            actual_columns = {column["name"] for column in inspector.get_columns(table_name)}
            expected_columns = set(table.columns.keys())
            if actual_columns != expected_columns:
                mismatches.append(
                    f"{table_name}: missing={sorted(expected_columns - actual_columns)}, "
                    f"unexpected={sorted(actual_columns - expected_columns)}"
                )
        if mismatches:
            raise SystemExit("Migrated schema does not match SQLModel metadata:\n" + "\n".join(mismatches))
        print(f"Schema check passed for {len(expected_tables)} tables.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
