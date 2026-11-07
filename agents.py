"""Four specialized agent definitions and lightweight local implementations.

CrewAI is optional for local/demo operation. When installed, create_crewai_agents()
returns actual CrewAI Agent objects; the local workflow remains testable offline.
"""
from dataclasses import dataclass

@dataclass
class AgentResult:
    agent: str
    summary: str
    evidence: list

class DataIntelligenceAgent:
    """Answer administrator questions by translating them into safe, read-only SQL."""
    def __init__(self, db):
        from .nl2sql import NL2SQL
        self.nl2sql = NL2SQL(db)
    def run(self, natural_language_query: str):
        """Return support status, generated SQL, and query results (or a graceful refusal)."""
        return self.nl2sql.answer(natural_language_query)

class MonitorAgent:
    """Inspect server metrics and log severity for threshold breaches."""
    def __init__(self, db, cpu_threshold=85.0, memory_threshold=90.0):
        self.db, self.cpu_threshold, self.memory_threshold = db, cpu_threshold, memory_threshold
    def run(self):
        servers = self.db.query("SELECT * FROM servers ORDER BY server_id")
        anomalies = []
        for s in servers:
            if s.get("cpu_usage_percent", 0) >= self.cpu_threshold:
                anomalies.append({"type":"high_cpu", **s})
            if s.get("memory_usage_percent", 0) >= self.memory_threshold:
                anomalies.append({"type":"high_memory", **s})
        levels = self.db.query("SELECT log_level, COUNT(*) AS count FROM logs GROUP BY log_level")
        return AgentResult("Monitor Agent", f"Detected {len(anomalies)} metric anomaly/anomalies.", anomalies + levels)

class DiagnosticianAgent:
    """Use a small local knowledge base (RAG-style retrieval) to suggest causes."""
    KNOWLEDGE = [
        ("high_cpu", "Sustained CPU pressure may indicate query load, runaway workers, or traffic spikes. Check process and query telemetry before changing capacity."),
        ("high_memory", "High memory pressure may indicate cache growth, connection accumulation, or a memory leak. Inspect trends and process-level metrics."),
        ("high_cpu+high_memory", "Combined CPU and memory pressure on a database host can indicate workload saturation. Review active queries, connection counts, and recent deployments.")
    ]
    def run(self, monitor_result):
        kinds = {x.get("type") for x in monitor_result.evidence if isinstance(x, dict)}
        key = "high_cpu+high_memory" if {"high_cpu","high_memory"} <= kinds else ("high_cpu" if "high_cpu" in kinds else ("high_memory" if "high_memory" in kinds else ""))
        match = next((v for k,v in self.KNOWLEDGE if k == key), "No threshold breach detected. Continue routine monitoring.")
        return AgentResult("Diagnostician Agent", match, [{"knowledge_key": key or "normal"}])

class RemediationAgent:
    """Propose safe, simulated actions; never executes host commands."""
    HIGH_RISK = {"system_reboot", "shutdown", "format_disk", "kill_database"}
    def __init__(self, db, critical_load=85.0):
        self.db, self.critical_load = db, critical_load
    def run(self, diagnosis):
        load = self.db.database_load()
        if load >= self.critical_load:
            return AgentResult("Remediation Agent", "Blocked high-risk remediation because database load is critical; only observation and escalation are permitted.", [{"blocked": sorted(self.HIGH_RISK), "db_load": load, "simulated": True}])
        return AgentResult("Remediation Agent", "No destructive command executed. Recommended actions: inspect top queries, review connection pool, and scale only after operator approval.", [{"action":"operator_review", "simulated": True, "db_load": load}])

def create_crewai_agents():
    """Return CrewAI agent objects if CrewAI is installed; otherwise explain clearly."""
    try:
        from crewai import Agent
    except ImportError as exc:
        raise RuntimeError("Install optional dependencies with `pip install -r requirements.txt` to enable CrewAI objects.") from exc
    return [
        Agent(role="Monitor Agent", goal="Detect anomalies from telemetry and logs.", backstory="A precise observability specialist.", verbose=True),
        Agent(role="Diagnostician Agent", goal="Find likely root causes using the knowledge base.", backstory="A cautious SRE diagnostician.", verbose=True),
        Agent(role="Remediation Agent", goal="Propose safe fixes and verify outcomes.", backstory="A safety-first incident responder.", verbose=True),
        Agent(role="Data Intelligence Agent", goal="Answer natural-language questions using read-only SQL.", backstory="A schema-grounded data analyst.", verbose=True),
    ]
