# Sentinel – The Autonomous System Health Guardian (v2.0)

A modular reference implementation for the supplied brief: four specialized agents, a LangGraph circular workflow, an MCP gateway, SQLite NL2SQL, safety guardrails, and an outage post-mortem.

## Important dataset finding
The supplied database contains **`servers` (2 rows)** and **`logs` (5,000 rows)**. It does **not** contain the `incidents` table mentioned in the brief. All 5,000 log messages are the generic text `Sample log message`, all belong to `SRV-001`, and the only service is `Auth-Service`. The server records show `SRV-002` (`db-prod-1`) at **88.5% CPU** and **92.3% memory**. Consequently, the report treats high resource utilization as an observed anomaly but does not invent a root cause from the generic logs.

## Requirements
- Python 3.10+
- Core local demo: Python standard library only
- Optional integrations: install `requirements.txt`; CrewAI, LangGraph, MCP, LangSmith and LangChain are optional imports.

## Quick start
1. Create an environment: `python -m venv .venv`
2. Activate it and install optional integrations: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set `SENTINEL_DB_PATH`.
4. Put the supplied database at `data/system_telemetry.db` (or pass `--db /path/to/file`).
5. Run:
   - `python -m sentinel.main schema`
   - `python -m sentinel.main ask --question "Show server health"`
   - `python -m sentinel.main workflow`
   - `python -m unittest discover -s tests -v`

## Architecture
- **Monitor Agent:** evaluates CPU/memory thresholds and log-level counts.
- **Diagnostician Agent:** retrieves relevant troubleshooting guidance from the local knowledge base.
- **Remediation Agent:** produces simulated recommendations and blocks high-risk operations when recorded database CPU load is at/above the configured critical threshold.
- **Data Intelligence Agent:** implemented by `DataIntelligenceAgent` over `NL2SQL` and exposed through the MCP `query_database` tool. It supports bounded operational query templates and gracefully declines out-of-schema questions.
- **MCP gateway:** the agent-facing interface exposes only `get_system_logs`, `execute_system_command`, `query_knowledge_base`, and `query_database`.
- **LangGraph:** `build_langgraph()` compiles the monitor → diagnose → remediate → verify graph when LangGraph is installed. Failed verification routes to retry → diagnose. `run_local()` supplies an offline deterministic fallback.

## Safety and limitations
- Database connections use SQLite read-only URI mode.
- SQL accepts one `SELECT` statement only; no writes, DDL, multi-statement execution, or shell interpolation.
- `execute_system_command` is simulated and never invokes a shell.
- The current dataset's maximum server CPU is 88.5%; therefore the default 85% critical-load gate blocks high-risk remediation.
- The local workflow cannot actually heal a host because no host-control adapter or permission is supplied. Verification is observational and reports unresolved anomalies honestly.
- LangSmith tracing is enabled by setting `LANGCHAIN_TRACING_V2=true`, `LANGSMITH_API_KEY`, and the project name. LangGraph/LLM calls should be instrumented in the deployment environment; this local deterministic demo does not claim a hosted trace exists.

## Extending NL2SQL
Add explicit, schema-checked query templates in `NL2SQL.translate()`. If adding an LLM, require it to return SQL plus parameters, validate against an allowlist/AST, enforce row limits and read-only mode, then execute through `Database.query()`. Never execute arbitrary generated SQL.

## Components
| Module | Responsibility |
|---|---|
| `config.py` | Environment-backed thresholds and paths |
| `database.py` | Read-only SQLite access, schema discovery, safe query execution |
| `nl2sql.py` | Natural-language query mapping and graceful fallback |
| `agents.py` | Four roles, local implementations, optional CrewAI agent definitions |
| `orchestrator.py` | LangGraph graph and local circular workflow |
| `mcp_server.py` | Four MCP tools and safe gateway |
| `main.py` | CLI entry point |

## Deliverables
See `docs/post_mortem.md`, `docs/workflow.mmd`, and `docs/agent_hierarchy.mmd`.
