"""Unit and integration tests for safety, NL2SQL, and workflow behavior."""
import sqlite3, tempfile, unittest
from pathlib import Path
from sentinel.database import Database
from sentinel.nl2sql import NL2SQL
from sentinel.mcp_server import SentinelGateway
from sentinel.orchestrator import SentinelOrchestrator

class SentinelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name) / "test.db")
        con = sqlite3.connect(self.path)
        con.executescript("""
        CREATE TABLE servers(server_id TEXT, hostname TEXT, region TEXT, status TEXT, cpu_usage_percent REAL, memory_usage_percent REAL);
        CREATE TABLE logs(log_id INTEGER PRIMARY KEY, server_id TEXT, timestamp TEXT, log_level TEXT, message TEXT, service_name TEXT);
        INSERT INTO servers VALUES('S1','db-1','test','ACTIVE',91,94);
        INSERT INTO logs VALUES(1,'S1','2026-01-01','ERROR','test error','db');
        """)
        con.commit(); con.close()
        self.db = Database(self.path)
    def tearDown(self): self.tmp.cleanup()
    def test_nl2sql_supported_and_read_only(self):
        result = NL2SQL(self.db).answer("Show server health")
        self.assertTrue(result["supported"]); self.assertEqual(len(result["rows"]), 1)
        with self.assertRaises(ValueError): self.db.query("DELETE FROM servers")
    def test_graceful_degradation(self):
        result = NL2SQL(self.db).answer("What is the CEO's favorite color?")
        self.assertFalse(result["supported"]); self.assertIsNone(result["sql"])
    def test_mcp_command_is_simulated(self):
        result = SentinelGateway(self.db).execute_system_command("system_reboot")
        self.assertTrue(result["blocked"]); self.assertTrue(result["simulated"])
    def test_critical_load_blocks_risky_remediation(self):
        state = SentinelOrchestrator(self.db, max_retries=1).run_local()
        self.assertIn("Blocked", state["remediation"].summary)
        self.assertFalse(state["verification"]["passed"])
    def test_schema(self):
        self.assertIn("servers", self.db.schema()); self.assertIn("logs", self.db.schema())

if __name__ == "__main__": unittest.main()
