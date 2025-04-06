import sqlite3
from typing import Any, Optional


def add_column_if_not_exists(
    sqlite_conn: sqlite3.Connection,
    table_name: str,
    col_name: str,
    col_type: str,
    default: Optional[Any] = None,
) -> None:
    try:
        cur = sqlite_conn.execute(f"PRAGMA table_info({table_name})")
        for row in cur.fetchall():
            row_col_name = row[1]
            if row_col_name == col_name:
                cur.close()
                return
        if default is not None:
            cur.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} DEFAULT {default}",
            )
        else:
            cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")
        cur.close()
        sqlite_conn.commit()

    except Exception as e:
        print("SSSSSSSSSS")
        raise e
