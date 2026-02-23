# Specification: Advanced Workflow Logic (WDL 2.0)

## Objective
Support complex, conditional security operations by implementing task dependencies, variable passing, and task-level execution controls (retries/timeouts).

## Requirements
1.  **Task Dependencies**: Tasks should specify which other tasks must complete before they can run.
2.  **Variable Passing**: Outputs from one task should be usable as inputs for subsequent tasks using a template syntax (e.g., `{{ tasks.discovery.outputs.target_ip }}`).
3.  **Task Controls**: Each task should support optional `retries` and `timeout` settings.
4.  **DAG Execution**: The engine must resolve dependencies and execute tasks in a valid order, or detect circular dependencies.
