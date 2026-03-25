# Implementation Plan: Simulation & Dry Run Mode

## Phase 1: Engine Updates & Tool Mocking
- [x] Add `dry_run: bool` parameter to `ExecutionEngine.run()`.
- [x] Update `BaseAdapter.run()` to respect the dry-run flag.
- [x] Implement `MockResponseGenerator`: A utility that returns realistic SOM entities for Nmap, Nuclei, etc., when in simulation mode.
- [x] **Verification:** Run a workflow with `--dry-run` and verify no Docker containers are started.

## Phase 2: Execution Planning & Graphing
- [x] Implement `ExecutionEngine.generate_plan(workflow)`: Returns a structured list of tasks with resolved variables but no execution.
- [x] Update the CLI to print a "Workflow Plan" table before starting (or as part of `--dry-run`).
- [x] **Verification:** Verify that `{{ tasks.discovery.outputs.ip }}` is correctly identified as a dependency in the plan even if not resolved yet.

## Phase 3: Web UI & API Support
- [x] Add `dry_run` support to `WorkflowRunRequest` in the API.
- [x] Add a "Dry Run" button next to "Run Workflow" in the Command Center modal.
- [x] Implement API background tasks that respect the dry-run flag.
- [x] **Verification:** Trigger a dry run via CLI or API and see "simulated" status in history.

## Phase 4: Safety Policy Enforcement
- [x] Implement a `PolicyEngine` that checks the plan against a set of constraints (e.g., time of day, restricted IPs).
- [x] Add a `safety_config.yaml` file to define these constraints.
- [x] Block execution if a policy violation is detected in dry-run or real mode.
- [x] **Verification:** Attempt to scan a "Blacklisted IP" and verify the engine prevents it.
