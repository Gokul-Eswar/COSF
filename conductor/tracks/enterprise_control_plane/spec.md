# Track Specification: Enterprise Foundation & API Control Plane

## Overview
This track transforms COSF from a CLI-based script runner into a persistent, enterprise-grade service. It introduces a central Control Plane (REST API) that manages workflow execution, state persistence, and data retrieval, allowing COSF to be integrated into larger ecosystems.

## Objectives
1.  **Persistent Control Plane:** Implement a long-running FastAPI server to act as the single source of truth.
2.  **Stable REST API:** Provide endpoints for uploading workflows, triggering executions, and querying SOM data.
3.  **Unified Execution Management:** Move from "fire-and-forget" CLI runs to a tracked job system.
4.  **Client-Server Architecture:** Refactor the CLI to become a thin client that communicates with the API.

## Scope

### In-Scope
-   **FastAPI Server:** The core web service logic.
-   **Workflow Management API:** Endpoints for CRUD operations on workflows and executions.
-   **Background Task Integration:** Using `asyncio` or a lightweight task queue to run workflows outside the request/response cycle.
-   **SOM Query API:** High-performance endpoints to fetch Assets, Vulnerabilities, and the Attack Graph.
-   **API Authentication:** Basic API key or JWT-based security for the control plane.

### Out-of-Scope
-   Distributed task queues like Celery/Redis (staying within the "self-hostable/local" spirit using internal `asyncio` first).
-   Full multi-tenancy/RBAC (focus on single-user/team access first).

## Success Criteria
-   A user can start the COSF server with a single command.
-   The CLI `run` command can trigger a workflow by sending it to the API.
-   Workflow status can be queried via HTTP while it is still running.
-   The attack graph can be retrieved as a JSON payload from a REST endpoint.
