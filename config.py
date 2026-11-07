"""Central configuration and environment loading."""
from dataclasses import dataclass
import os
from pathlib import Path

@dataclass(frozen=True)
class Settings:
    database_path: str = os.getenv("SENTINEL_DB_PATH", "data/system_telemetry.db")
    cpu_threshold: float = float(os.getenv("CPU_THRESHOLD", "85"))
    memory_threshold: float = float(os.getenv("MEMORY_THRESHOLD", "90"))
    critical_db_load: float = float(os.getenv("CRITICAL_DB_LOAD", "85"))
    langsmith_project: str = os.getenv("LANGSMITH_PROJECT", "sentinel-health-guardian")
    enable_langsmith: bool = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"

settings = Settings()
