# Capturing the required LangSmith NL2SQL trace

1. Configure `LANGCHAIN_TRACING_V2=true`, `LANGSMITH_API_KEY`, and `LANGSMITH_PROJECT` in `.env`.
2. Run the application in the environment where LangGraph/LangChain instrumentation is enabled.
3. Submit the NL2SQL request `Show server health` through the Data Intelligence Agent/MCP `query_database` tool.
4. Open the LangSmith project and select the trace showing the user question, translation step, generated SQL, database tool call, and result.
5. Capture a screenshot that includes the trace name and the relevant input/output panels. Do not include API keys or other secrets.

The supplied project includes the trace capture procedure, but cannot create an authentic hosted trace without your LangSmith credentials and execution environment.
