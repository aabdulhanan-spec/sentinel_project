"""Read-only SQLite access and schema introspection."""
from pathlib import Path
import sqlite3
from typing import Any

ALLOWED_TABLES = {"servers", "logs", "incidents"}

class Database:
    def __init__(self, path: str):
        self.path = str(path)
        if not Path(self.path).exists():
            raise FileNotFoundError(f"Telemetry database not found: {self.path}")

    def connect(self):
        # Use a proper file URI and close the connection explicitly to avoid Windows
        # file locking issues when the temp DB is cleaned up during tests.
        path = Path(self.path).resolve()
        return sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)

    def schema(self) -> dict[str, list[str]]:
        conn = self.connect()
        try:
            names = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
            return {name: [r[1] for r in conn.execute(f'PRAGMA table_info("{name}")')]
                    for name in names if name in ALLOWED_TABLES}
        finally:
            conn.close()

    def query(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        # Only a single SELECT statement is accepted. Parameters must be bound separately.
        statement = sql.strip().rstrip(";")
        if not statement.lower().startswith("select") or ";" in statement:
            raise ValueError("Only one read-only SELECT statement is allowed.")
        conn = self.connect()
        try:
            conn.row_factory = sqlite3.Row
            return [dict(row) for row in conn.execute(statement, params).fetchall()]
        finally:
            conn.close()

    def database_load(self) -> float:
        """Estimate DB load from the highest recorded CPU utilization."""
        rows = self.query("SELECT MAX(cpu_usage_percent) AS load FROM servers")
        return float(rows[0]["load"] or 0) if rows else 0.0
