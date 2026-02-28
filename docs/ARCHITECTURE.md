# COSF System Architecture

The Cyber Operations Standardization Framework (COSF) is designed to decouple security operations from specific tools. It functions as a runtime orchestrator that translates declarative intents into secure, auditable, and tool-agnostic operations.

## Architecture Layers

```mermaid
graph TD
    subgraph 1. Workflow Definition Layer
        WDL[Workflow Parser]
        Validator[Schema Validator]
    end

    subgraph 2. Execution Runtime Engine
        Plan[Plan Generator]
        Policy[Policy Engine]
        Scheduler[Async Scheduler]
        Graph[Dependency Graph Resolver]
        Crypto[Ed25519 Cryptography]
    end

    subgraph 3. Adapter ecosystem
        BaseAdapter[Abstract Base Adapter]
        DockerSandbox[Docker Container Isolation]
        Normalizer[Tool Output Normalizer]
    end

    subgraph 4. Data Layer
        SOM[Security Object Model Pydantic]
        DB[SQLite/PostgreSQL Storage]
    end

    WDL --> Validator
    Validator --> Plan
    Plan --> Policy
    Plan --> Graph
    Graph --> Scheduler
    Scheduler --> BaseAdapter
    BaseAdapter --> DockerSandbox
    DockerSandbox --> Normalizer
    Normalizer --> SOM
    SOM --> DB
    Scheduler -.->|Signs Execution State| Crypto
```

## Component Details

### 1. Workflow Definition Language (WDL) Parser
Located in `cosf/parser/`. Parses `.yaml` workflows into strict Pydantic `WorkflowSchema` and `WorkflowTask` objects. Hard fails on invalid schemas to guarantee "Shift-Left" predictability.

### 2. Execution Engine (`cosf/engine/runtime.py`)
Built on Python's `asyncio`.
*   **Dependency Resolution:** Creates an execution graph based on `depends_on`.
*   **Condition Evaluator:** Evaluates `when` clauses to conditionally execute or skip tasks dynamically based on previous task outputs (e.g., `{{ tasks.recon.outputs.target_ip }} == "192.168.1.1"`).
*   **State Management:** Stores running state into a relational DB via SQLAlchemy async sessions.

### 3. Tool Adapters (`cosf/engine/adapters/`)
Implements the `BaseAdapter` interface. 
*   **Sandboxing:** Every third-party tool execution is instantiated inside a temporary Docker container via the Python `docker` SDK to ensure isolation.
*   **Normalization:** Receives heterogeneous outputs (e.g., XML from Nmap, JSON from Nuclei) and forces them into strictly typed `SOM` objects.

### 4. Security Object Model (SOM) (`cosf/models/som.py`)
A generalized abstraction of security data. Entities include `Asset`, `Service`, `Vulnerability`, `Credential`, `AttackStep`, `Evidence`, and `Relationship`. Models map cleanly to industry ontologies like MITRE ATT&CK.

## Execution Sequence

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Parser
    participant Engine
    participant Policy
    participant Adapter
    participant Docker
    participant DB

    User->>CLI: cosf run workflow.yaml
    CLI->>Parser: parse(workflow.yaml)
    Parser-->>CLI: WorkflowSchema
    CLI->>Engine: execute(WorkflowSchema)
    Engine->>Engine: generate_plan()
    Engine->>Policy: check_plan(plan)
    Policy-->>Engine: OK
    
    loop For Each Runnable Task
        Engine->>Engine: Resolve Variables
        Engine->>Policy: check_task(dynamic_params)
        Policy-->>Engine: OK
        Engine->>Adapter: run(params)
        Adapter->>Docker: run_container(image, args)
        Docker-->>Adapter: Raw Output
        Adapter->>Adapter: normalize(Raw Output)
        Adapter-->>Engine: TaskResult(Entities, Output)
        Engine->>DB: persist_som_objects(Entities)
        Engine->>Engine: Sign Execution State (Crypto)
    end
    Engine-->>CLI: Workflow Complete
```