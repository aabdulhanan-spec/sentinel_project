"""Conservative NL2SQL translator with schema-aware graceful degradation.

The built-in translator intentionally supports common operational questions. For
production LLM translation, keep the same read-only validator and parameterized
execution boundary; never execute raw model output without validation.
"""
import re
from .database import Database

class NL2SQL:
    def __init__(self, db: Database):
        self.db = db

    def translate(self, question: str) -> tuple[str, tuple] | None:
        q = question.lower().strip()
        schema = self.db.schema()
        if not any(t in schema for t in ("servers", "logs")):
            return None
        if any(x in q for x in ("ceo", "favorite color", "weather", "stock price", "payroll")):
            return None
        if "server" in q and any(x in q for x in ("list", "show", "status", "health", "cpu", "memory", "utilization")):
            cols = "server_id, hostname, region, status, cpu_usage_percent, memory_usage_percent"
            if "highest cpu" in q or "top cpu" in q:
                return (f"SELECT {cols} FROM servers ORDER BY cpu_usage_percent DESC LIMIT 10", ())
            if "highest memory" in q or "top memory" in q:
                return (f"SELECT {cols} FROM servers ORDER BY memory_usage_percent DESC LIMIT 10", ())
            return (f"SELECT {cols} FROM servers ORDER BY server_id", ())
        if "log" in q or "error" in q or "warning" in q or "warn" in q:
            if "error" in q:
                return ("SELECT log_id, server_id, timestamp, log_level, message, service_name FROM logs WHERE log_level = ? ORDER BY timestamp DESC LIMIT 100", ("ERROR",))
            if "warning" in q or "warn" in q:
                return ("SELECT log_id, server_id, timestamp, log_level, message, service_name FROM logs WHERE log_level = ? ORDER BY timestamp DESC LIMIT 100", ("WARN",))
            return ("SELECT log_id, server_id, timestamp, log_level, message, service_name FROM logs ORDER BY timestamp DESC LIMIT 100", ())
        if "incident" in q:
            if "incidents" not in schema:
                return None
            return ("SELECT * FROM incidents LIMIT 100", ())
        return None

    def answer(self, question: str) -> dict:
        translated = self.translate(question)
        if translated is None:
            return {"supported": False, "message": "I cannot answer that from the available telemetry schema. Supported data includes servers and logs; no matching table or supported query was found.", "sql": None, "rows": []}
        sql, params = translated
        rows = self.db.query(sql, params)
        return {"supported": True, "message": f"Returned {len(rows)} row(s) from the telemetry database.", "sql": sql, "rows": rows}
