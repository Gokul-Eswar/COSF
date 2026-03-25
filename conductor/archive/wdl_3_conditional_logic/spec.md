# Specification: WDL 3.0 - Conditional & Dynamic Logic

## Objective
Enhance the Workflow Definition Language (WDL) to support decision-making and conditional execution based on the results of previous tasks.

## Requirements
1.  **Conditional Execution (`when`)**: Tasks should specify a condition under which they execute (e.g., `when: "tasks.nmap.outputs.port_80 == 'open'"`).
2.  **Logic Operators**: Support basic logical operators (`==`, `!=`, `in`, `contains`, `AND`, `OR`) within conditions.
3.  **Task Skipping**: The engine must skip tasks that don't meet their conditions without breaking the dependency chain for subsequent tasks (if applicable).
4.  **Dynamic Parameter Overrides**: Allow tasks to override parameters dynamically based on complex logic (e.g., `target: "{{ tasks.nmap.outputs.open_ports[0] }}"`).
5.  **Fail-Fast/Continue-On-Failure**: Configure whether the workflow should stop or continue if a conditional check fails or if a task fails.

## Key Design Considerations
-   The current engine uses a standard `ExecutionEngine.run` with simple dependency checks. This needs to be updated to evaluate conditions before adding tasks to the `runnable_tasks` list.
-   The condition evaluation should happen in the same context as variable resolution.
