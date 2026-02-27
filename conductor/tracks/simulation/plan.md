# Implementation Plan: Simulation & Dry Run Mode

## Phase 1: Engine Updates & Tool Mocking
- [ ] Add `dry_run: bool` parameter to `ExecutionEngine.run()`.
- [ ] Update `BaseAdapter.run()` to respect the dry-run flag.
- [ ] Implement `MockResponseGenerator`: A utility that returns realistic SOM entities for Nmap, Nuclei, etc., when in simulation mode.
- [ ] **Verification:** Run a workflow with `--dry-run` and verify no Docker containers are started.

## Phase 2: Execution Planning & Graphing
- [ ] Implement `ExecutionEngine.generate_plan(workflow)`: Returns a structured list of tasks with resolved variables but no execution.
- [ ] Update the CLI to print a "Workflow Plan" table before starting (or as part of `--dry-run`).
- [ ] **Verification:** Verify that `{{ tasks.discovery.outputs.ip }}` is correctly identified as a dependency in the plan even if not resolved yet.

## Phase 3: Web UI Preview Mode
- [ ] Add a "Dry Run" button next to "Run Workflow" in the Command Center modal.
- [ ] Implement a "Plan Viewer" that highlights the order of operations.
- [ ] Show "Estimated Impact" (e.g., number of tools, target subnet size).
- [ ] **Verification:** Click "Dry Run" in the UI and see the plan populated without creating a real execution history entry (or marked as "simulated").

## Phase 4: Safety Policy Enforcement
- [ ] Implement a `PolicyEngine` that checks the plan against a set of constraints (e.g., time of day, restricted IPs).
- [ ] Add a `safety_config.yaml` file to define these constraints.
- [ ] Block execution if a policy violation is detected in dry-run or real mode.
- [ ] **Verification:** Attempt to scan a "Blacklisted IP" and verify the engine prevents it.
