"""MCP standardized gateway. All agent-facing system access is exposed here."""
from .database import Database
from .nl2sql import NL2SQL
from .config import settings

class SentinelGateway:
    def __init__(self, db):
        self.db, self.nl2sql = db, NL2SQL(db)
    def get_system_logs(self, limit: int = 100):
        limit = max(1, min(int(limit), 500))
        return self.db.query("SELECT log_id, server_id, timestamp, log_level, message, service_name FROM logs ORDER BY timestamp DESC LIMIT ?", (limit,))
    def execute_system_command(self, command: str):
        # Deliberately simulated/read-only: never invokes subprocess or shell.
        if command.strip().lower() in {"uptime", "status", "health"}:
            return {"simulated": True, "command": command, "result": self.db.query("SELECT * FROM servers")}
        return {"simulated": True, "blocked": True, "message": "Only read-only status commands are supported."}
    def query_knowledge_base(self, query: str):
        q = query.lower()
        docs = [("cpu", "High CPU can result from query load, runaway workers, or traffic spikes."),
                ("memory", "High memory can result from cache growth, connection accumulation, or a memory leak."),
                ("database", "For database saturation, inspect active queries, connection counts, and deployment changes.")]
        hits = [d for d in docs if any(term in q for term in d[0].split())]
        return [d[1] for d in hits] or ["No matching knowledge-base entry."]
    def query_database(self, nl_query: str):
        return self.nl2sql.answer(nl_query)

def create_mcp_server(gateway=None):
    """Create the MCP server and register the four required tools."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("Install MCP with `pip install -r requirements.txt` to run the MCP server.") from exc
    gateway = gateway or SentinelGateway(Database(settings.database_path))
    mcp = FastMCP("Sentinel System Gateway")
    @mcp.tool()
    def get_system_logs(limit: int = 100):
        """Retrieve recent system logs (maximum 500 rows)."""
        return gateway.get_system_logs(limit)
    @mcp.tool()
    def execute_system_command(command: str):
        """Run a simulated, read-only status command; shell execution is disabled."""
        return gateway.execute_system_command(command)
    @mcp.tool()
    def query_knowledge_base(query: str):
        """Retrieve relevant operational troubleshooting guidance."""
        return gateway.query_knowledge_base(query)
    @mcp.tool()
    def query_database(nl_query: str):
        """Translate a natural-language telemetry question to safe SQL and execute it."""
        return gateway.query_database(nl_query)
    return mcp

if __name__ == "__main__":
    create_mcp_server().run()
