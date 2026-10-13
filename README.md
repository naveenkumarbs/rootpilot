# RootPilot

**Agentic root-cause investigation for observable microservices**  
**Status:** Working prototype — Milestone 4.5 validated; Milestone 4.6 (structured evidence and RCA evaluation) in progress.

> RootPilot currently **investigates and recommends**. It does **not** perform automated remediation, modify production infrastructure, or prove a fundamental root cause from logs alone.

## 1. Overview

RootPilot is a Python-based incident investigation agent that uses a large language model (LLM) to decide which **allowlisted observability tools** to call, interpret their results, investigate service dependencies, and write an evidence-based root-cause analysis (RCA) report.

The prototype uses **Gemini** through a provider-independent LLM interface and retrieves application logs from **OpenSearch**. A **Prometheus query client** and a memory-anomaly detection capability were implemented in earlier milestones; they are **not yet exposed as tools to the current RCA agent**. The OpenTelemetry Demo provides the third-party microservices workload used to generate telemetry.

### Current capabilities

- Multi-iteration **observe → decide → tool call → observe** investigation loop.
- Gemini native function calling, with execution performed by the application (not the model).
- Provider-neutral message, tool, response, and token-usage models.
- Allowlisted OpenSearch log search with service, severity, time-window, and result-limit arguments.
- Bounded investigation: maximum iterations, tool requests, and wall-clock deadline.
- In-investigation cache for identical tool requests.
- Token usage accounting (input, output, and reasoning tokens where reported by provider).
- Final RCA narrative distinguishing observed failure mechanisms from hypotheses.
- No automated remediation actions.

### Not yet implemented

- Claude/Anthropic or Vertex AI adapters (interfaces are prepared, not integrated).
- Evidence IDs, structured RCA schema, citation validation, or deterministic evaluation (Milestone 4.6).
- Prometheus metrics or distributed tracing as agent-callable tools.
- Autonomous fixes, change approval, rollback, or remediation policy engine.
- Production authentication, tenant isolation, persistent investigation history, or comprehensive deployment hardening.

## 2. Architecture

```text
                         Incident / investigation prompt
                                      |
                                      v
                              RCAAgent (Python)
                         +-------------------------+
                         | bounded agent loop      |
                         | message history         |
                         | tool allowlist + cache  |
                         | token/time accounting   |
                         | RCA finalization        |
                         +------------+------------+
                                      |
                          provider-neutral models
                                      |
                                      v
                               LLMProvider
                                      |
                                GeminiProvider
                                      |
                              Gemini API / model
                                      |
                        function-call request(s)
                                      |
                                      v
                          Tool registry / executor
                                      |
                             search_service_logs
                                      |
                               OpenSearch client
                                      |
                         OpenSearch log index(es)
                                      ^
                                      |
                   OpenTelemetry Demo microservices
                   (external third-party test workload)

    Separate earlier components:
    Prometheus client --> Prometheus server
    Memory anomaly detection --> telemetry analysis
    (not currently available as RCA agent tools)
```

**Security boundary:** the model proposes a tool name and arguments; the RootPilot application validates/dispatches the request through an allowlisted registry. The model does not execute arbitrary Python, shell commands, or remediation actions.

## 3. Technology stack

| Layer | Current technology | Role |
| --- | --- | --- |
| Language | Python | Agent orchestration and telemetry integrations |
| API foundation | FastAPI | Application foundation; public endpoint coverage should be verified against local code |
| Configuration | Pydantic Settings / `.env` | Runtime configuration |
| LLM SDK | `google-genai` | Gemini model calls and native function calling |
| Observability logs | OpenSearch | Searchable service logs |
| Observability metrics | Prometheus | Metric queries; earlier milestone integration |
| Test workload | OpenTelemetry Demo | Third-party microservices telemetry source |
| Infrastructure | Docker; Google Cloud VM | Test environment |
| Local development | Windows / PowerShell / Python virtual environment | Development workflow |

The exact package versions are defined by the repository's dependency file, if pinned. Do not assume versions from this README.

## 4. Repository layout

The following paths reflect the implementation discussed through Milestone 4.5; add or adjust paths as the repository evolves.

```text
RootPilot/
├── app/
│   ├── agents/
│   │   └── rca_agent.py           # Agent orchestration and guardrails
│   ├── config/
│   │   └── settings.py            # Runtime settings
│   ├── llm/
│   │   ├── base.py                # LLMProvider contract
│   │   ├── factory.py             # Provider selection
│   │   ├── gemini_provider.py     # Gemini-specific adapter
│   │   └── models.py              # Provider-independent message models
│   ├── telemetry/
│   │   ├── opensearch_client.py   # OpenSearch queries
│   │   └── prometheus_client.py   # Prometheus queries
│   └── tools/
│       ├── definitions.py        # Tool schemas shown to the model
│       ├── opensearch_tools.py   # Input validation and log search
│       └── registry.py           # Allowlisted tool dispatcher
├── tests/
│   ├── test_llm_provider.py       # Provider smoke test
│   └── test_rca_agent.py         # Agent integration smoke test
├── .env.example                  # Safe configuration template (create if absent)
├── .gitignore                    # Ignore secrets, virtualenvs, third-party checkout
├── requirements.txt              # Project dependencies
└── README.md
```

## 5. How an investigation works

1. The caller provides an incident prompt (for example, investigate recent `checkout` timeouts).
2. `RCAAgent` creates system and user messages and starts its deadline-limited loop.
3. The selected provider sends conversation history and declared tool schemas to Gemini.
4. Gemini may return a request to call `search_service_logs`.
5. RootPilot executes the request through the tool registry and OpenSearch client.
6. The tool result is appended as a **tool message**, following the assistant's original function-call message. Gemini-specific original content is preserved by the provider adapter to retain any thought signatures.
7. The loop repeats until the model finishes, a configured limit is reached, or an error occurs.
8. At the iteration limit, RootPilot makes a final model call **without tools** to generate a report from collected evidence.
9. The caller receives status, completion reason, report text, tool history, timing, and token totals.

**Important:** `status=completed` currently means a report was produced. It does **not** mean every hypothesis was proven or the investigation was exhaustive. `completion_reason=iteration_limit` indicates the investigation stopped at its configured budget.

## 6. Current tool: `search_service_logs`

**Purpose:** Retrieve service logs from OpenSearch for investigation.

| Argument | Type | Constraint | Notes |
| --- | --- | --- | --- |
| `service_name` | string | Required; tool-side max length 100 | Use exact service identifier, e.g. `checkout`, not an invented alias |
| `minutes` | integer | 1–60 | Lookback window |
| `severity` | string | Optional | Example: `ERROR`, `WARN`; omitted for all severities |
| `limit` | integer | 1–50 | Prefer 10–20 for bounded context |

The tool returns matching log records (possibly an empty list). **Successful execution is not evidence that matching logs were found.** Results are treated as untrusted data, never as instructions to the agent.

## 7. Setup and configuration

### Prerequisites

- Python environment compatible with the project's dependency versions.
- Access to a Gemini API key and a configured supported model.
- An OpenSearch instance containing service logs.
- Optional Prometheus instance for earlier telemetry experiments.
- The third-party OpenTelemetry Demo environment, if reproducing the microservices test workload.

### Local setup (PowerShell)

```powershell
cd <path-to-RootPilot>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `.env` from `.env.example` and supply **your own** API key. Never commit `.env` or cloud credentials.

Example configuration (verify exact observability setting names in `app/config/settings.py`):

```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=<your-secret-key>
GEMINI_MODEL=<supported-model-id>
AGENT_MAX_ITERATIONS=5
AGENT_MAX_TOOL_CALLS=10
AGENT_MAX_EXECUTION_SECONDS=120
# OPENSEARCH_URL=http://127.0.0.1:9200
# PROMETHEUS_URL=http://127.0.0.1:9090
```

### Accessing OpenSearch on a remote VM

The prototype has been tested with OpenSearch on a Google Cloud VM and an SSH tunnel to the developer's workstation. In a **separate PowerShell window**, use your actual SSH username, VM address, and key:

```powershell
ssh -i "$env:USERPROFILE\.ssh\google_compute_engine" -N -L 9200:127.0.0.1:9200 <VM_USER>@<VM_EXTERNAL_IP>
```

Verify the tunnel:

```powershell
Invoke-RestMethod http://127.0.0.1:9200/_cluster/health
```

Keep the tunnel open while running integration tests. The remote Docker/OpenSearch deployment and port-forwarding are test-environment details, not production deployment guidance.

### Smoke tests

```powershell
python -m tests.test_llm_provider
python -m tests.test_rca_agent
```

The RCA test requires the LLM API and OpenSearch to be reachable. Its findings depend on the logs available at execution time; results are **not deterministic**.

## 8. Validated example: checkout → email timeouts

A completed integration run on **2026-10-12** demonstrated:

- **5** investigation iterations and **5** successful log-search tool requests.
- **34.92 seconds** total reported runtime.
- Token usage: **9,605 input**, **942 output**, **378 reasoning** tokens (provider-reported).
- `checkout` ERROR search returned no matches; WARN search returned repeated `context deadline exceeded` warnings when POSTing to `http://email:6060/send_order_confirmation` around **18:17–18:27 UTC**.
- `email` ERROR and WARN searches returned no matches; an unfiltered search found later INFO records stating `Order confirmation email sent` around **18:40–18:45 UTC**.

**Evidence-supported conclusion:** checkout's outbound HTTP calls to the email endpoint exceeded their request context deadlines.

**Unproven hypotheses:** email-service saturation, temporary slow processing, or network degradation. The later successful email logs do **not** independently establish which of these caused the earlier failures.

**Limits of this example:** No incident-period email resource metrics or correlated failed-request traces were retrieved. The output is an example of investigation behavior, not a ground-truth diagnosis.

## 9. Current safety and operational limits

- **Tool allowlist:** only registered tools can be dispatched.
- **Input bounds:** time window, log count, and service-name length are restricted.
- **Execution budgets:** iteration count, tool-request count, and elapsed time are capped.
- **No write/remediation tools:** the agent cannot restart services, change configuration, or modify infrastructure.
- **Tool caching:** repeated identical queries within an investigation may be served from memory.
- **Prompt-injection posture:** the system prompt tells the agent to treat logs as untrusted evidence; this is a basic safeguard, **not a complete prompt-injection defense**.
- **Timeout caveat:** the current synchronous SDK call runs in `asyncio.to_thread`; timing out the awaiting coroutine does not necessarily cancel the underlying network request.
- **Audit caveat:** current in-memory tool history is not a durable audit trail.

## 10. Development milestones

| Milestone | Status | Scope |
| --- | --- | --- |
| 1–3: Telemetry foundation | Completed in prototype | Prometheus query client, memory anomaly detection, OpenSearch log retrieval |
| 4.4: Bounded RCA agent | Completed | Gemini tool calling, multi-step loop, budgets, report generation |
| 4.5: Provider-neutral refactor | Validated with Gemini | Common models, provider factory, Gemini adapter, agent decoupling |
| 4.6: Structured evidence and evaluation | **In progress** | Evidence IDs, structured RCA, claim validation, evaluation fixtures |
| Future: Additional providers | Planned | Anthropic API and/or Vertex AI adapters |
| Future: Expanded telemetry | Planned | Prometheus and tracing tools callable by RCA agent |
| Future: Controlled remediation | Planned | Approval gates, dry-run, policy checks, rollback, audit |

### Milestone 4.6 — planned implementation sequence

1. Define typed models for evidence, observations, hypotheses, findings, and RCA reports.
2. Capture tool outputs in an evidence store with stable IDs and provenance.
3. Require evidence references for confirmed findings; distinguish observations from hypotheses.
4. Validate RCA claims and completeness before marking a report as accepted.
5. Compress/deduplicate log evidence to reduce token usage without losing traceability.
6. Create reproducible evaluation fixtures and tests (including empty logs, conflicting evidence, and unsupported claims).

## 11. How to extend this README

**Keep sections 1–10 accurate as the architecture changes.** For every milestone, append a dated entry below using this template, then update the capability/status tables above.

```markdown
### YYYY-MM-DD — Milestone X.Y: <name>

**Status:** Completed / In progress / Experimental

**Objective:** <what this milestone adds>

**Files added or changed:**
- `path/to/file.py` — <purpose>

**Design and behavior:**
- <important architecture decisions and trade-offs>

**Validation:**
- Command: `<test command>`
- Outcome: <measured results, known limits>

**Safety and limitations:**
- <what is still unsupported or risky>

**Next:** <next milestone>
```

## 12. Development log (append new entries below)

### 2026-10-12 — Milestone 4.5: Provider-independent agent loop

**Status:** Validated with Gemini.

**Objective:** Separate RCA orchestration from provider-specific SDK models.

**Files involved:** `app/llm/models.py`, `app/llm/base.py`, `app/llm/factory.py`, `app/llm/gemini_provider.py`, `app/agents/rca_agent.py`, `app/tools/definitions.py`.

**Design and behavior:** Common `LLMMessage`, `LLMResponse`, `ToolCall`, `ToolResult`, and `ToolDefinition` types. Gemini adapter maps messages and tools to native SDK structures and retains original model content for function-call continuation. Agent handles bounded iterations, tool execution, caching, token accounting, and finalization.

**Validation:** `python -m tests.test_llm_provider` passed; `python -m tests.test_rca_agent` completed a five-iteration checkout/email investigation. The report correctly distinguished the observed timeout from hypotheses about its underlying cause.

**Limitations:** Only Gemini is integrated; RCA output is unstructured narrative; confidence and evidence citations are not mechanically validated.

**Next:** Milestone 4.6 — structured RCA models and evidence management.

## 13. Third-party attribution

**OpenTelemetry Demo** is maintained by the OpenTelemetry community and is used as an **external test workload**. Its source code is not part of RootPilot's original implementation. Upstream repository: https://github.com/open-telemetry/opentelemetry-demo . Follow its license and attribution requirements if redistributing any portions or derived configurations.

RootPilot's authorship claims apply to the RootPilot code and configurations actually authored in this repository, not to upstream telemetry services or the OpenTelemetry Demo application.

## 14. Contributing, licensing, and security

This is currently a learning and portfolio prototype. Do not deploy against production systems or expose service logs and API keys publicly without implementing appropriate authentication, authorization, secret management, data retention, and security review.

A RootPilot license has **not** been specified here. Add a `LICENSE` file only after selecting the intended license. Do not imply the repository is open-source merely because it is publicly visible.
