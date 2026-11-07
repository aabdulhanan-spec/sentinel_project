# Sentinel Post-Mortem: Database Host Resource Pressure

**Incident type:** Simulated infrastructure health event  
**Evidence source:** Supplied `system_telemetry.db`  
**Status:** Anomaly detected; root cause not established; remediation safely withheld

## 1. Executive summary
Sentinel identified a resource-pressure condition on `SRV-002` (`db-prod-1`, region `US-West`): CPU utilization is **88.5%** and memory utilization is **92.3%**. These values exceed Sentinel's default alert thresholds of 85% CPU and 90% memory. The Remediation Agent blocked high-risk actions because recorded database CPU load (88.5%) exceeds the critical-load guardrail (85%). No destructive command was run.

## 2. Scope and data quality
The brief describes `servers`, `logs`, and `incidents` tables. The delivered database actually contains only `servers` and `logs`: 2 server rows and 5,000 log rows. There is no `incidents` table. The logs contain 1,614 ERROR, 1,686 WARN, and 1,700 INFO records; however, every message is the generic `Sample log message`, every record is associated with `SRV-001`, and all records identify `Auth-Service`. These records cannot substantiate the cause of `SRV-002` resource pressure. The database timestamps are from 2026-06-29/30 and should not be treated as live telemetry.

## 3. Detection
Monitor Agent queried server metrics and compared them with configured thresholds:

```sql
SELECT * FROM servers ORDER BY server_id;
```

Observed records:

| Server | CPU | Memory | Status | Region |
|---|---:|---:|---|---|
| web-prod-1 (`SRV-001`) | 45.2% | 60.1% | ACTIVE | US-East |
| db-prod-1 (`SRV-002`) | 88.5% | 92.3% | ACTIVE | US-West |

Log-level distribution was checked with:

```sql
SELECT log_level, COUNT(*) AS count
FROM logs
GROUP BY log_level;
```

Results: ERROR 1,614; WARN 1,686; INFO 1,700. Because log messages are generic and belong only to `SRV-001`, they are not reliable causal evidence for `SRV-002`.

## 4. Diagnosis
The Diagnostician Agent retrieved knowledge-base guidance for combined CPU and memory pressure. Plausible hypotheses include database workload saturation, expensive queries, connection accumulation, cache growth, or a recent deployment. These are hypotheses only. The supplied database does not include query-level metrics, connection counts, process metrics, deployment history, or meaningful incident messages, so a definitive root cause cannot be assigned.

## 5. Remediation and safety decision
The Remediation Agent evaluated the database load using:

```sql
SELECT MAX(cpu_usage_percent) AS load FROM servers;
```

The result is 88.5%, above the configured critical-load threshold of 85%. Therefore, high-risk actions such as `system_reboot`, shutdown, disk formatting, or killing the database are blocked. Sentinel proposes operator-led inspection of top queries, connection-pool utilization, memory/cache trends, and recent deployment changes. Any scaling or restart requires explicit human approval and a verified maintenance plan.

## 6. Verification
Verification re-queried server telemetry and confirmed that threshold breaches remain. Since the implementation is intentionally read-only/simulated, it cannot claim recovery. The workflow sets the retry flag and routes back to diagnosis; after the configured retry limit, it escalates the unresolved condition.

## 7. Outcome and follow-up
- **Detected:** high CPU and memory on `db-prod-1`.
- **Contained:** high-risk remediation blocked under critical load.
- **Recovered:** not demonstrated; anomaly remains in source telemetry.
- **Root cause:** undetermined from available evidence.

Recommended data improvements: add the missing `incidents` table; populate meaningful, host-correlated log messages; provide time-series CPU/memory, database query latency, connection counts, disk I/O, deployment events, and post-remediation telemetry.

## 8. NL2SQL trace example
Administrator question: **“Show server health”**

Translation:

```sql
SELECT server_id, hostname, region, status,
       cpu_usage_percent, memory_usage_percent
FROM servers
ORDER BY server_id;
```

Execution uses a read-only SQLite connection. The application returns both the generated SQL and rows so the intent-to-query mapping is inspectable. An out-of-schema question such as “What is the CEO's favorite color?” returns a graceful unsupported-schema response and executes no SQL.

**LangSmith evidence:** The code supports LangSmith environment configuration, but no API key or live trace screenshot was supplied. A real trace screenshot must be captured after running the configured deployment; this report does not fabricate one.
