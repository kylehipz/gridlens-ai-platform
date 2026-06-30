from __future__ import annotations

from sqlalchemy import text

from gridlens_db.database import create_database_engine


def seed_database() -> None:
    engine = create_database_engine()
    with engine.begin() as connection:
        connection.execute(text("select 1"))


def main() -> None:
    seed_database()


if __name__ == "__main__":
    main()
