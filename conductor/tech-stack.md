# Tech Stack

## Core Runtime & Backend
- **Language:** Python 3.12+ (Utilizing `asyncio` for high-concurrency execution and `Pydantic` for strict schema enforcement).
- **API & CLI:** FastAPI for the control plane and Typer for a modern, text-based command interface.
- **Orchestration:** Temporal (Enterprise-grade) or Prefect (Lightweight) for building durable and fault-tolerant workflows.

## Data Layer
- **Relational Data:** PostgreSQL for structured data and ACID compliance.
- **Search & Correlation:** OpenSearch for log indexing, evidence search, and vulnerability correlation.
- **Attack Graph:** Neo4j for modeling attack paths, lateral movement, and asset relationships.

## Infrastructure & Messaging
- **Isolation:** Docker/Kubernetes for sandboxed tool execution and scaling.
- **Event Bus:** NATS for lightweight and high-performance message streaming between framework components.

## Development Standards
- **Linting & Formatting:** Ruff and Black.
- **Type Checking:** MyPy.
- **Testing:** Pytest with Hypothesis for property-based testing.
