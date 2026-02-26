# Implementation Plan: Enterprise Control Plane

## Phase 1: Server Scaffolding & Workflow API
- [ ] Create `cosf/api/` package.
- [ ] Implement `cosf/api/main.py` with FastAPI initialization.
- [ ] Create endpoints for:
    - `POST /workflows/run`: Accepts a YAML workflow and returns an execution ID.
    - `GET /executions/{id}`: Returns status and metadata of a specific run.
    - `GET /executions`: Lists all historical runs.
- [ ] **Verification:** Manual `curl` or Postman tests to trigger a mock workflow.

## Phase 2: Background Execution & Persistence
- [ ] Integrate `ExecutionEngine` with FastAPI background tasks.
- [ ] Ensure execution state (Running, Completed, Failed) is correctly synchronized between the database and the active task.
- [ ] Implement a `WorklowPool` to manage and limit concurrent executions.
- [ ] **Verification:** Trigger a 30-second workflow and verify `GET /executions/{id}` shows "running" then "completed".

## Phase 3: SOM & Intelligence API
- [ ] Implement `GET /assets`: List assets with their inferred risk scores.
- [ ] Implement `GET /graph`: Return the full attack graph in D3-compatible format.
- [ ] Implement `GET /vulnerabilities`: Filterable list of findings across all executions.
- [ ] **Verification:** Verify the API returns the same data as the `cosf graph visualize` CLI command.

## Phase 4: CLI "Client Mode" Refactor
- [ ] Add a `cosf serve` command to start the API server.
- [ ] Update `cosf run` to optionally talk to a remote/local COSF server instead of running the engine locally.
- [ ] Implement `cosf monitor {execution_id}` to follow remote progress.
- [ ] **Verification:** Run a full workflow end-to-end using `cosf serve` in one terminal and `cosf run` in another.
