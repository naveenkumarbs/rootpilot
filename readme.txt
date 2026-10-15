# RootPilot

### Agentic Root Cause Analysis & Remediation Assistance Platform

**RootPilot** is a multi-agent, AI-powered incident investigation and remediation-assistance platform built using **Python, Google Gemini, LangChain, LangGraph, FastAPI, and OpenSearch**.

The platform investigates operational incidents, retrieves relevant log evidence, generates grounded Root Cause Analysis (RCA) reports, recommends remediation actions, enforces deterministic safety policies, supports human approval, and simulates remediation execution.

RootPilot V1 is a **working prototype and learning project** focused on designing reliable, explainable, and controlled agentic AI systems.

> **V1 Safety Boundary:** RootPilot does not execute real production remediation actions. Restart and scaling operations are simulated. A simulated outcome must never be represented as verified production recovery.

---

## 1. Project Overview

Traditional incident investigation often involves manually searching logs, correlating errors, identifying root causes, and determining corrective actions.

RootPilot explores how specialized AI agents can assist with this process while maintaining clear boundaries between model-generated recommendations and authorized system operations.

### Key Capabilities

- AI-assisted incident investigation
- OpenSearch-based log retrieval
- Iterative agent reasoning and tool calling
- Evidence collection and validation
- Evidence-grounded RCA generation
- RCA quality evaluation and grounding enforcement
- Structured remediation planning
- Deterministic remediation policy validation
- Service authorization and evidence-reference checks
- Human-in-the-loop approval
- Simulated remediation execution
- Post-execution verification reporting
- Multi-agent orchestration using LangGraph
- Mock-based and live integration testing

### Project Goals

1. Understand and implement practical agentic AI architectures.
2. Build an evidence-driven RCA agent using operational logs.
3. Integrate LLM reasoning with external tools.
4. Coordinate specialized agents through a stateful workflow.
5. Apply deterministic controls to LLM-generated recommendations.
6. Implement human approval before potentially disruptive actions.
7. Evaluate agent outputs and prevent unsupported recovery claims.
8. Develop hands-on experience with concepts relevant to GenAI Architect and AI engineering roles.

---

## 2. Technology Stack

| Category | Technology | Purpose |
|---|---|---|
| Programming | Python | Core implementation |
| API Framework | FastAPI | Application/API foundation |
| LLM | Google Gemini | Agent reasoning and structured generation |
| LLM SDK | Google GenAI SDK | Direct model integration |
| LLM Framework | LangChain | Model abstraction and structured outputs |
| Agent Orchestration | LangGraph | Stateful multi-agent workflows |
| Log Search | OpenSearch | Operational log retrieval |
| Data Validation | Pydantic | Structured models and validation |
| State Persistence | LangGraph InMemorySaver | Local workflow checkpointing |
| Infrastructure | Docker | Containerized supporting services |
| Configuration | Environment variables / `.env` | Credentials and model configuration |
| Testing | Python test modules | Component and integration validation |

### Core Architectural Patterns

- Tool-augmented LLM reasoning
- Iterative agent execution
- Retrieval-augmented incident investigation
- Evidence grounding
- Structured output generation
- Multi-agent orchestration
- State-machine-based workflow execution
- Dependency injection
- Deterministic policy enforcement
- Human-in-the-loop approval
- Fail-closed authorization
- Simulation-based execution
- Post-execution verification

---

## 3. High-Level Architecture

```mermaid
flowchart TD
    A["Incident / User Request"] --> B["RootPilot Workflow"]

    B --> C["RCA Agent"]
    C --> D["OpenSearch Logs"]
    D --> C

    C --> E["Evidence Validation and Grounding"]
    E --> F["Grounded RCA Report"]

    F --> G["Remediation Planning Agent"]
    G --> H["Structured Remediation Plan"]

    H --> I{"Deterministic Policy Validation"}

    I -->|"Rejected"| J["Reject Execution"]
    I -->|"Allowed"| K{"Human Approval"}

    K -->|"Rejected"| J
    K -->|"Approved"| L["Simulated Remediation"]

    J --> M["Verification Agent"]
    L --> M

    M --> N["Verification Report"]
    N --> O["Final Workflow Result"]
```

### Architectural Principle

RootPilot separates **AI reasoning** from **system authorization and execution**.

The LLM can investigate an incident and propose remediation actions, but it cannot independently authorize those actions.

A deterministic policy layer validates the recommendations before human approval is requested.

---

## 4. Multi-Agent Architecture

RootPilot V1 contains three specialized AI agents.

### 4.1 RCA Agent

**Responsibility:** Investigate an operational incident and generate an evidence-backed root cause analysis.

The RCA Agent uses Gemini and operational tools to investigate incidents.

Its responsibilities include:

- Understanding incident symptoms
- Determining what evidence is required
- Requesting log-search tools
- Retrieving and examining operational logs
- Maintaining collected evidence
- Evaluating investigation progress
- Generating an RCA report
- Validating and enforcing evidence grounding

**Implementation:**

`app/agents/rca_agent.py`

**Primary interface:**

```python
result = await rca_agent.investigate(
    "Investigate checkout service failures"
)
```

The investigation returns a structured result containing the RCA report and workflow-related metadata.

### 4.2 Remediation Planning Agent

**Responsibility:** Convert an RCA report into structured remediation recommendations.

The planning agent receives the RCA report and proposes one or more actions.

It uses LangChain structured output with Pydantic models.

**Implementation:**

`app/agents/remediation_agent.py`

**Primary interface:**

```python
plan = await remediation_agent.plan(
    rca_report
)
```

Example action:

```json
{
  "action_type": "inspect_service_health",
  "target_service": "checkout",
  "rationale": "Inspect service health to investigate the reported failures.",
  "risk_level": "low",
  "supporting_evidence_ids": ["EV-0001"]
}
```

This is an illustrative action, not an actual incident result.

### 4.3 Remediation Verification Agent

**Responsibility:** Evaluate the recorded execution outcome and recommend follow-up verification steps.

The Verification Agent receives:

- The remediation plan
- The execution status

It generates structured observations and recommended next steps.

**Implementation:**

`app/agents/verification_agent.py`

**Primary interface:**

```python
report = await verification_agent.verify(
    remediation_plan=plan,
    execution_status="simulated"
)
```

The verification layer deterministically prevents a simulated execution from being reported as verified production recovery.

---

## 5. RCA Investigation Engine

The RCA Agent follows an iterative investigation pattern.

```mermaid
flowchart TD
    A["Incident"] --> B["Observe"]
    B --> C["Reason / Decide"]
    C --> D{"More Evidence Needed?"}
    D -->|"Yes"| E["Select Tool"]
    E --> F["Execute Tool"]
    F --> G["Collect Evidence"]
    G --> H["Evaluate Progress"]
    H --> C
    D -->|"No"| I["Generate RCA"]
    I --> J["Validate Grounding"]
    J --> K["Enforced RCA Report"]
```

### Investigation Lifecycle

1. Receive the incident description.
2. Determine which operational evidence is relevant.
3. Request a tool call when additional information is needed.
4. Execute the requested tool through application code.
5. Examine the returned evidence.
6. Evaluate whether further investigation is useful.
7. Continue within configured investigation limits.
8. Generate an RCA report.
9. Validate and enforce grounding requirements.

### Agent Loop

RootPilot implements the conceptual pattern:

**Observe → Reason / Decide → Act → Observe Result → Repeat → Finish**

The model requests tool calls, while the application is responsible for executing them.

### Investigation Control

The implementation includes:

- Bounded tool execution
- Evidence accumulation
- Evidence compression
- Progress evaluation
- Early stopping
- RCA quality evaluation

These mechanisms help limit unnecessary investigation steps and reduce unsupported conclusions.

---

## 6. Evidence Collection and Grounding

Evidence grounding is one of RootPilot's central design features.

An RCA report should not be considered trustworthy simply because it was generated by an LLM.

RootPilot therefore uses multiple validation and evaluation stages.

### 6.1 Evidence Collection

Operational evidence is retrieved through investigation tools, including OpenSearch-backed log retrieval.

Evidence references are maintained for use in downstream analysis.

### 6.2 Evidence Compression

Collected evidence can be compressed or summarized to reduce context size and avoid unnecessarily large model inputs.

The objective is to preserve relevant information while reducing context overhead.

### 6.3 Evidence Validation

Evidence is evaluated before being used to support conclusions.

The validation layer helps distinguish collected information from acceptable evidence.

### 6.4 Deterministic Grounding

Rule-based validation checks whether RCA findings reference permitted supporting evidence.

### 6.5 Semantic Grounding Evaluation

A semantic evaluator assesses the relationship between RCA conclusions and their supporting evidence.

### 6.6 RCA Quality Scoring

The RCA evaluation pipeline includes quality scoring to assess generated investigation results.

### 6.7 Grounding Enforcement

Grounding enforcement produces the RCA report that downstream components should consume.

The system can retain the original report separately for diagnostic purposes.

### Why Grounding Matters

Without grounding, an LLM might generate a technically plausible explanation that is not supported by actual logs.

RootPilot aims to reduce this risk by connecting RCA findings to collected evidence and validating that relationship.

> Grounding improves reliability, but it does not guarantee that an RCA conclusion is factually correct. Evidence quality and evaluator quality remain important limitations.

---

## 7. Remediation Planning

Once an RCA report is available, the Remediation Planning Agent proposes structured actions.

### Supported V1 Action Types

| Action | Purpose |
|---|---|
| `inspect_service_health` | Inspect service health |
| `inspect_service_metrics` | Inspect operational metrics |
| `restart_service` | Propose a service restart |
| `scale_service` | Propose a scaling operation |

All actions remain simulation-only in V1.

### Remediation Models

**Implementation:**

`app/remediation/models.py`

The primary models are:

- `RemediationAction`
- `RemediationPlan`

A remediation action contains:

```python
action_type
target_service
rationale
risk_level
supporting_evidence_ids
```

A remediation plan contains:

```python
incident_summary
actions
```

### Structured Output

The planning agent uses LangChain:

```python
llm.with_structured_output(
    RemediationPlan,
    method="json_schema"
)
```

This provides a typed contract between the planning agent and the workflow.

**Important:** Structured output validates the expected data shape; it does not establish that the recommendation is operationally safe.

---

## 8. Deterministic Remediation Policy

RootPilot does not allow an LLM-generated remediation plan to proceed directly to execution.

Every plan must pass a deterministic policy validator.

**Implementation:**

`app/remediation/policy.py`

### Policy Validation Rules

The policy checks:

1. A remediation plan contains at least one action.
2. Each action type is supported.
3. Each target service belongs to an authorized service allowlist.
4. Each action references supporting evidence.
5. Every referenced evidence ID belongs to the trusted evidence set.
6. Required trusted policy context is available.

### Evidence Validation

Evidence references are validated using set operations.

```python
unknown_ids = (
    set(action.supporting_evidence_ids)
    - set(valid_evidence_ids)
)
```

A nonempty result indicates that the action references evidence outside the trusted set.

### Service Authorization

Actions are restricted to explicitly authorized services.

For example:

```python
allowed_services = {
    "checkout",
    "email"
}
```

These values are illustrative. Actual authorized services must come from trusted configuration.

### Fail-Closed Behavior

If trusted evidence or service authorization context is missing, the policy rejects the plan.

This prevents missing security context from being interpreted as permission.

### Trust Boundary

The policy should validate evidence against authoritative, application-controlled evidence records.

An evidence ID appearing in an LLM-generated report is not, by itself, proof that the evidence exists or is trustworthy.

---

## 9. Human-in-the-Loop Approval

RootPilot uses LangGraph interrupts to pause the workflow before simulated execution.

**Implementation:**

`app/workflows/approval_workflow.py`

### Approval Lifecycle

```mermaid
flowchart TD
    A["Remediation Plan"] --> B{"Policy Allowed?"}
    B -->|"No"| C["Rejected"]
    B -->|"Yes"| D["Human Approval Interrupt"]
    D --> E{"Approved?"}
    E -->|"No"| C
    E -->|"Yes"| F["Simulated Execution"]
```

### LangGraph Interrupt

The workflow requests human approval using:

```python
interrupt(...)
```

The workflow can be resumed using:

```python
Command(resume=True)
```

or rejected using:

```python
Command(resume=False)
```

### Checkpointing

V1 uses LangGraph's:

```python
InMemorySaver
```

This supports local checkpointing and workflow resumption.

### Important Limitation

In-memory checkpointing does not provide durable recovery across application restarts.

Production deployment would require an appropriate persistent checkpoint store and stronger approval identity, authorization and audit controls.

---

## 10. Simulated Remediation Execution

RootPilot V1 intentionally does not perform actual production modifications.

When a plan passes policy validation and receives human approval, the workflow enters a simulated execution stage.

Example:

```text
[SIMULATED] inspect_service_health on checkout
```

The workflow records:

```python
execution_status = "simulated"
```

Rejected actions record:

```python
execution_status = "rejected"
```

### Why Simulation Was Chosen

Simulation provides a safe way to develop and demonstrate:

- Agent planning
- Policy validation
- Human approval
- Workflow routing
- Execution state tracking
- Verification behavior

It avoids exposing real infrastructure to model-generated operational commands during V1 development.

---

## 11. Remediation Verification

Verification is handled by a dedicated agent and a deterministic status-enforcement layer.

**Implementation:**

`app/remediation/verification_models.py`

`app/agents/verification_agent.py`

### Verification Model

```python
verification_status
observations
recommended_next_steps
production_recovery_verified
```

### Supported Verification Outcomes

| Execution Status | Verification Status |
|---|---|
| `simulated` | `simulated_only` |
| `rejected` | `not_executed` |
| Unsupported or unexpected | `verification_failed` |

### Recovery Verification Guardrail

The following value is enforced in V1:

```python
production_recovery_verified = False
```

This ensures that model-generated text cannot turn a simulated operation into a claim of verified production recovery.

---

## 12. LangGraph Workflow Orchestration

LangGraph coordinates the different stages of RootPilot.

### Main Workflow Responsibilities

- Prepare incident state
- Invoke RCA investigation
- Store the RCA result
- Invoke remediation planning
- Validate policy
- Route approval decisions
- Simulate execution
- Invoke verification
- Return the final workflow result

### RCA Workflow

**Implementation:**

`app/workflows/rca_workflow.py`

Important functions include:

```python
prepare_incident
create_rca_node
store_rca_result
create_remediation_node
build_rca_workflow
```

### Approval Workflow

**Implementation:**

`app/workflows/approval_workflow.py`

Handles policy validation, approval interrupts, simulation and rejection.

### Combined RootPilot Pipeline

**Implementation:**

`app/workflows/rootpilot_pipeline.py`

The combined pipeline uses shared state to coordinate the specialized agents.

### Why LangGraph?

LangGraph was selected for:

- Explicit workflow state
- Conditional routing
- Multi-agent orchestration
- Interrupt/resume support
- Checkpointing
- Reusable workflow nodes

Unlike an unrestricted agent loop, the overall RootPilot pipeline follows an explicit graph of permitted execution stages.

---

## 13. Project Structure

The following structure highlights the principal V1 components discussed in the implementation.

```text
rootpilot/
│
├── app/
│   ├── agents/
│   │   ├── rca_agent.py
│   │   ├── remediation_agent.py
│   │   └── verification_agent.py
│   │
│   ├── remediation/
│   │   ├── models.py
│   │   ├── policy.py
│   │   └── verification_models.py
│   │
│   └── workflows/
│       ├── rca_workflow.py
│       ├── approval_workflow.py
│       └── rootpilot_pipeline.py
│
├── tests/
│   ├── test_rca_workflow.py
│   ├── test_remediation_policy.py
│   ├── test_approval_workflow.py
│   ├── test_rootpilot_pipeline.py
│   ├── test_verification_workflow.py
│   └── test_rootpilot_v1_live.py
│
├── .env
├── requirements.txt
└── README.md
```

Additional modules supporting evidence storage, evaluation, LLM providers, API routes and tool integrations may be present in the repository.

The structure above is a functional overview, not an exhaustive file inventory.

---

## 14. Local Development Setup

### Prerequisites

- Python and pip
- Docker Desktop
- OpenSearch
- Google Gemini API key
- Git
- Windows PowerShell or another supported terminal

### Step 1: Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd rootpilot
```

Replace `<YOUR_REPOSITORY_URL>` with the actual repository URL.

### Step 2: Create a Virtual Environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```powershell
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file using the configuration expected by the application.

Example:

```dotenv
GOOGLE_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
```

The implementation also supports Gemini credential configuration through `GEMINI_API_KEY` where applicable.

Configure OpenSearch connectivity according to the repository's actual connection settings.

**Never commit `.env`, API keys, credentials, or sensitive operational logs to Git.**

### Step 5: Start Supporting Infrastructure

Start the OpenSearch services required by the project.

For a Docker Compose-based environment:

```powershell
docker compose up -d
```

Use the repository's actual Compose file and service configuration.

### Step 6: Verify OpenSearch

For a local OpenSearch HTTP endpoint:

```powershell
curl.exe http://localhost:9200/_cluster/health
```

Adjust the address and authentication as required by your deployment.

### Step 7: Run Tests

Start with mocked workflow tests before running live LLM integration tests.

---

## 15. Testing and Validation

RootPilot uses component tests, workflow tests and a live integration test.

### Test Modules

| Test | Purpose |
|---|---|
| `test_rca_workflow.py` | RCA workflow integration |
| `test_remediation_policy.py` | Policy validation |
| `test_approval_workflow.py` | Approval and rejection routing |
| `test_rootpilot_pipeline.py` | Combined multi-agent workflow |
| `test_verification_workflow.py` | Verification behavior |
| `test_rootpilot_v1_live.py` | Live Gemini/OpenSearch integration |

### Run RCA Workflow Test

```powershell
python -m tests.test_rca_workflow
```

### Run Remediation Policy Test

```powershell
python -m tests.test_remediation_policy
```

### Run Human Approval Test

```powershell
python -m tests.test_approval_workflow
```

### Run Combined Pipeline Test

```powershell
python -m tests.test_rootpilot_pipeline
```

### Run Verification Test

```powershell
python -m tests.test_verification_workflow
```

### Run Live Integration Test

```powershell
python -m tests.test_rootpilot_v1_live
```

The live test requires external service connectivity and valid Gemini credentials.

### Reported V1 Validation Status

The implemented tests were reported as passing during V1 development.

This confirms the scenarios exercised by those tests, not exhaustive correctness or production readiness.

### Important Testing Principle

A safe rejection can be a valid test result.

For example, if the policy detects missing evidence or an unauthorized target service, it should reject the plan rather than continue to approval.

---

## 16. V1 Development Milestones

| Milestone | Description | Status |
|---|---|---|
| M1 | Project foundation and environment | Completed |
| M2 | RCA Agent and investigation engine | Completed |
| M3 | RCA grounding, quality and control | Completed |
| M4 | LangChain and LangGraph integration | Completed |
| M5 | Remediation Planning Agent | Completed |
| M6 | Policy validation and human approval | Completed |
| M7 | Combined multi-agent pipeline | Completed |
| M8 | Remediation Verification Agent | Completed |
| M9 | V1 integration validation | Tests reported PASS |

### Milestone Highlights

**M1 — Foundation:** Python project setup, dependencies, configuration and OpenSearch connectivity.

**M2 — RCA:** Gemini-backed agent, tool calls, log retrieval, evidence collection and RCA generation.

**M3 — Grounding:** Evidence compression, validation, deterministic and semantic grounding, quality scoring and early stopping.

**M4 — Orchestration:** LangChain model integration, LangGraph nodes and RCA workflow composition.

**M5 — Planning:** Structured remediation models and LLM-generated remediation plans.

**M6 — Safety:** Deterministic policy checks, evidence authorization, service allowlists and human approval.

**M7 — Pipeline:** End-to-end graph composition, conditional routing and simulated execution.

**M8 — Verification:** Structured verification reports and deterministic prevention of false recovery claims.

**M9 — Validation:** Mocked workflows, regression tests and live integration testing.

---

## 17. Security and Safety Design

RootPilot applies several defensive architectural controls.

### Deterministic Policy Enforcement

Authorization decisions are evaluated outside the LLM.

### Evidence-Aware Remediation

Actions must reference trusted evidence IDs.

### Service Allowlisting

Actions are restricted to authorized services.

### Human Approval

Potentially disruptive operations require an explicit approval decision.

### Simulation-Only Execution

No real production remediation is performed.

### Verification Enforcement

Production recovery is never claimed based on simulation alone.

### Remaining Security Considerations

V1 should not be treated as a complete production security solution.

Areas requiring further work include:

- Prompt-injection resistance
- Strong identity and access management
- Approval identity verification
- Tenant and service authorization boundaries
- Durable audit trails
- Evidence provenance and integrity
- Secrets management
- Production tool sandboxing
- Network access controls
- Rate limiting and abuse prevention

---

## 18. Design Decisions and Trade-offs

| Decision | Benefit | Trade-off |
|---|---|---|
| Specialized agents | Clear separation of responsibilities | More integration complexity |
| Gemini integration | LLM reasoning and structured generation | External model dependency |
| LangChain | Standardized model interfaces | Additional abstraction |
| LangGraph | Stateful workflow orchestration | Graph and state management complexity |
| Evidence grounding | Reduces unsupported RCA claims | Depends on evidence quality |
| Deterministic policy | Separates authorization from AI reasoning | Requires policy maintenance |
| Human approval | Adds oversight | Introduces manual latency |
| In-memory checkpointing | Simple development workflow | Not durable across restarts |
| Simulation-only execution | Safe experimentation | No real operational recovery |
| Mocked and live testing | Separates orchestration and integration concerns | Does not establish exhaustive reliability |

---

## 19. Current Limitations

RootPilot V1 is a prototype rather than a production incident-management platform.

Current limitations include:

1. Remediation execution is simulated.
2. Production recovery is not verified.
3. Workflow checkpointing uses in-memory storage.
4. Production-grade authentication and authorization have not been established.
5. Comprehensive audit logging has not been validated.
6. Failure recovery and resilience require additional testing.
7. Agent tracing and model cost monitoring are not established as completed V1 capabilities.
8. Evidence trust boundaries require continued hardening.
9. RCA and remediation quality need systematic benchmark-based evaluation.
10. Operational deployment and production scalability have not been demonstrated.

---

## 20. Potential V2 Enhancements

The following are proposed improvements, not completed V1 features.

### Reliability and Persistence

- Persistent LangGraph checkpoints
- Workflow recovery after application restarts
- Timeouts, retries and backoff
- Circuit breakers
- Idempotent action execution

### Observability

- OpenTelemetry tracing
- Agent execution traces
- Prometheus metrics
- Grafana dashboards
- LLM latency and token usage tracking
- Model cost monitoring

### Security

- Role-based access control
- Service-scoped authorization
- Approval audit trails
- Stronger evidence provenance
- Prompt-injection defenses
- Secrets management

### Evaluation

- Golden incident datasets
- RCA correctness evaluation
- Grounding precision and recall
- Remediation relevance evaluation
- Policy rejection coverage
- Human approval workflow evaluation
- Agent regression testing

### Controlled Remediation

- Sandboxed remediation tools
- Dry-run previews
- Risk-based approval
- Rollback plans
- Post-action health checks
- Production recovery verification

Real remediation should only be introduced after appropriate authorization, isolation, operational safeguards and testing are established.

---

## 21. Developer Onboarding Guide

New developers should review the project in the following order:

1. `app/remediation/models.py` — Understand remediation contracts.
2. `app/remediation/policy.py` — Understand deterministic safety checks.
3. `app/agents/rca_agent.py` — Understand investigation and evidence collection.
4. `app/agents/remediation_agent.py` — Understand structured planning.
5. `app/workflows/rca_workflow.py` — Understand the basic LangGraph workflow.
6. `app/workflows/approval_workflow.py` — Understand interrupts and approval routing.
7. `app/workflows/rootpilot_pipeline.py` — Understand the complete multi-agent flow.
8. `app/agents/verification_agent.py` — Understand verification boundaries.
9. `tests/` — Understand expected behavior and rejection scenarios.

### Expected Developer Understanding

After onboarding, a developer should be able to:

- Explain the complete RootPilot workflow.
- Describe how the RCA Agent uses tools.
- Trace evidence references through the pipeline.
- Explain LangChain's and LangGraph's different responsibilities.
- Describe deterministic policy validation.
- Demonstrate the human approval process.
- Explain why execution is simulated.
- Run the regression tests.
- Identify the main production-readiness gaps.

---

## 22. Interview Discussion Guide

RootPilot was developed as a hands-on exploration of GenAI architecture, agent orchestration, grounding, safety controls and operational workflow design.

### Q1. What makes RootPilot an agentic AI system?

The RCA Agent uses an iterative reasoning-and-tool-calling process to investigate incidents and determine whether more evidence is needed.

The overall workflow also coordinates specialized agents through LangGraph.

Not every component is independently agentic: policy validation, routing and execution controls are deterministic.

### Q2. Why use multiple agents?

The system separates incident investigation, remediation planning and verification.

This improves modularity, testability and clarity of responsibility.

### Q3. Why use both LangChain and LangGraph?

LangChain provides model integration and structured output capabilities.

LangGraph manages shared state, execution order, conditional routing, checkpointing and human approval.

### Q4. How does RootPilot reduce hallucinations?

It uses operational evidence, evidence validation, grounding checks, semantic evaluation and report enforcement.

These mechanisms reduce unsupported conclusions but do not eliminate all hallucination or reasoning errors.

### Q5. Can the LLM directly restart a production service?

No.

In V1, the LLM proposes actions. Deterministic policy checks and human approval control progression, and execution remains simulated.

### Q6. Why implement a policy engine outside the LLM?

LLM outputs are probabilistic and should not be treated as authorization decisions.

A deterministic policy engine provides explicit, testable constraints.

### Q7. What happens when evidence is missing?

The remediation policy rejects the plan when required trusted evidence context is unavailable or action evidence references are invalid.

### Q8. How does human approval work?

LangGraph pauses execution using an interrupt. A human decision is supplied when the workflow resumes.

### Q9. How is remediation success verified?

V1 verifies the recorded workflow outcome, not production recovery.

The Verification Agent produces observations, while deterministic logic ensures that simulation is never reported as verified production recovery.

### Q10. What would be required before production deployment?

Persistent workflow storage, robust authorization, secure tool execution, observability, audit logging, failure handling, stronger evaluations, rollback support and controlled production verification.

---

## 23. Engineering Lessons

RootPilot demonstrates several important principles for building agentic AI systems.

**1. Agentic behavior should be purposeful.** Not every operation requires an autonomous agent. Deterministic operations are often more appropriate for authorization and control.

**2. LLM-generated output is not trusted input.** Structured generation improves consistency but does not replace validation.

**3. Evidence should be traceable.** Investigation results and remediation recommendations should be connected to verifiable evidence.

**4. Human approval is part of system design.** Approval should be implemented as a workflow control, not merely as a prompt instruction.

**5. Verification must reflect actual execution.** A model should not claim that a system has recovered unless recovery has been independently established.

**6. Testability should influence architecture.** Dependency injection and reusable graph nodes make it possible to test orchestration independently of external services.

**7. Production readiness is separate from functional completeness.** A workflow that passes functional tests still requires operational, reliability and security validation.

---

## 24. Project Status

**Current Release:** V1

**Development Status:** Implemented

**Testing Status:** Reported passing for V1 regression and live integration tests

**Execution Mode:** Simulation only

**Production Readiness:** Not established

### V1 Summary

RootPilot demonstrates an end-to-end agentic incident-investigation lifecycle:

**Investigate → Ground → Plan → Validate → Approve → Simulate → Verify**

The project's primary contribution is its controlled architecture: AI agents handle investigation and recommendations, while deterministic policies and human oversight govern progression through the remediation workflow.

---

## 25. Contributing

Contributions and suggestions are welcome.

Potential contribution areas include:

- Additional investigation tools
- Improved grounding evaluations
- More comprehensive tests
- Persistent workflow checkpointing
- Enhanced observability
- Security hardening
- Benchmark datasets
- Safer remediation simulations

When contributing, preserve the separation between model reasoning, policy authorization and execution.

Do not introduce production-changing operations without explicit safeguards and review.

---

## 26. License

No license has been specified for this repository.

Before publishing or accepting external contributions, add an appropriate `LICENSE` file and update this section.

---

## 27. Disclaimer

RootPilot is intended for educational, research, demonstration and controlled development purposes.

The current implementation does not provide verified production remediation or autonomous production recovery.

AI-generated diagnoses and remediation recommendations should be independently reviewed before operational use.

---

**RootPilot — Building evidence-grounded, controlled and explainable agentic incident workflows.**