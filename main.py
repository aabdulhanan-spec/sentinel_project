"""Command-line entry point for Sentinel demo and NL2SQL."""
import argparse, json
from .config import settings
from .database import Database
from .mcp_server import SentinelGateway
from .orchestrator import SentinelOrchestrator

def main():
    parser = argparse.ArgumentParser(description="Sentinel autonomous system health guardian")
    parser.add_argument("command", choices=["workflow", "ask", "schema"])
    parser.add_argument("--question", default="Show server health")
    parser.add_argument("--db", default=settings.database_path)
    args = parser.parse_args()
    db = Database(args.db)
    if args.command == "schema":
        result = db.schema()
    elif args.command == "ask":
        result = SentinelGateway(db).query_database(args.question)
    else:
        state = SentinelOrchestrator(db).run_local()
        result = {"attempts": state["attempts"], "retry": state["retry"], "history": state["history"]}
    print(json.dumps(result, indent=2, default=lambda x: x.__dict__))

if __name__ == "__main__":
    main()
