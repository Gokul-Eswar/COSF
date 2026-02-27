# Track Specification: Simulation & "Dry Run" Mode

## Overview
This track introduces a "Safe-to-Execute" verification layer for COSF. It allows users to preview the execution plan of a workflow without actually firing any network tools or modifying the environment. This is critical for enterprise environments where heavy scans must be pre-approved.

## Objectives
1.  **Execution Plan Generation:** Calculate and display the full dependency tree and resolved variables before execution.
2.  **Tool Mocking:** Provide a global "Simulation Mode" where adapters return synthetic but realistic data instead of executing containers.
3.  **Cost & Impact Estimation:** Estimate the time and network impact of a workflow based on the number of tasks and targets.
4.  **Policy Enforcement:** Check workflows against "Safety Rules" (e.g., "Don't scan production subnets during business hours") in dry-run mode.

## Scope

### In-Scope
-   **`ExecutionEngine` Dry-Run Flag:** A global toggle to bypass tool execution.
-   **Synthetic Data Generators:** Logic in `MockAdapter` or normalizers to produce varied test data.
-   **Plan Visualization:** A "Preview" button in the Web UI to show the execution graph.
-   **Pre-flight Checks:** Validation of credentials and target reachability (ping-only) before starting.

### Out-of-Scope
-   Full network traffic simulation (using `ns-3` or similar).
-   Accurate time estimation for complex tools like Burp Suite (will use historical averages).

## Success Criteria
-   A user can run `cosf run workflow.yaml --dry-run` and see exactly which tasks would have executed.
-   The Web UI shows an "Execution Plan" modal with resolved variables.
-   No network packets (other than pings) are sent to the target when dry-run is enabled.
