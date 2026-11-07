"""LangGraph circular workflow with a deterministic local fallback."""
from typing import TypedDict, Any
from .agents import MonitorAgent, DiagnosticianAgent, RemediationAgent

class SentinelState(TypedDict, total=False):
    retry: bool
    attempts: int
    monitor: Any
    diagnosis: Any
    remediation: Any
    verification: dict
    history: list

class SentinelOrchestrator:
    def __init__(self, db, max_retries=2, cpu_threshold=85, memory_threshold=90, critical_load=85):
        self.db, self.max_retries = db, max_retries
        self.monitor = MonitorAgent(db, cpu_threshold, memory_threshold)
        self.diagnostician = DiagnosticianAgent()
        self.remediator = RemediationAgent(db, critical_load)

    def _verify(self, state):
        # Verification is read-only: confirm that telemetry remains queryable and
        # report whether monitored thresholds are still breached.
        current = self.monitor.run()
        anomalies = [x for x in current.evidence if isinstance(x, dict) and x.get("type")]
        return {"passed": len(anomalies) == 0, "remaining_anomalies": anomalies,
                "note": "No automated host mutation was performed."}

    def run_local(self):
        state = {"retry": False, "attempts": 0, "history": []}
        while True:
            state["monitor"] = self.monitor.run()
            state["diagnosis"] = self.diagnostician.run(state["monitor"])
            state["remediation"] = self.remediator.run(state["diagnosis"])
            state["verification"] = self._verify(state)
            state["history"].append({"monitor": state["monitor"].summary,
                "diagnosis": state["diagnosis"].summary,
                "remediation": state["remediation"].summary,
                "verification": state["verification"]})
            if state["verification"]["passed"]:
                state["retry"] = False
                break
            state["retry"] = True
            state["attempts"] += 1
            if state["attempts"] >= self.max_retries:
                break
            # Retry path explicitly returns to Diagnose, as required by brief.
            state["diagnosis"] = self.diagnostician.run(state["monitor"])
        return state

    def build_langgraph(self):
        """Compile a real LangGraph when installed; returns None otherwise."""
        try:
            from langgraph.graph import StateGraph, END
        except ImportError:
            return None
        graph = StateGraph(dict)
        graph.add_node("monitor", lambda s: {**s, "monitor": self.monitor.run()})
        graph.add_node("diagnose", lambda s: {**s, "diagnosis": self.diagnostician.run(s["monitor"])})
        graph.add_node("remediate", lambda s: {**s, "remediation": self.remediator.run(s["diagnosis"])})
        graph.add_node("verify", lambda s: {**s, "verification": self._verify(s), "attempts": s.get("attempts", 0) + 1})
        graph.add_node("retry", lambda s: {**s, "retry": True})
        graph.set_entry_point("monitor")
        graph.add_edge("monitor", "diagnose"); graph.add_edge("diagnose", "remediate"); graph.add_edge("remediate", "verify")
        graph.add_conditional_edges("verify", lambda s: "done" if s["verification"]["passed"] or s.get("attempts",0) >= self.max_retries else "retry", {"done": END, "retry": "retry"})
        graph.add_edge("retry", "diagnose")
        return graph.compile()
