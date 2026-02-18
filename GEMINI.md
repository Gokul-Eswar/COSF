# Cyber Operations Standardization Framework (COSF)

## Project Overview
The **Cyber Operations Standardization Framework (COSF)** is a universal execution, orchestration, and data normalization layer for cybersecurity operations. It aims to establish a "Security-as-Code" standard by making security workflows executable, portable, and reproducible.

### Core Pillars
1.  **Workflow Definition Language (WDL):** A declarative, versioned YAML/JSON-based DSL for describing cyber operations (e.g., network assessments, vulnerability validation, incident response).
2.  **Execution Runtime Engine:** A deterministic engine that orchestrates workflow steps, manages dependencies, and tracks execution state with high reliability.
3.  **Tool Adapter Layer:** A pluggable ecosystem that abstracts tool-specific complexities (Nmap, Nuclei, etc.) and executes them in sandboxed environments (Docker).
4.  **Security Data Normalization Engine:** A unified model that transforms heterogeneous tool outputs into standardized **Security Object Model (SOM)** entities (Asset, Vulnerability, Evidence, etc.).

---

## Directory Overview
This directory contains the foundational specifications and architectural design for the COSF project. It currently serves as the "Source of Truth" for the project's vision and technical roadmap before the implementation phase begins.

### Key Files
- `details.md`: The comprehensive project specification, covering vision, problem statement, core objectives, high-level architecture, component requirements, and the recommended technology stack.
- `GEMINI.md`: This file, providing contextual guidance for AI agents interacting with the project.

---

## Technical Specifications (Planned)
Based on the architectural design in `details.md`, the following tech stack and standards are prioritized:

- **Language:** Python 3.12+ (Primary), utilizing `asyncio` for execution and `Pydantic` for strict schema enforcement.
- **API & CLI:** FastAPI for the control plane and Typer for the command-line interface.
- **Orchestration:** Temporal (Enterprise-grade) or Prefect (Lightweight) for durable workflows.
- **Data Layer:** 
    - PostgreSQL (Relational/Structured data)
    - OpenSearch (Log indexing & Search)
    - Neo4j (Attack path modeling & Graph relationships)
- **Infrastructure:** Docker/Kubernetes for tool isolation and plugin sandboxing.
- **Messaging:** NATS for lightweight event streaming.

---

## Development Conventions & Principles
- **Reproducibility First:** Every workflow execution must be deterministic. Environment fingerprinting (storing tool versions, Docker hashes, etc.) is mandatory for auditability.
- **Strict Contracts:** Use immutable Pydantic models for all input/output contracts. No free-form dictionaries are allowed in the core runtime or plugin interfaces.
- **Tool Agnosticism:** The core framework must remain independent of specific security tools. Integration is handled exclusively through the Adapter Layer.
- **Semantic Versioning:** Mandatory versioning for the DSL, Plugin API, and SOM to prevent ecosystem fragmentation.
- **RFC Process:** Any major changes to the core specifications (DSL, API, SOM) must be documented in an RFC before implementation.

---

## Usage & Interaction
- **Research & Strategy:** When asked to implement features, always refer back to `details.md` to ensure alignment with the established architectural principles.
- **Implementation:** Prioritize building the **Workflow Runtime Engine** and the **Security Object Model (SOM)** as the first steps.
- **Validation:** Every new feature or adapter must be verified against the "Minimalism Principle"—ensuring it strengthens standardization rather than introducing special-case logic.
