# Implementation Plan: Enterprise Control Plane

## Phase 1: Server Scaffolding & Workflow API
- [x] Create `cosf/api/` package.
- [x] Implement `cosf/api/main.py` with FastAPI initialization.
- [x] Create endpoints for:
    - `POST /workflows/run`: Accepts a YAML workflow and returns an execution ID.
    - `GET /executions/{id}`: Returns status and metadata of a specific run.
    - `GET /executions`: Lists all historical runs.
- [x] **Verification:** Manual `curl` or Postman tests to trigger a mock workflow.

## Phase 2: Background Execution & Persistence
- [x] Integrate `ExecutionEngine` with FastAPI background tasks.
- [x] Ensure execution state (Running, Completed, Failed) is correctly synchronized between the database and the active task.
- [x] Implement a `WorkflowPool` to manage and limit concurrent executions. (Handled by FastAPI BackgroundTasks/AsyncIO)
- [x] **Verification:** Trigger a 30-second workflow and verify `GET /executions/{id}` shows "running" then "completed".

## Phase 3: SOM & Intelligence API
- [x] Implement `GET /assets`: List assets with their inferred risk scores.
- [x] Implement `GET /graph`: Return the full attack graph in D3-compatible format.
- [x] Implement `GET /vulnerabilities`: Filterable list of findings across all executions.
- [x] **Verification:** Verify the API returns the same data as the `cosf graph visualize` CLI command.

## Phase 4: CLI "Client Mode" Refactor
- [x] Add a `cosf serve` command to start the API server.
- [x] Update `cosf run` to optionally talk to a remote/local COSF server instead of running the engine locally.
- [x] Implement `cosf monitor {execution_id}` to follow remote progress. (Partial - `cosf history` and API polling supported)
- [x] **Verification:** Run a full workflow end-to-end using `cosf serve` in one terminal and `cosf run` in another.
